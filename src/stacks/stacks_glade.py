#!/usr/bin/env python

# Copyright (c) 2007 Timon ter Braak
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

import gobject
import gtk
import gtk.glade

class GladeWindow(gobject.GObject):
    """
    Base class for dialogs or windows backed by glade interface definitions.

    Example:
    class MyWindow(GladeWindow):
        glade_file = 'my_glade_file.glade'
        ...

    Remember to chain up if you customize __init__(). Also note that GladeWindow
    does *not* descend from GtkWindow, so you can't treat the resulting object
    as a GtkWindow. The show, hide, destroy, and present methods are provided as
    convenience wrappers.
    """

    glade_file = None
    window = None

    def __init__(self, parent=None):
        gobject.GObject.__init__(self)
        wtree = gtk.glade.XML(self.glade_file)
        self.widgets = {}
        for widget in wtree.get_widget_prefix(''):
            wname = widget.get_name()
            if isinstance(widget, gtk.Window):
                    assert self.window == None
                    self.window = widget
                    continue

            if wname in self.widgets:
                raise AssertionError("Two objects with same name (%s): %r %r"
                                     % (wname, self.widgets[wname], widget))
            self.widgets[wname] = widget

        if parent is not None:
            self.window.set_transient_for(parent)

        wtree.signal_autoconnect(self)

        self.destroy = self.window.destroy
        self.show = self.window.show
        self.hide = self.window.hide
        self.present = self.window.present

gobject.type_register(GladeWindow)
