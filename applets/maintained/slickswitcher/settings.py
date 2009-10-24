#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import awn

from desktopagnostic.config import GROUP_DEFAULT


class Settings():
    def __init__(self, applet):
        #Get an AwnConfigClient
        self.config = awn.config_get_default_for_applet(applet)
        
        #Get a dictionary
        self.dict = {}
        self.__getitem__ = self.dict.__getitem__
        
        #List of strings to get
        list_of_strings = ['icon_border', 'normal_border', 'active_border', \
            'window_main', 'window_border', 'shine_top', 'shine_bottom', \
            'shine_hover_top', 'shine_hover_bottom', 'text_color', 'shadow_color', \
            'custom_back', 'custom_border']
        
        #List of integers to get
        list_of_integers = ['width', 'height']
        
        #List of booleans to get
        list_of_booleans = ['use_custom']
        
        #Get all the values
        #Strings
        for string in list_of_strings:
            self[string] = self.config.get_value(GROUP_DEFAULT, string)
        #Integers
        for integer in list_of_integers:
            self[integer] = self.config.get_value(GROUP_DEFAULT, integer)
            if integer == 'width' and self[integer] < 24:
                self[integer] = 160
            elif integer == 'height' and self[integer] < 24:
                self[integer] = 110
        #Booleans
        for boolean in list_of_booleans:
            self[boolean] = self.config.get_value(GROUP_DEFAULT, boolean)
        
        #Connect to changes to all the values
        for value in list_of_strings + list_of_integers + list_of_booleans:
            self.config.notify_add(GROUP_DEFAULT, value, self.value_changed)
    
    def value_changed(self, group, key, value):
        self.dict[key] = value
    
    def __setitem__(self, key, value, internal=False):
        if key in self.dict and value != self.dict[key]:
            self.config.set_value(GROUP_DEFAULT, key, value)

        self.dict[key] = value
