#!/usr/bin/python
#
#       config.py Version 0.5
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
import awn
import os
class ConfigManager :
	def __init__(self) :
		self.cfg = awn.Config("DesktopManager", None)
		self.button_actions = [0,0,0]
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "folder")) :
			self.folder = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "folder")
		else :
			self.set_folder("~")
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "secs")) :
			self.secs = self.cfg.get_int(awn.CONFIG_DEFAULT_GROUP, "secs")
		else :
			self.set_secs(60000)
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "play")) :
			self.play = self.cfg.get_bool(awn.CONFIG_DEFAULT_GROUP, "play")
		else :
			self.set_play(False)
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "subfolder")) :
			self.sub_folder = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "subfolder")
		else :
			self.set_sub_folder("")
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "environment")) :
			self.environment = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "environment")
		else :
			self.set_environment("GNOME")
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "attention")) :
			self.attention = self.cfg.get_bool(awn.CONFIG_DEFAULT_GROUP, "attention")
		else :
			self.set_attention(False)
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "button1_action")) :
			self.button_actions[1] = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "button1_action")
		else :
			self.set_button_action(1,"Switch Desktop Image")
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "button2_action")) :
			self.button_actions[2] = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "button2_action")
		else :
			self.set_button_action(2,"None")
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "show_desktop")) :
			self.show_desktop = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "show_desktop")
		else :
			self.set_show_desktop("Toggle showing the desktop")
		if (self.cfg.exists(awn.CONFIG_DEFAULT_GROUP, "method")) :
			self.method = self.cfg.get_string(awn.CONFIG_DEFAULT_GROUP, "method")
		else :
			self.set_method("Random")
		self.makepod()
	def makepod(self) :
		if (self.environment == "GNOME") :
			from configgnome import ConfigManagerGnome
			self.enviropod = ConfigManagerGnome()
		elif (self.environment == "Xfce") :
			from configxfce import ConfigManagerXfce
			self.enviropod = ConfigManagerXfce()
		else :
			from configgnome import ConfigManagerGnome
			self.enviropod = ConfigManagerGnome()
	def get_play(self) :
		return self.play
	def get_attention(self) :
		return self.attention
	def get_secs(self) :
		return self.secs
	def get_folder(self) :
		if (self.folder == "~") :
			self.folder = os.path.expanduser(self.folder)
		return self.folder
	def get_desktop(self) :
		return self.enviropod.get_desktop()
	def get_sub_folder(self) :
		return self.sub_folder
	def get_render(self) :
		return self.enviropod.get_render()
	def get_environment(self) :
		return self.environment
	def get_button_action(self,button) :
		return self.button_actions[button]
	def get_show_desktop(self) :
		return self.show_desktop
	def get_method(self) :
		return self.method
	def set_play(self, play) :
		self.cfg.set_bool(awn.CONFIG_DEFAULT_GROUP, "play", play)
		self.play = play
	def set_attention(self, attention) :
		self.cfg.set_bool(awn.CONFIG_DEFAULT_GROUP, "attention", attention)
		self.attention = attention
	def set_secs(self, secs) :
		self.cfg.set_int(awn.CONFIG_DEFAULT_GROUP, "secs", secs)
		self.secs = secs
	def set_folder(self, folder) :
		self.cfg.set_string(awn.CONFIG_DEFAULT_GROUP, "folder", folder)
		self.folder = folder
	def set_desktop(self, file) :
		self.enviropod.set_desktop(file)
	def set_sub_folder(self, sub_folder) :
		self.cfg.set_string(awn.CONFIG_DEFAULT_GROUP, "subfolder", sub_folder)
		self.sub_folder = sub_folder
	def set_render(self, render) :
		self.enviropod.set_render(render)
	def set_environment(self, environment) :
		self.cfg.set_string(awn.CONFIG_DEFAULT_GROUP, "environment", environment)
		self.environment = environment
		self.makepod()
	def set_button_action(self,button, action) :
		self.cfg.set_string(awn.CONFIG_DEFAULT_GROUP, "button"+ str(button) + "_action", action)
		self.button_actions[button] = action
	def set_show_desktop(self, show_desktop) :
		self.cfg.set_string(awn.CONFIG_DEFAULT_GROUP, "show_desktop", show_desktop)
		self.show_desktop = show_desktop
	def set_method(self, method) :
		self.cfg.set_string(awn.CONFIG_DEFAULT_GROUP, "method", method)
		self.method = method
