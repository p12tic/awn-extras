# !/usr/bin/python

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

    def __init__ (self, uid, orient, height):
        """Creating the applets core"""
        awn.AppletSimple.__init__(self, uid, orient, height)
        self.resultToolTip = "Media Control Applet"
        self.MediaPlayer = None
        self.location = __file__.replace('mediacontrol.py','')
        self.keylocation = "/apps/avant-window-navigator/applets/MediaControl/"
        self.set_awn_icon('media-control', 'media-control')
        self.load_keys()
        self.timer_running = False

        self.players_frame = gtk.Frame()
        self.controls = gtk.VBox()
        self.controls.set_spacing(5)
        self.label = gtk.Label("Media Control Applet")

        self.what_app()
        # The Heart
        self.height = height
        self.title = awn.awn_title_get_default ()
        self.dialog = awn.AppletDialog (self)
        self.dialog_visible = False
        self.popup_menu = self.create_default_menu()
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
        self.connect("leave-notify-event", self.leave_notify)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)
        # Button Connects
        button_previous.connect("clicked", self.button_previous_press)
        button_play.connect("clicked", self.button_pp_press)
        button_next.connect("clicked", self.button_next_press)

    def button_press(self, widget, event):
        if event.button == 1:
            if self.dialog_visible:
                self.dialog.hide()
                self.dialog_visible = False
            else:
                self.title.hide(self)
                if self.MediaPlayer == None: self.what_app()
                self.dialog_visible = True
                self.labeler()
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
        self.title.show(self, self.resultToolTip)

    def leave_notify(self, widget, event):
        self.title.hide(self)

    def what_app(self):
        self.player_name = mediaplayers.what_app()
        if self.player_name == None:
            self.players_frame.set_no_show_all(False)
            self.controls.set_no_show_all(True)
            self.controls.hide()
            self.resultToolTip = "Media Control Applet"
            self.label.set_text("Media Control Applet")
            self.MediaPlayer = None
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
        
        result = filter(lambda x: mediaplayers.__dict__[x]().is_available(), result)
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
        if self.timer_running == False:
          self.timer_running = True
          gobject.timeout_add(150, self.labeler)

    @error_decorator
    def labeler(self):
        """
        This method changes the application titles and album art
        """

        self.timer_running = False
        artExact, result, self.resultToolTip = self.MediaPlayer.labeler(self.artOnOff,
                                                                        self.titleOrder,
                                                                        self.titleLen,
                                                                        self.titleBoldFont)
        if self.dialog_visible == False: return False
        self.label.set_markup(result)
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
        return False

    @error_decorator
    def button_previous_press(self, widget):
        self.MediaPlayer.button_previous_press()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()

    @error_decorator
    def button_pp_press(self, widget):
        self.MediaPlayer.button_pp_press()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()

    @error_decorator
    def button_next_press(self, widget):
        self.MediaPlayer.button_next_press()
        if (self.MediaPlayer and self.MediaPlayer.is_async() == False): self.labeler()


if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
