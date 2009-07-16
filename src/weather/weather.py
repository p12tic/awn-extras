#!/usr/bin/python
# Copyright (C) 2007, 2008:
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
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

import os
import re
import threading
import urllib2
from xml.dom import minidom

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib
from awn import OverlayText

import cairo
import glib

applet_name = "Weather"
applet_version = "0.3.3"
applet_description = "Applet to display current weather and forecast"

# Applet's themed icon, also shown in the GTK About dialog
applet_logo = "weather-few-clouds"

# Interval in minutes between updating conditions, forecast, and map
update_interval = 30

# Timeout in secons of network operations
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

APP = "awn-weather-applet"
import gettext
import locale
DIR = os.path.dirname(__file__) + '/locale'
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

import forecast


class WeatherApplet:

    def __init__(self, applet):
        self.applet = applet

        self.cachedConditions = None
        self.iconPixBuf = None

        self.map_vbox = None
        self.image_map = None

        self.setup_context_menu()

        self.forecaster = forecast.Forecast(self)
        self.onRefreshForecast = self.forecaster.onRefreshForecast # <3 python

        # Set default icons/titles/dialogs so the applet is informative without data
        self.set_icon()
        self.applet.tooltip.set("%s %s..."%(_("Fetching conditions for"), self.settings['location']))

        self.__temp_overlay = OverlayText()
        self.__temp_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH
        applet.add_overlay(self.__temp_overlay)

        # Set up the timer which will refresh the conditions, forecast, and weather map
        applet.timing.register(self.activate_refresh_cb, update_interval * 60)
        applet.timing.delay(self.activate_refresh_cb, 1.0)

    def setup_context_menu(self):
        """Add "refresh" to the context menu and setup the preferences.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        refresh_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_REFRESH)
        refresh_item.connect("activate", self.activate_refresh_cb)
        menu.insert(refresh_item, menu_index)

        menu.insert(gtk.SeparatorMenuItem(), menu_index + 1)

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
        refresh_map = lambda v: self.createMapDialog(self.map_pixbuf)
        refresh_location_label = lambda v: self.location_label.set_markup("<b>%s</b>" % v)
        refresh_location = lambda v: self.activate_refresh_cb()

        # Only use themes that are likely to provide all the files
        def filter_theme(theme):
            return os.path.isfile(os.path.join(theme_dir, theme, "scalable/status/weather-clear.svg"))
        self.themes = [system_theme_name] + filter(filter_theme, os.listdir(theme_dir))
        self.themes.sort()
        self.themes.extend(["moonbeam"])

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
        awnlib.add_cell_renderer_text(fontsize_combobox)
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

            url = "http://xoap.weather.com/search/search?where=" + urllib2.quote(text)
            try:
                usock = urllib2.urlopen(url)
            except:
                print "Weather Applet: Unexpected error while fetching locations"
            else:
                xmldoc = minidom.parse(usock)
                usock.close()

                self.search_list.clear()

                locations = xmldoc.getElementsByTagName("loc")
                if len(locations) > 0:
                    self.treeview.set_sensitive(True)
                    for loc in locations:
                        city = loc.childNodes[0].data
                        code = loc.getAttribute("id")
                        self.search_list.append([city, code])
                else:
                    self.search_list.append([_("No records found"), None])

                xmldoc.unlink()

    def ok_button_clicked_cb(self, widget=None):
        (model, iter) = self.treeview.get_selection().get_selected()
        self.applet.settings["location_code"] = model.get_value(iter, 1)
        self.applet.settings["location"] = model.get_value(iter, 0)

        self.search_window.hide()

    def activate_refresh_cb(self, widget=None, map=True):
        """Refresh the icon, forecast, and map data. Called by the
        "Refresh" option in the context menu.

        """
        def refresh():
            self.refresh_conditions()
            self.onRefreshForecast()
            if map:
                self.onRefreshMap()
        threading.Thread(target=refresh).start()

    def setup_theme(self):
        def refresh_theme():
            states_names = {}
            for i in icon_states:
                states_names[i] = i
            self.applet.theme.set_states(states_names)

            theme = self.settings["theme"] if self.settings["theme"] != system_theme_name else None
            self.applet.theme.theme(theme)
        glib.idle_add(refresh_theme)

    def getAttributes(self):
        return self.settings['location_code'], self.settings['temperature-unit'], self.cachedConditions

    def set_icon(self, hint="twc"):
        def refresh_overlay():
            state = self.get_icon_name(hint, self.settings["theme"])
            self.applet.theme.icon(state)

            if hint != 'twc':
                self.__temp_overlay.props.font_sizing = font_sizes[self.settings['temperature-font-size']]
                self.__temp_overlay.props.text = tempText = self.convert_temperature(self.cachedConditions['TEMP']) + u"\u00B0"
                self.__temp_overlay.props.active = bool(self.settings["show-temperature-icon"])
        glib.idle_add(refresh_overlay)

    def refresh_conditions(self):
        """Download the current weather conditions. If this fails, or the
        conditions are unchanged, don't do anything. Refresh the applet's
        title and icon if the conditions have changed.

        """
        url = 'http://xoap.weather.com/weather/local/' + self.settings['location_code'] + '?cc=*&prod=xoap&par=1048871467&key=12daac2f3a67cb39&link=xoap'
        try:
            usock = urllib2.urlopen(url)
        except:
            print "Weather Applet: Unexpected error while fetching conditions"
        else:
            xmldoc = minidom.parse(usock)
            usock.close()

            names=['CITY', 'SUNRISE', 'SUNSET', 'DESCRIPTION', 'CODE', 'TEMP', 'FEELSLIKE', 'BAR', 'BARDESC', 'WINDSPEED', 'WINDGUST', 'WINDDIR', 'HUMIDITY', 'MOONPHASE']
            paths=['weather/loc/dnam', 'sunr', 'suns', 'cc/t', 'cc/icon', 'cc/tmp', 'cc/flik', 'cc/bar/r', 'cc/bar/d', 'cc/wind/s', 'cc/wind/gust', 'cc/wind/d', 'cc/hmid', 'cc/moon/t']
            conditions = self.dictFromXML(xmldoc, names, paths)
            xmldoc.unlink()

            if conditions != self.cachedConditions:
                self.cachedConditions = conditions
                self.refresh_icon()
            return conditions

    def refresh_icon(self, dummy_value=None):
        unit = self.get_temperature_unit()
        temp = self.convert_temperature(self.cachedConditions['TEMP'])
        title = "%s: %s, %s" % (self.cachedConditions['CITY'], _(self.cachedConditions['DESCRIPTION']), temp + u" \u00B0" + unit)
        #display the "Feels Like" temperature in parens, if it is different from the actual temperature
        if self.cachedConditions['TEMP'] != self.cachedConditions['FEELSLIKE']:
            feels_like = self.convert_temperature(self.cachedConditions['FEELSLIKE'])
            title += " (%s)" % (feels_like + u" \u00B0" + unit)

        self.applet.tooltip.set(title)
        self.set_icon(self.cachedConditions["CODE"])

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
            returnDict[key] = ''.join([node.data for node in cnode.childNodes if node.nodeType == node.TEXT_NODE])
        return returnDict

    def onRefreshMap(self):
        """Download the latest weather map from weather.com, storing it
        as a pixbuf, and create a dialog with the new map.

        """
        try:
            page = urllib2.urlopen('http://www.weather.com/outlook/travel/businesstraveler/map/' + self.settings['location_code']).read()
        except:
            print "Weather Applet: Unable to download weather map"
        else:
            mapExp = """<IMG NAME="mapImg" SRC="([^\"]+)" WIDTH=([0-9]+) HEIGHT=([0-9]+) BORDER"""
            result = re.findall(mapExp, page)
            if result and len(result) == 1:
                imgSrc, width, height = result[0]
                rawImg = urllib2.urlopen(imgSrc)
                pixbufLoader = gtk.gdk.PixbufLoader()
                pixbufLoader.write(rawImg.read())
                mapPixBuf = pixbufLoader.get_pixbuf()
                pixbufLoader.close()

                self.createMapDialog(mapPixBuf)

    def createMapDialog(self, pixbuf):
        """Create a map dialog from the current already-downloaded map
        image. Note that this does not show the dialog, it simply
        creates it. awnlib handles the rest.

        """
        if self.map_vbox is None:
            self.map_dialog = self.applet.dialog.new("secondary", title=self.settings['location'])
            self.map_vbox = gtk.VBox()
            self.map_dialog.add(self.map_vbox)
        else:
            for i in self.map_vbox.get_children():
                self.map_vbox.remove(i)
            self.map_dialog.set_title(self.settings['location'])

        self.map_pixbuf = pixbuf

        print "creating new map..."
        mapSize = pixbuf.get_width(), pixbuf.get_height()

        # resize if necessary as defined by map_maxwidth
        ratio = float(self.settings['map_maxwidth']) / mapSize[0]
        if ratio < 1:
            newX, newY = [int(ratio * dim) for dim in mapSize]
            pixbuf = pixbuf.scale_simple(newX, newY, gtk.gdk.INTERP_BILINEAR)

        self.map_vbox.add(gtk.image_new_from_pixbuf(pixbuf))

    def convert_temperature(self, value):
        unit = temperature_units[self.settings["temperature-unit"]]
        value = float(value)

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


if __name__ == "__main__":
    awnlib.init_start(WeatherApplet, {
        "name": applet_name, "short": "weather",
        "description": applet_description,
        "version": applet_version,
        "author": "onox, Mike Desjardins, Mike Rooney",
        "copyright-year": "2007 - 2009",
        "theme": applet_logo,
        "authors": ["Mike Desjardins", "Mike Rooney", "Isaac J.", "onox <denkpadje@gmail.com>"],
        "artists": ["Wojciech Grzanka", "Mike Desjardins"],
        "type": ["Network", "Weather"]},
        ["settings-per-instance"])
