#!/usr/bin/python
#coding: utf-8
#
#   Copyright 2008-2009 Grega Podlesek <grega.podlesek@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#   MA 02110-1301, USA.
#
# @version: 0.3.9

import os

import gtk

from awn.extras import _, awnlib, __version__
from awn import OverlayText

from desktopagnostic import Color

from interfaces import sensorinterface
from interfaces import acpisensors
from interfaces import omnibooksensors
from interfaces import hddtempsensors
from interfaces import lmsensors
from interfaces import nvidiasensors
from interfaces import nvclocksensors

from sensorvalues.tempvalue import TempValue
from sensorvalues.rpmvalue import RPMValue
from sensorvalues.voltvalue import VoltValue

from sensorvalues import units
from sensoricon import SensorIcon

applet_name = "Hardware Sensors"
short_name = "hardware-sensors"
applet_description = _("Applet to show the hardware sensors readouts")

# Applet's logo, used as the applet's icon and shown in the GTK About dialog
theme_dir = os.path.join(os.path.dirname(__file__), "themes")
applet_logo = os.path.join(os.path.dirname(__file__), "images/thermometer.svg")
no_sensors_icon = os.path.join(os.path.dirname(__file__),
                                                       "images/no_sensors.svg")
ui_file = os.path.join(os.path.dirname(__file__), "hardware-sensors.ui")

single_font_sizes = [11, 17, 22]
double_font_sizes = [12, 16, 20]
font_size_names = ["Small", "Medium", "Large"]

