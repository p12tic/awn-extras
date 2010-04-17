#!/usr/bin/python
#coding: utf-8
#
#   Copyright 2008-2010 Grega Podlesek <grega.podlesek@gmail.com>
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
from units import UNIT_VOLT


class VoltValue(SensorValue):

    def __init__(self):
        SensorValue.__init__(self)

        self.raw_value = 0
        self.raw_high_value = 12
        self.raw_low_value = -12
        self.unit = UNIT_VOLT
