#!/usr/bin/python
# Copyright (C) 2007, 2008:
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#     Please do not email the above person for support. The 
#     email address is only there for license/copyright purposes.
# Copyright (C) 2009  onox <denkpadje@gmail.com>
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

from __future__ import with_statement

from contextlib import closing, contextmanager
import os
import re
import urllib2
from xml.dom import minidom

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import _, awnlib, __version__
from awn.extras.threadqueue import ThreadQueue, async_method
from awn import OverlayText, OverlayThrobber, OverlayThemedIcon

import cairo
import glib

applet_name = "Weather"
applet_description = "Applet to display current weather and forecast"

# Applet's themed icon, also shown in the GTK About dialog
applet_logo = "weather-few-clouds"

# Interval in minutes between updating conditions, forecast, and map
update_interval = 30

# Timeout in seconds of network operations
socket_timeout = 20

# Import socket to set the default timeout, it is unlimited by default!
import socket
socket.setdefaulttimeout(socket_timeout)

ui_file = os.path.join(os.path.dirname(__file__), "weather.ui")

temperature_units = ["Celcius", "Fahrenheit"]
font_sizes = (15.0, 18.0, 23.0)

system_theme_name = "System theme"

theme_dir = "/usr/share/icons"

icon_states = ["twc-logo", "weather-clear", "weather-few-clouds", "weather-overcast",
"weather-snow-and-rain", "weather-showers", "weather-showers-scattered",
"weather-snow", "weather-fog", "weather-storm", "weather-severe-alert",
"weather-clear-night", "weather-few-clouds-night"]

network_error_message = "Could not retrieve weather data. You may be experiencing connectivity issues."

import forecast

disconnect_counter = {}
throbber_counter = {}

overlay_fsm = None


class OverlayStateMachine:

    def __init__(self, disconnect, throbber):
        self.disconnect_overlay = disconnect
        self.throbber_overlay = throbber

        # Set initial state
        self.set_next(IdleState)

    def set_next(self, state):
        self.__state = state(self)

    def evaluate(self):
        glib.idle_add(self.__state.evaluate)


class BaseState:

    def __init__(self, handler, throbber, disconnect):
        self.handler = handler

        self.handler.throbber_overlay.props.active = throbber
        self.handler.disconnect_overlay.props.active = disconnect

    def evaluate(self):
        disconnected = any(disconnect_counter.values())
        busy = any(throbber_counter.values())

        if busy and disconnected:
            self.handler.set_next(RefreshAndErrorState)
        elif busy and not disconnected:
            self.handler.set_next(RefreshState)
        elif not busy and disconnected:
            self.handler.set_next(ErrorState)
        else:
            self.handler.set_next(IdleState)


class IdleState(BaseState):

    def __init__(self, handler):
        BaseState.__init__(self, handler, False, False)


class RefreshState(BaseState):

    def __init__(self, handler):
        BaseState.__init__(self, handler, True, False)


class ErrorState(BaseState):

    def __init__(self, handler):
        BaseState.__init__(self, handler, False, True)


class RefreshAndErrorState(BaseState):

    def __init__(self, handler):
        BaseState.__init__(self, handler, True, False)


def with_overlays(func):
    """Makes the throbber visible while refreshing and
    the 'disconnect' icon if an error has occurred.

    """
    throbber_counter[func] = False
    disconnect_counter[func] = False
    def activate_throbber(show):
        throbber_counter[func] = show
        overlay_fsm.evaluate()
    def active_icon(error):
        disconnect_counter[func] = error
        overlay_fsm.evaluate()
    def bound_func(obj, *args, **kwargs):
        activate_throbber(True)
        try:
            result = func(obj, *args, **kwargs)
            active_icon(False)
            return result
        except:
            active_icon(True)
            raise
        finally:
            activate_throbber(False)
    return bound_func


@contextmanager
def unlink_xml(socket):
    xmldoc = minidom.parse(socket)
    try:
        yield xmldoc
    finally:
        xmldoc.unlink()


