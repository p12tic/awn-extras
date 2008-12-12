# Copyright (C) 2008  onox <denkpadje@gmail.com>
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
from datetime import datetime
import time
from xml.dom.minidom import parse

import pygtk
pygtk.require("2.0")
import gtk
import gobject
import pango

try:
    from dateutil import tz
except ImportError:
    tz = None

# Interval in seconds between two successive draws of the clocks
draw_clock_interval = 1.0

# File of libgweather
locations_file = "/usr/share/libgweather/Locations.xml"


class Locations:

    __previous_state = None
    __parent_container = None
    
    __city_boxes = {}
    __timezone_labels = {}
    
    def __init__(self, applet):
        self.__applet = applet
        self.__cities_vbox = gtk.VBox(spacing=6)
        
        if "cities-timezones" not in applet.applet.settings:
            applet.applet.settings["cities-timezones"] = set()
        self.__cities_timezones = applet.applet.settings["cities-timezones"]
        
        applet.applet.timing.register(self.draw_clock_cb, draw_clock_interval)
    
    def draw_clock_cb(self):
        local_time = time.localtime()
        
        new_state = (local_time[3], local_time[4], self.__applet.default_values["time-24-format"])
        if self.__previous_state == new_state:
            return
        self.__previous_state = new_state
        
        self.update_all_timezone_labels()
    
    def show_plugin(self):
        self.__parent_container.set_no_show_all(False)
        self.__parent_container.show_all()
    
    def hide_plugin(self):
        self.__parent_container.hide_all()
        self.__parent_container.set_no_show_all(True)
    
    @classmethod
    def plugin_useable(self):
        return tz is not None and os.path.isfile(locations_file)
    
    def get_name(self):
        return "Locations"
    
    def get_callback(self):
        return ("Edit", self.edit_action_cb)
    
    def get_element(self):
        return self.__cities_vbox
    
    def set_parent_container(self, parent):
        self.__parent_container = parent
        self.hide_plugin()
    
    def set_preferences_page_number(self, page_number):
        self.__page_number = page_number
    
    def get_preferences(self, prefs):
        self.__prefs = prefs
        self.location_store = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        
        tree_view = prefs.get_widget("treeview-locations")
        # TODO use ellepsis to handle large names of certain cities
        city_column = gtk.TreeViewColumn("City", gtk.CellRendererText(), text=0)
        city_column.set_min_width(100)
        city_column.set_max_width(150)
        tree_view.append_column(city_column)
        tree_view.append_column(gtk.TreeViewColumn("Timezone", gtk.CellRendererText(), text=1))
        
        self.__selection_buttons = (prefs.get_widget("button-edit-location"), prefs.get_widget("button-remove-location"))
        for button in self.__selection_buttons:
            button.set_sensitive(False)
        self.tree_selection = tree_view.get_selection()
        
        self.tree_selection.connect("changed", self.selection_changed_cb)
        self.location_store.connect("row-changed", self.row_changed_cb)
        
        prefs.get_widget("button-add-location").connect("clicked", self.clicked_add_location_button_cb)
        prefs.get_widget("button-remove-location").connect("clicked", self.clicked_remove_location_button_cb)
        
        for city_and_timezone in self.__cities_timezones:
            self.location_store.append(None, city_and_timezone)
        
        tree_view.set_model(self.location_store)
        self.location_store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        
        # Set up search dialog
        self.__search_dialog = prefs.get_widget("locations-search-dialog")
        prefs.get_widget("button-cancel-location-search").connect("clicked", lambda w: self.__search_dialog.hide())
        self.__search_dialog.set_skip_taskbar_hint(True)
        self.setup_location_search()
        
        return prefs.get_widget("vbox-locations")
    
    def selection_changed_cb(self, selection):
        row_selected = selection.count_selected_rows() > 0
        
        for button in self.__selection_buttons:
            button.set_sensitive(row_selected)
    
    def clicked_add_location_button_cb(self, button):
        self.__all_locations_view.collapse_all()
        self.__prefs.get_widget("scroll-all-locations").get_vadjustment().set_value(0)
        entry_location = self.__prefs.get_widget("entry-location-name")
        entry_location.set_text("")
        entry_location.grab_focus()
        
        self.__search_dialog.show_all()
    
    def clicked_remove_location_button_cb(self, button):
        iter = self.tree_selection.get_selected()[1]
        row = self.location_store[iter]
        city_timezone = (row[0], row[1])
        self.location_store.remove(iter)
        
        self.remove_city(city_timezone)
    
    def remove_city(self, city_timezone):
        self.__cities_timezones.remove(city_timezone)
        
        # Remove element from list of locations in the GUI
        del self.__timezone_labels[city_timezone]
        self.__city_boxes.pop(city_timezone).destroy()
        
        if len(self.__cities_timezones) == 0:
            self.hide_plugin()
        self.__applet.applet.settings["cities-timezones"] = self.__cities_timezones
    
    def is_location(self, row):
        return row[0] is not None and row[1] is not None
    
    def row_changed_cb(self, model, path, iter):
        row = self.location_store[iter]
        
        if self.is_location(row):
            self.add_city(row[0], row[1])
    
    def add_city(self, city, timezone):
        city_timezone = (city, timezone)
        assert city_timezone not in self.__city_boxes
        
        hbox = gtk.HBox(spacing=6)
        
        # TODO replace by real cairo clock :)
        image = gtk.image_new_from_file("/usr/share/avant-window-navigator/applets/cairo-clock/cairo-clock-logo.svg")
        hbox.pack_start(image, expand=False)
        
        vbox = gtk.VBox()
        hbox.pack_start(vbox, expand=False)
        
        city_label = gtk.Label("<big><b>" + city + "</b></big>")
        city_label.set_use_markup(True)
        city_label.set_alignment(0.0, 0.5)
        city_label.set_ellipsize(pango.ELLIPSIZE_END)
        city_label.set_max_width_chars(25)
        vbox.pack_start(city_label, expand=False)
        
        timezone_label = gtk.Label()
        timezone_label.set_alignment(0.0, 0.5)
        vbox.pack_start(timezone_label, expand=False)
        
        self.__timezone_labels[city_timezone] = timezone_label
        self.update_timezone_label(datetime.now(tz.tzlocal()), *city_timezone)
        
        self.__city_boxes[city_timezone] = hbox
        self.__cities_vbox.add(hbox)
        
        # Certain tuples are already present if dictionary was constructed from settings
        if city_timezone not in self.__cities_timezones:
            self.__cities_timezones.add(city_timezone)
            self.__applet.applet.settings["cities-timezones"] = self.__cities_timezones
        
        if len(self.__cities_timezones) > 0:
            self.show_plugin()
    
    def update_timezone_label(self, local_datetime, city, timezone):
        city_datetime = datetime.now(tz.gettz(timezone))
        
        if self.__applet.default_values["time-24-format"]:
            format = "%H:%M"
        else:
            # Strip leading zero for single-digit hours
            format = str(int(city_datetime.strftime("%I"))) + ":%M %p"
        
        if city_datetime.day != local_datetime.day:
            format = format + " (%A)"
        
        format = city_datetime.strftime(format + " %Z")
        
        if city_datetime.tzname() != local_datetime.tzname():
            remote_offset = city_datetime.utcoffset()
            local_offset = local_datetime.utcoffset()
            
            remote_minutes  = remote_offset.days * 24 * 60 + (remote_offset.seconds / 60)
            local_minutes  = local_offset.days * 24 * 60 + (local_offset.seconds / 60)
            time_diff = remote_minutes - local_minutes
            
            hours, minutes = divmod(abs(time_diff), 60)
            format += [" -", " +"][time_diff > 0] + str(hours) 
            if minutes != 0:
                format += ":" + str(minutes)
        
        self.__timezone_labels[(city, timezone)].set_text(format)
    
    def update_all_timezone_labels(self):
        local_datetime = datetime.now(tz.tzlocal())
        
        for city_timezone in self.__timezone_labels:
            self.update_timezone_label(local_datetime, *city_timezone)
    
    def edit_action_cb(self):
        self.__applet.applet.dialog.toggle("preferences", "show")
        self.__applet.preferences_notebook.set_current_page(self.__page_number)
    
    def setup_location_search(self):
        self.__all_locations_store = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        
        self.__all_locations_view = self.__prefs.get_widget("treeview-all-locations")
        self.__all_locations_view.append_column(gtk.TreeViewColumn("Location", gtk.CellRendererText(), text=0))
        
        # TODO only when ("Locations" tab in preferences window | search window) is visible for the first time? 
        self.parse_locations()
        
        self.__all_locations_view.set_model(self.__all_locations_store)
        self.__all_locations_store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        
        self.__button_ok_search = self.__prefs.get_widget("button-ok-location-search")
        self.__button_ok_search.set_sensitive(False)
        
        self.__button_ok_search.connect("clicked", self.button_ok_search_clicked_cb)
        self.__all_locations_view.connect("row-activated", self.all_locations_row_activated_cb)
        
        self.__all_locations_selection = self.__all_locations_view.get_selection()
        self.__all_locations_selection.connect("changed", self.all_locations_selection_changed_cb)
        
        self.__prefs.get_widget("entry-location-name").connect("changed", self.entry_location_changed_cb)
        # TODO find next entry when clicking button-find-next
    
    def parse_locations(self):
        dom = parse(locations_file)
        
        self.recursive_parse_locations(dom.childNodes[1], None, None)
        
        """ Clean up manually because certain versios of Python cannot
        garbage collect objects that are in a cycle """
        dom.unlink()
    
    def recursive_parse_locations(self, parent, parent_node, timezone):
        for element in parent.childNodes:
            if element.tagName == "tz-hint":
                timezone = element.firstChild.nodeValue
            elif element.tagName in ("region", "state", "country", "city"):
                location_node = self.__all_locations_store.append(parent_node, (element.firstChild.firstChild.nodeValue, None, element.tagName == "city"))
                self.recursive_parse_locations(element, location_node, timezone)
            elif element.tagName == "location":
                if timezone is None:
                    timezone = element.getElementsByTagName("tz-hint")[0].firstChild.nodeValue
                self.__all_locations_store.append(parent_node, (element.firstChild.firstChild.nodeValue, timezone, False))
    
    def all_locations_selection_changed_cb(self, selection):
        if selection.count_selected_rows() == 0:
            self.__button_ok_search.set_sensitive(False)
        
        select_iter = selection.get_selected()[1]
        if select_iter is not None:
            row = self.__all_locations_store[select_iter]
            self.__button_ok_search.set_sensitive(self.is_location(row))
    
    def all_locations_row_activated_cb(self, view, path, column):
        self.add_new_location()
    
    def button_ok_search_clicked_cb(self, button):
        self.add_new_location()
    
    def add_new_location(self):
        select_iter = self.__all_locations_selection.get_selected()[1]
        row = self.__all_locations_store[select_iter]
        
        if self.is_location(row):
            parent_row = self.__all_locations_store[self.__all_locations_store.iter_parent(select_iter)]
            
            # Use name of city if the row is a location in a city
            if parent_row[2]:
                city = parent_row[0]
            else:
                city = row[0]
            
            city_timezone = (city, row[1])
            if city_timezone not in self.__city_boxes:
                self.location_store.append(None, city_timezone)
            self.__search_dialog.hide()
    
    def entry_location_changed_cb(self, entry):
        iter = self.find_location(None, entry.get_text())
        if iter is not None:
            path = self.__all_locations_store.get_path(iter)
            self.__all_locations_view.expand_to_path(path)
            self.__all_locations_selection.select_iter(iter)
            self.__all_locations_view.scroll_to_cell(path, use_align=True, row_align=0.5)
    
    def find_location(self, parent_iter, text):
        """Do a depth first search to find a node whose city starts with the
        given text. Returns a {gtk.TreeIter} that points to the found element,
        or None if no location matched.
        
        """
        number_children = self.__all_locations_store.iter_n_children(parent_iter)
        for i in range(0, number_children):
            child_iter = self.__all_locations_store.iter_nth_child(parent_iter, i)
            row = self.__all_locations_store[child_iter]
            
            row_text = row[0]
            if text.islower():
                # Do case-insensitive comparison if text is lower case
                row_text = row_text.lower()
            if row_text.startswith(text):
                return child_iter
            
            result = self.find_location(child_iter, text)
            if result is not None:
                return result