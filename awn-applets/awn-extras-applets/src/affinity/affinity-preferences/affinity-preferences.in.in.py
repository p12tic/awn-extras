#!/usr/bin/env python
#
#  Copyright (C) 2007 Neil Jagdish Patel <njpatel@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
#
#  Author: Neil Jagdish Patel <njpatel@gmail.com>
#
#  Notes: Avant Window Navigator preferences window

import sys, os
try:
 	import pygtk
  	pygtk.require("2.0")
except:
  	pass
try:
	import gtk
  	import gtk.glade
except:
	sys.exit(1)

import gconf

PKG_DATA_DIR = "@PKGDATADIR@"
DATA_DIR = "@DATADIR@"

APP = 'affinity'
DIR = os.path.join (DATA_DIR, "locale")
I18N_DOMAIN = "affinity"

import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext


def dec2hex(n):
	"""return the hexadecimal string representation of integer n"""
	n = int(n)
	if n == 0:
		return "00"
	return "%0.2X" % n
 
def hex2dec(s):
	"""return the integer value of a hexadecimal string s"""
	return int(s, 16)

def make_color(hexi):
	"""returns a gtk.gdk.Color from a hex string RRGGBBAA"""
	color = gtk.gdk.color_parse('#' + hexi[:6])
	alpha = hex2dec(hexi[6:])
	alpha = (float(alpha)/255)*65535
	return color, int(alpha)
	
def make_ncolor(hexi):
	"""returns a gtk.gdk.Color from a hex string RRGGBBAA"""
	color = gtk.gdk.color_parse(hexi)
	return color	

def make_color_string(color, alpha):
	"""makes avant-readable string from gdk.color & alpha (0-65535) """
	string = ""
	
	string = string + dec2hex(int( (float(color.red) / 65535)*255))
	string = string + dec2hex(int( (float(color.green) / 65535)*255))
	string = string + dec2hex(int( (float(color.blue) / 65535)*255))
	string = string + dec2hex(int( (float(alpha) / 65535)*255))
	
	#hack
	return string	

def make_ncolor_string(color):
	"""makes avant-readable string from gdk.color & alpha (0-65535) """
	string = "#"
	
	string = string + dec2hex(int( (float(color.red) / 65535)*255))
	string = string + dec2hex(int( (float(color.green) / 65535)*255))
	string = string + dec2hex(int( (float(color.blue) / 65535)*255))
	
	#hack
	return string	
	

# GCONF KEYS
AFF_PATH		= "/apps/affinity"
AFF_KEY			= "/apps/affinity/global_key_binding"

COL_PATH		= "/apps/affinity/colors"				#color*/
COL_ROUNDED		= "/apps/affinity/colors/rounded_corners"		#bool*/		
COL_BACK_STEP_1		= "/apps/affinity/colors/back_step_1"		#color*/
COL_BACK_STEP_2		= "/apps/affinity/colors/back_step_2"		#color*/
COL_HIGH_STEP_1		= "/apps/affinity/colors/high_step_1"		#color*/
COL_HIGH_STEP_2		= "/apps/affinity/colors/high_step_2"		#color*/
COL_HIGHLIGHT		= "/apps/affinity/colors/highlight"		#color*/
COL_BORDER		= "/apps/affinity/colors/border"			#color*/
COL_WIDGET_BORDER	= "/apps/affinity/colors/widget_border"		#color*/
COL_WIDGET_HIGHLIGHT	= "/apps/affinity/colors/widget_highlight"	#color*/
COL_TEXT_COLOR		= "/apps/affinity/colors/text_color" 		#string*/

FILT_PATH               = "/apps/affinity/filters"
FILT_APPS               = "/apps/affinity/filters/applications"           #CSV*/
FILT_BOOKS              = "/apps/affinity/filters/bookmarks"              #CSV*/
FILT_CONTACTS           = "/apps/affinity/filters/contacts"               #CSV*/
FILT_DOCS               = "/apps/affinity/filters/documents"              #CSV*/
FILT_EMAILS             = "/apps/affinity/filters/emails"                 #CSV*/
FILT_IMAGES             = "/apps/affinity/filters/images"                 #CSV*/
FILT_MUSIC              = "/apps/affinity/filters/music"                  #CSV*/
FILT_VIDS               = "/apps/affinity/filters/vids"                   #CSV*/

