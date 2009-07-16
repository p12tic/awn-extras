#!/usr/bin/python
#
#       Manager.py Version 0.5
#
#       Copyright 2008 Allan Wirth <allanlw@gmail.com>
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

import sys
import random
import gobject
import gtk
import awn
import wnck
check_dependencies(globals(), 'pynotify')

from config import ConfigManager
from getlist import GetList
from configdialog import ConfigDialog
from menu import Menu
class DesktopManager(awn.AppletSimple):
	def __init__(self, uid, orient, height):
	        # Initiate Applet
	        awn.AppletSimple.__init__(self, uid, orient, height)
	        self.height = height
	        self.theme = gtk.icon_theme_get_default()

		self.config_manager = ConfigManager()
		self.make_icon()

	        # Get our title ready
	        self.title = awn.awn_title_get_default()
		self.titleLabel = "DesktopManager"
		# Create the popup menu
		self.popup_menu = Menu(self, self.config_manager)
		# Generate the preliminary list
		self.getter = GetList(self.config_manager,self)
		self.getter.start()
		# Update the desktop every so often
		if (self.config_manager.get_play() == True and self.config_manager.get_method() == "Random") :
			self.timeout = gobject.timeout_add(self.config_manager.get_secs(),self.refresh)
		else :
			self.timeout = False
		# Connect Our Events
	        self.connect("button-press-event", self.button_press)
	        self.connect("enter-notify-event", self.enter_notify)
	        self.connect("leave-notify-event", self.leave_notify)
	def set_files(self, files) :
		self.files = files
	def make_icon(self) :
		if (self.config_manager.get_desktop() != None) :
			try :
				pixbuf = gtk.gdk.pixbuf_new_from_file(self.config_manager.get_desktop())
				ratio = float(pixbuf.get_width())/float(pixbuf.get_height())
				pixbuf = pixbuf.scale_simple(int(self.height*ratio*(self.config_manager.get_scale()/float(100))),int(float(self.height)*(self.config_manager.get_scale()/float(100))),gtk.gdk.INTERP_BILINEAR)
			except gobject.GError:
				pixbuf = self.theme.load_icon("desktop", int(self.height*(self.config_manager.get_scale()/100)), 0)
		else :
			pixbuf = self.theme.load_icon("desktop", int(self.height*(self.config_manager.get_scale()/100)), 0)
		self.set_icon(pixbuf)
	def preferences(self, widget) :
		self.config = ConfigDialog(self, self.config_manager)
		self.config.show()
	def toggle_timeout(self, widget):
		if (self.timeout == False) :
			self.timeout = gobject.timeout_add(self.config_manager.get_secs(),self.refresh)
			self.config_manager.set_play(True)
		else :
			gobject.source_remove(self.timeout)
			self.timeout = False
			self.config_manager.set_play(False)
	def button_press(self, widget, event):
		if (event.button == 3) :
			self.title.hide(self)
			self.popup_menu.popup(None, None, None, event.button, event.time)
		elif (event.button == 2 or event.button == 1) :
			if (self.config_manager.get_button_action(event.button) == "Show Desktop") :
				self.show_desktop()
			elif (self.config_manager.get_button_action(event.button) == "Switch Desktop Image") :
				self.refresh()
			elif (self.config_manager.get_button_action(event.button) == "None") :
				pass
	def show_desktop(self) :
		screen = wnck.screen_get_default()
            	if (self.config_manager.get_show_desktop() == "Toggle showing the desktop") :
			showing_windows = not screen.get_showing_desktop()
			screen.toggle_showing_desktop(showing_windows)
		elif (self.config_manager.get_show_desktop() == "Just show the desktop") :
			screen.toggle_showing_desktop(True)
	def refresh(self, widget=None):
		if (self.config_manager.get_method() == "Random") :
			try :
				currentfile = random.sample(self.files, 1)[0]
			except (ValueError, AttributeError) :
				pynotify.init('DesktopManager')
				notification = pynotify.Notification("DesktopManager Error",
								     "Either there are no images in the selected folder, or DesktopManager has not had enough time to scan the folder yet.",
								     "desktop")
				notification.set_timeout(5000)
				notification.show()
				pynotify.uninit()
				return False
			if (self.config_manager.get_attention() == True) :
				awn.awn_effect_start_ex(self.get_effects(), "attention", 0, 0, 1)
			self.config_manager.set_desktop(currentfile)
			self.make_icon()
			return True
		elif (self.config_manager.get_method() == "Manual") :
			self.config_manager.set_desktop(self.config_manager.get_desktop())
			self.make_icon()
	def enter_notify(self, widget, event):
	        self.title.show(self, self.titleLabel)
	def leave_notify(self, widget, event):
	        self.title.hide(self)
	def updateConfig(self) :
		self.getter.kill()
		self.popup_menu.createMenu()
		self.getter = GetList(self.config_manager,self)
		self.getter.start()
		self.make_icon()
		if (self.timeout != False) :
			gobject.source_remove(self.timeout)
			self.timeout = False
		if (self.config_manager.get_play() == True and self.config_manager.get_method() == "Random") :
			self.timeout = gobject.timeout_add(self.config_manager.get_secs(),self.refresh)
	def aboutDialog(self, widget) :
		about = gtk.AboutDialog()
		about.set_name("DesktopManager")
		about.set_comments("Helps you manager your desktop wallpaper.")
		about.set_authors(["Allan Wirth <allanlw@gmail.com>"])
		about.set_copyright("Copyright 2008 Allan Wirth <allanlw@gmail.com>")
		about.set_license("""
This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
		""")
		about.set_wrap_license(True)
		about.set_logo(self.theme.load_icon("desktop", 150, 0))
		pixbuf = self.theme.load_icon("desktop", 64, 0)
		about.set_icon(pixbuf)
		about.show()
		about.connect("response", self.aboutResponse)
	def aboutResponse(self, widget, response) :
		widget.destroy()
if __name__ == "__main__":
    awn.init(sys.argv[1:])
    applet = DesktopManager(awn.uid, awn.orient, awn.height)
    awn.init_applet(applet)
    applet.show_all()
    gtk.main()
