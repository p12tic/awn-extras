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
import gobject
import gtk
from gtk import gdk
import random
import gnome.ui
import gnomevfs
import gnomedesktop
import locale
import gettext
import stacks
import stacksvfs
import stacksicons

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

# Backend types
BACKEND_TYPE_INVALID = -1
BACKEND_TYPE_FILE = 0
BACKEND_TYPE_FOLDER = 1

# Columns in the ListStore
COL_URI = 0
COL_LABEL = 1
COL_MIMETYPE = 2
COL_ICON = 3

# Visual layout parameters
ICON_VBOX_SPACE = 4
ROW_SPACING = 0
COL_SPACING = 0

class Backend(gobject.GObject):

    backend_uri = None
    store = None
    icon_size = 0

    __gsignals__ = {
        'attention' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, 
                        (gobject.TYPE_INT,)),
        'restructure' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        (gobject.TYPE_INT,))
    }

    def __init__(self, uri, icon_size):
        gobject.GObject.__init__(self)
        self.icon_size = icon_size
        # Setup store to hold the stack items
        self.store = gtk.ListStore( gobject.TYPE_OBJECT,
                                    gobject.TYPE_STRING, 
                                    gobject.TYPE_STRING,
                                    gtk.gdk.Pixbuf )
        self.store.set_sort_column_id(COL_URI, gtk.SORT_ASCENDING)
        self.store.set_sort_func(COL_URI, self._file_sort)

    # we use a sorted liststore.
    # this sort function sorts:
    # -directories first
    # -case insensitive
    # -first basename, then extension
    def _file_sort(self, model, iter1, iter2):
        f1 = model.get_value(iter1, COL_URI)
        f2 = model.get_value(iter2, COL_URI)
        if f1.get_type() == gnomevfs.FILE_TYPE_DIRECTORY and not \
                f2.get_type() == gnomevfs.FILE_TYPE_DIRECTORY:
            return -1
        elif f2.get_type() == gnomevfs.FILE_TYPE_DIRECTORY and not \
                f1.get_type() == gnomevfs.FILE_TYPE_DIRECTORY:
            return 1
        else:
            n1 = model.get_value(iter1, COL_LABEL)
            n2 = model.get_value(iter2, COL_LABEL)
            return cmp(n1, n2)

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
        name = uri.short_name
        mime_type = ""
        pixbuf = None

        # check for duplicates
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)            
            if store_uri.equals(uri):
                return None
            iter = self.store.iter_next(iter)

        # check for desktop item
        if uri.short_name.endswith(".desktop"):
            # TODO: uri
            item = gnomedesktop.item_new_from_uri(
                    uri.to_string(), 
                    gnomedesktop.LOAD_ONLY_IF_EXISTS)
            if not item:
                return None
            command = item.get_string(gnomedesktop.KEY_EXEC)
            name = item.get_localestring(gnomedesktop.KEY_NAME)
            icon_name = item.get_localestring(gnomedesktop.KEY_ICON)
            icon_uri = None
            if icon_name:
                icon_uri = gnomedesktop.find_icon(    
                                        gtk.icon_theme_get_default(), 
                                        icon_name,
                                        self.icon_size,
                                        0)
            if not icon_uri:
                icon_uri = uri.to_string()
            elif icon_uri.startswith("file://"):
                icon_uri = icon_uri[7:]
            icon_factory = stacksicons.IconFactory()
            pixbuf = icon_factory.load_icon_from_path(icon_uri, self.icon_size)
            if pixbuf is not None:
                pixbuf = icon_factory.scale_to_bounded(pixbuf, self.icon_size)

        if pixbuf is None:
            try:
                mime_type = gnomevfs.get_file_info(uri.vfs_uri, 
                                gnomevfs.FILE_INFO_GET_MIME_TYPE).mime_type
            except gnomevfs.NotFoundError:
                return None
            thumbnailer = stacksicons.Thumbnailer(uri.to_string(), mime_type)
            pixbuf = thumbnailer.get_icon(self.icon_size)

        self.store.append([ uri, 
                            name, 
                            mime_type,
                            pixbuf ])
        self.emit("restructure", self.get_type())
        return pixbuf

    # remove file from store
    def remove(self, uri):
        retval = False
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            if store_uri.equals(uri):
                self.store.remove(iter)
                retval = True
                break
            iter = self.store.iter_next(iter)     
        self.emit("restructure", self.get_type())
        return retval
        
    def read(self):
        return

    def clear(self):
        self.store.clear()

    def open(self):
        stacks.launch_manager.launch_uri(self.backend_uri.to_string(), None)
        
    def is_empty(self):
        iter = self.store.get_iter_first()
        if iter and self.store.iter_is_valid(iter):
            return False
        else:
            return True
        
    def get_title(self):
        return _("Stacks")

    def get_type(self):
        return stacksbackend.BACKEND_TYPE_INVALID

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
        self.backend_uri = stacksvfs.VfsFile(uri, create=True)

    # TODO: replace with gnomevfs version
    def remove(self, uri): 
        if not isinstance(uri, stacksvfs.VfsUri):
            uri = stacksvfs.get_vfsuri(uri)
        f = open(self.backend_uri.to_string(), "r") 
        if f: 
            try: 
                lines = f.readlines() 
                f.close() 
                f = open(self.backend_uri.to_string(), "w") 
                for furi in lines: 
                    furi = stacksvfs.get_vfsuri(furi)
                    if not uri.equals(furi): 
                        f.write(furi + os.linesep) 
            finally: 
                f.close()                 
        return Backend.remove(self, uri) 

    def add(self, uri, action=None):
        if not isinstance(uri, stacksvfs.VfsUri):
           uri = stacksvfs.get_vfsuri(uri)
        if action != None:
            self.backend_uri.append(uri.to_string() + os.linesep)
        uri.monitor()
        uri.connect("deleted", self._deleted)
        return Backend.add(self, uri)

    def read(self):
        for line in self.backend_uri.read().split(os.linesep):
            if len(line.strip()) > 0:
                self.add(line.strip())

    def clear(self):
        self.backend_uri.write(None)
        Backend.clear(self)

    # Do nothing on "open"; not really useful
    def open(self):
        return

    def get_type(self):
        return BACKEND_TYPE_FILE
        
