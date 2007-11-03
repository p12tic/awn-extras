#!/usr/bin/python

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
import gconf

class App (awn.AppletSimple):
    def __init__ (self, uid, orient, height):
        self.location = __file__.replace('quit-applet.py','')
        self.keylocation = "/apps/avant-window-navigator/applets/QuitApplet/"
        self.load_keys()
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
        self.theme = gtk.IconTheme ()
        try:
            icon = gdk.pixbuf_new_from_file (self.icon_location)
        except: icon = gdk.pixbuf_new_from_file (self.location + "icons/application-exit.svg")
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_temp_icon (icon)
        self.title = awn.awn_title_get_default ()
        self.connect ("button-press-event", self.button_press)
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)
    def button_press (self, widget, event):
        self.title.hide (self)
        os.system("gnome-session-save --kill")      
    #def dialog_focus_out (self, widget, event):
    #  print ""
    def enter_notify (self, widget, event):
        self.title.show (self, "Quit/Logout?")
    def leave_notify (self, widget, event):
        self.title.hide (self)
    def load_keys(self):
        self.client                         = gconf.client_get_default()
        #<Name of Variable> = self.key_control (<Name of Key>,<Default Value>)
        self.icon_location                       = self.key_control ("IconLocation",self.location + "icons/application-exit.svg")

    def key_control(self,keyname,default):
        keylocation_with_name               = self.keylocation + keyname
        try:
            var                             = self.client.get_string(keylocation_with_name)
            if var                         == None:
                var                         = default
                self.client.set_string        (keylocation_with_name,var)
        except NameError:
            var                             = default
        return var  
if __name__ == "__main__":
    awn.init (sys.argv[1:])
    applet = App (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
