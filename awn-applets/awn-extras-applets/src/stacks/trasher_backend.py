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

class TrashBackend(Backend):
    vol_monitor = None
    trash_dirs = {}
    trash_monitors = {}

    def __init__(self, applet, uri, icon_size):
        Backend.__init__(self, applet, None, icon_size)

        self.vol_monitor = gnomevfs.VolumeMonitor()
        for vol in self.vol_monitor.get_mounted_volumes():
            self._vol_mounted_cb(vol)
        self.vol_monitor.connect("volume_mounted", lambda v, d: self._vol_mounted_cb)
        self.vol_monitor.connect("volume_pre_unmount", lambda v, d: self._vol_unmounted_cb)

    def _create(self):
        return

    def _vol_unmounted_cb(self, volume):
        uri = VfsUri(volume.get_activation_uri())
        try:
            dir = self.trash_dirs[uri]
            vfs_uris = self.read_from_uri(dir)
            if vfs_uris:
                self.remove(vfs_uris)
            #mon = self.trash_monitors[uri]
            #mon.close()
            del self.trash_dirs[uri]
            #del self.trash_monitors[uri]
        except KeyError:
            return


    def _vol_mounted_cb(self, volume):
        uri = VfsUri(volume.get_activation_uri())
        if volume.handles_trash():
            gnomevfs.async.find_directory(
                    near_uri_list = [uri.as_uri()],
                    kind = gnomevfs.DIRECTORY_KIND_TRASH,
                    create_if_needed = True,
                    find_if_needed = True,
                    permissions = 0777,
                    callback = self._find_directory,
                    user_data = uri)


    def _find_directory(self, handle, results, volume_uri):
        # FIXME: Support multiple trash directories per volume?
        for uri, error in results:
            # error is None if Trash directory is successfully found
            if error != None:
                continue
            trash_uri = VfsUri(str(uri))
            if trash_uri.as_string() in [x.as_string() for x in self.trash_dirs.values()]:
                continue
            monitor = Monitor(trash_uri)
            monitor.connect("created", self._created_cb)
            monitor.connect("deleted", self._deleted_cb)
            #self.trash_monitors[volume_uri] = monitor
            vfs_uris = self.read_from_uri(trash_uri)
            if vfs_uris:
                self.add(vfs_uris)
            self.trash_dirs[volume_uri] = trash_uri
            break


    def _empty_cb(self, widget):
        self.clear()


    def clear(self):
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

        options = gnomevfs.XFER_EMPTY_DIRECTORIES
#        options |= gnomevfs.XFER_FOLLOW_LINKS
        options |= gnomevfs.XFER_RECURSIVE
#        options |= gnomevfs.XFER_FOLLOW_LINKS_RECURSIVE

        uris = []
        for b in self.trash_dirs.values():
            uris.append(b.as_uri())

        # TODO: nice msg: "Emptying trash" in stacksvfs
        GUITransfer(uris, [], options)
        Backend.clear(self)

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

    def _add_cb(self, handle, results, uri_list):
        source_uri_list = []
        target_uri_list = []
        unmovable_uri_list = []
        for i in xrange(len(results)):
            trash_uri, error = results[i]
            source_uri = uri_list[i]
            # error is None if Trash directory is successfully found
            if error == None:
                source_uri_list.append(source_uri)
                target_uri_list.append(trash_uri.append_file_name(source_uri.short_name))
            else:
                unmovable_uri_list.append(source_uri)
        if len(source_uri_list) > 0:
            options = gnomevfs.XFER_REMOVESOURCE | gnomevfs.XFER_RECURSIVE
            GUITransfer(source_uri_list, target_uri_list, options)

        num_files = len(unmovable_uri_list)
        if (num_files > 0):
            if len(source_uri_list) == 0:
                msg = _("Cannot move items to trash, do you want to delete them immediately?")
                msg2 = _("None of the %d selected items can be moved to the Trash") % num_files
            else:
                msg = _("Cannot move some items to trash, do you want to delete these immediately?")
                msg2 = _("%d of the selected items cannot be moved to the Trash") % num_files

            dialog = gtk.MessageDialog(type = gtk.MESSAGE_QUESTION,
                                       flags = gtk.DIALOG_MODAL,
                                       message_format = msg)
            dialog.format_secondary_text(msg2)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            button = gtk.Button(label=_("_Delete"), use_underline=True)
            button.set_property("can-default", True)
            button.show()
            dialog.add_action_widget(button, gtk.RESPONSE_ACCEPT)
            dialog.set_default_response(gtk.RESPONSE_ACCEPT)
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                options = gnomevfs.XFER_DELETE_ITEMS | gnomevfs.EMPTY_DIRECTORIES
                GUITransfer(unmovable_uri_list, [], options)

    def add(self, vfs_uris, action=None):
        if action is None:
            return Backend.add(self, vfs_uris, action)
        uri_list = [u.as_uri() for u in vfs_uris]
        gnomevfs.async.find_directory(
                near_uri_list = uri_list,
                kind = gnomevfs.DIRECTORY_KIND_TRASH,
                create_if_needed = True,
                find_if_needed = False,
                permissions = 0777,
                callback = self._add_cb,
                user_data = uri_list)
        # wait for monitor to add the file


    def read_from_uri(self, vfs_uri):
        try:
            handle = gnomevfs.DirectoryHandle(vfs_uri.as_uri())
        except:
            print "Stacks Error: ", vfs_uri.as_string(), " not found"
            return
        try:
            fileinfo = handle.next()
        except StopIteration:
            return
        vfs_uris = []
        while fileinfo:
            if fileinfo.name[0] != "." and not fileinfo.name.endswith("~"):
                try:
                    new_vfs_uri = VfsUri(vfs_uri.as_uri().append_path(fileinfo.name))
                    vfs_uris.append(new_vfs_uri)
                except TypeError:
                    continue
            try:
                fileinfo = handle.next()
            except StopIteration:
                break
        return vfs_uris


    def read(self):
        for vfs_uri in self.trash_dirs.values():
            vfs_uris = self.read_from_uri(vfs_uri)
            if vfs_uris:
                self.add(vfs_uris)
