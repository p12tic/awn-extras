#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is an implementation of the OWA plugin for a calendar applet for
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
import re
import socket
import urllib
import urlparse
import urllib2
import webbrowser
from awn.extras import _

__version__ = '0.1'
__author__ = 'Adrian Holovaty <holovaty@gmail.com>'

socket.setdefaulttimeout(15)


class OwaCal:

    requires_login = True

    def __init__(self, applet):
        self.applet = applet
        self.domain = self.applet.url

    def get_appointments(self, day, url):
        (year, month, date) = day
        # this creates a password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        theurl = '%s/exchange/%s/calendar/' % (url, self.applet.username) + \
                 '?Cmd=contents&view=daily&d=%s&m=%s&y=%s' % \
                 (date, month, year)
        # because we have put None at the start it will always use this
        # username/password combination
        passman.add_password(None, theurl, self.applet.username,
                             self.applet.crypt(self.applet.password,
                                               -17760704))
        # create the AuthHandler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        theurl = theurl.replace('\n', '')
        # build an 'opener' using the handler we've created
        opener = urllib2.build_opener(authhandler)
        # you can use the opener directly to open URLs
        # *or* you can install it as the default opener so that all calls to
        # urllib2.urlopen use this opener
        urllib2.install_opener(opener)
        post_data = urllib.urlencode({
            'destination': urlparse.urljoin(self.domain, 'exchange'),
            'flags': '0',
            'username': self.applet.username,
            'password': self.applet.crypt(self.applet.password, -17760704),
            'SubmitCreds': 'Log On',
            'forcedownlevel': '0',
            'trusted': '4',
        })
        f = opener.open(theurl, post_data)
        html = f.read()
        # I'm terrible at regular expressions, so I'm sure that there is a far
        # better way to do this:
        tableexp = re.compile("<TABLE class=\"calDayVwTbl\".*</TABLE>")
        tablehtml = tableexp.search(html)
        htmlsplitter = re.compile('(<.*?>)')
        splitted = htmlsplitter.split(tablehtml.group())
        result = []
        for token in splitted:
            titles = re.compile("<TD TITLE=\"[0-9]")  #"
            titlehtml = titles.match(token)
            textre = re.compile("\".*\"")
            if titlehtml != None:
                text = textre.search(token)
                result.append(["", text.group().replace("\"", "")])  #"
        if len(result) == 0:
            result.append([None, _("No appointments")])
        return result

    def open_integrated_calendar(self, when, url):
        dat = "&d=%02d&m=%02d&y=%04d" % (when[2], (when[1] + 1), when[0])
        url = url + "/exchange/calendar/?Cmd=contents&view=daily" + dat
        webbrowser.open_new_tab(url)
