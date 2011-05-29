#!/usr/bin/python
# Copyright (C) 2008 - 2010  onox <denkpadje@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import stat
import subprocess

import pygtk
pygtk.require('2.0')
import gtk
from gtk import gdk

from awn.extras import _, awnlib, __version__

try:
    import dbus
    import dbus.service

    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
except ImportError:
    dbus = None
except dbus.DBusException:
    dbus = None

applet_name = _("CPU Frequency Monitor")
applet_description = _("An applet to monitor and control the CPU frequency")

# Themed logo of the applet, used as the applet's icon and shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "cpufreq.svg")

# Interval in seconds between two successive draws of the icon
draw_freq_interval = 0.5

sysfs_dir = "/sys/devices/system/cpu"
proc_cpuinfo_file = "/proc/cpuinfo"

ui_file = os.path.join(os.path.dirname(__file__), "cpufreq.ui")

dbus_bus_name = "org.awnproject.Awn.Applets.CpuFreq"
dbus_object_path = "/org/awnproject/Awn/Applets/CpuFreq"
dbus_object_interface = dbus_bus_name
dbus_object_interface_scaling = dbus_object_interface + ".Scaling"


if dbus is not None:
    class CpuFreqBackendDBusObject(dbus.service.Object):

        """A DBus object to read available frequencies and governors, current
        frequency and governor, and to set new frequency or governor.

        """

        def __init__(self, backend):
            self.__backend = backend

            bus = dbus.SessionBus()
            bus.request_name(dbus_bus_name)

            dbus.service.Object.__init__(self, bus, dbus_object_path + "/" + str(backend.get_cpu_nr()))

        @dbus.service.method(dbus_interface=dbus_object_interface, out_signature="b")
        def SupportsScaling(self):
            return self.__backend.supports_scaling()

        @dbus.service.method(dbus_interface=dbus_object_interface, out_signature="i")
        def GetCurrentFrequency(self):
            return self.__backend.get_current_frequency()

        @dbus.service.method(dbus_interface=dbus_object_interface, out_signature="ai")
        def GetFrequencies(self):
            return self.__backend.get_frequencies()

        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, out_signature="as")
        def GetGovernors(self):
            assert self.__backend.supports_scaling()

            return self.__backend.get_governors()

        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, out_signature="s")
        def GetCurrentGovernor(self):
            assert self.__backend.supports_scaling()

            return self.__backend.get_current_governor()

        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, in_signature="i")
        def SetFrequency(self, frequency):
            assert self.__backend.supports_scaling()

            return self.__backend.set_frequency(int(frequency))

        @dbus.service.method(dbus_interface=dbus_object_interface_scaling, in_signature="s")
        def SetGovernor(self, governor):
            assert self.__backend.supports_scaling()

            return self.__backend.set_governor(str(governor))


