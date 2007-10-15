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

import sys, os
import gobject
import gtk
from gtk import gdk
import pango
import gconf
import awn
import time
import random
import gnome.ui
import gnomevfs
import gnomedesktop
import shutil
APP="Stacks"
DIR="locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

# Import our own stuff
import stacksconfig
import stackslauncher
import stacksmonitor
import stacksicons
import stacksvfs

# Backend types
BACKEND_TYPE_INVALID = -1
BACKEND_TYPE_FILE = 0
BACKEND_TYPE_FOLDER = 1

# Columns in the ListStore
COL_URI = 0
COL_LABEL = 1
COL_MIMETYPE = 2
COL_ICON = 3
COL_FILEMON = 4

# Visual layout parameters
ICON_VBOX_SPACE = 4
ROW_SPACING = 8
COL_SPACING = 8

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)
           
"""
Main Applet class
"""
class Stacks (awn.AppletSimple):
    # Some initialization values
    gconf_path = "/apps/avant-window-navigator/applets/"
    dnd_targets = [("text/uri-list", 0, 0)]
    dialog_visible = False
    just_dragged = False
    backend = None

    # Default configuration values, are overruled while reading config
    config_backend = gnomevfs.URI("file://" + 
                                    os.path.join(
                                    os.path.expanduser("~"), 
                                    ".config", "awn", "stacks")
                                    )
    config_cols = 5
    config_rows = 4
    config_fileops = gtk.gdk.ACTION_COPY
    config_fileops |= gtk.gdk.ACTION_MOVE
    config_fileops |= gtk.gdk.ACTION_LINK
    config_icon_size = 48
    config_composite_icon = True
    config_icon_empty = _to_full_path("icons/stacks-drop.svg")
    config_icon_full = _to_full_path("icons/stacks-full.svg")

    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__(self, uid, orient, height)

        # initalize variables
        self.height = height
        self.title = awn.awn_title_get_default()
        self.effects = self.get_effects()
        self.gconf_path += str(uid)
        self.config_backend = self.config_backend.append_path(uid)     
 
        # connect to events
        self.connect("button-press-event", self.applet_callback)
        self.connect("enter-notify-event", self.enter_notify)
        self.connect("leave-notify-event", self.leave_notify)
        self.connect("drag-data-received", self.drop_callback)
        
        # Setup popup menu
        self.popup_menu = gtk.Menu()
        open_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_OPEN)
        clear_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
        self.popup_menu.append(open_item)
        self.popup_menu.append(clear_item)
        self.popup_menu.append(pref_item)
        self.popup_menu.append(about_item)
        open_item.connect_object("activate", self.open_callback, self)
        clear_item.connect_object("activate",self.clear_callback,self)
        pref_item.connect_object("activate",self.pref_callback,self)
        about_item.connect_object("activate",self.about_callback,self)
        self.popup_menu.show_all()

        # get GConf client and read configuration
        self.gconf_client = gconf.client_get_default()
        self.gconf_client.notify_add(self.gconf_path, self.gconf_callback)
        self.get_config()

    # hide the dialog
    def dialog_hide(self):
        if self.dialog_visible != False:
            self.title.hide(self)
            self.dialog.hide()
            self.dialog_visible = False

    # show the dialog
    def dialog_show(self):
        if self.dialog_visible != True:
            self.dialog_visible = True
            self.title.hide(self)
            self.build_stack_dialog()
            self.dialog.show_all()

    # For direct feedback "feeling"
    # add drop source to stack immediately,
    # and prevent duplicates @ monitor callback
    def drop_callback(self, widget, context, x, y, 
                            selection, targetType, time):
        for uri in (selection.data).split("\r\n"):
            if uri:
                pixbuf = self.backend.add(uri, context.suggested_action)
        context.finish(True, False, time)
        if pixbuf:
            self.set_full_icon(pixbuf)
        if self.dialog_visible == True:
            self.dialog_hide()
            self.dialog_show()
        return True

    def open_callback(self, widget, event):
        self.backend.open()

    def clear_callback(self, widget):
        self.backend.clear()
        self.set_empty_icon()
 
    def pref_callback(self, widget):
        cfg = stacksconfig.StacksConfig(self)

    def about_callback(self, widget):
        cfg = stacksconfig.StacksConfig(self)
        cfg.notebook.set_current_page(-1)

    def remove_callback(self, widget, user_data):
        print "clear item: ", user_data
        return

    def applet_callback(self, widget, event):
        if event.button == 3:
            # right click
            self.dialog_hide()
            self.popup_menu.popup(None, None, None, event.button, event.time)
        elif event.button == 2:
            # middle click
            self.backend.open()
        else:
            # left click
            if self.dialog_visible:
               self.dialog_hide()
            else:
               if not self.backend.is_empty():
                    self.dialog_show()

    def gconf_callback(self, gconf_client, *args, **kwargs):
        self.dialog_hide()
        self.get_config()
               
    def attention_callback(self, widget, backend_type):
        awn.awn_effect_start(self.effects, "attention")
        time.sleep(1.0)
        awn.awn_effect_stop(self.effects, "attention")

    # launches the command for a stack icon
    # -distinguishes desktop items
    def button_callback(self, widget, event, user_data):
        uri, mimetype = user_data
        if event.button == 3:
            return
            #self._build_context_menu(user_data).popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            if self.just_dragged == True:
                self.just_dragged = False
            else:
                if uri.endswith(".desktop"):
                    # TODO: uri
                    item = gnomedesktop.item_new_from_uri(
                            uri, gnomedesktop.LOAD_ONLY_IF_EXISTS)
                    if item:
                        command = item.get_string(gnomedesktop.KEY_EXEC)
                        launch_manager.launch_command(command, uri)    
                else:
                    launch_manager.launch_uri(uri, mimetype) 

    def dialog_focus_out(self, widget, event):
        self.dialog_hide()

    def dialog_drag_data_delete(self, widget, context):
        return

    def dialog_drag_data_get(
            self, widget, context, selection, info, time, user_data):
        selection.set_uris([user_data])

    def dialog_drag_begin(self, widget, context):
        self.just_dragged = True

    def enter_notify (self, widget, event):
        self.title.show(self, self.backend.get_title())

    def leave_notify (self, widget, event):
        self.title.hide(self)

    def set_empty_icon(self):
        height = self.height
        icon = gdk.pixbuf_new_from_file (self.config_icon_empty)
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_temp_icon(icon)

    def set_full_icon(self, pixbuf):
        height = self.height
        icon = gdk.pixbuf_new_from_file(self.config_icon_full)
        if self.config_composite_icon and pixbuf:
            try:
                # scale with aspect ratio:
                pixbuf = stacksicons.IconFactory().scale_to_bounded(pixbuf, height)
                # determine center of composite
                cx = (height - pixbuf.get_width())/2
                if not cx >= 0:
                    cx = 0
                cy = (height - pixbuf.get_height())/2
                if not cy >= 0:
                    cy = 0

                # video previews (for example) have artifacts, so copy manually
                # create transparent pixbuf of correct size
                mythumb = gtk.gdk.Pixbuf(pixbuf.get_colorspace(),
                                         True,
                                         pixbuf.get_bits_per_sample(),
                                         height,
                                         height)
                mythumb.fill(0x00000000)
                # copy pixbuf into transparent to center
                pixels = mythumb.get_pixels_array()
                bufs = pixbuf.get_pixels_array()
                for row in range(pixbuf.get_height()):
                    for pix in range(pixbuf.get_width()):
                        try:
                            pixels[row+cy][pix+cx][0] = bufs[row][pix][0]
                            pixels[row+cy][pix+cx][1] = bufs[row][pix][1]
                            pixels[row+cy][pix+cx][2] = bufs[row][pix][2]
                            if pixbuf.get_has_alpha():
                                pixels[row+cy][pix+cx][3] = bufs[row][pix][3]
                            else:
                                pixels[row+cy][pix+cx][3] = 255
                        except:
                            pass
                
                # composite result over "full" icon
                mythumb.composite(   
                        icon, 0, 0,
                        height, height,
                        0, 0, 1, 1,
                        gtk.gdk.INTERP_BILINEAR,
                        255)
            except:
                pass
        self.set_temp_icon(icon)
     
    def get_config(self):
        if self.backend:
            self.backend.destroy()
        
        _config_backend = self.gconf_client.get_string(
                self.gconf_path + "/backend")
        if _config_backend:
            self.config_backend = gnomevfs.URI(_config_backend)
           
        _config_cols = self.gconf_client.get_int(self.gconf_path + "/cols")
        if _config_cols > 0:
            self.config_cols = _config_cols

        _config_rows = self.gconf_client.get_int(self.gconf_path + "/rows")
        if _config_rows > 0:
            self.config_rows = _config_rows

        _config_icon_size = self.gconf_client.get_int(
                self.gconf_path + "/icon_size")
        if _config_icon_size > 0:
            self.config_icon_size = _config_icon_size

        _config_fileops = self.gconf_client.get_int(
                self.gconf_path + "/file_operations")
        if _config_fileops > 0:
            self.config_fileops = _config_fileops

        _config_composite_icon = self.gconf_client.get_bool(
                self.gconf_path + "/composite_icon")
        if _config_composite_icon:
            self.config_composite_icon = True
        else:
            self.config_composite_icon = False

        _config_icon_empty = self.gconf_client.get_string(
                self.gconf_path + "/applet_icon_empty")
        if _config_icon_empty:
            self.config_icon_empty = _config_icon_empty

        _config_icon_full = self.gconf_client.get_string(
                self.gconf_path + "/applet_icon_full")
        if _config_icon_full:
            self.config_icon_full = _config_icon_full      

        _config_backend_type = self.gconf_client.get_int(
                self.gconf_path + "/backend_type")
        
        if _config_backend_type == BACKEND_TYPE_FOLDER:
            self.backend = FolderBackend(self.config_backend, 
                    self.config_icon_size)
        elif _config_backend_type == BACKEND_TYPE_FILE:
            self.backend = FileBackend(self.config_backend,
                    self.config_icon_size)
        self.backend.read()
        self.backend.connect("attention", self.attention_callback)
        self._setup_drag_drop()
        
        if self.backend.is_empty():
            self.set_empty_icon()
        else:
            pixbuf = self.backend.get_random_pixbuf()
            self.set_full_icon(pixbuf)

    # if backend is folder: use specified file operations
    # else: only enable link action
    def _setup_drag_drop(self):
        if self.backend.get_type() == BACKEND_TYPE_FOLDER:
            actions = self.config_fileops
        elif self.backend.get_type() == BACKEND_TYPE_FILE:
            actions = gtk.gdk.ACTION_LINK
        else:
            return
        self.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
                            gtk.DEST_DEFAULT_HIGHLIGHT | 
                            gtk.DEST_DEFAULT_DROP,
                            self.dnd_targets, 
                            actions)

    def _build_context_menu(self, uri):
        context_menu = gtk.Menu()
        del_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        context_menu.append(del_item)
        del_item.connect_object("activate", self.remove_callback, self, uri)     
        context_menu.show_all()
        return context_menu

    def build_stack_dialog(self):
        if self.backend.is_empty():
            return
        self.dialog = awn.AppletDialog (self)
        self.dialog.set_focus_on_map(True)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)
        if self.backend.get_type() == BACKEND_TYPE_FOLDER:
            self.dialog.set_title(self.backend.get_title())
        table = gtk.Table(1,1,True)
        table.set_row_spacings(ROW_SPACING)
        table.set_col_spacings(COL_SPACING)
        store = self.backend.get_store()
        iter = store.get_iter_first()
        x=0
        y=0
        while iter:
            button = gtk.Button()
            button.set_relief(gtk.RELIEF_NONE)
            button.connect( "button-release-event", 
                            self.button_callback,
                            store.get(iter, COL_URI, COL_MIMETYPE))
            # TODO connect on enter key
            button.connect( "drag-data-get",
                            self.dialog_drag_data_get,
                            store.get_value(iter, COL_URI))
            button.connect( "drag-begin",
                            self.dialog_drag_begin)
            button.drag_source_set( gtk.gdk.BUTTON1_MASK,
                                    self.dnd_targets,
                                    self.config_fileops )

            vbox = gtk.VBox(False, ICON_VBOX_SPACE)
            vbox.set_size_request(int(1.2 * self.config_icon_size), -1)
            icon = store.get_value(iter, COL_ICON)

            if icon:
                button.drag_source_set_icon_pixbuf(icon)
                image = gtk.Image()
                image.set_from_pixbuf(icon)
                image.set_size_request(self.config_icon_size, 
                        self.config_icon_size)
                vbox.pack_start(image, False, False, 0)
            label = gtk.Label(store.get_value(iter, COL_LABEL))
            if label:
                label.set_justify(gtk.JUSTIFY_CENTER)
                label.set_line_wrap(True)
                #layout = label.get_layout()
                #lw, lh = layout.get_size()
                #layout.set_alignment(pango.ALIGN_CENTER)
                #layout.set_width(self.config_icon_size * pango.SCALE)
                #layout.set_wrap(pango.WRAP_CHAR)
                #label.set_size_request(self.config_icon_size, lh*2/pango.SCALE)
                #label.set_ellipsize(pango.ELLIPSIZE_END)
                vbox.pack_start(label, False, False, 0)
      
            button.add(vbox)
            table.attach(button, x, x+1, y, y+1)
            x += 1
            if x == self.config_cols:
                y += 1
                x=0
            if y == self.config_rows:
                break
            iter = store.iter_next(iter)

        table.show_all()
        self.dialog.add(table)



