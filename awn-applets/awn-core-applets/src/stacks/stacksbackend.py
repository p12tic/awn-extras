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
BACKEND_TYPE_PLUGGER = 2
BACKEND_TYPE_TRASH = 3

# Columns in the ListStore
COL_URI = 0
COL_MONITOR = 1
COL_TYPE = 2
COL_LABEL = 3
COL_MIMETYPE = 4
COL_ICON = 5

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
        if isinstance(uri, stacksvfs.VfsUri):
            self.backend_uri = uri
        else:
            self.backend_uri = stacksvfs.VfsUri(uri)
        self._create_or_open()
        self.icon_size = icon_size
        # Setup store to hold the stack items
        self.store = gtk.ListStore( gobject.TYPE_OBJECT,
                                    gobject.TYPE_OBJECT,
                                    gobject.TYPE_INT,
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
        name = uri.as_uri().short_name
        mime_type = ""
        pixbuf = None
        # check for existence:
        if uri.as_uri().scheme == "file" and not gnomevfs.exists(uri.as_uri()):
            return None
        # check for duplicates
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            if uri.equals(store_uri):
                return None
            iter = self.store.iter_next(iter)
        # check for desktop item
        if uri.as_uri().short_name.endswith(".desktop"):
            # TODO: uri
            item = gnomedesktop.item_new_from_uri(
                    uri.as_string(), 
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
                icon_uri = uri.as_string()
            elif icon_uri.startswith("file://"):
                icon_uri = icon_uri[7:]
            icon_factory = stacksicons.IconFactory()
            pixbuf = icon_factory.load_icon_from_path(icon_uri, self.icon_size)
            if pixbuf is not None:
                pixbuf = icon_factory.scale_to_bounded(pixbuf, self.icon_size)
        # get file info
        try:
            fileinfo = gnomevfs.get_file_info(
                    uri.as_string(),
                    gnomevfs.FILE_INFO_DEFAULT |
                    gnomevfs.FILE_INFO_GET_MIME_TYPE |
                    gnomevfs.FILE_INFO_FORCE_SLOW_MIME_TYPE)
            type = fileinfo.type
            mime_type = fileinfo.mime_type
        except gnomevfs.NotFoundError:
            return None
        # get pixbuf for icon
        if pixbuf is None:
            thumbnailer = stacksicons.Thumbnailer(uri.as_string(), mime_type)
            pixbuf = thumbnailer.get_icon(self.icon_size)
        # create monitor
        try:
            monitor = Monitor(uri)
            monitor.connect("deleted", self._deleted)
        except gnomevfs.NotSupportedError:
            monitor = None
        # add to store
        self.store.append([uri, monitor, type, name, mime_type, pixbuf])
        # restructure of dialog needed
        self.emit("restructure", self.get_type())
        return pixbuf

    # remove file from store
    def remove(self, uri):
        retval = False
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            if uri.equals(store_uri):
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
        stackslauncher.LaunchManager.launch_uri(
                self.backend_uri.as_string(), None)

    def is_empty(self):
        iter = self.store.get_iter_first()
        if iter and self.store.iter_is_valid(iter):
            return False
        else:
            return True

    def get_title(self):
        return _("Stacks")

    def get_menu_items(self):
        return None

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

    handle = None

    def __init__(self, uri, icon_size):
        Backend.__init__(self, uri, icon_size)

    def _create_or_open(self):
        mode = gnomevfs.OPEN_WRITE | gnomevfs.OPEN_READ | gnomevfs.OPEN_RANDOM
        if not gnomevfs.exists(self.backend_uri.as_uri()):
            self.handle = gnomevfs.create(self.backend_uri.as_uri(), mode)
        else:
            self.handle = gnomevfs.Handle(self.backend_uri.as_uri(), mode)

    def remove(self, uri):
        if not isinstance(uri, stacksvfs.VfsUri):
            try:
                uri = stacksvfs.VfsUri(uri)
            except TypeError:
                return None
        uristr = uri.as_string()
        buffer = ""
        content = gnomevfs.read_entire_file(self.backend_uri.as_string())
        lines = content.splitlines()
        for line in lines:
            if cmp(uristr, line):
                buffer += line + os.linesep
        if buffer is not None:
            self.handle.truncate(0)
            self.handle.seek(0)
            self.handle.write(buffer)
        return Backend.remove(self, uri)

    def add(self, uri, action=None):
        if not isinstance(uri, stacksvfs.VfsUri):
            try:
                uri = stacksvfs.VfsUri(uri)
            except TypeError:
                return None
        pixbuf = Backend.add(self, uri)
        if action != None and pixbuf is not None:
            self.handle.seek(0, gnomevfs.SEEK_END)
            self.handle.write(uri.as_string() + os.linesep)
        return pixbuf

    def read(self):
        uris = []
        content = gnomevfs.read_entire_file(
                self.backend_uri.as_string())
        lines = content.splitlines()
        for line in lines:
            self.add(line.strip())

    def clear(self):
        self.handle.truncate(0)
        Backend.clear(self)

    # Do nothing on "open"; not really useful
    def open(self):
        return

    def get_type(self):
        return BACKEND_TYPE_FILE

class FolderBackend(Backend):

    monitor = None

    def __init__(self, uri, icon_size):
        if str(uri)[-1] != '/':
            uri += '/'
        Backend.__init__(self, uri, icon_size)

        self.monitor = Monitor(self.backend_uri)
        if self.monitor:
            self.monitor.connect("created", self._created)
            self.monitor.connect("deleted", self._deleted)

    def _create_or_open(self):
        path = self.backend_uri.as_uri().path
        uri = self.backend_uri.as_uri().resolve_relative("/")
        for folder in path.split("/"):
            if not folder:
                continue
            uri = uri.append_string(folder)
            try:
                gnomevfs.make_directory(uri, 0777)
            except gnomevfs.FileExistsError:
                pass

    def remove(self, uri):
        if not isinstance(uri, stacksvfs.VfsUri):
            uri = stacksvfs.VfsUri(uri)
        return Backend.remove(self, uri)

    def add(self, uri, action=None):
        if not isinstance(uri, stacksvfs.VfsUri):
            try:
                uri = stacksvfs.VfsUri(uri)
            except TypeError:
                return None
        pixbuf = Backend.add(self, uri)
        if action != None and pixbuf is not None:
            try:
                dst = self.backend_uri.as_uri().append_path(uri.as_uri().short_name)
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
            stacksvfs.GUITransfer(uri.as_uri(), dst, options)
            uri = dst
        return pixbuf

    def read(self):
        uris = []
        try:
            handle = gnomevfs.DirectoryHandle(self.backend_uri.as_uri())
        except:
            print "Stacks Error: ", self.backend_uri.as_string(), " not found"
            return []
        try:
            fileinfo = handle.next()
        except StopIteration:
            return []
        while fileinfo:
            if fileinfo.name[0] != "." and not fileinfo.name.endswith("~"):
                self.add(self.backend_uri.as_uri().append_path(fileinfo.name))
            try:
                fileinfo = handle.next()
            except StopIteration:
                break

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
            gnomevfs.unlink(store_uri.as_uri())
            iter = self.store.iter_next(iter)
        # destroy dialog
        dialog.destroy()
        Backend.clear(self)

    def get_title(self):
        return self.backend_uri.as_uri().short_name

    def get_type(self):
        return BACKEND_TYPE_FOLDER

    def destroy(self):
        if self.monitor:
            self.monitor.close()
        Backend.destroy(self)


class PluggerBackend(FolderBackend):

    applet = None

    def __init__(self, applet, uri, icon_size):
        FolderBackend.__init__(self, uri, icon_size)
        self.applet = applet

    def _eject_cb(self, *args, **kargs):
        return

    def _unmount_cb(self, widget):
        for volume in gnomevfs.VolumeMonitor().get_mounted_volumes():
             hudi = volume.get_hal_udi()
             if hudi is not None:
                hal,sep,vid = hudi.rpartition(os.sep)
                print vid
                if not cmp(vid, self.applet.uid):
                    volume.unmount(self._eject_cb)

    def _hide_cb(self, widget):
        self.applet.gconf_client.set_bool(self.applet.gconf_path + "/hide_volume", True)
        self.applet.destroy()

    def get_title(self):
        # TODO: get gconf entry "title"
        title = self.applet.gconf_client.get_string(self.applet.gconf_path + "/title")
        if title:
            if len(title) > 5:
                return title;
            else:
                return _("Mounted volume") + ": " + title
        return _("Removable device")

    def get_menu_items(self):
        items = []
        unmount_item = gtk.MenuItem(label=_("Unmount Volume"))
        unmount_item.connect_object("activate", self._unmount_cb, self)
        items.append(unmount_item)
        hide_item = gtk.MenuItem(label=_("Hide Volume"))
        hide_item.connect_object("activate", self._hide_cb, self)
        items.append(hide_item)
        return items


class TrashBackend(FolderBackend):

    def get_title(self):
        return _("Trash")

    def get_type(self):
        return BACKEND_TYPE_TRASH


class Monitor(gobject.GObject):

    __gsignals__ = {
        "event" :   (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                    (gobject.TYPE_STRING, gobject.TYPE_INT)),
        "created" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "deleted" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
        "changed" : (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, (gobject.TYPE_STRING,))
    }

    event_mapping = {
        gnomevfs.MONITOR_EVENT_CREATED : "created",
        gnomevfs.MONITOR_EVENT_DELETED : "deleted",
        gnomevfs.MONITOR_EVENT_CHANGED : "changed",
        gnomevfs.MONITOR_EVENT_METADATA_CHANGED : "changed"
    }

    monitor = None 

    def __init__(self, uri):
        gobject.GObject.__init__(self)
        type = gnomevfs.get_file_info(uri.as_uri(),
                gnomevfs.FILE_INFO_DEFAULT |gnomevfs.FILE_INFO_FOLLOW_LINKS).type
        if type == gnomevfs.FILE_TYPE_DIRECTORY:
            monitor_type = gnomevfs.MONITOR_DIRECTORY
        elif type == gnomevfs.FILE_TYPE_REGULAR:
            monitor_type = gnomevfs.MONITOR_FILE
        else:
            raise gnomevfs.NotSupportedError
        try:
            self.monitor = gnomevfs.monitor_add(
                    uri.as_string(),
                    monitor_type,
                    self._monitor_cb)
        except gnomevfs.NotSupportedError:
            return None

    def _monitor_cb(self, monitor_uri, info_uri, event):
        signal = self.event_mapping[event]
        if signal:
            self.emit(signal, info_uri)

    def close(self):
        try: 
            gnomevfs.monitor_cancel(self.monitor)
            self.monitor = None
        except:
            return


