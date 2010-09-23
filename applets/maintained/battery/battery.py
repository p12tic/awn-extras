#!/usr/bin/python
# Copyright (c) 2007 - 2008  Randal Barlow <im.tehk at gmail.com>
#               2008 - 2010  onox <denkpadje@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import commands
import os

import pygtk
pygtk.require('2.0')
import gtk
from gtk import gdk

from awn.extras import _, awnlib, __version__
from messagehandler import MessageHandler

try:
    import dbus
except ImportError:
    dbus = None

# Interval in seconds between two successive checks of the status
check_status_interval = 5.0

applet_name = _("Battery Status")
applet_description = _("An applet which displays battery information")

# Themed logo of the applet, used as the applet's icon and shown in the GTK About dialog
applet_theme_logo = "battery"

themes_dir = os.path.join(os.path.dirname(__file__), "themes")
default_theme = "gpm"

ui_file = os.path.join(os.path.dirname(__file__), "battery.ui")

charge_ranges = {"100": (100, 86), "080": (85, 66), "060": (65, 46), "040": (45, 26), "020": (25, 7), "000": (6, 0)}

warning_percentage = 5.0

"""
TODO:
1) update battery_models before displaying prefs
2) handle removal of current battery or other batteries
"""


class BatteryStatusApplet:

    """An applet which displays battery information.

    """

    # State of the icon (a tuple containing the icon path and size)
    __previous_state = None

    def __init__(self, applet):
        self.applet = applet

        applet.tooltip.disable_toggle_on_click()

        self.backend = None
        for b in backends:
            if b.backend_useable():
                self.backend = b()
                break

        self.setup_context_menu()

        if self.backend is not None:
            self.__message_handler = MessageHandler(self)

            applet.timing.register(self.check_status_cb, check_status_interval)
            self.check_status_cb()
        else:
            self.set_battery_missing()

        applet.connect_size_changed(self.size_changed_cb)

    def size_changed_cb(self):
        if self.backend is not None:
            self.check_status_cb()
        else:
            self.set_battery_missing()

    def set_battery_missing(self):
        self.applet.tooltip.set(_("No batteries"))

        icon = os.path.join(themes_dir, self.applet.settings["theme"], "battery-missing.svg")
        self.applet.icon.file(icon, size=awnlib.Icon.APPLET_SIZE)

    def setup_context_menu(self):
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)
        prefs.get_object("vbox-preferences").reparent(self.applet.dialog.new("preferences").vbox)

        """ Battery """
        if self.backend is not None:
            batteries = self.backend.get_batteries()

            self.combobox_battery = prefs.get_object("combobox-battery")
            awnlib.add_cell_renderer_text(self.combobox_battery)
            for model in batteries.values():
                self.combobox_battery.append_text(model)

            if self.applet.settings["battery-udi"] not in batteries:
                self.applet.settings["battery-udi"] = batteries.keys()[0]

            if len(self.applet.settings["low-level-unit"]) == 0:
                self.applet.settings["low-level-unit"] = _("Percent")

            battery_getter = lambda key_value: batteries[key_value]
            battery_setter = lambda widget_value: batteries.keys()[batteries.values().index(widget_value)]
        else:
            frame = prefs.get_object("frame-battery")
            frame.hide_all()
            frame.set_no_show_all(True)

            battery_getter = lambda v: v
            battery_setter = lambda v: v

        """ Display """
        # Only use themes that are likely to provide all the files
        self.themes = os.listdir(themes_dir)
        self.themes.sort()

        combobox_theme = prefs.get_object("combobox-theme")
        awnlib.add_cell_renderer_text(combobox_theme)
        for i in self.themes:
            combobox_theme.append_text(i)

        self.theme = self.applet.settings["theme"]
        if self.theme not in self.themes:
            self.applet.settings["theme"] = self.theme = default_theme

        """ Notifications """
        if self.backend is not None:
            self.hbox_low_level = prefs.get_object("hbox-low-level")
            self.hbox_low_level.set_sensitive(self.applet.settings["warn-low-level"])

            self.hbox_high_level = prefs.get_object("hbox-high-level")
            self.hbox_high_level.set_sensitive(self.applet.settings["notify-high-level"])
        else:
            frame = prefs.get_object("frame-notifications")
            frame.hide_all()
            frame.set_no_show_all(True)

        refresh_message = lambda v: self.__message_handler.evaluate()

        binder = self.applet.settings.get_binder(prefs)
        binder.bind("theme", "combobox-theme", key_callback=self.combobox_theme_changed_cb)
        binder.bind("battery-udi", "combobox-battery", getter_transform=battery_getter, setter_transform=battery_setter, key_callback=self.combobox_battery_changed_cb)
        binder.bind("warn-low-level", "checkbutton-warn-low-level", key_callback=self.toggled_warn_low_level_cb)
        binder.bind("notify-high-level", "checkbutton-notify-high-level", key_callback=self.toggled_notify_high_level_cb)
        binder.bind("level-warn-low", "spinbutton-low-level", key_callback=refresh_message)
        binder.bind("level-notify-high", "spinbutton-high-level", key_callback=refresh_message)
        binder.bind("low-level-unit", "combobox-low-level", key_callback=self.combobox_low_level_unit_changed_cb)
        self.applet.settings.load_bindings(binder)

    def toggled_warn_low_level_cb(self, active):
        self.hbox_low_level.set_sensitive(active)

        self.__message_handler.evaluate()

    def toggled_notify_high_level_cb(self, active):
        self.hbox_high_level.set_sensitive(active)

        self.__message_handler.evaluate()

    def combobox_low_level_unit_changed_cb(self, value):
        self.__message_handler.evaluate()

    def combobox_battery_changed_cb(self, udi):
        batteries = self.backend.get_batteries()

        try:
            self.backend.set_active_udi(udi)

            self.check_status_cb()
        except ValueError:
            pass
            # TODO restore combobox
