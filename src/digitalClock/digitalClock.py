#!/usr/bin/python

import sys, os
import gobject
import pygtk
import gtk
import gtk.glade
from gtk import gdk
from StringIO import StringIO
import string
import gconf
import cairo
import time
import math
import subprocess
import tempfile
import datetime
import awn
import dgClockPref
import dgTime

class App (awn.AppletSimple):

  dialog_visible    = False
  gconf_path        = "/apps/avant-window-navigator/applets/digitalClock"

  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)

    self.gconf_client = gconf.client_get_default()
    self.gconf_client.notify_add(self.gconf_path, self.gconf_event)

    self.pf = dgClockPref.dgClockPref()
    self.clock = dgTime.dgTime(self.pf.prefs, self)

    self.timer = gobject.timeout_add(1000, self.clock.draw_clock)

    #self.title = awn.awn_title_get_default ()

    cur_time = time.localtime()
    h = cur_time[3]
    m = cur_time[4]
    s = cur_time[5]
    utc = ((h*60*60) + (m*60) + s) - time.timezone
    print utc

    #12:00 - UTC = tz_sun_zone



    self.connect ("button-press-event", self.button_press)
    #self.connect ("enter-notify-event", self.enter_notify)
    #self.connect ("leave-notify-event", self.dialog_focus_out)

  ## Dialog callbacks
  def button_press (self, widget, event):
    if event.button == 3: # right click
      self.pf.menu.popup(None, None, None, event.button, event.time)
    else:
      if self.dialog_visible:
        self.dialog.hide()
        self.dialog_visible = False
      else:
        hbox = gtk.HBox(False,2)
        cal = gtk.Calendar()
        cal.set_display_options(gtk.CALENDAR_SHOW_HEADING | gtk.CALENDAR_SHOW_DAY_NAMES | gtk.CALENDAR_SHOW_WEEK_NUMBERS)
        cal.connect("day-selected-double-click", self.startEvolution)
        hbox.pack_start(cal, expand=False, fill=False, padding=0)

        #map_image = self.create_map()
        #hbox.pack_start(map_image, expand=False, fill=False, padding=0)

        self.dialog = awn.AppletDialog (self)
        self.dialog.connect ("focus-out-event", self.dialog_focus_out)
        self.dialog.set_title("Calendar")
        self.dialog.add(hbox)
        self.dialog.show_all()
        self.dialog_visible = True
  '''
  def create_map(self):
    cs_src = cairo.ImageSurface.create_from_png("/home/ryan/Desktop/mapOverlay.png")
    cs_dst = cairo.ImageSurface.create_from_png("/home/ryan/Desktop/map.png")
    ct_src = cairo.Context(cs_src)
    ct_dst = cairo.Context(cs_dst)

    ct_dst.set_source_surface(cs_src ,-245 ,0)
    ct_dst.set_operator(cairo.OPERATOR_OVER)
    ct_dst.paint()
    cairo.ImageSurface.write_to_png(cs_dst, "/home/ryan/Desktop/pic.png")
    im = gtk.Image()
    im.set_from_pixbuf(finalPix)
    return im
  '''

  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
    self.dialog_visible = False

  def startEvolution(self, cal):
    da = cal.get_date()
    dat = "%02d%02d%02d" % (da[0], (da[1]+1), da[2])
    subprocess.Popen('evolution calendar:///?startdate='+dat+'T120000', shell=True)

  def gconf_event(self, gconf_client, *args, **kwargs):
    self.pf.get_prefs()
    self.clock.update_prefs(self.pf.prefs)

if __name__ == "__main__":
  awn.init (sys.argv[1:])
  applet = App (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()