class Backend(gobject.GObject):

    backend_uri = None
    store = None
    icon_size = 0

    __gsignals__ = {
        'attention' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                        (gobject.TYPE_INT,))
    }

    def __init__(self, uri, icon_size):
        gobject.GObject.__init__(self)
        self.backend_uri = uri
        self.icon_size = icon_size
        # Setup store to hold the stack items
        self.store = gtk.ListStore( gobject.TYPE_STRING, 
                                    gobject.TYPE_STRING, 
                                    gobject.TYPE_STRING,
                                    gtk.gdk.Pixbuf,
                                    gobject.TYPE_OBJECT )
        self.store.set_sort_column_id(COL_URI, gtk.SORT_ASCENDING)
        self.store.set_sort_func(COL_URI, self._file_sort)

    # we use a sorted liststore.
    # this sort function sorts:
    # -directories first
    # -case insensitive
    # -first basename, then extension
    def _file_sort(self, model, iter1, iter2):
        f1 = gnomevfs.URI(model.get_value(iter1, 0))
        f2 = gnomevfs.URI(model.get_value(iter2, 0))
        t1 = gnomevfs.get_file_info(f1).type
        t2 = gnomevfs.get_file_info(f2).type
        if t1 == gnomevfs.FILE_TYPE_DIRECTORY and not \
                t2 == gnomevfs.FILE_TYPE_DIRECTORY:
            return -1
        elif t2 == gnomevfs.FILE_TYPE_DIRECTORY and not \
                t1 == gnomevfs.FILE_TYPE_DIRECTORY:
            return 1
        else:
            return cmp(f1.short_name, f2.short_name)

    def _get_attention(self):
        self.emit("attention", self.get_type())

    def _created(self, widget, uri):
        pixbuf = self.add(uri)
        if pixbuf:
            self._get_attention()

    def _deleted(self, widget, uri):
        if self.remove(uri):
            self._get_attention()
            
    # add item to the stack
    # -ignores hidden files
    # -checks for duplicates
    # -check for desktop item
    # -add file monitor       
    def add(self, uri, action=None):
        if not uri:
            return

        # check for hidden files
        name = uri.short_name
        mime_type = ""
        pixbuf = None

        # check for hidden or temp files
        if name[0] == "." or name.endswith("~"):
            return None

        # check for duplicates
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            if gnomevfs.uris_match(store_uri, uri.path):
                return None
            iter = self.store.iter_next(iter)

        # check for desktop item
        if uri.short_name.endswith(".desktop"):
            # TODO: uri
            item = gnomedesktop.item_new_from_uri(
                    uri, 
                    gnomedesktop.LOAD_ONLY_IF_EXISTS)
            if not item:
                return None
            command = item.get_string(gnomedesktop.KEY_EXEC)
            name = item.get_localestring(gnomedesktop.KEY_NAME)
            icon_name = item.get_localestring(gnomedesktop.KEY_ICON)
            if icon_name:
                icon_uri = gnomedesktop.find_icon(    
                        gtk.icon_theme_get_default(), 
                           icon_name,
                        self.config_icon_size,
                        0)
            else:
                icon_uri = uri
            mime_type = "application/x-desktop"
            thumbnailer = stacksicons.Thumbnailer(icon_uri, mime_type)
            pixbuf = thumbnailer.get_icon(self.icon_size)
        else:         
            try:
                mime_type = gnomevfs.get_file_info(uri, gnomevfs.FILE_INFO_GET_MIME_TYPE)
                thumbnailer = stacksicons.Thumbnailer(uri.path, mime_type)
                pixbuf = thumbnailer.get_icon(self.icon_size)
            except:
                thumbnailer = stacksicons.Thumbnailer(uri.path, "text/plain")
                pixbuf = thumbnailer.get_icon(self.icon_size)

        # add to store and add file monitor
        filemon = stacksmonitor.FileMonitor(uri)
        filemon.connect("deleted", self._deleted)
        filemon.open()
        self.store.append([ uri, 
                            name, 
                            mime_type,
                            pixbuf,
                            filemon ])
        return pixbuf

    # remove file from store
    def remove(self, uri):
        return False
        
    def read(self):
        return

    def clear(self):
        self.store.clear()

    def open(self):
        launch_manager.launch_uri(self.backend_uri, None)
        
    def is_empty(self):
        iter = self.store.get_iter_first()
        if iter and self.store.iter_is_valid(iter):
            return False
        else:
            return True
        
    def get_title(self):
        return _("Stacks")

    def get_type(self):
        return BACKEND_TYPE_INVALID

    def get_random_pixbuf(self):
        pixbuf = None
        iter = self.store.get_iter_first()
        if iter:
            rand = random.Random()
            pick = rand.randint(0, 10)
            start = 0
            while iter:
                pixbuf = self.store.get_value(iter, COL_ICON)
                if pick == start:
                    break
                iter = self.store.iter_next(iter)
                start += 1
        return pixbuf

    def get_store(self):
        return self.store
        
    def destroy(self):
        return

