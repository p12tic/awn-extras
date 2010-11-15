#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2008 Moses Palmér
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


# Import standard modules
import gobject
import gtk
from desktopagnostic import config
import awn
import os
import sys
import tempfile
from xml.sax.saxutils import escape
from awn.extras import _, awnlib

# Import Comics! modules, but check dependencies first
awn.check_dependencies(globals(), 'feedparser', 'pynotify')
from pynotify import init as notify_init, Notification

import comics_manage
import comics_view
from feed.settings import Settings
from feed import FeedContainer
from shared import (
    ALT_USER_DIR, ICONS_DIR, STRIPS_DIR, SYS_FEEDS_DIR, UI_DIR,
    USER_DIR, USER_FEEDS_DIR)

APPLET_NAME = 'comics'
applet_display_name = _('Comics!')
applet_icon = os.path.join(ICONS_DIR, 'comics-icon.svg')


class BidirectionalIterator:

    def __init__(self, sequence):
        self.sequence = sequence
        self.index = None
        self.direction = 1

    def set_direction(self, direction):
        if direction < 0:
            self.direction = -1
        elif direction > 0:
            self.direction = 1
        else:
            self.direction = None
            self.index = None

    def next(self):
        if not self.sequence or self.direction is None:
            return None
        if self.index is None:
            if self.direction > 0:
                self.index = 0
            else:
                self.index = len(self.sequence) - 1
        else:
            self.index += self.direction
            if self.index < 0:
                self.index = len(self.sequence)
                return None
            elif self.index >= len(self.sequence):
                self.index = -1
                return None
        return self.sequence[self.index]


