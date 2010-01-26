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

class SensorValue(object):

    def __init__(self):
        self.raw_value = None
        self.raw_high_value = None
        self.raw_low_value = None

    @property
    def value(self):
        """Current value"""
        return self.raw_value

    def low_value():
        doc = """Low value limit (at which alarm triggers). Also used for
        minimum needle angle in applet icon."""

        def fget(self):
            return self.raw_low_value

        def fset(self, value):
            self.raw_low_value = value

        return locals()

    low_value = property(**low_value())

    def high_value():
        doc = """High value limit (at which alarm triggers). Also used for
        maximum needle angle in applet icon."""

        def fget(self):
            return self.raw_high_value

        def fset(self, value):
            self.raw_high_value = value

        return locals()

    high_value = property(**high_value())
