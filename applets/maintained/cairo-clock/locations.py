# Copyright (C) 2008 - 2009  onox <denkpadje@gmail.com>
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

from __future__ import with_statement

import os
from datetime import datetime
from threading import Lock, Thread
import time

import pygtk
pygtk.require("2.0")
import gtk
import gobject

import cairo
import pango

try:
    from dateutil import tz
except ImportError:
    tz = None

try:
    from gweather.I_KNOW_THIS_IS_UNSTABLE import gweather
except ImportError:
    gweather = None

from analogclock import AnalogClock, AnalogClockThemeProvider

# Interval in seconds between two successive draws of the clocks
draw_clock_interval = 1.0

clock_size = 48


def is_location(row):
    return row[0] is not None and row[1] is not None


class Locations:

    __previous_state = None
    __parent_container = None

    __city_boxes = {}
    __images_labels = {}

    __cache_surface = {}

    def __init__(self, applet):
        self.__applet = applet
        self.__cities_vbox = gtk.VBox(spacing=6)

        if "cities-timezones" not in applet.applet.settings:
            applet.applet.settings["cities-timezones"] = list()
        self.__cities_timezones = applet.applet.settings["cities-timezones"]

        applet.applet.timing.register(self.draw_clock_cb, draw_clock_interval)

    def draw_clock_cb(self):
        local_time = time.localtime()

        new_state = (local_time[3], local_time[4], self.__applet.settings["theme"], self.__applet.settings["time-24-format"])
        if self.__previous_state == new_state:
            return

        if self.__previous_state is None or self.__previous_state[2] != new_state[2]:
            self.__base_clock = AnalogClock(AnalogClockThemeProvider(new_state[2]), clock_size)

        self.__previous_state = new_state

        # Clear cache because theme might have changed and to avoid memory leaks
        self.__cache_surface.clear()

        self.update_all_images_labels()

    def show_plugin(self):
        self.__parent_container.set_no_show_all(False)
        self.__parent_container.show_all()

    def hide_plugin(self):
        self.__parent_container.hide_all()
        self.__parent_container.set_no_show_all(True)

    @classmethod
    def plugin_useable(self):
        return tz is not None and gweather is not None

    def get_name(self):
        return "Locations"

    def get_callback(self):
        return ("Edit", self.edit_action_cb)

    def edit_action_cb(self):
        self.__applet.applet.dialog.toggle("preferences", "show")
        self.__applet.preferences_notebook.set_current_page(self.__page_number)

    def get_element(self):
        return self.__cities_vbox

    def set_parent_container(self, parent):
        self.__parent_container = parent
        self.hide_plugin()

    def set_preferences_page_number(self, page_number):
        self.__page_number = page_number

    def get_preferences(self, prefs):
        self.__prefs_tab = LocationsPreferencesTab(prefs, self.__applet.applet, self.__cities_timezones, self.add_city, self.remove_city, self.contains_city_timezone)

        return self.__prefs_tab.get_prefs_widget()

    def remove_city(self, city_timezone):
        self.__cities_timezones.remove(city_timezone)

        # Remove element from list of locations in the GUI
        del self.__images_labels[city_timezone]
        self.__city_boxes.pop(city_timezone).destroy()

        if len(self.__cities_timezones) == 0:
            self.hide_plugin()
        self.__applet.applet.settings["cities-timezones"] = self.__cities_timezones

    def contains_city_timezone(self, city_timezone):
        return city_timezone not in self.__city_boxes

    def add_city(self, city, timezone):
        city_timezone = "%s#%s" % (city, timezone)
        assert city_timezone not in self.__city_boxes

        hbox = gtk.HBox(spacing=6)
        self.__city_boxes[city_timezone] = hbox

        # Image of analog clock
        image = gtk.Image()
        image.set_size_request(clock_size, clock_size)
        hbox.pack_start(image, expand=False)

        def update_image_cb(widget, event):
            context = widget.window.cairo_create()
            context.translate(event.area.x, event.area.y)

            city_datetime = datetime.now(tz.gettz(timezone))
            key = (city_datetime.hour % 12, city_datetime.minute)  # Modulo 12 because clock has only 12 hours

            if key not in self.__cache_surface:
                self.__cache_surface[key] = context.get_target().create_similar(cairo.CONTENT_COLOR_ALPHA, clock_size, clock_size)
                cache_context = cairo.Context(self.__cache_surface[key])

                self.__base_clock.draw_clock(cache_context, clock_size, city_datetime.hour, city_datetime.minute, None)

            context.set_operator(cairo.OPERATOR_OVER)
            context.set_source_surface(self.__cache_surface[key])
            context.paint()
        image.connect("expose-event", update_image_cb)

        # Vertical box containing city label and timezone label
        vbox = gtk.VBox()
        hbox.pack_start(vbox, expand=False)

        # City label
        city_label = gtk.Label("<big><b>" + city + "</b></big>")
        city_label.set_use_markup(True)
        city_label.set_alignment(0.0, 0.5)
        city_label.set_ellipsize(pango.ELLIPSIZE_END)
        city_label.set_max_width_chars(25)
        vbox.pack_start(city_label, expand=False)

        # Timezone label
        timezone_label = gtk.Label()
        timezone_label.set_alignment(0.0, 0.5)
        vbox.pack_start(timezone_label, expand=False)

        self.__images_labels[city_timezone] = (image, timezone_label)
        self.update_timezone_label(datetime.now(tz.tzlocal()), timezone_label, timezone)

        self.__cities_vbox.add(hbox)

        # Certain tuples are already present if dictionary was constructed from settings
        if city_timezone not in self.__cities_timezones:
            self.__cities_timezones.append(city_timezone)

            # Sort the list based on its UTC offset or city name
            def key_compare(object):
                obj = object.split("#", 1)
                return (self.city_compare_key(obj[1]), obj[0])
            self.__cities_timezones.sort(reverse=True, key=key_compare)

            self.__applet.applet.settings["cities-timezones"] = self.__cities_timezones

        # After having sorted the list (see above), reorder the child
        index = self.__cities_timezones.index(city_timezone)
        self.__cities_vbox.reorder_child(hbox, index)

        if len(self.__cities_timezones) > 0:
            self.show_plugin()

    def city_compare_key(self, timezone):
        return self.get_offset_minutes(datetime.now(tz.gettz(timezone)))

    def get_offset_minutes(self, city_time):
        offset = city_time.utcoffset()
        return offset.days * 24 * 60 + (offset.seconds / 60)

    def update_timezone_label(self, local_datetime, label, timezone):
        city_datetime = datetime.now(tz.gettz(timezone))

        if self.__applet.settings["time-24-format"]:
            format = "%H:%M"
        else:
            # Strip leading zero for single-digit hours
            format = str(int(city_datetime.strftime("%I"))) + ":%M %p"

        if city_datetime.day != local_datetime.day:
            format = format + " (%A)"

        format = city_datetime.strftime(format + " %Z")

        if city_datetime.tzname() != local_datetime.tzname():
            time_diff = self.get_offset_minutes(city_datetime) - self.get_offset_minutes(local_datetime)

            hours, minutes = divmod(abs(time_diff), 60)
            format += (" +" if time_diff > 0 else " -") + str(hours)
            if minutes != 0:
                format += ":" + str(minutes)

        label.set_text(format)

    def update_all_images_labels(self):
        local_datetime = datetime.now(tz.tzlocal())

        for city_timezone, image_label in self.__images_labels.iteritems():
            image_label[0].queue_draw()
            self.update_timezone_label(local_datetime, image_label[1], city_timezone.split("#", 1)[1])


