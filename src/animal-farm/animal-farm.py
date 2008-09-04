#!/usr/bin/python

# Copyright (c) 2008 Arvind Ganga
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

import sys, os
import subprocess
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import random

class AnimalFarm(awn.AppletSimple):
	command = "fortune"

	def __init__ (self, uid, orient, height):
		awn.AppletSimple.__init__ (self, uid, orient, height)
		self.height = height
		self.iconname = ""
		self.previous_iconname = ""
		self.set_icon()
		self.title = awn.awn_title_get_default ()

		self.dialog = awn.AppletDialog (self)
		self.initialize_dialog()
		self.initialize_about_box()

		self.connect ("button-press-event", self.button_press)
		self.connect ("enter-notify-event", self.enter_notify)
		self.connect ("leave-notify-event", self.leave_notify)
		self.dialog.connect ("focus-out-event", self.dialog_focus_out)

	def initialize_about_box(self):
		# Context Menu
		self.context = self.create_default_menu()
		context_item = gtk.ImageMenuItem("gtk-about")
		self.context.append(context_item)
		context_item.show()
		context_item.connect("activate", self.context_response, "about")

	        # Context About dialog
        	self.context_about = awn.AppletDialog(self)
		context_box = gtk.VBox(False, 0)
		self.context_about.add(context_box)
		context_box.show()
		context_title = gtk.Label("")
		context_box.add(context_title)
		context_title.show()
		context_text = '<span size="large" weight="bold">Animal Farm Applet</span>\n\n<span size="medium" weight="bold">(c) 2008 Arvind Ganga</span>\n'
		context_title.set_use_markup(True)
		context_title.set_markup(context_text)
		context_title.set_justify(gtk.JUSTIFY_CENTER)
	        context_button = gtk.Button(stock="gtk-ok")
	        context_box.add(context_button)
	        context_button.show_all()
		context_button.connect("button-press-event", self.context_about_ok)
		self.context_about.connect("focus-out-event", self.context_about_ok)

	def context_about_ok(self, widget, event):
		self.context_about.hide()

	def context_response(self, widget, string):
		if string == "about":
			self.context_about.show_all()


	def set_icon(self):
		files = os.listdir(os.path.dirname (__file__) + '/icons/')

		if self.iconname is not "":
			files.remove(self.iconname)
		if self.previous_iconname is not "":
			files.remove(self.previous_iconname)
		self.previous_iconname = self.iconname
		while True:
			self.iconname = files[random.randint(0, len(files) - 1)]
			if self.iconname.endswith('.png'):
				break

		icon = gdk.pixbuf_new_from_file(os.path.dirname (__file__) + '/icons/' + self.iconname)
		if self.height != icon.get_height():
			icon = icon.scale_simple(self.height, self.height, gtk.gdk.INTERP_BILINEAR)
		self.set_temp_icon (icon)


	def button_press (self, widget, event):
		if event.button == 3:
			self.context.popup(None, None, None, event.button, event.time)
			return
		if event.button == 2:
			if self.showing_dialog:
				self.refresh_dialog()
			else:
				self.show_dialog()
		elif self.showing_dialog:
			self.hide_dialog()
		else:
			self.show_dialog()


	def show_dialog(self):
		self.label.set_text(self.get_display_string())
		self.dialog.show_all ()
		self.title.hide (self)
		self.showing_dialog = True


	def hide_dialog(self):
		self.showing_dialog = False
		self.dialog.hide()
		self.set_icon()


	def refresh_dialog(self):
		self.showing_dialog = True
		self.label.set_text(self.get_display_string())
		self.dialog.show_all ()
		self.title.hide (self)


	def initialize_dialog(self):
		self.label = gtk.Label(self.get_display_string())
		self.label.show()
		self.dialog.add (self.label)
		self.showing_dialog = False


	def get_display_string(self):
		try:
			return subprocess.Popen(self.command, stdout=subprocess.PIPE).communicate()[0]
		except OSError:
			return "Error executing \"" + self.command + "\"; make sure it is in your path and executable."


	def dialog_focus_out (self, widget, event):
		self.hide_dialog()

	def enter_notify (self, widget, event):
		self.title.show (self, "Animal Farm")


	def leave_notify (self, widget, event):
		self.title.hide (self)


if __name__ == "__main__":
	awn.init (sys.argv[1:])
	applet = AnimalFarm(awn.uid, awn.orient, awn.height)
	awn.init_applet (applet)
	applet.show_all ()
	gtk.main ()

