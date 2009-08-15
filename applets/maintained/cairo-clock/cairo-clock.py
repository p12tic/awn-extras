#!/usr/bin/python
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

import os
import time

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib
import cairo

from analogclock import *
import locations

applet_name = "Cairo Clock"
applet_version = "0.3.3"
applet_description = "Applet that displays an analog clock and supports additional clocks for different locations"

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "cairo-clock-logo.svg")

# Interval in seconds between two successive draws of the clock
draw_clock_interval = 1.0

default_theme = "gnome"

ui_file = os.path.join(os.path.dirname(__file__), "cairo-clock.ui")

# List of all available plugins
plugin_classes = frozenset([locations.Locations])


class CairoClockApplet:

    """Applet that display an analog clock.

    """

    def __init__(self, applet):
        self.applet = applet

        # Initialize useable plugins
        self.__plugins = [plugin(self) for plugin in plugin_classes if plugin.plugin_useable()]

        self.setup_main_dialog()
        self.setup_context_menu()

        self.__clock_updater = ClockUpdater(self)

        self.__clock_updater.load_theme()
        self.__clock_updater.draw_clock_cb()

        applet.tooltip.connect_becomes_visible(self.__clock_updater.update_title)
        applet.connect_size_changed(self.__clock_updater.draw_clock_cb)

        applet.timing.register(self.__clock_updater.draw_clock_cb, draw_clock_interval)

    def setup_main_dialog(self):
        dialog = self.applet.dialog.new("main")

        vbox = gtk.VBox(spacing=6)
        vbox.set_focus_chain([])
        dialog.add(vbox)

        """ Plug-ins """
        for i in self.__plugins:
            plugin_vbox = gtk.VBox(spacing=6)

            hbox = gtk.HBox()
            plugin_vbox.add(hbox)

            expander = gtk.Expander("<b>" + i.get_name() + "</b>")
            expander.set_use_markup(True)
            expander.set_expanded(True)
            hbox.pack_start(expander, expand=False)

            expander_vbox = gtk.VBox()

            callback = i.get_callback()
            if callback is not None:
                alignment = gtk.Alignment(xalign=1.0)
                hbox.add(alignment)

                label = gtk.Label("<small>" + callback[0] + "</small>")
                label.set_use_markup(True)
                button = gtk.Button()
                button.add(label)
                alignment.add(button)

                button.connect("clicked", lambda w, cb: cb(), callback[1])

                def toggle_callback_button_cb(widget, button):
                    if not widget.get_expanded(): # Old state of expander
                        button.set_no_show_all(False)
                        button.show()
                    else:
                        button.hide()
                        button.set_no_show_all(True)
                expander.connect("activate", toggle_callback_button_cb, button)

            def toggle_expander_vbox_cb(widget, vbox):
                if not widget.get_expanded(): # Old state of expander
                    vbox.set_no_show_all(False)
                    vbox.show_all()
                else:
                    vbox.hide_all()
                    vbox.set_no_show_all(True)
            expander.connect("activate", toggle_expander_vbox_cb, expander_vbox)

            expander_vbox.add(i.get_element())
            plugin_vbox.add(expander_vbox)
            i.set_parent_container(plugin_vbox)
            vbox.add(plugin_vbox)

        """ Calendar """
        calendar = gtk.Calendar()
        calendar.props.show_week_numbers = True
        vbox.add(calendar)

    def setup_context_menu(self):
        self.preferences_notebook = gtk.Notebook()
        self.preferences_notebook.props.border_width = 6
        self.applet.dialog.new("preferences").vbox.add(self.preferences_notebook)

        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        self.setup_general_preferences(prefs)
        self.setup_plugins_preferens(prefs)

    def setup_general_preferences(self, prefs):
        container = gtk.VBox()
        prefs.get_object("vbox-general").reparent(container)
        self.preferences_notebook.append_page(container, gtk.Label("General"))

        refresh_title = lambda v: self.__clock_updater.update_title()
        refresh_clock = lambda v: self.__clock_updater.draw_clock_cb()

        default_values = {
            "time-24-format": (True, refresh_title, prefs.get_object("radio-24-format")),  # True if the time in the title must display 24 hours, False if AM/PM
            "time-date": (True, refresh_title, prefs.get_object("check-time-date")),
            "time-seconds": (True, refresh_title, prefs.get_object("check-time-seconds")),
            "show-seconds-hand": (True, refresh_clock, prefs.get_object("check-second-hand")),  # True if the clock must display a second hand, False otherwise
            "theme": default_theme,
            "custom-time-format": ""
        }
        self.settings = self.applet.settings.load_preferences(default_values)

        self.themes = os.listdir(default_themes_dir)

        if os.path.isdir(cairo_clock_themes_dir):
            self.themes.extend(os.listdir(cairo_clock_themes_dir))

        # Remove duplicates and sort the list
        self.themes = list(set(self.themes))
        self.themes.sort()

        combobox_theme = prefs.get_object("combobox-theme")
        awnlib.add_cell_renderer_text(combobox_theme)
        for i in self.themes:
            combobox_theme.append_text(i)

        theme = self.settings["theme"]
        if theme not in self.themes:
            self.applet.settings["theme"] = theme = default_theme

        combobox_theme.set_active(self.themes.index(theme))
        combobox_theme.connect("changed", self.combobox_theme_changed_cb)

    def setup_plugins_preferens(self, prefs):
        for i in self.__plugins:
            preferences = i.get_preferences(prefs)
            if preferences is not None:
                container = gtk.VBox()
                preferences.reparent(container)
                page_number = self.preferences_notebook.append_page(container, gtk.Label(i.get_name()))
                i.set_preferences_page_number(page_number)

    def combobox_theme_changed_cb(self, combobox):
        self.applet.settings["theme"] = self.themes[combobox.get_active()]

        # Load the new theme and update the clock
        self.__clock_updater.load_theme()
        self.__clock_updater.draw_clock_cb()


