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
from stacks_vfs import VfsUri, Monitor

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class PluggerBackend(FolderBackend):

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

    def get_type(self):
        return BACKEND_TYPE_PLUGGER

    def get_title(self):
        title = self.applet.gconf_client.get_string(self.applet.gconf_path + "/title")
        if title:
            return title;
        else:
            return _("Mounted Volume")

    def get_menu_items(self):
        items = FolderBackend.get_menu_items(self)
        unmount_item = gtk.MenuItem(label=_("Unmount Volume"))
        unmount_item.connect_object("activate", self._unmount_cb, self)
        items.append(unmount_item)
        hide_item = gtk.MenuItem(label=_("Hide Volume"))
        hide_item.connect_object("activate", self._hide_cb, self)
        items.append(hide_item)
        return items
