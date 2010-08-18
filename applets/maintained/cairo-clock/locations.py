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

from __future__ import with_statement

import os
from datetime import datetime
from threading import Lock, Thread
import time

import pygtk
pygtk.require("2.0")
import gtk

import cairo
import glib
import pango

from awn.extras import _

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


class CityTimezoneCode(object):

    """Data object which contains the name of a city, its timezone, and
    its METAR weather station ID, or None if the location doesn't have one.

    """

    def __init__(self, city, timezone, code):
        self.__city = city
        self.__timezone = timezone
        self.__code = code if code != "None" else None

    @property
    def city(self):
        return self.__city

    @property
    def timezone(self):
        return self.__timezone

    @property
    def code(self):
        return self.__code

    def __str__(self):
        return "%s#%s#%s" % (self.city, self.timezone, self.code)

    def __iter__(self):
        def generate_data():
            yield self.city
            yield self.timezone
            yield self.code
        return generate_data()


class Locations:

    __parent_container = None

    def __init__(self, applet):
        self.__applet = applet

        self.__city_boxes = {}
        self.cache_surface = {}

        # Initialize the base clock so that the clocks can be drawn immediately when exposed
        self.__previous_state = (None, None, applet.applet.settings["theme"])
        self.base_clock = AnalogClock(AnalogClockThemeProvider(self.__previous_state[2]), clock_size)

        self.__cities_vbox = gtk.VBox(spacing=6)

        if "cities-timezones" not in applet.applet.settings:
            applet.applet.settings["cities-timezones"] = list()
        self.__cities_timezones = applet.applet.settings["cities-timezones"]

        applet.applet.timing.register(self.draw_clock_cb, draw_clock_interval)

    def draw_clock_cb(self):
        local_time = time.localtime()

        new_state = (local_time[3], local_time[4], self.__applet.applet.settings["theme"], self.__applet.applet.settings["time-24-format"])
        if self.__previous_state == new_state:
            return

        if self.__previous_state[2] != new_state[2]:
            self.base_clock = AnalogClock(AnalogClockThemeProvider(new_state[2]), clock_size)

        self.__previous_state = new_state

        # Clear cache because theme might have changed and to avoid memory leaks
        self.cache_surface.clear()

        # Update all clock images and timezone labels
        local_datetime = datetime.now(tz.tzlocal())

        for box in self.__city_boxes.itervalues():
            box.update_clock_image()
            box.update_timezone_label(local_datetime)

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
        return _("Locations")

    def get_callback(self):
        return (_("Edit"), self.edit_action_cb)

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
        self.__prefs_tab = LocationsPreferencesTab(prefs, self.__applet.applet, self.__cities_timezones, self.add_city, self.remove_city, self.contains_not_location)

        return self.__prefs_tab.get_prefs_widget()

    def remove_city(self, city_timezone_code):
        self.__cities_timezones.remove(str(city_timezone_code))

        # Remove element from list of locations in the GUI
        box = self.__city_boxes.pop(str(city_timezone_code))
        box.destroy_hbox(self.__cities_vbox)
        del box

        if len(self.__cities_timezones) == 0:
            self.hide_plugin()
        self.__applet.applet.settings["cities-timezones"] = self.__cities_timezones

    def contains_not_location(self, city_timezone):
        return str(city_timezone) not in self.__city_boxes

    def add_city(self, city_timezone_code_obj):
        city_timezone_code = str(city_timezone_code_obj)
        assert city_timezone_code not in self.__city_boxes

        box = self.LocationBox(self, city_timezone_code_obj)
        self.__city_boxes[city_timezone_code] = box

        # Certain tuples are already present if dictionary was constructed from settings
        if city_timezone_code not in self.__cities_timezones:
            self.__cities_timezones.append(city_timezone_code)

            # Sort the list based on its UTC offset or city name
            def key_compare(object):
                obj = object.split("#", 2)
                return (self.city_compare_key(obj[1]), obj[0])
            self.__cities_timezones.sort(reverse=True, key=key_compare)

            self.__applet.applet.settings["cities-timezones"] = self.__cities_timezones

        # After having sorted the list (see above), insert the box in the right position
        index = self.__cities_timezones.index(city_timezone_code)
        box.insert_in(self.__cities_vbox, index)

        if len(self.__cities_timezones) > 0:
            self.show_plugin()

    def city_compare_key(self, timezone):
        return self.get_offset_minutes(datetime.now(tz.gettz(timezone)))

    def get_offset_minutes(self, city_time):
        offset = city_time.utcoffset()
        return offset.days * 24 * 60 + (offset.seconds / 60)

    def uses_24hour_format(self):
        return self.__applet.applet.settings["time-24-format"]

    def get_weather_plugin(self):
        return self.__applet.get_plugin("Weather")

    class LocationBox:

        """Used to manage the Gtk+ widgets that correspond to a certain
        location.

        """

        def __init__(self, parent, city_timezone_code):
            self.__parent = parent
            self.__weather_plugin = parent.get_weather_plugin()

            #### START OF CRAP
            if self.__weather_plugin is not None and city_timezone_code.code is not None:
                self.__report_fetcher = self.__weather_plugin.get_report_fetcher(city_timezone_code.code)
            else:
                self.__report_fetcher = None
            #### END OF CRAP

            self.__timezone = city_timezone_code.timezone
            self.hbox = gtk.HBox(spacing=6)

            # Image of an analog clock
            self.__clock_image = gtk.Image()
            self.__clock_image.set_size_request(clock_size, clock_size)
            self.hbox.pack_start(self.__clock_image, expand=False)

            def update_image_cb(widget, event):
                context = widget.window.cairo_create()
                context.translate(event.area.x, event.area.y)

                city_datetime = datetime.now(tz.gettz(self.__timezone))
                key = (city_datetime.hour % 12, city_datetime.minute)  # Modulo 12 because clock has only 12 hours

                if key not in parent.cache_surface:
                    parent.cache_surface[key] = context.get_target().create_similar(cairo.CONTENT_COLOR_ALPHA, clock_size, clock_size)
                    cache_context = cairo.Context(parent.cache_surface[key])

                    parent.base_clock.draw_clock(cache_context, clock_size, city_datetime.hour, city_datetime.minute, None)

                context.set_operator(cairo.OPERATOR_OVER)
                context.set_source_surface(parent.cache_surface[key])
                context.paint()
            self.__clock_image.connect("expose-event", update_image_cb)

            # Vertical box containing city label and timezone label
            vbox = gtk.VBox()
            self.hbox.pack_start(vbox, expand=False)

            # City label
            city_label = gtk.Label("<big><b>%s</b></big>" % city_timezone_code.city)
            city_label.set_use_markup(True)
            city_label.set_alignment(0.0, 0.5)
            city_label.set_ellipsize(pango.ELLIPSIZE_END)
            city_label.set_max_width_chars(25)
            vbox.pack_start(city_label, expand=False)

            weather_timezone_hbox = gtk.HBox(spacing=6)

            #### START OF CRAP
            if self.__report_fetcher is not None:
                self.__weather_image = gtk.Image()
                self.__weather_image.props.has_tooltip = True
                weather_timezone_hbox.add(self.__weather_image)

                self.__tooltip_hbox = None
                def query_tooltip_cb(widget, x, y, keyboard_mode, tooltip):
                    if self.__tooltip_hbox is None:
                        return False
                    self.__tooltip_hbox.show_all()
                    tooltip.set_custom(self.__tooltip_hbox)
                    return True
                self.__weather_image.connect("query-tooltip", query_tooltip_cb)
            self.__can_update_weather = self.__report_fetcher is not None
            #### END OF CRAP

            # Timezone label
            self.__timezone_label = gtk.Label()
            self.__timezone_label.set_alignment(0.0, 0.2)
            weather_timezone_hbox.add(self.__timezone_label)

            vbox.pack_start(weather_timezone_hbox, expand=False)

            self.update_timezone_label(datetime.now(tz.tzlocal()))

        def update_clock_image(self):
            self.__clock_image.queue_draw()

        def update_timezone_label(self, local_datetime):
            city_datetime = datetime.now(tz.gettz(self.__timezone))

            if self.__parent.uses_24hour_format():
                format = "%H:%M"
            else:
                # Strip leading zero for single-digit hours
                format = str(int(city_datetime.strftime("%I"))) + ":%M %p"

            if city_datetime.day != local_datetime.day:
                format = format + " (%A)"

            text = city_datetime.strftime(format + " %Z")

            if city_datetime.tzname() != local_datetime.tzname():
                time_diff = self.__parent.get_offset_minutes(city_datetime) - self.__parent.get_offset_minutes(local_datetime)

                hours, minutes = divmod(abs(time_diff), 60)
                text += (" +" if time_diff > 0 else " -") + str(hours)
                if minutes != 0:
                    text += ":" + str(minutes)

            self.__timezone_label.set_text(text)

            #### START OF CRAP
            if self.__can_update_weather:
                self.__can_update_weather = False
                print "doing update..."

                def cb(weather, sky, srss, image):
                    print "tooltip update cb"
                    if image is not None:
                        self.__weather_image.set_from_icon_name(image, gtk.ICON_SIZE_BUTTON)

                        tooltip_hbox = gtk.HBox(spacing=6)
                        tooltip_hbox.set_border_width(2)
                        tooltip_hbox.add(gtk.image_new_from_icon_name(image, gtk.ICON_SIZE_DIALOG))
                        description_vbox = gtk.VBox()
                        tooltip_hbox.add(description_vbox)

                        tooltip_title = []
                        if weather is not None:
                            tooltip_title.append(weather[0].upper() + weather[1:])
                        if sky is not None:
                            tooltip_title.append(sky[0].upper() + sky[1:])
                        if len(tooltip_title) > 0:
                            sky_label = gtk.Label("<b>%s</b>" % ", ".join(tooltip_title))
                            sky_label.set_use_markup(True)
                            sky_label.set_alignment(0.0, 0.5)
                            description_vbox.pack_start(sky_label, expand=False)

                        sunriseset_label = gtk.Label("Sunrise: %s:%s / Sunset: %s:%s" % (srss[0] + srss[1]))
                        sunriseset_label.set_alignment(0.0, 0.5)
                        description_vbox.pack_start(sunriseset_label, expand=False)

                        print "constructed tooltip hbox:", tooltip_hbox
                        self.__tooltip_hbox = tooltip_hbox
                self.__weather_plugin.refresh_weather(self.__report_fetcher, cb, city_datetime, self.__parent.get_offset_minutes)

                def x():
                    self.__can_update_weather = True
                    print "can update!"
                    return False
                glib.timeout_add_seconds(15 * 60, x)
            #### END OF CRAP

        def insert_in(self, vbox, index):
            vbox.add(self.hbox)
            vbox.reorder_child(self.hbox, index)

        def destroy_hbox(self, vbox):
            vbox.remove(self.hbox)
            self.hbox.destroy()


