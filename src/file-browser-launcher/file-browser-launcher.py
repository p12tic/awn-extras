#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
#
# File Browser Launcher
# Main Applet File

import sys
import os
import pygtk
pygtk.require('2.0')
import gtk
import awn
import subprocess
import pango
import gconfwrapper

class App (awn.AppletSimple):
	def __init__(self, uid, orient, height):
		
		#AWN Applet Configuration
		awn.AppletSimple.__init__(self, uid, orient, height)
		self.title = awn.awn_title_get_default()
		self.dialog = awn.AppletDialog(self)
		
		#Has to do with GCONF
		self.client = gconfwrapper.GConfWrapper()
		
		#Get the icon theme default theme thing
		self.theme = gtk.icon_theme_get_default()
		
		#get the default icon path
		self.default_icon_path = '/'.join(__file__.split('/')[:-1])+'/folder.png'
		
		#Get the icon path, or default to /dev/null which will become the stock folder icon
		self.gconf_icon = self.client.get_string('/apps/avant-window-navigator/applets/file-browser-launcher/icon','default')
		try:
			if self.gconf_icon in ['/dev/null','','folder']:
				icon = self.theme.load_icon('folder',height,0)
			elif self.gconf_icon=='default':
				icon = gtk.gdk.pixbuf_new_from_file(self.default_icon_path)
			else:
				icon = gtk.gdk.pixbuf_new_from_file(self.gconf_icon)
			if height != icon.get_height():
				icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
			self.set_icon(icon)
		except:
			self.set_icon(gtk.gdk.pixbuf_new_from_file(self.default_icon_path))
		
		#Make the dialog, will only be shown when approiate
		#VBox for everything to go in
		self.vbox = gtk.VBox()
		#Make all the things needed for a treeview for the homefolder, root dir, bookmarks, and mounted drives
		self.liststore = gtk.ListStore(gtk.gdk.Pixbuf,str)
		self.treeview = gtk.TreeView(self.liststore)
		self.treeview.set_hover_selection(True)
		self.renderer0 = gtk.CellRendererPixbuf()
		self.renderer1 = gtk.CellRendererText()
		self.treeview.set_headers_visible(False)
		self.column0 = gtk.TreeViewColumn('0')
		self.column0.pack_start(self.renderer0,True)
		self.column0.add_attribute(self.renderer0,'pixbuf',0)
		self.column1 = gtk.TreeViewColumn('1')
		self.column1.pack_start(self.renderer1,True)
		self.column1.add_attribute(self.renderer1,'markup',1)
		self.treeview.append_column(self.column0)
		self.treeview.append_column(self.column1)
		self.treeview.connect('button-press-event',self.treeview_clicked)
		#self.treeview.connect('key-press-event',lambda a:pass)
		self.add_places()
		self.vbox.pack_start(self.treeview)
		
		#Entry widget for displaying the path to open
		self.entry = gtk.Entry()
		self.entry.set_text(os.path.expanduser('~'))
		self.entry.connect('key-release-event',self.detect_enter)
		#Open button to run the file browser
		self.enter = gtk.Button(stock=gtk.STOCK_OPEN)
		self.enter.connect('clicked',self.launch_fb)
		#HBox to put the two together
		self.hbox = gtk.HBox()
		self.hbox.pack_start(self.entry)
		self.hbox.pack_start(self.enter, False)
		#And add the HBox to the vbox and add the vbox to the dialog
		self.vbox.pack_start(self.hbox)
		self.dialog.add(self.vbox)
		
		#AWN applet signals
		self.connect('button-press-event', self.button_press)
		self.connect('enter-notify-event', lambda a,b: self.title.show(self,'File Browser Launcher'))
		self.connect('leave-notify-event', lambda a,b: self.title.hide(self))
		self.dialog.connect('focus-out-event', lambda a,b: self.dialog.hide())
	
	#Function to show the home folder, mounted drives/partitions, and bookmarks according to gconf
	#This also refreshes in case a CD was inserted, MP3 player unplugged, bookmark added, etc.
	def add_places(self):
		#This function adds items to the liststore. The TreeView was already made in __init__()
		
		#Empty the liststore if it isn't
		self.liststore.clear()
		self.places_paths = []
		
		#Get the needed GConf values
		self.show_home = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/places_home',2)
		self.show_local = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/places_local',2)
		self.show_network = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/places_network',2)
		self.show_bookmarks = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/places_bookmarks',2)
		
		#Now make the actual mounted items. First: Home Folder
		if self.show_home==2:
			self.icon_home = self.theme.load_icon('user-home',24,24)
			try:
				self.liststore.append([self.icon_home,'Home Folder'])
			except:
				self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
					.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Home Folder'])
			self.places_paths.append(os.path.expanduser('~'))
		
		#Get list of mounted drives from both $ mount and /etc/fstab AND the list of bookmarks
		self.mount2 = os.popen('mount')
		self.mount = self.mount2.readlines()
		self.mount2.close()
		self.fstab2 = open('/etc/fstab','r')
		self.fstab = self.fstab2.readlines()
		self.fstab2.close()
		self.bmarks2 = open(os.path.expanduser('~/.gtk-bookmarks'))
		self.bmarks = self.bmarks2.readlines()
		self.bmarks2.close()
		self.paths = []
		self.paths_fstab = []
		self.nfs_smb_paths = []
		self.nfs_smb_corr_hnames = []
		self.cd_paths = []
		self.dvd_paths = []
		
		#Get whether the trash is empty or not
		if len(os.listdir(os.path.expanduser('~/.Trash'))) > 2:
			self.trash_full = True
		else:
			self.trash_full = False
		
		#Get the mounted drives/partitions that are suitable to list (from fstab)
		z2 = []
		z3 = 0
		for x in self.fstab:
			if x[0]!="#":
				y = x.split(' ')
				for z in y[1:]:
					if z!='':
						if z[0]=='/':
							if z!='/proc':
								self.paths_fstab.append(z)
				for z in y:
					if z!='':
						z2.append(z)
		for x in z2:
			if x in ['smbfs','nfs']:
				self.nfs_smb_paths.append(z2[(z3-1)])
				self.nfs_smb_corr_hnames.append(z2[(z3-2)].replace('//',''))
			z3 = z3+1
				
		
		#Get the mounted drives/partitions that are suitable to list (from mount)
		for x in self.mount:
			y = x.split(' ')
			if y[0].find('/')!=-1:
				if y[0].split('/')[1]=='dev':
					self.paths.append(x.split(' on ')[1].split(' type ')[0])
					if x.split(' type ')[1].split(' ')[0]=='iso9660':
						self.cd_paths.append(x.split(' on ')[1].split(' type ')[0])
					elif x.split(' type ')[1].split(' ')[0]=='udf':
						self.dvd_paths.append(x.split(' on ')[1].split(' type ')[0])
				elif x.split(' on ')[1].split(' type ')[0] in self.nfs_smb_paths:
					self.paths.append(x.split(' on ')[1].split(' type ')[0])
		
		#Go through the list and get the right icon and name for specific ones
		#ie/eg: / -> harddisk icon and "Filesystem"
		#/media/Lexar -> usb-disk icon and "Lexar"
		if self.show_local==2:
			for x in self.paths:
				if x=='/':
					try:
						self.liststore.append([self.theme.load_icon('drive-harddisk',24,24),'Filesystem'])
					except:
						self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
							.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Filesystem'])
					self.places_paths.append(x)
				elif x.split('/')[1]=='media':
					if x.split('/')[2] in ['cdrom0','cdrom1','cdrom2','cdrom3','cdrom4','cdrom5']:
						#Find out if it's a CD or DVD
						if x in self.dvd_paths:
							try:
								self.liststore.append([self.theme.load_icon('media-optical',24,24),'DVD Drive'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'DVD Drive'])
							self.places_paths.append(x)
						else:
							try:
								self.liststore.append([self.theme.load_icon('media-optical',24,24),'CD Drive'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'CD Drive'])
							self.places_paths.append(x)
					elif x not in self.paths_fstab: #Means it's USB or firewire
						try:
							self.liststore.append([self.theme.load_icon('gnome-dev-harddisk-usb',24,24),x.split('/')[2].capitalize()])
						except:
							self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
								.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),x.split('/')[2].capitalize()])
						self.places_paths.append(x)
					else: #Regular mounted drive (ie/eg windows partition)
						try:
							self.liststore.append([self.theme.load_icon('drive-harddisk',24,24),x])
						except:
							self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
								.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),x])
						self.places_paths.append(x)
				else: #Maybe /home, /boot, /usr, etc.
					try:
						self.liststore.append([self.theme.load_icon('drive-harddisk',24,24),x])
					except:
						self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
							.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),x])
		
		#Go through the list of network drives/etc. from /etc/fstab
		if self.show_network==2:
			for x in self.nfs_smb_paths:
				try:
					self.liststore.append([self.theme.load_icon('network-folder',24,24),\
						self.nfs_smb_corr_hnames[self.nfs_smb_paths.index(x)]])
				except:
					self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
						.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),self.nfs_smb_corr_hnames[self.nfs_smb_paths.index(x)]])
				self.places_paths.append(x)
		
		#Go through the list of bookmarks and add them to the list IF it's not in the mount list
		if self.show_bookmarks==2:
			for x in self.bmarks:
				x = x.replace('file://','')
				if x not in self.paths and x!=os.path.expanduser('~'):
					if x[0]=='/': #Normal filesystem bookmark, not computer:///,burn:///,network:///,etc.
						try:
							self.liststore.append([self.theme.load_icon('folder',24,24),x.split('/')[-1:][0].replace('\n','')])
						except:
							self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
								.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),x.split('/')[-1:][0].replace('\n','')])
						self.places_paths.append(x.replace('\n',''))
					else:
						y = x.split(':')[0]
						if y=='computer':
							try:
								self.liststore.append([self.theme.load_icon('computer',24,24),'Computer'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Computer'])
							self.places_paths.append('%s:///' % y)
						elif y in ['network','smb','nfs','ftp','ssh']:
							try:
								self.liststore.append([self.theme.load_icon('network-server',24,24),'Network'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Network'])
							self.places_paths.append('%s:///' % y)
						elif y=='trash':
							if self.trash_full==True:
								try:
									self.liststore.append([self.theme.load_icon('user-trash-full',24,24),'Trash'])
								except:
									self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
										.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Trash'])
								self.places_paths.append('%s:///' % y)
							else:
								try:
									self.liststore.append([self.theme.load_icon('user-trash',24,24),'Trash'])
								except:
									self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
										.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Trash'])
								self.places_paths.append('%s:///' % y)
						elif y=='x-nautilus-search':
							try:
								self.liststore.append([self.theme.load_icon('search',24,24),'Search'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Search'])
							self.places_paths.append('%s:///' % y)
						elif y=='burn':
							try:
								self.liststore.append([self.theme.load_icon('drive-optical',24,24),'CD/DVD Burner'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'CD/DVD Burner'])
							self.places_paths.append('%s:///' % y)
						elif y=='fonts':
							try:
								self.liststore.append([self.theme.load_icon('font',24,24),'Fonts'])
							except:
								self.liststore.append([gtk.gdk.pixbuf_new_from_file(self.default_icon_path)\
									.scale_simple(24,24,gtk.gdk.INTERP_BILINEAR),'Fonts'])
							self.places_paths.append('%s:///' % y)
	
	#Function to do what should be done according to gconf when the treeview is clicked
	def treeview_clicked(self,widget,event):
		self.open_clicked = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/places_open',2)
		self.selection = self.treeview.get_selection()
		if self.open_clicked==2:
			self.dialog.hide()
			self.launch_fb(None,self.places_paths[self.liststore[self.selection.get_selected()[1]].path[0]])
		else:
			self.entry.set_text(self.places_paths[self.liststore[self.selection.get_selected()[1]].path[0]])
			self.entry.grab_focus()
	
	#Applet show/hide methods - copied from MiMenu (and edited)
	#When a button is pressed
	def button_press(self, widget, event):
		if self.dialog.flags() & gtk.VISIBLE:
			self.dialog.hide()
			self.title.hide(self)
		else:
			if event.button==1 or event.button==2:
				self.dialog_config(event.button)
			elif event.button==3:
				self.show_menu(event)
			self.title.hide(self)
	
	#dialog_config: 
	def dialog_config(self,button):
		if button!=1 and button!=2:
			return False
		self.curr_button = button
		
		#Get whether to focus the entry when displaying the dialog or not
		self.gconf_focus = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/focus_entry',2)
		
		if button==1: #Left mouse button
		#Get the value for the left mouse button to automatically open. Create and default to 1 the entry if it doesn't exist
		#Also get the default directory or default to ~
			self.gconf_lmb = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/lmb',1)
			self.gconf_lmb_path = self.client.get_string('/apps/avant-window-navigator/applets/file-browser-launcher/lmb_path',\
			os.path.expanduser('~'))
		
		elif button==2: #Middle mouse button
		#Get the value for the middle mouse button to automatically open. Create and default to 2 the entry if it doesn't exist
		#Also get the default directory or default to ~
			self.gconf_mmb = self.client.get_int('/apps/avant-window-navigator/applets/file-browser-launcher/mmb',2)
			self.gconf_mmb_path = self.client.get_string('/apps/avant-window-navigator/applets/file-browser-launcher/mmb_path',\
			os.path.expanduser('~'))
		
		#Now get the chosen program for file browsing from gconf
		self.gconf_fb = self.client.get_string('/apps/avant-window-navigator/applets/file-browser-launcher/fb','xdg-open')
		
		#Left mouse button - either popup with correct path or launch correct path OR do nothing
		if button==1:
			if self.gconf_lmb==1:
				self.entry.set_text(self.gconf_lmb_path)
				self.add_places()
				if self.gconf_focus==2:
					self.entry.grab_focus()
				self.dialog.show_all()
			elif self.gconf_lmb==2:
				self.launch_fb(None,self.gconf_lmb_path)
		
		#Right mouse button - either popup with correct path or launch correct path OR do nothing
		if button==2:
			if self.gconf_mmb==1:
				self.entry.set_text(self.gconf_mmb_path)
				self.add_places()
				if self.gconf_focus==2:
					self.entry.grab_focus()
				self.dialog.show_all()
			elif self.gconf_mmb==2:
				self.launch_fb(None,self.gconf_mmb_path)
	
	#If the user hits the enter key on the main part OR the number pad
	def detect_enter(self,a,event):
		if event.keyval==65293 or event.keyval==65421:
			self.enter.clicked()
	
	#Launces file browser to open "path". If "path" is None: use value from the entry widget
	def launch_fb(self,widget,path=None):
		self.dialog.hide()
		if path==None:
			path = self.entry.get_text()
		
		#Get the file browser app, or set to xdg-open if it's not set
		self.gconf_fb = self.client.get_string('/apps/avant-window-navigator/applets/file-browser-launcher/fb','xdg-open')
		
		#In case there is nothing but whitespace (or at all) in the entry widget
		if path.replace(' ','')=='':
			path = os.path.expanduser('~')
		
		#Launch file browser at path
		subprocess.Popen(self.gconf_fb.split(' ')+[path])
	
	#Right click menu - Preferences or About
	def show_menu(self,event):
		
		#Hide the dialog if it's shown
		self.dialog.hide()
		
		#Create the items for Preferences and About
		self.prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
		self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
		
		#Connect the two items to functions when clicked
		self.prefs.connect("activate",self.open_prefs)
		self.about.connect("activate",self.open_about)
		
		#Now create the menu to put the items in and show it
		self.menu = gtk.Menu()
		self.menu.append(self.prefs)
		self.menu.append(self.about)
		self.menu.show_all()
		self.menu.popup(None, None, None, event.button, event.time)
	
	#Show the preferences window
	def open_prefs(self,widget):
		#Import the prefs file from the same directory
		import prefs
		
		#Show the prefs window - see prefs.py
		prefs.Prefs(self.set_icon)
		gtk.main()
	
	#Show the about window
	def open_about(self,widget):
		#Import the about file from the same directory
		import about
		
		#Show the about window - see about.py
		about.About()
	
		
if __name__ == '__main__':
	awn.init(sys.argv[1:])
	applet = App(awn.uid, awn.orient,awn.height)
	awn.init_applet(applet)
	applet.show_all()
	gtk.main()
