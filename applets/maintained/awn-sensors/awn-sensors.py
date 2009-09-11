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

import gobject
try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except:
    import sys
    sys.exit(1)

from awn.extras import awnlib
from awn.extras import _

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

import sensoricon

applet_name = "Awn Sensors"
applet_version = "0.3.9"
applet_description = _("Applet to show the hardware sensors readouts")

# Applet's logo, used as the applet's icon and shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "images/thermometer.svg")
ui_file = os.path.join(os.path.dirname(__file__), "awn-sensors.ui")


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
        
        # Icon path
        images_dir = os.path.dirname(__file__) + "/images/"
        self.applet_icon_dir = images_dir + "applet/"
        
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
            self.applet.icon.file(images_dir + "no_sensors.svg",
                                                        size=applet.get_size())
            self.applet.tooltip.set(message)
            return
        
        self.update_all_sensors()
        
        # Load icons, if none are found, finish
        if not self.load_icons():
            return
        
        # == Settings == #
        # Load settings, setup rightclick menu and create settings dialog
        self.setup_preferences()
        
        # == Icon == #
        self.create_icon()
        # Recreate upon awn height change
        self.applet.connect_size_changed(self.height_changed_cb)
        
        # == Dialog == #
        self.create_dialog()
        
        
    # == Sensors == #
    def create_all_sensors(self):
        """
        Initialize sensors for all interfaces. Return False if no sensors are
        found.
        
        """
        self.interfaces = []
        self.interfaces.append(acpisensors.interface_name)
        self.interfaces.append(omnibooksensors.interface_name)
        self.interfaces.append(hddtempsensors.interface_name)
        self.interfaces.append(lmsensors.interface_name)
        self.interfaces.append(nvidiasensors.interface_name)
        self.interfaces.append(nvclocksensors.interface_name)
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
        self.icon.set_sensors(self.main_sensors)
    
    def update_all_sensors(self):
        """Update all of the sensor values."""
        for sensor in self.sensors:
            sensor.read_sensor()
    
    
    # == Applet icon == #
    def create_icon(self):
        """
        Create applet icon and start the update timer that calls update_icon
        method.
        
        """
        file = self.applet_icon_dir + self.settings["icon_file"]
        self.icon = sensoricon.SensorIcon(file,
                                          self.main_sensors,
                                          self.applet.get_size())
        self.old_values = None
        # Call the first update and start the updater
        self.update_icon()
        self.icon_timer = self.applet.timing.register(
                            self.update_icon, self.settings["timeout"])
    
    def update_icon(self, force=False):
        """
        Update applet icon to show the updated values.
        
        """
        for main_sensor in self.main_sensors:
            main_sensor.read_sensor()
        values = [sensor.value for sensor in self.main_sensors]
        # Check if values have changed
        if values != self.old_values or force:
            self.old_values = values
            
            # Get updated icon
            context = self.icon.get_icon()
            # Set updated icon
            self.applet.icon.set(context)
            
            # Update title
            title = ""
            for main_sensor in self.main_sensors:
                title += "%s: %d %s   " % (main_sensor.label,
                                           main_sensor.value,
                                           main_sensor.unit_str)
            self.applet.tooltip.set(title[:-3])
    
    
    # == Applet dialog == envoked by cliking the applet with left mouse button
    def create_dialog(self):
        """Create main applet dialog showing selected sensors."""
        self.dialog = self.applet.dialog.new("main", _("Sensors"))
        
        self.__dialog_vbox = None
        self.create_dialog_content()
        
        # Create a timer, but do not start it
        self.dialog_timer = self.applet.timing.register(
                    self.update_dialog, self.settings["timeout"], False)
        
        self.dialog.connect('show', self.dialog_shown_cb)
        self.dialog.connect('hide', self.dialog_hidden_cb)
    
    def create_dialog_content(self):
        """
        (Re)creates sensor labels and values for main applet dialog
        
        """
        # Destroy current dialog vbox
        if self.__dialog_vbox:
            self.__dialog_vbox.destroy()
        
        shown_sensors = dict()
        for sensor in self.sensors:
            if sensor.show:
                shown_sensors[sensor.dialog_row] = sensor
        
        rows = shown_sensors.keys()
        rows.sort()
        
        self.__dialog_vbox = gtk.VBox(False, 10)
        self.__dialog_values = dict()
        for row in rows:
            sensor = shown_sensors[row]
            hbox = gtk.HBox()
            label = gtk.Label(sensor.label + ':\t')
            self.__dialog_values[sensor] = gtk.Label(
                    str(sensor.value) + ' ' + sensor.unit_str)
            hbox.pack_start(label, False, False)
            hbox.pack_end(self.__dialog_values[sensor], False, False)
            self.__dialog_vbox.pack_start(hbox, False, False)
            
        self.__dialog_vbox.show_all()
        self.dialog.add(self.__dialog_vbox)
    
    def update_dialog(self):
        """Update main applet dialog with new values."""
        for sensor, label in self.__dialog_values.iteritems():
            sensor.read_sensor()
            label.set_text(str(sensor.value) + ' ' + sensor.unit_str)
    
    def load_icons(self):
        """
        Load backgrounds for applet icon from ./images/applet folder.
        Return False in an event of an error.
        """
        # Read icon names in ./images/applet folder
        path = self.applet_icon_dir
        # Check if the path exists
        if not os.path.exists(path):
            print _("Error:"), _("Directory"), path, _("does not exist.")
            return False
        
        self.icon_files = filter(
          lambda file: file.endswith((".svg", ".SVG")), os.listdir(path))
        if len(self.icon_files) == 0:
            print _("Error:"), _("No .svg images found in directory:"), path
            return False
        
        self.icon_files.sort()
        return True
    
    
    # == Settings == #
    def setup_preferences(self):
        """
        Load global and sensor settings and replace them with defaults if
        not set.
        
        """
        # Setup the rightclick context menu.
        self.pref_dialog = self.applet.dialog.new("preferences")
        self.pref_dialog.set_resizable(True)
        
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)
        prefs.get_object("notebook").reparent(self.pref_dialog.vbox)
        
        # Default settings
        default_settings = {
            # Global
            "unit": (units.UNIT_CELSIUS, self.change_unit),
            "timeout": (2, self.change_timeout,
                                             prefs.get_object("spin_timeout")),
            "icon_file": (self.icon_files[0]),
            # Sensor settings
            "ids": [str(sensor.id) for sensor in self.sensors],
            "labels": [sensor.label for sensor in self.sensors],
            "show": [sensor.show for sensor in self.sensors],
            "dialog_row": range(1, len(self.sensors) + 1),
            "in_icon": [sensor.in_icon for sensor in self.sensors],
            "hand_colors": [str(sensor.hand_color) for sensor in self.sensors],
            "text_colors": [str(sensor.text_color) for sensor in self.sensors],
            "high_values": [sensor.high_value for sensor in self.sensors],
            "low_values": [sensor.low_value for sensor in self.sensors],
            "high_alarms": [sensor.alarm_on_high for sensor in self.sensors],
            "low_alarms": [sensor.alarm_on_low for sensor in self.sensors]
        }
        
        # Load settings and replace with defaults if not set.
        self.settings = self.applet.settings.load_preferences(default_settings)
        settings = self.settings
        
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
                sensor.hand_color = eval(settings["hand_colors"][idx])
                sensor.text_color = eval(settings["text_colors"][idx])
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
                sensor.get_updater().set_timeout(settings["timeout"])
        
        # If a sensor was lost, a new one found or if order was changed
        if new_sensors or \
          len(self.sensors) != len(settings["ids"]) or \
          [str(sensor.id) for sensor in self.sensors] != settings["ids"]:
            
            # Sort sensors by dialog_row and renumber them in that order (to
            # eliminate any 'holes' in row order left by lost sensors and to
            # put the new sensors to the end).
            sorted_sensors = [sensor for sensor in self.sensors]
            sorted_sensors.sort(key=lambda s: s.dialog_row)
            # Renumber rows
            for row, sensor in enumerate(sorted_sensors):
                sensor.dialog_row = row + 1
            
            # Save all sensor settings.
            settings = self.applet.settings
            settings["ids"] = [str(sensor.id) for sensor in self.sensors]
            settings["labels"] = [sensor.label for sensor in self.sensors]
            settings["show"] = [sensor.show for sensor in self.sensors]
            settings["dialog_row"] = [s.dialog_row for s in self.sensors]
            settings["in_icon"] = [s.in_icon for s in self.sensors]
            settings["hand_colors"] = [str(s.hand_color) for s in self.sensors]
            settings["text_colors"] = [str(s.text_color) for s in self.sensors]
            settings["high_values"] = [s.high_value for s in self.sensors]
            settings["low_values"] = [s.low_value for s in self.sensors]
            settings["high_alarms"] = [s.alarm_on_high for s in self.sensors]
            settings["low_alarms"] = [s.alarm_on_low for s in self.sensors]
            
        # If none of the saved sensors has been selected as main, set default.
        if not self.main_sensors:
            # The default for the main sensor is the first sensor.
            self.sensors[0].in_icon = True
            self.main_sensors.append(self.sensors[0])
            self.applet.settings["in_icon"] = \
                                    [sensor.in_icon for sensor in self.sensors]
        
        if self.settings["icon_file"] not in self.icon_files:
            self.applet.settings["icon_file"] = self.icon_files[0]
        
        self.setup_general_preferences(prefs)
        self.setup_sensor_preferences(prefs)
        
    def setup_general_preferences(self, prefs):
        """Setup the main settings window."""
        # Unit combobox
        unit_combobox = prefs.get_object("combobox_unit")
        awnlib.add_cell_renderer_text(unit_combobox)
        for i in units.UNIT_STR_LONG[:3]:
            unit_combobox.append_text(i)
        unit_combobox.set_active(self.settings["unit"])
        unit_combobox.connect('changed', self.unit_changed_cb)
        
        # Icon combobox
        icon_combobox = prefs.get_object("combobox_icon")
        awnlib.add_cell_renderer_text(icon_combobox)
        for icon in self.icon_files:
            # Add filename without the extension and '_' replaced width space
            icon_combobox.append_text(icon[:-4].replace('_', ' '))
        icon_combobox.set_active(
                             self.icon_files.index(self.settings["icon_file"]))
        icon_combobox.connect('changed', self.icon_changed_cb)
    
    def setup_sensor_preferences(self, prefs):
        """Setup the sensor settings tab part of window."""
        # All sensors treeview
        treeview_all = prefs.get_object("treeview_sensors")
        # Main sensors treeview
        treeview_main = prefs.get_object("treeview_main_sensors")
        
        self.setup_sensors_treeview(treeview_all)
        self.setup_main_sensors_treeview(treeview_main)
        
        # Color buttons
        cb_hand = prefs.get_object("color_hand")
        cb_text = prefs.get_object("color_text")
        cb_hand.set_sensitive(False)
        cb_text.set_sensitive(False)
        
        # Connect 'color-set' event to change_*_color functions
        cb_hand.connect('color-set', lambda cb:
                        self.change_hand_color(cb.get_color(), cb.get_alpha()))
        cb_text.connect('color-set', lambda cb:
                        self.change_text_color(cb.get_color(), cb.get_alpha()))
        # When user selects a sensor in treeview_main, color buttons must
        # reflect that sensor's colors
        treeview_main.connect('cursor-changed', self.selection_changed_cb,
                         cb_hand, cb_text)
        
        # Properties button
        button_properties = prefs.get_object("button_properties")
        button_properties.connect('clicked', self.properties_cb, treeview_all)
        
        # Add button
        button_add = prefs.get_object("button_add")
        button_add.connect('clicked', self.add_cb, treeview_all)
        
        # Remove button
        button_remove = prefs.get_object("button_remove")
        button_remove.connect('clicked',
                              self.remove_cb, treeview_main, cb_hand, cb_text)
        
        # Up button
        button_up = prefs.get_object("button_up")
        button_up.connect('clicked', self.up_cb, treeview_all)
        
        # Down button
        button_down = prefs.get_object("button_down")
        button_down.connect('clicked', self.down_cb, treeview_all)
    
    def setup_sensors_treeview(self, treeview):
        """Create treeview with list of all sensors and their settings."""
        self.liststore = gtk.ListStore(
                            int, int, str, str, str, 'gboolean', 'gboolean')
        self.column_idx = 0
        self.column_row = 1
        self.column_interface = 2
        self.column_name = 3
        self.column_label = 4
        self.column_show = 5
        self.column_in_icon = 6
        
        # Fill liststore with data
        for idx, sensor in enumerate(self.sensors):
            # Add a row to liststore
            last = self.liststore.append([idx,
                                          sensor.dialog_row,
                                          sensor.interface,
                                          sensor.name,
                                          sensor.label,
                                          sensor.show,
                                          sensor.in_icon])
        
        # Set TreeView's liststore
        treeview.set_model(self.liststore)
        
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
                                          text=self.column_row,
                                          visible=self.column_show)
        tvcolumn_interface = gtk.TreeViewColumn(_("Interface"), cell_interface,
                                                text=self.column_interface)
        tvcolumn_name = gtk.TreeViewColumn(_("Name"), cell_name,
                                           text=self.column_name)
        tvcolumn_label = gtk.TreeViewColumn(_("Label"), cell_label,
                                            text=self.column_label)
        # Set the cell "active" attribute to column_show - retrieve the state
        # of the toggle button from that column in liststore
        tvcolumn_show = gtk.TreeViewColumn(_("In dialog"), cell_show,
                                           active=self.column_show)
        
        # Add treeview columns to treeview
        treeview.append_column(tvcolumn_row)
        treeview.append_column(tvcolumn_interface)
        treeview.append_column(tvcolumn_name)
        treeview.append_column(tvcolumn_label)
        treeview.append_column(tvcolumn_show)
        
        # Make name and label searchable
        treeview.set_search_column(self.column_name)
        treeview.set_search_column(self.column_label)
        
        # Allow sorting on the column
        tvcolumn_row.set_sort_column_id(self.column_row)
        tvcolumn_interface.set_sort_column_id(self.column_interface)
        tvcolumn_name.set_sort_column_id(self.column_name)
        tvcolumn_label.set_sort_column_id(self.column_label)
        tvcolumn_show.set_sort_column_id(self.column_show)
        
        # Sort by dialog_row
        self.liststore.set_sort_column_id(self.column_row, gtk.SORT_ASCENDING)
    
    def setup_main_sensors_treeview(self, treeview):
        """Create treeview with list of sensors to be shown in applet icon."""
        # List store for main sensors
        model_filter = self.liststore.filter_new()
        model_filter.set_visible_column(self.column_in_icon)
        
        # Set main sensor treeview's liststore
        treeview.set_model(model_filter)
        
        # Create a CellRendererText to render the data
        cell_label = gtk.CellRendererText()
        
        # Add treeview-column to treeview
        tvcolumn_label = gtk.TreeViewColumn(_("Sensors displayed in icon"),
                                            cell_label, text=self.column_label)
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
        prop_dialog.set_parent(self.pref_dialog)
        prop_dialog.set_icon(self.pref_dialog.get_icon())
        # Properties window should be on top of settings window
        prop_dialog.set_transient_for(self.pref_dialog)
        
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
        self.applet.notify.send(subject=None, body=message, icon="")
    
    def height_changed_cb(self, widget, event):
        """Update the applet's icon to reflect the new height."""
        self.icon.set_height(self.applet.get_height())
        # Force icon update
        self.update_icon(True)
    
    def dialog_shown_cb(self, dialog):
        """Update main applet dialog with new data and start update timer."""
        self.dialog_timer.start()
        self.update_dialog()
    
    def dialog_hidden_cb(self, dialog):
        """Stop update timer for main applet dialog."""
        self.dialog_timer.stop()
    
    
    # === Change setting methods === #
    def unit_changed_cb(self, widget):
        """Save unit setting and update icon."""
        unit = widget.get_active()
        self.applet.settings["unit"] = unit
        self.change_unit(unit)
    
    def change_unit(self, unit):
        """Change unit for all sensors and update icon."""
        for sensor in self.sensors:
            sensor.unit = unit
        self.update_icon(True)
    
    def icon_changed_cb(self, widget):
        """Save icon file setting and update icon."""
        filename = self.icon_files[widget.get_active()]
        # Save setting
        self.applet.settings["icon_file"] = filename
        # Apply icon change
        self.icon.set_icon_file(self.applet_icon_dir + filename)
        self.update_icon(True)
    
    def change_timeout(self, timeout):
        """Save timeout setting and change timer to new timeout."""
        self.update_icon(True)
        self.icon_timer.change_interval(timeout)
        self.dialog_timer.change_interval(timeout)
        for sensor in self.sensors:
            # Set timeout for updaters
            if sensor.interface in [lmsensors.interface_name,
                                    nvidiasensors.interface_name]:
                sensor.get_updater().set_timeout(timeout)
    
    def change_high_value(self, sensor, value):
        """Save high value setting for a specific sensor and update icon."""
        # Apply high value change
        sensor.high_value = value
        # Save high values
        self.applet.settings["high_values"] = \
                             [sensor.raw_high_value for sensor in self.sensors]
        if sensor in self.main_sensors:
            # Force icon update
            self.update_icon(True)
    
    def change_low_value(self, sensor, value):
        """Save low value setting for a specific sensor and update icon."""
        # Apply low value change
        sensor.low_value = value
        # Save low values
        self.applet.settings["low_values"] = \
                              [sensor.raw_low_value for sensor in self.sensors]
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
    
    def change_hand_color(self, color, alpha):
        """Save hand color setting for a specific sensor and update icon."""
        sensor = self.selected_sensor
        # Apply hand color change
        sensor.hand_color = (color.red, color.green, color.blue, alpha)
        # Save hand_color values
        self.applet.settings["hand_colors"] = \
                            [str(sensor.hand_color) for sensor in self.sensors]
        # Force icon update
        self.update_icon(True)
    
    def change_text_color(self, color, alpha):
        """Save text color setting for a specific sensor and update icon."""
        sensor = self.selected_sensor
        # Apply text color change
        sensor.text_color = (color.red, color.green, color.blue, alpha)
        # Save text_color values
        self.applet.settings["text_colors"] = \
                            [str(sensor.text_color) for sensor in self.sensors]
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
        self.create_dialog_content()
    
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
        self.liststore[path][self.column_label] = new_text
        sensor = self.sensors[self.liststore[path][self.column_idx]]
        # Apply change to sensor
        sensor.label = new_text
        # Save labels
        self.applet.settings["labels"] = \
                                    [sensor.label for sensor in self.sensors]
        # Recreate dialog
        self.create_dialog_content()
    
    def show_toggled_cb(self, cell_renderer, path):
        """
        Toggle specific sensor's "show in dialog" properity, save it and update
        dialog.
        
        """
        store = self.liststore
        sensor = self.sensors[store[path][self.column_idx]]
        
        # Toggle value in liststore
        store[path][self.column_show] = not store[path][self.column_show]
        # Apply change to sensor
        sensor.show = store[path][self.column_show]
        # Save show property
        self.applet.settings["show"] = [sensor.show for sensor in self.sensors]
        # Recreate dialog
        self.create_dialog_content()
    
    def selection_changed_cb(self, treeview, cb_hand, cb_text):
        """Handle selection change in treeview."""
        # Get selected sensor
        selection = treeview.get_selection()
        (model_filter, iter) = selection.get_selected()
        # Something must be selected
        if iter != None:
            child_iter = model_filter.convert_iter_to_child_iter(iter)
            sensor = self.sensors[self.liststore[child_iter][self.column_idx]]
            self.selected_sensor = sensor
            
            cb_hand.set_sensitive(True)
            cb_text.set_sensitive(True)
            
            (red, green, blue, alpha) = sensor.hand_color
            cb_hand.set_alpha(alpha)
            cb_hand.set_color(gtk.gdk.Color(red, green, blue))
            
            (red, green, blue, alpha) = sensor.text_color
            cb_text.set_alpha(alpha)
            cb_text.set_color(gtk.gdk.Color(red, green, blue))
            
        # If all unselected, gray out the buttons
        else:
            cb_hand.set_sensitive(False)
            cb_text.set_sensitive(False)
    
    
    # === Button callbacks === #
    def properties_cb(self, widget, treeview):
        """Open properties dialog for selected sensor."""
        # Get selected sensor
        treeselection = treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        # Something must be selected
        if iter != None:
            # Sensor index
            idx = model[iter][self.column_idx]
            self.create_properties_dialog(self.sensors[idx])
    
    def add_cb(self, widget, treeview_all):
        """
        Add selected sensors to main sensors (i.e. shown them in applet icon).
        
        """
        # Get selected sensor
        selection = treeview_all.get_selection()
        (model, iter) = selection.get_selected()
        # Something must be selected
        if iter != None:
            # Sensor index
            idx = self.liststore[iter][self.column_idx]
            # Apply setting
            self.change_in_icon(self.sensors[idx], True)
            # Change value in model
            model[iter][self.column_in_icon] = True
    
    def remove_cb(self, widget, treeview_main, cb_hand, cb_text):
        """
        Remove selected sensors from main sensors (i.e. do not shown them in
        applet icon).
        
        """
        # Get selected sensor
        selection = treeview_main.get_selection()
        (model_filter, iter) = selection.get_selected()
        # Something must be selected
        if iter != None:
            child_iter = model_filter.convert_iter_to_child_iter(iter)
            # Sensor index
            idx = self.liststore[child_iter][self.column_idx]
            # Apply setting
            self.change_in_icon(self.sensors[idx], False)
            # Change value in model
            self.liststore[child_iter][self.column_in_icon] = False
            # If row is removed, no row remains selected, so gray out the color
            # buttons
            cb_hand.set_sensitive(False)
            cb_text.set_sensitive(False)
    
    def up_cb(self, widget, treeview):
        """
        Move selected sensors up in main applet dialog.
        
        """
        # Get selected sensor
        selection = treeview.get_selection()
        (model, iter) = selection.get_selected()
        
        # Something must be selected
        if iter != None:
            dialog_row = model[iter][self.column_row]
            if dialog_row > 1:
                # Iterator pointing to predecessor (sensor/row that has
                # dialog_row one less than this one)
                row_pred = None
                for row in model:
                    if row[self.column_row] == dialog_row - 1:
                        row_pred = row
                        break
                if row_pred != None:
                    # Switch model_row-s
                    model[iter][self.column_row] = dialog_row - 1
                    row_pred[self.column_row] = dialog_row
                    
                    # Apply setting
                    sensor = self.sensors[model[iter][self.column_idx]]
                    sensor_pred = self.sensors[row_pred[self.column_idx]]
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
        if iter != None:
            dialog_row = model[iter][self.column_row]
            if dialog_row < len(self.sensors):
                # Iter pointing to predecessor (sensor/row that has dialog_row
                # one less than this one)
                row_pred = None
                for row in model:
                    if row[self.column_row] == dialog_row + 1:
                        row_pred = row
                        break
                if row_pred != None:
                # Switch model_row-s
                    model[iter][self.column_row] = dialog_row + 1
                    row_pred[self.column_row] = dialog_row
                    
                    # Apply setting
                    sensor = self.sensors[model[iter][self.column_idx]]
                    sensor_pred = self.sensors[row_pred[self.column_idx]]
                    sensor.dialog_row = dialog_row + 1
                    sensor_pred.dialog_row = dialog_row
                    self.update_dialog_rows()
    
    
if __name__ == "__main__":
    awnlib.init_start(SensorsApplet, {
        "name": applet_name,
        "short": "awn-sensors",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "Grega Podlesek",
        "copyright-year": "2008 - 2009",
        "authors": ["Grega Podlesek <grega.podlesek@gmail.com>"],
        "artists": ["Grega Podlesek <grega.podlesek@gmail.com>",
                    "Zdravko Podlesek"],
        "type": ["System"]},
        ["settings-per-instance"])
