#!/usr/bin/python
# Copyright (C) 2007  Richard "nazrat" Beyer, Jeff "Jawbreaker" Hubbard,
#                     Pavel Panchekha <pavpanchekha@gmail.com>,
#                     Spencer Creasey <screasey@gmail.com>
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

from collections import defaultdict
import os
import subprocess
import threading

import pygtk
pygtk.require("2.0")
import gtk
from gtk import gdk
from gtk import glade

from awn.extras import awnlib

import pygst
pygst.require("0.10")
import gst

gst_message_types = (gst.interfaces.MIXER_MESSAGE_MUTE_TOGGLED.value_nick, gst.interfaces.MIXER_MESSAGE_VOLUME_CHANGED.value_nick)

# Interval in seconds between two successive reads of the current volume
read_volume_interval = 0.5

# Delay in seconds to freeze the GStreamer messages. This is used by the
# value-changed callback of the volume scale to avoid jittering
gstreamer_freeze_messages_interval = 0.2

applet_name = "Volume Control"
applet_version = "0.3.3"
applet_description = "Applet to control your computer's volume"

#theme_dir = os.path.join(os.path.dirname(__file__), "Themes")
theme_dir = "/usr/share/icons"
glade_file = os.path.join(os.path.dirname(__file__), "volume-control.glade")

volume_control_apps = ("gnome-volume-control", "xfce4-mixer")

moonbeam_theme_dir = os.path.join(os.path.dirname(__file__), "themes")
moonbeam_ranges = [100, 93, 86, 79, 71, 64, 57, 50, 43, 36, 29, 21, 14, 1]

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "volume-control.svg")

volume_ranges = {"high": (100, 66), "medium": (65, 36), "low": (35, 1)}
volume_step = 4

mixer_names = ("pulsemixer", "oss4mixer", "alsamixer")


