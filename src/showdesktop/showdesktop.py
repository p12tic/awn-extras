# -*- coding: utf-8 -*-
# vim: ts=4
# 
# Copyright (C) 2006  Mehdi Abaakouk <theli48@gmail.com>
#               2008  onox <denkpadje@gmail.com>
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

import pygtk
pygtk.require('2.0')
import gtk
from awn.extras import AWNLib
import wnck

applet_name = "Show Desktop"
applet_version = "0.2.8"
applet_description = "An applet to hide your windows and show your desktop"

# Themed logo of the applet, used as the applet's icon and shown in the GTK About dialog
applet_logo = "desktop"

titles = {True: "Show hidden windows", False: "Hide windows and show desktop"}

class ShowDesktopApplet:
    """ An applet to hide your windows and show your desktop """
    
    def __init__(self, applet):
        self.applet = applet
        
        applet.title.set(titles[wnck.screen_get_default().get_showing_desktop()])
        
        applet.connect("button-press-event", self.button_press_event_cb)
    
    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            screen = wnck.screen_get_default()
            
            # showing windows = not showing desktop
            showing_windows = not screen.get_showing_desktop()
            screen.toggle_showing_desktop(showing_windows)
            
            """ If windows were shown, they are now hidden, and next switch
            will make them visible again """
            applet.title.set(titles[showing_windows])


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "show-desktop",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_logo,
        "author": "Mehdi Abaakouk, onox",
        "copyright-year": 2006,
        "authors": ["Mehdi Abaakouk <theli48@gmail.com>", "onox <denkpadje@gmail.com>"]})
    ShowDesktopApplet(applet)
    AWNLib.start(applet)