class SensorsApplet:
    """
    Applet to show the hardware sensors readouts.
    
    """

    def __init__(self, applet):
        """
        Initialize the entire applet.
        
        Create applet icon and main dialog, initialize sensors and load
        settings.
        
        """
        self.applet = applet

        # Init sensors
        no_sensors = not self.create_all_sensors()

        # If no sensors were found, display warning massage and icon, then exit
        if no_sensors:
            message = _("Warning: No sensors found. Install one or more of \
ACPI, HDDTemp, LM-Sensors and restart the applet.")

            print message

            # Show massage with awn notify
            self.applet.notify.send(subject=None, body=message, icon="")
            # Show "no sensors found" icon
            self.applet.icon.file(no_sensors_icon, size=applet.get_size())
            self.applet.tooltip.set(message)
            return

        self.update_all_sensors()

        # Get a list of themes
        def is_dir(path):
            return os.path.isdir(os.path.join(theme_dir, path))

        self.__themes = filter(is_dir, os.listdir(theme_dir))
        self.__themes = [theme.replace("_", " ") for theme in self.__themes]
        self.__themes.sort()

        # == Settings == #
        # Load settings, setup rightclick menu and create settings dialog
        self.setup_preferences()

        # == Icon == #
        self.setup_icon()

        # Recreate upon awn height change
        self.applet.connect_size_changed(self.height_changed_cb)

        # == Dialog == #
        # Create main applet dialog showing selected sensors.
        main_dialog = self.applet.dialog.new("main", _("Sensors"))
        self.__main_dialog = self.MainDialog(self, main_dialog)


    # == Sensors == #
    def create_all_sensors(self):
        """
        Initialize sensors for all interfaces. Return False if no sensors are
        found.
        
        """
        self.sensors = []
        self.sensors += acpisensors.get_sensors()
        self.sensors += omnibooksensors.get_sensors()
        self.sensors += hddtempsensors.get_sensors()
        self.sensors += lmsensors.get_sensors()
        self.sensors += nvidiasensors.get_sensors()
        self.sensors += nvclocksensors.get_sensors()

        # Check if any sensors were found
        if self.sensors == []:
            return False

        # Connect all the sensors to alarm callback function
        for sensor in self.sensors:
            sensor.connect_to_alarm(self.alarm_cb)

        return True

    def recreate_main_sensors(self):
        """
        Fill self.main_sensors with sensors that should be shown in the applet
        icon.
        
        """
        self.main_sensors = []
        for sensor in self.sensors:
            if sensor.in_icon:
                self.main_sensors.append(sensor)
        self.__icon.set_sensors(self.main_sensors)

    def update_all_sensors(self):
        """Update all of the sensor values."""
        for sensor in self.sensors:
            sensor.read_sensor()


    # == Applet icon == #
    def setup_icon(self):
        """
        Create icon, create overlay, run the first icon update and start icon
        timer.
        
        """
        self.__icon = SensorIcon(self.applet.settings["theme"],
                                 self.main_sensors,
                                 self.applet.get_size(),
                                 self.applet.settings["hand_color"])

        # Create text overlay
        self.__temp_overlay = OverlayText()
        self.change_font_size(self.applet.settings["font_size"])
        self.__temp_overlay.props.active = self.applet.settings["show_value_overlay"]
        self.applet.add_overlay(self.__temp_overlay)

        self.__old_values = None
        # Call the first update and start the updater
        self.update_icon()
        self.__icon_timer = self.applet.timing.register(
                                    self.update_icon, self.applet.settings["timeout"])

    def update_icon_type(self):
        """Updates icon type"""
        if len(self.main_sensors) is 1:
            self.__icon.type("single")
        else:
            self.__icon.type("double")
        self.change_font_size(self.applet.settings["font_size"])
        self.update_icon(True)

    def update_icon(self, force=False):
        """
        Update applet icon to show the updated values.
        
        """
        for main_sensor in self.main_sensors:
            main_sensor.read_sensor()
        values = [sensor.value for sensor in self.main_sensors]
        # Check if values have changed
        if values != self.__old_values or force:
            self.__old_values = values

            # Get updated icon
            context = self.__icon.get_icon()
            # Set updated icon
            self.applet.icon.set(context)

            # Update overlay
            if len(values) is 1:
                overlay_text = str(values[0])
            else:
                overlay_text = str(values[0]) + " " + str(values[1])

            self.__temp_overlay.props.text = overlay_text

            # Update title
            title = "   ".join(["%s: %d %s" % (s.label, s.value, s.unit_str)
                                                   for s in self.main_sensors])
            self.applet.tooltip.set(title)


    # == Settings == #
    def setup_preferences(self):
        """
        Load global and sensor settings and replace them with defaults if
        not set.
        
        """
        # Setup the rightclick context menu.
        self.__pref_dialog = self.applet.dialog.new("preferences")
        self.__pref_dialog.set_resizable(True)

        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)
        prefs.get_object("notebook").reparent(self.__pref_dialog.vbox)

        # = General settings = #

        self.setup_general_preferences(prefs)

        # Bind settings to the gtk+ widgets that control them and callbacks
        # that should be called on setting change.
        binder = self.applet.settings.get_binder(prefs)
        binder.bind("unit", "combobox_unit", key_callback=self.change_unit)
        binder.bind("timeout", "spin_timeout", key_callback=self.change_timeout)
        binder.bind("theme", "combobox_theme", key_callback=self.change_theme)
        binder.bind("show_value_overlay", "checkbutton_show_value_overlay",
                                   key_callback=self.change_show_value_overlay)
        binder.bind("font_size", "combobox_font_size",
                                   key_callback=self.change_font_size)
        binder.bind("hand_color", "colorbutton_hand",
                                   key_callback=self.change_hand_color)
        self.applet.settings.load_bindings(binder)

        # Set the color of the hand color colorbutton
        cb_hand = prefs.get_object("colorbutton_hand")
        cb_hand.set_da_color(self.applet.settings["hand_color"])

        # = Sensor settings = #

        # Copy to local variable for easy and fast access
        sensors = self.sensors

        sensor_default_settings = {
            # Sensor settings
            "ids": [str(sensor.id) for sensor in sensors],
            "labels": [sensor.label for sensor in sensors],
            "show": [sensor.show for sensor in sensors],
            "dialog_row": range(1, len(sensors) + 1),
            "in_icon": [sensor.in_icon for sensor in sensors],
            "high_values": [sensor.high_value for sensor in sensors],
            "low_values": [sensor.low_value for sensor in sensors],
            "high_alarms": [sensor.alarm_on_high for sensor in sensors],
            "low_alarms": [sensor.alarm_on_low for sensor in sensors]
        }

        # Load settings and replace with defaults if not set.
        for key, value in sensor_default_settings.iteritems():
            if key not in self.applet.settings:
                self.applet.settings[key] = value

        # Copy to local variable for easy and fast access
        settings = self.applet.settings

        self.main_sensors = []
        new_sensors = False

        # Apply settings to sensors.
        for sensor in self.sensors:
            sensor.unit = settings["unit"]
            if str(sensor.id) in settings["ids"]:
                idx = settings["ids"].index(str(sensor.id))
                sensor.label = settings["labels"][idx]
                sensor.show = settings["show"][idx]
                sensor.dialog_row = settings["dialog_row"][idx]
                sensor.in_icon = settings["in_icon"][idx]
                sensor.raw_high_value = settings["high_values"][idx]
                sensor.raw_low_value = settings["low_values"][idx]
                sensor.alarm_on_high = settings["high_alarms"][idx]
                sensor.alarm_on_low = settings["low_alarms"][idx]
            else:
                new_sensors = True
            if sensor.in_icon:
                self.main_sensors.append(sensor)
            # Set timeout for updaters.
            if sensor.interface in [lmsensors.interface_name,
                                    nvidiasensors.interface_name]:
                sensor.updater.set_timeout(settings["timeout"])

        # If a sensor was lost, a new one found or if the order was changed
        if new_sensors or \
          len(sensors) != len(settings["ids"]) or \
          [str(sensor.id) for sensor in sensors] != settings["ids"]:

            # Sort sensors by dialog_row and renumber them in that order (to
            # eliminate any 'holes' in row order left by lost sensors and to
            # put the new sensors to the end).
            sorted_sensors = [sensor for sensor in sensors]
            sorted_sensors.sort(key=lambda s: s.dialog_row)
            # Renumber rows
            for row, sensor in enumerate(sorted_sensors):
                sensor.dialog_row = row + 1

            # Save all sensor settings.
            settings = self.applet.settings
            settings["ids"] = [str(sensor.id) for sensor in sensors]
            settings["labels"] = [sensor.label for sensor in sensors]
            settings["show"] = [sensor.show for sensor in sensors]
            settings["dialog_row"] = [sensor.dialog_row for sensor in sensors]
            settings["in_icon"] = [sensor.in_icon for sensor in sensors]
            settings["high_values"] = [s.high_value for s in sensors]
            settings["low_values"] = [s.low_value for s in sensors]
            settings["high_alarms"] = [s.alarm_on_high for s in sensors]
            settings["low_alarms"] = [s.alarm_on_low for s in sensors]

        # If none of the saved sensors has been selected as main, set default.
        if not self.main_sensors:
            # The default for the main sensor is the first sensor.
            sensors[0].in_icon = True
            self.main_sensors.append(sensors[0])
            self.applet.settings["in_icon"] = \
                                         [sensor.in_icon for sensor in sensors]

        if self.applet.settings["theme"] not in self.__themes:
            self.__icon = None
            self.applet.settings["theme"] = self.__themes[0]

        self.setup_sensor_preferences(prefs)

    def setup_general_preferences(self, prefs):
        """Setup the main settings window."""
        # Unit combobox
        unit_combobox = prefs.get_object("combobox_unit")
        awnlib.add_cell_renderer_text(unit_combobox)
        for i in units.UNIT_STR_LONG[:3]:
            unit_combobox.append_text(i)

        # Theme combobox
        theme_combobox = prefs.get_object("combobox_theme")
        awnlib.add_cell_renderer_text(theme_combobox)
        for theme in self.__themes:
            # Add filename with '_' replaced width space
            theme_combobox.append_text(theme)
        # If the set theme is not available, revert to default 
        if self.applet.settings["theme"] not in self.__themes:
            self.__icon = None
            self.applet.settings["theme"] = self.__themes[0]

        # Font size combobox
        font_combobox = prefs.get_object("combobox_font_size")
        awnlib.add_cell_renderer_text(font_combobox)
        for font_size in font_size_names:
            font_combobox.append_text(font_size)

        # Font size combobox should be grayed out when value overlay is
        # disabled
        show_checkbutton = prefs.get_object("checkbutton_show_value_overlay")
        fontsize_hbox = prefs.get_object("hbox_font_size")
        fontsize_hbox.set_sensitive(show_checkbutton.get_active())
        show_checkbutton.connect("toggled", lambda w:
                                   fontsize_hbox.set_sensitive(w.get_active()))

    def setup_sensor_preferences(self, prefs):
        """Setup the sensor settings tab part of window."""
        # All sensors treeview
        treeview_all = prefs.get_object("treeview_sensors")
        # Main sensors treeview
        treeview_main = prefs.get_object("treeview_main_sensors")

        self.setup_sensors_treeview(treeview_all)
        self.setup_main_sensors_treeview(treeview_main)

        # Properties button
        button_properties = prefs.get_object("button_properties")
        button_properties.connect('clicked', self.properties_cb, treeview_all)

        # Add button
        button_add = prefs.get_object("button_add")
        button_add.connect('clicked', self.add_cb, treeview_all)

        # Remove button
        button_remove = prefs.get_object("button_remove")
        button_remove.connect('clicked', self.remove_cb, treeview_main)

        # Up button
        button_up = prefs.get_object("button_up")
        button_up.connect('clicked', self.up_cb, treeview_all)

        # Down button
        button_down = prefs.get_object("button_down")
        button_down.connect('clicked', self.down_cb, treeview_all)

    def setup_sensors_treeview(self, treeview):
        """Create treeview with list of all sensors and their settings."""
        self.__liststore = gtk.ListStore(
                            int, int, str, str, str, 'gboolean', 'gboolean')
        self.__column_idx = 0
        self.__column_row = 1
        self.__column_interface = 2
        self.__column_name = 3
        self.__column_label = 4
        self.__column_show = 5
        self.__column_in_icon = 6

        # Fill liststore with data
        for idx, sensor in enumerate(self.sensors):
            # Add a row to liststore
            last = self.__liststore.append([idx,
                                          sensor.dialog_row,
                                          sensor.interface,
                                          sensor.name,
                                          sensor.label,
                                          sensor.show,
                                          sensor.in_icon])

        # Set TreeView's liststore
        treeview.set_model(self.__liststore)

        # Create a CellRendererText to render the data
        cell_row = gtk.CellRendererText()
        cell_interface = gtk.CellRendererText()
        cell_name = gtk.CellRendererText()
        cell_label = gtk.CellRendererText()
        cell_show = gtk.CellRendererToggle()

        # Set labels to be editable
        cell_label.set_property('editable', True)
        # Make toggle buttons in the show column activatable
        cell_show.set_property('activatable', True)

        # Connect the edited event
        cell_label.connect('edited', self.label_edited_cb)
        # Connect the toggle event
        cell_show.connect('toggled', self.show_toggled_cb)

        # Create the TreeViewColumns to display the data, add the cell renderer
        # and set the cell "text" attribute to correct column (treeview
        # retrieves text from that column in liststore)
        tvcolumn_row = gtk.TreeViewColumn("#", cell_row,
                                          text=self.__column_row,
                                          visible=self.__column_show)
        tvcolumn_interface = gtk.TreeViewColumn(_("Interface"), cell_interface,
                                                  text=self.__column_interface)
        tvcolumn_name = gtk.TreeViewColumn(_("Name"), cell_name,
                                                       text=self.__column_name)
        tvcolumn_label = gtk.TreeViewColumn(_("Label"), cell_label,
                                                      text=self.__column_label)
        # Set the cell "active" attribute to column_show - retrieve the state
        # of the toggle button from that column in liststore
        tvcolumn_show = gtk.TreeViewColumn(_("In dialog"), cell_show,
                                                     active=self.__column_show)

        # Add treeview columns to treeview
        treeview.append_column(tvcolumn_row)
        treeview.append_column(tvcolumn_interface)
        treeview.append_column(tvcolumn_name)
        treeview.append_column(tvcolumn_label)
        treeview.append_column(tvcolumn_show)

        # Make name and label searchable
        treeview.set_search_column(self.__column_name)
        treeview.set_search_column(self.__column_label)

        # Allow sorting on the column
        tvcolumn_row.set_sort_column_id(self.__column_row)
        tvcolumn_interface.set_sort_column_id(self.__column_interface)
        tvcolumn_name.set_sort_column_id(self.__column_name)
        tvcolumn_label.set_sort_column_id(self.__column_label)
        tvcolumn_show.set_sort_column_id(self.__column_show)

        # Sort by dialog_row
        self.__liststore.set_sort_column_id(self.__column_row,
                                          gtk.SORT_ASCENDING)

    def setup_main_sensors_treeview(self, treeview):
        """Create treeview with list of sensors to be shown in applet icon."""
        # List store for main sensors
        model_filter = self.__liststore.filter_new()
        model_filter.set_visible_column(self.__column_in_icon)

        # Set main sensor treeview's liststore
        treeview.set_model(model_filter)

        # Create a CellRendererText to render the data
        cell_label = gtk.CellRendererText()

        # Add treeview-column to treeview
        tvcolumn_label = gtk.TreeViewColumn(_("Sensors displayed in icon"),
                                          cell_label, text=self.__column_label)
        treeview.append_column(tvcolumn_label)

    def create_properties_dialog(self, sensor):
        """
        Create a dialog with individual sensors settings.
        
        Create a dialog with settings for high and low values and alarms for
        the given sensor
        @param prefs: opened glade XML file
        @param sensor: the sensor for which this settings dialog is for
        
        """
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        prop_dialog = prefs.get_object("sensor_properties_dialog")
        prop_dialog.set_title(sensor.label + " - " + _("properties"))
        prop_dialog.set_icon(self.__pref_dialog.get_icon())
        # Properties window should be on top of settings window
        prop_dialog.set_transient_for(self.__pref_dialog)

        # Get sensor value's type
        value_type = sensor.type

        # Adjustment for sensor high value spin button
        spin_button = prefs.get_object("spin_high_value")
        if value_type is TempValue:
            if sensor.unit == units.UNIT_CELSIUS:
                adj = gtk.Adjustment(sensor.high_value, -273, 200, 1, 10)
            elif sensor.unit == units.UNIT_FAHRENHEIT:
                adj = gtk.Adjustment(sensor.high_value, -460, 392, 1, 10)
            elif sensor.unit == units.UNIT_KELVIN:
                adj = gtk.Adjustment(sensor.high_value, 0, 473, 1, 10)
        elif value_type is RPMValue:
            adj = gtk.Adjustment(sensor.high_value, 0, 20000, 100, 1000)
        elif value_type is VoltValue:
            adj = gtk.Adjustment(sensor.high_value, -20, 20, 0.05, 1)
            spin_button.set_digits(2)

        # Set adjustment
        spin_button.set_adjustment(adj)
        spin_button.set_value(sensor.high_value)

        adj.connect('value-changed', lambda adjustment:
                        self.change_high_value(sensor, adjustment.get_value()))

        # Adjustment for sensor low value spin button
        spin_button = prefs.get_object("spin_low_value")
        if value_type is TempValue:
            if sensor.unit == units.UNIT_CELSIUS:
                adj = gtk.Adjustment(sensor.low_value, -273, 200, 1, 10)
            elif sensor.unit == units.UNIT_FAHRENHEIT:
                adj = gtk.Adjustment(sensor.low_value, -460, 392, 1, 10)
            elif sensor.unit == units.UNIT_KELVIN:
                adj = gtk.Adjustment(sensor.low_value, 0, 473, 1, 10)
        elif value_type is RPMValue:
            adj = gtk.Adjustment(sensor.low_value, 0, 20000, 100, 1000)
        elif value_type is VoltValue:
            adj = gtk.Adjustment(sensor.low_value, -20, 20, 0.05, 1)
            spin_button.set_digits(2)

        # Set adjustment
        spin_button.set_adjustment(adj)
        spin_button.set_value(sensor.low_value)

        adj.connect('value-changed', lambda adjustment:
                        self.change_low_value(sensor, adjustment.get_value()))

        # "Enable high alarm" CheckButton
        alarm_cbutton = prefs.get_object("check_high_alarm")
        alarm_cbutton.set_active(sensor.alarm_on_high)
        alarm_cbutton.connect('toggled', lambda w:
                                                self.toggle_high_alarm(sensor))

        # "Enable low alarm" CheckButton
        alarm_cbutton = prefs.get_object("check_low_alarm")
        alarm_cbutton.set_active(sensor.alarm_on_low)
        alarm_cbutton.connect('toggled', lambda w:
                                                 self.toggle_low_alarm(sensor))

        # Close button
        close_button = prefs.get_object("close_properties")
        close_button.connect('clicked', lambda w: prop_dialog.destroy())

        prop_dialog.show_all()


    # === Event handlers === #
    def alarm_cb(self, sensor, message):
        """Show alarm message with awn notify."""
        self.applet.notify.send(subject=None, body=message, icon=applet_logo)

    def height_changed_cb(self):
        """Update the applet's icon to reflect the new height."""
        self.__icon.set_height(self.applet.get_size())
        # Force icon update
        self.update_icon(True)

    # === Change setting methods === #
    def change_unit(self, unit):
        """Change unit for all sensors and update icon."""
        for sensor in self.sensors:
            sensor.unit = unit
        self.update_icon(True)

    def change_font_size(self, size_idx):
        """Change font size for overlay."""
        if len(self.main_sensors) is 1:
            self.__temp_overlay.props.font_sizing = single_font_sizes[size_idx]
            self.__temp_overlay.props.y_override = \
                                          30 + size_idx if size_idx < 2 else 28
        else:
            self.__temp_overlay.props.font_sizing = double_font_sizes[size_idx]
            self.__temp_overlay.props.y_override = \
                                          30 + size_idx if size_idx < 2 else 29

    def change_theme(self, theme):
        """Save theme setting and update icon."""
        if self.__icon is None:
            return
        self.__icon.theme(theme)
        # Force icon change
        self.update_icon(True)

    def change_show_value_overlay(self, show_value_overlay):
        """Change whether to show the valu in applet icon"""
        self.__temp_overlay.props.active = show_value_overlay

    def change_timeout(self, timeout):
        """Save timeout setting and change timer to new timeout."""
        self.update_icon(True)
        self.__icon_timer.change_interval(timeout)
        self.__main_dialog.change_interval(timeout)
        for sensor in self.sensors:
            # Set timeout for updaters
            if sensor.interface in [lmsensors.interface_name,
                                    nvidiasensors.interface_name]:
                sensor.updater.set_timeout(timeout)

    def change_high_value(self, sensor, value):
        """Save high value setting for a specific sensor and update icon."""
        # Apply high value change
        sensor.high_value = value
        # Save high values
        self.applet.settings["high_values"] = \
                                       [s.raw_high_value for s in self.sensors]
        if sensor in self.main_sensors:
            # Force icon update
            self.update_icon(True)

    def change_low_value(self, sensor, value):
        """Save low value setting for a specific sensor and update icon."""
        # Apply low value change
        sensor.low_value = value
        # Save low values
        self.applet.settings["low_values"] = \
                                        [s.raw_low_value for s in self.sensors]
        if sensor in self.main_sensors:
            # Force icon update
            self.update_icon(True)

    def change_in_icon(self, sensor, in_icon):
        """Save in_icon setting for a specific sensor and update icon."""
        # Apply in_icon value change
        sensor.in_icon = in_icon
        # Save in_icon values
        self.applet.settings["in_icon"] = \
                                   [sensor.in_icon for sensor in self.sensors]
        self.recreate_main_sensors()
        # Force icon update
        self.update_icon(True)

    def change_hand_color(self, color):
        """Apply hand color setting and update icon."""
        self.__icon.set_hand_color(color)
        # Force icon update
        self.update_icon(True)

    def update_dialog_rows(self):
        """
        Save dialog row setting and update main dialog.
        
        """
        # Save dialog_row values
        self.applet.settings["dialog_row"] = \
                                [sensor.dialog_row for sensor in self.sensors]
        # Recreate dialog
        self.__main_dialog.recreate()

    def toggle_high_alarm(self, sensor):
        """Toggle high alarm for a specific sensor and save it."""
        sensor.toggle_alarm_on_high()
        self.applet.settings["high_alarms"] = \
                             [sensor.alarm_on_high for sensor in self.sensors]

    def toggle_low_alarm(self, sensor):
        """Toggle low alarm for a specific sensor and save it."""
        sensor.toggle_alarm_on_low()
        self.applet.settings["low_alarms"] = \
                              [sensor.alarm_on_low for sensor in self.sensors]


    # === Treeview callbacks === #
    def label_edited_cb(self, cell_renderer, path, new_text):
        """
        Change specific sensor's label, save it and update dialog and icon.
        
        """
        # Change label value in liststore
        self.__liststore[path][self.__column_label] = new_text
        sensor = self.sensors[self.__liststore[path][self.__column_idx]]
        # Apply change to sensor
        sensor.label = new_text
        # Save labels
        self.applet.settings["labels"] = \
                                    [sensor.label for sensor in self.sensors]
        # Recreate dialog
        self.__main_dialog.recreate()

    def show_toggled_cb(self, cell_renderer, path):
        """
        Toggle specific sensor's "show in dialog" properity, save it and update
        dialog.
        
        """
        store = self.__liststore
        sensor = self.sensors[store[path][self.__column_idx]]

        # Toggle value in liststore
        store[path][self.__column_show] = not store[path][self.__column_show]
        # Apply change to sensor
        sensor.show = store[path][self.__column_show]
        # Save show property
        self.applet.settings["show"] = [sensor.show for sensor in self.sensors]
        # Recreate dialog
        self.__main_dialog.recreate()

    # === Button callbacks === #
    def properties_cb(self, widget, treeview):
        """Open properties dialog for selected sensor."""
        # Get selected sensor
        treeselection = treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        # Something must be selected
        if iter is not None:
            # Sensor index
            idx = model[iter][self.__column_idx]
            self.create_properties_dialog(self.sensors[idx])

    def add_cb(self, widget, treeview_all):
        """
        Add selected sensors to main sensors (i.e. shown them in applet icon).
        
        """
        # Get selected sensor
        selection = treeview_all.get_selection()
        (model, iter) = selection.get_selected()
        # Something must be selected
        if iter is not None:
            # Sensor index
            idx = self.__liststore[iter][self.__column_idx]
            # Apply setting
            self.change_in_icon(self.sensors[idx], True)
            # Change value in model
            model[iter][self.__column_in_icon] = True
        self.update_icon_type()

    def remove_cb(self, widget, treeview_main):
        """
        Remove selected sensors from main sensors (i.e. do not shown them in
        applet icon).
        
        """
        # Get selected sensor
        selection = treeview_main.get_selection()
        (model_filter, iter) = selection.get_selected()
        # Something must be selected and at least one sensor must remain
        if iter is not None and len(treeview_main.get_model()) > 1:
            child_iter = model_filter.convert_iter_to_child_iter(iter)
            # Sensor index
            idx = self.__liststore[child_iter][self.__column_idx]
            # Apply setting
            self.change_in_icon(self.sensors[idx], False)
            # Change value in model
            self.__liststore[child_iter][self.__column_in_icon] = False
        self.update_icon_type()

    def up_cb(self, widget, treeview):
        """
        Move selected sensors up in main applet dialog.
        
        """
        # Get selected sensor
        selection = treeview.get_selection()
        (model, iter) = selection.get_selected()

        # Something must be selected
        if iter is not None:
            dialog_row = model[iter][self.__column_row]
            if dialog_row > 1:
                # Iterator pointing to predecessor (sensor/row that has
                # dialog_row one less than this one)
                row_pred = None
                for row in model:
                    if row[self.__column_row] == dialog_row - 1:
                        row_pred = row
                        break
                if row_pred is not None:
                    # Switch model_row-s
                    model[iter][self.__column_row] = dialog_row - 1
                    row_pred[self.__column_row] = dialog_row

                    # Apply setting
                    sensor = self.sensors[model[iter][self.__column_idx]]
                    sensor_pred = self.sensors[row_pred[self.__column_idx]]
                    sensor.dialog_row = dialog_row - 1
                    sensor_pred.dialog_row = dialog_row
                    self.update_dialog_rows()

    def down_cb(self, widget, treeview):
        """
        Move selected sensors down in the main applet dialog.
        
        """
        # Get selected sensor
        selection = treeview.get_selection()
        (model, iter) = selection.get_selected()
        # Something must be selected
        if iter is not None:
            dialog_row = model[iter][self.__column_row]
            if dialog_row < len(self.sensors):
                # Iter pointing to predecessor (sensor/row that has dialog_row
                # one less than this one)
                row_pred = None
                for row in model:
                    if row[self.__column_row] == dialog_row + 1:
                        row_pred = row
                        break
                if row_pred is not None:
                # Switch model_row-s
                    model[iter][self.__column_row] = dialog_row + 1
                    row_pred[self.__column_row] = dialog_row

                    # Apply setting
                    sensor = self.sensors[model[iter][self.__column_idx]]
                    sensor_pred = self.sensors[row_pred[self.__column_idx]]
                    sensor.dialog_row = dialog_row + 1
                    sensor_pred.dialog_row = dialog_row
                    self.update_dialog_rows()

    class MainDialog:

        def __init__(self, parent, main_dialog):

            self.__parent = parent
            self.__dialog = main_dialog

            self.create_content()

            # Create a timer, but do not start it
            self.__timer = parent.applet.timing.register(
                         self.update_values, parent.applet.settings["timeout"], False)

            self.__dialog.connect('show', self.dialog_shown_cb)
            self.__dialog.connect('hide', self.dialog_hidden_cb)

        def create_content(self):
            """
            (Re)creates sensor labels and values for main applet dialog
            
            """
            # List of sensors to be shown in dialog
            shown_sensors = dict()
            for sensor in self.__parent.sensors:
                if sensor.show:
                    shown_sensors[sensor.dialog_row] = sensor

            rows = shown_sensors.keys()
            rows.sort()

            # List of gtkLabel-s that contain the sensor value
            self.__value_labels = dict()

            new_vbox = gtk.VBox(False, 10)

            for row in rows:
                sensor = shown_sensors[row]
                hbox = gtk.HBox()
                label = gtk.Label(sensor.label + ':\t')
                self.__value_labels[sensor] = gtk.Label(
                                     str(sensor.value) + ' ' + sensor.unit_str)
                hbox.pack_start(label, False, False)
                hbox.pack_end(self.__value_labels[sensor], False, False)
                new_vbox.pack_start(hbox, False, False)

            new_vbox.show_all()
            self.__dialog.add(new_vbox)

        def recreate(self):
            # Destroy current dialog vbox
            self.__dialog.child.child.get_children()[-1].destroy()
            # Create new content
            self.create_content()

        def update_values(self):
            """Update main applet dialog with new values."""
            for sensor, label in self.__value_labels.iteritems():
                sensor.read_sensor()
                label.set_text(str(sensor.value) + ' ' + sensor.unit_str)

        def change_interval(self, timeout):
            self.__timer.change_interval(timeout)

        def dialog_shown_cb(self, dialog):
            """Start updating sensor values in main applet dialog."""
            self.__timer.start()
            # Force update
            self.update_values()

        def dialog_hidden_cb(self, dialog):
            """Stop update timer for main applet dialog."""
            self.__timer.stop()


if __name__ == "__main__":
    awnlib.init_start(SensorsApplet, {
        "name": applet_name,
        "short": short_name,
        "version": __version__,
        "description": applet_description,
        "logo": applet_logo,
        "author": "Grega Podlesek",
        "copyright-year": "2008 - 2009",
        "authors": ["Grega Podlesek <grega.podlesek@gmail.com>"],
        "artists": ["Grega Podlesek <grega.podlesek@gmail.com>",
                    "Zdravko Podlesek"],
        "type": ["System"]},
        ["settings-per-instance"])