class FileBackend(Backend):

    def __init__(self, uri, icon_size):
        Backend.__init__(self, uri, icon_size)
        bdir = self.backend_uri.dirname
        if not gnomevfs.exists(bdir):
            gnomevfs.make_directory(bdir, 
                    gnomevfs.PERM_USER_READ | gnomevfs.PERM_USER_WRITE)
        if not gnomevfs.exists(self.backend_uri):
            gnomevfs.create(self.backend_uri, 
                    gnomevfs.OPEN_MODE_NONE, False, 
                    gnomevfs.PERM_USER_READ | gnomevfs.PERM_USER_WRITE)

    def remove(self, uri): 
        f = open(self.backend_uri, "r") 
        if f: 
            try: 
                lines = f.readlines() 
                f.close() 
                f = open(self.backend_uri, "w") 
                for furi in lines: 
                    if not furi.strip() == uri.path.strip(): 
                        f.write(furi) 
            finally: 
                f.close()                 
        return Backend.remove(self, uri) 
  
    def add(self, uri, action=None):
        try:
            uri = gnomevfs.URI(uri) 
        except TypeError:
            pass
        f = open(self.backend_uri.path, "a") 
        if f: 
            try: 
                f.write(uri.path + os.linesep) 
            finally: 
                f.close() 
        return Backend.add(self, uri)
                     
    def read(self): 
        f = open(self.backend_uri.path, "r") 
        if f: 
            try: 
                lines = f.readlines() 
                for uri in lines: 
                    if len(uri) > 0: 
                        self.add(uri.strip())
            finally: 
                f.close() 

    def clear(self):
        gnomevfs.truncate(self.backend_uri, 0)
        Backend.clear(self)

    # Do nothing on "open"; not really useful
    def open(self):
        return

    def get_type(self):
        return BACKEND_TYPE_FILE
        
