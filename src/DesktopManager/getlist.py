#!/usr/bin/python
#
#       getlist.py Version 0.5
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
import threading
import os
class GetList(threading.Thread) :
	def __init__(self, config, parent) :
		self.config = config
		self.switcher = parent
		threading.Thread.__init__ (self)
		self.alive = True
	def run(self) :
		folder = self.config.get_sub_folder()
		filesList = []
		self.switcher.set_files(filesList)
		a = []
		if (folder != "") :
			folder2 = self.config.get_folder() + folder
		else :
			folder2 = self.config.get_folder()
		for root, dirs, files in os.walk(folder2) :
			for file in files :
				if (self.alive == False) :
					return False
				fil = root+"/"+file
				ext = fil.split('.')
				ext = ext[len(ext)-1]
				if (ext != "jpg" and ext != "png" and ext != "jpeg") :
					continue
				else :
					filesList.append(fil)
					self.switcher.set_files(filesList)
	def kill(self) :
		self.alive = False
