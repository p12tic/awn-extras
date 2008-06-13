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


import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import dbus
import gconf
import awn.extras.awnmediaplayers as mediaplayers


class App (awn.AppletSimple):
    """
    """
    def __init__ (self, uid, orient, height):
        """
        Creating the applets core
        """

        self.resultToolTip = "Media Control Applet"
        self.keylocation = "/apps/avant-window-navigator/applets/MediaControl/"
        location =  __file__
        self.location = location.replace('mediacontrol.py','')
        self.location_icon = self.location + '/icons/rhythmbox.svg'
        self.load_keys()
        self.what_app()
        # The Heart
        awn.AppletSimple.__init__(self, uid, orient, height)
        self.height = height
        icon = gdk.pixbuf_new_from_file (self.location_icon)
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_icon(icon)
        self.title = awn.awn_title_get_default ()
        self.dialog = awn.AppletDialog (self)
        self.dialog_visible = False
        self.popup_menu = self.create_default_menu()
        # Defining Widgets
        vbox = gtk.VBox()
        hbox = gtk.HBox()
        self.label = gtk.Label("Media Control Applet")
        button_previous = gtk.ToolButton ("gtk-media-previous")
        button_play = gtk.ToolButton ("gtk-media-play")
        button_pause = gtk.ToolButton ("gtk-media-pause")
        button_next = gtk.ToolButton ("gtk-media-next")
        self.image = gtk.Image()
        # Packing Widgets
        hbox.pack_start(button_previous)
        hbox.add(button_play)
        hbox.add(button_next)
        vbox.pack_start(self.image)
        vbox.add(self.label)
        vbox.add(hbox)
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
                self.labeler()
                self.dialog.show_all()
                self.dialog_visible = True
        elif event.button == 2:
            self.button_pp_press(widget)
        elif event.button == 3:
            self.popup_menu.popup(None, None, None, event.button, event.time)

    def wheel_turn (self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.button_next_press(widget)
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.button_previous_press(widget)
        self.labeler()

    def dialog_focus_out(self, widget, event):
        self.dialog.hide()
        self.dialog_visible = False

    def enter_notify(self, widget, event):
        self.labeler()
        self.title.show(self, self.resultToolTip)

    def leave_notify(self, widget, event):
        self.title.hide(self)

    def what_app(self):
        self.player_name = mediaplayers.what_app()
        if self.player_name == None:pass
        else:self.MediaPlayer = mediaplayers.__dict__[self.player_name]()

    def key_control(self,keyname,default):
        """
        This Method takes the keyname and the defualt value and either loads an existing key -or- loads and saves the defualt key if no key is defined
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
        #self.player_name = self.key_control ("PlayerName","Rhythmbox")
        self.artOnOff = self.key_control("Album_Art",'on')
        self.titleBoldFont = self.key_control("titleBoldFont","on")
        self.titleLen = self.key_control("TitleLen","33")
        self.titleLen = eval(self.titleLen)
        self.albumArtSize = self.key_control('albumArtSize',"150")
        self.albumArtSize = eval(self.albumArtSize)
        self.noArtIconDefault = self.location + "noArtIcon.png"
        self.noArtIcon = self.key_control('noArtIcon',self.noArtIconDefault)
        self.titleOrder = self.key_control('titleOrder',"artist - title")

    def labeler(self):
        """
        This method changes the application titles and album art
        """
        try:
            try:
                try:
                    artExact, result, self.resultToolTip = self.MediaPlayer.labeler(self.artOnOff,self.titleOrder,self.titleLen,self.titleBoldFont)
                    self.label.set_markup(result)
                    try:
                        if self.artOnOff               == 'on':
                            self.image.set_from_pixbuf    (gtk.gdk.pixbuf_new_from_file(artExact).scale_simple(self.albumArtSize,self.albumArtSize,gtk.gdk.INTERP_BILINEAR))
                    except gobject.GError:
                        try:self.image.set_from_pixbuf    (gtk.gdk.pixbuf_new_from_file(self.noArtIcon).scale_simple(self.albumArtSize,self.albumArtSize,gtk.gdk.INTERP_BILINEAR))
                        except:gobject.GError
                except dbus.exceptions.DBusException:self.what_app()
            except:AttributeError
        except RuntimeError: self.what_app()

    def button_previous_press                 (self, widget):
        try:
            try:
                try:
                    self.MediaPlayer.button_previous_press()
                    self.labeler                          ()
                except dbus.exceptions.DBusException:self.what_app()
            except AttributeError:self.what_app()
        except RuntimeError:self.what_app()

    def button_pp_press                       (self, widget):
        try:
            try:
                try:
                    self.MediaPlayer.button_pp_press()
                    self.labeler()
                except dbus.exceptions.DBusException:self.what_app()
            except AttributeError:self.what_app()
        except RuntimeError:self.what_app()

    def button_next_press                     (self, widget):
        try:
            try:
                try:
                    self.MediaPlayer.button_next_press()
                    self.labeler                        ()
                except dbus.exceptions.DBusException:self.what_app()
            except AttributeError:self.what_app()
        except RuntimeError:self.what_app()


if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
