import os
import gtk
import gtk.glade
from gtk import gdk
import gconf
import time
import tempfile
import cairo

class dgTime:

  #temp directory
  tmp_dir   = tempfile.gettempdir()
  tmp_image = os.path.join(tmp_dir, 'digitalclock.png')

  curY = 0
  curX = 0
  shadow_offset = 1

  def __init__(self, prefs, awn):
    self.awn = awn
    self.prefs = prefs
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

    cs.write_to_png (self.tmp_image)
    new_icon = gdk.pixbuf_new_from_file(self.tmp_image)
    self.awn.set_temp_icon(new_icon)
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
    am_pm = ''
    cur_time = time.localtime()
    h = cur_time[3]
    m = cur_time[4]
    s = cur_time[5]

    if self.prefs['hour12']:
      if h > 12:
        h = str(h-12)
        am_pm = " PM"
      elif h == 12:
 	am_pm = " PM"
      elif h == 0:
        h = 12
        am_pm = " AM"
      else:
        am_pm = " AM"
    else:
      h = "%02d" % (h)
    m = "%02d" % (m)
    s = "%02d" % (s)

    fullDate.append(str(h) + ":" + m + am_pm)
    fullDate.append(time.strftime("%a"))
    fullDate.append(time.strftime("%b") + " " + time.strftime("%d"))
    return fullDate
