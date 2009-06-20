#!/usr/bin/python
# Copyright (C) 2008 - 2009  onox <denkpadje@gmail.com>
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

import operator
import os
import platform

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib
from awn import OverlayThemedIcon

try:
    from pyinotify import WatchManager, ThreadedNotifier, EventsCodes
    pyinotify = True
except ImportError:
    pyinotify = None

applet_name = "ThinkHDAPS"
applet_version = "0.3.3"
applet_description = "Applet that shows the shock protection status of your disks"

# Interval in seconds between two successive status checks
check_status_interval = 0.1

hdaps_short_description = "protected from shocks"

# Logo of the applet, shown in the GTK+ About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "images/thinkhdaps-logo.svg")


def compare_linux_version(wanted_version, op):
    assert callable(op)

    version = map(int, platform.release().split("-")[0].split("."))
    return all(map(lambda i: op(*i), zip(version, wanted_version)))


version_ge_2_6_28 = compare_linux_version([2, 6, 28], operator.ge)

sysfs_dir = "/sys/block"

if version_ge_2_6_28:
    protect_file = "device/unload_heads"
else:
    method_file = "queue/protect_method"
    protect_file = "queue/protect"

notifier = None


class ThinkHDAPSApplet:

    """Applet that shows the status of HDAPS.

    """

    __hdaps_device = None

    __was_paused = False
    __error_occurred = False

    def check_status_cb(self):
        """Check the status the hard disk monitored by HDAPS and change
        the applet's icon if necessary,

        """
        try:
            paused = bool(int(open(self.__status_file).readline()))

            # Change icon if status has changed
            if paused != self.__was_paused or self.__error_occurred:
                self.icon_paused.props.active = paused
                self.icon_running.props.active = not paused
                self.applet.get_icon().queue_draw()

            if self.__error_occurred:
                self.__error_occurred = False
                self.applet.tooltip.set(self.__hdaps_device + " " + hdaps_short_description)

            self.__was_paused = paused
        except IOError:
            if not self.__error_occurred:
                self.__error_occurred = True

                self.set_error_icon()
                self.applet.tooltip.set(self.__hdaps_device + " not " + hdaps_short_description)

    def __init__(self, applet):
        self.applet = applet

        applet.tooltip.disable_toggle_on_click()
        applet.icon.theme("harddrive")

        if version_ge_2_6_28:
            def can_unload(disk):
                file = os.path.join(sysfs_dir, disk, protect_file)
                if not os.path.isfile(file):
                    return False
                try:
                    open(file).read()
                    return True
                except IOError:
                    return False
        else:
            def can_unload(disk):
                file = os.path.join(sysfs_dir, disk, method_file)
                return os.path.isfile(file) and "[unload]" in open(file).read()
        disks = [disk for disk in os.listdir(sysfs_dir) if can_unload(disk)]

        if len(disks) > 0:
            self.__hdaps_device = disks[0]

        icon = applet.get_icon()

        self.icon_running = OverlayThemedIcon(icon, "thinkhdaps-running", "running")
        self.icon_running.props.scale = 0.6

        self.icon_paused = OverlayThemedIcon(icon, "thinkhdaps-paused", "paused")
        self.icon_paused.props.scale = 0.5

        self.icon_error = OverlayThemedIcon(icon, "dialog-error", "error")
        self.icon_error.props.scale = 0.6

        for overlay in (self.icon_running, self.icon_paused, self.icon_error):
            overlay.props.gravity = gtk.gdk.GRAVITY_NORTH_WEST
            overlay.props.active = False
            applet.add_overlay(overlay)

        if self.__hdaps_device is not None:
            self.icon_running.props.active = True

            self.__status_file = os.path.join(sysfs_dir, self.__hdaps_device, protect_file)

            applet.tooltip.set(self.__hdaps_device + " " + hdaps_short_description)

            if not self.setup_inotify():
                applet.timing.register(self.check_status_cb, check_status_interval)
        else:
            self.set_error_icon()
            applet.tooltip.set("No hard disk found")

    def setup_inotify(self):
        if pyinotify is None:
            return False

        watch_manager = WatchManager()

        result = watch_manager.add_watch(self.__status_file, EventsCodes.IN_MODIFY)[self.__status_file] > 0

        if result:
            global notifier
            notifier = ThreadedNotifier(watch_manager, lambda e: self.check_status_cb())
            notifier.start()
        return result

    def set_error_icon(self):
        self.icon_paused.props.active = False
        self.icon_running.props.active = False
        self.icon_error.props.active = True
        self.applet.get_icon().queue_draw()


if __name__ == "__main__":
    awnlib.init_start(ThinkHDAPSApplet, {"name": applet_name,
        "short": "thinkhdaps",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": "2008 - 2009",
        "authors": ["onox <denkpadje@gmail.com>"],
        "artists": ["Jakub Steiner", "Lapo Calamandrei", "Rodney Dawes", "Garrett LeSage", "onox"]})

    if isinstance(notifier, ThreadedNotifier):
        notifier.stop()
