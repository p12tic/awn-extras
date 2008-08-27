#!/usr/bin/python
#
#       configgnome.py Version 0.5
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
import gconf

class ConfigManagerGnome :
	def __init__(self) :
		self.conf_client = gconf.client_get_default()
		self.current = self.conf_client.get_string("/desktop/gnome/background/picture_filename")
		self.render = self.conf_client.get_string("/desktop/gnome/background/picture_options")
	def get_desktop(self) :
		return self.current
	def get_render(self) :
		return self.render
	def set_desktop(self, file) :
		self.conf_client.set_string("/desktop/gnome/background/picture_filename", file)
		self.current = file
	def set_render(self, render) :
		self.conf_client.set_string("/desktop/gnome/background/picture_options", render)
		self.render = render
