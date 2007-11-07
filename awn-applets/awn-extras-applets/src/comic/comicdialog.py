#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
# by Chris Johnson
# Much code was taken from Mike (mosburger) Desjardins <desjardinsmike@gmail.com> 
# Weather applet
# 
# This is the dialog for a comic applet for Avant Window Navigator.
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
#
import gtk
from gtk import gdk
import cairo
import wnck
import Image

class ComicDialog(gtk.DrawingArea):
	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self.connect("expose_event", self.expose)
		
	def expose(self,widget,event):
		comic = Image.open("./dilbert.gif")
		dim = comic.size
		comic.save("./dilbert.gif")
		
		self.set_size_request(dim[0], dim[1])
		
		context = widget.window.cairo_create()
		context.set_source_rgb(0,0,0)
		icon_name = './dilbert.gif'
		icon = gdk.pixbuf_new_from_file(icon_name)
		
		context.set_source_pixbuf(icon,1,1)
		context.fill()
		context.paint()
		return False
		
