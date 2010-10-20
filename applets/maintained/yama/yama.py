#!/usr/bin/python
# Copyright (C) 2009 - 2010  onox <denkpadje@gmail.com>
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

from collections import defaultdict
import commands
import os
import re
import subprocess
from threading import Lock
from urllib import unquote

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import _, awnlib, __version__
from desktopagnostic import fdo, vfs

try:
    import dbus
    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)
except ImportError:
    dbus = None

import gio
import glib
import gmenu

xdg_data_dirs = [os.path.expanduser("~/.local/share")] + os.environ["XDG_DATA_DIRS"].split(":")

applet_name = _("YAMA")
applet_description = _("Main menu with places and recent documents")

# Applet's themed icon, also shown in the GTK About dialog
applet_logo = "start-here"

menu_editor_apps = ("alacarte", "gmenu-simple-editor")

# Describes the pattern used to try to decode URLs
url_pattern = re.compile("^[a-z]+://(?:[^@]+@)?([^/]+)/(.*)$")

# Delay in seconds before starting rebuilding the menu
menu_rebuild_delay = 2

gtk_show_image_ok = awnlib.is_required_version(gtk.gtk_version, (2, 16, 0))
pygio_emblemed_icon_ok = awnlib.is_required_version(gio.pygio_version, (2, 17, 0))


