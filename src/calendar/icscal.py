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
from datetime import date
import subprocess
import calendarprefs
import fileinput
import re
import string
# This will allow me to distribute google data services with the calendar applet, which might (?) be a
# non-Pythonic, bad idea.  
#here = os.getcwd()
sys.path.append(os.path.abspath(os.path.dirname(__file__)) + "/icalendar")
from datetime import datetime
from icalendar import Calendar, Event, UTC, vDatetime
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
		year,month,x=day
		for file in self.files:
			cal = Calendar.from_string(open(file,'rb').read())
			for component in cal.walk():
				if component.name == "VEVENT":
					# Need to figure out if this thing is for the current day
					if component['rrule'] != None:
						print "RRULE Exists"
					dtstart = component.decoded('dtstart')
					dtend = component.decoded('dtend')
					summary = str(component['summary'])
					text = dtstart.strftime("%I:%M%p") + "-" + dtend.strftime("%I:%M%p") + " " + summary
					if dtstart.year == year and dtstart.month == month and dtstart.day == x:
						self.events.append([dtstart.strftime("%H:%M"),text])
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

					
