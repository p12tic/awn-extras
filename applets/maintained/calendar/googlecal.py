#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#     Please do not email the above person for support. The 
#     email address is only there for license/copyright purposes.
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
import sys
import datetime
import awn
awn.check_dependencies(globals(), 'gdata')
import gdata.calendar.service
import gdata.service
import gdata.calendar
import webbrowser
from awn.extras import _

CAPTCHA_URI = 'https://www.google.com/accounts/DisplayUnlockCaptcha' + \
              '?service=calendar'


class GoogleCal:

    events = []
    requires_login = True

    def __init__(self, applet):
        self.applet = applet

    def get_appointments(self, day, url):
        self.cal_client = gdata.calendar.service.CalendarService()
        self.cal_client.email = self.applet.username
        self.cal_client.password = self.applet.crypt(self.applet.password,
                                                     -17760704)
        try:
            self.cal_client.ProgrammaticLogin()
        except gdata.service.CaptchaRequired:
            # I'm not sure what to do about these.  :/
            print 'Google is saying CAPTCHA required... don\'t know what I', \
                  'should do about these... sleep???', sys.exc_info()[0], \
                  sys.exc_info()[1]
            print 'User can go to %s to unlock' % CAPTCHA_URI
        query = gdata.calendar.service.CalendarEventQuery('default', 'private',
                                                          'full')
        (year, month, date) = day
        cal_date_start = datetime.datetime(year, month, date, 0, 0, 0)
        cal_date_end = datetime.datetime(year, month, date, 23, 59, 59)
        query.start_min = cal_date_start.strftime("%Y-%m-%dT%H:%m:%S")
        query.start_max = cal_date_end.strftime("%Y-%m-%dT%H:%m:%S")
        feed = self.cal_client.CalendarQuery(query)
        self.events = []
        for j, an_event in enumerate(feed.entry):
            if an_event.title.text != None:
                for a_when in an_event.when:
                    if len(a_when.start_time) <= 10:
                        start_text = "12:00am"
                    else:
                        start_text = \
                            self.convert_time_to_text(a_when.start_time)
                    if len(a_when.end_time) <= 10:
                        end_text = "11:59pm"
                    else:
                        end_text = self.convert_time_to_text(a_when.end_time)
                    event_text = '%s - %s: %s' % (start_text, end_text,
                                                  an_event.title.text)
                    #print "event_text: %s" % (event_text)
                    event = ([a_when.start_time, event_text])
                    self.events.append(event)
        # The list comes to us from Google sorted in the order in which the
        # events were added.  Re-sort it here by start time.
        if len(self.events) == 0:
            self.events.append([None, _("No appointments.")])
        self.events.sort()
        return self.events

    def open_integrated_calendar(self, when, url):
        dat = "%02d%02d%02d" % (when[0], (when[1] + 1), when[2])
        url ="http://www.google.com/calendar/render?pli=1\&date=" + dat
        webbrowser.open_new_tab(url)

    def convert_time_to_text(self, when):
        hour = int(when[11:13])
        mins = when[13:16]
        text = ""
        if self.applet.twelve_hour_clock == True:
            trail = "am"
            if hour >= 12:
                trail = "pm"
            hour = hour % 12
            if hour == 0:
                hour = 12
            text = str(hour) + mins + trail
        else:
            text = when[11:16]
        return text
