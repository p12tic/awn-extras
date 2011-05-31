#!/usr/bin/python
# Copyright (C) 2010 - 2011  onox <denkpadje@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import os
import re
from urllib import unquote

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import _, awnlib, __version__
from desktopagnostic import fdo, vfs

import gio
import glib

applet_name = _("Common Folder Launcher")
applet_description = _("Applet to launch common folders and bookmarks")

# Applet's themed icon, also shown in the GTK About dialog
applet_logo = "folder"

# Describes the pattern used to try to decode URLs
url_pattern = re.compile("^[a-z]+://(?:[^@]+@)?([^/]+)/(.*)$")

user_path = os.path.expanduser("~/")
bookmarks_file = os.path.expanduser("~/.gtk-bookmarks")

# Ordered sequence of XDG user special folders
user_dirs = [glib.USER_DIRECTORY_DOCUMENTS,
             glib.USER_DIRECTORY_MUSIC,
             glib.USER_DIRECTORY_PICTURES,
             glib.USER_DIRECTORY_VIDEOS,
             glib.USER_DIRECTORY_DOWNLOAD,
             glib.USER_DIRECTORY_PUBLIC_SHARE,
             glib.USER_DIRECTORY_TEMPLATES]
xdg_user_uris = ["file://%s" % glib.get_user_special_dir(dir) for dir in user_dirs]


class CommonFolderApplet:

    """Applet to launch common folders and bookmarks.

    """

    def __init__(self, applet):
        self.applet = applet

        self.__monitors = []

        self.icon_theme = gtk.icon_theme_get_default()

        # Monitor bookmarks file for changes
        self.__bookmarks_monitor = gio.File(bookmarks_file).monitor_file()  # keep a reference to avoid getting it garbage collected
        def bookmarks_changed_cb(monitor, file, other_file, event):
            if event == gio.FILE_MONITOR_EVENT_CHANGES_DONE_HINT:
                self.rebuild_icons()
        self.__bookmarks_monitor.connect("changed", bookmarks_changed_cb)

        self.rebuild_icons()

    def rebuild_icons(self):
        glib.idle_add(self.add_folders_and_bookmarks)

    def add_folders_and_bookmarks(self):
        self.applet.icons.destroy_all()

        # Destroy all current local bookmark monitors
        for monitor in self.__monitors:
            monitor.cancel()
        self.__monitors = []

        self.add_folder_icon(_("Home Folder"), "user-home", "file://%s" % user_path)

        # Add Desktop
        desktop_path = glib.get_user_special_dir(glib.USER_DIRECTORY_DESKTOP)
        if desktop_path != user_path:
            self.add_folder_icon(glib.filename_display_basename(desktop_path), "user-desktop", "file://%s" % desktop_path)

        # Add XDG user special folders
        for uri in xdg_user_uris:
            self.add_url_name(uri)

        # Add bookmarks
        if os.path.isfile(bookmarks_file):
            with open(bookmarks_file) as f:
                for url_name in (i.rstrip().split(" ", 1) for i in f):
                    if url_name[0] not in xdg_user_uris:
                        self.add_url_name(*url_name)

    def add_url_name(self, uri, name=None):
        if not uri:
            return

        file = vfs.File.for_uri(uri)

        if file.is_native():
            monitor = gio.File(uri).monitor_file()
            self.__monitors.append(monitor)
            monitor.connect("changed", self.file_changed_cb)

            if not file.exists():
                return

            icon = None

            # Use a custom icon if it has been set
            info = gio.File(uri).query_info("metadata::custom-icon", gio.FILE_QUERY_INFO_NONE)
            custom_icon_uri = info.get_attribute_string("metadata::custom-icon")
            if custom_icon_uri is not None:
                icon = vfs.File.for_uri(custom_icon_uri)

            if icon is None or not icon.exists():
                existing_icons = filter(self.icon_theme.has_icon, file.get_icon_names())
                icon = existing_icons[0] if len(existing_icons) > 0 else "image-missing"
        else:
            icon = "folder-remote"

        if name is None:
            match = url_pattern.match(uri)
            if match is not None:
                name = "/%s on %s" % (match.group(2), match.group(1))
            else:
                if file.is_native():
                    filename = os.path.abspath(file.props.path)
                    name = glib.filename_display_basename(filename)
                else:
                    name = uri
                name = unquote(str(name))

        self.add_folder_icon(name, icon, uri)

    def add_folder_icon(self, label, icon_name, uri):
        icon = self.applet.icons.add(icon_name, label)
        icon.connect("clicked", self.icon_clicked_cb, uri)

    def icon_clicked_cb(self, widget, uri):
        file = vfs.File.for_uri(uri)

        if file is not None:
            try:
                file.launch()
            except glib.GError, e:
                if file.is_native():
                    print "Error while launching: %s" % e
                else:
                    def mount_result(gio_file2, result):
                        try:
                            if gio_file2.mount_enclosing_volume_finish(result):
                                file.launch()
                        except glib.GError, e:
                            print "Error while launching remote location: %s" % e
                    gio_file = gio.File(file.props.uri)
                    gio_file.mount_enclosing_volume(gtk.MountOperation(), mount_result)

    def file_changed_cb(self, monitor, file, other_file, event):
        if event in (gio.FILE_MONITOR_EVENT_CREATED, gio.FILE_MONITOR_EVENT_DELETED):
            self.rebuild_icons()


if __name__ == "__main__":
    awnlib.init_start(CommonFolderApplet, {"name": applet_name,
        "short": "common-folder",
        "version": __version__,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox",
        "copyright-year": "2010 - 2011",
        "authors": ["onox <denkpadje@gmail.com>"]},
        ["multiple-icons"])
