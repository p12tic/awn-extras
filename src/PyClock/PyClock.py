#!/usr/bin/python
import sys, os
import gobject
import pygtk
import cairo
import gtk
from gtk import gdk
import awn
import time
import rsvg
from StringIO import StringIO


def timer1 (applet, ObjClock):
  return ObjClock.ThreadFunction(applet)

class App (awn.AppletSimple):
  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    self.height = height

    self.ObjClock = Clock()
    self.ObjClock.LoadTheme("Tango")
    self.ObjClock.DrawClockTheme(self)

    self.timer = gobject.timeout_add (1050, timer1, self, self.ObjClock)

    self.title = awn.awn_title_get_default ()
    self.dialog = awn.AppletDialog (self)
    button = gtk.Button (stock="gtk-apply")
    self.dialog.add (button)
    button.show_all ()
    #self.connect ("button-press-event", self.button_press)
    self.connect ("enter-notify-event", self.enter_notify)
    self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)

  def button_press (self, widget, event):
    self.dialog.show_all ()
    self.title.hide (self)
    print "show dialog"

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
    print "hide dialog"

  def enter_notify (self, widget, event):
    self.ObjClock.SetHover(self, True)
    #print "show title"

  def leave_notify (self, widget, event):
    self.ObjClock.SetHover(self, False)
    #print "hide title"


class Clock:

  Hover = False
  ClockBaseSurface = ""

  #Svg Memory Space

  SVGH_Drop_Shadow = ""
  SVGH_Face = ""
  SVGH_Marks = ""
  SVGH_Frame = ""
  SVGH_Hour_Hand = ""
  SVGH_Minute_Hand = ""
  SVGH_Second_Hand = ""



  def GetTime(self, part):
    GotTime = time.localtime()
    if part == 'H':
        return GotTime[3]
    if part == 'M':
        return GotTime[4]
    if part == 'S':
        return GotTime[5]

  def GetTimeString(self):
    Hour = str(self.GetTime('H'))
    Mins = str(self.GetTime('M'))
    Secs = str(self.GetTime('S'))
    if len(Hour) == 1:
        Hour = "0" + Hour
    if len(Mins) == 1:
        Mins = "0" + Mins
    if len(Secs) == 1:
        Secs = "0" + Secs
    return Hour + ":" + Mins + ":" + Secs

  def SetTittle(self, applet):
    applet.title.show (applet, self.GetTimeString())

  def SetHover(self, applet, status):
    if status == True:
        self.Hover = True
        self.SetTittle(applet)
    if status == False:
        self.Hover = False
        applet.title.hide(applet)

  def ThreadFunction(self, applet):
    self.DrawClockTheme(applet)
    if self.Hover == True:
        self.SetTittle(applet)
    return True

  def GetPixbufFromSurface(self, surface):
    sio = StringIO()
    surface.write_to_png(sio)
    sio.seek(0)
    loader = gtk.gdk.PixbufLoader()
    loader.write(sio.getvalue())
    loader.close()
    return loader.get_pixbuf()

  def GetThemeFile(self, filen, theme):
    return os.path.abspath(os.path.dirname(__file__)) + "/Themes/" + theme + "/" + filen

  def LoadTheme(self, theme):
    self.SVGH_Drop_Shadow = rsvg.Handle(self.GetThemeFile('clock-drop-shadow.svg', theme))
    self.SVGH_Face = rsvg.Handle(self.GetThemeFile('clock-face.svg', theme))
    self.SVGH_Marks = rsvg.Handle(self.GetThemeFile('clock-marks.svg', theme))
    self.SVGH_Frame = rsvg.Handle(self.GetThemeFile('clock-frame.svg', theme))
    self.SVGH_Hour_Hand = rsvg.Handle(self.GetThemeFile('clock-hour-hand.svg', theme))
    self.SVGH_Minute_Hand = rsvg.Handle(self.GetThemeFile('clock-minute-hand.svg', theme))
    self.SVGH_Second_Hand = rsvg.Handle(self.GetThemeFile('clock-second-hand.svg', theme))

  def SetIconFromSurface(self, applet, surface):
    icon = self.GetPixbufFromSurface(surface)
    if applet.height != icon.get_height(): # Check if the icon height is not correct
        icon = icon.scale_simple(applet.height, applet.height, gtk.gdk.INTERP_BILINEAR) # Scale it if so
    applet.set_temp_icon (icon)


  def DrawClockCairo(self, applet):
    PI = 3.141593
    # Setup Cairo
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 48, 48)
    ctx = cairo.Context(surface)
    # Set thickness of brush
    ctx.set_line_width(2)
    #draw circle
    ctx.set_source_rgba(1, 0.2, 0.2, 0.6)
    ctx.arc(24, 24, 22, 0 * (PI/180), 360 * (PI/180))
    ctx.fill()
    #draw hour pointer
    ctx.set_source_rgba(0, 0, 0, 0.6)
    ctx.arc(24, 24, 16, (360/12) * (self.GetTime('H')+9+(self.GetTime('M')/60.0)) * (PI/180), (360/12) * (self.GetTime('H')+9+(self.GetTime('M')/60.0)) * (PI/180))
    ctx.line_to(24, 24)
    ctx.stroke()
    #draw minute pointer
    ctx.set_source_rgba(0, 0, 0, 0.6)
    ctx.arc(24, 24, 21, (360/60) * (self.GetTime('M')+45) * (PI/180), (360/60) * (self.GetTime('M')+45) * (PI/180))
    ctx.line_to(24, 24)
    ctx.stroke()
    #draw seconds pointer
    ctx.set_source_rgba(0.2, 0.2, 1, 0.6)
    ctx.arc(24, 24, 21, (360/60) * (self.GetTime('S')+45) * (PI/180), (360/60) * (self.GetTime('S')+45) * (PI/180))
    ctx.line_to(24, 24)
    ctx.stroke()

    self.SetIconFromSurface(applet, surface)

  def DrawClockTheme(self, applet):
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 48, 50)
    ctx = cairo.Context(surface)
    ctx.scale(0.50,0.50)
    self.SVGH_Drop_Shadow.render_cairo(ctx)
    self.SVGH_Face.render_cairo(ctx)
    self.SVGH_Marks.render_cairo(ctx)
    self.SVGH_Frame.render_cairo(ctx)
    ctx.translate(50,50)
    ctx.save()
    ctx.rotate((360/12) * (self.GetTime('H')+9+(self.GetTime('M')/60.0)) * (3.141593/180))
    self.SVGH_Hour_Hand.render_cairo(ctx)
    ctx.restore()
    ctx.save()
    ctx.rotate((360/60) * (self.GetTime('M')+45) * (3.141593/180))
    self.SVGH_Minute_Hand.render_cairo(ctx)
    ctx.restore()
    ctx.save()
    ctx.rotate((360/60) * (self.GetTime('S')+45) * (3.141593/180))
    self.SVGH_Second_Hand.render_cairo(ctx)

    self.SetIconFromSurface(applet, surface)




if __name__ == "__main__":
  awn.init (sys.argv[1:])
  #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
