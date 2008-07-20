#!/usr/bin/env python
#
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

import gobject
import pygtk
pygtk.require("2.0")
import cairo
import gtk
from gtk import gdk
from gtk import glade
from awn.extras import AWNLib
import rsvg

# Interval in milliseconds between two successive draws of the clock
draw_clock_interval = 1000

applet_name = "Cairo Clock"
applet_version = "0.2.8"
applet_description = "Applet that displays an analog clock using\n(optionally) MacSlow's Cairo-Clock's themes"

theme_dir = "/usr/share/cairo-clock/themes"
default_theme = os.path.join(os.path.dirname(__file__), "themes", "tango")
glade_file = os.path.join(os.path.dirname(__file__), "cairo-clock.glade")

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "cairo-clock-logo.png")


class CairoClockApplet:
    """ Applet that display an analog clock """
    
    def __init__(self, applet):
        self.applet = applet
        
        self.clock = ClockUpdater(applet)
        
        self.setup_main_dialog()
        self.setup_context_menu()
        
        self.clock.draw_clock_cb()
        
        applet.connect("enter-notify-event", lambda w, e: self.clock.enable_title(True))
        applet.connect("leave-notify-event", lambda w, e: self.clock.enable_title(False))
        
        gobject.timeout_add(draw_clock_interval, self.clock.draw_clock_cb)
    
    def setup_main_dialog(self):
        dialog = self.applet.dialog.new("calendar-dialog")
        
        calendar = gtk.Calendar()
        calendar.props.show_week_numbers = True
        
        dialog.add(calendar)
        
        self.dialog_focus_lost_time = time.time()
        self.applet.connect("button-press-event", self.button_press_event_cb)
        dialog.connect("focus-out-event", self.dialog_focus_out_cb)
    
    def button_press_event_cb(self, widget, event):
        if event.button == 1 and (time.time() - self.dialog_focus_lost_time) > 0.01:
            self.applet.dialog.toggle("calendar-dialog")
            self.clock.title_is_visible = False
    
    def dialog_focus_out_cb(self, dialog, event):
        self.dialog_focus_lost_time = time.time()
    
    def setup_context_menu(self):
        """ Creates a context menu to activate "Preferences" ("About" window
        is created automatically by AWNLib) """
        
        prefs_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        prefs_item.connect("activate", self.show_dialog_cb)
        
        self.applet.dialog.menu.insert(prefs_item, 3)
        
        prefs = glade.XML(glade_file)
        prefs.get_widget("dialog-vbox").reparent(self.applet.dialog.new("preferences").vbox)
        
        self.setup_dialog_settings(prefs)
    
    def show_dialog_cb(self, widget):
        self.applet.dialog.toggle("preferences", "show")
    
    def setup_dialog_settings(self, prefs):
        """ Loads the settings """
        
        default_values = {
            "time-24-format": self.clock.time_24_format,
            "time-date": self.clock.time_date,
            "time-seconds": self.clock.time_seconds,
            "show-second-hand": self.clock.show_second_hand,
            "theme": "tango"
        }
        self.applet.settings.load(default_values)
        
        # Time format
        self.clock.time_24_format = self.applet.settings["time-24-format"]
        
        radio_24_format = prefs.get_widget("radio-24-format")
        radio_24_format.set_active(self.clock.time_24_format)
        radio_24_format.connect("toggled", self.radiobutton_24_format_toggled_cb)
        
        # Showing date in title
        self.clock.time_date = self.applet.settings["time-date"]
        
        check_title_date = prefs.get_widget("check-time-date")
        check_title_date.set_active(self.clock.time_date)
        check_title_date.connect("toggled", self.checkbox_title_date_toggled_cb)
        
        # Showing seconds in title
        self.clock.time_seconds = self.applet.settings["time-seconds"]
        
        check_title_seconds = prefs.get_widget("check-time-seconds")
        check_title_seconds.set_active(self.clock.time_seconds)
        check_title_seconds.connect("toggled", self.checkbox_title_seconds_toggled_cb)
        
        # Showing the seconds hand in the applet's icon
        self.clock.show_second_hand = self.applet.settings["show-second-hand"]
        
        checkbox_second_hand = prefs.get_widget("check-second-hand")
        checkbox_second_hand.set_active(self.clock.show_second_hand)
        checkbox_second_hand.connect("toggled", self.second_hand_toggled_cb)
        
        # Combobox in preferences window to choose a theme
        vbox_theme = prefs.get_widget("vbox-theme")
        
        if os.path.isdir(theme_dir):
            theme = self.applet.settings["theme"]
            
            self.themes = os.listdir(theme_dir)
            self.themes.sort()
            
            combobox_theme = gtk.combo_box_new_text()
            vbox_theme.add(combobox_theme)
            
            for i in self.themes:
                combobox_theme.append_text(i)
            
            combobox_theme.set_active(self.themes.index(theme))
            current_theme = os.path.join(theme_dir, theme)
            
            combobox_theme.connect("changed", self.combobox_theme_changed_cb)
        else:
            label = gtk.Label()
            label.set_markup("<i><b>Note:</b> the current theme can be changed once\nyou have installed MacSlow's Cairo-Clock's\nthemes</i>")
            vbox_theme.add(label)
            
            current_theme = default_theme
        
        self.clock.load_theme(current_theme)
    
    def combobox_theme_changed_cb(self, button):
        self.applet.settings["theme"] = theme = self.themes[button.get_active()]
        
        # Load the new theme and update the clock
        self.clock.load_theme(os.path.join(theme_dir, theme))
        self.clock.draw_clock_cb()
    
    def checkbox_title_date_toggled_cb(self, button):
        self.applet.settings["time-date"] = self.clock.time_date = button.get_active()
    
    def checkbox_title_seconds_toggled_cb(self, button):
        self.applet.settings["time-seconds"] = self.clock.time_seconds = button.get_active()
    
    def radiobutton_24_format_toggled_cb(self, button):
        self.applet.settings["time-24-format"] = self.clock.time_24_format = button.get_active()
    
    def second_hand_toggled_cb(self, button):
        self.applet.settings["show-second-hand"] = self.clock.show_second_hand = button.get_active()
        
        # Update clock immediately
        self.clock.draw_clock_cb()
    

