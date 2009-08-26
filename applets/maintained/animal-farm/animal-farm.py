#!/usr/bin/env python
# Copyright (c) 2008  Arvind Ganga
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

import os
import subprocess
import sys

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib
import random

applet_name = "Animal Farm"
applet_version = "0.3.3"
applet_description = "Applet that displays fortune messages"

images_dir = os.path.join(os.path.dirname(__file__), "icons")

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(images_dir, 'lemmling-cartoon-gnu.svg')

command = "fortune"


class AnimalFarmApplet:

    """Applet that displays fortune messages.

    """

    def __init__(self, applet):
        self.applet = applet

        self.iconname = self.previous_iconname = None
        self.set_icon()

        self.setup_main_dialog()

        applet.connect_size_changed(self.refresh_icon)

    def setup_main_dialog(self):
        self.dialog = self.applet.dialog.new("fortune-dialog")

        alignment = gtk.Alignment()
        padding = 6
        alignment.set_padding(padding, padding, padding, padding)
        self.dialog.add(alignment)

        self.label = gtk.Label()
        alignment.add(self.label)
        self.refresh_fortune()

        self.applet.connect("clicked", self.clicked_cb)
        self.applet.connect("button-release-event", self.button_release_event_cb)
        self.dialog.connect("focus-out-event", self.dialog_focus_out_cb)

    def clicked_cb(self, widget):
        if self.dialog.is_active():
            self.set_icon()
            self.refresh_fortune()
        self.applet.dialog.toggle("fortune-dialog")

    def button_release_event_cb(self, widget, event):
        if event.button == 2:
            self.refresh_fortune()
            if not self.dialog.is_active():
                self.applet.dialog.toggle("fortune-dialog", "show")

    def dialog_focus_out_cb(self, dialog, event):
        self.set_icon()
        self.refresh_fortune()

    def set_icon(self):
        files = [i for i in os.listdir(images_dir) if i.endswith('.svg') and i != self.iconname and i != self.previous_iconname]

        self.previous_iconname = self.iconname
        self.iconname = files[random.randint(0, len(files) - 1)]

        self.refresh_icon()

    def refresh_icon(self):
        self.applet.icon.file(os.path.join(images_dir, self.iconname), size=awnlib.Icon.APPLET_SIZE)

    def refresh_fortune(self):
        try:
            text = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
        except OSError:
            text = "Error executing \"" + command + "\"; make sure it is in your path and executable."
        self.label.set_text(text.rstrip())


if __name__ == "__main__":
    awnlib.init_start(AnimalFarmApplet, {"name": applet_name,
        "short": "animal-farm",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "Arvind Ganga",
        "copyright-year": 2008,
        "authors": ["Arvind Ganga", "onox <denkpadje@gmail.com>"]})
