#!/usr/bin/python
"""
Python Icon - An example System tray Icon
Copyright (c) 2008 Nathan Howard (triggerhapp@googlemail.com)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

# Very litterally, this creates a small window and tells the system tray
# it wants to be embedded. For RGB system trays, this will probably
# cause it a problem since, even though it reads _NET_SYSYTEM_TRAY_VISUAL
# it ignores it and aggressively uses RGBA.

# Since this was created to test RGBA PyNot, why not?

# currently it chooses a random colour, with 0.6 alpha,
# and fills its window with it, OR draws the "default application" icon

# Hacked together from small fragments I wrote to do the same thing in
# PyNot

import sys
from Xlib import X, display, error,Xatom,Xutil
from Xlib.ext import shape
import Xlib.protocol.event
import gtk
from gtk import gdk
import gobject      #Gtk/Gdk/GObj for interfacing with the applet
import select
import random
import cairo

dsp=display.Display()
scr = dsp.screen()
root = scr.root

def sendEv(dest,type,data,evty):
    data = (data+[0]*(5-len(data)))[:5]
    myevent=Xlib.protocol.event.ClientMessage(
               window=dest.id,
               client_type=type,
               data=(32,(data)),
               type=X.ClientMessage
               )
    dest.send_event(myevent,event_mask=evty)
_OPCODE = dsp.intern_atom("_NET_SYSTEM_TRAY_OPCODE")
_VISUAL = dsp.intern_atom("_NET_SYSTEM_TRAY_VISUAL")
_XEMBED_INFO= dsp.intern_atom("_XEMBED_INFO")
_MANAGER = dsp.intern_atom("_NET_SYSTEM_TRAY_S%d"%dsp.get_default_screen())
_DESKTOP = dsp.intern_atom("_NET_WM_DESKTOP")

tray= dsp.get_selection_owner(_MANAGER)
traywin= dsp.create_resource_object("window",tray.id)

print traywin.get_full_property(_VISUAL,Xatom.VISUALID)

dudwindow = gtk.Window()
dudwindow.set_title("PyNoT Test Icon")
dudwindow.set_decorated(False)
dudwindow.add_events(gdk.BUTTON_RELEASE_MASK)
dudwindow.add_events(gdk.EXPOSURE_MASK)
dudwindow.add_events(gdk.BUTTON_PRESS_MASK)
dudwindow.set_app_paintable(True)
screen = dudwindow.get_screen()
colormap = screen.get_rgba_colormap()
#print colormap
dudwindow.set_colormap(colormap)
dudwindow.show()
wind_id= dudwindow.window.xid
wind=dsp.create_resource_object("window",wind_id)

def expose(widget, event):
    if(random.random() < 0.8):
        cr=dudwindow.window.cairo_create()
        cr.set_source_rgba(random.random(),random.random(),random.random(),
                           0.6)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
    else:
        cr=dudwindow.window.cairo_create()
        cr.set_source_rgba(0.0,0.0,0.0,0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        imagefile = "/usr/share/icons/application-default-icon.png"
        image=cairo.ImageSurface.create_from_png(imagefile)
        pattern =cairo.SurfacePattern(image)
        cr.set_source(pattern)
        cr.paint()



def button(widget,event):
    print event.button

dudwindow.connect("expose-event",expose)
dudwindow.connect("button-press-event",button)

wind.configure(width=24,height=24)

sendEv(traywin,_OPCODE,[X.CurrentTime,0L,wind.id,0L,0L],X.NoEventMask)

dsp.flush()

gtk.main()

