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

import commands
import os
import re
import subprocess

import pygtk
pygtk.require('2.0')
import gtk

from awn.extras import awnlib

import gio
from glib import filename_display_basename
import gmenu
from xdg import DesktopEntry

applet_name = "YAMA"
applet_version = "0.3.3"
applet_description = "Main menu with places and recent documents"

# Applet's themed icon, also shown in the GTK About dialog
applet_logo = "gnome-main-menu"

file_manager_apps = ("nautilus", "thunar", "xdg-open")

data_dirs = os.environ["XDG_DATA_DIRS"] if "XDG_DATA_DIRS" in os.environ else "/usr/local/share/:/usr/share/"

# Describes the pattern used to try to decode URLs
url_pattern = re.compile("^[a-z]+://(?:[^@]+@)?([^/]+)/(.*)$")

logout_command = "gnome-session-save --kill --silent"

# TODO handle updates in removed/new and included/excluded apps and bookmarks
# TODO add devices to places


class YamaApplet:

    """Applet to show Yet Another Menu Applet.

    """

    def __init__(self, applet):
        self.applet = applet

        self.setup_context_menu()

        self.menu = gtk.Menu()
        self.icon_theme = gtk.icon_theme_get_default()

        # Applications
        tree = gmenu.lookup_tree("applications.menu")
        self.append_directory(tree.root, self.menu)
        tree.add_monitor(self.applications_menu_changed_cb)
        # TODO remove monitor when destroy signal of menu is fired?

        self.menu.append(gtk.SeparatorMenuItem())

        # Places
        self.create_places_submenu(self.menu)

        # System
        tree = gmenu.lookup_tree("settings.menu")
        self.append_directory(tree.root, self.menu)
        tree.add_monitor(self.settings_menu_changed_cb)
        # TODO remove monitor when destroy signal of menu is fired?

        self.menu.append(gtk.SeparatorMenuItem())

        # TODO test wheter we can lock the screen and also try xscreensaver-command
        lock_item = self.append_menu_item(self.menu, "Lock Screen", "lock", "Protect your computer from unauthorized use")
        lock_item.connect("activate", self.start_subprocess_cb, "gnome-screensaver-command --lock", True)

        user_name = commands.getoutput("/usr/bin/whoami")
        logout_item = self.append_menu_item(self.menu, "Log Out %s..." % user_name, "application-exit", "Log out %s of this session to log in as a different user" % user_name)
        logout_dialog = self.LogoutDialog(self.applet, lambda: self.start_subprocess_cb(None, logout_command, True))
        def logout_cb(widget):
            logout_dialog.show_all()
            logout_dialog.deiconify()
        logout_item.connect("activate", logout_cb)

        self.menu.show_all()

        applet.connect("button-press-event", self.button_press_event_cb)

    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            def get_position(menu):
                icon_x, icon_y = self.applet.get_icon().window.get_origin()

                menu_size = self.menu.size_request()
                # Make sure the bottom of the menu doesn't get below the bottom of the screen
                icon_y = min(icon_y, self.menu.get_screen().get_height() - menu_size[1])

                padding = 6
                orientation = int(self.applet.get_orientation())
                if orientation == 2:
                    icon_y = self.menu.get_screen().get_height() - self.applet.get_size() - self.applet.props.offset - menu_size[1] - padding  # bottom
                elif orientation == 0:
                    icon_y = self.applet.get_size() + self.applet.props.offset + padding  # top
                elif orientation == 1:
                    icon_x = self.menu.get_screen().get_width() - self.applet.get_size() - self.applet.props.offset - menu_size[0] - padding  # right
                else:
                    icon_x = self.applet.get_size() + self.applet.props.offset + padding  # left

                return (icon_x, icon_y, False)
            self.menu.popup(None, None, get_position, event.button, event.time)

    def setup_context_menu(self):
        """Add "Edit Menus" to the context menu.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        edit_menus_item = gtk.MenuItem("_Edit Menus")
        edit_menus_item.connect("activate", self.start_subprocess_cb, "gmenu-simple-editor", False)
        menu.insert(edit_menus_item, menu_index)

        menu.insert(gtk.SeparatorMenuItem(), menu_index + 1)

    def applications_menu_changed_cb(self, tree):
        print "applications menu changed!"

    def settings_menu_changed_cb(self, tree):
        print "settings menu changed!"

    def start_subprocess_cb(self, widget, command, use_shell):
        try:
            subprocess.Popen(command, shell=use_shell)
        except OSError:
            pass

    def open_folder_cb(self, widget, path):
        for command in file_manager_apps:
            if len(commands.getoutput("%s %s" % (command, path))) == 0:
                return
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

        self.places_menu = menu
        self.bookmarks_items = []
        self.append_bookmarks()

        bookmarks_file = os.path.join(user_path, ".gtk-bookmarks")
        bookmarks_monitor = gio.File(bookmarks_file).monitor_file()
        def bookmarks_changed_cb(monitor, file, other_file, event):
            if event is gio.FileMonitorEvent.__enum_values__[0]:
                self.append_bookmarks()
        bookmarks_monitor.connect("changed", bookmarks_changed_cb)
        # FIXME boehoehoe doesn't seem to work atm :'( need glib.MainLoop().run()

        menu.append(gtk.SeparatorMenuItem())

        added = False
        added |= self.append_awn_desktop(menu, "nautilus-computer")
        added |= self.append_awn_desktop(menu, "nautilus-cd-burner")

        # TODO add devices here

        if added:
            menu.append(gtk.SeparatorMenuItem())

        added = False
        added |= self.append_awn_desktop(menu, "network-scheme")

        ncs_exists = os.path.exists(commands.getoutput("which nautilus-connect-server"))
        if ncs_exists:
            connect_item = self.append_menu_item(menu, "Connect to Server...", "stock_internet", "Connect to a remote computer or shared disk")
            connect_item.connect("activate", self.start_subprocess_cb, "nautilus-connect-server", False)
        added |= ncs_exists

        if added:
            menu.append(gtk.SeparatorMenuItem())

        self.append_awn_desktop(menu, "gnome-search-tool")

        # Recent Documents
        recent_manager = gtk.recent_manager_get_default()

        chooser_menu = gtk.RecentChooserMenu(recent_manager)
        recent_item = self.append_menu_item(menu, "Recent Documents", "document-open-recent", None)
        recent_item.set_submenu(chooser_menu)

        def set_sensitivity_recent_menu(widget):
            recent_item.set_sensitive(recent_manager.props.size > 0)
        recent_manager.connect("changed", set_sensitivity_recent_menu)
        set_sensitivity_recent_menu(None)

        def open_recent_document(widget):
            self.start_subprocess_cb(None, "xdg-open %s" % chooser_menu.get_current_uri(), True)
        chooser_menu.connect("item-activated", open_recent_document)

        chooser_menu.append(gtk.SeparatorMenuItem())
        item = self.append_menu_item(chooser_menu, "Clear Recent Documents", "gtk-clear", "Clear all items from the recent documents list")
        clear_dialog = self.ClearRecentDocumentsDialog(self.applet, recent_manager.purge_items)
        def purge_items_cb(widget):
            clear_dialog.show_all()
            clear_dialog.deiconify()
        item.connect("activate", purge_items_cb)

    def append_bookmarks(self):
        for item in self.bookmarks_items:
            item.destroy()
        self.bookmarks_items = []
        index = 2
        bookmarks_file = os.path.expanduser("~/.gtk-bookmarks")
        for url_name in (i.rstrip().split(" ", 1) for i in open(bookmarks_file)):
            if len(url_name) == 1:
                match = url_pattern.match(url_name[0])
                if match is not None:
                    url_name.append("/%s on %s" % (match.group(2), match.group(1)))
                else:
                    url_name.append(filename_display_basename(url_name[0]))
            url, name = (url_name[0], url_name[1])

            icon = "folder" if url.startswith("file://") else "folder-remote"
            display_url = url[7:] if url.startswith("file://") else url

            item = self.create_menu_item(name, icon, "Open '%s'" % display_url)
            self.places_menu.insert(item, index)
            item.connect("activate", self.open_folder_cb, url)
            index += 1
            self.bookmarks_items.append(item)

    def create_menu_item(self, label, icon_name, comment):
        item = gtk.ImageMenuItem(label)
        icon_pixbuf = self.get_pixbuf_icon(icon_name)
        item.set_image(gtk.image_new_from_pixbuf(icon_pixbuf))
        if comment is not None:
            item.set_tooltip_text(comment)
        return item

    def append_menu_item(self, menu, label, icon_name, comment):
        item = self.create_menu_item(label, icon_name, comment)
        menu.append(item)
        return item

    def launch_app(self, widget, path):
        if os.path.exists(path):
            self.start_subprocess_cb(None, DesktopEntry.DesktopEntry(path).getExec(), True)

    def append_directory(self, tree, menu):
        for node in tree.contents:
            if not isinstance(node, gmenu.Entry) and not isinstance(node, gmenu.Directory):
                continue
            # Don't set comment yet because we don't want it for submenu's
            item = self.append_menu_item(menu, node.name, node.icon, None)
            if isinstance(node, gmenu.Entry):
                item.set_tooltip_text(node.comment)
                item.connect("activate", self.launch_app, node.desktop_file_path)
            else:
                sub_menu = gtk.Menu()
                item.set_submenu(sub_menu)
                self.append_directory(node, sub_menu)

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
                return gtk.gdk.pixbuf_new_from_file_at_size(icon_value, 24, 24)
            icon_name = os.path.basename(icon_value)
        else:
            icon_name = icon_value

        if re.match(".*\.(png|xpm|svg)$", icon_name) is not None:
            icon_name = icon_name[:-4]
        try:
            return self.icon_theme.load_icon(icon_name, 24, 0)
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

    class LogoutDialog(awnlib.Dialogs.BaseDialog, gtk.MessageDialog):

        def __init__(self, parent, clear_cb):
            gtk.MessageDialog.__init__(self, type=gtk.MESSAGE_QUESTION, message_format="Log out of this system now?", buttons=gtk.BUTTONS_CANCEL)
            awnlib.Dialogs.BaseDialog.__init__(self, parent)

            self.set_image(gtk.image_new_from_stock(gtk.STOCK_QUIT, gtk.ICON_SIZE_DIALOG))
            user_name = commands.getoutput("/usr/bin/whoami")
            real_name = commands.getoutput("grep %s /etc/passwd" % user_name).split(":")[4].rstrip(",")
            name = "\"%s\"" % real_name if len(real_name) > 0 else user_name
            self.format_secondary_markup("You are currently logged in as %s.\nDo you want to log out?" % name)

            logout_button = gtk.Button("_Log Out")
            logout_button.connect("clicked", lambda w: clear_cb())
            self.action_area.add(logout_button)


if __name__ == "__main__":
    awnlib.init_start(YamaApplet, {"name": applet_name,
        "short": "yama",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox",
        "copyright-year": 2009,
        "authors": ["onox <denkpadje@gmail.com>"]},
        ["no-tooltip"])
