#!/usr/bin/python

# Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>
#               2008-2009 Michal Hruby <michal.mhr at gmail.com>
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
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import sys
import os.path

from gobject import GError
import gobject
import gtk
import dbus
import pango

import awn
from desktopagnostic.config import Client, GROUP_DEFAULT, BIND_METHOD_FALLBACK
from desktopagnostic import vfs

from awn.extras import _
import awn.extras.awnmediaplayers as mediaplayers

def error_decorator(fn):
    """Handles errors caused by dbus"""
    def errors(cls, *args, **kwargs):
        try:
            fn(cls, *args)
        except (dbus.exceptions.DBusException, AttributeError, RuntimeError):
            cls.ensure_player()
    return errors


class MediaControlApplet (awn.AppletSimple):
    """Displays a dialog with controls and track/album info and art"""

    APPLET_NAME = "Media Control Applet"
    APPLET_NAME_MARKUP = "<span weight=\"bold\">Media Control Applet</span>"

    use_docklet = gobject.property(type=bool, nick='Use docklet',
                                   blurb='Use docklet if possible',
                                   default=False)
    album_art_enabled = gobject.property(type=bool, nick='Album Art enabled',
                                         default=True)
    album_art_size = gobject.property(type=int, nick='Album art image size',
                                      blurb='Max size of the album art images',
                                      default=150)
    tooltip_order = gobject.property(type=int, nick='Tooltip order',
                                     blurb='Tooltip text order',
                                     default=0)

    def __init__(self, uid, panel_id):
        """Creating the applets core"""
        awn.AppletSimple.__init__(self, "media-control", uid, panel_id)
        self.set_tooltip_text(MediaControlApplet.APPLET_NAME)
        self.set_icon_info(
            ['main-icon', 'play', 'pause', 'prev', 'next'],
            ['media-control', 'media-playback-start', 'media-playback-pause',
             'media-skip-backward', 'media-skip-forward']
        )
        self.set_icon_state('main-icon')

        # get the missing album art pixbuf
        try:
            file_name = __file__[0:__file__.rfind('/')]
            file_name += "/icons/missing-artwork.svg"
            self.no_album_art_pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(
                file_name, 128, 128)
        except:
            self.no_album_art_pixbuf = None
        self.album_art_pixbuf = None

        self.timer_running = False
        self.playing_changed_id = 0
        self.dbus_names = {}
        self.MediaPlayer = None
        self.is_playing = False

        # Player selection frame
        self.players_frame = gtk.Frame()
        self.controls = gtk.VBox()
        self.controls.set_spacing(5)
        self.label = gtk.Label()
        self.label.set_ellipsize(pango.ELLIPSIZE_END)
        self.label.set_max_width_chars(30)
        self.label.set_padding(4, 0)
        self.label.set_markup(MediaControlApplet.APPLET_NAME_MARKUP)

        # album overlay
        self.album_overlay = awn.OverlayPixbuf()
        self.album_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.album_overlay.props.alpha = 0.85
        self.album_overlay.props.active = False
        self.add_overlay(self.album_overlay)

        # Dialog
        self.dialog = awn.Dialog (self)

        # Docklet related stuff
        self.docklet = None
        self.docklet_visible = False
        self.docklet_image = None
        self.docklet_label = None
        self.docklet_play_pause = None

        #Popup menu
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect("activate", self.show_about)
        self.prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.prefs.connect("activate", self.show_prefs)

        self.popup_menu = self.create_default_menu()
        self.popup_menu.append(self.prefs)
        self.popup_menu.append(gtk.SeparatorMenuItem())
        self.popup_menu.append(self.about)
        self.popup_menu.show_all()

        self.ensure_player()

        # Defining Widgets
        vbox = gtk.VBox()
        self.players_frame.add(vbox)
        for player in self.get_supported_player_names():
          button = gtk.Button(player)
          button.connect("clicked", self.start_player_pressed, player)
          vbox.add(button)

        # dialog widgets
        button_previous = gtk.ToolButton ("gtk-media-previous")
        button_play = gtk.ToolButton ("gtk-media-play")
        button_pause = gtk.ToolButton ("gtk-media-pause")
        button_next = gtk.ToolButton ("gtk-media-next")
        self.image = gtk.Image()
        # Packing Widgets
        hbox = gtk.HBox()
        hbox.pack_start(button_previous)
        hbox.add(button_play)
        hbox.add(button_next)
        self.controls.pack_start(self.image)
        self.controls.add(hbox)
        vbox = gtk.VBox()
        vbox.set_spacing(5)
        vbox.pack_start(self.label)
        vbox.add(self.players_frame)
        vbox.add(self.controls)
        self.dialog.add(vbox)
        hbox.show_all()
        vbox.show_all()
        # Button Connects
        button_previous.connect("clicked", self.button_previous_press)
        button_play.connect("clicked", self.button_pp_press)
        button_next.connect("clicked", self.button_next_press)

        # Standard AWN Connects
        self.connect("scroll-event", self.wheel_turn)
        self.connect("clicked", self.icon_clicked)
        self.connect("middle-clicked", self.button_pp_press)
        self.connect("context-menu-popup", self.menu_popup)
        self.connect("enter-notify-event", self.enter_notify)
        self.dialog.props.hide_on_unfocus = True
        # Drag&drop support
        self.get_icon().connect("drag-data-received", self.applet_drop_cb)
        self.get_icon().connect("drag-motion", self.applet_drag_motion_cb)
        self.get_icon().connect("drag-leave", self.applet_drag_leave_cb)

        self.get_icon().drag_dest_set(
                           gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION,
                           [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                           gtk.gdk.ACTION_COPY)
        
        self.client = awn.config_get_default_for_applet(self)

        self.client.bind(GROUP_DEFAULT, "use_docklet",
                         self, "use-docklet", True, BIND_METHOD_FALLBACK)
        self.client.bind(GROUP_DEFAULT, "show_album_art",
                         self, "album-art-enabled", True, BIND_METHOD_FALLBACK)
        self.client.bind(GROUP_DEFAULT, "album_art_size",
                         self, "album-art-size", True, BIND_METHOD_FALLBACK)
        self.client.bind(GROUP_DEFAULT, "tooltip_format",
                         self, "tooltip-order", True, BIND_METHOD_FALLBACK)

        try:
            if self.MediaPlayer: self.update_song_info()
        except:
            pass

        proxy = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        proxy.connect_to_signal('NameOwnerChanged', self.name_owner_changed_cb)

    def is_dialog_visible(self):
        return self.dialog.flags() & gtk.VISIBLE != 0

    def get_pixbuf_for_docklet(self):
        pixbuf = self.album_art_pixbuf
        if pixbuf is None:
            if self.no_album_art_pixbuf:
                pixbuf = self.no_album_art_pixbuf
            else:
                return None
        # TODO: orient support
        max_size = self.docklet.props.max_size
        offset = self.docklet.props.offset

        dest_width = int(pixbuf.get_width() * (max_size - offset)
                         / pixbuf.get_height())
        pixbuf = pixbuf.scale_simple(dest_width, max_size - offset,
                                     gtk.gdk.INTERP_BILINEAR)

        return pixbuf

    def show_docklet(self, window_id):
        self.docklet_visible = True
        docklet = awn.Applet(self.get_canonical_name(),
                             self.props.uid, self.props.panel_id)
        self.docklet = docklet
        docklet.props.quit_on_delete = False

        def invalidate_docklet(widget, applet):
            applet.docklet_visible = False
            applet.docklet = None
            applet.docklet_play_pause = None
        docklet.connect("destroy", invalidate_docklet, self)

        docklet_position = docklet.get_pos_type()
        top_box = awn.Box()
        top_box.set_orientation_from_pos_type(docklet_position)

        align = awn.Alignment(docklet)
        box = awn.Box()
        box.set_orientation_from_pos_type(docklet_position)
        align.add(box)

        # TODO: not really for side orient yet
        pixbuf = self.get_pixbuf_for_docklet()
        if pixbuf:
            self.docklet_image = gtk.image_new_from_pixbuf(pixbuf)
        else:
            self.docklet_image = gtk.Image()

        if box.props.orientation == gtk.ORIENTATION_HORIZONTAL:
            self.docklet_image.set_padding(6, 0)
        else:
            self.docklet_image.set_padding(0, 6)
        box.pack_start(self.docklet_image, False)

        label_align = gtk.Alignment() # for BOTTOM
        self.docklet_label = awn.Label()
        self.docklet_label.set_markup(self.label.get_label())

        if (docklet.get_pos_type() == gtk.POS_TOP):
            label_align.set(0.0, 0.0, 1.0, 0.0)
            self.docklet_label.set_size_request(-1, docklet.props.size)
            self.docklet_label.set_alignment(0.1, 0.5)
        elif (docklet.get_pos_type() == gtk.POS_BOTTOM):
            label_align.set(0.0, 1.0, 1.0, 0.0)
            self.docklet_label.set_size_request(-1, docklet.props.size)
            self.docklet_label.set_alignment(0.1, 0.5)
        elif (docklet.get_pos_type() == gtk.POS_LEFT):
            label_align.set(0.0, 0.0, 0.0, 1.0)
            self.docklet_label.set_angle(90)
            self.docklet_label.set_size_request(docklet.props.size, -1)
            self.docklet_label.set_alignment(0.5, 0.1)
        elif (docklet.get_pos_type() == gtk.POS_RIGHT):
            label_align.set(1.0, 0.0, 0.0, 1.0)
            self.docklet_label.set_angle(270)
            self.docklet_label.set_size_request(docklet.props.size, -1)
            self.docklet_label.set_alignment(0.5, 0.1)
        label_align.add(self.docklet_label)

        box.pack_start(label_align)
        top_box.pack_start(align)

        icon_box = awn.IconBox(docklet)

        icon_loader = self.get_icon()
        
        play_state = 'pause' if self.is_playing else 'play'
        play_button_size = (docklet.props.max_size + docklet.props.size) / 2
        play_pause = awn.Icon(bind_effects = False)
        play_pause.set_from_pixbuf(
            icon_loader.get_icon_at_size(play_button_size, play_state)
        )
        play_pause.connect("clicked", self.button_pp_press)
        # we need to add the child in two steps, because IconBox overrides 
        # add() method and it must be called to set proper size/orient etc.
        icon_box.add(play_pause)
        icon_box.set_child_packing(play_pause, False, True, 0, gtk.PACK_START)
        self.docklet_play_pause = play_pause

        prev_button = awn.Icon(bind_effects = False)
        prev_button.set_from_pixbuf(
            icon_loader.get_icon_at_size(docklet.props.size, 'prev')
        )
        prev_button.connect("clicked", self.button_previous_press)
        icon_box.add(prev_button)
        icon_box.set_child_packing(prev_button, False, True, 0, gtk.PACK_START)

        next_button = awn.Icon(bind_effects = False)
        next_button.set_from_pixbuf(
            icon_loader.get_icon_at_size(docklet.props.size, 'next')
        )
        next_button.connect("clicked", self.button_next_press)
        icon_box.add(next_button)
        icon_box.set_child_packing(next_button, False, True, 0, gtk.PACK_START)

        top_box.add(icon_box)
        docklet.add(top_box)

        gtk.Plug.__init__(docklet, long(window_id))
        docklet.show_all()

    def icon_clicked(self, widget):
        if self.is_dialog_visible():
            self.dialog.hide()
        else:
            if not self.MediaPlayer: self.ensure_player()
            # update controls
            if self.MediaPlayer:
                self.update_song_info(True)
                if self.use_docklet and self.MediaPlayer.is_async():
                    docklet_win = self.docklet_request (450, False)
                    if docklet_win != 0:
                        self.show_docklet(docklet_win)
                    else:
                        self.dialog.show_all()
                else:
                    self.dialog.show_all()
            else:
                # show the media-players menu
                self.dialog.show_all()

    def menu_popup(self, widget, event):
        self.popup_menu.popup(None, None, None, event.button, event.time)

    def wheel_turn (self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.button_next_press(widget)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.button_previous_press(widget)

    def start_player_pressed(self, widget, args):
        mediaplayers.__dict__[args]().start()
        self.dialog.hide()

    def enter_notify(self, widget, event):
        try:
            if (self.MediaPlayer and self.MediaPlayer.is_async() == False):
                self.update_song_info()
        except:
            self.MediaPlayer = None

    def ensure_player(self, player_name = None):
        try:
            if not player_name: self.player_name = mediaplayers.get_app_name()
            else: self.player_name = player_name
        except:
            self.player_name = None
        if self.player_name in [None, '']:
            self.players_frame.set_no_show_all(False)
            self.controls.set_no_show_all(True)
            self.controls.hide()
            self.set_tooltip_text(MediaControlApplet.APPLET_NAME)
            self.label.set_markup(MediaControlApplet.APPLET_NAME_MARKUP)
            self.MediaPlayer = None
            self.is_playing = False
            self.album_overlay.props.active = False
            if self.docklet_visible: self.docklet.destroy()
        else:
            self.MediaPlayer = mediaplayers.__dict__[self.player_name]()
            self.MediaPlayer.set_song_change_callback(self.song_changed)
            self.MediaPlayer.set_playing_changed_callback(self.play_state_changed)
            self.players_frame.set_no_show_all(True)
            self.controls.set_no_show_all(False)
            self.players_frame.hide()

    def get_supported_player_names(self):
        """
        This function gets all supported player names from
        awn.extras.awnmediaplayers module.
        """
        result = []
        for name, value in mediaplayers.__dict__.iteritems():
            # check if value is subclass of GenericPlayer
            if hasattr(value, '__bases__') and issubclass(value, mediaplayers.GenericPlayer) and value != mediaplayers.GenericPlayer and value != mediaplayers.MPRISPlayer:
                result.append(name)

        self.dbus_names = {}
        def filter_and_append(clsName):
            obj = mediaplayers.__dict__[clsName]()
            if obj.is_available():
                name = obj.get_dbus_name()
                if name != None: self.dbus_names[name] = clsName
                return True
            return False

        result = filter(filter_and_append, result)
        result.sort()

        return result

    def song_changed(self):
        # multiple signals can come in at once - better use a timer
        if not self.timer_running:
            def timer_callback():
                self.timer_running = False
                self.update_song_info(True)
                return False
 
            self.timer_running = True
            gobject.timeout_add(150, timer_callback)

    def play_state_changed(self, playing):
        if self.playing_changed_id != 0:
            gobject.source_remove(self.playing_changed_id)

        def timer_callback(playing):
            self.playing_changed_id = 0
            self.is_playing = playing
            self.update_playing_state()
            return False

        self.playing_changed_id = gobject.timeout_add(150, timer_callback, playing)

    def name_owner_changed_cb(self, name, oldAddress, newAddress):
        if name in self.dbus_names:
            started = newAddress != ''
            if started and not self.MediaPlayer:
                self.ensure_player(self.dbus_names[name])
            elif self.MediaPlayer and started == False and name == self.MediaPlayer.get_dbus_name():
                self.ensure_player('')

    def update_playing_state(self):
        if self.docklet_visible:
            icon_loader = self.get_icon()
            state = 'pause' if self.is_playing else 'play'

            play_button_size = (self.docklet.props.max_size + self.docklet.props.size) / 2

            self.docklet_play_pause.set_from_pixbuf(
                icon_loader.get_icon_at_size(play_button_size, state)
            )

    @error_decorator
    def update_song_info(self, force_update=False):
        """
        This method changes the application titles and album art
        """

        song_info = self.MediaPlayer.get_media_info()
        self.is_playing = self.MediaPlayer.is_playing()

        def get_tooltip_text(info):
            if 'artist' in info:
                if self.tooltip_order == 0:
                    return '%s - %s' % (info['title'], info['artist'])
                else:
                    return '%s - %s' % (info['artist'], info['title'])
            else:
                return info['title']

        tooltip_text = get_tooltip_text(song_info)
        self.set_tooltip_text(tooltip_text)

        try:
            album_art_file = song_info['album-art']
            if self.album_art_enabled and album_art_file != '':
                self.album_art_pixbuf = gtk.gdk.pixbuf_new_from_file(album_art_file)
                self.album_overlay.props.pixbuf = self.album_art_pixbuf
                self.album_overlay.props.active = True
            else:
                raise RuntimeError('No album art')
        except:
            self.album_overlay.props.active = False
            self.album_art_pixbuf = None

        # no need to set dialog elements if it's not visible
        if not force_update:
            if (not self.is_dialog_visible()) and (not self.docklet_visible):
                return False

        if self.is_dialog_visible() or force_update:
            has_artist = 'artist' in song_info and song_info['artist'] != ''
            has_album = 'album' in song_info and song_info['album'] != ''
            markup = '<span weight="bold">' + gobject.markup_escape_text(song_info['title']) + '</span>'
            if has_artist:
                markup += '\n<span style="italic">by</span> %s' % gobject.markup_escape_text(song_info['artist'])
                if has_album:
                    markup += ' <span style="italic">from</span> %s' % gobject.markup_escape_text(song_info['album'])

            self.label.set_markup(markup)
            try:
                if self.album_art_enabled and self.album_art_pixbuf is not None:
                    scaled_pixbuf = self.album_art_pixbuf.scale_simple(
                        self.album_art_size, 
                        self.album_art_size,
                        gtk.gdk.INTERP_BILINEAR)
                    self.image.set_from_pixbuf(scaled_pixbuf)
            except:
                if self.no_album_art_pixbuf is not None:
                    scaled_pixbuf = self.no_album_art_pixbuf.scale_simple(
                        self.album_art_size,
                        self.album_art_size,
                        gtk.gdk.INTERP_BILINEAR)
                    self.image.set_from_pixbuf(scaled_pixbuf)

        # update docklet
        if self.docklet_visible:
            pixbuf = self.get_pixbuf_for_docklet()
            if pixbuf: self.docklet_image.set_from_pixbuf(pixbuf)
            self.docklet_label.set_markup(markup)

        return False

    @error_decorator
    def button_previous_press(self, widget, *args):
        self.MediaPlayer.previous()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False):
            self.update_song_info()

    @error_decorator
    def button_pp_press(self, widget, *args):
        self.MediaPlayer.play_pause()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False):
            self.update_song_info()

    @error_decorator
    def button_next_press(self, widget, *args):
        self.MediaPlayer.next()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False):
            self.update_song_info()

    @error_decorator
    def applet_drag_motion_cb(self, widget, context, x, y, time):
        if not self.MediaPlayer: return True
        self.get_effects().start(awn.EFFECT_LAUNCHING)
        return True

    @error_decorator
    def applet_drag_leave_cb(self, widget, context, time):
        self.get_effects().stop(awn.EFFECT_LAUNCHING)
        return True

    @error_decorator
    def applet_drop_cb(self, wdgt, context, x, y, selection, targetType, time):
        if not self.MediaPlayer:
            context.finish(False, False, time)
            return True
        result = False
        # I wonder why there are zeroes sometimes?
        all_uris = selection.data.strip('\000').strip()

        # lets support directories
        def walk_dirs(vfs_file, out_list):
            for item in vfs_file.enumerate_children():
                if item.props.file_type == vfs.FILE_TYPE_DIRECTORY:
                    walk_dirs(item, out_list)
                else:
                    # lda doesn't support getting mime-type :/
                    out_list.append(item.props.uri) # lda leaks here

        uris = []
        for uri in all_uris.split():
            f = vfs.File.for_uri(uri)
            if f.props.file_type == vfs.FILE_TYPE_DIRECTORY:
                walk_dirs(f, uris)
            else:
                uris.append(f.props.uri)

        if len(uris) == 0:
            result = False
        elif len(uris) > 1:
            result = self.MediaPlayer.enqueue_uris(uris)
        else:
            result = self.MediaPlayer.play_uri(uris[0])
        context.finish(result, False, time)
        return True

    def show_prefs(self, widget):
        ui_path = os.path.join(os.path.dirname(__file__), "media-control.ui")

        wTree = gtk.Builder()
        wTree.add_from_file(ui_path)

        window = wTree.get_object("dialog1")
        window.set_icon(self.get_icon().get_icon_at_size(48))

        client = awn.config_get_default_for_applet(self)

        combo = wTree.get_object("tooltip_format_combo")
        formats = gtk.ListStore(str)
        for item in [_("Title - Artist"), _("Artist - Title")]:
            formats.append([item])
        combo.set_model(formats)
        ren = gtk.CellRendererText()
        combo.pack_start(ren)
        combo.add_attribute(ren, "text", 0)

        docklet_check = wTree.get_object("docklet_checkbox")
        album_art_check = wTree.get_object("album_art_checkbox")
        size_spin = wTree.get_object("album_art_size_spin")

        client.bind(GROUP_DEFAULT, "tooltip_format",
                    combo, "active", False, BIND_METHOD_FALLBACK)
        client.bind(GROUP_DEFAULT, "use_docklet",
                    docklet_check, "active", False, BIND_METHOD_FALLBACK)
        client.bind(GROUP_DEFAULT, "show_album_art",
                    album_art_check, "active", False, BIND_METHOD_FALLBACK)
        client.bind(GROUP_DEFAULT, "album_art_size",
                    size_spin, "value", False, BIND_METHOD_FALLBACK)

        close_button = wTree.get_object("close_button")
        close_button.connect("clicked", lambda x: window.destroy())

        def unbind_all():
            client.unbind_all_for_object(combo)
            client.unbind_all_for_object(docklet_check)
            client.unbind_all_for_object(album_art_check)
            client.unbind_all_for_object(size_spin)
        window.connect("destroy", lambda x: unbind_all())
        window.show()

    def show_about(self, widget):
        about = gtk.AboutDialog()
        awn_icon = self.get_icon()
        about.set_logo(awn_icon.get_icon_at_size(48))
        about.set_icon(awn_icon.get_icon_at_size(64))
        about.set_name("Media Control Applet")
        about.set_copyright("Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>")
        about.set_authors(["Randal Barlow <im.tehk at gmail.com>", "Michal Hruby <michal.mhr at gmail.com>"])
        about.set_comments("Controls your favourite music player.")
        about.set_license("This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.")
        about.set_wrap_license(True)
        about.set_documenters(["Randal Barlow <im.tehk at gmail.com>"])
        about.set_artists(["Claudio Benech"])
        about.run()
        about.destroy()


if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    applet = MediaControlApplet   (awn.uid, awn.panel_id)
    awn.embed_applet              (applet)
    applet.show_all               ()
    gtk.main                      ()