class YamaApplet:

    """Applet to show Yet Another Menu Applet.

    """

    def __init__(self, applet):
        self.applet = applet

        self.__rebuild_lock = Lock()

        self.__schedule_id = defaultdict(lambda: None)
        self.__schedule_lock = Lock()

        self.setup_context_menu()

        self.menu = gtk.Menu()
        self.icon_theme = gtk.icon_theme_get_default()
        self.icon_theme.connect("changed", self.theme_changed_cb)

        if dbus is not None:
            self.session_bus = dbus.SessionBus()
            dbus_proxy = self.session_bus.get_object("org.freedesktop.DBus", "/org/freedesktop/DBus")
            def name_owner_changed_cb(name, old_address, new_address):
                if name in ("org.gnome.ScreenSaver", "org.gnome.SessionManager"):
                    with self.__rebuild_lock:
                        self.append_session_actions(self.menu)
                        # Refresh menu to re-initialize the widget
                        self.menu.show_all()
            dbus_proxy.connect_to_signal("NameOwnerChanged", name_owner_changed_cb)

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
        self.session_items = []

        """ Applications """
        tree = gmenu.lookup_tree("applications.menu")
        tree.add_monitor(self.menu_changed_cb, self.applications_items)
        if tree.root is not None:
            self.append_directory(tree.root, self.menu, item_list=self.applications_items)

            self.menu.append(gtk.SeparatorMenuItem())

        """ Places """
        self.create_places_submenu(self.menu)

        """ System """
        tree = gmenu.lookup_tree("settings.menu")
        tree.add_monitor(self.menu_changed_cb, self.settings_items)
        if tree.root is not None:
            self.append_directory(tree.root, self.menu, item_list=self.settings_items)

        """ Session actions """
        if dbus is not None:
            self.append_session_actions(self.menu)

        self.menu.show_all()

    def append_session_actions(self, menu):
        for i in xrange(len(self.session_items)):
            self.session_items.pop().destroy()

        dbus_services = self.session_bus.list_names()
        can_lock_screen = "org.gnome.ScreenSaver" in dbus_services
        can_manage_session = "org.gnome.SessionManager" in dbus_services

        if can_lock_screen or can_manage_session:
            separator = gtk.SeparatorMenuItem()
            self.session_items.append(separator)
            menu.append(separator)

        if can_lock_screen:
            lock_item = self.append_menu_item(menu, _("Lock Screen"), "system-lock-screen", _("Protect your computer from unauthorized use"))
            def lock_screen_cb(widget):
                try:
                    ss_proxy = self.session_bus.get_object("org.gnome.ScreenSaver", "/")
                    dbus.Interface(ss_proxy, "org.gnome.ScreenSaver").Lock()
                except dbus.DBusException, e:
                    # NoReply exception may occur even while the screensaver did lock the screen
                    if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
                        raise
            lock_item.connect("activate", lock_screen_cb)
            self.session_items.append(lock_item)

        if can_manage_session:
            sm_proxy = self.session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
            sm_if = dbus.Interface(sm_proxy, "org.gnome.SessionManager")

            user_name = commands.getoutput("whoami")
            # Translators: %s is a user name.
            logout_item = self.append_menu_item(menu, _("Log Out %s...") % user_name, "system-log-out", _("Log out %s of this session to log in as a different user") % user_name)
            logout_item.connect("activate", lambda w: sm_if.Logout(0))
            self.session_items.append(logout_item)

            shutdown_item = self.append_menu_item(menu, _("Shut Down..."), "system-shutdown", _("Shut down the system"))
            shutdown_item.connect("activate", lambda w: sm_if.Shutdown())
            self.session_items.append(shutdown_item)

    def clicked_cb(self, widget):
        self.applet.popup_gtk_menu (self.menu, 0, gtk.get_current_event_time())

    def setup_context_menu(self):
        """Add "Edit Menus" to the context menu.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        edit_menus_item = gtk.MenuItem(_("_Edit Menus"))
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
            if tree.root is not None:
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

    def open_folder_cb(self, widget, path):
        self.open_uri(path)

    def open_uri(self, uri):
        file = vfs.File.for_uri(uri)

        if file is not None and (not file.is_native() or file.exists()):
            try:
                if not file.is_native() and not file.exists():
                    def mount_result(gio_file2, result):
                        try:
                            if gio_file2.mount_enclosing_volume_finish(result):
                                file.launch()
                        except gio.Error, e:
                            print "Error when mounting remote location: %s" % e
                    gio_file = gio.File(file.props.uri)
                    gio_file.mount_enclosing_volume(gtk.MountOperation(), mount_result)
                else:
                    file.launch()
            except glib.GError, e:
                print "Error when opening: %s" % e
        else:
            print "File at URI not found (%s)" % uri

    def create_places_submenu(self, parent_menu):
        item = self.append_menu_item(parent_menu, _("Places"), "folder", None)

        menu = gtk.Menu()
        item.set_submenu(menu)

        user_path = os.path.expanduser("~/")

        home_item = self.append_menu_item(menu, _("Home Folder"), "user-home", _("Open your personal folder"))
        home_item.connect("activate", self.open_folder_cb, "file://%s" % user_path)
        desktop_item = self.append_menu_item(menu, _("Desktop"), "user-desktop", _("Open the contents of your desktop in a folder"))
        desktop_item.connect("activate", self.open_folder_cb, "file://%s" % os.path.join(user_path, "Desktop"))

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
        # TODO if added is False and no mounts, then there are two separators

        # Connect signals after having initialized volumes and mounts
        for signal in ("volume-added", "volume-changed", "volume-removed", "mount-added", "mount-changed", "mount-removed"):
            self.__volumes_mounts_monitor.connect(signal, self.refresh_volumes_mounts_cb)

        ncs_exists = os.path.exists(commands.getoutput("which nautilus-connect-server"))
        if ncs_exists:
            connect_item = self.append_menu_item(menu, _("Connect to Server..."), "applications-internet", _("Connect to a remote computer or shared disk"))
            connect_item.connect("activate", lambda w: subprocess.Popen("nautilus-connect-server"))
        added |= ncs_exists

        if added:
            menu.append(gtk.SeparatorMenuItem())

        self.append_awn_desktop(menu, "gnome-search-tool")

        """ Recent Documents """
        self.create_documents_submenu(menu)

    def create_documents_submenu(self, menu):
        recent_manager = gtk.recent_manager_get_default()

        chooser_menu = gtk.RecentChooserMenu(recent_manager)
        recent_item = self.append_menu_item(menu, _("Recent Documents"), "document-open-recent", None)
        recent_item.set_submenu(chooser_menu)

        def set_sensitivity_recent_menu(widget=None):
            recent_item.set_sensitive(recent_manager.props.size > 0)
        recent_manager.connect("changed", set_sensitivity_recent_menu)
        set_sensitivity_recent_menu()

        def open_recent_document(widget):
            self.open_uri(widget.get_current_uri())
        chooser_menu.connect("item-activated", open_recent_document)

        chooser_menu.append(gtk.SeparatorMenuItem())

        item = self.append_menu_item(chooser_menu, _("Clear Recent Documents"), "gtk-clear", _("Clear all items from the recent documents list"))
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
                    uri, name = (url_name[0], url_name[1])

                    if uri.startswith("file://"):
                        file = vfs.File.for_uri(uri)

                        if not file.exists():
                            continue

                        icon = self.get_first_existing_icon(file.get_icon_names())
                        display_uri = uri[7:]
                    else:
                        icon = "folder-remote"
                        display_uri = uri
                    display_uri = unquote(display_uri)

                    item = self.create_menu_item(name, icon, _("Open '%s'") % display_uri)
                    self.places_menu.insert(item, index)
                    item.connect("activate", self.open_folder_cb, uri)
                    index += 1
                    self.bookmarks_items.append(item)

    def refresh_volumes_mounts_cb(self, monitor, volume_mount):
        with self.__rebuild_lock:
            self.append_volumes()
            self.append_mounts()

            # Refresh menu to re-initialize the widget
            self.places_menu.show_all()

    def get_icon_name(self, icon):
        if pygio_emblemed_icon_ok and isinstance(icon, gio.EmblemedIcon):
            icon = icon.get_icon()

        if isinstance(icon, gio.ThemedIcon):
            return self.get_first_existing_icon(icon.get_names())
        elif isinstance(icon, gio.FileIcon):
            return icon.get_file().get_path()

    def get_first_existing_icon(self, icons):
        existing_icons = filter(self.icon_theme.has_icon, icons)
        return existing_icons[0] if len(existing_icons) > 0 else "image-missing"

    def append_volumes(self):
        # Delete old items
        for item in self.volume_items:
            item.destroy()
        self.volume_items = []

        index = self.__volumes_index + len(self.bookmarks_items)
        for volume in self.__volumes_mounts_monitor.get_volumes():
            name = volume.get_name()

            mount = volume.get_mount()
            if mount is not None:
                icon_name = self.get_icon_name(mount.get_icon())
                tooltip = name
            else:
                icon_name = self.get_icon_name(volume.get_icon())
                tooltip = _("Mount %s") % name

            item = self.create_menu_item(name, icon_name, tooltip)
            self.places_menu.insert(item, index)
            index += 1
            self.volume_items.append(item)

            if mount is not None:
                uri = mount.get_root().get_uri()
                item.connect("activate", self.open_folder_cb, uri)
            else:
                def mount_volume(widget, vol):
                    def mount_result(vol2, result):
                        try:
                            if vol2.mount_finish(result):
                                uri = vol2.get_mount().get_root().get_uri()
                                self.open_uri(uri)
                        except glib.GError, e:
                            error_dialog = self.UnableToMountErrorDialog(self.applet, vol2.get_name(), e)
                            error_dialog.show_all()
                    vol.mount(gio.MountOperation(), mount_result)
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
                icon_name = self.get_icon_name(mount.get_icon())

                item = self.create_menu_item(name, icon_name, name)
                self.places_menu.insert(item, index)
                index += 1
                self.mount_items.append(item)

                uri = mount.get_root().get_uri()
                item.connect("activate", self.open_folder_cb, uri)

    def create_menu_item(self, label, icon_name, comment):
        item = gtk.ImageMenuItem(label)
        if gtk_show_image_ok:
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
        file = vfs.File.for_path(desktop_path)

        if file is not None and file.exists():
            entry = fdo.DesktopEntry.for_file(file)

            if entry.key_exists("Exec"):
                try:
                    entry.launch(0, None)
                except glib.GError, e:
                    print "Error when launching: %s" % e
        else:
            print "File not found (%s)" % desktop_path

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
        for dir in xdg_data_dirs:
            path = os.path.join(dir, "applications", desktop_name + ".desktop")
            file = vfs.File.for_path(path)

            if file is not None and file.exists():
                entry = fdo.DesktopEntry.for_file(file)

                item = self.append_menu_item(menu, entry.get_localestring("Name"), entry.get_icon(), entry.get_localestring("Comment"))
                item.connect("activate", self.launch_app, file.props.path)
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
            self.icon_theme.handler_block_by_func(self.theme_changed_cb)
            return self.icon_theme.load_icon(icon_name, 24, gtk.ICON_LOOKUP_FORCE_SIZE)
        except:
            for dir in xdg_data_dirs:
                for i in ("pixmaps", "icons"):
                    path = os.path.join(dir, i, icon_value)
                    if os.path.isfile(path):
                        return gtk.gdk.pixbuf_new_from_file_at_size(path, 24, 24)
        finally:
            self.icon_theme.handler_unblock_by_func(self.theme_changed_cb)

    class ClearRecentDocumentsDialog(awnlib.Dialogs.BaseDialog, gtk.MessageDialog):

        def __init__(self, parent, clear_cb):
            gtk.MessageDialog.__init__(self, type=gtk.MESSAGE_WARNING, message_format=_("Clear the Recent Documents list?"), buttons=gtk.BUTTONS_CANCEL)
            awnlib.Dialogs.BaseDialog.__init__(self, parent)

            self.set_skip_taskbar_hint(False)

            self.set_title(_("Clear Recent Documents"))
            self.format_secondary_markup(_("Clearing the Recent Documents list will clear the following:\n\
* All items from the Places > Recent Documents menu item.\n\
* All items from the recent documents list in all applications."))

            clear_button = gtk.Button(stock=gtk.STOCK_CLEAR)
            clear_button.set_image(gtk.image_new_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_MENU))
            def clear_and_hide(widget):
                self.response(gtk.RESPONSE_CANCEL)
                clear_cb()
            clear_button.connect("clicked", clear_and_hide)
            self.action_area.add(clear_button)

    class UnableToMountErrorDialog(awnlib.Dialogs.BaseDialog, gtk.MessageDialog):

        def __init__(self, parent, volume_name, error):
            gtk.MessageDialog.__init__(self, type=gtk.MESSAGE_ERROR, message_format=_("Unable to mount %s") % volume_name, buttons=gtk.BUTTONS_OK)
            awnlib.Dialogs.BaseDialog.__init__(self, parent)

            self.set_skip_taskbar_hint(True)

            self.format_secondary_markup(str(error))


if __name__ == "__main__":
    awnlib.init_start(YamaApplet, {"name": applet_name,
        "short": "yama",
        "version": __version__,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox",
        "copyright-year": "2009 - 2010",
        "authors": ["onox <denkpadje@gmail.com>"]},
        ["no-tooltip"])
