#!/usr/bin/python
import sys, os
import gobject
import pygtk
import cairo
import gtk
from gtk import gdk
import awn
from StringIO import StringIO
import wnck
import gconf
import CairoWidgets_BlingSwitcher

##############################################################################
#                                                                            #
# todo: draw-windows, better surface getting, change dialog on layout change #
#                                                                            #
##############################################################################
def timer1 (applet, ObjSwitcher):
  return ObjSwitcher.DrawSwitcher(applet)

class App (awn.AppletSimple):

  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)

    self.ObjSwitcher = Switcher()
    self.timer = gobject.timeout_add (1000, timer1, self, self.ObjSwitcher)
    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)
    self.ObjSwitcher.CreateDialog(self.dialog)
    self.ObjSwitcher.DrawSwitcher(self)
    self.connect ("button-press-event", self.button_press)
    #self.connect ("enter-notify-event", self.enter_notify)
    #self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)

  def button_press (self, widget, event):
    self.dialog.show_all ()
    self.title.hide (self)
    #print "show dialog"

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
    #print "hide dialog"

  #def enter_notify (self, widget, event):
    #self.ObjClock.SetHover(self, True)
    #print "show title"

  #def leave_notify (self, widget, event):
    #self.ObjClock.SetHover(self, False)
    #print "hide title"


class Switcher:

  bgurl = ""
  bgpixbuf = ""
  client = gconf.client_get_default()
  switcher = ""
  activeworkspace = ""

  def __init__(self):
    self.activeworkspace = 0

  def CreateDialog(self, dialog):
    box1 = gtk.HBox(False, 0)
    dialog.add(box1)
    self.switcher = CairoWidgets_BlingSwitcher.BlingSwitcher()
    box1.pack_start(self.switcher, True, True, 0)
    self.switcher.show()
    box1.show()

  def DrawSwitcher(self, applet):

    if (self.activeworkspace != self.GetActiveWorkspaceNumber()):
    	icon = self.GenerateBackgroundThumbPixbuf(self.GetActiveWorkspaceNumber(),50)
    	applet.set_temp_icon(icon)

    return True

  def GenerateBackgroundThumbPixbuf(self,n,h):
    cs = cairo.ImageSurface(0,h,h)
    ct = cairo.Context(cs)
    ct2 = gtk.gdk.CairoContext(ct)
    self.switcher.draw_on_square(ct2, n, h)
    icon = self.GetPixbufFromSurface(cs)
    return icon

  def GetActiveWorkspaceNumber(self):
    scr = wnck.screen_get_default()
    while gtk.events_pending():
        gtk.main_iteration()
    wrkspace = scr.get_active_workspace()
    nviewp = wrkspace.get_width()/scr.get_width()
    return (wrkspace.get_viewport_x() + scr.get_width())/scr.get_width()

  def GetPixbufFromSurface(self, surface):
    sio = StringIO()
    surface.write_to_png(sio)
    sio.seek(0)
    loader = gtk.gdk.PixbufLoader()
    loader.write(sio.getvalue())
    loader.close()
    return loader.get_pixbuf()



if __name__ == "__main__":
  awn.init (sys.argv[1:])
  #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
