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
import awn
import cairo
import gnome.ui
import gnomedesktop
import time

from stacks_backend import *
from stacks_backend_file import *
from stacks_backend_folder import *
from stacks_config import *
from stacks_launcher import LaunchManager
from stacks_icons import IconFactory
from stacks_vfs import VfsUri

import stacks_gui_trasher
import stacks_gui_curved
import stacks_gui_dialog

"""
Main Applet class
"""
class StacksApplet (awn.AppletSimple):

    # Awn applet
    effects = None
    drag_timer = None
    drag_open_timeout = 500

    gui = None
    gui_type = 0
    active_gui = -1

    # Structures
    backend = None

    # Status values
    dialog_visible = False
    just_dragged = False

    # Basically drop everything to everything
    dnd_targets = [("text/uri-list", 0, 0), ("text/plain", 0, 1)]

    # Default configuration values, are overruled while reading config
    client = None
    config = {}

    def __init__ (self, uid, panel_id):
        self.awn = awn
        awn.AppletSimple.__init__(self, "stacks", uid, panel_id)

        gobject.signal_new("stacks-gui-hide", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ())
        gobject.signal_new("stacks-gui-show", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ())
        gobject.signal_new("stacks-gui-toggle", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ())
        gobject.signal_new("stacks-gui-destroy", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ())
        gobject.signal_new("stacks-gui-config", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ())
        gobject.signal_new("stacks-config-changed", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
        gobject.signal_new("stacks-item-removed", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (gtk.ListStore, gtk.TreeIter,))
        gobject.signal_new("stacks-item-created", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, (gtk.ListStore, gtk.TreeIter,))
        gobject.signal_new("stacks-gui-request-hide", StacksApplet, gobject.SIGNAL_RUN_LAST,
                gobject.TYPE_NONE, ())


        # initalize variables
        self.effects = self.get_effects()

        # connect to events
        self.connect("button-release-event", self.applet_button_cb)
        self.connect("enter-notify-event", self.applet_enter_cb)
        self.connect("drag-data-received", self.applet_drop_cb)
        self.connect("drag-motion", self.applet_drag_motion_cb)
        self.connect("drag-leave", self.applet_drag_leave_cb)
        self.connect("size-changed", self.applet_size_changed_cb)

        # read configuration
        #self.gconf_client.notify_add(self.gconf_path, self.backend_gconf_cb)
        self.client = awn.config_get_default_for_applet(self)
        self.config = get_config_dict(self.client, self.get_uid())

        self.set_gui(self.config['gui_type'])


    """
    Functions concerning the Applet
    """
    # Launch the preferences dialog
    def applet_menu_pref_cb(self, widget):
        cfg = StacksConfig(self)


    # Launch the about dialog
    def applet_menu_about_cb(self, widget):
        cfg = StacksConfig(self)
        cfg.set_current_page(-1)


    # Bar size changed
    def applet_size_changed_cb(self, widget, size):
        self.size = size
        self.applet_set_icon(None)


    # On enter -> show the title of the stack
    def applet_enter_cb (self, widget, event):
        title = self.backend.get_title()
        if self.config['item_count']:
            n_items = self.backend.get_number_items()
            if n_items > 0:
                title += " (" + str(n_items) + ")"
        self.set_tooltip_text(title)
        return False


    def applet_menu_gui_cb(self, widget):
        self.emit("stacks-gui-destroy")
        if self.gui_type == STACKS_GUI_DIALOG:
            self.gui = stacks_gui_curved.StacksGuiCurved(self)
            self.gui_type = STACKS_GUI_CURVED
        else:
            self.gui = stacks_gui_dialog.StacksGuiDialog(self)
            self.gui_type = STACKS_GUI_DIALOG

        self.client.set_int(GROUP_DEFAULT, "gui_type", self.gui_type)

    # set the gui type
    def set_gui(self,gui_type = 1):
        self.emit("stacks-gui-destroy")
        if gui_type == STACKS_GUI_CURVED:
            self.gui = stacks_gui_curved.StacksGuiCurved(self)
        elif gui_type == STACKS_GUI_TRASHER:
            self.gui = stacks_gui_trasher.StacksGuiTrasher(self)
        else:
            self.gui = stacks_gui_dialog.StacksGuiDialog(self)
        self.backend_get_config()
        #print "Setting dialog type to ", gui_type


    # On mouseclick on applet ->
    # * hide the dialog and show the context menu on button 3
    # * open the backend on button 2
    # * show/hide the dialog on button 1 (if backend not empty)
    def applet_button_cb(self, widget, event):
        if event.button == 3:
            # right click
            self.emit("stacks-gui-hide")
            # create popup menu
            popup_menu = self.create_default_menu()
            # get list of backend specified menu items
            items = self.backend.get_menu_items()
            if items:
                for i in items:
                    popup_menu.append(i)
            pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
            popup_menu.append(pref_item)
            popup_menu.append(gtk.SeparatorMenuItem())

            about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
            popup_menu.append(about_item)
            pref_item.connect_object("activate",self.applet_menu_pref_cb,self)
            about_item.connect_object("activate",self.applet_menu_about_cb,self)
            popup_menu.show_all()
            popup_menu.popup(None, None, None, event.button, event.time)
        elif event.button == 2:
            # middle click
            self.backend.open()
        else:
            # left click
            if not self.backend.is_empty():
                self.emit("stacks-gui-toggle")
            #self.get_icon().get_tooltip().hide(self)


    def applet_drag_leave_cb(self, widget, context, time):
        self.effects.stop(awn.EFFECT_LAUNCHING)
        if self.drag_timer:
            gobject.source_remove(self.drag_timer)
        self.drag_timer = None;
        self.emit("stacks-gui-request-hide")


    def applet_drag_motion_cb(self, widget, context, x, y, time):
        self.effects.start(awn.EFFECT_LAUNCHING)
        if self.drag_timer:
            gobject.source_remove(self.drag_timer)
        self.drag_timer = gobject.timeout_add (self.drag_open_timeout, self.show_gui )
        return True

    def show_gui(self):
        if self.drag_timer:
            gobject.source_remove(self.drag_timer)
        self.drag_timer = None;
        self.emit("stacks-gui-show")

    # On drag-drop on applet icon ->
    # * add each uri in the list to the backend
    # * set "full" icon as applet icon
    # --
    # For direct feedback "feeling"
    # add drop source to stack immediately,
    # and prevent duplicates @ monitor callback
    def applet_drop_cb(self, widget, context, x, y,
                            selection, targetType, time):
        pixbuf = None
        vfs_uris = []
        for uri in selection.data.split():
            try:
                vfs_uris.append(VfsUri(uri))
            except TypeError:
                pass
        if vfs_uris:
            self.backend.add(vfs_uris, context.action)
        context.finish(True, False, time)
        return True

    def applet_set_icon(self, pixbuf):
        # setting applet icon
        if not self.backend.is_empty():
            if not pixbuf:
                pixbuf = self.backend.get_random_pixbuf()
            if pixbuf: return self.applet_set_full_icon(pixbuf)
        self.applet_set_empty_icon()

    # Set the empty icon as applet icon
    def applet_set_empty_icon(self):
        icon = IconFactory().load_icon(self.config['icon_empty'],
                                       self.get_size())
        if icon: self.set_icon_pixbuf(icon)


    # Set the full icon as applet icon
    def applet_set_full_icon(self, pixbuf):
        size = self.get_size()
        icon = IconFactory().load_icon(self.config['icon_full'], size)
        if self.config['composite_icon'] \
                and isinstance(icon, gtk.gdk.Pixbuf) \
                and isinstance(pixbuf, gtk.gdk.Pixbuf):
            pixbuf = IconFactory().scale_to_bounded(pixbuf, 0.9 * size)
            cx = (size-pixbuf.get_width())/2
            cy = (size-pixbuf.get_height())/2
            trans = gdk.Pixbuf(
                    pixbuf.get_colorspace(),
                    True,
                    pixbuf.get_bits_per_sample(),
                    size,
                    size)
            trans.fill(0x00000000)
            pixbuf.composite(
                    trans,
                    cx, cy,
                    pixbuf.get_width(),
                    pixbuf.get_height(),
                    cx, cy, 1, 1,
                    gtk.gdk.INTERP_BILINEAR, 255)
            icon.composite(
                    trans, 0,0,
                    size, size,
                    0, 0, 1, 1,
                    gtk.gdk.INTERP_BILINEAR, 255)
            icon = trans
        if icon: self.set_icon_pixbuf(icon)


    # only enable link action if we have a FILE type backend
    def applet_setup_drag_drop(self):
        self.drag_dest_set( gtk.DEST_DEFAULT_ALL,
                            self.dnd_targets,
                            self.config['fileops'])


    """
    Functions concerning the Backend
    """
    def backend_gconf_cb(self, gconf_client, *args, **kwargs):
        self.emit("stacks-gui-hide")
        self.backend_get_config()

    def backend_item_created_cb(self, widget, iter):

    	if self.backend.get_store().iter_is_valid(iter):
			self.emit("stacks-item-created", self.backend.get_store(), iter)
			pixbuf = self.backend.get_store().get_value(iter, COL_ICON)
			self.applet_set_icon(pixbuf)
        else:
        	print "ERROR in STACK: invalid iter!?  (stacks_applet.py)"



    def backend_item_removed_cb(self, widget, iter):
        self.emit("stacks-item-removed", self.backend.get_store(), iter)
        if iter and not self.backend.is_empty():
            pixbuf = self.backend.get_store().get_value(iter, COL_ICON)
        else:
            pixbuf = None
        self.applet_set_icon(pixbuf)

    def backend_attention_cb(self, widget, backend_type):
        self.effects.start_ex(awn.EFFECT_ATTENTION, max_loops=1)

    def backend_get_config(self):
        self.config = get_config_dict(self.client, self.get_uid())
        self.emit("stacks-config-changed", self.config)

        # setup dnd area
        self.applet_setup_drag_drop()

        # destroy backend
        if self.backend:
            self.backend.destroy()

        # create new backend of specified type
        _config_backend_type = self.config['backend_type']
        if _config_backend_type == BACKEND_TYPE_FOLDER:
            self.backend = FolderBackend(self,
                    self.config['backend'], self.config['icon_size'])
        else:   # BACKEND_TYPE_FILE:
            self.backend = FileBackend(self,
                    self.config['backend'], self.config['icon_size'])

        # read the backends contents and connect to its signals
        self.backend.read()
        self.backend.connect("item-created", self.backend_item_created_cb)
        self.backend.connect("item-removed", self.backend_item_removed_cb)
        self.backend.connect("attention", self.backend_attention_cb)
        self.applet_set_icon(None)

if __name__ == "__main__":
    print sys.argv[1:]
    awn.init (sys.argv[1:])
    # might needed to request passwords from user
    gnome.ui.authentication_manager_init()
    applet = StacksApplet (awn.uid, awn.panel_id)
    awn.embed_applet (applet)
    applet.show_all()
    gtk.main()
