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
import locale
import gettext

from stacks_backend import *
from stacks_backend_file import *
from stacks_backend_folder import *
from stacks_backend_plugger import *
from stacks_backend_trasher import *
from stacks_config import *
from stacks_launcher import LaunchManager
from stacks_icons import IconFactory
from stacks_vfs import VfsUri

import stacks_gui_trasher
import stacks_gui_curved
import stacks_gui_dialog



APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext


"""
Main Applet class
"""
class StacksApplet (awn.AppletSimple):

    # Awn applet
    uid = None
    orient = None
    height = None
    title = None
    effects = None

    gui = None
    gui_type = 0
    active_gui = -1

    # GConf
    gconf_path = None
    gconf_client = None

    # Structures
    backend = None

    # Status values
    dialog_visible = False
    just_dragged = False

    # Basically drop everything to everything
    dnd_targets = [("text/uri-list", 0, 0), ("text/plain", 0, 1)]

    # Default configuration values, are overruled while reading config
    config = {}

    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__(self, uid, orient, height)

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


        # initalize variables
        self.uid = uid
        self.orient = orient
        self.height = height
        self.title = awn.awn_title_get_default()
        self.effects = self.get_effects()

        # get GConf client and read configuration
        self.gconf_path = "/apps/avant-window-navigator/applets/stacks/" + self.uid
        self.gconf_client = gconf.client_get_default()
        self.gconf_client.notify_add(self.gconf_path, self.backend_gconf_cb)

        # connect to events
        self.connect("button-release-event", self.applet_button_cb)
        self.connect("enter-notify-event", self.applet_enter_cb)
        self.connect("leave-notify-event", self.applet_leave_cb)
        self.connect("drag-data-received", self.applet_drop_cb)
        self.connect("drag-motion", self.applet_drag_motion_cb)
        self.connect("drag-leave", self.applet_drag_leave_cb)
        self.connect("orientation-changed", self.applet_orient_changed_cb)
        self.connect("height-changed", self.applet_height_changed_cb)

        # experimental: makeing more guis available
        #self.gui_type = self.gconf_client.get_int(self.gconf_path + "/gui_type")
        """
        self.gui_type = self.config['gui_type']

        if self.gui_type <= 0 or self.gui_type > 3:
            self.gui_type = STACKS_GUI_DIALOG

        if self.gui_type == STACKS_GUI_CURVED:
            self.gui = stacks_gui_curved.StacksGuiCurved(self)
        elif self.gui_type == STACKS_GUI_TRASHER:
            self.gui = stacks_gui_trasher.StacksGuiTrasher(self)
        else:
            self.gui = stacks_gui_dialog.StacksGuiDialog(self)
        """

        #self.gui_type = STACKS_GUI_DIALOG
        #self.gui = stacks_gui_dialog.StacksGuiDialog(self)
        
        #self.backend_get_config()
        self.config = get_config_from_gconf(self.gconf_client, self.gconf_path, self.uid)
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


    # not supported yet, maybe in future
    def applet_orient_changed_cb(self, widget, orient):
        return


    # Bar height changed
    def applet_height_changed_cb(self, widget, height):
        self.height = height


    # On enter -> show the title of the stack
    def applet_enter_cb (self, widget, event):
        title = self.backend.get_title()
        if self.config['item_count']:
            n_items = self.backend.get_number_items()
            if n_items > 0:
                title += " (" + str(n_items) + ")"
        self.title.show(self, title)


    # On leave -> hide the title of the stack
    def applet_leave_cb (self, widget, event):
        self.title.hide(self)

    def applet_menu_gui_cb(self, widget):
        self.emit("stacks-gui-destroy")
        if self.gui_type == STACKS_GUI_DIALOG:
            self.gui = stacks_gui_curved.StacksGuiCurved(self)
            self.gui_type = STACKS_GUI_CURVED
        else:
            self.gui = stacks_gui_dialog.StacksGuiDialog(self)
            self.gui_type = STACKS_GUI_DIALOG
        
        self.gconf_client.set_int(
                self.gconf_path + "/gui_type", self.gui_type )

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
        print "Setting dialog type to ", gui_type


    # On mouseclick on applet ->
    # * hide the dialog and show the context menu on button 3
    # * open the backend on button 2
    # * show/hide the dialog on button 1 (if backend not empty) 
    def applet_button_cb(self, widget, event):
        if event.button == 3:
            # right click
            self.emit("stacks-gui-hide")
            # create popup menu
            popup_menu = gtk.Menu()
            # get list of backend specified menu items
            items = self.backend.get_menu_items()
            if items:
                for i in items:
                  popup_menu.append(i)
                popup_menu.append(gtk.SeparatorMenuItem())
            #gui_item = gtk.CheckMenuItem(label=_("Use experimental gui"))
            #gui_item.set_active(self.gui_type > STACKS_GUI_DIALOG)
            #gui_item.connect_object("toggled", self.applet_menu_gui_cb, self)
            #popup_menu.append(gui_item)
            pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
            popup_menu.append(pref_item)
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


    def applet_drag_leave_cb(self, widget, context, time):
        awn.awn_effect_stop(self.effects, "hover")


    def applet_drag_motion_cb(self, widget, context, x, y, time):
        awn.awn_effect_start(self.effects, "hover")
        return True


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
        icon = IconFactory().load_icon(self.config['icon_empty'], self.height)
        if icon: self.set_temp_icon(icon)


    # Set the full icon as applet icon
    def applet_set_full_icon(self, pixbuf):
        icon = IconFactory().load_icon(self.config['icon_full'], self.height)
        if self.config['composite_icon'] \
                and isinstance(icon, gtk.gdk.Pixbuf) \
                and isinstance(pixbuf, gtk.gdk.Pixbuf):
            pixbuf = IconFactory().scale_to_bounded(pixbuf, 0.9 * self.height)
            cx = (self.height-pixbuf.get_width())/2
            cy = (self.height-pixbuf.get_height())/2
            trans = gdk.Pixbuf(
                    pixbuf.get_colorspace(),
                    True,
                    pixbuf.get_bits_per_sample(),
                    self.height,
                    self.height)
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
                    self.height, self.height,
                    0, 0, 1, 1,
                    gtk.gdk.INTERP_BILINEAR, 255)
            icon = trans
        if icon: self.set_temp_icon(icon)


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
        awn.awn_effect_start(self.effects, "attention")
        time.sleep(1.0)
        awn.awn_effect_stop(self.effects, "attention")

    def backend_get_config(self):
        self.config = get_config_from_gconf(self.gconf_client, self.gconf_path, self.uid)
        self.emit("stacks-config-changed", self.config)

        # setup dnd area
        self.applet_setup_drag_drop()

        # destroy backend
        if self.backend:
            self.backend.destroy()

        # create new backend of specified type
        _config_backend_type = self.gconf_client.get_int(
                self.gconf_path + "/backend_type")
        if _config_backend_type == BACKEND_TYPE_FOLDER:
            self.backend = FolderBackend(self,
                    self.config['backend'], self.config['icon_size'])
        elif _config_backend_type == BACKEND_TYPE_PLUGGER:
            self.backend = PluggerBackend(self,
                    self.config['backend'], self.config['icon_size'])
        elif _config_backend_type == BACKEND_TYPE_TRASHER:
            self.backend = TrashBackend(self,
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
    awn.init (sys.argv[1:])
    # might needed to request passwords from user
    gnome.ui.authentication_manager_init()
    applet = StacksApplet (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all()
    gtk.main()
