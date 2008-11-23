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

import math
import os
import time

import pygtk
pygtk.require("2.0")
import gtk
from gtk import glade

from awn.extras import AWNLib
import cairo
import rsvg

import locations

applet_name = "Cairo Clock"
applet_version = "0.2.8"
applet_description = "Applet that displays an analog clock using\n(optionally) MacSlow's Cairo-Clock's themes"

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "cairo-clock-logo.svg")

# Interval in seconds between two successive draws of the clock
draw_clock_interval = 1.0

cairo_clock_themes_dir = "/usr/share/cairo-clock/themes"
default_themes_dir = os.path.join(os.path.dirname(__file__), "themes")
default_theme = "gnome"

glade_file = os.path.join(os.path.dirname(__file__), "cairo-clock.glade")

# List of all available plugins
plugin_classes = [locations.Locations]


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
        applet.connect("height-changed", lambda w, e: self.__clock_updater.draw_clock_cb())
        
        applet.timing.register(self.__clock_updater.draw_clock_cb, draw_clock_interval)
    
    def setup_main_dialog(self):
        dialog = self.applet.dialog.new("main")
        
        vbox = gtk.VBox(spacing=6)
        vbox.set_focus_chain([])
        dialog.add(vbox)
        
        for i in self.__plugins:
            expander = gtk.Expander("<b>" + i.get_name() + "</b>")
            expander.set_use_markup(True)
            expander.set_expanded(True)
            
            callback = i.get_callback()
            
            element = i.get_element()
            
            # Add extra padding because of the callback button
            if callback is not None:
                alignment = gtk.Alignment()
                alignment.set_padding(6, 0, 0, 0)
                alignment.add(element)
                expander.add(alignment)
            else:
                expander.add(element)
            
            hbox = gtk.HBox()
            hbox.add(expander)
            
            if callback is not None:
                label = gtk.Label("<small>" + callback[0] + "</small>")
                label.set_use_markup(True)
                button = gtk.Button()
                button.add(label)
                
                """ Get the wrapper via an additional function to avoid that
                every wrapper uses "callback[1]"'s last binded value """
                def get_clicked_cb(cb):
                    def clicked_cb(widget):
                        cb()
                    return clicked_cb
                button.connect("clicked", get_clicked_cb(callback[1]))
                
                alignment = gtk.Alignment(xalign=1.0)                    
                alignment.add(button)
                hbox.pack_start(alignment, expand=False)
                
                def hide_edit_button_cb(widget):
                    if not widget.get_expanded(): # Old state of expander
                        button.show()
                    else:
                        button.hide()
                expander.connect("activate", hide_edit_button_cb)
            
            vbox.add(hbox)
            i.set_parent_container(hbox)
        
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
            "theme": default_theme
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
            label.set_markup("<i><b>Note:</b> you can choose more themes by\ninstalling MacSlow's Cairo-Clock's\nthemes</i>")
            vbox_theme.add(label)
        
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
        
        self.__clock = AnalogClock(self)
    
    def update_title(self):
        """Update the title according to the settings.
        
        """
        if not self.applet.title.is_visible():
            return
        
        if self.default_values["time-24-format"]:
            hours = "%H"
            ampm = ""
        else:
            hours = "%I"
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
        
        self.applet.title.set(time.strftime(date + hours + ":%M" + seconds + ampm + year))
        self.applet.title.show()
    
    def draw_clock_cb(self):
        """Draw the clock and update the title to keep it synchronized with
        the drawn clock.
        
        """
        self.__clock.draw_clock()
        self.update_title()
        
        return True
    
    def load_theme(self):
        self.__clock.load_theme()

