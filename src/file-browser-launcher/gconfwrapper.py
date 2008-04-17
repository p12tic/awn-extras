#! /usr/bin/env python
# -*- coding:utf-8 -*-
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
#File Browser Launcher
#GCONF Wrapper File

import gconf
class GConfWrapper:
	
	def __init__(self,uid):
		self.uid = uid
		self.client = gconf.client_get_default()
	
	#Get a GConf string
	def get_string(self,key,default):
		try:
			self.client.add_dir('/apps/avant-window-navigator/applets/'+str(self.uid))
		except:
			pass
		val = self.client.get_string(key)
		if val==None:
			val = default
			self.client.set_string(key,default)
		return val

	#Set a GConf string
	def set_string(self,key,val):
		try:
			self.client.add_dir('/apps/avant-window-navigator/applets/'+str(self.uid))
		except:
			pass
		val = self.client.set_string(key,val)
		return val

	#Get a GConf integer
	def get_int(self,key,default):
		try:
			self.client.add_dir('/apps/avant-window-navigator/applets/'+str(self.uid))
		except:
			pass
		val = self.client.get_int(key)
		if val==0:
			val = default
			self.client.set_int(key,default)
		return val

	#Set a GConf integer	
	def set_int(self,key,val):
		try:
			self.client.add_dir('/apps/avant-window-navigator/applets/'+str(self.uid))
		except:
			pass
		val = self.client.set_int(key,val)
		return val
