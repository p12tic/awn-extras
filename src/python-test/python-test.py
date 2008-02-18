#!/usr/bin/python
#
#       AWN Test Python Applet
#
#       Copyright (c) 2007 Neil Jagdish Patel
#
#       This library is free software; you can redistribute it and/or
#       modify it under the terms of the GNU Lesser General Public
#       License as published by the Free Software Foundation; either
#       version 2 of the License, or (at your option) any later version.
#
#       This library is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#       Lesser General Public License for more details.
#
#       You should have received a copy of the GNU Lesser General Public
#       License along with this library; if not, write to the
#       Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#       Boston, MA 02111-1307, USA.

import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn

class App(awn.AppletSimple):
    def __init__(self, uid, orient, height):
        # Initiate Applet
        awn.AppletSimple.__init__(self, uid, orient, height)
        self.height = height

        # Get, resize, set icon
        self.theme = gtk.IconTheme()
        icon = self.theme.load_icon("gtk-apply", height, 0)
        if height != icon.get_height():
          icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        #icon = gdk.pixbuf_new_from_file("/home/njp/Projects/test.png")
        self.set_temp_icon(icon)

        # Get out title ready
        self.title = awn.awn_title_get_default()

        # Draw our dialog
        self.dialog = awn.AppletDialog(self)
        button = gtk.Button(stock="gtk-apply")
        self.dialog.add(button)
        button.show_all()

        self.showing_dlog = False

        # Connect our events
        self.connect("button-press-event", self.button_press)
        self.connect("enter-notify-event", self.enter_notify)
        self.connect("leave-notify-event", self.leave_notify)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)

    def button_press(self, widget, event):
        if self.showing_dlog:
            self.dialog.hide()
        else:
            self.dialog.show_all()

        self.title.hide(self)
        self.showing_dlog = not self.showing_dlog
        # show dialog

    def dialog_focus_out(self, widget, event):
        self.dialog.hide()
        # hide dialog

    def enter_notify(self, widget, event):
        self.title.show(self, "Test python applet")

        #icon = self.theme.load_icon ("gtk-apply", self.height, 0)
        #if self.height != icon.get_height():
          #icon = icon.scale_simple(self.height,self.height,gtk.gdk.INTERP_BILINEAR)
        #self.set_temp_icon (icon)
        # show title

    def leave_notify(self, widget, event):
        self.title.hide (self)
        #icon = self.theme.load_icon ("gtk-cancel", self.height, 0)
        #if self.height != icon.get_height():
          #icon = icon.scale_simple(self.height,self.height,gtk.gdk.INTERP_BILINEAR)
        #self.set_temp_icon (icon)
        # hide title

if __name__ == "__main__":
    awn.init(sys.argv[1:])
    #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
    applet = App(awn.uid, awn.orient, awn.height)
    awn.init_applet(applet)
    applet.show_all()
    gtk.main()
