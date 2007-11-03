#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is the forecast dialog for a weather applet for Avant Window Navigator.
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
import gtk
from gtk import gdk
import cairo
import wnck
import weathericons
APP="awn-weather-applet"
DIR="locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class WeatherDialog(gtk.DrawingArea):

	def __init__(self,forecast):
		gtk.DrawingArea.__init__(self)
		super(WeatherDialog, self).__init__()
		self.connect("expose_event", self.expose) 
		self.connect('button-press-event', self.button_press)
		self.forecast = forecast
		self.icons = weathericons.WeatherIcons()

	def button_press(self):
		self.hide()

	def expose(self,widget,event):
		context = widget.window.cairo_create()
		context.set_source_rgb(0,0,0)
		context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)
		context.set_font_size(10.0)
		context.set_line_width(1)
		i = 15
		for f in self.forecast[0:5]:
			context.set_source_rgb(0,0,0)
			context.rectangle(i,5,70,100)
			context.fill()			
			context.set_source_rgba(0.6,0.7,1.0,1.0)
			context.rectangle(i+1,19,68,72)
			context.fill()
			context.move_to(i+5,15)
			context.set_source_rgba(1,1,1)
			context.show_text(f.day_of_week)
			icon_name=self.icons.day_icons[f.condition_code]
			icon = gdk.pixbuf_new_from_file(icon_name)
			scaled = icon.scale_simple(55,55,gdk.INTERP_BILINEAR)
			context.set_source_pixbuf(scaled,i+8,27)
			context.fill()
			context.paint()
			context.move_to(i+10,102)
			context.set_source_rgba(1.0,0.25,0.25,1.0)
			context.show_text(f.high + u"\u00B0")
			context.move_to(i+40,102)
			context.set_source_rgba(0.25,0.25,1.0,1.0)
			context.show_text(f.low + u"\u00B0")
			i = i + 75
		context.set_source_rgb(0.3,0.3,0.8)
		context.move_to(105,125)
		context.show_text(_("Weather data provided by weather.com"))
		return False 
		
