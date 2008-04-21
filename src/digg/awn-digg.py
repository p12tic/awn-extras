#!/usr/bin/python
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
#import gtkmozembed
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
except:
       print 'Gtkmozembed is need to run the RTM-Applet, please install'

class App (awn.AppletSimple):
  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    self.pref_path = os.path.dirname (__file__)
    self.height = height
    icon = gdk.pixbuf_new_from_file(os.path.dirname (__file__) + '/digg.png')

    if height != icon.get_height():
        icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
    self.set_icon(icon)
    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)

    gtkmozembed.set_profile_path(self.pref_path, "profile")
    self.moz = gtkmozembed.MozEmbed()
    pad = gtk.Alignment()
    pad.add(self.moz)
    self.moz.set_size_request(450, 580)
    self.moz.load_url('http://digg.com/iphone#_stories')
    pad.show_all()
    self.dialog.add(pad)

    self.connect ("button-press-event", self.button_press)
    #self.connect ("enter-notify-event", self.enter_notify)
    #self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)

  def button_press (self, widget, event):
    self.dialog.show_all ()
    self.title.hide (self)
    print "show dialog"

  def dialog_focus_out (self, widget, event):
    self.moz.load_url('http://digg.com/iphone#_stories')
    self.dialog.hide ()
    print "hide dialog"

  def enter_notify (self, widget, event):
    self.title.show (self, "Test python applet")
    icon = self.theme.load_icon ("gtk-apply", self.height, 0)
    self.set_temp_icon (icon)
    print "show title"

  def leave_notify (self, widget, event):
    self.title.hide (self)
    icon = self.theme.load_icon ("gtk-cancel", self.height, 0)
    self.set_temp_icon (icon)
    print "hide title"

if __name__ == "__main__":
  awn.init (sys.argv[1:])
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