class LocationsPreferencesTab:

    __search_window = None

    def __init__(self, prefs, applet, cities_timezones, add_city, remove_city, contains_city_timezone):
        self.__prefs = prefs
        self.__applet = applet
        self.add_city = add_city
        self.remove_city = remove_city
        self.contains_city_timezone = contains_city_timezone

        self.location_store = gtk.TreeStore(str, str)

        tree_view = prefs.get_object("treeview-locations")
        # TODO use ellepsis to handle large names of certain cities
        city_column = gtk.TreeViewColumn("City", gtk.CellRendererText(), text=0)
        city_column.set_min_width(100)
        city_column.set_max_width(150)
        tree_view.append_column(city_column)
        tree_view.append_column(gtk.TreeViewColumn("Timezone", gtk.CellRendererText(), text=1))

        self.__selection_buttons = (prefs.get_object("button-edit-location"), prefs.get_object("button-remove-location"))
        for button in self.__selection_buttons:
            button.set_sensitive(False)
        self.tree_selection = tree_view.get_selection()

        self.tree_selection.connect("changed", self.selection_changed_cb)
        self.location_store.connect("row-changed", self.row_changed_cb)

        prefs.get_object("button-add-location").connect("clicked", self.clicked_add_location_button_cb)
        prefs.get_object("button-remove-location").connect("clicked", self.clicked_remove_location_button_cb)

        for city_and_timezone in cities_timezones:
            self.location_store.append(None, city_and_timezone.split("#", 1))

        tree_view.set_model(self.location_store)
        self.location_store.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def get_prefs_widget(self):
        return self.__prefs.get_object("vbox-locations")

    def selection_changed_cb(self, selection):
        row_selected = selection.count_selected_rows() > 0

        for button in self.__selection_buttons:
            button.set_sensitive(row_selected)

    def init_search_window(self):
        with self.__init_search_window_lock:
            if self.__search_window is None:
                def add_row(city_timezone):
                    """Adds a row to the tree store that represents all added
                    locations.

                    """
                    self.location_store.append(None, city_timezone.split("#", 1))
                self.__search_window = LocationSearchWindow(self.__prefs, add_row, self.contains_city_timezone)
                self.__search_window.show_window()

    __init_search_window_lock = Lock()

    def clicked_add_location_button_cb(self, button):
        if self.__search_window is None:
            if not self.__init_search_window_lock.locked():
                with self.__init_search_window_lock:
                    Thread(target=self.init_search_window).start()
        else:
            self.__search_window.show_window()

    def clicked_remove_location_button_cb(self, button):
        iter = self.tree_selection.get_selected()[1]
        row = self.location_store[iter]
        city_timezone = "%s#%s" % (row[0], row[1])
        self.location_store.remove(iter)

        self.remove_city(city_timezone)

    def row_changed_cb(self, model, path, iter):
        row = self.location_store[iter]

        if is_location(row):
            self.add_city(row[0], row[1])


