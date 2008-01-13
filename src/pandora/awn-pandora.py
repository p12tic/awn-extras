#!/usr/bin/python
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import gtkmozembed
import awn

class App (awn.AppletSimple):
  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    self.pref_path = os.path.join(os.path.expanduser('~'), ".config/awn/applets/pandora")
    self.height = height
    icon = gdk.pixbuf_new_from_file(os.path.dirname (__file__) + '/pandora.ico')
        
    if height != icon.get_height():
        icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
    self.set_icon(icon)
    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)

    self.mo  = gtkmozembed;
    #gtkmozembed.set_profile_path(self.pref_path, "profile")
    self.moz = self.mo.MozEmbed()
    pad = gtk.Alignment()
    pad.add(self.moz)
    self.moz.set_size_request(640, 535)
    self.moz.load_url('http://www.pandora.com/radio/tuner_8_2_0_1_pandora.swf')
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
    #self.moz.load_url('https://www.pandora.com/radio/tuner_8_2_0_1_pandora.swf')
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
