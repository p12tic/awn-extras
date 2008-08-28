#!/usr/bin/python
#
#       menu.py Version 0.5
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
import gtk
import os
from getlist import GetList
import gobject
class Menu(gtk.Menu) :
	def __init__(self, switcher, config) :
		self.switcher = switcher
		gtk.Menu.__init__(self)
		self.config = config
		self.createMenu()
		# Set up our Popup Menu
	def createMenu(self, half=False) :
		folder = self.config.get_folder()
		play = self.config.get_play()
		self.foreach(self.remove)
		refresh_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_REFRESH)
		# First add the default AWN menu
		defaultmenu = self.switcher.create_default_menu()
		items = defaultmenu.get_children()
		for item in items :
			defaultmenu.remove(item)
			self.append(item)
		# Set up our Radio Buttons for selecting which folder to use
		if (half != True) :
			try :
				self.All = RadioMenuItemFixed(None, "Base Folder")
				activated = 0
				if (self.config.get_sub_folder() == "") :
					self.All.set_active(True)
					activated = 1
				self.All.connect("toggled",self.changeDir)
				Allgroup = self.All.get_group()
				folderscount = 0
				self.folders = gtk.MenuItem("Subfolders")
				folderssubmenu = gtk.Menu()
				self.folders.set_submenu(folderssubmenu)
				menutree = {"":folderssubmenu}
				itemtree = {"":self.folders}
				for root, dirs, files in os.walk(folder) :
					root = root.partition(folder)[2]
					if (root != "" and len(dirs) != 0) :
						tempmenu = gtk.Menu()
						itemtree[root].set_submenu(tempmenu)
						menutree[root] = tempmenu
					for dir in dirs :
						temp = RadioMenuItemFixed(Allgroup, dir)
						menutree[root].append(temp)
						itemtree[root+"/"+dir] = temp
						temp.connect("toggled",self.changeDir, root+"/"+dir)
						if (root+"/"+dir == self.config.get_sub_folder()) :
							temp.set_active(True)
							activated = 1
						folderscount += 1
			except OSError:
				error = extras.notify_message("Error","A problem occured when trying to read the selected directory.", "desktop",15000,True)
				self.All = gtk.MenuItem("Could not read directory")
				self.All.set_sensitive(False)
			else :
				if (folderscount == 0) :
					nofolders = gtk.MenuItem("No Subfolders")
					nofolders.set_sensitive(False)
					self.append(nofolders)
				else :
					self.append(self.folders)
				if (activated == 0) :
					self.All.set_active(True)
		else :
			self.append(self.folders)
		self.append(self.All)
		sep = gtk.SeparatorMenuItem()
		self.append(sep)
		# Setup the menu for selecting the image manually if in manual mode
		if (self.config.get_method() == "Manual") :
			try :
				imagesgroup = gtk.RadioButton(None,None)
				imagescount = 0
				images = gtk.MenuItem("Images")
				imagessubmenu = gtk.Menu()
				images.set_submenu(imagessubmenu)
				root = folder+self.config.get_sub_folder()
				files = os.listdir(root)
				for file in files :
					fil = root+"/"+file
					ext = fil.split('.')
					ext = ext[len(ext)-1]
					if (ext != "jpg" and ext != "png" and ext != "jpeg") :
						continue
					else :
						temp = RadioMenuItemFixed(imagesgroup, file)
						temp.connect("toggled",self.changeImage, root+"/"+file)
						imagessubmenu.append(temp)
						if (root+"/"+file == self.config.get_desktop()) :
							temp.set_active(True)
						imagescount += 1
			except OSError:
				error = extras.notify_message("Error","A problem occured when trying to read the selected directory.", "desktop",15000,True)
				images = gtk.MenuItem("Could not read directory")
				images.set_sensitive(False)
			else :
				if (imagescount == 0) :
					noimages = gtk.MenuItem("No Images")
					noimages.set_sensitive(False)
					self.append(noimages)
				else :
					self.append(images)
				sep2 = gtk.SeparatorMenuItem()
				self.append(sep2)
		# The rest of the Menu's Items
		self.append(refresh_item)
		prefs_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
		self.append(prefs_item)
		about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
		self.append(about_item)
		if (self.config.get_method() == "Random") :
			play_toggle = gtk.CheckMenuItem("Cycle Desktop", False)
			play_toggle.set_active(play)
			self.append(play_toggle)
			play_toggle.connect("toggled", self.switcher.toggle_timeout)
		refresh_item.connect("activate",self.switcher.refresh)
		prefs_item.connect("activate",self.switcher.preferences)
		about_item.connect("activate", self.switcher.aboutDialog)
	def popup(self,parent_menu_shell, parent_menu_item, func, button, activate_time, data=None) :
		self.show_all()
		gtk.Menu.popup(self,parent_menu_shell, parent_menu_item, func, button, activate_time, data)
	def changeDir(self, widget, active, dir="") :
		self.hide()
		self.config.set_sub_folder(dir)
		self.switcher.getter.kill()
		self.switcher.getter = GetList(self.config,self.switcher)
		self.switcher.getter.start()
		self.createMenu()
	def changeImage(self,widget,active,image) :
		self.config.set_desktop(image)
		self.switcher.make_icon()
# Yeah, this is really hacky, but it works!
class RadioMenuItemFixed(gtk.ImageMenuItem) :
	__gsignals__ = {
		'toggled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_BOOLEAN,))
	}
	def __init__(self,group=None, label=None) :
		self.__gobject_init__()
		gtk.MenuItem.__init__(self)
		self.radio = gtk.RadioButton(group,None)
		self.set_image(self.radio)
		label = gtk.Label(label)
		label.set_alignment(0,.5)
		self.add(label)
		self.connect("button-press-event", self.toggle)
	def set_active(self, active) :
		self.radio.set_active(active)
	def get_active(self) :
		return self.radio.get_active()
	def get_group(self) :
		return self.radio
	def toggle(self, widget, event) :
		if (event.button == 1) :
			if (self.get_active() == False) :
				self.radio.set_active(True)
			else :
				self.radio.set_active(False)
			self.emit("toggled", self.get_active())