class FolderBackend(Backend):

    folder_monitor = None
           
    def _set_monitor(self):
        self.folder_monitor = stacksmonitor.FileMonitor(self.backend_uri)
        self.folder_monitor.open()
        self.folder_monitor.connect("created", self._created)
        self.folder_monitor.connect("deleted", self._deleted)

    def remove(self, uri):
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            if(store_uri == ("file://" + uri)):
                self.store.remove(iter)
                return True
            iter = self.store.iter_next(iter)     
        return Backend.remove(self, uri)
     
    def add(self, uri, action=None):
        if action != None:
            dst = self.backend_uri.append_path(uri.short_name) 
            if action == gtk.gdk.ACTION_LINK:
                options = gnomevfs.XFER_LINK_ITEMS
            elif action == gtk.gdk.ACTION_COPY:
                options = gnomevfs.XFER_DEFAULT
            elif action == gtk.gdk.ACTION_MOVE:
                options = gnomevfs.XFER_REMOVESOURCE
            else:
                return None

            #options |= gnomevfs.XFER_FOLLOW_LINKS
            #options |= gnomevfs.XFER_RECURSIVE
            #options |= gnomevfs.XFER_FOLLOW_LINKS_RECURSIVE
            #options |= gnomevfs.XFER_TARGET_DEFAULT_PERMS
            stacksvfs.GUITransfer(uri, dst, options)
        return Backend.add(self, uri)

    def read(self):
        hdir = gnomevfs.open_directory(self.backend_uri)
        for finfo in hdir:
            if finfo.type == gnomevfs.FILE_TYPE_REGULAR or \
                    finfo.type == gnomevfs.FILE_TYPE_SYMBOLIC_LINK or \
                    finfo.type == gnomevfs.FILE_TYPE_DIRECTORY:
                self.add(self.backend_uri.append_path(finfo.name))
        self._set_monitor()
        
    def clear(self):
        dialog = gtk.Dialog(_("Confirm removal"),
                            None,
                            gtk.DIALOG_MODAL | 
                            gtk.DIALOG_DESTROY_WITH_PARENT | 
                            gtk.DIALOG_NO_SEPARATOR,
                            (gtk.STOCK_NO, gtk.RESPONSE_REJECT,
                            gtk.STOCK_YES, gtk.RESPONSE_ACCEPT))
        dialog.set_default_response(gtk.RESPONSE_REJECT)
        align = gtk.Alignment(0.5,0.5,0,0)
        align.set_padding(10,10,20,20)
        label = gtk.Label(_("This stack has a <b>folder backend</b>. Do you \
                really want to <b>delete</b> the files from that folder?"))
        label.set_use_markup(True)
        label.set_line_wrap(True)
        align.add(label)
        align.show_all()
        dialog.vbox.pack_start(align, True, True, 0)
        if dialog.run() == gtk.RESPONSE_REJECT:
            dialog.destroy()
            return
        # remove files
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            gnomevfs.unlink(store_uri)
            iter = self.store.iter_next(iter)
        # destroy dialog
        dialog.destroy()
        Backend.clear()

    def get_title(self):
        return self.backend_uri.short_name

    def get_type(self):
        return BACKEND_TYPE_FOLDER
        
    def destroy(self):
        self.folder_monitor.close()
        Backend.destroy()

launch_manager = stackslauncher.LaunchManager()
gnome.ui.authentication_manager_init()
           
if __name__ == "__main__":
    awn.init (sys.argv[1:])
    
    applet = Stacks (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
