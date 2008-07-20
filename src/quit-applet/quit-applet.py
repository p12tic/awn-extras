#!/usr/bin/python

# Copyright (c) 2007  Randal Barlow <im.tehk at gmail.com>
#               2008  onox <denkpadje@gmail.com>
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

import commands
import os
import subprocess

import pygtk
pygtk.require("2.0")
import gtk
from awn.extras import AWNLib

applet_name = "Quit-Log Out"
applet_version = "0.2.8"
applet_description = "An applet to exit or log out of your session"

# Themed logo of the applet, used as the applet's icon and shown in the GTK About dialog
applet_logo = "application-exit"


class QuitLogOutApplet:
    """ An applet to exit or log out of your session """
    
    def __init__(self, applet):
        self.applet = applet
        
        applet.title.set("Log Out " + commands.getoutput("/usr/bin/whoami") + "...")
        
        self.setup_context_menu()
        
        applet.connect("button-press-event", self.button_press_event_cb)
    
    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            subprocess.Popen(self.logout_command, shell=True)
    
    def setup_context_menu(self):
        """ Creates a context menu to activate "Preferences" ("About" window
        is created automatically by AWNLib) """
        
        prefs_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        prefs_item.connect("activate", self.show_prefs_dialog_cb)
        self.applet.dialog.menu.insert(prefs_item, 3)
        
        pref_dialog = self.applet.dialog.new("preferences")
        pref_dialog.connect("response", self.pref_dialog_response_cb)
        
        self.setup_dialog_settings(pref_dialog.vbox)
    
    def show_prefs_dialog_cb(self, widget):
        self.applet.dialog.toggle("preferences", "show")
    
    def setup_dialog_settings(self, vbox):
        """ Loads the settings """
        
        if "logout_command" not in self.applet.settings:
            self.applet.settings["logout_command"] = "gnome-session-save --kill"
        self.logout_command = self.applet.settings["logout_command"]
        
        # TODO replace the entry by a combobox that has the values: GNOME, KDE, ..., custom, etc.
        self.entry_logout = gtk.Entry()
        self.entry_logout.set_text(self.logout_command)
        
        """ Wrap the entry in a vbox that has a non-zero border width
        to align the entry with the close button """
        extra_vbox = gtk.VBox()
        extra_vbox.set_border_width(5)
        extra_vbox.add(self.entry_logout)
        
        vbox.add(extra_vbox)
    
    def pref_dialog_response_cb(self, widget, response):
        self.applet.settings["logout_command"] = self.logout_command = self.entry_logout.get_text()


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "quit",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox, tehk",
        "copyright-year": 2008,
        "authors": ["Randal Barlow <im.tehk at gmail.com>", "onox <denkpadje@gmail.com>"]})
    QuitLogOutApplet(applet)
    AWNLib.start(applet)