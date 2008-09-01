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
from stacks_config import StacksConfig
from stacks_launcher import LaunchManager
from stacks_icons import IconFactory
from stacks_vfs import *

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext


"""
Main Applet class
"""
class StacksGuiDialog:

    # Structures
    dialog = None
    hbox = None
    table = None
    navbuttons = None
    bt_left = None
    bt_right = None

    applet = None
    config = None
    store = None
    current_page = 0
    gui_visible = False

    # Status values
    context_menu_visible = False
    just_dragged = False

    hide_timer = None
    hide_timeout = 500
    
    dnd_targets = [("text/uri-list", 0, 0), ("text/plain", 0, 1)]

    signal_ids = []

    def __init__ (self, applet):
        # connect to events
        self.applet = applet
        self.signal_ids.append(applet.connect("stacks-gui-hide", self._stacks_gui_hide_cb))
        self.signal_ids.append(applet.connect("stacks-gui-show", self._stacks_gui_show_cb))
        self.signal_ids.append(applet.connect("stacks-gui-toggle", self._stacks_gui_toggle_cb))
        self.signal_ids.append(applet.connect("stacks-gui-destroy", self._destroy_cb))
        self.signal_ids.append(applet.connect("stacks-config-changed", self._stacks_config_changed_cb))
        self.signal_ids.append(applet.connect("stacks-item-removed", self._item_removed_cb))
        self.signal_ids.append(applet.connect("stacks-item-created", self._item_created_cb))
        self.signal_ids.append(applet.connect("stacks-gui-request-hide", self._stacks_gui_request_hide))


    def _destroy_cb(self, widget):
        for id in self.signal_ids: self.applet.disconnect(id)
        if self.dialog: self.dialog.destroy()

    def _stacks_gui_hide_cb(self, widget = None):
        self.reset_hide_timer()
        if self.dialog:
            self.dialog.hide()
        self.gui_visible = False

    def _stacks_gui_show_cb(self, widget):
        self.dialog_show_new(self.current_page)
        self.gui_visible = True

    def _stacks_gui_toggle_cb(self, widget):
        if self.gui_visible: return self._stacks_gui_hide_cb(None)
        return self._stacks_gui_show_cb(None)

    def reset_hide_timer(self):
    	#print "hide timer reset"
    	if self.hide_timer:
            gobject.source_remove(self.hide_timer)
        self.hide_timer = None


    def _stacks_gui_request_hide(self, widget = None):
    	#print "request hide"

    	#if self.hide_timer == None:
    	#	self.hide_timer = gobject.timeout_add (self.hide_timeout, self._stacks_gui_hide_cb )
    	return True


    def _stacks_config_changed_cb(self, widget, config):
        self.config = config

    def _item_removed_cb(self, widget, store, iter):
        self.store = store
        if self.gui_visible:
            return self._stacks_gui_show_cb(None)

    # launches the command for a stack icon
    # -distinguishes desktop items
    def item_button_cb(self, widget, event, user_data):
        uri, mimetype = user_data
        if event.button == 3:
            self.context_menu_visible = True
            self.item_context_menu(uri).popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            if self.just_dragged:
                self.just_dragged = False
            else:
                self.item_activated_cb(None, user_data)


    def item_activated_cb(self, widget, user_data):
        uri, mimetype = user_data
        if uri.as_string().endswith(".desktop"):
            item = gnomedesktop.item_new_from_uri(
                    uri.as_string(), gnomedesktop.LOAD_ONLY_IF_EXISTS)
            if item:
                command = item.get_string(gnomedesktop.KEY_EXEC)
                #LaunchManager().launch_command(command, uri.as_string())
                LaunchManager().launch_dot_desktop(uri.as_string())
        else:
            LaunchManager().launch_uri(uri.as_string(), mimetype)


    def item_drag_data_get(
            self, widget, context, selection, info, time, vfs_uri):
        selection.set_uris([vfs_uri.as_string()])


    def item_drag_begin(self, widget, context):
        self.just_dragged = True

    def button_drag_motion(self, widget, context, x, y, time):
    	
    	return True

    def button_drag_leave(self, widget, context, time):
        self.applet.effects.stop("launching")
    	return

    def button_drag_drop(self, widget, context, x, y,
                            selection, targetType, time, target_uri):
    	self._stacks_gui_hide_cb(widget)
    	self.applet.effects.stop("launching")
    	vfs_uris = []
    	for uri in selection.data.split():
    		try:
    			vfs_uris.append(VfsUri(uri))
    		except TypeError:
    			pass                            	
    	
    	if context.action == gtk.gdk.ACTION_LINK:
    		options = gnomevfs.XFER_LINK_ITEMS
    	elif context.action == gtk.gdk.ACTION_MOVE:
    		options = gnomevfs.XFER_REMOVESOURCE
    	elif context.action == gtk.gdk.ACTION_COPY:
    		options = gnomevfs.XFER_DEFAULT
    	else:
    		return False

    	src_lst = []
    	dst_lst = []
    	vfs_uri_lst = []
    	for vfs_uri in vfs_uris:
    		dst_uri = target_uri.as_uri().append_path(vfs_uri.as_uri().short_name)
    		src_lst.append(vfs_uri.as_uri())
    		dst_lst.append(dst_uri)
    		

    	GUITransfer(src_lst, dst_lst, options)
    	
    	
    	return True

    def item_clear_cb(self, widget, uri):
        self.applet.backend.remove([uri])

    def item_menu_hide_cb(self, widget):
        self.context_menu_visible = False

    def item_context_menu(self, uri):
        self.context_menu_visible = True
        context_menu = gtk.Menu()
        del_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        context_menu.append(del_item)
        del_item.connect_object("activate", self.item_clear_cb, self, uri)
        context_menu.connect("hide", self.item_menu_hide_cb)
        context_menu.show_all()
        return context_menu


    def _item_created_cb(self, widget, store, iter):
        if store:
            self.store = store

        # get values from store
        
        vfs_uri, lbl_text, mime_type, icon, button = self.store.get(
                iter, COL_URI, COL_LABEL, COL_MIMETYPE, COL_ICON, COL_BUTTON)
        if button:
            return button

        icon_size = self.config['icon_size']
        # create new button
        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        button.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.LEAVE_NOTIFY) 

        button.drag_source_set( gtk.gdk.BUTTON1_MASK,
                                self.applet.dnd_targets,
                                self.config['fileops'])
        button.drag_source_set_icon_pixbuf(icon)
        button.connect( "button-release-event",
                        self.item_button_cb,
                        (vfs_uri, mime_type))
        button.connect( "activate",
                        self.item_activated_cb,
                        (vfs_uri, mime_type))
        button.connect( "drag-data-get",
                        self.item_drag_data_get,
                        vfs_uri)
        button.connect( "drag-begin",
                        self.item_drag_begin)
                        
        
        if mime_type == "x-directory/normal":
        	button.connect("drag-motion", self.button_drag_motion)
        	button.connect("drag-leave", self.button_drag_leave)
        	button.connect("drag-data-received", self.button_drag_drop,vfs_uri)
        	button.drag_dest_set( gtk.DEST_DEFAULT_ALL,
                            self.dnd_targets,
                            self.config['fileops'])
                            
                     
                        
        # add to vbox
        vbox = gtk.VBox(False, 4)
        button.add(vbox)
        # icon -> button.image
        image = gtk.Image()
        image.set_from_pixbuf(icon)
        image.set_size_request(icon_size, icon_size)
        vbox.pack_start(image, False, False, 0)
        # label
        label = gtk.Label(lbl_text)
        label.set_justify(gtk.JUSTIFY_CENTER)
        label.set_line_wrap(True)
        # pango layout
        layout = label.get_layout()
        lw, lh = layout.get_size()
        layout.set_width(int(1.5 * icon_size) * pango.SCALE)
        layout.set_wrap(pango.WRAP_WORD_CHAR)
        layout.set_alignment(pango.ALIGN_CENTER)
        _lbltxt = label.get_text()
        lbltxt = ""
        for i in range(layout.get_line_count()):
            length = layout.get_line(i).length
            lbltxt += str(_lbltxt[0:length]) + '\n'
            _lbltxt = _lbltxt[length:]
        label.set_text(lbltxt)
        label.set_size_request(-1, lh*2/pango.SCALE)
        # add to vbox
        vbox.pack_start(label, True, True, 0)
        vbox.set_size_request(int(1.5 * icon_size), -1)
        self.store.set_value(iter, COL_BUTTON, button)
        return button


    def dialog_show_prev_page(self, widget):
        self.dialog_show_new(self.current_page-1)


    def dialog_show_next_page(self, widget):
        self.dialog_show_new(self.current_page+1)

    def stack_drag_motion_event(self, *args):
    	self.reset_hide_timer()

    def dialog_focus_out(self, widget, event):
        if self.context_menu_visible: return
        if self.config['close_on_focusout']:
        	self._stacks_gui_hide_cb(widget)
        	
    def dialog_drag_leave_event(self, *args):
        self._stacks_gui_request_hide()        	

    def dialog_show_new(self, page=0):
        assert page >= 0
        self.current_page = page

        # create new dialog if it does not exists yet
        if not self.dialog:
            self.dialog = awn.AppletDialog (self.applet)
            self.dialog.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.LEAVE_NOTIFY |
                        gtk.gdk.DRAG_MOTION |
                        gtk.gdk.DRAG_ENTER |
                        gtk.gdk.DRAG_LEAVE |
                        gtk.gdk.DRAG_STATUS |
                        gtk.gdk.DROP_START |
                        gtk.gdk.DROP_FINISHED)
            self.dialog.set_focus_on_map(True)
            self.dialog.set_keep_above(True) 
            self.dialog.connect("focus-out-event", self.dialog_focus_out)
            self.dialog.connect("drag-leave", self.dialog_drag_leave_event)
            self.dialog.connect("drag-motion", self.stack_drag_motion_event)
            self.dialog.set_title(self.applet.backend.get_title())
            self.hbox = gtk.HBox(False, 0)
            self.dialog.add(self.hbox)

        # create dialog's internals
        rows = self.config['rows']
        cols = self.config['cols']
        self.store = self.applet.backend.get_store()
        iter = self.store.iter_nth_child(None, page * rows * cols)

        if self.table:
            for item in self.table.get_children():
                self.table.remove(item)
            self.table.destroy()

        if page > 0:
            self.table = gtk.Table(rows, cols, True)
        else:
            self.table = gtk.Table(1, 1, True)
        self.table.set_resize_mode(gtk.RESIZE_PARENT)
        self.table.set_row_spacings(0)
        self.table.set_col_spacings(0)

        x=y=0
        theres_more = False
        while iter:
            button = self.store.get_value(iter, COL_BUTTON)
            if not button:
                button = self._item_created_cb(None, None, iter)
            t = button.get_parent()
            if t:
                t.remove(button)
            self.table.attach(button, x, x+1, y, y+1)

            iter = self.store.iter_next(iter)
            x += 1
            if x == cols:
                x = 0
                y += 1
            if y == rows:
                theres_more = (iter is not None)
                break
        self.hbox.add(self.table)

        # if we have more than 1 page and browsing is enabled
        if self.config['browsing'] and (theres_more or page > 0):
            if self.navbuttons is None:
                self.navbuttons = gtk.HButtonBox()
                self.navbuttons.set_layout(gtk.BUTTONBOX_EDGE)
                self.dialog.add(self.navbuttons)

                self.bt_left = gtk.Button(stock=gtk.STOCK_GO_BACK)
                self.bt_left.set_use_stock(True)
                self.bt_left.set_relief(gtk.RELIEF_NONE)
                self.bt_left.connect("clicked", self.dialog_show_prev_page)
                self.navbuttons.add(self.bt_left)
                self.bt_right = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
                self.bt_right.set_use_stock(True)
                self.bt_right.set_relief(gtk.RELIEF_NONE)
                self.bt_right.connect("clicked", self.dialog_show_next_page)
                self.navbuttons.add(self.bt_right)

            # enable appropriate navigation buttons
            if page > 0:
                self.bt_left.set_sensitive(True)
            else:
                self.bt_left.set_sensitive(False)
            if theres_more:
                self.bt_right.set_sensitive(True)
            else:
                self.bt_right.set_sensitive(False)

        # show everything on the dialog
        self.dialog.present()
        self.dialog.show_all()
