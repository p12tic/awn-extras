#!/usr/bin/python

# Copyright (c) 2009 Sharkbaitbobby
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


import sys
import pygtk
import gtk
import gettext
import os

import awn

import awn.extras.awnmediaplayers as mediaplayers
from awn.extras import defs

APP = "awn-extras-applets"
gettext.bindtextdomain(APP, defs.GETTEXTDIR)
gettext.textdomain(APP)
_ = gettext.gettext

def error_decorator(fn):
    """Handles errors caused by dbus"""
    def errors(cls, *args, **kwargs):
        try:
            fn(cls, *args)
        except (dbus.exceptions.DBusException, AttributeError, RuntimeError):
            cls.what_app()
    return errors

class App (awn.AppletSimple):
    """
    """
    def __init__ (self, uid, panel_id, media_button_type):
        """
        Creating the applet's core
        """
        awn.AppletSimple.__init__(self, uid, panel_id)

        self.icon_names = {}
        self.icon_names["--next"] = "media-skip-forward"
        self.icon_names["--previous"] = "media-skip-backward"
        self.icon_names["--pp"] = "media-playback-start"

        self.tooltips = {}
        self.tooltips["--next"] = _("Next")
        self.tooltips["--previous"] = _("Previous")
        self.tooltips["--pp"] = _("Play/Pause")

        self.funcs = {}
        self.funcs["--next"] = self.button_next_press
        self.funcs["--previous"] = self.button_previous_press
        self.funcs["--pp"] = self.button_pp_press

        #(Same as desktop files so there's only one string each for i18n)
        self.desc = {}
        self.desc["--next"] = _("A media-control applet (Next Track)")
        self.desc["--previous"] = _("A media-control applet (Previous Track)")
        self.desc["--pp"] = _("A media-control applet (Play/Pause)")

        #(Also same as desktop files)
        self.titles = {}
        self.titles["--next"] = _("Media Icons Next")
        self.titles["--previous"] = _("Media Icons Previous")
        self.titles["--pp"] = _("Media Icons Play/Pause")

        gtk.window_set_default_icon_name(self.icon_names[media_button_type])

        self.media_button_type = media_button_type
        self.set_icon_name('media-icon' + media_button_type[1:], \
            self.icon_names[media_button_type])

        self.what_app()
        self.set_tooltip_text(self.tooltips[media_button_type])

        self.popup_menu = self.create_default_menu()
        about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.popup_menu.append(about)

        gtk.about_dialog_set_url_hook(self.do_url, None)

        about.connect("activate", self.show_about)
        self.connect("button-press-event", self.button_press)

    def button_press(self, widget, event):
        if event.button == 1:
            self.funcs[self.media_button_type]()
        elif event.button == 3:
            self.popup_menu.show_all()
            self.popup_menu.popup(None, None, None, event.button, event.time)

    def what_app(self):
        self.player_name = mediaplayers.what_app()
        if self.player_name == None:pass
        else:
            self.MediaPlayer = mediaplayers.__dict__[self.player_name]()

    @error_decorator
    def button_previous_press(self):
        self.MediaPlayer.previous()

    @error_decorator
    def button_pp_press(self):
        self.MediaPlayer.play_pause()

    @error_decorator
    def button_next_press(self):
        self.MediaPlayer.next()

    def do_url(self, about, url, data):
        try:
            gtk.show_uri(None, url, gtk.get_current_event_time())

        #For GTK < 2.14
        except:
            os.system('xdg-open %s &' % url)

    def show_about(self, menuitem):
        win = gtk.AboutDialog()
        win.set_name(self.titles[self.media_button_type])
        win.set_copyright('Copyright 2009 sharkbaitbobby')
        win.set_authors(['Randal Barlow <im.tehk at gmail.com>',
            'Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>'])
        win.set_comments(self.desc[self.media_button_type])
        win.set_license("This program is free software; you can redistribute it "+\
          "and/or modify it under the terms of the GNU General Public License "+\
          "as published by the Free Software Foundation; either version 2 of "+\
          "the License, or (at your option) any later version. This program is "+\
          "distributed in the hope that it will be useful, but WITHOUT ANY "+\
          "WARRANTY; without even the implied warranty of MERCHANTABILITY or "+\
          "FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public "+\
          "License for more details. You should have received a copy of the GNU "+\
          "General Public License along with this program; if not, write to the "+\
          "Free Software Foundation, Inc.,"+\
          "51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.")
        win.set_wrap_license(True)
        win.set_logo_icon_name(self.icon_names[self.media_button_type])
        win.set_website('http://wiki.awn-project.org/Media_Icons_Applet')
        win.set_website_label('wiki.awn-project.org')
        win.run()
        win.destroy()

if __name__ == "__main__":
    awn.init(sys.argv[2:])
    applet = App(awn.uid, awn.panel_id, sys.argv[1])
    awn.init_applet(applet)
    applet.show_all()
    gtk.main()
