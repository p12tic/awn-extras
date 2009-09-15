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

from awn.extras import _

# Units
UNIT_CELSIUS = 0
UNIT_FAHRENHEIT = 1
UNIT_KELVIN = 2
UNIT_VOLT = 3
UNIT_RPM = 4

# Unit short strings
UNIT_STR = [u"˚C", u"˚F", u"˚K", "V", "rpm"]

# Unit long strings
UNIT_STR_LONG = [_("Celsius"), _("Fahrenheit"),
                 _("Kelvin"), _("Volt"), _("rpm")]
