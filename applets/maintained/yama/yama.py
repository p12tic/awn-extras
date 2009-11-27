#!/usr/bin/python
# Copyright (C) 2009  onox <denkpadje@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import commands
import os
import re
import subprocess
from threading import Lock
from urllib import unquote

import pygtk
pygtk.require('2.0')
import gtk

from awn.extras import awnlib, __version__

try:
    import dbus
except ImportError:
    dbus = None

import gio
import glib
import gmenu
from xdg import DesktopEntry

applet_name = "YAMA"
applet_description = "Main menu with places and recent documents"

# Applet's themed icon, also shown in the GTK About dialog
applet_logo = "gnome-main-menu"

file_manager_apps = ("nautilus", "thunar", "xdg-open")

menu_editor_apps = ("alacarte", "gmenu-simple-editor")

data_dirs = os.environ["XDG_DATA_DIRS"] if "XDG_DATA_DIRS" in os.environ else "/usr/local/share/:/usr/share/"

# Describes the pattern used to try to decode URLs
url_pattern = re.compile("^[a-z]+://(?:[^@]+@)?([^/]+)/(.*)$")

# Pattern to extract the part of the path that doesn't end with %<a-Z>
exec_pattern = re.compile("^(.*?)\s+\%[a-zA-Z]$")

# Delay in seconds before starting rebuilding the menu
menu_rebuild_delay = 3