class ClockUpdater:
    """ Redraws the clock and sets the title (when visible) every second  """
    
    def __init__(self, applet):
        self.applet = applet
        
        self.title_is_visible = False
        
        """ Values of the properties below will be used to initialize 
        the corresponding settings """
        
        # True if the time in the title must display 24 hours, False if AM/PM
        self.time_24_format = True
        
        self.time_seconds = True
        self.time_date = True
        
        # True if the clock must display a second hand, False otherwise
        self.show_second_hand = True
        
        self.clock = AnalogClock(self)
    
    def update_title(self):
        """ Updates the title according to the settings """
        
        if self.time_24_format:
            hours = "%H"
            ampm = ""
        else:
            hours = "%I"
            ampm = " %p"
        
        if self.time_seconds:
            seconds = ":%S"
        else:
            seconds = ""
        
        if self.time_date:
            date = "%a %b %d "
            year = " %Y"
        else:
            date = ""
            year = ""
        
        self.applet.title.set(time.strftime(date + hours + ":%M" + seconds + ampm + year))
        self.applet.title.show()
    
    def enable_title(self, show):
        """ Shows or hides the title, if it must show, the title is updated first """
        
        self.title_is_visible = show
        
        if show:
            # Update the title immediately because it is visible now
            self.update_title()
    
    def draw_clock_cb(self):
        """ Draws the clock and updates the title if the title is visible """
        
        self.clock.draw_clock()
        
        # Update the title to keep it synchronized with the drawn clock
        if self.title_is_visible:
            self.update_title()
        
        return True
    
    def load_theme(self, theme):
        self.clock.load_theme(theme)

class AnalogClock:
    """ Renders an analog clock using SVG files as the applet icon """
    
    def __init__(self, clock_manager):
        self.applet = clock_manager.applet
        self.clock_manager = clock_manager
        
        self.previous_state = None
    
    def load_theme(self, theme):
        """ Loads the necessary SVG files of the specified theme """
        
        self.theme = theme
        
        get_theme = lambda filename, theme: rsvg.Handle(os.path.join(theme, filename))
        
        self.clock_drop_shadow = get_theme('clock-drop-shadow.svg', theme)
        self.clock_face = get_theme('clock-face.svg', theme)
        self.clock_marks = get_theme('clock-marks.svg', theme)
        self.clock_frame = get_theme('clock-frame.svg', theme)
        
        self.clock_hour_hand = get_theme('clock-hour-hand.svg', theme)
        self.clock_minute_hand = get_theme('clock-minute-hand.svg', theme)
        self.clock_second_hand = get_theme('clock-second-hand.svg', theme)
    
    def draw_clock(self):
        """ Renders the SVGs on a Cairo surface and converts it to a gdk.Pixbuf,
        which is used as the applet's icon """
        
        local_time = time.localtime()
        hours, minutes, seconds = (local_time[3], local_time[4], local_time[5])
        
        height = self.applet.get_height()
        
        new_state = (self.clock_manager.show_second_hand, height, self.theme, hours, minutes)
        if not self.clock_manager.show_second_hand and self.previous_state == new_state:
            return
        self.previous_state = new_state
        
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
        context = cairo.Context(surface)
        
        scale = self.applet.get_height() / 100.0
        context.scale(scale, scale)
        
        # Draw the clock itself
        self.clock_drop_shadow.render_cairo(context)
        self.clock_face.render_cairo(context)
        self.clock_marks.render_cairo(context)
        self.clock_frame.render_cairo(context)
        
        context.translate(50, 50)
        
        # Draw the hour hand
        context.save()
        context.rotate((360/12) * (hours+9+(minutes/60.0)) * (math.pi/180))
        self.clock_hour_hand.render_cairo(context)
        context.restore()
        
        # Draw the minute hand
        context.save()
        context.rotate((360/60) * (minutes+45) * (math.pi/180))
        self.clock_minute_hand.render_cairo(context)
        context.restore()
        
        # Draw the second hand if configured to do so
        if self.clock_manager.show_second_hand:
            context.save()
            context.rotate((360/60) * (seconds+45) * (math.pi/180))
            self.clock_second_hand.render_cairo(context)
            context.restore()
        
        self.applet.icon.set_context(context)


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "cairo-clock",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": 2008,
        "authors": ["onox"],
        "artists": ["Artists of MacSlow's Cairo-Clock"]})
    CairoClockApplet(applet)
    AWNLib.start(applet)