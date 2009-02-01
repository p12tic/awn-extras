#!/usr/bin/python
# Copyright (C) 2007  Richard "nazrat" Beyer, Jeff "Jawbreaker" Hubbard,
#                     Pavel Panchekha <pavpanchekha@gmail.com>,
#                     Spencer Creasey <screasey@gmail.com>
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
import subprocess

import pygtk
pygtk.require("2.0")
import gtk
from gtk import gdk
from gtk import glade

from awn.extras import AWNLib

# Interval in seconds between two successive reads of the current volume
read_volume_interval = 0.5

applet_name = "Volume Control"
applet_version = "0.3.1"
applet_description = "Applet to control your computer's volume"

#theme_dir = os.path.join(os.path.dirname(__file__), "Themes")
theme_dir = "/usr/share/icons"
glade_file = os.path.join(os.path.dirname(__file__), "volume-control.glade")

volume_control_apps = ("gnome-volume-control", "xfce4-mixer")

moonbeam_theme_dir = os.path.join(os.path.dirname(__file__), "themes")
moonbeam_ranges = [100, 93, 86, 79, 71, 64, 57, 50, 43, 36, 29, 21, 14, 1, 0]

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "volume-control.svg")

volume_ranges = {"high": (100, 66), "medium": (65, 36), "low": (35, 1)}
volume_step = 4


class VolumeControlApplet:

    """Applet to control your computer's volume.

    """

    # Used to check whether the applet's icon must be updated
    __old_volume = None
    __was_muted = None

    def __init__(self, applet):
        self.applet = applet

        self.applet.errors.module(globals(), "alsaaudio")

        self.backend = ALSABackend(self)

        self.setup_main_dialog()
        self.setup_context_menu()

        applet.connect("scroll-event", self.scroll_event_cb)
        applet.connect("height-changed", self.height_changed_cb)

        self.applet.timing.register(self.refresh_icon, read_volume_interval)

    def scroll_event_cb(self, widget, event):
        if event.direction == gdk.SCROLL_UP:
            self.backend.up()
        elif event.direction == gdk.SCROLL_DOWN:
            self.backend.down()

    def height_changed_cb(self, widget, event):
        """Reload the applet's icon, because the height of the panel has
        changed.

        """
        self.refresh_icon(True)

    def setup_main_dialog(self):
        dialog = self.applet.dialog.new("main")
        dialog.set_geometry_hints(min_width=50, min_height=200)

        vbox = gtk.VBox()

        adjustment = gtk.Adjustment(lower=0, upper=100, step_incr=volume_step, page_incr=10)
        self.volume_scale = gtk.VScale(adjustment)

        self.volume_scale.set_digits(0)
        self.volume_scale.set_inverted(True)

        inc_button = gtk.Button("+")
        inc_button.set_relief(gtk.RELIEF_NONE)
        inc_button.props.can_focus = False
        vbox.pack_start(inc_button, expand=False)

        vbox.add(self.volume_scale)
        self.volume_scale.props.can_focus = False

        dec_button = gtk.Button("-")
        dec_button.set_relief(gtk.RELIEF_NONE)
        dec_button.props.can_focus = False
        vbox.pack_start(dec_button, expand=False)

        dialog.add(vbox)

        self.volume_scale.connect("value-changed", self.volume_scale_changed_cb)
        inc_button.connect("button-press-event", self.backend.up)
        dec_button.connect("button-press-event", self.backend.down)

        self.applet.connect("button-press-event", self.button_press_event_cb)

    def button_press_event_cb(self, widget, event):
        if event.button == 2:
            # Toggle 'Mute' checkbutton
            self.mute_item.set_active(not self.mute_item.get_active())

    def volume_scale_changed_cb(self, widget):
        volume = widget.get_value()

        # Don't update if the callback was invoked via refresh_icon()
        if volume != self.backend.get_volume():
            self.backend.set_volume(volume)

    def setup_context_menu(self):
        """Add "Mute" and "Open Volume Control" to the context menu.

        """
        menu = self.applet.dialog.menu

        self.mute_item = gtk.CheckMenuItem("Mu_te")
        self.mute_item.connect("toggled", self.backend.mute_toggled_cb)
        menu.insert(self.mute_item, 3)

        volume_control_item = gtk.MenuItem("_Open Volume Control")
        volume_control_item.connect("activate", self.show_volume_control_cb)
        menu.insert(volume_control_item, 4)

        menu.insert(gtk.SeparatorMenuItem(), 5)

        prefs = glade.XML(glade_file)

        preferences_vbox = self.applet.dialog.new("preferences").vbox
        prefs.get_widget("dialog-vbox").reparent(preferences_vbox)

        self.load_theme_pref(prefs)
        self.load_channel_pref(prefs)

    def show_volume_control_cb(self, widget):
        for command in volume_control_apps:
            try:
                subprocess.Popen(command)
                return
            except OSError:
                pass
        raise RuntimeError("No volume control found (%s)" % ", ".join(volume_control_apps))

    def load_theme_pref(self, prefs):
        # Only use themes that are likely to provide all the files
        self.themes = filter(self.filter_themes, os.listdir(theme_dir))
        self.themes.sort()

        # Combobox in preferences window to choose a theme
        combobox_theme = gtk.combo_box_new_text()
        prefs.get_widget("hbox-theme").pack_start(combobox_theme, expand=False)
        prefs.get_widget("label-theme").set_mnemonic_widget(combobox_theme)

        for i in self.themes:
            combobox_theme.append_text(i)

        moonbeam_themes = os.listdir(moonbeam_theme_dir)
        moonbeam_themes.sort()
        self.themes.extend(moonbeam_themes)

        for i in moonbeam_themes:
            combobox_theme.append_text(i)

        if "theme" not in self.applet.settings or self.applet.settings["theme"] not in self.themes:
            self.applet.settings["theme"] = self.themes[0]
        self.theme = self.applet.settings["theme"]

        combobox_theme.set_active(self.themes.index(self.theme))

        combobox_theme.connect("changed", self.combobox_theme_changed_cb)

    def load_channel_pref(self, prefs):
        if "channel" not in self.applet.settings or self.applet.settings["channel"] not in self.backend.channels:
            self.applet.settings["channel"] = self.backend.channels[0]
        channel = self.applet.settings["channel"]

        # Combobox in preferences window to choose a channel
        self.combobox_channel = gtk.combo_box_new_text()
        prefs.get_widget("hbox-mixer-channel").pack_start(self.combobox_channel, expand=False)
        prefs.get_widget("label-mixer-channel").set_mnemonic_widget(self.combobox_channel)

        for i in self.backend.channels:
            self.combobox_channel.append_text(i)

        self.combobox_channel.set_active(self.backend.channels.index(channel))
        self.combobox_channel.connect("changed", self.combobox_channel_changed_cb)

        self.backend.set_channel(channel)

    def filter_themes(self, theme):
        return os.path.isfile(os.path.join(theme_dir, theme, "scalable/status/audio-volume-high.svg"))

    def combobox_channel_changed_cb(self, button):
        channel = self.backend.channels[button.get_active()]
        self.applet.settings["channel"] = channel

        self.backend.set_channel(channel)

    def combobox_theme_changed_cb(self, button):
        self.theme = self.themes[button.get_active()]
        self.applet.settings["theme"] = self.theme
        self.refresh_icon(True)

    def refresh_icon(self, force_update=False):
        volume = self.backend.get_volume()

        if self.backend.can_be_muted():
            muted = self.backend.is_muted()
        else:
            muted = False

        mute_changed = self.__was_muted != muted

        # Update if the update is forced or volume/mute has changed
        if force_update or self.__old_volume != volume or mute_changed:
            if mute_changed:
                self.refresh_mute_checkbox()

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

            self.__old_volume = volume
            self.__was_muted = muted

    def refresh_mute_checkbox(self):
        """Update the state of the 'Mute' checkbox.

        """
        can_be_muted = self.backend.can_be_muted()

        self.mute_item.set_sensitive(can_be_muted)

        if can_be_muted:
            self.mute_item.set_active(self.backend.is_muted())
        else:
            # Clear checkbox (this will fire the "toggled" signal)
            self.mute_item.set_active(False)


