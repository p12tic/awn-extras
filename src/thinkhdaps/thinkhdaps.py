#!/usr/bin/env python
#
# Copyright (C) 2008  onox
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import gobject
import pygtk
pygtk.require("2.0")
import gtk
from gtk import gdk
from awn.extras import AWNLib

applet_name = "ThinkHDAPS Applet"
applet_version = "0.2.8"
applet_description = "Applet that shows the status of HDAPS"

# Interval in milliseconds between two successive status checks
check_status_interval = 100

""" Set of names of possible hard disk devices. It's important
that names of devices that may not be a hard disk are at the end of the set """
devices = ("sda", "hda")

hdaps_short_description = "Active Protection System"

image_dir = os.path.join(os.path.dirname(__file__), "images")

# Logo of the applet, shown in the GTK+ About dialog
applet_logo = os.path.join(image_dir, "thinkhdaps-logo.svg")

# Images used as the applet's icon to reflect the current status of HDAPS
file_icon_running = os.path.join(image_dir, "thinkhdaps-logo.svg")
file_icon_paused = os.path.join(image_dir, "thinkhdaps-paused.svg")
file_icon_error = os.path.join(image_dir, "thinkhdaps-error.svg")


class AboutDialog(gtk.AboutDialog):
    """ Shows the GTK+ About dialog """
    
    def __init__(self, applet):
        gtk.AboutDialog.__init__(self)
        
        self.applet = applet
        
        self.set_name(applet_name)
        self.set_version(applet_version)
        self.set_comments(applet_description)
        self.set_copyright("Copyright \xc2\xa9 2008 onox")
        self.set_authors(["onox"])
        self.set_artists(["Jakub Steiner", "Lapo Calamandrei", "Rodney Dawes", "Garrett LeSage", "onox"])
        self.set_logo(gdk.pixbuf_new_from_file(applet_logo))
        
        self.update_icon()
        
        # Connect some signals to be able to hide the window
        self.connect("response", self.response_event)
        self.connect("delete_event", self.delete_event)
    
    def delete_event(self, widget, event):
        return True
    
    def response_event(self, widget, response):
        if response < 0:
            self.hide()
    
    def update_icon(self):
        """ Reloads the applet's logo to be of the same height as the panel """
        
        height = self.applet.get_height()
        self.set_icon(gdk.pixbuf_new_from_file_at_size(applet_logo, height, height))

class ThinkHDAPSApplet:
    """ Applet that shows the status of HDAPS """

    def check_status_cb(self, this):
        """ Checks the status the hard disk monitored by HDAPS. Changes
        the applet's icon when necessary """
        
        try:
            self.was_paused = self.paused
            self.paused = int(open("/sys/block/" + self.hdaps_device + "/queue/protect").readline())
            
            # Change icon if status has changed
            if self.paused != self.was_paused or self.error_occurred:
                if self.paused:
                    self.applet.icon.set(self.icon_paused, True)
                else:
                    self.applet.icon.set(self.icon_running, True)
            
            if self.error_occurred:
                self.error_occurred = False
                self.applet.title.set(hdaps_short_description + " active")
        except IOError:
            if not self.error_occurred:
                self.error_occurred = True
                
                # Just load the icon here, it's not gonna be used often
                height = self.applet.get_height()
                icon_error = gdk.pixbuf_new_from_file_at_size(file_icon_error, height, height)
                
                self.applet.icon.set(icon_error, True)
                
                if self.hdaps_device:
                    self.applet.title.set(hdaps_short_description + " disabled")
                else:
                    self.applet.title.set("No hard disk found")
        
        return True
    
    def __init__(self, applet):
        self.applet = applet
        
        self.setup_icon()
        
        # Set the applet's current icon
        self.applet.icon.set(self.icon_running, True)
        
        applet.title.set(hdaps_short_description + " active")
        
        self.setup_dialog_about()
        
        self.paused = 0
        self.was_paused = False
        self.error_occurred = False
        
        self.hdaps_device = ""
        for device in devices:
            if os.path.isdir(os.path.join("/sys/block", device)):
                self.hdaps_device = device
                break
        
        applet.connect("height-changed", self.height_changed_cb)
        
        # Set up a timer for checking the status of HDAPS if a hard disk has been found
        if self.hdaps_device:
            gobject.timeout_add(check_status_interval, self.check_status_cb, self)
        else:
            self.check_status_cb(self)
    
    def height_changed_cb(self, widget, event):
        """ Updates the applet's icon and the icon of
        the About dialog to reflect the new height """
        
        self.setup_icon()
        
        # Toggle the flag to the wrong state to trigger the update of the icon
        self.error_occurred = not self.error_occurred
        
        # Check the status to update the applet's icon
        self.check_status_cb(self)
        
        # Update the icon of the AboutDialog
        self.about_dialog.update_icon()
    
    def setup_icon(self):
        """ Loads the images that are going to be used as the applet's icon """
        
        height = self.applet.get_height()
        self.icon_running = gdk.pixbuf_new_from_file_at_size(file_icon_running, height, height)
        self.icon_paused = gdk.pixbuf_new_from_file_at_size(file_icon_paused, height, height)
    
    def setup_dialog_about(self):
        """ Creates the GTK+ About dialog """
        
        self.about_dialog = AboutDialog(self.applet)
        
        menu = self.applet.dialog.new("menu")
        about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
        menu.append(about_item)
        menu.show_all()
        about_item.connect("activate", self.activate_about_dialog_cb)
    
    def activate_about_dialog_cb(self, widget):
        self.about_dialog.show()
    

if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "hdaps"})
    ThinkHDAPSApplet(applet)
    AWNLib.start(applet)