class AnalogClock:

    """Renders an analog clock using SVG files as the applet icon.
    
    """
    
    def __init__(self, clock_updater):
        self.applet = clock_updater.applet
        self.default_values = clock_updater.default_values
    
    def load_theme(self):
        """Load the necessary SVG files of the specified theme.
        
        """
        theme = self.get_theme_dir(self.default_values["theme"])
        
        get_theme = lambda filename, theme: rsvg.Handle(os.path.join(theme, filename))
        
        # Background
        self.clock_drop_shadow = get_theme('clock-drop-shadow.svg', theme)
        self.clock_face = get_theme('clock-face.svg', theme)
        self.clock_marks = get_theme('clock-marks.svg', theme)
        
        # Foreground
        self.clock_face_shadow = get_theme('clock-face-shadow.svg', theme)
        self.clock_glass = get_theme('clock-glass.svg', theme)
        self.clock_frame = get_theme('clock-frame.svg', theme)
        
        # Shadows of hands
        self.clock_hour_hand_shadow = get_theme('clock-hour-hand-shadow.svg', theme)
        self.clock_minute_hand_shadow = get_theme('clock-minute-hand-shadow.svg', theme)
        self.clock_second_hand_shadow = get_theme('clock-second-hand-shadow.svg', theme)
        
        # Hands
        self.clock_hour_hand = get_theme('clock-hour-hand.svg', theme)
        self.clock_minute_hand = get_theme('clock-minute-hand.svg', theme)
        self.clock_second_hand = get_theme('clock-second-hand.svg', theme)
        
        self.__previous_state = None
    
    def get_theme_dir(self, theme):
        theme_dirs = (cairo_clock_themes_dir, default_themes_dir)
        
        for theme_dir in theme_dirs:
            path = os.path.join(theme_dir, theme)
            if os.path.isdir(path):
                return path
        
        raise RuntimeError, "Did not find path to theme '" + theme + "'"
    
    def create_scaled_surface(self, source_surface, height):
        surface = source_surface.create_similar(cairo.CONTENT_COLOR_ALPHA, height, height)
        context = cairo.Context(surface)
        
        svg_width, svg_height = map(float, self.clock_face.get_dimension_data()[:2])
        context.scale(height / svg_width, height / svg_height)
        
        return surface, context
    
    def setup_background_foreground(self, source_surface, height):
        """Create new Cairo surfaces for the background and foreground.
        
        """
        self.__background_surface, background_context = self.create_scaled_surface(source_surface, height)
        
        # Draw the background of the clock
        self.clock_drop_shadow.render_cairo(background_context)
        self.clock_face.render_cairo(background_context)
        self.clock_marks.render_cairo(background_context)
        
        self.__foreground_surface, foreground_context = self.create_scaled_surface(source_surface, height)
        
        # Draw the foreground of the clock
        self.clock_face_shadow.render_cairo(foreground_context)
        self.clock_glass.render_cairo(foreground_context)
        self.clock_frame.render_cairo(foreground_context)
    
    def draw_clock(self):
        """Render the SVGs on a Cairo surface and uses it as the applet's icon.
        
        """
        local_time = time.localtime()
        hours, minutes, seconds = (local_time[3], local_time[4], local_time[5])
        
        height = self.applet.get_height()
        show_seconds_hand = self.default_values["show-seconds-hand"]
        
        new_state = (show_seconds_hand, height, self.default_values["theme"], hours, minutes)
        if not show_seconds_hand and self.__previous_state == new_state:
            return
        
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
        context = cairo.Context(surface)
        
        if self.__previous_state is None or (self.__previous_state and height != self.__previous_state[1]):
            self.setup_background_foreground(surface, height)
        
        self.__previous_state = new_state
        
        svg_width, svg_height = map(float, self.clock_face.get_dimension_data()[:2])
        
        # Draw the background of the clock
        context.set_operator(cairo.OPERATOR_SOURCE)
        context.set_source_surface(self.__background_surface)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)
        
        # Scale hands (after having painted the background to avoid messing it up)
        context.scale(height / svg_width, height / svg_height)
        
        context.save()
        
        context.translate(svg_width / 2, svg_height / 2)
        
        # Draw the hour hand
        context.save()
        context.rotate((360/12) * (hours+9+(minutes/60.0)) * (math.pi/180))
        self.clock_hour_hand_shadow.render_cairo(context)
        self.clock_hour_hand.render_cairo(context)
        context.restore()
        
        # Draw the minute hand
        context.save()
        context.rotate((360/60) * (minutes+45) * (math.pi/180))
        self.clock_minute_hand_shadow.render_cairo(context)
        self.clock_minute_hand.render_cairo(context)
        context.restore()
        
        # Draw the second hand if configured to do so
        if show_seconds_hand:
            context.save()
            context.rotate((360/60) * (seconds+45) * (math.pi/180))
            self.clock_second_hand_shadow.render_cairo(context)
            self.clock_second_hand.render_cairo(context)
            context.restore()
        
        context.restore()
        
        # Don't scale to avoid messing up the foreground
        context.scale(svg_width / height, svg_height / height)
        
        # Draw foreground of the clock
        context.set_source_surface(self.__foreground_surface)
        context.paint()
        
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