class ALSABackend:

    """ALSA backend. Controls the volume, mute and channels.

    """

    def __init__(self, parent):
        self.parent = parent
        self.channels = filter(self.filter_channels, alsaaudio.mixers())

    def filter_channels(self, channel):
        try:
            mixer = alsaaudio.Mixer(channel)
            return bool(mixer.getvolume()) and "Playback Volume" in mixer.volumecap()
        except alsaaudio.ALSAAudioError:
            return False

    def set_channel(self, channel):
        """Changes the current channel and enables/disables the 'Mute'
        checkbox.

        """
        self.channel = channel

        self.parent.refresh_mute_checkbox()

        # Read volume from new channel
        self.set_volume(self.get_volume())

    def can_be_muted(self):
        mixer = alsaaudio.Mixer(self.channel)

        if "Playback Mute" not in mixer.switchcap():
            return False

        """ Test if mute switch is really present because
        alsaaudio is sometimes a little bit crazy """
        try:
            mixer.getmute()
            return True
        except alsaaudio.ALSAAudioError:
            return False

    def is_muted(self):
        """Return whether all channels (left and right if there are two)
        are muted.

        """
        muted_channels = alsaaudio.Mixer(self.channel).getmute()

        if len(muted_channels) > 1:
            return bool(muted_channels[0]) and bool(muted_channels[1])
        else:
            return bool(muted_channels[0])

    def get_volume(self):
        volume_channels = alsaaudio.Mixer(self.channel).getvolume()

        if len(volume_channels) > 1:
            volume = (volume_channels[0] + volume_channels[1]) / 2
        else:
            volume = volume_channels[0]

        # Sometimes ALSA is a little bit crazy and returns -(2^32 / 2)
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
            item_active = int(self.parent.mute_item.get_active())
            alsaaudio.Mixer(self.channel).setmute(item_active)

            # Update applet's icon
            self.parent.refresh_icon(True)


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "volume-control",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": 2008,
        "authors": ['Richard "nazrat" Beyer', 'Jeff "Jawbreaker" Hubbard',
                    'Spencer Creasey <screasey@gmail.com>',
                    "Pavel Panchekha <pavpanchekha@gmail.com>",
                    "onox <denkpadje@gmail.com>"],
        "artists": ["Jakub Steiner"],
        "type": ["Audio", "Midi"]},
        ["settings-per-instance"])
    VolumeControlApplet(applet)
    AWNLib.start(applet)
