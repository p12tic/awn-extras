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
import re
import weatherdialog
import weathercurved
import weathericons
import weatherconfig
import weathertext
import weathermap
import override
import socket

# locale stu
APP="awn-weather-applet"
DIR=os.path.dirname(__file__) + '/locale'
import locale
import gettext
#locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

socket.setdefaulttimeout(15)

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
	curved_dialog = False
	locale_lang = "en"
	img_file = ""

	# Default only - we fetch the "real" answer from GConf
	location = "Portland ME"

	# Default only - we fetch the "real" answer from GConf
	units = "Imperial"

	# Default only - we fetch the "real" answer from GConf
	polling_frequency = 30 * 2
	
	# Counts the number of minutes until the next attempted fetch.
	countdown = 0
	
	def __init__(self, uid, orient, height):
		awn.AppletSimple.__init__(self, uid, orient, height)
		self.height = height
		# Implementation of awn-effects
		self.effects = self.get_effects()
		icon = gdk.pixbuf_new_from_file_at_scale(os.path.dirname(__file__)+'/images/twc-logo.png', -1, height, True)
		self.set_temp_icon(icon)
		self.title = awn.awn_title_get_default()
		self.dialog = awn.AppletDialog(self)
		#self.dialog = override.Dialog(self)
		self.connect("button-press-event", self.button_press)
		self.connect("enter-notify-event", self.enter_notify)
		self.connect("leave-notify-event", self.leave_notify)
		self.dialog.connect("focus-out-event", self.dialog_focus_out)
		gobject.timeout_add(1,self.download_first_map)
		self.gconf_client = gconf.client_get_default()
		self.gconf_client.notify_add(self.gconf_path, self.config_event)
		self.get_config()
		self.timer = gobject.timeout_add(30000,self.twice_per_minute)		
		self.forecast_timer = gobject.timeout_add(7200000,self.update_forecast)
		self.icons = weathericons.WeatherIcons()
		# Setup popup menu
		self.popup_menu = gtk.Menu()
		refresh_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_REFRESH)
		map_item = gtk.MenuItem("View Weather Map")
		pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
		about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
		self.popup_menu.append(refresh_item)
		self.popup_menu.append(map_item)
		self.popup_menu.append(pref_item)
		self.popup_menu.append(about_item)
		refresh_item.connect_object("activate",self.refresh_callback,self)
		pref_item.connect_object("activate",self.pref_callback,self)
		about_item.connect_object("activate",self.about_callback,self)
		map_item.connect_object("activate",self.map_callback,self)
		refresh_item.show()
		map_item.show()
		pref_item.show()
		about_item.show()
		try:
			self.locale_lang = locale.getdefaultlocale()[0][0:2]
		except:
			print "locale not set"


	def build_forecast_dialog(self):
		if self.curved_dialog == True:
			self.dialog = override.Dialog(self)
			#dialog = awn.AppletDialog(self)
			self.forecast_area = weathercurved.WeatherDialog(self.forecast)
			box = gtk.VBox()
			self.forecast_area.set_size_request(450,160)
			box.pack_start(self.forecast_area,False,False,0)
			box.show_all()
			self.dialog.add(box)
		else:
			self.dialog = awn.AppletDialog(self)
			self.dialog.set_title(_("Forecast"))
			box = gtk.VBox()
			self.forecast_area = weatherdialog.WeatherDialog(self.forecast)
			self.forecast_area.set_size_request(450,160)
			box.pack_start(self.forecast_area,False,False,0)
			box.show_all()
			self.dialog.add(box)


	def config_event(self, gconf_client, *args, **kwargs):
		self.forecast_visible = False
		self.dialog.hide()     
		self.title.hide(self)
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
		self.polling_frequency = self.gconf_client.get_int(self.gconf_path + "/frequency") * 2
		if self.polling_frequency == 0:
			self.gconf_client.set_int(self.gconf_path + "/frequency", 30)
			self.polling_frequency = 30 * 2
		# Temperature Position, default is 0
		self.temp_position = self.gconf_client.get_int(self.gconf_path + "/temp_position")
		self.gconf_client.set_int(self.gconf_path + "/temp_position", self.temp_position)
		self.open_til_clicked = self.gconf_client.get_bool(self.gconf_path + "/open_til_clicked")
		self.gconf_client.set_bool(self.gconf_path + "/open_til_clicked", self.open_til_clicked)
		# Curved Look
		self.curved_dialog = self.gconf_client.get_bool(self.gconf_path + "/curved_dialog")
		self.gconf_client.set_bool(self.gconf_path + "/curved_dialog", self.curved_dialog)
		return True


	def button_press(self, widget, event):
		try:
			self.map_dialog.hide()
		except AttributeError:
			pass
		if event.button == 3:
			# right click
			self.title.hide(self)
			self.forecast_visible = False
			self.dialog.hide()
			self.popup_menu.popup(None, None, None, event.button, event.time)
		elif event.button == 2:
			self.map_callback(widget)		
		else:
			if self.forecast_visible != True:
				self.forecast_visible = True
				self.title.hide(self)
				# When the dialog is visible the icon will drain color				
				awn.awn_effect_start(self.effects,"desaturate")
				self.build_forecast_dialog()
				self.dialog.show_all()
			else:
				self.forecast_visible = False
				self.dialog.hide()     
				self.title.hide(self)

	def twice_per_minute(self):
		if self.countdown == 0:
			self.countdown = self.polling_frequency
			self.update_weather()
		else:
			self.countdown = self.countdown - 1
		return True
			

	def refresh_callback(self, widget):
		self.get_conditions()
		self.draw_current_conditions()
		return True


	def pref_callback(self, widget):
		window = weatherconfig.WeatherConfig(self)
		window.set_size_request(500, 250)
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
		about_dialog.set_comments("A Weather Applet for the Avant Window Navigator.  Weather data provided by weather.com.  Images by Wojciech Grzanka.")
		about_dialog.set_authors(["Mike Desjardins","Chaz (c.atterly)"])		
		about_dialog.set_artists(["Wojciech Grzanka", "Mike Desjardins"])		
		about_dialog.connect("response", lambda d, r: d.destroy())
		about_dialog.show()


	def map_callback(self, widget):
		# When the map dialog is visible the icon will drain color				
		awn.awn_effect_start(self.effects,"desaturate")
		self.map_dialog = weathermap.WeatherMap(self)
		self.map_dialog.show_all()

		
	def dialog_focus_out(self, widget, event):
		self.title.hide(self)    


	def enter_notify(self, widget, event):
		self.title.show(self, self.titleText)


	def leave_notify(self, widget, event):
		# When the dialog closed, the icon color returns		
		awn.awn_effect_stop(self.effects,"desaturate")
		if self.open_til_clicked == False:
			self.forecast_visible = False
			self.dialog.hide()     
		self.title.hide(self)    


	def update_weather(self):
		self.get_map()
		self.get_conditions()
		self.draw_current_conditions()
		return True


	def update_forecast(self):
		self.get_forecast()
		return True


	def download_first_map(self):
		self.get_map()
		return False;


	def get_conditions(self):
		url = 'http://xoap.weather.com/weather/local/' + self.location_code + '?cc=*&prod=xoap&par=1048871467&key=12daac2f3a67cb39&link=xoap'
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
		url = 'http://xoap.weather.com/weather/local/' + self.location_code + '?dayf=5&prod=xoap&par=1048871467&key=12daac2f3a67cb39&link=xoap'
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
			self.countdown = 0
		return True


	def get_map(self):
		old_map = ""
		if self.map != "":
			old_map = self.map
		try:
			usock = urllib.urlopen('http://www.weather.com/outlook/travel/businesstraveler/map/' + self.location_code)
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
						usock2.close()
			usock.close()
			# practice good hygeine.
			try:
				if old_map != "" and old_map != None:
					os.remove(old_map)
			except:
				pass
		except:
			print "Unable to download weather map. ", sys.exc_info()[0], sys.exc_info()[1]
			self.countdown = 0


	def draw_current_conditions(self):
		try:
			width,height=self.window.get_size()
			iconName = self.icons.day_icons[self.current_code]
			cs = cairo.ImageSurface.create_from_png(iconName)
			ct = cairo.Context(cs)
			ct.set_source_surface(cs)
			ct.paint()
			degrees = self.current_temp + u"\u00B0"
			text, width = self.get_text_width(ct,self.current_temp,128)
			if self.temp_position != 7:
				if self.temp_position in (0,1,2):
					temp_y = 115
				else:
					temp_y = 30
				if self.temp_position == 0 or self.temp_position == 3:
					temp_x = 64 - (width * 2)
				if self.temp_position == 1 or self.temp_position == 4:
					temp_x = 11
				if self.temp_position == 2 or self.temp_position == 5:
					temp_x = 100 - (width * 4)
				# Text Shadow
				ct.set_line_width(1)
				ct.stroke()
				ct.move_to(temp_x+2,temp_y+2)
				ct.set_source_rgba(0.2,0.2,0.2,.8)
				ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)				
				ct.set_font_size(32.0)
				ct.show_text(self.current_temp + u"\u00B0")
				# White Text
				ct.move_to(temp_x,temp_y)
				ct.set_source_rgb(1,1,1)
				ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_NORMAL)				
				ct.show_text(self.current_temp + u"\u00B0")
			ns = ct.get_target()
			new_icon = self.get_pixbuf_from_surface(ns)
			scaled_icon = new_icon.scale_simple(self.height, self.height, gtk.gdk.INTERP_HYPER)
			self.set_icon(scaled_icon)
			# Weather.com's TOS state that I'm not supposed to change their text.  However, I asked them, and they do not
			# supply non-English weather descriptions.  So, if the current locale uses an English language, use weather.com's
			# description... otherwise, use our own.
			if self.locale_lang == "en":
				self.titleText = self.city + ": " + self.current_desc + ", " + self.current_temp + u"\u00B0"
			else:
				self.titleText = self.city + ": " + weathertext.WeatherText.conditions_text[self.current_code] + ", " + self.current_temp + u"\u00B0"			
			del new_icon
		except:
			print "Unexpected error: ", sys.exc_info()[0]
			print "Unable to update current conditions."
			self.countdown = 0

	def get_text_width(self, context, text, maxwidth):
		potential_text = text
		text_width = context.text_extents(potential_text)[2]
		end = -1
		while text_width > maxwidth:
			end -= 1
			potential_text = text[:end] + '...'
			text_width = context.text_extents(potential_text)[2]
		return potential_text, text_width

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
	awn.init(sys.argv[1:])
	#print "main %s %d %d" % (awn.uid, awn.orient, awn.height)
	applet = App(awn.uid, awn.orient, awn.height)
	awn.init_applet(applet)
	applet.show_all()
	applet.get_conditions()
	applet.get_forecast()
	applet.draw_current_conditions()
	gtk.main()