class CpuFreqApplet:

    """An applet to monitor and control the CPU frequency.

    """

    __button_press_event_id = None

    def __init__(self, applet):
        self.applet = applet

        self.dialog = None

        self.setup_icon()
        self.setup_context_menu()

        applet.tooltip.connect_becomes_visible(self.update_title)
        applet.connect_size_changed(self.size_changed_cb)

        applet.timing.register(self.draw_freq_cb, draw_freq_interval)
        self.draw_freq_cb()

        if dbus is not None:
            try:
                CpuFreqBackendDBusObject(self.backend)
            except dbus.DBusException:
                pass

    def initialize_backend(self, cpu_number):
        self.backend = None
        for b in backends:
            if b.backend_useable(cpu_number):
                self.backend = b(cpu_number)
                break

        assert self.backend is not None

        if self.backend.supports_scaling():
            """
            Compute the difference, R, (in KHz) between the physical maximum and
            minimum frequency. Then, if there are n images, we can split R into n-1
            frequency ranges and map the frequencies in those ranges to the various images
            """
            self.freq_range_per_image = (self.backend.get_phys_max_frequency() - self.backend.get_phys_min_frequency()) / (len(self.icon_states) - 1)
            assert self.freq_range_per_image > 0

        self.setup_main_dialog()

    def size_changed_cb(self):
        """Update the applet's icon to reflect the new height.

        """
        self.setup_icon()
        self.draw_freq_cb()

    def setup_icon(self):
        """Load the images that are going to be used as the applet's icon.

        """
        self.icon_states = {}
        for i in map(str, range(0, 14)):
            self.icon_states[i] = "cpufreq-%s" % i
        self.applet.theme.set_states(self.icon_states)
        self.applet.theme.theme("moonbeam")

    def setup_context_menu(self):
        number_of_cpus = SysFSBackend.get_number_of_cpus()  # called only once: assumes that every backend returns the same number

        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        combobox = prefs.get_object("combobox-cpu")
        awnlib.add_cell_renderer_text(combobox)
        for i in range(0, number_of_cpus):
            combobox.append_text(str(i))

        binder = self.applet.settings.get_binder(prefs)
        binder.bind("cpu_number", "combobox-cpu", key_callback=self.initialize_backend)
        self.applet.settings.load_bindings(binder)

        self.initialize_backend(self.applet.settings["cpu_number"])

        if number_of_cpus > 1:
            prefs.get_object("preferences-vbox").reparent(self.applet.dialog.new("preferences").vbox)

    def setup_main_dialog(self):
        if self.dialog is None:
            self.dialog = self.applet.dialog.new("main")
            self.vbox = gtk.VBox()
            self.dialog.add(self.vbox)
        else:
            self.vbox.foreach(gtk.Widget.destroy)

        if self.backend.supports_scaling():
            group = None
            self.radio_buttons = {}

            governors = self.backend.get_governors()

            if "userspace" in governors:
                governors.remove("userspace")

                for i in self.backend.get_frequencies():
                    group = gtk.RadioButton(group, self.human_readable_freqency(i))
                    group.props.can_focus = False
                    self.vbox.add(group)
                    self.radio_buttons[i] = group
                    group.connect("toggled", self.frequency_changed_cb, i)

                self.vbox.add(gtk.SeparatorMenuItem())

            for i in governors:
                group = gtk.RadioButton(group, i)
                group.props.can_focus = False
                self.vbox.add(group)
                self.radio_buttons[i] = group
                group.connect("toggled", self.governor_changed_cb, i)
        else:
            hbox = gtk.HBox(spacing=6)
            hbox.set_border_width(6)
            self.vbox.add(hbox)

            hbox.add(gtk.image_new_from_icon_name("dialog-information", gtk.ICON_SIZE_DIALOG))
            label = gtk.Label(_("<span size=\"large\"><b>Scaling unavailable</b></span>\n\nFrequency scaling is not\navailable for the selected CPU."))
            label.set_use_markup(True)
            hbox.add(label)

        if self.__button_press_event_id is not None:
            self.applet.disconnect(self.__button_press_event_id)
        self.__button_press_event_id = self.applet.connect("button-press-event", self.button_press_event_cb)

    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            if self.backend.supports_scaling() and not self.dialog.is_active():
                governor = self.backend.get_current_governor()

                if governor == "userspace":
                    active_item = self.radio_buttons[self.backend.get_current_frequency()]
                    callback = self.frequency_changed_cb
                else:
                    active_item = self.radio_buttons[governor]
                    callback = self.governor_changed_cb
                active_item.handler_block_by_func(callback)
                active_item.set_active(True)
                active_item.handler_unblock_by_func(callback)

    def human_readable_freqency(self, frequency):
        frequency = float(frequency)

        if frequency >= 1e6:
            divisor = 1e6
            unit = _("GHz")
        else:
            divisor = 1e3
            unit = _("MHz")

        if frequency % divisor == 0:
            ffreq = str(int(frequency / divisor))
        else:
            ffreq = "%3.2f" % (frequency / divisor)

        return ffreq + " " + unit

    def frequency_changed_cb(self, widget, frequency):
        """Set the governor to 'userspace' and changes the current frequency.

        """
        if widget.get_active():
            self.backend.set_frequency(frequency)

            self.applet.dialog.toggle("main", "hide")
            self.applet.tooltip.hide()

    def governor_changed_cb(self, widget, governor):
        """Change the current governor.

        """
        if widget.get_active():
            self.backend.set_governor(governor)

            self.applet.dialog.toggle("main", "hide")
            self.applet.tooltip.hide()

    def draw_freq_cb(self):
        """Draw the icon and updates the title to keep it synchronized with the drawn frequency.

        """
        if self.backend.supports_scaling():
            number = float(self.backend.get_current_frequency() - self.backend.get_phys_min_frequency()) / self.freq_range_per_image
            icon = int(round(number))
        else:
            icon = len(self.icon_states) - 1
        self.applet.theme.icon(str(icon))

        self.update_title()

        return True

    def update_title(self):
        if not self.applet.tooltip.is_visible():
            return

        title = self.human_readable_freqency(self.backend.get_current_frequency())

        if self.backend.supports_scaling():
            title = self.backend.get_current_governor() + ": " + title

        self.applet.tooltip.set(title)


