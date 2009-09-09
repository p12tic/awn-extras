#!/usr/bin/python
# Copyright (C) 2008 - 2009  Julien Lavergne <julien.lavergne@gmail.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import threading

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib, __version__

try:
    import dbus
except ImportError:
    dbus = None

applet_name = "Tomboy Applet"
applet_description = "Control Tomboy with D-Bus"
applet_system_notebook = "system:notebook:"
applet_system_template = "system:template"

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "icons", "tomboy.png")

bus_name = "org.gnome.Tomboy"
object_name = "/org/gnome/Tomboy/RemoteControl"
if_name = "org.gnome.Tomboy.RemoteControl"


class TomboyApplet:

    __interface = None
    tags = None

    def __init__(self, awnlib):
        self.awn = awnlib

        awnlib.icon.file(applet_logo)

        if dbus is not None:
            def run_tomboy():
                try:
                    bus = dbus.SessionBus()
                    if bus_name not in bus.list_names():
                        bus.start_service_by_name(bus_name)
                    self.connect(bus)
                except dbus.DBusException, e:
                    awnlib.errors.general("Could not connect to Tomboy: %s" % e)
            threading.Thread(target=run_tomboy).start()

    def connect(self, bus):
        object = bus.get_object(bus_name, object_name)
        self.__interface = dbus.Interface(object, if_name)
        self.__version = self.__interface.Version()
        if self.__interface is not None:
            self.main_dialog()

    def display_search(self, widget):
        self.__interface.DisplaySearch()

    def list_all_notes(self):
        return self.__interface.ListAllNotes()

    def display_note(self, uri=None):
        self.__interface.DisplayNote(uri)

    def button_display(self, widget, label):
        self.display_note(label)

    def create_note(self, widget):
        self.display_note(self.__interface.CreateNote())

    def create_from_tag(self, widget, tag):
        note = self.__interface.CreateNote()
        self.__interface.AddTagToNote(note, applet_system_notebook + tag)
        self.display_note(note)

    def collect_tags(self):
        if self.tags is None:
            self.tags = []
            for s in self.list_all_notes():
                for tag in self.__interface.GetTagsForNote(s):
                    if tag.startswith(applet_system_notebook):
                        atag = tag[len(applet_system_notebook):]
                        if atag not in self.tags:
                            self.tags.append(atag)
            self.tags.sort()
        return self.tags

    def create_from_tag_dialog(self, widget):
        dialog = self.awn.dialog.new("create_from_tag")
        dialog.add(gtk.Label("Select a tag:"))
        for tag in self.collect_tags():
            button = gtk.Button(tag)
            button.connect("clicked", self.create_from_tag, tag)
            dialog.add(button)
        dialog.show_all()

    def view_from_tag(self, widget, tag):
        dialog = self.awn.dialog.new("view_from_tag")
        dialog.add(gtk.Label("Select a note:"))

        for note in self.__interface.GetAllNotesWithTag(applet_system_notebook + tag):
            if applet_system_template not in self.__interface.GetTagsForNote(note):
                button = gtk.Button(self.__interface.GetNoteTitle(note))
                button.connect("clicked", self.button_display, note)
                dialog.add(button)
        dialog.show_all()

    def view_from_tag_dialog(self, widget):
        dialog = self.awn.dialog.new("view_from_tag_select")
        dialog.add(gtk.Label("Select a tag:"))
        for tag in self.collect_tags():
            button = gtk.Button(tag)
            button.connect("clicked", self.view_from_tag, tag)
            dialog.add(button)
        dialog.show_all()

    def main_dialog(self):
        dialog = self.awn.dialog.new("main")

        for note in self.list_all_notes()[:10]:
            self.button = gtk.Button(self.__interface.GetNoteTitle(note))
            self.button.connect("clicked", self.button_display, note)
            dialog.add(self.button)

        dialog.add(gtk.Label("Version : " + self.__version))

        button1 = gtk.Button("Search")
        button1.connect("clicked", self.display_search)
        dialog.add(button1)

        button2 = gtk.Button("New Note")
        button2.connect("clicked", self.create_note)
        dialog.add(button2)

        button3 = gtk.Button("New Tagged Note")
        button3.connect("clicked", self.create_from_tag_dialog)
        dialog.add(button3)

        button4 = gtk.Button("View Tagged Note")
        button4.connect("clicked", self.view_from_tag_dialog)
        dialog.add(button4)


if __name__ == "__main__":
    awnlib.init_start(TomboyApplet, {"name": applet_name, "short": "tomboy",
        "version": __version__,
        "description": applet_description,
        "logo": applet_logo,
        "author": "Julien Lavergne",
        "copyright-year": "2008 - 2009",
        "authors": ["Julien Lavergne <julien.lavergne@gmail.com>",
                    "onox <denkpadje@gmail.com>",
                    "Hugues Casse <casse@irit.fr>"]})
