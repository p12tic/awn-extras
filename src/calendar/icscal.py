#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is an implementation of the google plugin for a calendar applet for 
# Avant Window Navigator.
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
from StringIO import StringIO
import datetime
import time
import subprocess
import calendarprefs
import fileinput
import re
import string

# locale stuff
APP="awn-calendar"
DIR="locale"
import locale
import gettext
#locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class IcsCal:

	events = []
	get_start = False
	get_end = False
	in_event = False
	summary = None
	start = None
	end = None
	requires_login = False

	#def __init__(self,applet,files):
	def __init__(self,applet,files):
		self.applet = applet
		self.files = files

	def get_appointments(self, day, url):
		self.events = []
		for line in fileinput.input(self.files):
			if line[:12] == "BEGIN:VEVENT":
				self.in_event = True
			elif line[:10] == "END:VEVENT":
				self.in_event = False
				if self.start != None and self.end != None and self.summary != None:
					# Determine if this thing is even for the current day
					if day == (int(self.start[:4]), int(self.start[4:6]), int(self.start[6:8])):
						starttext = self.convert_time_to_text(self.start)
						endtext = self.convert_time_to_text(self.end)
						eventtext = starttext + "-" + endtext + " " + self.summary
						self.events.append([self.start,eventtext])
						self.start = None
						self.end = None
						self.summary = None
			if self.get_start == True:
				ex = re.compile("[0-9]{8}T[0-9]{6}$")
				if re.search(ex,line) != None:
					self.start = line.replace(' ','')
					self.get_start = False
			if self.get_end == True:
				ex = re.compile("[0-9]{8}T[0-9]{6}$")
				if re.search(ex,line) != None:
					self.end = line.replace(' ','')
					self.get_end = False
			if line[:7] == "DTSTART" and self.in_event == True:
				# Need to determine if the start time is on this line, or the next.  Evo puts it on a separate line :(
				ex = re.compile("[0-9]{8}T[0-9]{6}$")
				if re.search(ex, line) != None:
					pos = string.find(line,':')
					if pos > 0:
						self.start = line[pos+1:-1]
				else:
					# First, see if it's an all day event.
					ex = re.compile("[0-9]{8}$")
					if re.search(ex,line) != None:
						# All-day.
						pos = string.find(line,':')
						if pos > 0:
							self.start = line[pos+1:-1]						
							self.start = self.start + "T000000" 
					else:
						ex = re.compile("[:;]$")
						if re.search(ex,line) != None:
							self.get_start = True
						else:
							# ???
							self.start = "000000000"
			#else:
			#	self.get_start = False
			if line[:5] == "DTEND" and self.in_event == True:
				# Need to determine if the end time is on this line, or the next.  Evo puts it on a separate line :(
				ex = re.compile("[0-9]{8}T[0-9]{6}$")
				if re.search(ex,line) != None:
					pos = string.find(line,':')
					if pos > 0:
						self.end = line[pos+1:-1]
				else:
					# First, see if it's an all day event.
					ex = re.compile("[0-9]{8}$")
					if re.search(ex,line) != None:
						# All-day.
						pos = string.find(line,':')
						if pos > 0:
							self.end = line[pos+1:-1]						
							self.end = self.end + "T235959" 
					else:
						ex = re.compile("[:;]$")
						if re.search(ex,line) != None:
							self.get_end = True
						else:
							# ???
							self.end = "000000000"
			if line[:8] == "SUMMARY:":
				self.summary = line[8:-1]
		self.events.sort()
		if len(self.events) == 0:
			self.events.append([None,_("No appointments")])
		fileinput.close()		
		return self.events
		
	def convert_time_to_text(self, when):
		hour = int(when[9:11])
		mins = when[11:13]
		text = ""						
		if self.applet.twelve_hour_clock == True:														
			trail = "am"
			if hour >= 12:
				trail = "pm"
			hour = hour % 12
			if hour == 0:
				hour = 12
			text = str(hour) + ":" + mins + trail
		else:
			text = when[9:11] + ":" + when[11:13]
		return text

					