class VolumeControlApplet:

    """Applet to control your computer's volume.

    """

    # Used to check whether the applet's icon must be updated
    __old_volume = None
    __was_muted = None

    __volume_scale_lock = threading.Lock()

    def __init__(self, applet):
        self.applet = applet

        self.backend = GStreamerBackend(self)
        self.message_delay_handler = applet.timing.delay(self.backend.freeze_messages.clear, gstreamer_freeze_messages_interval, False)

        self.setup_main_dialog()
        self.setup_context_menu()

        applet.connect("scroll-event", self.scroll_event_cb)
        applet.connect_size_changed(self.size_changed_cb)
        applet.connect("orientation-changed", self.orientation_changed_cb)

    def scroll_event_cb(self, widget, event):
        if event.direction == gdk.SCROLL_UP:
            self.backend.up()
        elif event.direction == gdk.SCROLL_DOWN:
            self.backend.down()

    def size_changed_cb(self):
        """Reload the applet's icon, because the size of the panel has changed.

        """
        self.setup_icons()

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
            with self.__volume_scale_lock:
                self.message_delay_handler.stop()
                self.backend.freeze_messages.set()

                self.backend.set_volume(volume)

                self.message_delay_handler.start()

    def setup_context_menu(self):
        """Add "Mute" and "Open Volume Control" to the context menu.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        self.mute_item = gtk.CheckMenuItem("Mu_te")
        self.mute_item.connect("toggled", self.mute_toggled_cb)
        menu.insert(self.mute_item, menu_index)

        volume_control_item = gtk.MenuItem("_Open Volume Control")
        volume_control_item.connect("activate", self.show_volume_control_cb)
        menu.insert(volume_control_item, menu_index + 1)

        menu.insert(gtk.SeparatorMenuItem(), menu_index + 2)

        prefs = glade.XML(glade_file)

        preferences_vbox = self.applet.dialog.new("preferences").vbox
        prefs.get_widget("dialog-vbox").reparent(preferences_vbox)

        self.load_theme_pref(prefs)
        self.load_device_pref(prefs)
        self.load_track_pref(prefs)

        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        size_group.add_widget(prefs.get_widget("label-device"))
        size_group.add_widget(prefs.get_widget("alignment-mixer-track"))
        size_group.add_widget(prefs.get_widget("label-theme"))

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
        def filter_theme(theme):
            return os.path.isfile(os.path.join(theme_dir, theme, "scalable/status/audio-volume-high.svg"))
        self.themes = filter(filter_theme, os.listdir(theme_dir))
        self.themes.sort()

        combobox_theme = prefs.get_widget("combobox-theme")
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

        self.setup_icons()

        combobox_theme.set_active(self.themes.index(self.theme))
        combobox_theme.connect("changed", self.combobox_theme_changed_cb)

    def load_device_pref(self, prefs):
        device_labels = self.backend.get_device_labels()

        if "device" not in self.applet.settings or self.applet.settings["device"] not in device_labels:
            self.applet.settings["device"] = self.backend.get_default_device()
        device = self.applet.settings["device"]

        self.combobox_device = prefs.get_widget("combobox-device")
        for i in device_labels:
            self.combobox_device.append_text(i)

        self.combobox_device.set_active(device_labels.index(device))
        self.combobox_device.connect("changed", self.combobox_device_changed_cb)

        self.backend.set_device(device)

    def load_track_pref(self, prefs):
        track_labels = self.backend.get_track_labels()

        if "track" not in self.applet.settings or self.applet.settings["track"] not in track_labels:
            self.applet.settings["track"] = self.backend.get_default_track()
        track = self.applet.settings["track"]

        self.combobox_track = prefs.get_widget("combobox-mixer-track")
        for i in track_labels:
            self.combobox_track.append_text(i)

        self.combobox_track.set_active(track_labels.index(track))
        self.combobox_track.connect("changed", self.combobox_track_changed_cb)

        self.backend.set_track(track)

    def reload_tracks(self):
        track_labels = self.backend.get_track_labels()

        if "track" not in self.applet.settings or self.applet.settings["track"] not in track_labels:
            self.applet.settings["track"] = self.backend.get_default_track()
        track = self.applet.settings["track"]

        self.combobox_track.get_model().clear()
        for i in track_labels:
            self.combobox_track.append_text(i)

        self.combobox_track.set_active(track_labels.index(track))

        self.backend.set_track(track)

    def combobox_device_changed_cb(self, button):
        device = self.backend.get_device_labels()[button.get_active()]
        self.applet.settings["device"] = device

        self.backend.set_device(device)
        self.reload_tracks()

    def combobox_track_changed_cb(self, button):
        track = self.backend.get_track_labels()[button.get_active()]
        self.applet.settings["track"] = track

        self.backend.set_track(track)

    def combobox_theme_changed_cb(self, button):
        self.theme = self.themes[button.get_active()]
        self.applet.settings["theme"] = self.theme

        # Load icons in different thread to avoid freezing the Gtk+ preferences window
        def reload_icon():
            self.setup_icons()
            self.refresh_icon(True)
        threading.Thread(target=reload_icon).start()

    def refresh_icon(self, force_update=False):
        volume = self.backend.get_volume()
        muted = self.backend.is_muted() if self.backend.can_be_muted() else False

        mute_changed = self.__was_muted != muted

        # Update if the update is forced or volume/mute has changed
        if force_update or self.__old_volume != volume or mute_changed:
            if mute_changed:
                self.refresh_mute_checkbox()

            this_is_moonbeam_theme = os.path.isdir(os.path.join(moonbeam_theme_dir, self.theme))

            if muted or volume == 0:
                icon = title = "muted"
            else:
                title = str(volume) + "%"

                if this_is_moonbeam_theme:
                    icon = filter(lambda i: volume >= i, moonbeam_ranges)[0]
                else:
                    icon = [key for key, value in volume_ranges.iteritems() if volume <= value[0] and volume >= value[1]][0]

            self.applet.tooltip.set(self.backend.get_current_track_label() + ": " + title)
            self.applet.icon.set(self.theme_icons[icon])

            self.volume_scale.set_value(volume)

            self.__old_volume = volume
            self.__was_muted = muted

    def setup_icons(self):
        this_is_moonbeam_theme = os.path.isdir(os.path.join(moonbeam_theme_dir, self.theme))

        self.theme_icons = {}

        if this_is_moonbeam_theme:
            keys = list(moonbeam_ranges)
            path = os.path.join(moonbeam_theme_dir, self.theme, "audio-volume-%s.svg")
        else:
            keys = volume_ranges.keys()
            path = os.path.join(theme_dir, self.theme, "scalable/status/audio-volume-%s.svg")

        keys.extend(["muted"])
        for i in keys:
            self.theme_icons[i] = self.applet.icon.file(path % i, set=False, size=awnlib.Icon.APPLET_SIZE)
        if self.theme == "Minimal" and self.applet.get_orientation() in (1, 3):
            for i in keys:
                self.theme_icons[i] = self.theme_icons[i].rotate_simple(gtk.gdk.PIXBUF_ROTATE_CLOCKWISE)

    def orientation_changed_cb(self, applet, orientation):
        if self.theme == "Minimal":
            self.setup_icons()
            self.refresh_icon(True)

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

    def mute_toggled_cb(self, widget):
        """ Only (un)mute if possible (this callback can be invoked because we
        set the 'Mute' checkbox to False """
        if self.backend.can_be_muted():
            item_active = int(self.mute_item.get_active())
            self.backend.set_mute(item_active)


class GStreamerBackend:

    """GStreamer backend. Controls the current device and track, and the
    current track's volume and mute status.

    """

    __devices = {}
    __current_track = None

    def __init__(self, parent):
        self.__parent = parent

        self.freeze_messages = threading.Event()

        # Collect a set of possible mixers to use
        found_mixers = set()
        for f in gst.registry_get_default().get_feature_list(gst.ElementFactory):
            if f.get_name().endswith("mixer") and f.get_klass() == "Generic/Audio":
                found_mixers.add(f.get_name())

        # Only keep certain names and sort it in order of mixer_names' order
        mixer_name = [i for i in mixer_names if i in found_mixers][0]
        mixer = gst.element_factory_make(mixer_name)

        if not isinstance(mixer, gst.interfaces.PropertyProbe):
            raise RuntimeError(mixer.get_factory().get_name() + " cannot probe properties")

        occurrences = defaultdict(int)

        mixer.probe_property_name("device")
        for device in mixer.probe_get_values_name("device"):
            self.init_mixer_device(mixer, device)

            if not isinstance(mixer, gst.interfaces.Mixer) or len(self.get_mixer_tracks(mixer)) == 0:
                mixer.set_state(gst.STATE_NULL)
                continue

            name = mixer.get_property("device-name")
            occurrences[name] += 1
            if occurrences[name] > 1:
                name += " (%d)" % occurrences[name]

            self.__devices[name] = device

        self.__mixer = mixer

        if mixer.get_mixer_flags() & gst.interfaces.MIXER_FLAG_AUTO_NOTIFICATIONS:
            bus = gst.Bus()
            bus.add_signal_watch()
            bus.connect("message::element", self.message_element_cb)
            mixer.set_bus(bus)
        else:
            parent.applet.timing.register(parent.refresh_icon, read_volume_interval)

    def message_element_cb(self, bus, message):
        if not self.freeze_messages.isSet() \
            and message.type is gst.MESSAGE_ELEMENT and message.src is self.__mixer \
            and message.structure["type"] in gst_message_types \
            and message.structure["track"] is self.__current_track:
                self.__parent.refresh_icon()

    def get_mixer_tracks(self, mixer):
        """Return those tracks of the mixer that are output tracks and have
        at least one channel. Assumes the mixer has been initialized.

        """
        assert mixer.get_state()[1] is gst.STATE_READY

        def filter_track(track):
            return bool(track.flags & gst.interfaces.MIXER_TRACK_OUTPUT) and track.num_channels > 0
        return filter(filter_track, mixer.list_tracks())

    def init_mixer_device(self, mixer, device):
        mixer.set_state(gst.STATE_NULL)
        mixer.set_property("device", device)
        mixer.set_state(gst.STATE_READY)

    def set_device(self, device_label):
        """Set the mixer to the device labeled by the given label.

        """
        self.init_mixer_device(self.__mixer, self.__devices[device_label])

        self.__tracks = self.get_mixer_tracks(self.__mixer)
        self.__track_labels = [track.label for track in self.__tracks]

    def get_device_labels(self):
        return self.__devices.keys()

    def get_default_device(self):
        return self.get_device_labels()[0]

    def set_track(self, track_label):
        """Change the current track and enable or disable the 'Mute'
        checkbox.

        """
        for track in self.__tracks:
            if track.label == track_label:
                self.__current_track = track
                break

        self.__volume_multiplier = 100.0 / (self.__current_track.max_volume - self.__current_track.min_volume)

        self.__parent.refresh_mute_checkbox()
        self.__parent.refresh_icon(True)

    def get_current_track_label(self):
        return self.__current_track.label

    def get_track_labels(self):
        return self.__track_labels

    def get_default_track(self):
        """Return the default track of the current mixer device. This is the
        master track or otherwise the first track of the list of known tracks.

        """
        for track in self.__tracks:
            if track.flags & gst.interfaces.MIXER_TRACK_MASTER:
                return track.label
        return self.__track_labels[0]

    def can_be_muted(self):
        return True

    def is_muted(self):
        """Return whether all channels (left and right if there are two)
        are muted.

        """
        return bool(self.__current_track.flags & gst.interfaces.MIXER_TRACK_MUTE)

    def set_mute(self, mute):
        self.__mixer.set_mute(self.__current_track, mute)

        # Update applet's icon
        self.__parent.refresh_icon(True)

    def get_gst_volume(self):
        volume_channels = self.__mixer.get_volume(self.__current_track)
        return sum(volume_channels) / len(volume_channels)

    def get_volume(self):
        return int(round(self.get_gst_volume() * self.__volume_multiplier))

    def set_gst_volume(self, volume):
        self.__mixer.set_volume(self.__current_track, (self.__current_track.min_volume + volume, ) * self.__current_track.num_channels)

    def set_volume(self, value):
        self.set_gst_volume(int(round(value / self.__volume_multiplier)))

        # Update applet's icon
        self.__parent.refresh_icon(True)

    def up(self, widget=None, event=None):
        self.set_volume(min(100, self.get_volume() + volume_step))

    def down(self, widget=None, event=None):
        self.set_volume(max(0, self.get_volume() - volume_step))


if __name__ == "__main__":
    awnlib.init_start(VolumeControlApplet, {"name": applet_name, "short": "volume-control",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": "2008 - 2009",
        "authors": ["onox <denkpadje@gmail.com>"],
        "artists": ["Jakub Steiner"],
        "type": ["Audio", "Midi"]},
        ["settings-per-instance"])
