# !/usr/bin/python

# Copyright (c) 2007 Randal Barlow
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
import mediaplayers
class App (awn.AppletSimple):
    """
    """
    def __init__ (self, uid, orient, height):
        """
        Creating the applets core
        """

        #self.resultToolTip                  = "Rhythmbox Control Applet"
        self.keylocation                    = "/apps/avant-window-navigator/applets/MediaControl/"
        location                            =  __file__
        self.location                       = location.replace('medialogoback.py','')
        self.location_icon                  = self.location + 'icons/backward.svg'
        self.what_app()
        # The Heart
        awn.AppletSimple.__init__             (self, uid, orient, height)
        self.height                         = height
        icon                                = gdk.pixbuf_new_from_file (self.location_icon)
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_icon                         (icon)
        self.title                          = awn.awn_title_get_default ()

        # Standard AWN Connects
        self.connect                          ("button-press-event", self.button_press)
        #self.connect                          ("enter-notify-event", self.enter_notify)
        #self.connect                          ("leave-notify-event", self.leave_notify)

    #############
    # Applet standard methods
    #############
    def button_press                          (self, widget, event):
        self.button_previous_press                  ()
    #    self.title.hide                       (self)
    #def dialog_focus_out                      (self, widget, event):
    #    print ''
    #def enter_notify                          (self, widget, event):
    #    self.title.show                       (self, self.resultToolTip)
    #def leave_notify                          (self, widget, event):
    #    self.title.hide                       (self)
    #############
    # Gconf
    #############
    def what_app(self):
        self.player_name                    = mediaplayers.what_app()
        if self.player_name == None:pass
        else:self.MediaPlayer               = mediaplayers.__dict__[self.player_name]()
        #print self.player_name
    #############
    # Rhythmbox specific control methods
    #############
    def button_previous_press                 (self):
        try:
            try:
                try:
                    self.MediaPlayer.button_previous_press()
                except dbus.exceptions.DBusException:self.what_app()
            except AttributeError:self.what_app()
        except RuntimeError:self.what_app()
    def button_pp_press                       (self):
        try:
            try:
                try:
                    self.MediaPlayer.button_pp_press()
                except dbus.exceptions.DBusException:self.what_app()
            except AttributeError:self.what_app()
        except RuntimeError:self.what_app()
    def button_next_press                     (self):
        try:
            try:
                try:
                    self.MediaPlayer.button_next_press()
                except dbus.exceptions.DBusException:self.what_app()
            except AttributeError:self.what_app()
        except RuntimeError:self.what_app()
if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