class WeatherApplet:

    def __init__(self, applet):
        self.applet = applet

        self.cached_conditions = None
        self.map_vbox = None
        self.image_map = None
        self.map_pixbuf = None

        self.network_handler = self.NetworkHandler()
        self.notification = applet.notify.create_notification("Network error in Weather", network_error_message, "dialog-warning", 20)

        self.setup_context_menu()

        self.forecaster = forecast.Forecast(self)

        # Set default icons/titles/dialogs so the applet is informative without data
        self.set_icon()
        self.applet.tooltip.set("%s %s..."%(_("Fetching conditions for"), self.settings['location']))

        # Overlays
        self.__temp_overlay = OverlayText()
        self.__temp_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH
        applet.add_overlay(self.__temp_overlay)

        disconnect_overlay = OverlayThemedIcon(applet.get_icon(), "stock_disconnect", "error")
        disconnect_overlay.props.alpha = 1.0
        throbber_overlay = OverlayThrobber(applet.get_icon())

        for i in (disconnect_overlay, throbber_overlay):
            i.props.scale = 0.5
            i.props.gravity = gtk.gdk.GRAVITY_SOUTH_EAST
            i.props.apply_effects = False
            applet.add_overlay(i)

        global overlay_fsm
        overlay_fsm = OverlayStateMachine(disconnect_overlay, throbber_overlay)

        # Set up the timer which will refresh the conditions, forecast, and weather map
        applet.timing.register(self.activate_refresh_cb, update_interval * 60)
        applet.timing.delay(self.activate_refresh_cb, 1.0)

    def network_error_cb(self, e, tb):
        if type(e) is self.NetworkHandler.NetworkException:
            print "Error in Weather:", e
            self.notification.show()
        else:
            self.applet.errors.set_error_icon_and_click_to_restart()
            self.applet.errors.general(e, traceback=tb, callback=gtk.main_quit)

    def setup_context_menu(self):
        """Add "refresh" to the context menu and setup the preferences.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        map_item = gtk.MenuItem(_("Show _Map"))
        map_item.connect("activate", self.activate_map_cb)
        menu.insert(map_item, menu_index)

        refresh_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_REFRESH)
        refresh_item.connect("activate", self.activate_refresh_cb)
        menu.insert(refresh_item, menu_index + 1)

        menu.insert(gtk.SeparatorMenuItem(), menu_index + 2)

        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        preferences_vbox = self.applet.dialog.new("preferences").vbox
        prefs.get_object("dialog-vbox").reparent(preferences_vbox)

        self.setup_preferences(prefs)

    def setup_preferences(self, prefs):
        refresh_dialog = lambda v: self.refresh_icon_and_forecast()
        def refresh_curved_dialog(value):
            self.forecaster.setup_forecast_dialog()
            refresh_dialog(None)  # dummy value
        refresh_map = lambda v: self.set_map_pixbuf(self.map_pixbuf)
        refresh_location_label = lambda v: self.location_label.set_markup("<b>%s</b>" % v)
        refresh_location = lambda v: self.activate_refresh_cb()

        # Only use themes that are likely to provide all the files
        def filter_theme(theme):
            return os.path.isfile(os.path.join(theme_dir, theme, "scalable/status/weather-clear.svg")) \
                or os.path.isfile(os.path.join(theme_dir, theme, "48x48/status/weather-clear.png")) \
                or os.path.isfile(os.path.join(theme_dir, theme, "48x48/status/weather-clear.svg"))
        self.themes = filter(filter_theme, os.listdir(theme_dir))
        self.themes.sort()
        self.themes = [system_theme_name] + self.themes + ["moonbeam"]

        def refresh_theme_and_dialog(value):
            self.setup_theme()
            refresh_dialog(None)

        defaults = {
            "show-temperature-icon": (True, self.refresh_icon, prefs.get_object("checkbutton-temperature-icon")),
            "temperature-font-size": (1, self.refresh_icon),
            "temperature-unit": (0, refresh_dialog),
            "theme": (system_theme_name, refresh_theme_and_dialog),
            "curved_dialog": (False, refresh_curved_dialog, prefs.get_object("curvedCheckbutton")),
            "location": ("Portland, ME", refresh_location_label),
            "location_code": ("USME0328", refresh_location),
            "map_maxwidth": (450, refresh_map, prefs.get_object("mapWidthSpinbutton"))
        }
        self.settings = self.applet.settings.load_preferences(defaults)

        self.setup_theme()

        """ General preferences """
        self.search_window = prefs.get_object("locations-search-dialog")
        def response_event_cb(widget, response):
            if response < 0:
                self.search_window.hide()
        self.search_window.connect("response", response_event_cb)
        self.search_window.connect("delete_event", lambda w, e: True)
        def location_button_clicked_cb(widget):
            self.init_search_window()
            self.search_list.append([_("No records found"), None])
            self.search_window.show_all()
        prefs.get_object("button-location").connect("clicked", location_button_clicked_cb)

        unit_combobox = prefs.get_object("combobox-temperature-unit")
        awnlib.add_cell_renderer_text(unit_combobox)
        for i in temperature_units:
            unit_combobox.append_text(i)
        unit_combobox.set_active(self.settings["temperature-unit"])
        unit_combobox.connect("changed", self.unit_changed_cb)

        theme_combobox = prefs.get_object("combobox-theme")
        awnlib.add_cell_renderer_text(theme_combobox)
        for i in self.themes:
            theme_combobox.append_text(i)
        if self.settings["theme"] not in self.themes:
            self.applet.settings["theme"] = self.themes[0]
        theme_combobox.set_active(self.themes.index(self.settings["theme"]))
        theme_combobox.connect("changed", self.theme_changed_cb)

        fontsize_combobox = prefs.get_object("combobox-font-size")
        fontsize_combobox.set_active(self.settings["temperature-font-size"])
        fontsize_combobox.connect("changed", self.fontsize_changed_cb)

        tempicon_checkbutton = prefs.get_object("checkbutton-temperature-icon")
        fontsize_hbox = prefs.get_object("hbox-font-size")
        fontsize_hbox.set_sensitive(tempicon_checkbutton.get_active())
        tempicon_checkbutton.connect("toggled", lambda w: fontsize_hbox.set_sensitive(w.get_active()))

        self.location_label = prefs.get_object("locationLabel")
        self.location_label.set_markup("<b>%s</b>" % self.settings["location"])

        """ Location search window """
        self.search_list = gtk.ListStore(str, str)

        self.treeview = prefs.get_object("location-treeview")
        self.treeview.set_model(self.search_list)
        self.treeview.append_column(gtk.TreeViewColumn("Location", gtk.CellRendererText(), text=0))

        self.ok_button = prefs.get_object("location-ok-button")
        self.ok_button.connect("clicked", self.ok_button_clicked_cb)

        self.treeview.connect("cursor-changed", lambda w: self.ok_button.set_sensitive(True))
        self.treeview.connect("row-activated", lambda v, p, c: self.ok_button_clicked_cb())

        find_button = prefs.get_object("location-find-button")

        self.location_entry = prefs.get_object("location-entry")
        def location_entry_changed_cb(widget):
            find_button.set_sensitive(len(self.location_entry.get_text()) > 0)
        self.location_entry.connect("changed", location_entry_changed_cb)

        self.location_entry.connect("activate", self.search_locations_cb)
        find_button.connect("clicked", self.search_locations_cb)

    def unit_changed_cb(self, widget):
        self.applet.settings["temperature-unit"] = widget.get_active()

    def theme_changed_cb(self, widget):
        self.applet.settings["theme"] = self.themes[widget.get_active()]

    def fontsize_changed_cb(self, widget):
        self.applet.settings["temperature-font-size"] = widget.get_active()

    def refresh_icon_and_forecast(self):
        self.refresh_icon()
        self.forecaster.refresh_unit()

    def init_search_window(self):
        self.search_list.clear()
        self.treeview.set_sensitive(False)
        self.ok_button.set_sensitive(False)

    def search_locations_cb(self, widget):
        text = self.location_entry.get_text()
        if len(text) > 0:
            self.init_search_window()
            self.search_list.append([_("Searching..."), None])

            def cb(locations):
                self.search_list.clear()
                if len(locations) > 0:
                    self.treeview.set_sensitive(True)
                    for i in locations:
                        self.search_list.append(i)
                else:
                    self.search_list.append([_("No records found"), None])
            self.network_handler.get_locations(text, callback=cb, error=self.network_error_cb)

    def ok_button_clicked_cb(self, widget=None):
        (model, iter) = self.treeview.get_selection().get_selected()
        self.applet.settings["location_code"] = model.get_value(iter, 1)
        self.applet.settings["location"] = model.get_value(iter, 0)

        self.search_window.hide()

    def activate_map_cb(self, widget):
        self.map_dialog.show_all()

    def activate_refresh_cb(self, widget=None, map=True):
        """Refresh the icon, forecast, and map data. Called by the
        "Refresh" option in the context menu.

        """
        self.refresh_conditions()
        self.forecaster.refresh_forecast()
        if map:
            self.fetch_weather_map()

    def setup_theme(self):
        def refresh_theme():
            states_names = {}
            for i in icon_states:
                states_names[i] = i
            self.applet.theme.set_states(states_names)

            theme = self.settings["theme"] if self.settings["theme"] != system_theme_name else None
            self.applet.theme.theme(theme)
        glib.idle_add(refresh_theme)

    def set_icon(self, hint="twc"):
        def refresh_overlay():
            state = self.get_icon_name(hint, self.settings["theme"])
            self.applet.theme.icon(state)

            if hint != 'twc':
                self.__temp_overlay.props.font_sizing = font_sizes[self.settings['temperature-font-size']]
                self.__temp_overlay.props.text = tempText = self.convert_temperature(self.cached_conditions['TEMP']) + u"\u00B0"
                self.__temp_overlay.props.active = bool(self.settings["show-temperature-icon"])
        glib.idle_add(refresh_overlay)

    def refresh_conditions(self, retries=3):
        """Download the current weather conditions. If this fails, or the
        conditions are unchanged, don't do anything. Refresh the applet's
        title and icon if the conditions have changed.

        """
        def cb(conditions):
            if conditions != self.cached_conditions:
                self.cached_conditions = conditions
                self.refresh_icon()
        def error_cb(e, tb):
            if type(e) is self.NetworkHandler.NetworkException and retries > 0:
                print "Warning in Weather:", e
                delay_seconds = 10.0
                print "Reattempt (%d retries remaining) in %d seconds" % (retries, delay_seconds)
                self.applet.timing.delay(lambda: self.refresh_conditions(retries - 1), delay_seconds)
            else:
                self.network_error_cb(e, tb)
        self.network_handler.get_conditions(self.settings['location_code'], callback=cb, error=error_cb)

    def refresh_icon(self, dummy_value=None):
        if self.cached_conditions is not None:
            unit = self.get_temperature_unit()
            temp = self.convert_temperature(self.cached_conditions['TEMP'])
            title = "%s: %s, %s" % (self.cached_conditions['CITY'], _(self.cached_conditions['DESCRIPTION']), temp + u" \u00B0" + unit)
            # display the "Feels Like" temperature in parens, if it is different from the actual temperature
            if self.cached_conditions['TEMP'] != self.cached_conditions['FEELSLIKE']:
                feels_like = self.convert_temperature(self.cached_conditions['FEELSLIKE'])
                if feels_like != "N/A" and feels_like != temp:
                    title += " (%s)" % (feels_like + u" \u00B0" + unit)
    
            self.applet.tooltip.set(title)
            self.set_icon(self.cached_conditions["CODE"])

    def fetch_forecast(self, cb, retries=3):
        """Use weather.com's XML service to download the latest 5-day
        forecast.

        """
        def error_cb(e, tb):
            if type(e) is self.NetworkHandler.NetworkException and retries > 0:
                print "Warning in Weather:", e
                delay_seconds = 10.0
                print "Reattempt (%d retries remaining) in %d seconds" % (retries, delay_seconds)
                self.applet.timing.delay(lambda: self.fetch_forecast(cb, retries - 1), delay_seconds)
            else:
                self.network_error_cb(e, tb)
        self.network_handler.get_forecast(self.settings['location_code'], callback=cb, error=error_cb)

    def fetch_weather_map(self, retries=3):
        """Download the latest weather map from weather.com, storing it
        as a pixbuf, and create a dialog with the new map.

        """
        def cb(pixbuf):
            self.set_map_pixbuf(pixbuf)
        def error_cb(e, tb):
            if type(e) is self.NetworkHandler.NetworkException and retries > 0:
                print "Warning in Weather:", e
                delay_seconds = 10.0
                print "Reattempt (%d retries remaining) in %d seconds" % (retries, delay_seconds)
                self.applet.timing.delay(lambda: self.fetch_weather_map(retries - 1), delay_seconds)
            else:
                self.network_error_cb(e, tb)
        self.network_handler.get_weather_map(self.settings['location_code'], callback=cb, error=error_cb)

    def set_map_pixbuf(self, pixbuf):
        """Create a map dialog from the current already-downloaded map
        image. Note that this does not show the dialog, it simply
        creates it. awnlib handles the rest.

        """
        if pixbuf is None:
            return
        if self.map_vbox is None:
            self.map_dialog = self.applet.dialog.new("secondary", title=self.settings['location'])
            self.map_vbox = gtk.VBox()
            self.map_dialog.add(self.map_vbox)
        else:
            for i in self.map_vbox.get_children():
                self.map_vbox.remove(i)
            self.map_dialog.set_title(self.settings['location'])

        self.map_pixbuf = pixbuf

        map_size = pixbuf.get_width(), pixbuf.get_height()

        # resize if necessary as defined by map_maxwidth
        ratio = float(self.settings['map_maxwidth']) / map_size[0]
        if ratio < 1:
            width, height = [int(ratio * dim) for dim in map_size]
            pixbuf = pixbuf.scale_simple(width, height, gtk.gdk.INTERP_BILINEAR)

        self.map_vbox.add(gtk.image_new_from_pixbuf(pixbuf))

    def convert_temperature(self, value):
        unit = temperature_units[self.settings["temperature-unit"]]
        try:
            value = float(value)
        except ValueError:
            return "N/A"

        if "Fahrenheit" == unit:
            converted_value = value
        elif "Celcius" == unit:
            converted_value = 5.0 * (value - 32.0) / 9.0
        return str(int(round(converted_value)))

    def get_temperature_unit(self):
        return temperature_units[self.settings["temperature-unit"]][0]

    def get_icon_name(self, hint, theme):
        if hint == "twc":
            return "twc-logo"

        hint = int(hint)

        if hint in (32, 34, 36):
            return "weather-clear"
        elif hint in (23, 24, 25, 28, 30, 44):
            return "weather-few-clouds"
        elif hint in (26, ):
            return "weather-overcast"
        elif hint in (5, 6, 7, 8, 9, 10, 11, 12, 45):
            # Special conditional for the extreme weather in moonbeam's Ottawa
            if theme == "moonbeam" and hint in (5, 6, 7):
                return "weather-snow-and-rain"
            return "weather-showers"
        elif hint in (40, ):
            return "weather-showers-scattered"
        elif hint in (13, 14, 15, 16, 17, 18, 41, 42, 43, 46):
            return "weather-snow"
        elif hint in (19, 20, 21, 22):
            return "weather-fog"
        elif hint in (4, 35, 37, 38, 39, 47):
            return "weather-storm"
        elif hint in (0, 1, 2, 3):
            return "weather-severe-alert"
        elif hint in (31, 33):
            return "weather-clear-night"
        elif hint in (27, 29):
            return "weather-few-clouds-night"

    class NetworkHandler(ThreadQueue):

        __ws_key = "&prod=xoap&par=1048871467&key=12daac2f3a67cb39&link=xoap"

        class NetworkException(Exception):
            pass

        def dictFromXML(self, rootNode, keys, paths):
            """Given an XML node, iterate over keys and paths, grabbing the
            value from each path and putting it into the dictionary as the
            given key.

            """
            returnDict = {}
            for key, path in zip(keys, paths):
                items = path.split('/')
                cnode = rootNode
                for item in items:
                    cnode = cnode.getElementsByTagName(item)[0]
                returnDict[key] = "".join([node.data for node in cnode.childNodes if node.nodeType == node.TEXT_NODE])
            return returnDict

        @async_method
        def get_locations(self, text):
            url = "http://xoap.weather.com/search/search?where=" + urllib2.quote(text)
            try:
                with closing(urllib2.urlopen(url)) as usock:
                    with unlink_xml(usock) as xmldoc:
                        locations_list = []
                        for i in xmldoc.getElementsByTagName("loc"):
                            city = i.childNodes[0].data
                            code = i.getAttribute("id")
                            locations_list.append([city, code])
                        return locations_list
            except urllib2.URLError, e:
                raise self.NetworkException("Couldn't download locations: %s" % e)

        @async_method
        @with_overlays
        def get_conditions(self, location_code):
            url = "http://xoap.weather.com/weather/local/" + location_code + "?cc=*" + self.__ws_key
            try:
                with closing(urllib2.urlopen(url)) as usock:
                    with unlink_xml(usock) as xmldoc:
                        names = ['CITY', 'SUNRISE', 'SUNSET', 'DESCRIPTION', 'CODE', 'TEMP', 'FEELSLIKE', 'BAR', 'BARDESC', 'WINDSPEED', 'WINDGUST', 'WINDDIR', 'HUMIDITY', 'MOONPHASE']
                        paths = ['weather/loc/dnam', 'sunr', 'suns', 'cc/t', 'cc/icon', 'cc/tmp', 'cc/flik', 'cc/bar/r', 'cc/bar/d', 'cc/wind/s', 'cc/wind/gust', 'cc/wind/d', 'cc/hmid', 'cc/moon/t']
                        try:
                            return self.dictFromXML(xmldoc, names, paths)
                        except IndexError, e:
                            raise self.NetworkException("Couldn't parse conditions: %s" % e)
            except urllib2.URLError, e:
                raise self.NetworkException("Couldn't download conditions: %s" % e)

        @async_method
        def get_weather_map(self, location_code):
            map_url = "http://www.weather.com/outlook/travel/businesstraveler/map/%s" % location_code
            try:
                with closing(urllib2.urlopen(map_url)) as usock:
                    mapExp = """<IMG NAME="mapImg" SRC="([^\"]+)" WIDTH=([0-9]+) HEIGHT=([0-9]+) BORDER"""
                    result = re.findall(mapExp, usock.read())
                    if not result or len(result) != 1:
                        raise self.NetworkException("Couldn't parse weather map")
                    with closing(urllib2.urlopen(result[0][0])) as raw_image:
                        with closing(gtk.gdk.PixbufLoader()) as loader:
                            loader.write(raw_image.read())
                            return loader.get_pixbuf()
            except urllib2.URLError, e:
                raise self.NetworkException("Couldn't download weather map: %s" % e)

        @async_method
        @with_overlays
        def get_forecast(self, location_code):
            url = "http://xoap.weather.com/weather/local/" + location_code + "?dayf=5" + self.__ws_key
            try:
                with closing(urllib2.urlopen(url)) as usock:
                    with unlink_xml(usock) as xmldoc:
                        try:
                            forecast = {'DAYS': []} #, 'CITY': cachedConditions['CITY']}
                            cityNode = xmldoc.getElementsByTagName('loc')[0].getElementsByTagName('dnam')[0]
                            forecast['CITY'] = ''.join([node.data for node in cityNode.childNodes if node.nodeType == node.TEXT_NODE])
    
                            dayNodes = xmldoc.getElementsByTagName('dayf')[0].getElementsByTagName('day')
                            for dayNode in dayNodes:
                                names = ['HIGH', 'LOW', 'CODE', 'DESCRIPTION', 'PRECIP', 'HUMIDITY', 'WSPEED', 'WDIR', 'WGUST']
                                paths = ['hi', 'low', 'part/icon', 'part/t', 'part/ppcp', 'part/hmid', 'part/wind/s', 'part/wind/t', 'part/wind/gust']
                                day = self.dictFromXML(dayNode, names, paths)
                                day.update({'WEEKDAY': dayNode.getAttribute('t'), 'YEARDAY': dayNode.getAttribute('dt')})
                                forecast['DAYS'].append(day)
                            return forecast
                        except IndexError, e:
                            raise self.NetworkException("Couldn't parse forecast: %s" % e)
            except urllib2.URLError, e:
                raise self.NetworkException("Couldn't download forecast: %s" % e)


if __name__ == "__main__":
    awnlib.init_start(WeatherApplet, {
        "name": applet_name, "short": "weather",
        "description": applet_description,
        "version": __version__,
        "author": "onox, Mike Desjardins, Mike Rooney",
        "copyright-year": "2007 - 2009",
        "theme": applet_logo,
        "authors": ["Mike Desjardins", "Mike Rooney", "Isaac J.", "onox <denkpadje@gmail.com>"],
        "artists": ["Wojciech Grzanka", "Mike Desjardins"],
        "type": ["Network", "Weather"]},
        ["settings-per-instance"])
