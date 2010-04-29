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

import gtk
import gio
from stacks_backend import *


class FileBackend(Backend):

    handle = None
    backend_uri = None

    def __init__(self, applet, vfs_uri, icon_size):
        Backend.__init__(self, applet, icon_size)
        self.backend_uri = vfs_uri
        uri = self.backend_uri.as_uri()
        if not uri.query_exists():
            # create folder
            try:
                uri.get_parent().make_directory_with_parents(gio.Cancellable())
            except gio.Error:
                pass
            # create file
            self.handle = uri.create()
        else:
            self.handle = uri.append_to()


    def remove(self,vfs_uris):
        buffer = ""
        content, length, etag = self.backend_uri.as_uri().load_contents()
        lines = content.splitlines()
        for line in lines:
            for vfs_uri in vfs_uris:
                uri = vfs_uri.as_string()
                if cmp(uri, line):
                    buffer += line + os.linesep
                    break
        if len(buffer) > 0:
            self.handle.truncate(0)
            self.handle.seek(0)
            self.handle.write(buffer)
        return Backend.remove(self, vfs_uris)


    def add(self, vfs_uris, action=None):
        if action is not None:
            for vfs_uri in vfs_uris:
                self.handle.seek(0, 2) # hopefully 2 is SEEK_END
                self.handle.write(vfs_uri.as_string() + os.linesep)
        return Backend.add(self, vfs_uris)


    def read(self):
        content, length, etag = self.backend_uri.as_uri().load_contents()
        lines = content.splitlines()
        vfs_uris = []
        for line in lines:
            try:
                vfs_uri = VfsUri(line.strip())
                vfs_uris.append(vfs_uri)
            except TypeError:
                continue
        if vfs_uris:
            self.add(vfs_uris)


    def clear(self):
        self.handle.truncate(0)
        Backend.clear(self)


    # Do nothing on "open"; not really useful
    def open(self):
        return


    def get_type(self):
        return BACKEND_TYPE_FILE


    def _clear_cb(self, widget):
        self.clear()


    def get_menu_items(self):
        items = []
        clear_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        clear_item.connect_object("activate",self._clear_cb,self)
        items.append(clear_item)
        return items