#            udi = self.backend.get_active_udi()
#            self.combobox_battery.set_active(batteries.values().index(batteries[udi]))

    def combobox_theme_changed_cb(self, value):
        if self.backend is not None:
            self.check_status_cb()
        else:
            self.set_battery_missing()

    def check_status_cb(self):
        if not self.backend.is_present():
            self.set_battery_missing()
            return

        charge_percentage = self.backend.get_capacity_percentage()
        power_type = _("AC") if self.backend.is_on_ac_power() else _("battery")
        charge_message = _("Computer running on %s power") % power_type

        if self.backend.is_charged():
            charge_message += "\n" + _("Battery charged")
            icon = os.path.join(themes_dir, self.applet.settings["theme"], "battery-charged.svg")
        else:
            is_charging = self.backend.is_charging()

            if is_charging:
                actoggle = "charging"
                time = self.backend.get_charge_time()
                title_message_suffix = _("until charged")
            else:
                actoggle = "discharging"
                time = self.backend.get_remaining_time()
                title_message_suffix = _("remaining")

            # May be None because charge rate is not always known (when switching between charging and discharging)
            if time is not None:
                charge_message += "\n" + self.format_time(time, suffix=title_message_suffix)

            level = [key for key, value in charge_ranges.iteritems() if charge_percentage <= value[0] and charge_percentage >= value[1]][0]
            icon = os.path.join(themes_dir, self.applet.settings["theme"], "battery-" + actoggle + "-" + level + ".svg")

        self.applet.tooltip.set(" ".join([charge_message, "(" + str(charge_percentage) + "%)"]))

        self.draw_icon(icon)
        self.__message_handler.evaluate()

    def draw_icon(self, icon):
        new_state = (icon, self.applet.get_size())
        if self.__previous_state == new_state:
            return

        self.__previous_state = new_state

        self.applet.icon.file(icon, size=awnlib.Icon.APPLET_SIZE)

    def is_battery_low(self):
        if not self.backend.is_discharging():
            return False

        unit = self.applet.settings["low-level-unit"]

        if unit == _("Percent") and self.backend.get_capacity_percentage() <= self.applet.settings["level-warn-low"]:
            return True

        time = self.backend.get_remaining_time()

        if time is None:
            return None

        hours, minutes = time
        return unit == _("Time Remaining") and hours == 0 and minutes <= self.applet.settings["level-warn-low"]

    def is_battery_high(self):
        if self.backend.is_discharging():
            return False

        return self.backend.get_capacity_percentage() >= self.applet.settings["level-notify-high"]

    def format_time(self, time, suffix=""):
        hours, minutes = time

        message = []
        time = []

        if hours > 0:
            if hours > 1:
                message.append(_("%d hours"))
            else:
                message.append(_("%d hour"))
            time.append(hours)
        if minutes > 0:
            if minutes > 1:
                message.append(_("%d minutes"))
            else:
                message.append(_("%d minute"))
            time.append(minutes)

        message = " ".join(message) % tuple(time)
        return " ".join([message, suffix]).strip() if len(message) > 0 else ""


