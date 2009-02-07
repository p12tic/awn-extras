#!/usr/bin/python
# awndbus applet for AWN Version 1.0
#
# Copyright 2008 Julien Lavergne <julien.lavergne@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

import os

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib

try:
    import dbus
except ImportError:
    dbus = None

applet_name = "Tomboy Applet"
applet_version = "0.3.1"
applet_description = "Control Tomboy with D-Bus"

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "icons", "tomboy.png")

bus_name = "org.gnome.Tomboy"
object_name = "/org/gnome/Tomboy/RemoteControl"
if_name = "org.gnome.Tomboy.RemoteControl"


class TomboyApplet:

    __interface = None

    def __init__(self, awnlib):
        self.awn = awnlib

        awnlib.icon.file(applet_logo)
        awnlib.title.set("Tomboy Applet")

        if dbus is not None:
            try:
                bus = dbus.SessionBus()
                if bus_name in bus.list_names():
                    object = bus.get_object(bus_name, object_name)
                    self.__interface = dbus.Interface(object, if_name)
                    self.__version = self.__interface.Version()
            except dbus.DBusException, e:
                print e.message

        if self.__interface is not None:
            self.MainDialog()
        else:
            awnlib.errors.general("Could not connect to Tomboy")

    def DisplaySearch(self, widget, data=None):
        self.__interface.DisplaySearch()

    def ListAllNotes(self):
        return self.__interface.ListAllNotes()

    def DisplayNote(self, uri=None):
        self.__interface.DisplayNote(uri)

    def ButtonDisplay(self, widget, label):
        self.DisplayNote(label)

    def CreateNote(self, data=None):
        self.DisplayNote(self.__interface.CreateNote())

    def MainDialog(self):
        dialog = self.awn.dialog.new("main")

        for s in self.ListAllNotes()[:10]:
            self.button = gtk.Button(self.__interface.GetNoteTitle(s))
            self.button.connect("clicked", self.ButtonDisplay, s)
            dialog.add(self.button)

        dialog.add(gtk.Label("Version : " + self.__version))

        button1 = gtk.Button("Search")
        button1.connect("clicked", self.DisplaySearch)
        dialog.add(button1)

        button2 = gtk.Button("New Note")
        button2.connect("clicked", self.CreateNote)
        dialog.add(button2)


if __name__ == "__main__":
    awnlib.init_start(TomboyApplet, {"name": applet_name, "short": "tomboy",
        "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "Julien Lavergne",
        "copyright-year": 2008,
        "authors": ["Julien Lavergne <julien.lavergne@gmail.com>", "onox <denkpadje@gmail.com>"]})
