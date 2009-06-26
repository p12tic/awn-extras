#!/usr/bin/python

# Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>
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
import gnomevfs
import urllib

from gobject import GError
import gobject
import gtk
import dbus
import gconf

import awn

import awn.extras.awnmediaplayers as mediaplayers

def error_decorator(fn):
    """Handles errors caused by dbus"""
    def errors(cls, *args, **kwargs):
        try:
            fn(cls, *args)
        except (dbus.exceptions.DBusException, AttributeError, RuntimeError):
            cls.what_app()
    return errors


class App (awn.AppletSimple):
    """Displays a dialog with controls and track/album info and art"""

    APPLET_NAME = "Media Control Applet"
    APPLET_NAME_MARKUP = "<span weight=\"bold\">Media Control Applet</span>"
    def __init__(self, uid, panel_id):
        """Creating the applets core"""
        awn.AppletSimple.__init__(self, uid, panel_id)
        self.set_tooltip_text(App.APPLET_NAME)
        self.MediaPlayer = None
        self.location = __file__.replace('mediacontrol.py','')
        self.keylocation = "/apps/avant-window-navigator/applets/MediaControl/"
        self.set_icon_name('media-control', 'media-control')
        self.load_keys()
        self.timer_running = False
        self.dbus_names = {}

        self.players_frame = gtk.Frame()
        self.controls = gtk.VBox()
        self.controls.set_spacing(5)
        self.label = gtk.Label()
        self.label.set_padding(4, 0)
        self.label.set_markup(App.APPLET_NAME_MARKUP)

        self.album_overlay = awn.OverlayPixbufFile()
        self.album_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.album_overlay.props.alpha = 0.85
        self.album_overlay.props.active = False
        self.add_overlay(self.album_overlay)

        # The Heart
        self.dialog = awn.Dialog (self)
        self.dialog_visible = False

        # Docklet related stuff
        self.docklet = None
        self.docklet_visible = False
        self.docklet_image = None
        self.docklet_label = None

        #Popup menu
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect("activate", self.show_about)

        self.popup_menu = self.create_default_menu()
        self.popup_menu.append(self.about)
        self.popup_menu.show_all()

        self.what_app()

        # Defining Widgets
        vbox = gtk.VBox()
        self.players_frame.add(vbox)
        for player in self.get_supported_player_names():
          button = gtk.Button(player)
          button.connect("clicked", self.start_player_pressed, player)
          vbox.add(button)

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
        # Standard AWN Connects
        self.connect("scroll-event", self.wheel_turn)
        self.connect("button-press-event", self.button_press)
        self.connect("enter-notify-event", self.enter_notify)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)
        # Drag&drop support
        self.connect("drag-data-received", self.applet_drop_cb)
        self.connect("drag-motion", self.applet_drag_motion_cb)
        self.connect("drag-leave", self.applet_drag_leave_cb)
        # Button Connects
        button_previous.connect("clicked", self.button_previous_press)
        button_play.connect("clicked", self.button_pp_press)
        button_next.connect("clicked", self.button_next_press)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                           [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                           gtk.gdk.ACTION_COPY)

        try:
            if self.MediaPlayer: self.labeler()
        except: pass

        proxy = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        proxy.connect_to_signal('NameOwnerChanged', self.name_owner_changed_cb)

    def docklet_image_from_dialog_image(self):
        pixbuf = self.image.get_pixbuf()
        if pixbuf == None: return None
        # TODO: orient support
        max_size = self.docklet.props.max_size
        offset = self.docklet.props.offset

        dest_width = int(pixbuf.get_width() * (max_size - offset)
                         / pixbuf.get_height())
        pixbuf = pixbuf.scale_simple(dest_width, max_size - offset,
                                     gtk.gdk.INTERP_BILINEAR)

        return pixbuf

    def init_docklet(self, window_id):
        self.docklet_visible = True
        docklet = awn.Applet(self.props.uid, self.props.panel_id)
        self.docklet = docklet
        docklet.props.quit_on_delete = False

        def invalidate_docklet(widget, applet):
            applet.docklet_visible = False
            applet.docklet = None
        docklet.connect("destroy", invalidate_docklet, self)

        align = awn.Alignment(docklet)
        box = None
        if (docklet.props.orient in [awn.ORIENTATION_TOP,
                                     awn.ORIENTATION_BOTTOM]):
            box = gtk.HBox()
            align.add(box)
        else:
            box = gtk.VBox()
            align.add(box)

        # TODO: not really for side orient yet
        pixbuf = self.docklet_image_from_dialog_image()
        if pixbuf:
            self.docklet_image = gtk.image_new_from_pixbuf(pixbuf)
        else:
            self.docklet_image = gtk.Image()
        self.docklet_image.set_padding(6, 0)
        box.add(self.docklet_image)

        label_align = gtk.Alignment(0.5, 1.0, 1.0, 0.0) # for BOTTOM
        self.docklet_label = gtk.Label()
        self.docklet_label.set_markup(self.label.get_label())
        self.docklet_label.set_size_request(-1, docklet.props.size)
        label_align.add(self.docklet_label)

        box.add(label_align)

        play_button_size = (docklet.props.max_size + docklet.props.size) / 2
        play_pause = awn.ThemedIcon(bind_effects = False)
        play_pause.set_orientation(docklet.props.orient)
        play_pause.set_size(play_button_size)
        play_pause.set_info_simple("media-control-docklet",
                                   docklet.props.uid,
                                   "media-playback-start")
        play_pause.connect("button-press-event", self.button_pp_press)
        box.pack_start(play_pause, False)

        prev_button = awn.ThemedIcon(bind_effects = False)
        prev_button.set_orientation(docklet.props.orient)
        prev_button.set_size(docklet.props.size)
        prev_button.set_info_simple("media-control-docklet",
                                   docklet.props.uid,
                                   "media-skip-backward")
        prev_button.connect("button-press-event", self.button_previous_press)
        box.pack_start(prev_button, False)

        next_button = awn.ThemedIcon(bind_effects = False)
        next_button.set_orientation(docklet.props.orient)
        next_button.set_size(docklet.props.size)
        next_button.set_info_simple("media-control-docklet",
                                   docklet.props.uid,
                                   "media-skip-forward")
        next_button.connect("button-press-event", self.button_next_press)
        box.pack_start(next_button, False)

        docklet.add(align)

        docklet.applet_construct(window_id)
        docklet.show_all()

    def button_press(self, widget, event):
        if event.button == 1:
            if self.dialog_visible:
                self.dialog.hide()
                self.dialog_visible = False
            else:
                if not self.MediaPlayer: self.what_app()
                # update controls
                self.dialog_visible = True
                if self.MediaPlayer:
                    self.labeler()
                    docklet_win = self.docklet_request (400, False) if self.MediaPlayer.is_async() else 0
                    if docklet_win != 0:
                        self.dialog_visible = False
                        self.init_docklet(docklet_win)
                    else:
                        self.dialog.show_all()
                else:
                    # show the media-players menu
                    self.dialog.show_all()
        elif event.button == 2:
            self.button_pp_press(widget)
        elif event.button == 3:
            self.popup_menu.popup(None, None, None, event.button, event.time)

    def wheel_turn (self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.button_next_press(widget)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.button_previous_press(widget)

    def start_player_pressed(self, widget, args):
        mediaplayers.__dict__[args]().start()
        self.dialog.hide()
        self.dialog_visible = False

    def dialog_focus_out(self, widget, event):
        self.dialog.hide()
        self.dialog_visible = False

    def enter_notify(self, widget, event):
        try:
            if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()
        except:
            self.MediaPlayer = None

    def what_app(self, player_name = None):
        if not player_name: self.player_name = mediaplayers.what_app()
        else: self.player_name = player_name
        if self.player_name in [None, '']:
            self.players_frame.set_no_show_all(False)
            self.controls.set_no_show_all(True)
            self.controls.hide()
            self.set_tooltip_text(App.APPLET_NAME)
            self.label.set_markup(App.APPLET_NAME_MARKUP)
            self.MediaPlayer = None
            self.album_overlay.props.active = False
            if self.docklet_visible: self.docklet.destroy()
        else:
            self.MediaPlayer = mediaplayers.__dict__[self.player_name]()
            self.MediaPlayer.set_callback(self.song_changed)
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
            if hasattr(value, '__bases__') and issubclass(value, mediaplayers.GenericPlayer) and value != mediaplayers.GenericPlayer:result.append(name)

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

    def key_control(self,keyname,default):
        """
        This Method takes the keyname and the defualt
        value and either loads an existing key -or-
        loads and saves the defualt key if no key is defined
        """
        keylocation_with_name = self.keylocation + keyname
        try:
            somevar = self.client.get_string(keylocation_with_name)
            if somevar == None:
                somevar = default
                self.client.set_string(keylocation_with_name, somevar)
        except NameError:
            somevar = default
        return somevar

    def load_keys(self):
        """
        Loads all the gconf variables by calling the key_control method
        """
        self.client = gconf.client_get_default()
        self.artOnOff = self.key_control("Album_Art",'on')
        self.titleBoldFont = self.key_control("titleBoldFont","on")
        self.titleLen = self.key_control("TitleLen","33")
        self.titleLen = eval(self.titleLen)
        self.albumArtSize = self.key_control('albumArtSize',"150")
        self.albumArtSize = eval(self.albumArtSize)
        self.noArtIconDefault = self.location + "/icons/noArtIcon.png"
        self.noArtIcon = self.key_control('noArtIcon',self.noArtIconDefault)
        self.titleOrder = self.key_control('titleOrder',"artist - title")

    def song_changed(self):
        # multiple signals can come in at once - better use a timer
        if self.timer_running == False:
          self.timer_running = True
          gobject.timeout_add(150, self.labeler)

    def name_owner_changed_cb(self, name, oldAddress, newAddress):
        if name in self.dbus_names:
            started = newAddress != ''
            if started and not self.MediaPlayer:
                self.what_app(self.dbus_names[name])
            elif self.MediaPlayer and started == False and name == self.MediaPlayer.get_dbus_name():
                self.what_app('')

    @error_decorator
    def labeler(self):
        """
        This method changes the application titles and album art
        """

        self.timer_running = False
        artExact, markup, resultToolTip = self.MediaPlayer.labeler(
            self.artOnOff,
            self.titleOrder,
            self.titleLen,
            self.titleBoldFont)
        self.set_tooltip_text(resultToolTip)
        try:
            if self.artOnOff == 'on' and artExact != '':
                self.album_overlay.props.file_name = artExact
                self.album_overlay.props.active = True
            else:
                self.album_overlay.props.active = False
        except GError:
            self.album_overlay.props.active = False
        
        # no need to set dialog elements if it's not visible
        if (not self.dialog_visible) and (not self.docklet_visible):
            return False

        self.label.set_markup(markup)
        try:
            if self.artOnOff == 'on':
                self.image.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(
                    artExact).scale_simple(self.albumArtSize,
                                           self.albumArtSize,
                                           gtk.gdk.INTERP_BILINEAR))
        except GError:
            try:self.image.set_from_pixbuf(gtk.gdk.pixbuf_new_from_file(
                self.noArtIcon).scale_simple(
                    self.albumArtSize,
                    self.albumArtSize,
                    gtk.gdk.INTERP_BILINEAR))
            except GError: pass

        # update docklet
        if self.docklet_visible:
            pixbuf = self.docklet_image_from_dialog_image()
            if pixbuf: self.docklet_image.set_from_pixbuf(pixbuf)
            self.docklet_label.set_markup(markup)

        return False

    @error_decorator
    def button_previous_press(self, widget, *args):
        self.MediaPlayer.previous()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()

    @error_decorator
    def button_pp_press(self, widget, *args):
        self.MediaPlayer.play_pause()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()

    @error_decorator
    def button_next_press(self, widget, *args):
        self.MediaPlayer.next()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()

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
        uris = []

        # lets support directories
        for uri in all_uris.split():
            uri_obj = gnomevfs.URI(uri)
            path = urllib.unquote(uri_obj.path)
            if os.path.isdir(path) == True:
                for dir, subdirs, filenames in os.walk(path):
                    for filename in filenames:
                        file_uri = gnomevfs.URI(urllib.quote(dir))
                        file_uri = file_uri.append_file_name(filename)
                        is_audio = gnomevfs.Handle(file_uri).get_file_info(gnomevfs.FILE_INFO_GET_MIME_TYPE).mime_type.find('audio') != -1
                        if is_audio == True: uris.append(str(file_uri))
            else:
                uris.append(str(uri_obj))

        if len(uris) == 0: 
            result = False
        elif len(uris) > 1:
            result = self.MediaPlayer.enqueue_uris(uris)
        else:
            result = self.MediaPlayer.play_uri(uris[0])
        context.finish(result, False, time)
        return True

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
    applet = App                  (awn.uid, awn.panel_id)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