class AbstractBackend(object):

    """Abstract backend that provides general implementations of some common methods.

    """

    def get_charge_time(self):
        assert self.is_charging()

        charge_rate = float(self.get_charge_rate())

        if charge_rate == 0.0:
            return None

        rate = (self.get_last_full_capacity() - self.get_remaining_capacity()) / charge_rate
        return (int(rate), int(rate * 60 % 60))

    def get_remaining_time(self):
        assert not self.is_charging()

        charge_rate = float(self.get_charge_rate())

        if charge_rate == 0.0:
            return None

        rate = self.get_remaining_capacity() / charge_rate
        return (int(rate), int(rate * 60 % 60))

    def get_capacity_percentage(self):
        return int(100 / (self.get_last_full_capacity() / float(self.get_remaining_capacity())))

    def is_charged(self):
        return not self.is_charging() and not self.is_discharging()

    def is_below_low_capacity(self):
        return self.get_remaining_capacity() <= self.get_warning_capacity()


class UPowerBackend(AbstractBackend):

    """Backend that uses UPower via DBus.

    Reference: http://upower.freedesktop.org/docs/Device.html

    """

    device_iface_name = "org.freedesktop.UPower.Device"

    devices = None

    def __init__(self):
        self.__system_bus = dbus.SystemBus()

        self.udi = UPowerBackend.get_batteries().keys()[0]
        self.__set_dbus_interface(self.udi)

    @staticmethod
    def backend_useable():
        return dbus is not None and len(UPowerBackend.get_batteries()) > 0

    @staticmethod
    def get_batteries():
        udi_models = {}

        try:
            system_bus = dbus.SystemBus()

            proxy = system_bus.get_object("org.freedesktop.UPower", "/org/freedesktop/UPower")
            interface = dbus.Interface(proxy, "org.freedesktop.UPower")

            UPowerBackend.devices = list(interface.EnumerateDevices())

            for udi in UPowerBackend.devices:
                device_iface = UPowerBackend.__get_dbus_interface(system_bus, udi)

                # Type 2 is battery (1 is AC, 3 is UPS)
                device_type = int(UPowerBackend.__get_property(device_iface, "Type"))
                is_present = bool(UPowerBackend.__get_property(device_iface, "IsPresent"))

                if device_type == 2 and is_present:
                    udi_models[str(udi)] = str(UPowerBackend.__get_property(device_iface, "Model"))
        except dbus.DBusException, e:
            print e.message
        finally:
            return udi_models

    def set_active_udi(self, udi):
        udi_models = UPowerBackend.get_batteries()

        assert udi in udi_models

        self.udi = udi
        self.__set_dbus_interface(udi)

    @staticmethod
    def __get_dbus_interface(system_bus, udi):
        proxy = system_bus.get_object("org.freedesktop.UPower", udi)
        return dbus.Interface(proxy, "org.freedesktop.DBus.Properties")

    def __set_dbus_interface(self, udi):
        self.__battery = UPowerBackend.__get_dbus_interface(self.__system_bus, udi)
    
    @staticmethod
    def __get_property(interface, property_name):
        return interface.Get(UPowerBackend.device_iface_name, property_name)

    def get_active_udi(self):
        return self.udi

    def is_present(self):
        return bool(UPowerBackend.__get_property(self.__battery, "IsPresent"))

    def is_charging(self):
        # State 1 is charging
        return int(UPowerBackend.__get_property(self.__battery, "State")) == 1

    def is_discharging(self):
        # State 2 is discharging
        return int(UPowerBackend.__get_property(self.__battery, "State")) == 2

    def get_last_full_capacity(self):
        # Measured in Wh
        return int(UPowerBackend.__get_property(self.__battery, "EnergyFull"))

    def get_remaining_capacity(self):
        # Measured in Wh
        return int(UPowerBackend.__get_property(self.__battery, "Energy"))

    def get_charge_rate(self):
        # Measured in W. Original value positive if being discharged, negative if being charged
        return abs(int(UPowerBackend.__get_property(self.__battery, "EnergyRate")))

    def get_capacity_percentage(self):
        # Percentage in range 0 .. 100
        return int(UPowerBackend.__get_property(self.__battery, "Percentage"))

    def get_warning_capacity(self):
        # Measured in Wh
        return int(int(UPowerBackend.__get_property(self.__battery, "EnergyFullDesign")) * (warning_percentage / 100.))

    def get_charge_time(self):
        assert self.is_charging()

        # Charge time in seconds
        time = int(UPowerBackend.__get_property(self.__battery, "TimeToFull"))

        if time == 0:
            return super(UPowerBackend, self).get_charge_time()

        hours = time / 3600
        seconds = time % 3600
        return (hours, int(round(seconds / 60.0)))

    def get_remaining_time(self):
        assert self.is_discharging()

        # Discharge time in seconds
        time = int(UPowerBackend.__get_property(self.__battery, "TimeToEmpty"))

        if time == 0:
            return super(UPowerBackend, self).get_discharge_time()

        hours = time / 3600
        seconds = time % 3600
        return (hours, int(round(seconds / 60.0)))

    def is_charged(self):
        # State 4 is fully charged
        return int(UPowerBackend.__get_property(self.__battery, "State")) == 4

    def is_on_ac_power(self):
        for udi in UPowerBackend.devices:
            device_iface = UPowerBackend.__get_dbus_interface(self.__system_bus, udi)

            # Property "Online" only has a value for AC power device
            if bool(UPowerBackend.__get_property(device_iface, "Online")):
                return True
        return False


