#!/usr/bin/python
# Copyright (c) 2009  Michal Hruby <michal.mhr AT gmail.com>
# Copyright (C) 2009 - 2010  onox <denkpadje@gmail.com>
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

import gtk

from awn import config_get_default_for_applet_by_info
from awn.extras import configbinder

ui_file = os.path.join(os.path.dirname(__file__), "shiny-prefs.ui")


class Preferences:

    def __init__(self):
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        s2w_1000 = lambda v: v/1000.0
        w2s_1000 = lambda v: int(v*1000)

        s2w_100 = lambda v: v*100
        w2s_100 = lambda v: v/100

        shiny_config = config_get_default_for_applet_by_info("shinyswitcher", "")

        binder = configbinder.get_config_binder(shiny_config, "DEFAULT", prefs)
        binder.bind("applet_scale", "appletSizeScale", False, s2w_100, w2s_100)
        binder.bind("grab_wallpaper", "grabWallpaperRadio")
        binder.bind("desktop_colour", "backgroundColor")
        binder.bind("applet_border_colour", "borderColor")
        binder.bind("applet_border_width", "borderSizeSpin")
        binder.bind("win_active_icon_alpha", "activeIconAlphaScale", False, s2w_100, w2s_100)
        binder.bind("win_inactive_icon_alpha", "inactiveIconAlphaScale", False, s2w_100, w2s_100)
        binder.bind("background_alpha_active", "activeWsAlphaScale", False, s2w_100, w2s_100)
        binder.bind("background_alpha_inactive", "inactiveWsAlphaScale", False, s2w_100, w2s_100)

        binder.bind("rows", "rowsSpin")
        binder.bind("columns", "columnsSpin")
        binder.bind("win_grab_mode", "combobox-thumbnailing")
        binder.bind("show_icon_mode", "combobox-icon-display")
        binder.bind("scale_icon_mode", "combobox-icon-scaling")
        binder.bind("scale_icon_position", "iconPosCombobox")
        binder.bind("scale_icon_factor", "iconScaleScale", False, s2w_100, w2s_100)
        binder.bind("cache_expiry", "cacheSpin")
        binder.bind("queued_render_timer", "renderSpin", False, s2w_1000, w2s_1000)
        binder.create_gobject()

        self.window = prefs.get_object("dialog1")
        self.window.set_icon_name("gnome-panel-workspace-switcher")
        self.window.connect("destroy", gtk.main_quit)
        prefs.get_object("closeButton").connect("clicked", gtk.main_quit)
        self.window.show_all()


if __name__ == "__main__":
    pref_dialog = Preferences()
    gtk.main()