class ComicApplet(awn.AppletSimple):
    DIALOG_DURATION = 3000

    def set_visibility(self, visible):
        """Show or hide the comic windows."""
        self.visible = visible

        for window in self.windows:
            window.set_visibility(visible)

        if visible:
            self.current_window = None

    def show_next(self):
        if self.current_window:
            self.current_window.set_visibility(False)
        self.current_window = self.window_iterator.next()
        if self.current_window:
            self.current_window.set_visibility(True)

    def create_window(self, filename=None, template=None):
        """Creates a new strip and stores its configuration in the directory
        path."""
        if filename is None:
            f, filename = tempfile.mkstemp('.strip', '', STRIPS_DIR, True)
            os.close(f)
        settings = Settings(filename)
        if template:
            settings.update(template)
        settings['cache-file'] = filename.rsplit('.', 1)[0] + '.cache'
        window = comics_view.ComicsViewer(self, settings, self.visible)
        self.windows.append(window)
        window.connect('removed', self.on_window_removed)
        window.connect('updated', self.on_window_updated)
        settings.save()

    def toggle_feed(self, feed_name, visible):
        """Toggles a comic."""
        if feed_name not in self.feeds.feeds:
            return

        if not visible:
            windows = [w for w in self.windows if w.feed_name == feed_name]
            if not windows:
                return

            for window in windows:
                window.close()
                window.destroy()

        else:
            template = Settings()
            template['feed_name'] = feed_name
            self.create_window(template=template)

    def make_menu(self):
        """Generate the menu listing the comics."""
        # Generate comics menu
        menu = self.create_default_menu()
        feed_menu = gtk.Menu()
        names = self.feeds.feeds.keys()
        names.sort(key=str.lower)
        for feed in names:
            label = gtk.Label()
            # Gtk wants '&' and '<' to be escaped
            # this escapes '&', '<' and '>'
            label.set_markup(escape(feed))
            align = gtk.Alignment(xalign=0.0)
            align.add(label)
            menu_item = gtk.CheckMenuItem()
            menu_item.data = feed
            menu_item.add(align)
            menu_item.set_active(len([w for w in self.windows
                                      if w.feed_name == feed]) > 0)
            menu_item.connect('toggled', self.on_comics_toggled)
            feed_menu.append(menu_item)
        feed_menu.show_all()
        container = gtk.MenuItem(_('Comics'))
        container.set_sensitive(len(self.feeds.feeds) > 0)
        container.set_submenu(feed_menu)
        menu.append(container)
        manage_item = gtk.MenuItem(_('Manage Comics'))
        manage_item.connect("activate", self.on_manage_comics_activated)
        menu.append(manage_item)
        about_item = gtk.ImageMenuItem(_("_About %s") % applet_display_name)
        if awnlib.is_required_version(gtk.gtk_version, (2, 16, 0)):
            about_item.props.always_show_image = True
        about_item.set_image(gtk.image_new_from_stock(gtk.STOCK_ABOUT,
                                                      gtk.ICON_SIZE_MENU))
        menu.append(about_item)
        about_item.connect("activate", self.on_show_about_activated)
        menu.show_all()
        return menu

    def show_message(self, message, icon_id):
        self.message_label.set_markup(message)
        self.message_icon.set_from_stock(icon_id, gtk.ICON_SIZE_DIALOG)
        self.dialog.show_all()
        gobject.timeout_add(self.DIALOG_DURATION, self.on_dialog_timer)

    def __init__(self, uid, panel_id, feeds):
        super(awn.AppletSimple, self).__init__(APPLET_NAME, uid, panel_id)

        self.feeds = feeds
        self.configuration = awn.config_get_default_for_applet(self)

        self.set_icon_name('comics-icon')
        # Initialise notifications
        notify_init(applet_display_name)
        self.dialog = awn.Dialog(self)
        self.dialog.connect('button-release-event',
                            self.on_dialog_button_press)

        hbox = gtk.HBox(False)
        self.message_icon = gtk.Image()
        self.message_label = gtk.Label()
        hbox.pack_start(self.message_icon, expand=False, fill=False)
        hbox.pack_end(self.message_label)
        hbox.show_all()
        self.dialog.add(hbox)

        self.connect('destroy', self.on_destroy)
        self.connect('button-press-event', self.on_button_press)
        self.connect('scroll-event', self.on_scroll)

        self.visible = False
        self.windows = []
        self.window_iterator = BidirectionalIterator(self.windows)
        self.current_window = None

        try:
            for filename in (f for f in os.listdir(STRIPS_DIR)
                             if f.endswith('.strip')):
                strip = self.create_window(os.path.join(STRIPS_DIR, filename))
        except OSError:
            return

        self.feeds.update()

    def on_window_updated(self, widget, title):
        msg = Notification(_('There is a new strip of %s!') % widget.feed_name,
                           None, applet_icon)
        msg.show()

    def on_window_removed(self, widget):
        self.windows.remove(widget)

    def on_destroy(self, widget):
        for window in self.windows:
            window.save_settings()

    def on_button1_pressed(self, event):
        self.set_visibility(not self.visible)

    def on_button3_pressed(self, event):
        menu = self.make_menu()
        if menu:
            self.popup_gtk_menu(menu, event.button, event.time)

    def on_button_press(self, widget, event):
        if event.button == 1:
            self.on_button1_pressed(event)
        elif event.button == 3:
            self.on_button3_pressed(event)
        return True

    def on_scroll(self, widget, event):
        if self.visible:
            return
        if event.direction == gtk.gdk.SCROLL_UP:
            self.window_iterator.set_direction(-1)
            self.show_next()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.window_iterator.set_direction(1)
            self.show_next()

    def on_dialog_button_press(self, widget, event):
        self.dialog.hide()

    def on_dialog_timer(self):
        self.dialog.hide()

    def on_comics_toggled(self, widget):
        self.toggle_feed(widget.data, widget.get_active())

    def on_manage_comics_activated(self, widget):
        manager = comics_manage.ComicsManager(self)
        manager.show()

    def on_show_about_activated(self, widget):
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(applet_icon, 48, 48)

        win = gtk.AboutDialog()
        win.set_name(applet_display_name)
        win.set_copyright('Copyright \xc2\xa9 2008 Moses Palmér')
        win.set_authors(['Moses Palmér',
                         'Sharkbaitbobby',
                         'Mark Lee',
                         'Kyle L. Huff',
                         'Gabor Karsay'])
        win.set_artists(['Moses Palmér'])
        win.set_comments(_("View your favourite comics on your desktop"))
        win.set_license("This program is free software; you can redistribute it " +\
            "and/or modify it under the terms of the GNU General Public License " +\
            "as published by the Free Software Foundation; either version 2 of " +\
            "the License, or (at your option) any later version.\n\nThis program is " +\
            "distributed in the hope that it will be useful, but WITHOUT ANY " +\
            "WARRANTY; without even the implied warranty of MERCHANTABILITY or " +\
            "FITNESS FOR A PARTICULAR PURPOSE.    See the GNU General Public " +\
            "License for more details.\n\nYou should have received a copy of the GNU " +\
            "General Public License along with this program; if not, write to the " +\
            "Free Software Foundation, Inc., " +\
            "51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.")
        win.set_wrap_license(True)
        win.set_logo(pixbuf)
        win.set_icon_from_file(applet_icon)
        win.set_version(awn.extras.__version__)
        win.run()
        win.destroy()

if __name__ == '__main__':
    # Initialise threading
    gobject.threads_init()
    gtk.gdk.threads_init()
    # Make sure that all required directories exist
    if not os.access(USER_DIR, os.W_OK):
        if os.access(ALT_USER_DIR, os.W_OK):
            os.symlink(ALT_USER_DIR, USER_DIR)
        else:
            os.makedirs(USER_DIR)
    if not os.access(USER_FEEDS_DIR, os.W_OK):
        os.makedirs(USER_FEEDS_DIR)

    # Load the feeds
    feeds = FeedContainer()
    feeds.load_directory(SYS_FEEDS_DIR)
    feeds.load_directory(USER_FEEDS_DIR)

    #Initialise AWN and create the applet
    awn.init(sys.argv[1:])
    applet = ComicApplet(awn.uid, awn.panel_id, feeds)

    # Initialize user agent string
    import urllib

    user_agent = applet.configuration.get_string(config.GROUP_DEFAULT,
                                                 'user_agent')

    class ComicURLOpener(urllib.FancyURLopener):
        version = user_agent
    urllib._urlopener = ComicURLOpener()

    # Run
    awn.embed_applet(applet)
    applet.show_all()

    gtk.main()
