#!/usr/bin/python
#Copyright 2007 Isaac J. 
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import cairo
import pango

BOR = 4
GAP = 20


class Dialog (awn.AppletDialog):
  def __init__ (self, applet):
    awn.AppletDialog.__init__ (self, applet)
    self.connect ("expose-event",self._expose)

  def _expose (self, widget, event):
    cr = widget.window.cairo_create ()
    cr.set_operator (cairo.OPERATOR_CLEAR)
    cr.paint ()
    cr.set_operator (cairo.OPERATOR_OVER)
   
    for c in self.get_children():
      self.propagate_expose (c, event)

    return True
