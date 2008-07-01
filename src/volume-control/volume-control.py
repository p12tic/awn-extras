#!/usr/bin/env python
#
# Copyright (C) 2007  Richard "nazrat" Beyer, Jeff "Jawbreaker" Hubbard,
#                     Pavel Panchekha <pavpanchekha@gmail.com>,
#                     Spencer Creasey <screasey@gmail.com>
# Copyright (C) 2008  onox (complete rewrite and new features)
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
import subprocess
import time

import pygtk
pygtk.require("2.0")
import gtk
from gtk import glade
from gtk import gdk
from awn.extras import AWNLib

# To later import alsaaudio
alsaaudio = None

# Interval in seconds between two successive reads of the current volume
read_volume_interval = 0.5

applet_name = "Volume Control Applet"
applet_version = "0.2.8"
applet_description = "Applet to control your computer's volume"

#theme_dir = os.path.join(os.path.dirname(__file__), "Themes")
theme_dir = "/usr/share/icons"
glade_file = os.path.join(os.path.dirname(__file__), "volume-control.glade")

moonbeam_theme_dir = os.path.join(os.path.dirname(__file__), "themes")
moonbeam_ranges = [100, 93, 86, 79, 71, 64, 57, 50, 43, 36, 29, 21, 14, 1, 0]

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(theme_dir, "Tango/scalable/status/audio-volume-high.svg")

volume_ranges = {"high": (100, 66), "medium": (65, 36), "low": (35, 1)}
volume_step = 4


class AboutDialog(gtk.AboutDialog):
    """ Shows the GTK About dialog """
    
    def __init__(self, applet):
        gtk.AboutDialog.__init__(self)
        
        self.applet = applet
        
        self.set_name(applet_name)
        self.set_version(applet_version)
        self.set_comments(applet_description)
        self.set_copyright("Copyright \xc2\xa9 2008 onox")
        self.set_authors(["onox (complete rewrite and new features)",
                          'Richard "nazrat" Beyer',
                          'Jeff "Jawbreaker" Hubbard',
                          "Pavel Panchekha <pavpanchekha@gmail.com>",
                          "Spencer Creasey <screasey@gmail.com>"])
        self.set_logo(gdk.pixbuf_new_from_file_at_size(applet_logo, 48, 48))
        self.set_icon(gdk.pixbuf_new_from_file(applet_logo))
        
        # Connect some signals to be able to hide the window
        self.connect("response", self.response_event)
        self.connect("delete_event", self.delete_event)
    
    def delete_event(self, widget, event):
        return True
    
    def response_event(self, widget, response):
        if response < 0:
            self.hide()
    
    def update_icon(self):
        """ Reloads the applet's logo to be of the same height as the panel """
        
        height = self.applet.get_height()
        self.set_icon(gdk.pixbuf_new_from_file_at_size(applet_logo, height, height))


class PreferencesDialog:
    """ Shows the preferences window """
    
    def __init__(self, volume_applet):
        self.volume_applet = volume_applet
        
        prefs = glade.XML(glade_file)
        
        # Register the dialog window
        self.dialog = prefs.get_widget("dialog-window")
        self.volume_applet.applet.dialog.register("dialog-settings", self.dialog)
        
        self.dialog.set_icon(gdk.pixbuf_new_from_file(applet_logo))
        
        self.volume_applet.setup_dialog_settings(prefs)
        
        # Connect some signals to be able to hide the window
        prefs.get_widget("button-close").connect("clicked", self.button_close_clicked_cb)
        self.dialog.connect("response", self.response_event)
        self.dialog.connect("delete_event", self.delete_event)
    
    def button_close_clicked_cb(self, button):
        self.volume_applet.applet.dialog.toggle("dialog-settings", "hide")
    
    def delete_event(self, widget, event):
        return True
    
    def response_event(self, widget, response):
        if response < 0:
            self.volume_applet.applet.dialog.toggle("dialog-settings", "hide")


