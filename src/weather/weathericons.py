#!/usr/bin/python
# Copyright (C) 2008:
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
# Copyright (C) 2009  onox <denkpadje@gmail.com>
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
# License along with this librarym.  If not, see <http://www.gnu.org/licenses/>

import os

theme_dir = "/usr/share/icons"

moonbeam_theme = os.path.join(os.path.dirname(__file__), "themes/moonbeam")


def get_icon_name(hint):
    hint = int(hint)

    if hint in (32, 34, 36):
        return "weather-clear"
    elif hint in (23, 24, 25, 28, 30, 44):
        return "weather-few-clouds"
    elif hint in (26, ):
        return "weather-overcast"
    elif hint in (5, 6, 7, 8, 9, 10, 11, 12, 45):
        return "weather-showers"
    elif hint in (40, ):
        return "weather-showers-scattered"
    elif hint in (13, 14, 15, 16, 17, 18, 41, 42, 43, 46):
        return "weather-snow"
    elif hint in (19, 20, 21, 22):
        return "weather-fog"
    elif hint in (4, 35, 37, 38, 39, 47):
        return "weather-storm"
    elif hint in (0, 1, 2, 3):
        return "weather-severe-alert"
    elif hint in (31, 33):
        return "weather-clear-night"
    elif hint in (27, 29):
        return "weather-few-clouds-night"


def get_icon(hint, theme):
    if hint == "twc":
        return os.path.join(moonbeam_theme, "twc-logo.png")

    this_is_moonbeam_theme = (theme == "moonbeam")

    if not this_is_moonbeam_theme:
        theme_path = os.path.join(theme_dir, theme, "scalable/status")
    else:
        theme_path = moonbeam_theme

    extension = ".svg" if not this_is_moonbeam_theme else ".png"

    # Special conditional for the extreme weather in moonbeam's Ottawa
    if this_is_moonbeam_theme and hint in (5, 6, 7):
        icon_name = "weather-snow-and-rain"
    else:
        icon_name = get_icon_name(hint)
    icon = os.path.join(theme_path, icon_name) + extension

    if os.path.exists(icon):
        return icon
    else:
        return os.path.join(moonbeam_theme, get_icon_name(hint)) + ".png"