SYS_PATH                = "/apps/affinity/system"
SYS_SOFTWARE            = "/apps/affinity/system/config_software"         #command line*/
SYS_CONTROL_PANEL       = "/apps/affinity/system/control_panel"           #command line*/
SYS_LOCK_SCREEN         = "/apps/affinity/system/lock_screen"             #command line*/
SYS_LOG_OUT             = "/apps/affinity/system/log_out"                 #command line*/	
SYS_OPEN_URI            = "/apps/affinity/system/open_uri"                #command line*/
SYS_FILE_MAN            = "/apps/affinity/system/file_manager"            #command line*/
SYS_COMPUTER            = "/apps/affinity/system/computer"                #command line*/
SYS_NETWORK             = "/apps/affinity/system/network"                 #command line*/

class main:
	"""This is the main class, duh"""

	def __init__(self):
		
		self.client = gconf.client_get_default()
		self.client.add_dir(AFF_PATH, gconf.CLIENT_PRELOAD_NONE)
		self.client.add_dir(COL_PATH, gconf.CLIENT_PRELOAD_NONE)
		self.client.add_dir(FILT_PATH, gconf.CLIENT_PRELOAD_NONE)
		self.client.add_dir(SYS_PATH, gconf.CLIENT_PRELOAD_NONE)
		
		#Set the Glade file
		gtk.glade.bindtextdomain(APP, DIR)
		gtk.glade.textdomain(APP)
		self.gladefile = os.path.join(PKG_DATA_DIR, "window.glade") 
		print self.gladefile 
	        self.wTree = gtk.glade.XML(self.gladefile, domain=I18N_DOMAIN) 
		
		#Get the Main Window, and connect the "destroy" event
		self.window = self.wTree.get_widget("main_window")
		self.window.connect("delete-event", gtk.main_quit)
		
		close = self.wTree.get_widget("closebutton")
		close.connect("clicked", gtk.main_quit)

		self.setup_entry(SYS_SOFTWARE, self.wTree.get_widget("softwareentry"))
		self.setup_entry(SYS_CONTROL_PANEL, self.wTree.get_widget("controlentry"))
		self.setup_entry(SYS_LOCK_SCREEN, self.wTree.get_widget("lockentry"))
		self.setup_entry(SYS_LOG_OUT, self.wTree.get_widget("logoutentry"))
		self.setup_entry(SYS_OPEN_URI, self.wTree.get_widget("openentry"))
		self.setup_entry(SYS_FILE_MAN, self.wTree.get_widget("filemanentry"))
		self.setup_entry(SYS_COMPUTER, self.wTree.get_widget("computerentry"))
		self.setup_entry(SYS_NETWORK, self.wTree.get_widget("networkentry"))

		self.setup_entry(FILT_APPS, self.wTree.get_widget("appentry"))
		self.setup_entry(FILT_BOOKS, self.wTree.get_widget("bookentry"))
		self.setup_entry(FILT_CONTACTS, self.wTree.get_widget("contactsentry"))
		self.setup_entry(FILT_DOCS, self.wTree.get_widget("docsentry"))
		self.setup_entry(FILT_EMAILS, self.wTree.get_widget("emailentry"))
		self.setup_entry(FILT_IMAGES, self.wTree.get_widget("imageentry"))
		self.setup_entry(FILT_MUSIC, self.wTree.get_widget("musicentry"))
		self.setup_entry(FILT_VIDS, self.wTree.get_widget("videntry"))				
		
		self.setup_bool (COL_ROUNDED, self.wTree.get_widget("roundedcornerscheck"))
		self.setup_color(COL_BACK_STEP_1, self.wTree.get_widget("backstep1color"))
		self.setup_color(COL_BACK_STEP_2, self.wTree.get_widget("backstep2color"))
		self.setup_color(COL_HIGH_STEP_1, self.wTree.get_widget("highstep1color"))
		self.setup_color(COL_HIGH_STEP_2, self.wTree.get_widget("highstep2color"))		
		self.setup_color(COL_BORDER, self.wTree.get_widget("winbordermaincolor"))
		self.setup_color(COL_HIGHLIGHT, self.wTree.get_widget("winborderhighcolor"))
		self.setup_color(COL_WIDGET_BORDER, self.wTree.get_widget("widbordermaincolor"))
		self.setup_color(COL_WIDGET_HIGHLIGHT, self.wTree.get_widget("widborderhighcolor"))
		self.setup_ncolor(COL_TEXT_COLOR, self.wTree.get_widget("textcolor"))

	def win_destroy(self, button, w):
		w.destroy()

	def setup_entry(self, key, entry):
		text = self.client.get_string(key)
		entry.set_text (text)
		entry.connect("changed", self.entry_changed, key)
	
	def entry_changed (self, entry, key):
		text = entry.get_text()
		self.client.set_string(key, text)
	
	def setup_ncolor(self, key, colorbut):
		color = make_ncolor (self.client.get_string(key))
		colorbut.set_color(color)
		colorbut.connect("color-set", self.ncolor_changed, key)
	
	def ncolor_changed(self, colorbut, key):
		string = make_ncolor_string (colorbut.get_color())
		self.client.set_string(key, string)
	
	def setup_color(self, key, colorbut):
		color, alpha = make_color(self.client.get_string(key))
		colorbut.set_color(color)
		colorbut.set_alpha(alpha)
		colorbut.connect("color-set", self.color_changed, key)
	
	def color_changed(self, colorbut, key):
		string =  make_color_string(colorbut.get_color(), colorbut.get_alpha())
		self.client.set_string(key, string)

	def setup_scale(self, key, scale):
		val = self.client.get_float(key)
		val = 100 - (val * 100)
		scale.set_value(val)
		scale.connect("value-changed", self.scale_changed, key)
	
	def scale_changed(self, scale, key):
		val = scale.get_value()
		val = 100 - val
		if (val):
			val = val/100
		self.client.set_float(key, val)
		
	
	def setup_spin(self, key, spin):
		spin.set_value(	self.client.get_float(key))
		spin.connect("value-changed", self.spin_changed, key)
	
	def spin_changed(self, spin, key):
		self.client.set_float(key, spin.get_value())
		

	def setup_chooser(self, key, chooser):
		"""sets up png choosers"""
		fil = gtk.FileFilter()
		fil.set_name("PNG Files")
		fil.add_pattern("*.png")
		fil.add_pattern("*.PNG")
		chooser.add_filter(fil)
		preview = gtk.Image()
		chooser.set_preview_widget(preview)
		chooser.connect("update-preview", self.update_preview, preview)
		chooser.set_filename(self.client.get_string(key))
		chooser.connect("selection-changed", self.chooser_changed, key)
	
	def chooser_changed(self, chooser, key):
		f = chooser.get_filename()
		if f == None:
			return
		self.client.set_string(key, f)
	
	def update_preview(self, chooser, preview):
		f = chooser.get_preview_filename()
		try:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(f, 128, 128)
			preview.set_from_pixbuf(pixbuf)
			have_preview = True
		except:
			have_preview = False
		chooser.set_preview_widget_active(have_preview)
	
	def setup_bool(self, key, check):
		"""sets up checkboxes"""
		check.set_active(self.client.get_bool(key))
		check.connect("toggled", self.bool_changed, key)
		
	
	def bool_changed(self, check, key):
		self.client.set_bool(key, check.get_active())
		print "toggled"


if __name__ == "__main__":
	gettext.textdomain(I18N_DOMAIN)
	gtk.glade.bindtextdomain(I18N_DOMAIN, "/usr/share/locale")
	app = main()
	gtk.main()

