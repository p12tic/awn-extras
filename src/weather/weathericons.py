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
import os
class WeatherIcons:

	#image_path = os.path.dirname (__file__) + '/images/'
	day_icons = {}
	
	def __init__ (self):
		image_path = os.path.dirname (__file__) + '/images/'

		self.day_icons = {
		"0": image_path + "0.png",					# tornado
		"1": image_path + "1.png",					# tropical storm
		"2": image_path + "2.png",					# hurricane
		"3": image_path + "3.png",					# severe t'storms
		"4": image_path + "4.png",					# t'storms
		"5": image_path + "5.png", 					# mixed rain and snow
		"6": image_path + "6.png",  				# mixed rain and sleet
		"7": image_path + "7.png",  				# mixed precip snow/rain/sleet
		"8": image_path + "8.png",					# freezing drizzle
		"9": image_path + "9.png", 					# drizzle
		"10": image_path + "10.png", 				# freezing rain
		"11": image_path + "11.png", 				# showers
		"12": image_path + "12.png", 				# showers
		"13": image_path + "13.png",				# snow flurries
		"14": image_path + "14.png", 				# light snow showers
		"15": image_path + "15.png", 				# blowing snow
		"16": image_path + "16.png", 				# snow
		"17": image_path + "17.png",	 			# hail
		"18": image_path + "18.png", 				# sleet
		"19": image_path + "19.png", 				# dust
		"20": image_path + "20.png", 				# fog
		"21": image_path + "21.png", 				# haze
		"22": image_path + "22.png", 				# smoke
		"23": image_path + "23.png", 				# blustery 
		"24": image_path + "24.png", 				# windy
		"25": image_path + "25.png",	 			# cold
		"26": image_path + "26.png", 				# cloudy
		"27": image_path + "27.png", 				# mostly cloudy/overcast (night)
		"28": image_path + "28.png", 				# mostly cloudy
		"29": image_path + "29.png",				# partly cloudy (night)
		"30": image_path + "30.png", 				# partly cloudy
		"31": image_path + "31.png", 				# clear night
		"32": image_path + "32.png", 				# clear day
		"33": image_path + "33.png",	 			# fair (night)
		"34": image_path + "34.png", 				# fair
		"35": image_path + "35.png",				# mixed rain and hail
		"36": image_path + "36.png", 				# hot
		"37": image_path + "37.png",				# isolated t'storms
		"38": image_path + "38.png", 				# scattered t'storms
		"39": image_path + "39.png", 				# scattered t'storms
		"40": image_path + "40.png", 				# scattered showers
		"41": image_path + "41.png", 				# heavy snow
		"42": image_path + "42.png",				# scattered snow showers
		"43": image_path + "43.png", 				# heavy snow
		"44": image_path + "44.png", 				# partly cloudy
		"45": image_path + "45.png", 				# t'showers (night)
		"46": image_path + "46.png", 				# snow showers (night)
		"47": image_path + "47.png", 				# isolated t'storms (night)
		"na": image_path + "twc-logo.png", 	# When data cannot be retrieved
		}
