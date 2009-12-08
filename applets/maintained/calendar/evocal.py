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
import os
import subprocess
import icscal


class EvoCal:

    requires_login = False

    def __init__(self, applet):
        self.applet = applet

    def get_appointments(self, day, url):
        filelist = []
        # Assumes UNIX.
        cmd = 'find ~/.evolution/calendar/local/* -name "*.ics" -print'
        for file in os.popen(cmd).readlines():     # run find command
            name = file[:-1]                       # strip '\n'
            filelist.append(name)
        calendar = icscal.IcsCal(self.applet, filelist)
        return calendar.get_appointments(day, url)

    def open_integrated_calendar(self, when, url):
        dat = "%02d%02d%02d" % (when[0], (when[1] + 1), when[2])
        subprocess.Popen('evolution calendar:///?startdate=%sT120000' % dat,
                         shell=True)
        return
