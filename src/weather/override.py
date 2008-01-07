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

    
  def BubbleRect(self,ct,x0,y0,width,height,radius):
    radius *= 2
    x1 = x0 + width
    y1 = y0 + height
    ct.move_to(x0, y0+radius)
    ct.curve_to(x0,y0,x0,y0,x0+radius,y0)
    ct.line_to(x1-radius,y0)
    ct.curve_to(x1,y0,x1,y0,x1,y0+radius)
    ct.line_to(x1,y1-radius)
    ct.curve_to(x1,y1,x1,y1,x1-radius,y1)
    ct.line_to(x0+radius,y1)
    ct.curve_to(x0,y1,x0,y1,x0,y1-radius)
    ct.close_path()
    return

  def _expose (self, widget, event):
    cr = widget.window.cairo_create ()
    cr.set_operator (cairo.OPERATOR_CLEAR)
    cr.paint ()
    cr.set_operator (cairo.OPERATOR_OVER)
   
    for c in self.get_children():
      self.propagate_expose (c, event)

    return True
