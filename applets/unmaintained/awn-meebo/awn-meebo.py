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

import sys, os
import pygtk
import gtk
import awn
import re

# workaround for weirdness with regards to Ubuntu + gtkmozembed
if os.path.exists('/etc/issue'):
  fp = open('/etc/issue')
  os_version = fp.read()
  fp.close()
  if re.search(r'7\.(?:04|10)', os_version): # feisty or gutsy
    os.putenv('LD_LIBRARY_PATH', '/usr/lib/firefox')
    os.putenv('MOZILLA_FIVE_HOME', '/usr/lib/firefox')

try:
  import gtkmozembed
except ImportError:
  print '       #####################################'
  print 'Gtkmozembed is needed to run Mobile Meebo, please install.'
  print ' * On Debian or Ubuntu based systems, install python-gnome2-extras'
  print ' * On Gentoo based systems, install dev-python/gnome-python-extras'
  print ' * On Fedora based systems, install gnome-python2-gtkmozembed'
  print ' * On SUSE based systems, install python-gnome-extras'
  print ' * On Mandriva based systems, install gnome-python-gtkmozembed'
  print 'See: http://wiki.awn-project.org/Awn_Extras:Dependency_Matrix'
  print '       #####################################'

# Add pop up if gtkmozembed isn't found
awn.check_dependencies(globals(), 'gtkmozembed')


class App (awn.AppletSimple):
  displayed = False
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
    if self.displayed == True:
      self.dialog.hide()
      self.displayed = False
    if event.button == 3:
      menu = self.create_default_menu()
      menu.show_all()
      menu.popup(None, None, None, event.button, event.time)
    else:
      self.dialog.show_all()
      self.title.hide(self)
      self.displayed = True

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
    self.displayed = False

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
