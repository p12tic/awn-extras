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

import awn
import md5

class LastFmConfiguration:
    #username
    #password
    #icon
    
    def __init__(self):
        self.config = awn.Config('lastfm', None)
    
    def set_username(self, value):
        self.config.set_string(awn.CONFIG_DEFAULT_GROUP, 'username', value)
        return value
        
    def get_username(self):
        username = self.config.get_string(awn.CONFIG_DEFAULT_GROUP, 'username')
        if username is None:
            username = ''
        return username
    
    def set_password(self, value):
        md5_password = md5.md5(value).hexdigest()
        self.config.set_string(awn.CONFIG_DEFAULT_GROUP, 'password', md5_password)
        return md5_password
    
    def get_password(self):
        passwd = self.config.get_string(awn.CONFIG_DEFAULT_GROUP, 'password')
        if passwd is None:
            passwd = ''
            
        return passwd
    
    def get_icon(self):
        icon = self.config.get_string(awn.CONFIG_DEFAULT_GROUP, 'icon')
        if icon is None:
            icon = 'red.ico'
        return icon
    
    def set_icon(self, value):
        self.config.set_string(awn.CONFIG_DEFAULT_GROUP, 'icon', value)
        return value
    
    #def set_last_station_
