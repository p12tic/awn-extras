#!/usr/bin/python
#coding: utf-8
#
#   Copyright 2008-2009 Grega Podlesek <grega.podlesek@gmail.com>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#   MA 02110-1301, USA.

from sensorvalue import SensorValue
from units import *


class TempValue(SensorValue):
    
    def __init__(self):
        SensorValue.__init__(self)
        
        self.raw_value = -273
        self.raw_high_value = 60
        self.raw_low_value = 20
        self.unit = UNIT_CELSIUS
    
    @property
    def value(self):
        """Current value"""
        return self.to_unit(int(self.raw_value))
    
    @property
    def low_value(self):
        return self.to_unit(self.raw_low_value)
    
    @low_value.setter
    def low_value(self, low_value):
        self.raw_low_value = self.from_unit(int(low_value))
    
    @property
    def high_value(self):
        return self.to_unit(self.raw_high_value)
    
    @high_value.setter
    def high_value(self, high_value):
        self.raw_high_value = self.from_unit(int(high_value))

    def to_unit(self, value):
        if self.unit is UNIT_FAHRENHEIT:
            return int(value * 9/5 + 32)
        elif self.unit is UNIT_KELVIN:
            return value + 273
        return value
    
    def from_unit(self, value):
        if self.unit is UNIT_FAHRENHEIT:
            return int((value - 32) * 5/9)
        elif self.unit is UNIT_KELVIN:
            return value - 273
        return value