class LocationSearchWindow:

    def __init__(self, prefs, add_row, contains_city_timezone):
        self.__prefs = prefs
        self.add_row = add_row
        self.contains_city_timezone = contains_city_timezone

        self.__search_dialog = prefs.get_object("locations-search-dialog")
        self.__search_dialog.connect("delete_event", lambda w, e: True)
        self.__search_dialog.connect("response", self.response_event_cb)

        self.__button_ok_search = self.__prefs.get_object("button-ok-location-search")
        self.__button_ok_search.set_sensitive(False)
        self.__button_ok_search.connect("clicked", self.button_ok_search_clicked_cb)

        self.__entry_location_name = self.__prefs.get_object("entry-location-name")
        self.__entry_location_name.connect("changed", self.entry_location_changed_cb)

        self.__button_find_next = self.__prefs.get_object("button-find-next")
        self.__button_find_next.set_sensitive(False)
        self.__button_find_next.connect("clicked", self.button_find_next_clicked_cb)

        self.__vadjustment = self.__prefs.get_object("scroll-all-locations").get_vadjustment()

        self.__all_locations_store = gtk.TreeStore(str, str, bool)

        self.__all_locations_view = self.__prefs.get_object("treeview-all-locations")
        self.__all_locations_view.connect("row-activated", self.all_locations_row_activated_cb)

        self.__all_locations_selection = self.__all_locations_view.get_selection()
        self.__all_locations_selection.connect("changed", self.all_locations_selection_changed_cb)

        column = gtk.TreeViewColumn("Location", gtk.CellRendererText(), text=0)
        column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
        self.__all_locations_view.append_column(column)
        self.__all_locations_view.set_fixed_height_mode(True)

        # Parse locations _before_ setting model and sorting to avoid slowdown
        self.parse_locations()

        self.__all_locations_view.set_model(self.__all_locations_store)
        self.__all_locations_store.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def response_event_cb(self, widget, response):
        if response < 0:
            self.hide_window()

    def hide_window(self):
        self.__search_dialog.hide()

    def show_window(self):
        self.__all_locations_view.collapse_all()
        self.__vadjustment.set_value(0)

        # Clear text but block callable connected to "changed" to avoid expanding selected node
        self.__entry_location_name.handler_block_by_func(self.entry_location_changed_cb)
        self.__entry_location_name.set_text("")
        self.__entry_location_name.handler_unblock_by_func(self.entry_location_changed_cb)

        self.__entry_location_name.grab_focus()

        self.__search_dialog.show_all()

    def parse_gweather_locations(self, node, parent):
        children = node.get_children()
        if len(children) > 0:
            for i in children:
                timezone = i.get_timezone().get_tzid() if i.get_timezone() is not None else None
                is_city = i.get_level() is gweather.LOCATION_CITY
                node_iter = self.__all_locations_store.append(parent, (i.get_name(), timezone, is_city))

                # Iterate through children
                self.parse_gweather_locations(i, node_iter)
        elif node.get_level() is gweather.LOCATION_COUNTRY:
            for i in node.get_timezones():
                if i.get_name() is not None:
                    self.__all_locations_store.append(parent, (i.get_name(), i.get_tzid(), False))

    def parse_locations(self):
        node = gweather.location_new_world(True)
        self.parse_gweather_locations(node, None)

    def all_locations_selection_changed_cb(self, selection):
        """Enable the 'OK' button if the user selected a valid location,
        disable otherwise.

        """
        if selection.count_selected_rows() == 0:
            self.__button_ok_search.set_sensitive(False)

        select_iter = selection.get_selected()[1]
        if select_iter is not None:
            self.__button_ok_search.set_sensitive(self.is_location_and_leaf_node(select_iter))

    def all_locations_row_activated_cb(self, view, path, column):
        self.add_new_location()

    def button_ok_search_clicked_cb(self, button):
        self.add_new_location()

    def is_location_and_leaf_node(self, iter):
        row = self.__all_locations_store[iter]
        is_leaf_node = not self.__all_locations_store.iter_has_child(iter)
        return is_location(row) and is_leaf_node

    def add_new_location(self):
        """Add the selected location to the list of locations in the
        preferences window. This will subsequently trigger an event that adds
        the necessary widgets to the main dialog of the applet.

        Invoked when the user double clicks on a row or presses the 'OK'
        button.

        """
        select_iter = self.__all_locations_selection.get_selected()[1]

        if self.is_location_and_leaf_node(select_iter):
            row = self.__all_locations_store[select_iter]
            parent_row = self.__all_locations_store[self.__all_locations_store.iter_parent(select_iter)]

            # Use name of city if the row is a location in a city
            if parent_row[2]:
                city = parent_row[0]
            else:
                city = row[0]

            self.hide_window()
            city_timezone = "%s#%s" % (city, row[1])
            if self.contains_city_timezone(city_timezone):
                self.add_row(city_timezone)

    __search_cb_id = None
    __search_lock = Lock()
    __schedule_lock = Lock()

    def entry_location_changed_cb(self, entry):
        """Expand the tree and scroll to the first location that matches the
        text in the text entry.

        """
        def search_cb():
            with self.__search_lock:
                self.__search_results = []
                self.__search_result_index = 0

                search_text = entry.get_text()
                self.find_location(None, search_text, self.__search_results)
                if len(self.__search_results) > 0:
                    self.select_next_location()

                    self.__button_find_next.set_sensitive(len(search_text) > 0 and len(self.__search_results) > 1)
        with self.__schedule_lock:
            if self.__search_cb_id is not None:
                gobject.source_remove(self.__search_cb_id)
                self.__search_cb_id = None
            self.__search_cb_id = gobject.timeout_add(100, search_cb)

    def select_next_location(self):
        iter = self.__search_results[self.__search_result_index]

        path = self.__all_locations_store.get_path(iter)
        self.__all_locations_view.expand_to_path(path)
        self.__all_locations_selection.select_iter(iter)
        self.__all_locations_view.scroll_to_cell(path, use_align=True, row_align=0.5)

    def button_find_next_clicked_cb(self, button):
        with self.__search_lock:
            self.__search_result_index = (self.__search_result_index + 1) % len(self.__search_results)
            self.select_next_location()

    def find_location(self, parent_iter, text, result_list):
        """Do a depth-first search to find a node whose city starts with the
        given text. Fills the C{result_list} with instances of C{gtk.TreeIter}
        that points to the found element.

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
                result_list.append(child_iter)

            self.find_location(child_iter, text, result_list)
