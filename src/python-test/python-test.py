#!/usr/bin/python
#
#       AWN Test Python Applet
#
#       Copyright (c) 2008 Pavel Panchekha <pavpanchekha@gmail.com>
#
#       This library is free software; you can redistribute it and/or
#       modify it under the terms of the GNU Lesser General Public
#       License as published by the Free Software Foundation; either
#       version 2 of the License, or (at your option) any later version.
#
#       This library is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#       Lesser General Public License for more details.
#
#       You should have received a copy of the GNU Lesser General Public
#       License along with this library; if not, write to the
#       Free Software Foundation, Inc., 59 Temple Place - Suite 330,
#       Boston, MA 02111-1307, USA.

from awn.extras import AWNLib # Interact with awn
import gtk # For GUI building

if __name__ == "__main__":
    applet = AWNLib.initiate() # Create a new applet
    applet.title.set("Test python applet") # This is the hover name
    applet.icon.theme("gtk-apply") # Applet icon

    #applet.connect("enter-notify-event", lambda x, y: applet.icon.theme("gtk-apply"))
    #applet.connect("leave-notify-event", lambda x, y: applet.icon.theme("gtk-cancel"))

    # According to the guidelines, this is wrong.
    # Do not do anything on hover but show/hide the title
    # Which AWNLib does for you

    dlog = applet.dialog.new("main") # "main" will be the left-click dialog
    button = gtk.Button(stock="gtk-apply") # Standard GTK
    dlog.add(button) # Again, GTK. dialog's are Box's
    AWNLib.start(applet) # Show the actual icon. Get here as fast as possible.
