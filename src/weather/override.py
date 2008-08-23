#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007, 2008:
#   Isaac J.
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#
# Contains a subclassed Dialog to show a transparent dialog.
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

import awn, cairo

class Dialog(awn.AppletDialog):
    def __init__(self, applet):
        awn.AppletDialog.__init__(self, applet)
        self.connect("expose-event",self._expose)

    def _expose(self, widget, event):
        self.position_reset()
        cr = widget.window.cairo_create()
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
       
        for c in self.get_children():
          self.propagate_expose(c, event)

        return True