class LocationsPreferencesTab:

    """Deals with the "Location" tab in the preferences window of the
    applet.

    It can show a search window, which is used to add locations, and it
    indirectly updates the locations (C{LocationBoxes}) in the Awn dialog
    if the C{gtk.TreeStore} is modified.

    """

    __search_window = None

    def __init__(self, prefs, applet, cities_timezones, add_city, remove_city, contains_not_location):
        self.__prefs = prefs
        self.__applet = applet
        self.add_city = add_city
        self.remove_city = remove_city
        self.contains_not_location = contains_not_location

        self.location_store = gtk.TreeStore(str, str, str)

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

        prefs.get_object("button-add-location").connect("clicked", self.clicked_add_location_button_cb)
        prefs.get_object("button-remove-location").connect("clicked", self.clicked_remove_location_button_cb)

        # Fill the tree store which will result in adding locations to the Awn dialog
        for city_and_timezone in cities_timezones:
            iter = self.location_store.append(None, city_and_timezone.split("#", 2))
            self.add_location(iter)

        tree_view.set_model(self.location_store)
        self.location_store.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def get_prefs_widget(self):
        return self.__prefs.get_object("vbox-locations")

    def selection_changed_cb(self, selection):
        row_selected = selection.count_selected_rows() > 0

        for button in self.__selection_buttons:
            button.set_sensitive(row_selected)

    __init_search_window_lock = Lock()

    def init_search_window(self):
        def add_row(city_timezone_code):
            """Adds a row to the tree store that represents all added
            locations.

            """
            if self.contains_not_location(city_timezone_code):
                iter = self.location_store.append(None, tuple(city_timezone_code))
                self.add_location(iter)
        try:
            self.__search_window = LocationSearchWindow(self.__prefs, add_row)
            self.__search_window.show_window()
        finally:
            self.__init_search_window_lock.release()

    def clicked_add_location_button_cb(self, button):
        if self.__search_window is None:
            if self.__init_search_window_lock.acquire(False):
                Thread(target=self.init_search_window).start()
        else:
            self.__search_window.show_window()

    def clicked_remove_location_button_cb(self, button):
        iter = self.tree_selection.get_selected()[1]
        row = self.location_store[iter]

        city_timezone_code = CityTimezoneCode(row[0], row[1], row[2])
        self.location_store.remove(iter)

        self.remove_city(city_timezone_code)

    def add_location(self, iter):
        row = self.location_store[iter]

        city_timezone_code = CityTimezoneCode(row[0], row[1], row[2])
        assert city_timezone_code.city is not None and city_timezone_code.timezone is not None
        self.add_city(city_timezone_code)


