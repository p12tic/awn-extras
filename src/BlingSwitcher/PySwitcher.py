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
    self.timer = gobject.timeout_add (2500, timer1, self, self.ObjSwitcher)
    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)
    self.ObjSwitcher.CreateDialog(self.dialog)
    self.ObjSwitcher.SetRgba(self.dialog)
    self.ObjSwitcher.DrawSwitcher(self)
    self.scr = wnck.screen_get_default()
    self.scr.connect("window-stacking-changed", self.windowchanged)
    self.scr.connect("viewports-changed", self.viewportchanged)
    self.connect ("button-press-event", self.button_press)
    self.connect("scroll_event", self.scroll, self.ObjSwitcher)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)


  ###################################################### Event Functions

  def scroll (self, widget, event, ObjSwitcher):
    if event.direction == gtk.gdk.SCROLL_UP:
        ObjSwitcher.move_viewport('next')
    if event.direction == gtk.gdk.SCROLL_DOWN:
        ObjSwitcher.move_viewport('prev')

  def button_press (self, widget, event):
    self.dialog.show_all ()
    self.title.hide (self)

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()

  def viewportchanged (self, screen):
    self.ObjSwitcher.DrawSwitcher(applet)

  def windowchanged (self, screen):
    self.ObjSwitcher.DrawSwitcher(applet)


class Switcher:

  switcher = ""
  activeworkspace = ""
  activeworkspace = 0

  ################################################## Initial Functions

  def SetRgba(self, dialog):
    color = dialog.get_style().base[gtk.STATE_NORMAL]
    self.switcher.set_bg_rgba(color.red/65335.0, color.green/65335.0, color.blue/65335.0, 0.85)

  def CreateDialog(self, dialog):
    box1 = gtk.HBox(False, 0)
    dialog.add(box1)
    self.switcher = CairoWidgets_BlingSwitcher.BlingSwitcher()
    box1.pack_start(self.switcher, True, True, 0)
    self.switcher.show()
    box1.show()

  ################################################## Icon Drawing Related Functions

  def DrawSwitcher(self, applet):
    icon = self.GenerateBackgroundThumbPixbuf(self.GetActiveWorkspaceNumber(),applet.get_height())
    applet.set_temp_icon(icon)

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
    sio.close()
    loader.close()
    pixbuf = loader.get_pixbuf()
    print pixbuf
    return pixbuf

  ################################################### Redirection Functions

  def move_viewport(self, direction):
    self.switcher.move_viewport(direction)





if __name__ == "__main__":
  awn.init (sys.argv[1:])
  #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
