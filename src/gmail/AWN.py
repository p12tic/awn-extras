#!/usr/bin/python
#
#       AWN Applet Library
#
#       Copyright 2007 Pavel Panchekha <pavpanchekha@gmail.com>
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

import sys, os
import gobject
import gtk
from gtk import gdk
import awn
import time
import re

class Dialogs:
	def __init__(self, parent, mainDlog=None, secDlog=None, program=None, context=None):
		self.main = mainDlog
		self.secondary = secDlog
		self.program = program
		self.menu = context
		self.parent = parent

	def register(self, dlog, type="main"):
		assert type in ["main", "secondary", "program", "menu"]
		self.__dict__[type] = dlog
		dlog.connect("focus-out-event", lambda x, y: dlog.hide())

	def toggle(self, w=None, e=None):
		if e.button == 3: # right click
			self.__context(w, e)
		elif e.button == 2: # middle click
			self.__secondary(w, e)
		else:
			self.__main(w, e) # other, including single click

	def new(self, type=None):
		dlog = awn.AppletDialog(self.parent)
		if type != None:
			self.register(dlog, type)
		return dlog

	def __main(self, w=None, e=None):
		if self.main.is_active():
			self.main.hide()
		else:
			self.main.show_all()

	def __secondary(self, w=None, e=None):
		if self.secondary:
			if self.secondary.is_active():
				self.secondary.hide()
			else:
				self.secondary.show_all()
		else:
			self.program()

	def __context(self, w=None, e=None):
		self.context.popup(None, None, None, e.button, e.time)

class Title:
	def __init__(self, parent, text=""):
		self.__title = awn.awn_title_get_default()
		self.parent = parent
		self.text = text

	def show(self, x=None, y=None, show=True):
		def f(text):
			if show:
				self.__title.show(self.parent, text)
			else:
				self.__title.hide(self.parent)

		f(self.text)

	def set(self, text=""):
		self.text = text

class Icon:
	def __init__(self, parent):
		self.parent = parent
		self.height = self.parent.height

	def getFile(self, file):
		return gdk.pixbuf_new_from_file(os.path.join(os.path.abspath( \
			os.path.dirname(__file__)), file))

	def getTheme(self, name):
		self.theme = gtk.IconTheme()
		return self.theme.load_icon (name, self.height, 0)


	def set(self, icon):
		if self.height != icon.get_height():
			icon = icon.scale_simple(self.height, \
				self.height, gtk.gdk.INTERP_BILINEAR)
		self.parent.set_temp_icon(icon)

class Modules:
	def __init__(self, parent):
		self.parent = parent

	def get(self, name):
		try:
			module = __import__(name)
		except ImportError:
			return False
		else:
			return module

	def visual(self, name, packagelist, callback):
		module = self.get(name)
		if module:
			return callback(module)

		self.parent.dialog.new("main")

		# Table based layout
		table = gtk.Table()
		dlog.add(table)
		table.resize(3, 1)
		table.show_all()

		# Title of Window
		title = gtk.Label("<b>Error in Applet:</b>")
		table.attach(title, 0, 1, 0, 1)
		title.set_use_markup(True)
		title.show_all()

		error = "You must have the python module <i>%s</i> installed to use the Gmail Applet. Make sure you do and click OK.\nHere is a list of distros and the package names for each:\n\n" % (name)
		for (k, v) in packagelist.items():
			error = "%s%s: <i>%s</i>\n" % (error, k, v)

		# Error Message
		text = gtk.Label(error)
		text.set_line_wrap(True)
		table.attach(text, 0, 1, 1, 2)
		text.set_use_markup(True)
		text.set_justify(gtk.JUSTIFY_FILL)
		text.show_all()

		# Submit button
		ok = gtk.Button(label = "OK, I've installed it")
		table.attach(ok, 0, 1, 2, 3)
		ok.show_all()

		def qu(x):
			dlog.hide()
			self.visual(name, packagelist)

		ok.connect("clicked", qu)
		dlog.show_all()

class App(awn.AppletSimple):
	def __init__(self, uid, orient, height):
		awn.AppletSimple.__init__(self, uid, orient, height)
		self.height = height

		self.icon = Icon(self)
		self.dialog = Dialogs(self)
		self.title = Title(self)
		self.module = Modules(self)

		self.connect("button-press-event", self.dialog.toggle)
		self.connect("enter-notify-event", self.title.show)
		self.connect("leave-notify-event", lambda x, y: self.title.show(show=False))

def initiate():
	awn.init(sys.argv[1:])
	applet = App(awn.uid, awn.orient, awn.height)
	awn.init_applet(applet)
	return applet

def start(applet):
	applet.show_all()
	gtk.main()
