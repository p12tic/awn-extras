#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is a class to handle drawing a simulated seven-segment LED.
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
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import gconf
import pango
import awn
import cairo
from StringIO import StringIO
import datetime
import gc

# locale stuff
APP="awn-calendar"
DIR="locale"
import locale
import gettext
#locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class SevenSegLed:

   #
   #   ---0---
   #  |       |
   #  5       1
   #  |       |
   #   ---6---
   #  |       |
   #  4       2
   #  |       |
   #   ---3---
   #
	digit_map = { 0 : [ True,  True,  True,  True,  True,  True,  False ],
	              1 : [ False, True,  True,  False, False, False, False ],
	              2 : [ True,  True,  False, True,  True,  False, True  ],
	              3 : [ True,  True,  True,  True,  False, False, True  ],
	              4 : [ False, True,  True,  False, False, True,  True  ],
	              5 : [ True,  False, True,  True,  False, True,  True  ],
	              6 : [ True,  False, True,  True,  True,  True,  True  ],
	              7 : [ True,  True,  True,  False, False, False, False ],
	              8 : [ True,  True,  True,  True,  True,  True,  True  ],
	              9 : [ True,  True,  True,  True,  False, True,  True  ] 
	            }

	def __init__(self, ct):
		self.ct = ct

	def next_dest(self, digit, segment, x, y):
		if (self.digit_map[digit][segment] == True):
			self.ct.line_to(x,y)
		else:
			self.ct.move_to(x,y)

	def draw(self, digit, ct, x0, y0, x1, y1):
		ct.set_line_width(5.0)
		ct.move_to(x0,y0)	
		mid_y = (y0 + y1)/2
		self.next_dest(digit, 0, x1, y0)
		self.next_dest(digit, 1, x1, mid_y)
		self.next_dest(digit, 6, x0, mid_y)
		self.next_dest(digit, 4, x0, y1)
		self.next_dest(digit, 3, x1, y1)
		self.next_dest(digit, 2, x1, mid_y)
		self.next_dest(digit, 6, x0, mid_y)
		self.next_dest(digit, 5, x0, y0)
		ct.stroke()
				

		
		
		
