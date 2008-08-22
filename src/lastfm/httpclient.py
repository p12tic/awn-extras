#!/usr/bin/env python

# Copyright (c) 2007 Tomas Kramar (kramar.tomas@gmail.com), Jonathan Rauprich (joni@noplu.de)
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

import base64
import socket
import string
import lastfmexception
import sys

True = 1
False = 0

class httpclient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.status = None
        self.headers = None
        self.response = None

    def readline(self, s):
        res = ""
        while True:
            try:
                c = s.recv(1)
            except:
                break
            res = res + c
            if c == '\n':
                break
            if not c:
                break
        return res

    def req(self, url):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, self.port))
            s.send("GET " + url + " HTTP/1.0\r\n")
            s.send("Host: " + self.host + "\r\n")
            s.send("\r\n")
    
            line = self.readline(s)
            self.status = string.rstrip(line)
    
            self.headers = {}
            while True:
                line = self.readline(s)
                if not line:
                    break
                if line == "\r\n":
                    break
                tmp = string.split(line, ": ")
                self.headers[tmp[0]] = string.rstrip(tmp[1])
    
            self.response = ""
            while True:
                line = self.readline(s)
                if not line:
                    break
                self.response = self.response + line
            s.close()
        except:
            #print "Unexpected error: ", sys.exc_info()[0]
            #print "Unable to contact last.fm"
            raise lastfmexception.LastFmException(sys.exc_info()[0])