class SysFSBackend:

    """Backend using the syfs filesystem. Requires Linux 2.6 and the
    cpufreq-selector program from gnome-applets.

    """

    __selector_binary = "cpufreq-selector"
    __scaling_files = ["scaling_available_governors", "scaling_available_frequencies", "scaling_governor"]

    def __init__(self, cpu_nr):
        self.__cpu_nr = cpu_nr
        self.__command = self.__selector_binary

        self.__supports_scaling = self.__can_support_scaling()

    @staticmethod
    def backend_useable(cpu_nr):
        return os.path.isdir(os.path.join(sysfs_dir, "cpu" + str(cpu_nr), "cpufreq"))

    def supports_scaling(self):
        return self.__supports_scaling

    def __can_support_scaling(self):
        cpufreq_dir = os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq")

        if not all(os.path.isfile(os.path.join(cpufreq_dir, f)) for f in self.__scaling_files):
            return False
        if len(self.get_frequencies()) <= 1:
            return False
        if not self.__has_freq_selector():
            return False
        return True

    def __has_freq_selector(self):
        get_path = lambda d: os.path.join(d, self.__selector_binary)
        paths = [get_path(i) for i in os.environ["PATH"].split(":") if os.access(get_path(i), os.X_OK)]

        if len(paths) == 0:
            return False
        if os.stat(paths[0])[stat.ST_MODE] & stat.S_ISUID == stat.S_ISUID:
            return True
        p = subprocess.Popen(self.__selector_binary, stderr=subprocess.PIPE)
        out, err = p.communicate()
        return err.find('org.gnome.CPUFreqSelector') >= 0

    def get_cpu_nr(self):
        return self.__cpu_nr

    @staticmethod
    def get_number_of_cpus():
        pattern = re.compile("cpu\d")
        return len([i for i in os.listdir(sysfs_dir) if pattern.match(i)])

    def get_governors(self):
        return open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq/scaling_available_governors")).read().strip().split()

    def get_frequencies(self):
        return map(int, open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq/scaling_available_frequencies")).read().strip().split())

    def set_governor(self, governor):
        assert governor in self.get_governors(), "Governor '" + governor + "' unknown"

        subprocess.Popen(self.__command + " -c %d -g %s" % (self.__cpu_nr, governor), shell=True)

    def set_frequency(self, frequency):
        assert frequency in self.get_frequencies(), "Frequency " + str(frequency) + " invalid"

        subprocess.Popen(self.__command + " -c %d -g userspace -f %d " % (self.__cpu_nr, frequency), shell=True)

    def get_current_governor(self):
        return open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq/scaling_governor")).read().strip()

    def get_current_frequency(self):
        return self.__read_frequency("scaling_cur_freq")

    def get_phys_min_frequency(self):
        return self.__read_frequency("cpuinfo_min_freq")

    def get_phys_max_frequency(self):
        return self.__read_frequency("cpuinfo_max_freq")

    def __read_frequency(self, file):
        return int(open(os.path.join(sysfs_dir, "cpu" + str(self.__cpu_nr), "cpufreq", file)).read().strip())


class ProcCPUInfoBackend:

    """Backend using /proc/cpuinfo. Does not provide the ability to scale
    the CPU frequency.

    """

    __cpuinfo_pattern = pattern = re.compile("cpu MHz\s+: (\d+\.\d+)")

    def __init__(self, cpu_nr):
        self.__cpu_nr = cpu_nr

    @staticmethod
    def backend_useable(cpu_nr):
        if not os.path.isfile(proc_cpuinfo_file):
            return False
        return re.compile("processor\s+: %d" % cpu_nr).search(open(proc_cpuinfo_file).read()) is not None

    def supports_scaling(self):
        return False

    def get_cpu_nr(self):
        return self.__cpu_nr

    @staticmethod
    def get_number_of_cpus():
        file = open(proc_cpuinfo_file).read()
        return len(ProcCPUInfoBackend.__cpuinfo_pattern.findall(file))

    def get_frequencies(self):
        return [self.get_current_frequency()]

    def get_current_frequency(self):
        file = open(proc_cpuinfo_file).read()
        # Multiply by 1000 because value is in MHz and should be in KHz
        return int(float(self.__cpuinfo_pattern.findall(file)[self.__cpu_nr])) * 1000


backends = [SysFSBackend, ProcCPUInfoBackend]


if __name__ == "__main__":
    awnlib.init_start(CpuFreqApplet, {"name": applet_name,
        "short": "cpufreq",
        "version": __version__,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": "2008 - 2010",
        "authors": ["onox <denkpadje@gmail.com>"]})
