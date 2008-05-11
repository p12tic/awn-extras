#
# Copyright Ryan Rushton  ryan@rrdesign.ca
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA



import os
import gtk
import gtk.glade
import time
import tempfile
import cairo
from awn import extras

class dgTime:

  curY = 0
  curX = 0
  shadow_offset = 1

  def __init__(self, prefs, awn):
    self.awn = awn
    self.prefs = prefs
    self.pixbuf = None
    self.draw_clock()

  def update_prefs(self, prefs):
    self.prefs = prefs

  def draw_clock (self):
    self.curY = 0
    if self.prefs['dateBeforeTime']:
      self.width = int(self.awn.get_height()*2.5)
    else:
      self.width = int(self.awn.get_height()*1.3)

    if self.prefs['hour12']:
      increase_size = 0
    else:
      increase_size = 1

    self.height = self.awn.get_height()

    t = self.get_time_string()

    cs = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
    ct = cairo.Context(cs)
    ct.set_source_surface(cs)
    ct.paint()
    ct.select_font_face(self.prefs['fontFace'], cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)

    if self.prefs['dateBeforeTime']:
      self.draw_text_beside(ct, t[1], 8, 'd') #Day
      self.draw_text_beside(ct, t[2], 9.5, 'm') #Month
      self.draw_text_beside(ct, t[0], 4.4-increase_size, 't') #Time
    else:
      self.draw_text(ct, t[0], 5-increase_size) #Time
      self.draw_text(ct, t[1], 4) #Day
      self.draw_text(ct, t[2], 4.4) #Month

    if self.pixbuf is None:
      self.pixbuf = extras.surface_to_pixbuf(cs)
    else:
      self.pixbuf = extras.surface_to_pixbuf(cs, self.pixbuf)
    self.awn.set_icon(self.pixbuf)
    del ct
    cs.finish()
    del cs
    return True

  def draw_text(self, ct, text, size):
    size = self.width/size
    ct.set_font_size(size)
    font_dim = self.get_font_size(ct, text)
    x = (self.width/2) - (font_dim['width']/2)
    v_space = ((self.awn.get_height()/2.4)-font_dim["height"])/2.5 #adjust vert spacing
    y = self.curY+font_dim["height"]+(v_space)
    #Shadow
    ct.move_to(x+self.shadow_offset,y+self.shadow_offset)
    ct.set_source_rgba(self.prefs['fontShadowColor'].red/65535.0, self.prefs['fontShadowColor'].green/65535.0, self.prefs['fontShadowColor'].blue/65535.0, 0.8)
    ct.show_text(text)
    #Text
    ct.move_to(x,y)
    ct.set_source_rgb(self.prefs['fontColor'].red/65535.0, self.prefs['fontColor'].green/65535.0, self.prefs['fontColor'].blue/65535.0)
    ct.show_text(text)
    self.curY = y

  def draw_text_beside(self, ct, text, size, type):
    if self.curY == 0:
      self.curY = self.awn.get_height()/5
    if type == "t":
      self.width = self.width - (self.curX + 5)
      size = self.width/size
    else:
      size = self.width/size
    ct.set_font_size(size)
    font_dim = self.get_font_size(ct, text)
    x = 0
    v_space = ((self.awn.get_height()/2.4)-font_dim["height"])/1.5 #adjust vert spacing
    y = self.curY+font_dim["height"]+(v_space)
    if type == 't':
      x = self.curX + 5
      y = (self.awn.get_height()/2)+(font_dim['height']/2)
    self.curX = font_dim['width']

    #Shadow
    ct.move_to(x+self.shadow_offset,y+self.shadow_offset)
    ct.set_source_rgba(self.prefs['fontShadowColor'].red/65535.0, self.prefs['fontShadowColor'].green/65535.0, self.prefs['fontShadowColor'].blue/65535.0, 0.8)
    ct.show_text(text)
    #Text
    ct.move_to(x,y)
    ct.set_source_rgb(self.prefs['fontColor'].red/65535.0, self.prefs['fontColor'].green/65535.0, self.prefs['fontColor'].blue/65535.0)
    ct.show_text(text)
    self.curY = y

  def get_font_size(self, ct, text):
    xbearing, ybearing, width, height, xadvance, yadvance = (ct.text_extents(text))
    if xadvance > width:
      fwidth = xadvance
    else:
      fwidth = width
    return {'width':fwidth, 'height':height}

  def get_time_string(self):
    fullDate = []

    if self.prefs['hour12']:
      fullDate.append(time.strftime('%I:%M %p'))
    else:
      fullDate.append(time.strftime('%H:%M'))
    fullDate.append(time.strftime("%a"))
    fullDate.append(time.strftime('%b %d'))
    return fullDate
