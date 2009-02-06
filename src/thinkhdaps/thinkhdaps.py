#!/usr/bin/python
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

from awn.extras import awnlib

applet_name = "ThinkHDAPS"
applet_version = "0.3.1"
applet_description = "Applet that shows the shock protection status of your disks"

# Interval in milliseconds between two successive status checks
check_status_interval = 100

sysfs_dir = "/sys/block"
pm_file = "queue/protect_method"

hdaps_short_description = "protected from shocks"

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

    __hdaps_device = None

    __was_paused = False
    __error_occurred = False

    def check_status_cb(self, this):
        """Check the status the hard disk monitored by HDAPS and change
        the applet's icon if necessary,

        """
        try:
            paused = int(open("/sys/block/" + self.__hdaps_device + "/queue/protect").readline())

            # Change icon if status has changed
            if paused != self.__was_paused or self.__error_occurred:
                if paused:
                    self.applet.icon.set(self.icon_paused, True)
                else:
                    self.applet.icon.set(self.icon_running, True)

            if self.__error_occurred:
                self.__error_occurred = False
                self.applet.title.set(self.__hdaps_device + " " + hdaps_short_description)

            self.__was_paused = paused
        except IOError:
            if not self.__error_occurred:
                self.__error_occurred = True

                self.set_error_icon()
                self.applet.title.set(self.__hdaps_device + " not " + hdaps_short_description)

        return True

    def __init__(self, applet):
        self.applet = applet

        self.setup_icon()

        applet.icon.set(self.icon_running, True)

        def can_unload(disk):
            file = os.path.join(sysfs_dir, disk, pm_file)
            return os.path.isfile(file) and "[unload]" in open(file).read()
        disks = [disk for disk in os.listdir(sysfs_dir) if can_unload(disk)]

        if len(disks) > 0:
            self.__hdaps_device = disks[0]

        applet.connect("height-changed", self.height_changed_cb)

        if self.__hdaps_device is not None:
            applet.title.set(self.__hdaps_device + " " + hdaps_short_description)
            gobject.timeout_add(check_status_interval, self.check_status_cb, self)
        else:
            self.set_error_icon()
            self.applet.title.set("No hard disk found")

    def height_changed_cb(self, widget, event):
        """Update the applet's icon, because the height of the panel
        has changed.

        """
        self.setup_icon()

        # Toggle the flag to the wrong state to trigger the update of the icon
        self.__error_occurred = not self.__error_occurred

        # Check the status to update the applet's icon
        self.check_status_cb(self)

    def setup_icon(self):
        """Load the images that are going to be used as the applet's icon.

        """
        height = self.applet.get_height()
        self.icon_running = gdk.pixbuf_new_from_file_at_size(file_icon_running, height, height)
        self.icon_paused = gdk.pixbuf_new_from_file_at_size(file_icon_paused, height, height)

    def set_error_icon(self):
        height = self.applet.get_height()
        icon_error = gdk.pixbuf_new_from_file_at_size(file_icon_error, height, height)

        self.applet.icon.set(icon_error, True)


if __name__ == "__main__":
    awnlib.init_start(ThinkHDAPSApplet, {"name": applet_name,
        "short": "hdaps",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": 2008,
        "authors": ["onox"],
        "artists": ["Jakub Steiner", "Lapo Calamandrei", "Rodney Dawes", "Garrett LeSage", "onox"]})
