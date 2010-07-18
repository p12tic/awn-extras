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
import gio

from awn.extras import _

from stacks_backend import *
from stacks_vfs import *


class FolderBackend(Backend):

    monitor = None
    backend_uri = None

    def __init__(self, applet, vfs_uri, icon_size):
        Backend.__init__(self, applet, icon_size)
        self.backend_uri = vfs_uri
        # Create folder if it does not exist
        self._create()
        self.monitor = Monitor(self.backend_uri)
        if self.monitor:
            self.monitor.connect("created", self._created_cb)
            self.monitor.connect("deleted", self._deleted_cb, True)

    def _create(self):
        uri = self.backend_uri.as_uri()
        try:
            uri.make_directory_with_parents(gio.Cancellable())
        except gio.Error:
            pass

    def add(self, vfs_uris, action=None):
        if not action:
            return Backend.add(self, vfs_uris)
        else:
            src_lst = []
            dst_lst = []
            vfs_uri_lst = []
            for vfs_uri in vfs_uris:

                dst_uri = self.backend_uri.create_child(vfs_uri.as_uri())
                src_lst.append(vfs_uri.as_uri())
                dst_lst.append(dst_uri)
                vfs_uri_lst.append(VfsUri(dst_uri))

            GUITransfer(src_lst, dst_lst, action)
            return Backend.add(self, vfs_uri_lst)

    def read(self):
        if not self.backend_uri.as_uri().query_exists():
            print "Stacks Error: ", self.backend_uri.as_string(), " not found"
            return

        vfs_uris = []
        attrs = ','.join([gio.FILE_ATTRIBUTE_STANDARD_IS_HIDDEN,
                          gio.FILE_ATTRIBUTE_STANDARD_IS_BACKUP,
                          gio.FILE_ATTRIBUTE_STANDARD_NAME])
        enumerator = self.backend_uri.as_uri().enumerate_children(attrs)
        fileinfo = enumerator.next_file()
        while fileinfo:
            if not fileinfo.get_is_hidden() and not fileinfo.get_is_backup():
                try:
                    f = self.backend_uri.create_child(fileinfo.get_name())
                    vfs_uri = VfsUri(f)
                    vfs_uris.append(vfs_uri)
                except TypeError:
                    continue
            fileinfo = enumerator.next_file()
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

        GUITransfer([self.backend_uri.as_uri()], [], 0)

        # destroy dialog
        dialog.destroy()
        Backend.clear(self)

    def get_title(self):
        title = self.applet.client.get_string(GROUP_DEFAULT, "title")
        if title is None or len(title) == 0:
            title = None
        return title or self.backend_uri.as_uri().get_basename()

    def get_type(self):
        return BACKEND_TYPE_FOLDER

    def destroy(self):
        if self.monitor:
            self.monitor.close()
        Backend.destroy(self)

    def open(self):
        LaunchManager().launch_uri(self.backend_uri.as_string(), None)

    def _open_cb(self, widget):
        self.open()

    def get_menu_items(self):
        items = []
        open_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_OPEN)
        open_item.connect_object("activate", self._open_cb, self)
        items.append(open_item)
        return items
