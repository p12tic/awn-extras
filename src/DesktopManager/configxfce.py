#!/usr/bin/python
#
#       conigxfce.py Version 0.5
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
import os
import re

class ConfigManagerXfce :
	trans = ["","centered","","stretched","scaled","zoom"]
	def __init__(self) :
		self.config = os.path.expanduser("~")+"/.config/xfce4/mcs_settings/desktop.xml"
		self.filename = os.path.expanduser("~")+"/.config/xfce4/desktop/backdrops.list"
		confighandle = open(self.config, "r")
		lines = confighandle.readlines()
		for line in lines :
			#line2 = re.sub('<option name="imagepath_0_0" type="string" value="(.+)"/>', '<option name="imagepath_0_0" type="string" value="'+self.filename+'"/>', line)
			#lines[lines.index(line)] = line2
			if (re.search('<option name="imagestyle_0_0" type="int" value="(.+)"/>', line) != None) :
				self.render = self.trans[int(re.findall('<option name="imagestyle_0_0" type="int" value="(.+)"/>', line)[0])]
		confighandle.close()
		print self.render
		#confighandle = open(self.config, "w")
		#confighandle.writelines(lines)
		#confighandle.close()
		try :
			file = open(self.filename, "r")
		except IOError:
			self.current = None
			try :
				os.makedirs(os.path.expanduser("~")+"/.config/xfce4/desktop/")
			except OSError:
				pass
		else :
			lines = file.readlines()
			self.current = lines[1]
			file.close()
	def get_desktop(self) :
		return self.current
	def get_render(self) :
		return self.render
	def set_desktop(self, image) :
		file = open(self.filename, "w")
		file.write("# xfce backdrop list\n"+image)
		file.close()
		os.system("xfdesktop --reload")
		self.current = image
	def set_render(self, render) :
		#current = str(self.trans.index(render))
		#confighandle = open(self.config, "r")
		#lines = confighandle.readlines()
		#for line in lines :
		#	line2 = re.sub('<option name="imagestyle_0_0" type="int" value="(.+)"/>', '<option name="imagestyle_0_0" type="int" value="'+current+'"/>', line)
		#	lines[lines.index(line)] = line2
		#confighandle.close()
		#confighandle = open(self.config, "w")
		#confighandle.writelines(lines)
		#confighandle.close()
		#os.system("xfdesktop --reload")
		pass