class ClockUpdater:

    """Redraws the clock and sets the title (when visible) every second.

    """

    def __init__(self, clock_applet):
        self.applet = clock_applet.applet
        self.settings = clock_applet.settings

        self.__clock = AppletAnalogClock(self)

    def update_title(self):
        """Update the title according to the settings or a custom time
        format if it's not empty.

        """
        if not self.applet.tooltip.is_visible():
            return

        if len(self.settings["custom-time-format"]) > 0:
            format = self.settings["custom-time-format"]
        else:
            if self.settings["time-24-format"]:
                hours = "%H"
                ampm = ""
            else:
                # Strip leading zero for single-digit hours
                hours = str(int(time.strftime("%I")))
                ampm = " %p"

            if self.settings["time-seconds"]:
                seconds = ":%S"
            else:
                seconds = ""

            format = hours + ":%M" + seconds + ampm

            if self.settings["time-date"]:
                format = "%a %b %d " + format + " %Y"

        self.applet.tooltip.set(time.strftime(format))

    def draw_clock_cb(self):
        """Draw the clock and update the title to keep it synchronized with
        the drawn clock.

        """
        self.__clock.draw_clock()
        self.update_title()

        return True

    def load_theme(self):
        provider = AnalogClockThemeProvider(self.settings["theme"])
        self.__clock.load_theme(provider)


class AppletAnalogClock:

    """Renders an analog clock using SVG files as the applet icon.

    """

    def __init__(self, clock_updater):
        self.applet = clock_updater.applet
        self.settings = clock_updater.settings

    def load_theme(self, provider):
        self.__theme = provider
        self.__previous_state = None

    def draw_clock(self):
        """Render the SVGs on a Cairo surface and uses it as the applet's icon.

        """
        local_time = time.localtime()
        hours, minutes, seconds = (local_time[3], local_time[4], local_time[5])

        height = self.applet.get_size()
        show_seconds_hand = self.settings["show-seconds-hand"]

        new_state = (show_seconds_hand, height, self.__theme.get_name(), hours, minutes)
        if not show_seconds_hand and self.__previous_state == new_state:
            return

        if self.__previous_state is None or height != self.__previous_state[1]:
            self.__base_clock = AnalogClock(self.__theme, height)

        self.__previous_state = new_state

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
        context = cairo.Context(surface)

        if not show_seconds_hand:
            seconds = None
        self.__base_clock.draw_clock(context, height, hours, minutes, seconds)

        self.applet.icon.set(context)


if __name__ == "__main__":
    awnlib.init_start(CairoClockApplet, {"name": applet_name,
        "short": "cairo-clock",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": "2008 - 2009",
        "authors": ["onox <denkpadje@gmail.com>"],
        "artists": ["Lapo Calamandrei", "Rodney Dawes", "Jakub Steiner", "Artists of MacSlow's Cairo-Clock"]},
        ["settings-per-instance"])
