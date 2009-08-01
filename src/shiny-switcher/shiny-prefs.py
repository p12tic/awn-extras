#!/usr/bin/python
# Copyright (c) 2009  Michal Hruby <michal.mhr AT gmail.com>
# Copyright (C) 2009  onox <denkpadje@gmail.com>
#
# This is the configuration dialog for shiny-switcher applet for AWN.
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
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import os

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib

ui_file = os.path.join(os.path.dirname(__file__), "shiny-prefs.ui")


class Preferences:

    def __init__(self):
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        s2w_1000 = lambda v: v/1000.0
        w2s_1000 = lambda v: int(v*1000)

        s2w_100 = lambda v: v*100
        w2s_100 = lambda v: v/100

        shiny_settings = awnlib.Settings(folder="applets/shinyswitcher")
        default_values = {
            "applet_scale":                 ("appletSizeScale", s2w_100, w2s_100),
            "grab_wallpaper":               "grabWallpaperRadio",
            "desktop_colour":               "backgroundColor",
            "applet_border_colour":         "borderColor",
            "applet_border_width":          "borderSizeSpin",
            "win_active_icon_alpha":        ("activeIconAlphaScale", s2w_100, w2s_100),
            "win_inactive_icon_alpha":      ("inactiveIconAlphaScale", s2w_100, w2s_100),
            "background_alpha_active":      ("activeWsAlphaScale", s2w_100, w2s_100),
            "background_alpha_inactive":    ("inactiveWsAlphaScale", s2w_100, w2s_100),

            "rows":                         "rowsSpin",
            "columns":                      "columnsSpin",
            "win_grab_mode":                "combobox-thumbnailing",
            "show_icon_mode":               "combobox-icon-display",
            "scale_icon_mode":              "combobox-icon-scaling",
            "scale_icon_position":          "iconPosCombobox",
            "scale_icon_factor":            ("iconScaleScale", s2w_100, w2s_100),
            "cache_expiry":                 "cacheSpin",
            "queued_render_timer":          ("renderSpin", s2w_1000, w2s_1000)
        }
        shiny_settings.load_via_gtk_builder(prefs, default_values)

        self.window = prefs.get_object("dialog1")
        self.window.set_icon_name("gnome-panel-workspace-switcher")
        self.window.connect("destroy", gtk.main_quit)
        prefs.get_object("closeButton").connect("clicked", gtk.main_quit)
        self.window.show_all()


if __name__ == "__main__":
    pref_dialog = Preferences()
    gtk.main()
