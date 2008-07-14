#!/usr/bin/python
"""
Copyright 2007, 2008 Ryan Rushton (ryancr) <ryan@rrdesign.ca>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys#, os
import pygtk
import gtk
import gtkmozembed
import awn

class App (awn.AppletSimple):
  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    #self.pref_path = os.path.join(os.path.expanduser('~'), ".config/awn/applets/awn-meebo")
    self.set_awn_icon('awn-meebo', 'meebo')
    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)

    self.mo  = gtkmozembed;
    #self.mo.gtk_moz_embed_set_profile_path(self.pref_path, "profile")
    self.moz = self.mo.MozEmbed()
    pad = gtk.Alignment()
    pad.add(self.moz)
    self.moz.set_size_request(320, 480)
    self.moz.load_url('https://www.meebo.com/mobile/')
    pad.show_all()
    self.dialog.add(pad)

    self.connect ("button-press-event", self.button_press)
    self.connect ("enter-notify-event", self.enter_notify)
    self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)

  def button_press (self, widget, event):
    self.dialog.show_all ()
    self.title.hide (self)

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()

  def enter_notify (self, widget, event):
    self.title.show (self, "Mobile Meebo")

  def leave_notify (self, widget, event):
    self.title.hide (self)

if __name__ == "__main__":
  awn.init (sys.argv[1:])
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
