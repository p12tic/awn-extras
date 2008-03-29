#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Name:        comic.py
# Version:     .5.
# Date:        10-15-07
# Description: A python Applet for the avant-windows-navigator to display comic strips.
#
# Authors:     cj13
#
import gtk
from gtk import gdk
import cairo

class ComicDialog(gtk.DrawingArea):
	def __init__(self):
		gtk.DrawingArea.__init__(self)
		self.connect("expose_event", self.expose)

	def expose(self,widget,event):
		icon_name = '/tmp/dilbert.gif'
		icon = gdk.pixbuf_new_from_file(icon_name)
		dim = [icon.get_width(),icon.get_height()]
		self.set_size_request(dim[0], dim[1])

		context = widget.window.cairo_create()
		context.set_source_rgb(0,0,0)

		context.set_source_pixbuf(icon,1,1)
		context.fill()
		context.paint()
		return False

