#!/usr/bin/env python

# Copyright (c) 2007 Randal Barlow
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
import os
import gtk
from gtk import gdk
import gobject
import pango
import gconf
import awn
import cairo
import gnome.ui
import gnomedesktop
import time

from stacks_backend import *
from stacks_backend_file import *
from stacks_backend_folder import *
from stacks_backend_plugger import *
from stacks_backend_trasher import *
from stacks_config import StacksConfig
from stacks_launcher import LaunchManager
from stacks_icons import IconFactory
from stacks_vfs import VfsUri

from stacks_gui_dialog import StacksGuiDialog


class StacksGuiTrasher(StacksGuiDialog):

    bt_empty = None

    def __init__(self, applet):
        StacksGuiDialog.__init__(self, applet)


    def dialog_show_new(self, page=0):
        StacksGuiDialog.dialog_show_new(self, page)
        if self.navbuttons is None:
            self.navbuttons = gtk.HButtonBox()
            self.navbuttons.set_layout(gtk.BUTTONBOX_EDGE)
            self.navbuttons.show()
            self.dialog.add(self.navbuttons)

        if self.bt_empty is None:
            self.bt_empty = gtk.Button(stock=gtk.STOCK_DELETE)
            self.bt_empty.set_use_stock(True)
            self.bt_empty.set_relief(gtk.RELIEF_NONE)
            self.bt_empty.connect("clicked", self.empty_trash)
            self.bt_empty.show()
            self.navbuttons.add(self.bt_empty)
            self.navbuttons.reorder_child(self.bt_empty, 1)

    def empty_trash(self, widget):
        self.applet.backend.clear()
