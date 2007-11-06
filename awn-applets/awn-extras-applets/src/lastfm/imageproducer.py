#!/usr/bin/env python

import sys
import gtk
import cairo
import os

class ImageProducer:

  WIDTH = 45.0
  HEIGHT = 39.0
  BORDER_TOP = 1.0
  BORDER_LEFT =5.0
  BORDER_BOTTOM = 0.0
  BORDER_RIGHT = 1.0

  def __init__(self):
      self.path = os.path.dirname(__file__)

  def generate_cover(self, filename):
      # first step is to create a surface from jpg image and scale it down

      pixbuf = gtk.gdk.pixbuf_new_from_file(filename)

      image_width = self.WIDTH - self.BORDER_RIGHT - self.BORDER_LEFT
      image_height = self.HEIGHT - self.BORDER_TOP - self.BORDER_BOTTOM
 
      surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, image_width, image_height)
      ctx = cairo.Context(surface)

      x_scale = image_width / pixbuf.get_width() 
      y_scale = image_height / pixbuf.get_height()
      ctx.scale(x_scale,y_scale)

      ct = gtk.gdk.CairoContext(ctx)
      ct.set_source_pixbuf(pixbuf,0,0)
      ctx.paint()

      # we want to create an effect of cd in a box,
      # so the cover go first, and then the cd box on top
      f_surface =  cairo.ImageSurface(cairo.FORMAT_ARGB32, self.WIDTH, self.HEIGHT)
      f_ctx = cairo.Context(f_surface)
      f_ctx.set_source_surface(surface, self.BORDER_LEFT, self.BORDER_TOP)
      f_ctx.rectangle(self.BORDER_LEFT, self.BORDER_TOP, self.WIDTH, self.HEIGHT)

      f_ctx.fill()

      base = cairo.ImageSurface.create_from_png(self.path + "/icons/top_small.png")

      f_ctx.new_path()
      f_ctx.set_source_surface(base)
      f_ctx.paint()     
	
      f_surface.write_to_png("/tmp/cover")      

      return "/tmp/cover"

  def __get_default_cover(self):
      return "icons/default.png"      

if __name__ == '__main__':  
    app = ImageProducer()
    app.generate_cover("icons/sample_cover.jpg")
