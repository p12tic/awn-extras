#!/usr/bin/python
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import dircache

class App (awn.AppletSimple):

  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    self.height = height
    self.theme = gtk.IconTheme ()
    icon = self.theme.load_icon ("gtk-apply", height, 0)
    location = __file__.replace('tsclient_app.py','')
    icon0 = location + "icons/Tsclient.svg"
    icon0 = gdk.pixbuf_new_from_file (icon0)
    if height != icon0.get_height():
      icon0 = icon0.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
    self.set_temp_icon (icon0)
    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)
    self.dialog_showing = False
    self.connect ("button-press-event", self.button_press)
    #self.connect ("enter-notify-event", self.enter_notify)
    #self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)
    #a=dircache.listdir('/home/david/.tsclient')
    home = os.path.expanduser('~')
    a=os.listdir(home + '/.tsclient')
    self.rootPath = home + "/.tsclient/"
    for item in a:
        (shortname, extension) = os.path.splitext(item)
	if extension == '.rdp':
	    button = gtk.Button (label=shortname)
	    self.dialog.add (button)
	    button.show_all ()
	    button.connect ("button-press-event", self.start_tsclient, item)
    button = gtk.Button (label="New Connection...")
    self.dialog.add (button)
    button.show_all ()
    button.connect ("button-press-event", self.start_tsclient, "")

  def start_tsclient (self, widget, event, rdpFile):
    os.system('tsclient -x ' + self.rootPath + rdpFile)
    #print rdpFile

  def button_press (self, widget, event):
    if self.dialog_showing:
        self.dialog.hide()
        self.dialog_showing = False
    else:
        self.dialog.show_all ()
        self.dialog_showing = True
    self.title.hide (self)
    #print os.path.expanduser('~')

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
    #print "hide dialog"

  def enter_notify (self, widget, event):
    self.title.show (self, "TsClient Applet")
    icon = self.theme.load_icon ("gtk-apply", self.height, 0)
    if self.height != icon.get_height():
      icon = icon.scale_simple(self.height,self.height,gtk.gdk.INTERP_BILINEAR)
    self.set_temp_icon (icon)
    #print "show title"

  def leave_notify (self, widget, event):
    self.title.hide (self)
    icon = self.theme.load_icon ("gtk-cancel", self.height, 0)
    if self.height != icon.get_height():
      icon = icon.scale_simple(self.height,self.height,gtk.gdk.INTERP_BILINEAR)
    self.set_temp_icon (icon)
    #print "hide title"

if __name__ == "__main__":
  awn.init (sys.argv[1:])
  #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
