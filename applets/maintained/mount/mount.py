#!/usr/bin/python
# Copyright (C) 2007  Arvind Ganga
#               2009 - 2010  onox <denkpadje@gmail.com>
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
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import os
import subprocess
import threading

import pygtk
pygtk.require('2.0')
import gtk

from awn.extras import _, awnlib, __version__

import glib

applet_name = _("Mount Applet")
applet_description = _("An applet to (un)mount devices")

ui_file = os.path.join(os.path.dirname(__file__), "mount.ui")
image_dir = os.path.join(os.path.dirname(__file__), "icons")

# Logo of the applet, shown in the GTK+ About dialog
applet_logo = os.path.join(image_dir, "mount.png")


class MountApplet:

    """An applet to (un)mount devices.

    """

    __mountpoints = {}

    def __init__(self, applet):
        self.applet = applet

        applet.icon.file(applet_logo, size=awnlib.Icon.APPLET_SIZE)

        self.setup_context_menu()
        self.setup_main_dialog()

        def clicked_cb(widget):
            self.refresh_dialog()
        applet.connect("clicked", clicked_cb)

    def setup_main_dialog(self):
        dialog = self.applet.dialog.new("main")

        self.__mountpoints_vbox = gtk.VBox(spacing=6)
        dialog.add(self.__mountpoints_vbox)

        self.init_dialog()

    def setup_context_menu(self):
        pref_dialog = self.applet.dialog.new("preferences")

        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)
        prefs.get_object("dialog-vbox").reparent(pref_dialog.vbox)

        binder = self.applet.settings.get_binder(prefs)
        binder.bind("execute-command", "entry-execute-command")
        self.applet.settings.load_bindings(binder)

        self.__entry_hidden_mountpoints = prefs.get_object("entry-hidden-mountpoints")
        self.__entry_hidden_mountpoints.set_text(" ".join(self.applet.settings["hidden-mountpoints"]))

        pref_dialog.connect("response", self.pref_dialog_response_cb)

    def pref_dialog_response_cb(self, widget, response):
        hidden_mountspoints = self.__entry_hidden_mountpoints.get_text().strip().split(" ")
        if self.applet.settings["hidden-mountpoints"] != hidden_mountspoints:
            self.applet.settings["hidden-mountpoints"] = hidden_mountspoints
            self.init_dialog()

    def init_dialog(self):
        for mountpoint in self.__mountpoints_vbox.get_children():
            self.__mountpoints_vbox.remove(mountpoint)

        for mountpoint in self.get_file_content("/etc/fstab"):
            if self.applet.settings["hidden-mountpoints"].count(mountpoint) > 0:
                continue

            button = gtk.Button(mountpoint)
            self.__mountpoints[mountpoint] = [None, button]
            button.connect("clicked", self.toggle_mount, mountpoint)

            self.__mountpoints_vbox.add(button)

        self.refresh_dialog()

    def refresh_dialog(self):
        mounts = self.get_file_content("/proc/mounts")

        for mountpoint, button_mounted in self.__mountpoints.iteritems():
            mounted = mounts.count(mountpoint) > 0
            button_mounted[0] = mounted

            stock_image = gtk.STOCK_APPLY if mounted else gtk.STOCK_CANCEL
            button_mounted[1].set_image(gtk.image_new_from_stock(stock_image, gtk.ICON_SIZE_BUTTON))

    def get_file_content(self, filename):
        fstab = []
        for line in open(filename, "r"):
            if not line.isspace() and not line.startswith("#") and not line.startswith("none"):
                fstab.append(line.split()[1])
        fstab.sort()
        return fstab

    def toggle_mount(self, widget, mountpoint):
        def run():
            if not self.__mountpoints[mountpoint][0]:
                fp = subprocess.Popen("mount " + mountpoint, shell=True)
                execute_command = self.applet.settings["execute-command"]
                if fp.wait() == 0 and len(execute_command) > 0:
                    command = execute_command.replace("%D", mountpoint)
                    print command
                    subprocess.Popen(command, shell=True)
            else:
                subprocess.Popen("umount " + mountpoint, shell=True).wait()
            glib.idle_add(self.refresh_dialog)
        threading.Thread(target=run).start()


if __name__ == "__main__":
    awnlib.init_start(MountApplet, {"name": applet_name,
        "short": "mount",
        "version": __version__,
        "description": applet_description,
        "logo": applet_logo,
        "author": "onox",
        "copyright-year": "2009 - 2010",
        "authors": ["Arvind Ganga", "onox <denkpadje@gmail.com>"]})