class VolumeControlApplet:
    """ Applet to control your computer's volume """
    
    def __init__(self, applet):
        self.applet = applet
        
        self.applet.errors.module("alsaaudio", {"Ubuntu": "python-alsaaudio",
            "Gentoo": "dev-python/pyalsaaudio",
            "Mandriva": "python-alsaaudio"}, self.__init2)
    
    def __init2(self, module):
        global alsaaudio
        alsaaudio = module
        
        # Contains old values to check if the applet's icon must be updated
        self.old_volume = None
        self.was_muted = None
        
        self.backend = Backend(self)
        
        self.setup_main_dialog()
        self.setup_context_menu()
        PreferencesDialog(self)
        
        applet.connect("scroll-event", self.scroll_event_cb)
        applet.connect("height-changed", self.height_changed_cb)
        
        self.applet.timing.register(self.refresh_icon, read_volume_interval)
    
    def scroll_event_cb(self, widget, event):
        if event.direction == gdk.SCROLL_UP:
            self.backend.up()
        elif event.direction == gdk.SCROLL_DOWN:
            self.backend.down()
    
    def height_changed_cb(self, widget, event):
        """ Updates the applet's icon and the icon of
        the About dialog to reflect the new height """
        
        self.refresh_icon(True)
        
        # Update the icon of the AboutDialog
        self.about_dialog.update_icon()
    
    def setup_main_dialog(self):
        dialog = self.applet.dialog.new("volume-dialog")
        dialog.set_geometry_hints(min_width=50, min_height=200)
        
        vbox = gtk.VBox()
        
        adjustment = gtk.Adjustment(lower=0, upper=100, step_incr=volume_step, page_incr=10)
        self.volume_scale = gtk.VScale(adjustment)
        
        self.volume_scale.set_digits(0)
        self.volume_scale.set_inverted(True)
        
        inc_button = gtk.Button("+")
        inc_button.set_relief(gtk.RELIEF_NONE)
        vbox.pack_start(inc_button, expand=False)
        
        vbox.add(self.volume_scale)
        
        dec_button = gtk.Button("-")
        dec_button.set_relief(gtk.RELIEF_NONE)
        vbox.pack_start(dec_button, expand=False)
        
        dialog.add(vbox)
        
        self.volume_scale.connect("value-changed", self.volume_scale_changed_cb)
        inc_button.connect("button-press-event", self.backend.up)
        dec_button.connect("button-press-event", self.backend.down)
        
        self.dialog_focus_lost_time = time.time()
        self.applet.connect("button-press-event", self.button_press_event_cb)
        dialog.connect("focus-out-event", self.dialog_focus_out_cb)
    
    def button_press_event_cb(self, widget, event):
        if event.button == 1 and (time.time() - self.dialog_focus_lost_time) > 0.01:
            self.applet.dialog.toggle("volume-dialog")
        elif event.button == 2:
            # Toggle 'Mute' checkbutton
            self.mute_item.set_active(not self.mute_item.get_active())
    
    def dialog_focus_out_cb(self, dialog, event):
        self.dialog_focus_lost_time = time.time()
    
    def volume_scale_changed_cb(self, widget):
        volume = widget.get_value()
        
        # Don't update if the callback was invoked via refresh_icon()
        if volume != self.backend.get_volume():
            self.backend.set_volume(volume)
    
    def setup_context_menu(self):
        """ Creates a context menu to activate "Preferences" or "About" window """
        
        self.about_dialog = AboutDialog(self.applet)
        
        menu = self.applet.dialog.new("menu")
        
        self.mute_item = gtk.CheckMenuItem("Mu_te")
        menu.append(self.mute_item)
        
        volume_control_item = gtk.MenuItem("_Open Volume Control")
        menu.append(volume_control_item)
        
        menu.append(gtk.SeparatorMenuItem())
        
        prefs_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        menu.append(prefs_item)
        about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
        menu.append(about_item)
        
        menu.show_all()
        
        self.mute_item.connect("toggled", self.backend.mute_toggled_cb)
        volume_control_item.connect("activate", self.show_volume_control_cb)
        prefs_item.connect("activate", self.show_dialog_cb)
        about_item.connect("activate", self.activate_about_dialog_cb)
    
    def show_volume_control_cb(self, widget):
        subprocess.Popen("gnome-volume-control")
    
    def show_dialog_cb(self, widget):
        self.applet.dialog.toggle("dialog-settings", "show")
    
    def activate_about_dialog_cb(self, widget):
        self.about_dialog.show()
    
    def setup_dialog_settings(self, prefs):
        """ Loads the settings from gconf """
        
        self.load_theme_pref(prefs)
        self.load_channel_pref(prefs)
    
    def load_theme_pref(self, prefs):
        # Combobox in preferences window to choose a theme
        vbox_theme = prefs.get_widget("vbox-theme")
        
        if "theme" not in self.applet.settings:
            self.applet.settings["theme"] = "Tango"
        self.theme = self.applet.settings["theme"]
        
        # Only use themes that are likely to provide all the files
        self.themes = filter(self.filter_themes, os.listdir(theme_dir))
        
        self.themes.sort()
        
        combobox_theme = gtk.combo_box_new_text()
        vbox_theme.add(combobox_theme)
        
        for i in self.themes:
            combobox_theme.append_text(i)
        
        moonbeam_themes = os.listdir(moonbeam_theme_dir)
        moonbeam_themes.sort()
        self.themes.extend(moonbeam_themes)
        
        for i in moonbeam_themes:
            combobox_theme.append_text(i)
        
        combobox_theme.set_active(self.themes.index(self.theme))
        
        combobox_theme.connect("changed", self.combobox_theme_changed_cb)
    
    def load_channel_pref(self, prefs):
        # Combobox in preferences window to choose a channel
        vbox_channel = prefs.get_widget("vbox-mixer-channel")
        
        if "channel" not in self.applet.settings:
            self.applet.settings["channel"] = self.backend.channels[0]
        channel = self.applet.settings["channel"]
        
        self.combobox_channel = gtk.combo_box_new_text()
        vbox_channel.add(self.combobox_channel)
        
        for i in self.backend.channels:
            self.combobox_channel.append_text(i)
        
        self.combobox_channel.set_active(self.backend.channels.index(channel))
        self.combobox_channel.connect("changed", self.combobox_channel_changed_cb)
        
        self.backend.set_channel(channel)
    
    def filter_themes(self, theme):
        return os.path.isfile(os.path.join(theme_dir, theme, "scalable/status/audio-volume-high.svg"))
    
    def combobox_channel_changed_cb(self, button):
        self.applet.settings["channel"] = channel = self.backend.channels[button.get_active()]
        
        self.backend.set_channel(channel)
    
    def combobox_theme_changed_cb(self, button):
        self.applet.settings["theme"] = self.theme = self.themes[button.get_active()]
        self.refresh_icon(True)
    
    def refresh_icon(self, force_update=False):
        volume = self.backend.get_volume()
        
        if self.backend.can_be_muted():
            muted = self.backend.is_muted()
        else:
            muted = False
        
        mute_changed = self.was_muted != muted
        
        # Update if the update is forced or volume/mute has changed
        if force_update or self.old_volume != volume or mute_changed:
            if mute_changed:
                self.backend.refresh_mute_checkbox()
            
            this_is_moonbeam_theme = os.path.isdir(os.path.join(moonbeam_theme_dir, self.theme))
            
            if muted or volume == 0:
                self.applet.title.set(self.backend.channel + ": muted")
                icon = "muted"
            else:
                self.applet.title.set(self.backend.channel + ": " + str(volume) + "%")
                
                if this_is_moonbeam_theme:
                    icon = filter(lambda i: volume >= i, moonbeam_ranges)[0]
                else:
                    icon = [key for key, value in volume_ranges.iteritems() if volume <= value[0] and volume >= value[1]][0]
                    
            
            if this_is_moonbeam_theme:
                icon = os.path.join(moonbeam_theme_dir, self.theme, "audio-volume-%s.svg" % icon)
            else:
                icon = os.path.join(theme_dir, self.theme, "scalable/status/audio-volume-%s.svg" % icon)
            
            height = self.applet.get_height()
            self.applet.icon.set(gdk.pixbuf_new_from_file_at_size(icon, height, height), True)
            
            self.volume_scale.set_value(volume)
            
            self.old_volume = volume
            self.was_muted = muted