class YamaApplet:

    """Applet to show Yet Another Menu Applet.

    """

    def __init__(self, applet):
        self.applet = applet

        self.__rebuild_lock = Lock()

        self.__schedule_id = {"applications.menu": None, "settings.menu": None}
        self.__schedule_lock = Lock()

        self.setup_context_menu()

        self.menu = gtk.Menu()
        self.icon_theme = gtk.icon_theme_get_default()
        self.icon_theme.connect("changed", self.theme_changed_cb)

        with self.__rebuild_lock:
            self.build_menu()

        applet.connect("clicked", self.clicked_cb)

        # Inhibit autohide while main menu is visible
        def show_menu_cb(widget):
            self.__autohide_cookie = applet.inhibit_autohide("showing main menu")
            applet.get_icon().set_is_active(True)
            applet.get_icon().get_effects().props.depressed = False
        self.menu.connect("show", show_menu_cb)
        def hide_menu_cb(widget):
            applet.uninhibit_autohide(self.__autohide_cookie)
            applet.get_icon().set_is_active(False)
            applet.get_icon().get_effects().props.depressed = False
        self.menu.connect("hide", hide_menu_cb)

    def build_menu(self):
        self.applications_items = []
        self.settings_items = []

        """ Applications """
        tree = gmenu.lookup_tree("applications.menu")
        self.append_directory(tree.root, self.menu, item_list=self.applications_items)
        tree.add_monitor(self.menu_changed_cb, self.applications_items)

        self.menu.append(gtk.SeparatorMenuItem())

        """ Places """
        self.create_places_submenu(self.menu)

        """ System """
        tree = gmenu.lookup_tree("settings.menu")
        self.append_directory(tree.root, self.menu, item_list=self.settings_items)
        tree.add_monitor(self.menu_changed_cb, self.settings_items)

        """ Session actions """
        if dbus is not None:
            self.append_session_actions(self.menu)

        self.menu.show_all()

    def append_session_actions(self, menu):
        session_bus = dbus.SessionBus()

        dbus_services = session_bus.list_names()
        can_lock_screen = "org.gnome.ScreenSaver" in dbus_services
        can_manage_session = "org.gnome.SessionManager" in dbus_services

        if can_lock_screen or can_manage_session:
            menu.append(gtk.SeparatorMenuItem())

        if can_lock_screen:
            lock_item = self.append_menu_item(menu, "Lock Screen", "system-lock-screen", "Protect your computer from unauthorized use")
            def lock_screen_cb(widget):
                try:
                    ss_proxy = session_bus.get_object("org.gnome.ScreenSaver", "/")
                    dbus.Interface(ss_proxy, "org.gnome.ScreenSaver").Lock()
                except dbus.DBusException, e:
                    # NoReply exception may occur even while the screensaver did lock the screen
                    if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
                        raise
            lock_item.connect("activate", lock_screen_cb)

        if can_manage_session:
            sm_proxy = session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
            sm_if = dbus.Interface(sm_proxy, "org.gnome.SessionManager")

            user_name = commands.getoutput("whoami")
            logout_item = self.append_menu_item(menu, "Log Out %s..." % user_name, "system-log-out", "Log out %s of this session to log in as a different user" % user_name)
            logout_item.connect("activate", lambda w: sm_if.Logout(0))

            shutdown_item = self.append_menu_item(menu, "Shut Down...", "system-shutdown", "Shut down the system")
            shutdown_item.connect("activate", lambda w: sm_if.Shutdown())

    def clicked_cb(self, widget):
        def get_position(menu):
            icon_x, icon_y = self.applet.get_icon().window.get_origin()

            menu_size = self.menu.size_request()
            # Make sure the bottom of the menu doesn't get below the bottom of the screen
            icon_y = min(icon_y, self.menu.get_screen().get_height() - menu_size[1])

            padding = 6
            orientation = self.applet.get_pos_type()
            if orientation == gtk.POS_BOTTOM:
                icon_y = self.menu.get_screen().get_height() - self.applet.get_size() - self.applet.props.offset - menu_size[1] - padding
            elif orientation == gtk.POS_TOP:
                icon_y = self.applet.get_size() + self.applet.props.offset + padding
            elif orientation == gtk.POS_RIGHT:
                icon_x = self.menu.get_screen().get_width() - self.applet.get_size() - self.applet.props.offset - menu_size[0] - padding
            elif orientation == gtk.POS_LEFT:
                icon_x = self.applet.get_size() + self.applet.props.offset + padding

            return (icon_x, icon_y, False)
        self.menu.popup(None, None, get_position, 0, 0)

    def setup_context_menu(self):
        """Add "Edit Menus" to the context menu.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        edit_menus_item = gtk.MenuItem("_Edit Menus")
        edit_menus_item.connect("activate", self.show_menu_editor_cb)
        menu.insert(edit_menus_item, menu_index)

        menu.insert(gtk.SeparatorMenuItem(), menu_index + 1)

    def show_menu_editor_cb(self, widget):
        for command in menu_editor_apps:
            try:
                subprocess.Popen(command)
                return
            except OSError:
                pass
        raise RuntimeError("No menu editor found (%s)" % ", ".join(menu_editor_apps))

    def menu_changed_cb(self, menu_tree, menu_items):
        def refresh_menu(tree, items):
            with self.__rebuild_lock:
                # Delete old items
                for i in xrange(len(items)):
                    items.pop().destroy()

                index = len(self.applications_items) + 2 if items is self.settings_items else 0  # + 2 = separator + Places
                self.append_directory(tree.root, self.menu, index=index, item_list=items)
                # Refresh menu to re-initialize the widget
                self.menu.show_all()
            return False
        with self.__schedule_lock:
            file = menu_tree.menu_file
            if self.__schedule_id[file] is not None:
                glib.source_remove(self.__schedule_id[file])
            self.__schedule_id[file] = glib.timeout_add_seconds(menu_rebuild_delay, refresh_menu, menu_tree, menu_items)

    def theme_changed_cb(self, icon_theme):
        """Upon theme change clean the whole menu, and then rebuild it.

        """
        with self.__rebuild_lock:
            self.menu.foreach(gtk.Widget.destroy)
            self.build_menu()

    def start_subprocess_cb(self, widget, command, use_shell):
        try:
            subprocess.Popen(command, shell=use_shell)
        except OSError:
            pass

    def open_folder_cb(self, widget, path):
        for command in file_manager_apps:
            try:
                subprocess.Popen([command, path])
                return
            except OSError:
                pass
        raise RuntimeError("No file manager found (%s) for %s" % (", ".join(file_manager_apps), path))

    def create_places_submenu(self, parent_menu):
        item = self.append_menu_item(parent_menu, "Places", "folder", None)

        menu = gtk.Menu()
        item.set_submenu(menu)

        user_path = os.path.expanduser("~/")

        home_item = self.append_menu_item(menu, "Home Folder", "user-home", "Open your personal folder")
        home_item.connect("activate", self.open_folder_cb, user_path)
        desktop_item = self.append_menu_item(menu, "Desktop", "user-desktop", "Open the contents of your desktop in a folder")
        desktop_item.connect("activate", self.open_folder_cb, os.path.join(user_path, "Desktop"))

        """ Bookmarks """
        self.places_menu = menu
        self.bookmarks_items = []
        self.append_bookmarks()

        # Monitor bookmarks file for changes
        bookmarks_file = os.path.expanduser("~/.gtk-bookmarks")
        self.__bookmarks_monitor = gio.File(bookmarks_file).monitor_file()  # keep a reference to avoid getting it garbage collected
        def bookmarks_changed_cb(monitor, file, other_file, event):
            if event == gio.FILE_MONITOR_EVENT_CHANGES_DONE_HINT:
                with self.__rebuild_lock:
                    self.append_bookmarks()
                    # Refresh menu to re-initialize the widget
                    self.places_menu.show_all()
        self.__bookmarks_monitor.connect("changed", bookmarks_changed_cb)

        menu.append(gtk.SeparatorMenuItem())

        """ Devices """
        added = False
        added |= self.append_awn_desktop(menu, "nautilus-computer")
        added |= self.append_awn_desktop(menu, "nautilus-cd-burner")

        # Set up volumes and mounts monitor
        self.__volumes_mounts_monitor = gio.volume_monitor_get()

        self.__volumes_index = len(self.places_menu) - len(self.bookmarks_items)
        self.volume_items = []
        self.append_volumes()
        # TODO if added is False and no volumes, then their are two separators

        if added:
            menu.append(gtk.SeparatorMenuItem())

        added = False
        added |= self.append_awn_desktop(menu, "network-scheme")

        self.__mounts_index = len(self.places_menu) - len(self.volume_items) - len(self.bookmarks_items)
        self.mount_items = []
        self.append_mounts()
        # TODO if added is False and no mounts, then their are two separators

        # Connect signals after having initialized volumes and mounts
        for signal in ("volume-added", "volume-changed", "volume-removed", "mount-added", "mount-changed", "mount-removed"):
            self.__volumes_mounts_monitor.connect(signal, self.refresh_volumes_mounts_cb)

        ncs_exists = os.path.exists(commands.getoutput("which nautilus-connect-server"))
        if ncs_exists:
            connect_item = self.append_menu_item(menu, "Connect to Server...", "stock_internet", "Connect to a remote computer or shared disk")
            connect_item.connect("activate", self.start_subprocess_cb, "nautilus-connect-server", False)
        added |= ncs_exists

        if added:
            menu.append(gtk.SeparatorMenuItem())

        self.append_awn_desktop(menu, "gnome-search-tool")

        """ Recent Documents """
        self.create_documents_submenu(menu)

    def create_documents_submenu(self, menu):
        recent_manager = gtk.recent_manager_get_default()

        chooser_menu = gtk.RecentChooserMenu(recent_manager)
        recent_item = self.append_menu_item(menu, "Recent Documents", "document-open-recent", None)
        recent_item.set_submenu(chooser_menu)

        def set_sensitivity_recent_menu(widget=None):
            recent_item.set_sensitive(recent_manager.props.size > 0)
        recent_manager.connect("changed", set_sensitivity_recent_menu)
        set_sensitivity_recent_menu()

        def open_recent_document(widget):
            self.start_subprocess_cb(None, "xdg-open %s" % widget.get_current_uri(), True)
        chooser_menu.connect("item-activated", open_recent_document)

        chooser_menu.append(gtk.SeparatorMenuItem())

        item = self.append_menu_item(chooser_menu, "Clear Recent Documents", "gtk-clear", "Clear all items from the recent documents list")
        clear_dialog = self.ClearRecentDocumentsDialog(self.applet, recent_manager.purge_items)
        def purge_items_cb(widget):
            clear_dialog.show_all()
            clear_dialog.deiconify()
        item.connect("activate", purge_items_cb)

    def append_bookmarks(self):
        # Delete old items
        for item in self.bookmarks_items:
            item.destroy()
        self.bookmarks_items = []

        index = 2
        bookmarks_file = os.path.expanduser("~/.gtk-bookmarks")
        if os.path.isfile(bookmarks_file):
            with open(bookmarks_file) as f:
                for url_name in (i.rstrip().split(" ", 1) for i in f):
                    if len(url_name) == 1:
                        match = url_pattern.match(url_name[0])
                        if match is not None:
                            url_name.append("/%s on %s" % (match.group(2), match.group(1)))
                        else:
                            basename = glib.filename_display_basename(url_name[0])
                            url_name.append(unquote(str(basename)))
                    url, name = (url_name[0], url_name[1])

                    icon = "folder" if url.startswith("file://") else "folder-remote"
                    display_url = url[7:] if url.startswith("file://") else url

                    item = self.create_menu_item(name, icon, "Open '%s'" % display_url)
                    self.places_menu.insert(item, index)
                    item.connect("activate", self.open_folder_cb, url)
                    index += 1
                    self.bookmarks_items.append(item)

    def refresh_volumes_mounts_cb(self, monitor, volume_mount):
        with self.__rebuild_lock:
            self.append_volumes()
            self.append_mounts()
    
            # Refresh menu to re-initialize the widget
            self.places_menu.show_all()

    def append_volumes(self):
        # Delete old items
        for item in self.volume_items:
            item.destroy()
        self.volume_items = []

        index = self.__volumes_index + len(self.bookmarks_items)
        for volume in self.__volumes_mounts_monitor.get_volumes():
            name = volume.get_name()

            def get_icon_name(icon):
                if isinstance(icon, gio.ThemedIcon):
                    icons = icon.get_names()
                    return filter(self.icon_theme.has_icon, icons)[0]
                else:
                    return icon.get_file().get_path()
            mount = volume.get_mount()
            if mount is not None:
                icon_name = get_icon_name(mount.get_icon())
                tooltip = name
            else:
                icon_name = get_icon_name(volume.get_icon())
                tooltip = "Mount %s" % name

            item = self.create_menu_item(name, icon_name, tooltip)
            self.places_menu.insert(item, index)
            index += 1
            self.volume_items.append(item)

            if mount is not None:
                url = mount.get_root().get_uri()
                item.connect("activate", self.open_folder_cb, url)
            else:
                def mount_volume(widget, vol):
                    def mount_result(vol2, result):
                        if volume.mount_finish(result):
                            url = volume.get_mount().get_root().get_uri()
                            self.open_folder_cb(None, url)
                    volume.mount(gio.MountOperation(), mount_result)
                item.connect("activate", mount_volume, volume)

    def append_mounts(self):
        # Delete old items
        for item in self.mount_items:
            item.destroy()
        self.mount_items = []

        index = self.__mounts_index + len(self.volume_items) + len(self.bookmarks_items)
        for mount in self.__volumes_mounts_monitor.get_mounts():
            if mount.get_volume() is None:
                name = mount.get_name()
                icons = mount.get_icon().get_names()

                item = self.create_menu_item(name, icons[1], name)
                self.places_menu.insert(item, index)
                index += 1
                self.mount_items.append(item)

                url = mount.get_root().get_uri()
                item.connect("activate", self.open_folder_cb, url)

    def create_menu_item(self, label, icon_name, comment):
        item = gtk.ImageMenuItem(label)
        if gtk.gtk_version >= (2, 16, 0):
            item.props.always_show_image = True
        icon_pixbuf = self.get_pixbuf_icon(icon_name)
        item.set_image(gtk.image_new_from_pixbuf(icon_pixbuf))
        if comment is not None:
            item.set_tooltip_text(comment)
        return item

    def append_menu_item(self, menu, label, icon_name, comment):
        item = self.create_menu_item(label, icon_name, comment)
        menu.append(item)
        return item

    def launch_app(self, widget, desktop_path):
        if os.path.exists(desktop_path):
            path = DesktopEntry.DesktopEntry(desktop_path).getExec()

            # Strip last part of path if it contains %<a-Z>
            match = exec_pattern.match(path)
            if match is not None:
                path = match.group(1)

            self.start_subprocess_cb(None, path, True)

    def append_directory(self, tree, menu, index=None, item_list=None):
        for node in tree.contents:
            if not isinstance(node, gmenu.Entry) and not isinstance(node, gmenu.Directory):
                continue
            # Don't set comment yet because we don't want it for submenu's
            item = self.create_menu_item(node.name, node.icon, None)

            menu.append(item) if index is None else menu.insert(item, index)
            if item_list is not None:
                item_list.append(item)

            if isinstance(node, gmenu.Entry):
                item.set_tooltip_text(node.comment)
                item.connect("activate", self.launch_app, node.desktop_file_path)

                # Setup drag & drop
                item.drag_source_set(gtk.gdk.BUTTON1_MASK, [("text/uri-list", 0, 0)], gtk.gdk.ACTION_COPY)
                if node.icon is not None:
                    item.drag_source_set_icon_name(node.icon)
                item.connect("drag-data-get", self.drag_item_cb, node.desktop_file_path)
            else:
                sub_menu = gtk.Menu()
                item.set_submenu(sub_menu)
                self.append_directory(node, sub_menu)
            if index is not None:
                index += 1

    def drag_item_cb(self, widget, context, selection_data, info, time, path):
        selection_data.set_uris(["file://" + path])

    def append_awn_desktop(self, menu, desktop_name):
        for dir in data_dirs.split(":"):
            path = os.path.join(dir, "applications", desktop_name + ".desktop")
            if os.path.isfile(path):
                desktop_entry = DesktopEntry.DesktopEntry(path)
                item = self.append_menu_item(menu, desktop_entry.getName(), desktop_entry.getIcon(), desktop_entry.getComment())
                item.connect("activate", self.launch_app, desktop_entry.getFileName())
                return True
        return False

    def get_pixbuf_icon(self, icon_value):
        if not icon_value:
            return None

        if os.path.isabs(icon_value):
            if os.path.isfile(icon_value):
                try:
                    return gtk.gdk.pixbuf_new_from_file_at_size(icon_value, 24, 24)
                except glib.GError:
                    return None
            icon_name = os.path.basename(icon_value)
        else:
            icon_name = icon_value

        if re.match(".*\.(png|xpm|svg)$", icon_name) is not None:
            icon_name = icon_name[:-4]
        try:
            return self.icon_theme.load_icon(icon_name, 24, gtk.ICON_LOOKUP_FORCE_SIZE)
        except:
            for dir in data_dirs.split(":"):
                for i in ("pixmaps", "icons"):
                    path = os.path.join(dir, i, icon_value)
                    if os.path.isfile(path):
                        return gtk.gdk.pixbuf_new_from_file_at_size(path, 24, 24)

    class ClearRecentDocumentsDialog(awnlib.Dialogs.BaseDialog, gtk.MessageDialog):

        def __init__(self, parent, clear_cb):
            gtk.MessageDialog.__init__(self, type=gtk.MESSAGE_WARNING, message_format="Clear the Recent Documents list?", buttons=gtk.BUTTONS_CANCEL)
            awnlib.Dialogs.BaseDialog.__init__(self, parent)

            self.set_skip_taskbar_hint(False)

            self.set_title("Clear Recent Documents")
            self.format_secondary_markup("Clearing the Recent Documents list will clear the following:\n\
* All items from the Places > Recent Documents menu item.\n\
* All items from the recent documents list in all applications.")

            clear_button = gtk.Button("C_lear")
            clear_button.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
            def clear_and_hide(widget):
                self.response(gtk.RESPONSE_CANCEL)
                clear_cb()
            clear_button.connect("clicked", clear_and_hide)
            self.action_area.add(clear_button)


if __name__ == "__main__":
    awnlib.init_start(YamaApplet, {"name": applet_name,
        "short": "yama",
        "version": __version__,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox",
        "copyright-year": 2009,
        "authors": ["onox <denkpadje@gmail.com>"]},
        ["no-tooltip"])
