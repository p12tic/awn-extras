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
import datetime
import vobject
from dateutil.rrule import rrulestr
# locale stuff
APP = "awn-calendar"
DIR = "locale"
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

    def __init__(self, applet, files):
        self.applet = applet
        self.files = files

    def add_event(self, start, end, summary):
        text = '%s-%s %s' % (start.strftime("%I:%M%p"),
                             end.strftime("%I:%M%p"),
                             summary)
        self.events.append([start.strftime("%H:%M"), text])

    def get_appointments(self, date, url):
        dtdate = datetime.date(date[0], date[1], date[2])
        self.events = []
        for filename in self.files:
            cal = vobject.readOne(open(filename, 'rb'))
            for component in cal.components:
                if component.name == 'VEVENT':
                    dtstart = component.dtstart.value
                    dtend = component.dtend.value
                    summary = component.summary.value
                    # See if this is a recurring appointment
                    if hasattr(component, 'rrule'):
                        # Add only if an instance happens to be today.
                        [self.add_event(dtstart, dtend, summary)
                         for appt in rrulestr(str(component.rrule.value))
                         if appt.date() == dtdate]
                    elif dtstart.date == dtdate:
                        self.add_event(dtstart, dtend, summary)
        if len(self.events) == 0:
            self.events.append([None, _("No appointments")])
        else:
            self.events.sort()
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
