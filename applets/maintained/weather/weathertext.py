#!/usr/bin/python
# Copyright (c) 2008:
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#     Please do not email the above person for support. The 
#     email address is only there for license/copyright purposes.
# Copyright (c) 2010 Gabor Karsay <gabor.karsay@gmx.at>
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
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.


# This is needed for i18n support.
#
# intltool extracts the strings and makes them translatable. It should cover
# all possible strings that are delivered by weather.com. If you find missing
# strings, please insert them in alphabetical order.
#
# The program is not intended to be executed, however, it provides a small
# test routine in case it's run from command line. 


from awn.extras import _

def N_(message): return message

conditions = [
    N_("Blowing Snow"),
    N_("Blustery"), 
    N_("Clear"),
    N_("Cloudy"),
    N_("Cold"),
    N_("Drizzle"),
    N_("Dust"),
    N_("Fair"),
    N_("Fog"),
    N_("Freezing Drizzle"),
    N_("Freezing Rain"),
    N_("Hail"),
    N_("Haze"),
    N_("Heavy Snow"),
    N_("Hot"),
    N_("Hurricane"),
    N_("Isolated Thunderstorms"),
    N_("Light Drizzle"),
    N_("Light Rain Shower"),
    N_("Light Rain with Thunder"),
    N_("Light Snow"),
    N_("Light Snow Showers"),
    N_("Mist"),
    N_("Mixed Precipitation"),
    N_("Mixed Rain and Hail"),
    N_("Mixed Rain and Sleet"),
    N_("Mixed Rain and Snow"),
    N_("Mostly Cloudy"),
    N_("N/A"),
    N_("Partly Cloudy"),
    N_("Scattered Showers"),
    N_("Scattered Snow Showers"),
    N_("Scattered Thunderstorms"),
    N_("Severe Thunderstorms"),
    N_("Showers"),
    N_("Showers in the Vicinity"),
    N_("Sleet"),
    N_("Smoke"),
    N_("Snow"),
    N_("Snow and Fog"),
    N_("Snow Flurries"),
    N_("Snow Showers"),
    N_("Thunder Showers"),
    N_("Thunderstorms"),
    N_("Tornado"),
    N_("Tropical Storm"),
    N_("Windy"),
]

forecast = [
    # Please keep translation short, approx. 12 characters
    N_("AM Clouds / PM Sun"),
    # Please keep translation short, approx. 12 characters
    N_("AM Drizzle"),
    # Please keep translation short, approx. 12 characters
    N_("AM Drizzle / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("AM Fog / PM Sun"),
    # Please keep translation short, approx. 12 characters
    N_("AM Light Rain"),
    # Please keep translation short, approx. 12 characters
    N_("AM Light Snow"),
    # Please keep translation short, approx. 12 characters
    N_("AM Rain / Snow"),
    # Please keep translation short, approx. 12 characters
    N_("AM Rain / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("AM Showers"), 
    # Please keep translation short, approx. 12 characters
    N_("AM Snow Showers"), 
    # Please keep translation short, approx. 12 characters
    # T-Showers = Thunder Showers
    N_("AM T-Showers"),
    # Please keep translation short, approx. 12 characters
    # T-Storms = Thunderstorms
    N_("AM T-Storms"),
    # Please keep translation short, approx. 12 characters
    N_("Few Showers"), 
    # Please keep translation short, approx. 12 characters
    N_("Heavy Rain"), 
    # Please keep translation short, approx. 12 characters
    # T-Storms = Thunderstorms
    N_("Isolated T-Storms"),
    # Please keep translation short, approx. 12 characters
    N_("Light Rain"),
    # Please keep translation short, approx. 12 characters
    N_("Light Rain / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("Light Snow / Fog"),
    # Please keep translation short, approx. 12 characters
    N_("Mostly Sunny"),
    # Please keep translation short, approx. 12 characters
    N_("Partly Cloudy / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("PM Drizzle"),
    # Please keep translation short, approx. 12 characters
    N_("PM Light Rain"), 
    # Please keep translation short, approx. 12 characters
    N_("PM Light Snow"), 
    # Please keep translation short, approx. 12 characters
    N_("PM Rain"), 
    # Please keep translation short, approx. 12 characters
    N_("PM Rain / Snow"), 
    # Please keep translation short, approx. 12 characters
    N_("PM Showers"), 
    # Please keep translation short, approx. 12 characters
    # T-Showers = Thunder Showers
    N_("PM T-Showers"),
    # Please keep translation short, approx. 12 characters
    # T-Storms = Thunderstorms
    N_("PM T-Storms"),
    # Please keep translation short, approx. 12 characters
    N_("Rain"),
    # Please keep translation short, approx. 12 characters
    N_("Rain / Snow"),
    # Please keep translation short, approx. 12 characters
    N_("Rain / Snow Showers"),
    # Please keep translation short, approx. 12 characters
    N_("Rain / Thunder"),
    # Please keep translation short, approx. 12 characters
    N_("Rain / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("Scattered Showers / Wind"),
    # Please keep translation short, approx. 12 characters
    # T-Storms = Thunderstorms
    N_("Scattered T-Storms"),
    # Please keep translation short, approx. 12 characters
    N_("Showers / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("Snow Shower"),
    # Please keep translation short, approx. 12 characters
    N_("Snow to Rain"),
    # Please keep translation short, approx. 12 characters
    N_("Snow to Wintry Mix"),
    # Please keep translation short, approx. 12 characters
    N_("Snow / Wind"),
    # Please keep translation short, approx. 12 characters
    N_("Sunny"),
    # Please keep translation short, approx. 12 characters
    N_("Sunny / Wind"),
    # Please keep translation short, approx. 12 characters
    # T-Showers = Thunder Showers
    N_("T-Showers"),
]

days = [
    N_("Monday"),
    N_("Tuesday"),
    N_("Wednesday"),
    N_("Thursday"),
    N_("Friday"),
    N_("Saturday"),
    N_("Sunday"),
]


# Test routine

print "Translation status for weekdays (C : your locale)"
for a in days:
    print "%s : %s" % (a, _(a))

print "\nTranslation status for weather conditions (C : your locale)"
for a in conditions:
    print "%s : %s" % (a, _(a))

print "\nTranslation status for forecast (C : your locale)"
for a in forecast:
    print "%s : %s" % (a, _(a))