class HalBackend(AbstractBackend):

    """Backend that uses HAL via DBus.

    """

    def __init__(self):
        self.udi = HalBackend.get_batteries().keys()[0]
        self.__set_dbus_interface(self.udi)

    @staticmethod
    def backend_useable():
        return dbus is not None and len(HalBackend.get_batteries()) > 0

    @staticmethod
    def get_batteries():
        udi_models = {}

        try:
            proxy = dbus.SystemBus().get_object("org.freedesktop.Hal", "/org/freedesktop/Hal/Manager")
            interface = dbus.Interface(proxy, "org.freedesktop.Hal.Manager")

            for udi in list(interface.FindDeviceByCapability("battery")):
                # TODO use dbus
                if commands.getoutput("hal-get-property --udi " + str(udi) + " --key battery.type") == "primary":
                    udi_models[str(udi)] = commands.getoutput("hal-get-property --udi " + str(udi) + " --key battery.model")
            return udi_models
        except dbus.DBusException, e:
            print e.message
            return udi_models

    def set_active_udi(self, udi):
        udi_models = HalBackend.get_batteries()

        assert udi in udi_models

        self.udi = udi
        self.__set_dbus_interface(udi)

    def __set_dbus_interface(self, udi):
        proxy = dbus.SystemBus().get_object("org.freedesktop.Hal", udi)
        self.__hal_battery = dbus.Interface(proxy, "org.freedesktop.Hal.Device")

    def get_active_udi(self):
        return self.udi

    def is_present(self):
        return bool(self.__hal_battery.GetProperty("battery.present"))

    def is_charging(self):
        return bool(self.__hal_battery.GetProperty("battery.rechargeable.is_charging"))

    def is_discharging(self):
        return bool(self.__hal_battery.GetProperty("battery.rechargeable.is_discharging"))

    def get_last_full_capacity(self):
        return int(self.__hal_battery.GetProperty("battery.charge_level.last_full"))

    def get_remaining_capacity(self):
        return int(self.__hal_battery.GetProperty("battery.charge_level.current"))

    def get_charge_rate(self):
        return int(self.__hal_battery.GetProperty("battery.charge_level.rate"))

    def get_capacity_percentage(self):
        return int(self.__hal_battery.GetProperty("battery.charge_level.percentage"))

    def get_warning_capacity(self):
        try:
            return int(self.__hal_battery.GetProperty("battery.charge_level.warning"))
        except dbus.DBusException:
            return int(int(self.__hal_battery.GetProperty("battery.charge_level.design")) * (warning_percentage / 100.))

    def is_on_ac_power(self):
        # TODO Should check that _all_ batteries are not discharging
        return not self.is_discharging()


backends = [UPowerBackend, HalBackend]


if __name__ == "__main__":
    awnlib.init_start(BatteryStatusApplet, {"name": applet_name,
        "short": "battery",
        "version": __version__,
        "description": applet_description,
        "theme": applet_theme_logo,
        "author": "onox, Randal Barlow",
        "copyright-year": "2008 - 2009",
        "authors": ["onox <denkpadje@gmail.com>", "Randal Barlow <im.tehk at gmail.com>"]})
