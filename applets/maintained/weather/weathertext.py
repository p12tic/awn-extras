#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2008:
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#
# This is a weather applet for Avant Window Navigator.
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

# mrooney: I am maintaining this file for now but it doesn't seem to be needed.
#   the XML feed gives us a description already so the mapping below isn't necessary,
#   and the gettext wrapping can be done in weather.py.

conditions = {
    "0": _("Tornado"),
    "1": _("Tropical Storm"),
    "2": _("Hurricane"),
    "3": _("Severe Thunderstorms"),
    "4": _("Thunderstorms"),
    "5": _("Mixed Rain and Snow"),
    "6": _("Mixed Rain and Sleet"),
    "7": _("Mixed Precipitation"),
    "8": _("Freezing Drizzle"),
    "9": _("Drizzle"),
    "10": _("Freezing Rain"),
    "11": _("Showers"),
    "12": _("Showers"),
    "13": _("Snow Flurries"),
    "14": _("Light Snow Showers"),
    "15": _("Blowing Snow"),
    "16": _("Snow"),
    "17": _("Hail"),
    "18": _("Sleet"),
    "19": _("Dust"),
    "20": _("Fog"),
    "21": _("Haze"),
    "22": _("Smoke"),
    "23": _("Blustery"), 
    "24": _("Windy"),
    "25": _("Cold"),
    "26": _("Cloudy"),
    "27": _("Mostly Cloudy"),
    "28": _("Mostly Cloudy"),
    "29": _("Partly Cloudy"),
    "30": _("Partly Cloudy"),
    "31": _("Clear"),
    "32": _("Clear"),
    "33": _("Fair"),
    "34": _("Fair"),
    "35": _("Mixed Rain and Hail"),
    "36": _("Hot"),
    "37": _("Isolated Thunderstorms"),
    "38": _("Scattered Thunderstorms"),
    "39": _("Scattered Thunderstorms"),
    "40": _("Scattered Showers"),
    "41": _("Heavy Snow"),
    "42": _("Scattered Snow Showers"),
    "43": _("Heavy Snow"),
    "44": _("Partly Cloudy"),
    "45": _("Thunder Showers"),
    "46": _("Snow Showers"),
    "47": _("Isolated Thunderstorms"),
    "na": _("N/A")
}
    
days = {
    "Monday": _("Monday"),
    "Tuesday": _("Tuesday"),
    "Wednesday": _("Wednesday"),
    "Thursday": _("Thursday"),
    "Friday": _("Friday"),
    "Saturday": _("Saturday"),
    "Sunday": _("Sunday")
}
