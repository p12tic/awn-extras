#!/usr/bin/python
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
import time

import pygtk
pygtk.require("2.0")
import gtk
from gtk import glade

from awn.extras import AWNLib
import cairo

from analogclock import *
import locations

applet_name = "Cairo Clock"
applet_version = "0.3.1"
applet_description = "Applet that displays an analog clock using\n(optionally) MacSlow's Cairo-Clock's themes"

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "cairo-clock-logo.svg")

# Interval in seconds between two successive draws of the clock
draw_clock_interval = 1.0

default_theme = "gnome"

glade_file = os.path.join(os.path.dirname(__file__), "cairo-clock.glade")

# Notice displayed in the preferences window
themes_notice = "you can choose more themes by installing MacSlow's Cairo-Clock's themes"

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

        applet.connect("enter-notify-event", lambda w, e: self.__clock_updater.update_title())
        applet.connect("size-changed", lambda w, e: self.__clock_updater.draw_clock_cb())
        
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

                def toggle_edit_button_cb(widget, button):
                    if not widget.get_expanded(): # Old state of expander
                        button.set_no_show_all(False)
                        button.show()
                    else:
                        button.hide()
                        button.set_no_show_all(True)
                expander.connect("activate", toggle_edit_button_cb, button)

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

        prefs = glade.XML(glade_file)

        self.setup_general_preferences(prefs)
        self.setup_plugins_preferens(prefs)

    def setup_general_preferences(self, prefs):
        container = gtk.VBox()
        prefs.get_widget("vbox-general").reparent(container)
        self.preferences_notebook.append_page(container, gtk.Label("General"))

        self.default_values = {
            "time-24-format": True, # True if the time in the title must display 24 hours, False if AM/PM
            "time-date": True,
            "time-seconds": True,
            "show-seconds-hand": True, # True if the clock must display a second hand, False otherwise
            "theme": default_theme,
            "custom-time-format": ""
        }
        self.applet.settings.load(self.default_values)

        # Time format
        radio_24_format = prefs.get_widget("radio-24-format")
        radio_24_format.set_active(self.default_values["time-24-format"])
        radio_24_format.connect("toggled", self.radiobutton_24_format_toggled_cb)

        # Showing date in title
        check_title_date = prefs.get_widget("check-time-date")
        check_title_date.set_active(self.default_values["time-date"])
        check_title_date.connect("toggled", self.checkbox_title_date_toggled_cb)

        # Showing seconds in title
        check_title_seconds = prefs.get_widget("check-time-seconds")
        check_title_seconds.set_active(self.default_values["time-seconds"])
        check_title_seconds.connect("toggled", self.checkbox_title_seconds_toggled_cb)

        # Showing the seconds hand in the applet's icon
        checkbox_second_hand = prefs.get_widget("check-second-hand")
        checkbox_second_hand.set_active(self.default_values["show-seconds-hand"])
        checkbox_second_hand.connect("toggled", self.seconds_hand_toggled_cb)

        # Combobox in preferences window to choose a theme
        vbox_theme = prefs.get_widget("vbox-theme")

        combobox_theme = gtk.combo_box_new_text()
        vbox_theme.add(combobox_theme)
        prefs.get_widget("label-vbox-theme").set_mnemonic_widget(combobox_theme)

        self.themes = os.listdir(default_themes_dir)

        if os.path.isdir(cairo_clock_themes_dir):
            self.themes.extend(os.listdir(cairo_clock_themes_dir))
        else:
            label = gtk.Label()
            label.set_markup("<i><b>Note:</b> %s</i>" % themes_notice)
            label.set_alignment(0.0, 0.5)
            label.set_line_wrap(True)
            prefs.get_widget("theme-vbox").add(label)

        # Remove duplicates and sort the list
        self.themes = list(set(self.themes))
        self.themes.sort()

        for i in self.themes:
            combobox_theme.append_text(i)

        theme = self.default_values["theme"]
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

    def checkbox_title_date_toggled_cb(self, button):
        self.applet.settings["time-date"] = button.get_active()
        self.__clock_updater.update_title()

    def checkbox_title_seconds_toggled_cb(self, button):
        self.applet.settings["time-seconds"] = button.get_active()
        self.__clock_updater.update_title()

    def radiobutton_24_format_toggled_cb(self, button):
        self.applet.settings["time-24-format"] = button.get_active()
        self.__clock_updater.update_title()

    def seconds_hand_toggled_cb(self, button):
        self.applet.settings["show-seconds-hand"] = button.get_active()

        # Update clock immediately
        self.__clock_updater.draw_clock_cb()


class ClockUpdater:

    """Redraws the clock and sets the title (when visible) every second.

    """

    def __init__(self, clock_applet):
        self.applet = clock_applet.applet
        self.default_values = clock_applet.default_values

        self.__clock = AppletAnalogClock(self)

    def update_title(self):
        """Update the title according to the settings or a custom time
        format if it's not empty.

        """
        if not self.applet.title.is_visible():
            return

        if len(self.default_values["custom-time-format"]) > 0:
            format = self.default_values["custom-time-format"]
        else:
            if self.default_values["time-24-format"]:
                hours = "%H"
                ampm = ""
            else:
                # Strip leading zero for single-digit hours
                hours = str(int(time.strftime("%I")))
                ampm = " %p"

            if self.default_values["time-seconds"]:
                seconds = ":%S"
            else:
                seconds = ""

            if self.default_values["time-date"]:
                date = "%a %b %d "
                year = " %Y"
            else:
                date = ""
                year = ""

            format = date + hours + ":%M" + seconds + ampm + year

        self.applet.title.set(time.strftime(format))
        self.applet.title.show()

    def draw_clock_cb(self):
        """Draw the clock and update the title to keep it synchronized with
        the drawn clock.

        """
        self.__clock.draw_clock()
        self.update_title()

        return True

    def load_theme(self):
        provider = AnalogClockThemeProvider(self.default_values["theme"])
        self.__clock.load_theme(provider)


class AppletAnalogClock:

    """Renders an analog clock using SVG files as the applet icon.

    """

    def __init__(self, clock_updater):
        self.applet = clock_updater.applet
        self.default_values = clock_updater.default_values

    def load_theme(self, provider):
        self.__theme = provider
        self.__previous_state = None

    def draw_clock(self):
        """Render the SVGs on a Cairo surface and uses it as the applet's icon.

        """
        local_time = time.localtime()
        hours, minutes, seconds = (local_time[3], local_time[4], local_time[5])
        
        height = self.applet.get_size()
        show_seconds_hand = self.default_values["show-seconds-hand"]

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
    applet = AWNLib.initiate({"name": applet_name, "short": "cairo-clock",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": 2008,
        "authors": ["onox"],
        "artists": ["Lapo Calamandrei", "Rodney Dawes", "Jakub Steiner", "Artists of MacSlow's Cairo-Clock"]},
        ["settings-per-instance"])
    CairoClockApplet(applet)
    AWNLib.start(applet)