class FolderBackend(Backend):

    def __init__(self, uri, icon_size):
        Backend.__init__(self, uri, icon_size)
        self.backend_uri = stacksvfs.VfsDir(uri, create=True)
           
    def _set_monitor(self):
        self.backend_uri.monitor()
        self.backend_uri.connect("created", self._created)
        self.backend_uri.connect("deleted", self._deleted)

    def remove(self, uri):
        if not isinstance(uri, stacksvfs.VfsUri):
            uri = stacksvfs.get_vfsuri(uri)
        return Backend.remove(self, uri)
  
    def add(self, uri, action=None):
        if not isinstance(uri, stacksvfs.VfsUri):
            uri = stacksvfs.get_vfsuri(uri)
            if uri is None:
                return None
        if action != None:
            try:
                dst = self.backend_uri.vfs_uri.append_path(uri.short_name)
            except AttributeError:
                return None
            if action == gtk.gdk.ACTION_LINK:
                options = gnomevfs.XFER_LINK_ITEMS
            elif action == gtk.gdk.ACTION_COPY:
                options = gnomevfs.XFER_DEFAULT
            elif action == gtk.gdk.ACTION_MOVE:
                options = gnomevfs.XFER_REMOVESOURCE
            else:
                return None

            options |= gnomevfs.XFER_FOLLOW_LINKS
            options |= gnomevfs.XFER_RECURSIVE
            options |= gnomevfs.XFER_FOLLOW_LINKS_RECURSIVE
            stacksvfs.GUITransfer(uri.vfs_uri, dst, options)
            uri = stacksvfs.get_vfsuri(dst)
        return Backend.add(self, uri)

    def read(self):
        for finfo in self.backend_uri.read():
            self.add(finfo)
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
        self.backend_uri.close()
        Backend.destroy(self)