class LocationSearchWindow:

    """Used to manage the search window. It contains a tree with all
    the locations found by GWeather, and a text entry, which can be
    used to search for a particular location in the tree.

    If the action of "adding" a location is invoked, then an element is
    added to the tree store of C{LocationsPreferencesTab} to start the
    process of adding a new location to the Awn dialog.

    """

    def __init__(self, prefs, add_row):
        self.__prefs = prefs
        self.add_row = add_row

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

        self.__all_locations_store = gtk.TreeStore(str, str, bool, str)

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
                node_iter = self.__all_locations_store.append(parent, (i.get_name(), timezone, is_city, i.get_code()))

                # Iterate through children
                self.parse_gweather_locations(i, node_iter)
        elif node.get_level() is gweather.LOCATION_COUNTRY:
            for i in node.get_timezones():
                if i.get_name() is not None:
                    self.__all_locations_store.append(parent, (i.get_name(), i.get_tzid(), False, None))

    def parse_locations(self):
        """Parse the locations found by GWeather and add these to
        the C{gtk.TreeStore} of the search window.

        """
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
        return row[0] is not None and row[1] is not None and is_leaf_node

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
            city = parent_row[0] if parent_row[2] else row[0]

            self.hide_window()
            self.add_row(CityTimezoneCode(city, row[1], row[3]))

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
                else:
                    self.__button_find_next.set_sensitive(False)
        with self.__schedule_lock:
            if self.__search_cb_id is not None:
                glib.source_remove(self.__search_cb_id)
            self.__search_cb_id = glib.timeout_add(100, search_cb)

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
