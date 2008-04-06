#!/usr/bin/python
#
#       awndbus applet for AWN Version 1.0
#
#       Copyright 2008 Julien Lavergne <julien.lavergne@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

from awn.extras import AWNLib
import gobject
import gtk
from gtk import gdk
import dbus

bus = dbus.SessionBus()

interface = bus.get_object('org.gnome.Tomboy','/org/gnome/Tomboy/RemoteControl')
interface = dbus.Interface(interface,dbus_interface='org.gnome.Tomboy.RemoteControl')
version = interface.Version()

class TomboyApplet:
	def __init__(self, awnlib):
		self.awn=awnlib	
		self.awn.icon.set(applet.icon.getTheme("tomboy"))
		self.awn.title.set("Tomboy Applet")

	def DisplaySearch(self, widget, data=None):
		interface.DisplaySearch()

	def ListAllNotes(self):
		return interface.ListAllNotes()

	def ListAllTitles(self):
		titles =[]
		for s in self.ListAllNotes():
			titles.append(interface.GetNoteTitle(s))
		return titles

	def DisplayNote(self, uri=None):
		interface.DisplayNote(uri)

	def DicoNotes(self):
		d = {}
		for s in self.ListAllNotes():
			d [interface.GetNoteTitle(s)]= s
		return d

	def ButtonDisplay (self,widget,label):
		self.DisplayNote(label)

	def CreateNote(self, data=None):
		self.new = interface.CreateNote()
		self.DisplayNote(self.new)

	def MainDialog(self):
		self.dlog = applet.dialog.new("main")

		li = self.ListAllNotes()
		for s in li[:10]:
			self.button = gtk.Button(label=interface.GetNoteTitle(s))
			self.button.connect("clicked", self.ButtonDisplay, s)
			self.dlog.add(self.button)

		self.label1 = gtk.Label(str="Version : "+version)
		self.dlog.add(self.label1)

		self.button1 = gtk.Button(label="Search")
		self.button1.connect("clicked", self.DisplaySearch)
		self.dlog.add(self.button1)

		self.button2 = gtk.Button(label="New Note")
		self.button2.connect("clicked", self.CreateNote)
		self.dlog.add(self.button2)

applet = AWNLib.initiate({"name": "Tomboy Applet", "short": "tomboy applet"})
awntomboy = TomboyApplet(applet)
awntomboy.MainDialog()
AWNLib.start(applet)
