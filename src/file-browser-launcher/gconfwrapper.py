#!/usr/bin/env python
# -*- coding:utf-8 -*-
import gconf
class GConfWrapper:
	
	def __init__(self):
		self.client = gconf.client_get_default()
	
	#Get a GConf string
	def get_string(self,key,default):
		try:
			self.client.add_dir('/apps/avant-window-navigator/applets/file-browser-launcher')
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
			self.client.add_dir('/apps/avant-window-navigator/applets/file-browser-launcher')
		except:
			pass
		val = self.client.set_string(key,val)
		return val

	#Get a GConf integer
	def get_int(self,key,default):
		try:
			self.client.add_dir('/apps/avant-window-navigator/applets/file-browser-launcher')
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
			self.client.add_dir('/apps/avant-window-navigator/applets/file-browser-launcher')
		except:
			pass
		val = self.client.set_int(key,val)
		return val
