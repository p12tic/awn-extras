#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is a weather applet for Avant Window Navigator... this module loads
# and displays a sattelite image
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
import sys, os
import urllib
import awn
import gtk
from gtk import gdk
import cairo
import re
import weathericons
import weathertext
APP="awn-weather-applet"
DIR=os.path.dirname (__file__) + '/locale'
import locale
import gettext
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class WeatherMap(awn.AppletDialog):

	def __init__(self,applet):
		super(WeatherMap, self).__init__(applet)
		self.location_code = applet.location_code
		self.effects = awn.AppletSimple.get_effects(applet)
		self.applet = applet
		self.set_size_request(400,375)
		self.set_title(_("Weather Map"))
		self.area = gtk.DrawingArea();
		self.area.set_size_request(380,250)
		self.area.show()
		vbox = gtk.VBox()
		vbox.pack_start(self.area)
		self.close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
		self.close_button.connect("clicked", self.button_press) 
		vbox.pack_end(self.close_button)
		self.area.connect("expose-event", self.expose_area)
		self.add(vbox)
		
	def expose_area(self,widget,event):
		image = gtk.Image()
		image.set_from_file(self.applet.img_file)
		pixbuf = image.get_pixbuf()
		scaled = pixbuf.scale_simple(380,250,gtk.gdk.INTERP_BILINEAR)		
		context = self.area.window.cairo_create()
		surface = context.set_source_pixbuf(scaled,0,0)
		context.rectangle(0,0,380,270)
		context.fill()

	def button_press(self,widget):
		# When the "close" button is clicked, the color returns		
		awn.awn_effect_stop(self.effects,"desaturate")
		self.hide()

	def expose(self,widget,event):
		return True

	def get_map(self):
		try:
			usock = urllib.urlopen('http://www.weather.com/outlook/travel/businesstraveler/map/USME0038')
			lines = usock.readlines()
			iframe_re = re.compile(".*[iI][fF][rR][aA][mM][eE].*")
			for line in lines:
				if iframe_re.match(line):
					frame_src_start = line.find("src")
					frame_src_end = line.find("?")
					if frame_src_start > -1 and frame_src_end > -1:
						frame_src = line[frame_src_start+5 : frame_src_end]
						usock2 =  urllib.urlopen('http://www.weather.com' + frame_src)
						frame_lines = usock2.readlines()
						img_re = re.compile(".*[iI][mM][gG] [nN][aA][mM][eE]=\"mapImg\".*")
						for frame_line in frame_lines:
							if img_re.match(frame_line):
								img_src_start = frame_line.find("SRC")
								img_src_end = frame_line.find("jpg")
								img_src = frame_line[img_src_start+5 : img_src_end+3]
								self.img_file = urllib.urlretrieve(img_src)[0]
								print self.img_file
						usock2.close()
			usock.close()
		except:
			print "Unable to download weather map. ", sys.exc_info()[0], sys.exc_info()[1]

		
