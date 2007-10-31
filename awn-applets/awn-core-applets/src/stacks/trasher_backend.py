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
import gnomevfs
import gettext
from stacks_backend_folder import *
from stacks_launcher import LaunchManager
from stacks_vfs import *

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class TrashBackend(FolderBackend):
# TODO: monitor gconf for volume changes

    def __init__(self, applet, uri, icon_size):
        # For now: quick'n'dirty hack:
        for dir in applet.gconf_client.get_list(
            applet.gconf_path + "/trash_dirs", "string"):
            if dir.find("home"):    # probably the "home" trash of user
                return Backend.__init__(self, applet, dir, icon_size)
        return Backend.__init__(self, applet, VfsUri("~/.Trash"), icon_size)

    def _empty_cb(self, widget):
        if self.applet.gconf_client.get_bool("/apps/nautilus/preferences/confirm_trash"):
            dialog = gtk.MessageDialog(type = gtk.MESSAGE_WARNING,
                                       flags = gtk.DIALOG_MODAL,
                                       message_format = _("Empty all of the items from the trash?"))
            dialog.format_secondary_text(_("If you choose to empty the trash, all items in it will be permanently lost.  Please note that you can also delete them separately."))
            dialog.set_wmclass("empty_trash", "Nautilus");
            # FIXME: Set transient
            dialog.realize()
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            button = gtk.Button(label=_("_Empty Trash"), use_underline=True)
            button.set_property("can-default", True)
            button.show()
            dialog.add_action_widget(button, gtk.RESPONSE_ACCEPT)
            dialog.set_default_response(gtk.RESPONSE_ACCEPT)
            if dialog.run() == gtk.RESPONSE_REJECT:
                dialog.destroy()
                return
            dialog.destroy()

        Backend.clear(self)
        options = gnomevfs.XFER_EMPTY_DIRECTORIES
        options |= gnomevfs.XFER_FOLLOW_LINKS
        options |= gnomevfs.XFER_RECURSIVE
        options |= gnomevfs.XFER_FOLLOW_LINKS_RECURSIVE

        uris = []
        for dir in self.applet.gconf_client.get_list(
            self.applet.gconf_path + "/trash_dirs", "string"):
            uri = VfsUri(dir)
            uris.append(uri.as_uri())
        # TODO: nice msg: "Emptying trash" in stacksvfs
        GUITransfer(uris, [], options)

    def get_title(self):
        title = self.applet.gconf_client.get_string(self.applet.gconf_path + "/title")
        if title:
            return title;
        else:
            return _("Trash")

    def get_type(self):
        return BACKEND_TYPE_TRASHER

    def get_menu_items(self):
        items = []
        open_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_OPEN)
        open_item.connect_object("activate", self._open_cb, self)
        items.append(open_item)
        empty_item = gtk.MenuItem(label=_("Empty Trash"))
        empty_item.connect_object("activate", self._empty_cb, self)
        items.append(empty_item)
        return items

    def _open_cb(self, widget):
        self.open()

    def open(self):
        LaunchManager().launch_uri("trash:", None)

    def add(self, uris, action=None):
        # note: assume all files "in one drag" originate from same device
        # (meaning -> have to be moved to same trash)
        pixbuf = Backend.add(self, uris)
        if action != None and pixbuf is not None:
            # TODO: still have to find the right trash
            trash_uri = self.backend_uri.as_uri()
            src_lst = []
            dst_lst = []
            for uri in uris:
                src_lst.append(uri.as_uri())
                dst_lst.append(trash_uri.append_path(uri.as_uri().short_name))
            options = gnomevfs.XFER_REMOVESOURCE
            options |= gnomevfs.XFER_FOLLOW_LINKS
            options |= gnomevfs.XFER_RECURSIVE
            options |= gnomevfs.XFER_FOLLOW_LINKS_RECURSIVE
            GUITransfer(src_lst, dst_lst, options)
        return pixbuf

    def read(self):
        for dir in self.applet.gconf_client.get_list(
                    self.applet.gconf_path + "/trash_dirs", "string"):
            trash_uri = VfsUri(dir)
#            try:
            if True:
                handle = gnomevfs.DirectoryHandle(trash_uri.as_uri())
                monitor = Monitor(trash_uri)
                if monitor:
                    monitor.connect("created", self._created_cb)
                    monitor.connect("deleted", self._deleted_cb)
#            except:
#                print "Stacks Error: ", trash_uri.as_string(), " not found"
#                continue
            try:
                fileinfo = handle.next()
            except StopIteration:
                continue
            uris = []
            while fileinfo:
                if fileinfo.name[0] != "." and not fileinfo.name.endswith("~"):
                    try:
                        uri = VfsUri(trash_uri.as_uri().append_path(fileinfo.name))
                        uris.append(uri)
                    except TypeError:
                        continue
                try:
                    fileinfo = handle.next()
                except StopIteration:
                    break
            if uris:
                self.add(uris)
