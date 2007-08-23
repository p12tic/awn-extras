# Album Cover Plugin code changed for awn/kiba pleasure
# Shamelessly Modified By: sandi.newton
# Original Copyright 2005 Joe Wreschnig
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation


def_image = "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"


import base64
import config
import sys
import shutil
import qltk
import dbus
import atexit
from widgets import main as window, watcher
from player import playlist as player
from plugins.events import EventPlugin
awn = None
kiba_bus = None
png1 = None
out = "/tmp/current.cover"
ICON_NAME = "quod-cover"
def resetpic():
	global awn
	global kiba_bus
	if awn:
		try:
			awn.UnsetTaskIconByName("quodlibet")
		except:
			pass	
	if kiba_bus:
		try:
			kiba_bus.RemoveObject(ICON_NAME)
		except:
			pass
class PictureSaver(EventPlugin):
    PLUGIN_ID = "Album Art Display in AWN or Kiba Dock"
    PLUGIN_NAME = _("Album Art Display")
    PLUGIN_DESC = "The cover image is shown in AWN/Kiba dock's "
    PLUGIN_VERSION = "0.2"
    def __init__(self):
	global awn
	global kiba_bus
	global png1
	bus_obj = dbus.SessionBus().get_object("com.google.code.Awn", "/com/google/code/Awn")
	awn = dbus.Interface(bus_obj, "com.google.code.Awn")
	kiba_bus = dbus.SessionBus().get_object("org.kiba.dock.Kiba","/org/kiba/dock/Kiba")
	png1 = base64.b64decode(def_image)
	try:
		awn.GetTaskByPid(1)
	except:
		pass	
	try:
		kiba_bus.AddObject(ICON_NAME,out)
	except:
		pass
	atexit.register(resetpic)
    def plugin_on_song_started(self, song):
	global awn
	global kiba_bus
	global png1
        if song is None:
		fp = open(out,"wb")
		fp.write(png1)
		fp.close()
		if awn:
			try:
				awn.SetTaskIconByName("quodlibet",out)
			except:
				pass
		if kiba_bus:
			try:
				kiba_bus.SetActiveIconByName(ICON_NAME,"")
				kiba_bus.SetActiveIconByName(ICON_NAME,out)
			except dbus.DBusException,e:
				if e.__str__() == "No Object Found":
					kiba_bus.AddObject(ICON_NAME,out)
				pass
        else:
            cover = song.find_cover()
            if cover is None:
		fp = open(out,"wb")
		fp.write(png1)
		fp.close()
		if awn:
			try:
				awn.SetTaskIconByName("quodlibet",out)
			except:
				pass
		if kiba_bus:
			try:
				kiba_bus.SetActiveIconByName(ICON_NAME,"")
				kiba_bus.SetActiveIconByName(ICON_NAME,out)
			except dbus.DBusException,e:
				if e.__str__() == "No Object Found":
					kiba_bus.AddObject(ICON_NAME,out)
				pass	
		
            else:
                f = file(out, "wb")
                f.write(cover.read())
                f.close()
		if awn:
			try:
				awn.SetTaskIconByName("quodlibet", out)
			except:
				pass	
		if kiba_bus:
			try:
				kiba_bus.SetActiveIconByName(ICON_NAME,"")
				kiba_bus.SetActiveIconByName(ICON_NAME,out)
			except dbus.DBusException,e:
				if e.__str__() == "No Object Found":
					kiba_bus.AddObject(ICON_NAME,out)
				pass

    def disabled(self):
	resetpic()
    def enabled(self):
	global kiba_bus
	global awn
	if kiba_bus:
		try:
			kiba_bus.AddObject(ICON_NAME,out) 
		except:
			pass	
	if awn:
		try:
			awn.SetTaskIconByName("quodlibet",out)
		except:
			pass
    def destroy(self):
	resetpic()