class Backend:
    """  ALSA backend. Controls the volume, mute and channels """
    
    def __init__(self, parent):
        self.parent = parent
        self.channels = filter(self.filter_channels, alsaaudio.mixers())
    
    def filter_channels(self, channel):
        try:
            return bool(alsaaudio.Mixer(channel).getvolume())
        except alsaaudio.ALSAAudioError:
            return False
    
    def set_channel(self, channel):
        """ Changes the current channel and enables/disables the 'Mute' checkbox """
        
        self.channel = channel
        
        self.refresh_mute_checkbox()
        
        # Read volume from new channel
        self.set_volume(self.get_volume())
    
    def can_be_muted(self):
        return "Playback Mute" in alsaaudio.Mixer(self.channel).switchcap()
    
    def is_muted(self):
        """ Mixer is only called 'muted' if both channels (left and right)
        are muted """
        
        muted_channels = alsaaudio.Mixer(self.channel).getmute()
        
        if len(muted_channels) > 1:
            return bool(muted_channels[0]) and bool(muted_channels[1])
        else:
            return bool(muted_channels[0])
    
    def refresh_mute_checkbox(self):
        """ Enables/disables 'Mute' checkbox. This does not update the applet's icon! """
        can_be_muted = self.can_be_muted()
        
        self.parent.mute_item.set_sensitive(can_be_muted)
        if can_be_muted:
            self.parent.mute_item.set_active(self.is_muted())
        else:
            # Clear checkbox (this will fire the "toggled" signal)
            self.parent.mute_item.set_active(False)
    
    def get_volume(self):
        volume_channels = alsaaudio.Mixer(self.channel).getvolume()
        
        if len(volume_channels) > 1:
            volume = (volume_channels[0] + volume_channels[1]) / 2
        else:
            volume = volume_channels[0]
        
        # Sometimes ALSA is a little crazy and returns -(2^32 / 2) 
        return max(0, volume)
    
    def set_volume(self, value):
        alsaaudio.Mixer(self.channel).setvolume(int(value))
        
        self.parent.refresh_icon(True)
    
    def up(self, widget=None, event=None):
        self.set_volume(min(100, self.get_volume() + volume_step))
    
    def down(self, widget=None, event=None):
        self.set_volume(max(0, self.get_volume() - volume_step))
    
    def mute_toggled_cb(self, widget):
        """ Only (un)mute if possible (this callback can be invoked because we
        set the 'Mute' checkbox to False """
        if self.can_be_muted():
            alsaaudio.Mixer(self.channel).setmute(int(self.parent.mute_item.get_active()))
            
            # Update applet's icon
            self.parent.refresh_icon(True)


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name,
        "short": "volume-control",
        "author": "Pavel Panchekha",
        "email": "pavpanchekha@gmail.com",
        "description": applet_description,
        "type": ["Audio", "Midi"]})
    VolumeControlApplet(applet)
    AWNLib.start(applet)
