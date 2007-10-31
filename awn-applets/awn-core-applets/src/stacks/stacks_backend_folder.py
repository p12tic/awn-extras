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

import gtk
import gnomevfs
import gettext
from stacks_backend import *
from stacks_vfs import VfsUri, Monitor

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class FolderBackend(Backend):

    monitor = None

    def __init__(self, applet, vfs_uri, icon_size):
        Backend.__init__(self, applet, vfs_uri, icon_size)
        # Create folder if it does not exist
        self._create()
        self.monitor = Monitor(self.backend_uri)
        if self.monitor:
            self.monitor.connect("created", self._created_cb)
            self.monitor.connect("deleted", self._deleted_cb)


    def _create(self):
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


    def add(self, vfs_uris, action=None):
        pixbuf = Backend.add(self, vfs_uris)
        if action is not None and pixbuf is not None:
            src_lst = [], dst_lst = []
            for vfs_uri in vfs_uris:
                src_lst.append(vfs_uri.as_uri())
                dst_lst.append(
                        self.backend_uri.as_uri().append_path(
                                vfs_uri.as_uri().short_name))
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
            GUITransfer(src_lst, dst_lst, options)
        return pixbuf


    def read(self):
        try:
            handle = gnomevfs.DirectoryHandle(self.backend_uri.as_uri())
        except:
            print "Stacks Error: ", self.backend_uri.as_string(), " not found"
            return
        try:
            fileinfo = handle.next()
        except StopIteration:
            return
        vfs_uris = []
        while fileinfo:
            if fileinfo.name[0] != "." and not fileinfo.name.endswith("~"):
                try:
                    vfs_uri = VfsUri(self.backend_uri.as_uri().append_path(fileinfo.name))
                    vfs_uris.append(vfs_uri)
                except TypeError:
                    continue
            try:
                fileinfo = handle.next()
            except StopIteration:
                break
        if vfs_uris:
            self.add(vfs_uris)


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
        label = gtk.Label(_("This stack has a <b>folder backend</b>. Do you really want to <b>delete</b> the files from that folder?"))
        label.set_use_markup(True)
        label.set_line_wrap(True)
        align.add(label)
        align.show_all()
        dialog.vbox.pack_start(align, True, True, 0)
        if dialog.run() == gtk.RESPONSE_REJECT:
            dialog.destroy()
            return
        # remove files
        options = gnomevfs.XFER_EMPTY_DIRECTORIES
        options |= gnomevfs.XFER_FOLLOW_LINKS
        options |= gnomevfs.XFER_RECURSIVE
        options |= gnomevfs.XFER_FOLLOW_LINKS_RECURSIVE
        GUITransfer([self.backend_uri.as_uri()], [], options)

        # destroy dialog
        dialog.destroy()
        Backend.clear(self)


    def get_title(self):
        title = self.applet.gconf_client.get_string(
                self.applet.gconf_path + "/title")
        return title or self.backend_uri.as_uri().short_name


    def get_type(self):
        return BACKEND_TYPE_FOLDER


    def destroy(self):
        if self.monitor:
            self.monitor.close()
        Backend.destroy(self)


    def _open_cb(self, widget):
        Backend.open(self)


    def get_menu_items(self):
        items = []
        open_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_OPEN)
        open_item.connect_object("activate", self._open_cb, self)
        items.append(open_item)
        return items
