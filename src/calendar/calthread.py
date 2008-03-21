#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is a thread that polls for calendar updates, and caches them.
#
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
import os, sys
import threading
import time

class CalThread(threading.Thread):

	list = dict()
	applet = None
	cache_ready = False
	die = False
	refresh_counter = 0

	def __init__(self,applet):
		super(CalThread, self).__init__()
		self.applet = applet
		self.die = False

	def days_in_month(self,month,year):
		days = 31
		if month in (4,6,9,11):
			days = 30
		elif month == 2:
			if year % 4 == 0:
				days = 29
			else:
				days = 28
		return days

	def kill(self):
		self.die = True

	def run(self):
		while self.die == False:
			if self.refresh_counter % 60 == 0:
				#print "fetching update"
				self.fetch()
			#print "sleeping for 5 seconds", self.refresh_counter
			time.sleep(5)
			self.refresh_counter = self.refresh_counter + 1

	def check_cache(self,cal_date):
		if self.cache_ready == True:
			if cal_date in self.list:
				return True
		return False
		
	def get_appointments(self,cal_date):
		return self.list[cal_date]
		
	def get_days(self,year,month):
		days = self.days_in_month(month,year)
		x=1
		busy_day = []
		while x <= days:
			if self.list[year,month,x][0][0] != None:
				busy_day.append(x)
			x=x+1
		return busy_day

	def fetch(self):
		if self.applet.integration != None:
			year,month,day,hour,minute,sec,msec,who,cares = time.localtime()
			prev_month = month - 1
			prev_year = year		
			if month == 0:
				month = 12
				prev_year = prev_year - 1
			next_month = month + 1
			next_year = year
			if next_month == 13:
				next_month = 1
				next_year = year + 1
			scan = [(prev_year,prev_month),(year,month),(next_year,next_month)]
			temp_list = dict()
			for y,m in scan:
				days = self.days_in_month(m,y)
				x = 1
				while x <= days:
					if self.die == True:
						print "Thread terminating"
						exit()
					cal_date = (y,m,x)
					if self.applet.integ_text == "Google Calendar":
						time.sleep(2) # so google doesn't think we're DoS'ing them and require a captcha, and to use less CPU
					try:			
						temp_list[cal_date] = self.applet.integration.get_appointments(cal_date,self.applet.url)
					except:
						print "Login error: ", sys.exc_info()[0], sys.exc_info()[1]
					finally:
						x=x+1
			self.list = temp_list
			self.cache_ready = True

