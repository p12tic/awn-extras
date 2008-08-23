#!/usr/bin/env python

# Copyright (c) 2007 Tomas Kramar (kramar.tomas@gmail.com), Jonathan Rauprich (joni@noplu.de)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import sys
import gtk
import cairo
import os

class ImageProducer:

  # dimensions of the cover picture
  WIDTH = 128.0 
  HEIGHT = 112.0
  # look at the image "icons/top.png"
  # it is an image of empty cd cover
  # the cover image is put in the area between borders
  BORDER_TOP = 3.0
  BORDER_LEFT = 18.0
  BORDER_BOTTOM = 8.0
  BORDER_RIGHT = 6.0

  def __init__(self, height):
      self.path = os.path.dirname(__file__)
      
      self.calculate_cover_dimensions(height)
      
  def calculate_cover_dimensions(self, height):
      #this is needed to make the generated cover fit the height of awn bar
      #cover dimensions written in uppercase are default - the borders have been measured
      #now we need to scale it, recalculate new borders and width - the height is not calculated - it is the height of awn bar
            
      scale_factor = height / self.HEIGHT
      self.HEIGHT = float(height) # casting it to float is really important due to the way how python division works
      self.WIDTH = round(self.WIDTH * scale_factor)
      self.BORDER_TOP = round(self.BORDER_TOP * scale_factor)
      self.BORDER_LEFT = round(self.BORDER_LEFT * scale_factor)
      self.BORDER_BOTTOM = round(self.BORDER_BOTTOM * scale_factor)
      self.BORDER_RIGHT = round(self.BORDER_RIGHT * scale_factor)     
      

  def generate_cover(self, filename):
      # first step is to create a surface from jpg image and scale it down

      pixbuf = gtk.gdk.pixbuf_new_from_file(filename)

      image_width = self.WIDTH - self.BORDER_RIGHT - self.BORDER_LEFT
      image_height = self.HEIGHT - self.BORDER_TOP - self.BORDER_BOTTOM
 
      surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(image_width), int(image_height))
      ctx = cairo.Context(surface)

      x_scale = image_width / pixbuf.get_width() 
      y_scale = image_height / pixbuf.get_height()
      ctx.scale(x_scale,y_scale)

      ct = gtk.gdk.CairoContext(ctx)
      ct.set_source_pixbuf(pixbuf,0,0)
      ctx.paint()

      # we want to create an effect of cd in a box,
      # so the cover go first, and then the cd box on top
      f_surface =  cairo.ImageSurface(cairo.FORMAT_ARGB32, int(self.WIDTH), int(self.HEIGHT))
      f_ctx = cairo.Context(f_surface)
      f_ctx.set_source_surface(surface, self.BORDER_LEFT, self.BORDER_TOP)
      f_ctx.rectangle(self.BORDER_LEFT, self.BORDER_TOP, self.WIDTH, self.HEIGHT)

      f_ctx.fill()

      base = cairo.ImageSurface.create_from_png(self.path + "/icons/top.png")
      x_scale = self.WIDTH / base.get_width()
      y_scale = self.HEIGHT / base.get_height()
     
      f_ctx.scale(x_scale, y_scale)

      #f_ctx.new_path()
      f_ctx.set_source_surface(base)
      f_ctx.paint()     
	
      f_surface.write_to_png("/tmp/cover")      

      return "/tmp/cover"

  def get_default_cover(self):
      return "icons/default.png"      

if __name__ == '__main__':  
    app = ImageProducer(40)
    app.generate_cover("icons/sample_cover.jpg")
