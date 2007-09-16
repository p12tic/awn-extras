# -*- coding: utf-8 -*-
# vim: ts=4 
###
#
# showdesktop.py
# Copyright (c) 2006 Mehdi Abaakouk
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
###
#
# Name : showdesktop.py
# Version: 0.1
# Author : mehdi ABAAKOUK Mehdi <theli48@gmail.com>
# Description: Applet to show/hide desktop for awn 
#
###



import pygtk
pygtk.require('2.0')
import gtk
import sys

import wnck
import awn

class ShowDesktopButton (awn.AppletSimple):
    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
        self.theme = gtk.icon_theme_get_default()
        icon = self.theme.load_icon ("desktop", height, 0)
        self.set_icon(icon)
        self.connect ("button-press-event", self.__on_button_press)
    
    def __on_button_press(self,widget, event):
        if event.button == 1:
            screen = wnck.screen_get_default()
            screen.toggle_showing_desktop(not screen.get_showing_desktop())
        
if __name__ == '__main__':
    awn.init (sys.argv[1:])
    applet = ShowDesktopButton (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()

