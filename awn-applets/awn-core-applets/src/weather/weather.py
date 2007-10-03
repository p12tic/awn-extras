#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is a weather applet for Avant Window Navigator.
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
import gobject
import pygtk
import gtk
from gtk import gdk
import gconf
import pango
import awn
import urllib
from xml.dom import minidom
import cairo
from StringIO import StringIO
import weatherdialog
import weathericons
import weatherconfig
APP="awn-weather-applet"
DIR="locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class Forecast:
	def __init__(self, day_of_week, day_of_year, low, high, condition_code, condition_text, precip, humidity, wind_dir, wind_speed, wind_gusts, city):
		self.day_of_week = day_of_week
		self.day_of_year = day_of_year
		self.low = low
		self.high = high
		self.condition_code = condition_code
		self.condition_text = condition_text
		self.precip = precip
		self.humidity = humidity
		self.wind_dir = wind_dir
		self.wind_speed = wind_speed
		self.wind_gusts = wind_gusts
		self.city = city
  
class App(awn.AppletSimple):

	# default title/tooltip to show on startup.
	titleText = _("Fetching weather data.")

	# "Private" stuff
	forecast_visible = False
	current_condition = ""
	city = ""
	current_temp = ""
	forecast = []
	gconf_path = "/apps/avant-window-navigator/applets/weather"
	open_til_clicked = False

	# Default only - we fetch the "real" answer from GConf
	location = "Portland ME"

	# Default only - we fetch the "real" answer from GConf
	units = "Imperial"

	# Default only - we fetch the "real" answer from GConf
	polling_frequency = 1000 * 60 * 30

	def __init__(self, uid, orient, height):
		awn.AppletSimple.__init__ (self, uid, orient, height)
		self.height = height
		icon = gdk.pixbuf_new_from_file(os.path.dirname (__file__) + '/images/twc-logo.png')
		self.set_temp_icon (icon)
		self.title = awn.awn_title_get_default()
		self.dialog = awn.AppletDialog (self)
		self.connect ("button-press-event", self.button_press)
		self.connect ("enter-notify-event", self.enter_notify)
		self.connect ("leave-notify-event", self.leave_notify)
		self.dialog.connect ("focus-out-event", self.dialog_focus_out)
		self.timer = gobject.timeout_add(self.polling_frequency,self.update_weather)
		self.forecast_timer = gobject.timeout_add(7200000,self.update_forecast)
		self.gconf_client = gconf.client_get_default()
		self.gconf_client.notify_add(self.gconf_path, self.config_event)
		self.get_config()
		self.icons = weathericons.WeatherIcons()
		# Setup popup menu
		self.popup_menu = gtk.Menu()
		refresh_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_REFRESH)
		pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
		about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
		self.popup_menu.append(refresh_item)
		self.popup_menu.append(pref_item)
		self.popup_menu.append(about_item)
		refresh_item.connect_object("activate",self.refresh_callback,self)
		pref_item.connect_object("activate",self.pref_callback,self)
		about_item.connect_object("activate",self.about_callback,self)
		refresh_item.show()
		pref_item.show()
		about_item.show()

	def build_forecast_dialog(self):
		self.dialog = awn.AppletDialog (self)
		self.dialog.set_title(_("Forecast"))
		box = gtk.VBox()
		self.forecast_area = weatherdialog.WeatherDialog(self.forecast)
		self.forecast_area.set_size_request(400,140)
		box.pack_start(self.forecast_area,False,False,0)
		box.show_all()
		self.dialog.add(box)

	def config_event(self, gconf_client, *args, **kwargs):
		self.forecast_visible = False
		self.dialog.hide()     
		self.title.hide (self)
		self.get_config()
		self.update_weather()
		self.update_forecast()

	def get_config(self):
		# Location
		self.location = self.gconf_client.get_string(self.gconf_path + "/location")
		if self.location == None:
			self.gconf_client.set_string(self.gconf_path + "/location", "Portland, ME") # My hometown!
			self.location = "Portland ME"
		self.location_code = self.gconf_client.get_string(self.gconf_path + "/location_code")
		if self.location_code == None:
			self.gconf_client.set_string(self.gconf_path + "/location_code", "USME0328") # My hometown!
			self.location_code = "USME0328"
		# Units
		units = self.gconf_client.get_bool(self.gconf_path + "/metric")
		self.gconf_client.set_bool(self.gconf_path + "/metric", units)   # First time through, will be False
		if units == None:
			self.gconf_client.set_bool(self.gconf_path + "/metric", True)  # default to Metric
			units = True
		if units:
			self.units = "Metric"
		else:
			self.units = "Stupid"  # I can say this... I'm American. 
		# Polling Frequency
		self.polling_frequency = self.gconf_client.get_int(self.gconf_path + "/frequency") * 1000 * 60
		if self.polling_frequency == 0:
			self.gconf_client.set_int(self.gconf_path + "/frequency", 30)
			self.polling_frequency = 30 * 1000 * 60
		# Temperature Position, default is 0
		self.temp_position = self.gconf_client.get_int(self.gconf_path + "/temp_position")
		self.gconf_client.set_int(self.gconf_path + "/temp_position", self.temp_position)
		self.open_til_clicked = self.gconf_client.get_bool(self.gconf_path + "/open_til_clicked")
		self.gconf_client.set_bool(self.gconf_path + "/open_til_clicked", self.open_til_clicked)
		return True

	def button_press(self, widget, event):
		if event.button == 3:
			# right click
			self.title.hide(self)
			self.forecast_visible = False
			self.dialog.hide()
			self.popup_menu.popup(None, None, None, event.button, event.time)
		else:
			if self.forecast_visible != True:
				self.forecast_visible = True
				self.title.hide(self)
				self.build_forecast_dialog()
				self.dialog.show_all()
			else:
				self.forecast_visible = False
				self.dialog.hide()     
				self.title.hide(self)

	def refresh_callback(self, widget):
		self.get_conditions()
		self.draw_current_conditions()
		return True

	def pref_callback(self, widget):
		window = weatherconfig.WeatherConfig(self)
		window.set_size_request(400, 225)
		window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		window.set_destroy_with_parent(True)
		icon_name = self.icons.day_icons["0"]
		icon = gdk.pixbuf_new_from_file(icon_name)
		window.set_icon(icon)
		window.show_all()

	def about_callback(self, widget):
		about_dialog = gtk.AboutDialog()
		about_dialog.set_name("Avant Weather Applet")
		about_dialog.set_copyright("Copyright 2007 Mike Desjardins")
		about_dialog.set_comments("A Weather Applet for the Avant Window Navigator.  Weather data provided by weather.com.  Images by Wojciech Grzanka. Additional help from Isaac J.")
		about_dialog.set_authors(["Mike Desjardins", "Isaac J."])		
		about_dialog.set_artists(["Wojciech Grzanka", "Mike Desjardins"])		
		about_dialog.connect("response", lambda d, r: d.destroy())
		about_dialog.show()

	def dialog_focus_out(self, widget, event):
		self.title.hide(self)    

	def enter_notify(self, widget, event):
		self.title.show(self, self.titleText)

	def leave_notify(self, widget, event):
		if self.open_til_clicked == False:
			self.forecast_visible = False
			self.dialog.hide()     
		self.title.hide(self)    

	def update_weather(self):
		self.get_conditions()
		self.draw_current_conditions()
		return True

	def update_forecast(self):
		self.get_forecast()
		return True

	def get_conditions(self):
		url = 'http://xoap.weather.com/weather/local/' + self.location_code + '?cc=*&prod=xoap&par=1048871467&key=12daac2f3a67cb39'
		if self.units == "Metric":
			url = url + '&unit=m'
		try:    
			usock = urllib.urlopen(url)
			xmldoc = minidom.parse(usock)
			usock.close()
			weather_n = xmldoc.getElementsByTagName('weather')[0]
			location_n = weather_n.getElementsByTagName('loc')[0]
			city_n = location_n.getElementsByTagName('dnam')[0]
			self.city = self.getText(city_n.childNodes)
			sunrise_n = xmldoc.getElementsByTagName('sunr')[0]
			self.sunrise = self.getText(sunrise_n.childNodes)
			sunset_n = xmldoc.getElementsByTagName('suns')[0]
			self.sunset = self.getText(sunset_n.childNodes)
			current_condition_n = xmldoc.getElementsByTagName('cc')[0]
			current_desc_n = current_condition_n.getElementsByTagName('t')[0]
			self.current_desc = self.getText(current_desc_n.childNodes)
			current_code_n = current_condition_n.getElementsByTagName('icon')[0]
			self.current_code = self.getText(current_code_n.childNodes)
			current_temp_n = current_condition_n.getElementsByTagName('tmp')[0]
			self.current_temp = self.getText(current_temp_n.childNodes)
			current_temp_feels_n = current_condition_n.getElementsByTagName('flik')[0]
			self.current_temp_feels = self.getText(current_temp_feels_n.childNodes)
			bar_n = current_condition_n.getElementsByTagName('bar')[0]
			bar_read_n = bar_n.getElementsByTagName('r')[0]
			self.bar_read = self.getText(bar_read_n.childNodes)
			bar_desc_n = bar_n.getElementsByTagName('d')[0]
			self.bar_desc = self.getText(bar_desc_n.childNodes)
			wind_n = current_condition_n.getElementsByTagName('wind')[0]
			wind_speed_n = wind_n.getElementsByTagName('s')[0]
			self.wind_speed = self.getText(wind_speed_n.childNodes)
			wind_gust_n = wind_n.getElementsByTagName('gust')[0]
			self.wind_gust = self.getText(wind_gust_n.childNodes)
			wind_dir_n = wind_n.getElementsByTagName('d')[0]
			self.wind_dir = self.getText(wind_dir_n.childNodes)
			humidity_n = current_condition_n.getElementsByTagName('hmid')[0]
			self.humidity = self.getText(humidity_n.childNodes)
			moon_n = current_condition_n.getElementsByTagName('moon')[0]
			moon_phase_n = moon_n.getElementsByTagName('t')[0]
			self.moon_phase = self.getText(moon_phase_n.childNodes)
		except:
			print "Unexpected error: ", sys.exc_info()[0]
			print "Unable to contact weather source"
		return True

	def getText(self,nodelist):
		rc = ""
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc = rc + node.data
		return rc	

	def get_forecast(self):
		url = 'http://xoap.weather.com/weather/local/' + self.location_code + '?dayf=5&prod=xoap&par=1048871467&key=12daac2f3a67cb39'
		if self.units == "Metric":
			url = url + '&unit=m'
		try:
			usock = urllib.urlopen(url)
			xmldoc = minidom.parse(usock)
			usock.close()
			location_n = xmldoc.getElementsByTagName('loc')[0]
			city_n = location_n.getElementsByTagName('dnam')[0]
			city = self.getText(city_n.childNodes)
			forecast_n = xmldoc.getElementsByTagName('dayf')[0]
			day_nodes = forecast_n.getElementsByTagName('day')
			self.forecast = []
			for day in day_nodes:
				day_of_week = day.getAttribute('t')
				day_of_year = day.getAttribute('dt')
				high_temp_n = day.getElementsByTagName('hi')[0]
				high_temp = self.getText(high_temp_n.childNodes)
				low_temp_n = day.getElementsByTagName('low')[0]
				low_temp = self.getText(low_temp_n.childNodes)
				daytime_n = day.getElementsByTagName('part')[0]
				condition_code_n = daytime_n.getElementsByTagName('icon')[0]
				condition_code = self.getText(condition_code_n.childNodes)
				condition_n = daytime_n.getElementsByTagName('t')[0]
				condition = self.getText(condition_n.childNodes)
				precip_n = daytime_n.getElementsByTagName('ppcp')[0]
				precip = self.getText(precip_n.childNodes)
				humidity_n = daytime_n.getElementsByTagName('hmid')[0]
				humidity = self.getText(humidity_n.childNodes)
				wind_n = daytime_n.getElementsByTagName('wind')[0]
				wind_speed_n = wind_n.getElementsByTagName('s')[0]
				wind_speed = self.getText(wind_speed_n.childNodes)
				wind_direction_n = wind_n.getElementsByTagName('t')[0]
				wind_direction = self.getText(wind_direction_n.childNodes)
				wind_gusts_n = wind_n.getElementsByTagName('gust')[0]
				wind_gusts = self.getText(wind_gusts_n.childNodes)
				day_forecast = Forecast(day_of_week, day_of_year, low_temp, high_temp, condition_code, condition, precip, humidity, wind_direction, wind_speed, wind_gusts, city)
				self.forecast.append(day_forecast) 	
		except:
			print "Unexpected error: ", sys.exc_info()[0]
			print "Unable to contact weather source"
		return True

	def draw_rounded_rect(self,ct,x,y,w,h,r = 10):
		#   A****BQ
		#  H      C
		#  *      *
		#  G      D
		#   F****E
		ct.move_to(x+r,y)                      # Move to A
		ct.line_to(x+w-r,y)                    # Straight line to B
		ct.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
		ct.line_to(x+w,y+h-r)                  # Move to D
		ct.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
		ct.line_to(x+r,y+h)                    # Line to F
		ct.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
		ct.line_to(x,y+r)                      # Line to H
		ct.curve_to(x,y,x,y,x+r,y)             # Curve to A
		return

	def draw_current_conditions(self):
		try:
			width,height=self.window.get_size()
			iconName = self.icons.day_icons[self.current_code]
			cs = cairo.ImageSurface.create_from_png(iconName)
			ct = cairo.Context(cs)
			ct.set_source_surface(cs)
			ct.paint()
			if self.temp_position != 7:
				if self.temp_position in (0,1,2):
					temp_y = 47
				else:
					temp_y = 8
				if self.temp_position == 0 or self.temp_position == 3:
					temp_x = 18
				if self.temp_position == 1 or self.temp_position == 4:
					temp_x = 4
				if self.temp_position == 2 or self.temp_position == 5:
					temp_x = 30
				# Text Shadow
				ct.set_line_width(1)
				ct.stroke()
				ct.move_to(temp_x+1,temp_y+1)
				ct.set_source_rgba(0.1,0.1,0.1,.8)
				ct.show_text(self.current_temp + u"\u00B0")
				# White Text
				ct.move_to(temp_x,temp_y)
				ct.set_source_rgb(1,1,1)
				ct.show_text(self.current_temp + u"\u00B0")
			ns = ct.get_target()
			new_icon = self.get_pixbuf_from_surface(ns)
			scaled_icon = new_icon.scale_simple(self.height, self.height, gtk.gdk.INTERP_HYPER) 
			self.set_icon(scaled_icon)
			self.titleText = self.city + ": " + self.current_desc + ", " + self.current_temp + u"\u00B0"
			del new_icon
		except:
			print "Unexpected error: ", sys.exc_info()[0]
			print "Unable to update current conditions."

	# Stolen from "BlingSwitcher"
	def get_pixbuf_from_surface(self, surface):
		sio = StringIO()
		surface.write_to_png(sio)
		sio.seek(0)
		loader = gtk.gdk.PixbufLoader()
		loader.write(sio.getvalue())
		loader.close()
		return loader.get_pixbuf()


if __name__ == "__main__":
	awn.init (sys.argv[1:])
	#print "main %s %d %d" % (awn.uid, awn.orient, awn.height)
	applet = App(awn.uid, awn.orient, awn.height)
	awn.init_applet(applet)
	applet.show_all()
	applet.get_conditions()
	applet.get_forecast()
	applet.draw_current_conditions()
	gtk.main()


