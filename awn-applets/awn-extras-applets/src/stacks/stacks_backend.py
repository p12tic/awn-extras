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

from stacks_vfs import VfsUri, Monitor
from stacks_icons import IconFactory, Thumbnailer
from stacks_launcher import LaunchManager

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
BACKEND_TYPE_PLUGGER = 2
BACKEND_TYPE_TRASHER = 3

# Columns in the ListStore
COL_URI = 0
COL_MONITOR = 1
COL_TYPE = 2
COL_LABEL = 3
COL_MIMETYPE = 4
COL_ICON = 5
COL_BUTTON = 6

class Backend(gobject.GObject):

    applet = None           # ref to the applet
    store = None            # store that holds the stack items
    icon_size = 0           # (current) icon size of the stack items

    __gsignals__ = {
        'attention' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        (gobject.TYPE_INT,)),
        'item-created' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        (gtk.TreeIter,)),
        'item-removed' : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                        (gtk.TreeIter,))
    }

    # initialize the backend
    def __init__(self, applet, icon_size):
        gobject.GObject.__init__(self)
        # set class references
        self.applet = applet
        self.icon_size = icon_size
        # Setup store to hold the stack items
        self.store = gtk.ListStore( gobject.TYPE_OBJECT,
                                    gobject.TYPE_OBJECT,
                                    gobject.TYPE_INT,
                                    gobject.TYPE_STRING,
                                    gobject.TYPE_STRING,
                                    gtk.gdk.Pixbuf,
                                    gobject.TYPE_OBJECT)
        self.store.set_sort_column_id(COL_URI, gtk.SORT_ASCENDING)
        self.store.set_sort_func(COL_URI, self._file_sort)


    # we use a sorted liststore.
    # this sort function sorts:
    # -directories first
    # -case insensitive
    # -first basename, then extension
    def _file_sort(self, model, iter1, iter2):
        t1 = model.get_value(iter1, COL_TYPE)
        t2 = model.get_value(iter2, COL_TYPE)
        if t1 == gnomevfs.FILE_TYPE_DIRECTORY and not \
                t2 == gnomevfs.FILE_TYPE_DIRECTORY:
            return -1
        elif t2 == gnomevfs.FILE_TYPE_DIRECTORY and not \
                t1 == gnomevfs.FILE_TYPE_DIRECTORY:
            return 1
        else:
            n1 = model.get_value(iter1, COL_LABEL)
            if n1 is not None: n1 = n1.lower()
            n2 = model.get_value(iter2, COL_LABEL)
            if n2 is not None: n2 = n2.lower()
            return cmp(n1, n2)


    # emits attention signal
    def _get_attention(self):
        self.emit("attention", self.get_type())


    def _created_cb(self, widget, vfs_uri):
        assert isinstance(vfs_uri, VfsUri)
        if self.add([vfs_uri]):
             self._get_attention()


    def _deleted_cb(self, widget, vfs_uri):
        assert isinstance(vfs_uri, VfsUri)
        if self.remove([vfs_uri]):
             self._get_attention()

    # add item to the stack
    # -ignores hidden files
    # -checks for duplicates
    # -check for desktop item
    # -add file monitor
    def add(self, vfs_uris, action=None):
        retval = None
        for vfs_uri in vfs_uris:
            uri = vfs_uri.as_uri()
            path = vfs_uri.as_string()
            name = uri.short_name
            mime_type = ""
            pixbuf = None

            # check for existence:
            if uri.scheme == "file" and not gnomevfs.exists(uri):
                continue

            # check for duplicates
            duplicate = False
            iter = self.store.get_iter_first()
            while iter:
                store_uri = self.store.get_value(iter, COL_URI)
                if vfs_uri.equals(store_uri):
                    duplicate = True
                    break
                iter = self.store.iter_next(iter)
            if duplicate: continue

            # check for desktop item
            if name.endswith(".desktop"):
                item = gnomedesktop.item_new_from_uri(
                        path, gnomedesktop.LOAD_ONLY_IF_EXISTS)
                if not item:
                    continue
                command = item.get_string(gnomedesktop.KEY_EXEC)
                name = item.get_localestring(gnomedesktop.KEY_NAME)
                mime_type = item.get_localestring(gnomedesktop.KEY_MIME_TYPE)
                type = gnomevfs.FILE_TYPE_REGULAR
                icon_name = item.get_localestring(gnomedesktop.KEY_ICON)
                icon_uri = None
                if icon_name:
                    icon_uri = gnomedesktop.find_icon(
                                        gtk.icon_theme_get_default(),
                                        icon_name,
                                        self.icon_size,
                                        0)
                    if not icon_uri:
                        icon_uri = path
                    pixbuf = IconFactory().load_icon(icon_uri, self.icon_size)
                    pixbuf.add_alpha (True, '\0', '\0', '\0')
            else:
                # get file info
                try:
                    fileinfo = gnomevfs.get_file_info(
                            path,
                            gnomevfs.FILE_INFO_DEFAULT |
                            gnomevfs.FILE_INFO_GET_MIME_TYPE |
                            gnomevfs.FILE_INFO_FORCE_SLOW_MIME_TYPE |
                            gnomevfs.FILE_INFO_FOLLOW_LINKS )
                    type = fileinfo.type
                    mime_type = fileinfo.mime_type
                except gnomevfs.NotFoundError:
                    continue
                # get pixbuf for icon
                pixbuf = Thumbnailer(path, mime_type).get_icon(self.icon_size)
                pixbuf.add_alpha (True, '\0', '\0', '\0')

            # create monitor
            try:
                monitor = Monitor(vfs_uri)
                monitor.connect("deleted", self._deleted_cb)
            except gnomevfs.NotSupportedError:
                monitor = None

            # add to store
            iter = self.store.append([vfs_uri, monitor, type, name, mime_type, pixbuf, None])
            self.emit("item-created", iter)

            # return pixbuf later?
            if pixbuf: retval = pixbuf

        # restructure of dialog needed
        return (retval is not None)


    # remove file from store
    def remove(self, vfs_uris):
        changed = False
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            for vfs_uri in vfs_uris:
                if vfs_uri.equals(store_uri):
                    self.store.remove(iter)
                    self.emit("item-removed", None) # iter not valid any more?
                    return True
            iter = self.store.iter_next(iter)
        return False

    def read(self):
        return


    def clear(self):
        self.store.clear()
        self.emit("item-removed", None)


    def open(self):
        return


    def is_empty(self):
        iter = self.store.get_iter_first()
        return not (iter and self.store.iter_is_valid(iter))


    def get_title(self):
        title = self.applet.gconf_client.get_string(
                self.applet.gconf_path + "/title") or _("Stacks")
        return title;


    def get_number_items(self):
        return self.store.iter_n_children(None)


    def get_menu_items(self):
        return []


    def get_type(self):
        return stacksbackend.BACKEND_TYPE_INVALID


    def get_random_pixbuf(self):
        max = self.get_number_items()
        rand = random.Random()
        pick = rand.randint(0, max-1)
        iter = self.store.iter_nth_child(None, pick)
        if not iter: return None
        return self.store.get_value(iter, COL_ICON)


    def get_store(self):
        return self.store


    def destroy(self):
        return
