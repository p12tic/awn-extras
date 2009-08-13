#!/usr/bin/python
# PyNotConfig - Awn Notification/system tray config manager.
#
# Copyright (C) 2008 Nathan Howard (triggerhapp@googlemail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

import pygtk
pygtk.require("2.0")
import gtk
from gtk import glade

import awn

glade_file = os.path.join(os.path.dirname(__file__), "pynot-rgba.glade")

global D_CUSTOM_Y, D_HIGH, D_ICONSIZE
D_CUSTOM_Y = 10
D_HIGH = 2
D_ICONSIZE = 24

awn_options = awn.Config("pynot-rgba", None)

CUSTOM_Y = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y")
HIGH = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "HIGH")
ICONSIZE = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE")

if HIGH == 0:
    HIGH = D_HIGH
    CUSTOM_Y = D_CUSTOM_Y
    ICONSIZE = D_ICONSIZE
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y", CUSTOM_Y)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "HIGH", HIGH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE", ICONSIZE)

if ICONSIZE == 0:
    ICONSIZE = D_ICONSIZE


class PreferencesDialog(gtk.Dialog):

    """A Dialog window that has the title "PyNot Preferences",
    uses the applet's logo as its icon and has a Close button.

    """

    def __init__(self):
        gtk.Dialog.__init__(self, flags=gtk.DIALOG_NO_SEPARATOR)

        self.set_resizable(False)
        self.set_border_width(5)

        self.set_title("PyNot Preferences")
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)

        self.set_icon(gtk.gdk.pixbuf_new_from_file_at_size(
                                os.path.dirname(__file__)+"/PyNot.png", 48, 48))

        self.connect("response", self.response_event)

    def response_event(self, widget, response):
        if response < 0:
            gtk.main_quit()


dialog = PreferencesDialog()

prefs = glade.XML(glade_file)
prefs.get_widget("vbox-preferences").reparent(dialog.vbox)

spinbutton_column = prefs.get_widget("spinbutton-icons-per-column")
spinbutton_column.set_value(HIGH)
def column_value_changed_cb(widget):
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "HIGH", widget.get_value_as_int())
spinbutton_column.connect("value-changed", column_value_changed_cb)

spinbutton_offset = prefs.get_widget("spinbutton-offset-from-bottom")
spinbutton_offset.set_value(CUSTOM_Y)
def offset_value_changed_cb(widget):
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y", widget.get_value_as_int())
spinbutton_offset.connect("value-changed", offset_value_changed_cb)

spinbutton_size = prefs.get_widget("spinbutton-size-of-icons")
spinbutton_size.set_value(ICONSIZE)
def size_value_changed_cb(widget):
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE", widget.get_value_as_int())
spinbutton_size.connect("value-changed", size_value_changed_cb)

dialog.show_all()
gtk.main()
