# Copyright (C) 2008  onox <denkpadje@gmail.com>
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

import gobject
import pygtk
pygtk.require("2.0")
import gtk
from gtk import gdk

from awn.extras import AWNLib

applet_name = "ThinkHDAPS"
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


class ThinkHDAPSApplet:

    """Applet that shows the status of HDAPS.
    
    """

    def check_status_cb(self, this):
        """Check the status the hard disk monitored by HDAPS and change
        the applet's icon if necessary,
        
        """
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
        applet.icon.set(self.icon_running, True)
        
        applet.title.set(hdaps_short_description + " active")
        
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
        """Update the applet's icon, because the height of the panel
        has changed.
        
        """
        self.setup_icon()
        
        # Toggle the flag to the wrong state to trigger the update of the icon
        self.error_occurred = not self.error_occurred
        
        # Check the status to update the applet's icon
        self.check_status_cb(self)
    
    def setup_icon(self):
        """Load the images that are going to be used as the applet's icon.
        
        """
        height = self.applet.get_height()
        self.icon_running = gdk.pixbuf_new_from_file_at_size(file_icon_running, height, height)
        self.icon_paused = gdk.pixbuf_new_from_file_at_size(file_icon_paused, height, height)


if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "hdaps",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": 2008,
        "authors": ["onox"],
        "artists": ["Jakub Steiner", "Lapo Calamandrei", "Rodney Dawes", "Garrett LeSage", "onox"]})
    ThinkHDAPSApplet(applet)
    AWNLib.start(applet)