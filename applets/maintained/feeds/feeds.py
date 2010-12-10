#! /usr/bin/python
#
# Copyright (c) 2009, 2010 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from __future__ import with_statement

import sys
import os
import urllib2
import socket
from xml.dom import minidom
import time

import pygtk
pygtk.require('2.0')
import gtk
import pango
import gobject
import gettext

from desktopagnostic.config import GROUP_DEFAULT
import awn
from awn.extras import _, awnlib, __version__, APPLET_BASEDIR
from awn.extras.threadqueue import ThreadQueue, async_method

awn.check_dependencies(globals(), 'feedparser', 'pynotify', json=('json', 'simplejson'))

import classes

socket.setdefaulttimeout(30)

icondir = os.path.join(APPLET_BASEDIR, 'feeds', 'icons')

icon_path = os.path.join(icondir, 'awn-feeds.svg')

greader_path = os.path.join(icondir, 'awn-feeds-greader.svg')

config_dir = os.environ['HOME'] + '/.config/awn/applets'
config_path = os.path.join(config_dir, 'feeds.txt')

cache_dir = os.environ['HOME'] + '/.cache/awn-feeds-applet'
cache_index = os.path.join(cache_dir, 'index.txt')

user_agent = 'AwnFeedsApplet/' + __version__

override_icons = {'google-reader': 'http://www.google.com/reader/ui/favicon.ico',
    'twitter.com': icondir + '/' + 'twitter-16x16.png'}

gtk.gdk.threads_init()

if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

if not os.path.exists(config_dir):
    os.makedirs(config_dir)


class App(awn.AppletSimple):
    displays = {}
    toggles = []
    feeds = {}
    feed_icons = {}
    pixbufs = {}
    timer = 0
    finished_feeds = 0
    menu = None
    keyring = None
    dragged_toggle = None
    prefs_dialog = None
    show_only_new_check = None
    urls = []
    written_urls = []
    num_notify_while_updating = 0
    google_logins = {}

    def __init__(self, uid, panel_id):
        self.network_handler = self.NetworkHandler()
        self.tokens = classes.Tokens()
        self.favicons = classes.Tokens(cache_index)

        #AWN Applet Configuration
        awn.AppletSimple.__init__(self, 'feeds', uid, panel_id)
        self.set_tooltip_text(_("Loading feeds..."))
        self.dialog = awn.Dialog(self)

        self.main_vbox = gtk.VBox(False, False)
        self.dialog.add(self.main_vbox)
        self.main_vbox.show()

        #Need icon theme
        self.icon_theme = gtk.icon_theme_get_default()
        self.icon_theme.connect('changed', self.icon_theme_changed)

        #Get a 16x16 icon representing the Internet/web
        self.web_image = self.icon_theme.load_icon('applications-internet', 16, 0)

        #Force a size of 16x16
        if self.web_image.get_width() != 16 or self.web_image.get_height() != 16:
            self.web_image = self.web_image.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)

        #Throbber overlay
        self.throbber = awn.OverlayThrobber()
        self.throbber.props.gravity = gtk.gdk.GRAVITY_SOUTH_WEST

        #Error icon overlay
        self.error_icon = awn.OverlayThemedIcon("gtk-dialog-error")
        self.error_icon.props.gravity = gtk.gdk.GRAVITY_SOUTH_WEST

        #First updated feed favicon (bottom right)
        self.favicon1 = awn.OverlayPixbuf(self.web_image)
        self.favicon1.props.gravity = gtk.gdk.GRAVITY_SOUTH_EAST

        #Second updated feed favicon (bottom)
        self.favicon2 = awn.OverlayPixbuf(self.web_image)
        self.favicon2.props.gravity = gtk.gdk.GRAVITY_SOUTH

        #Third updated feed favicon (right)
        self.favicon3 = awn.OverlayPixbuf(self.web_image)
        self.favicon3.props.gravity = gtk.gdk.GRAVITY_EAST

        for overlay in (self.throbber, self.error_icon, self.favicon1, self.favicon2, self.favicon3):
            if self.get_size() > 48:
                overlay.props.scale = 16.0 / self.get_size()
            else:
                overlay.props.scale = 0.33
            overlay.props.apply_effects = True
            overlay.props.active = False
            self.add_overlay(overlay)

        #Magic at work. Position the 2nd and 3rd favicons adjacent to the icon
        if self.get_size() > 48:
            self.favicon2.props.x_adj = 0.5 - 24.0 / self.get_size()
            self.favicon3.props.y_adj = 0.5 - 24.0 / self.get_size()

        else:
            self.favicon2.props.x_adj = 0.0
            self.favicon3.props.y_adj = 0.0

        #"Loading feeds..." label
        self.loading_feeds = gtk.Label(_("Loading feeds..."))
        self.loading_feeds.modify_font(pango.FontDescription('bold'))
        self.main_vbox.pack_start(self.loading_feeds, False, False, 3)
        self.loading_feeds.show()
        self.loading_feeds.set_no_show_all(True)

        #No feeds label
        self.no_feeds = gtk.Label(_("You don't have any feeds."))
        self.main_vbox.pack_start(self.no_feeds)
        self.no_feeds.set_no_show_all(True)

        #AwnConfigClient instance
        self.client = awn.config_get_default_for_applet(self)

        #Connect to signals
        self.connect('button-release-event', self.button_release)
        self.dialog.props.hide_on_unfocus = True

        self.get_urls()

        #TODO: put this and the similar code in add_feed() into a single, better place
        for url in self.urls:
            _base_url = '-'.join(url.split('-')[:-1])
            username = url.split('-')[-1]

            if _base_url == 'google-reader':
                self.feeds[url] = classes.GoogleReader(self, username)

            elif _base_url == 'google-wave':
                self.feeds[url] = classes.GoogleWave(self, username)

            elif _base_url == 'reddit':
                self.feeds[url] = classes.Reddit(self, username)

            elif _base_url in ('twitter-timeline', 'twitter-both', 'twitter-replies'):
                self.feeds[url] = classes.Twitter(self, username, None, base_url=_base_url)

            else:
                self.feeds[url] = classes.WebFeed(self, url)

        #Set the icon
        only_greader = bool(len(self.urls))
        for feed in self.feeds.values():
            if not isinstance(feed, classes.GoogleReader):
                only_greader = False
                break

        self.set_icon_name(['awn-feeds', 'awn-feeds-greader'][only_greader])

        self.setup_dialog()

        #Allow user to drag and drop feed URLs onto the applet icon
        #E.g. In a browser, user drags and drops a link to an Atom feed onto the applet
        self.get_icon().drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
          [("STRING", 0, 0), ("text/plain", 0, 0), ("text/uri-list", 0, 0)], \
          gtk.gdk.ACTION_COPY)
        self.get_icon().connect('drag_data_received', self.applet_drag_data_received)
        self.get_icon().connect('drag-motion', self.applet_drag_motion)
        self.get_icon().connect('drag-leave', self.applet_drag_leave)
        self.dialog.connect('scroll-event', self.scroll)
        self.connect('size-changed', self.size_changed)

        #Set up the D-Bus service
        self.service = classes.DBusService(self)

        self.update_feeds()

    #Tell each feed object to update
    def update_feeds(self, *args):
        self.error_icon.props.active = False

        if len(self.urls) != 0:
            self.throbber.props.active = True
            self.finished_feeds = 0
            self.started_updating = 0
            self.num_notify_while_updating = 0
            self.loading_feeds.show()
            self.set_tooltip_text(_("Loading feeds..."))

            for url in self.urls:
                self.feed_throbbers[url].props.active = True

            self.update_timer = gobject.timeout_add(250, self.update_next_feed)

            self.do_timer()

        else:
            self.loading_feeds.hide()
            self.set_tooltip_text(_("Feeds Applet"))
            self.no_feeds.show()#Just in case

        return False

    #250ms before starting updating each feed to ease the load a bit
    def update_next_feed(self):
        try:
            feed = self.feeds[self.urls[self.started_updating]]
        except:
            pass
        else:
            feed.num_new = 0
            feed.num_notify = 0
            feed.io_error = False

            feed.update()

            self.started_updating += 1
            self.update_timer = gobject.timeout_add(250, self.update_next_feed)

        return False

    #Set the timeout to automatically update
    def do_timer(self):
        if self.timer:
            gobject.source_remove(self.timer)

        #Update the feeds automatically
        if self.client.get_value(GROUP_DEFAULT, 'auto_update'):
            interval = self.client.get_value(GROUP_DEFAULT, 'update_interval')

            #Range of 3 to 60
            if interval < 3:
                interval = 3

            elif interval > 60:
                interval = 60

            self.timer = gobject.timeout_add_seconds(interval * 60, self.update_feeds)

    def got_favicon(self, feed, override=False, no_do_favicons=False):
        icon = [feed.icon, 'gtk://gtk-dialog-error'][feed.io_error]

        if override or self.client.get_value(GROUP_DEFAULT, 'show_favicons'):
            icon = [feed.icon, 'gtk://gtk-dialog-error'][feed.io_error]

            try:
                pb = self.get_favicon(icon)

                if feed.url in self.feed_icons:
                    self.feed_icons[feed.url].set_from_pixbuf(pb)

                #On startup, all feeds could be updated, and certain ones may have new items,
                #(e.g. Reddit, which recognizes unread items as new) though the favicon is not yet
                #loaded.
                if not no_do_favicons and feed.url in self.feeds:
                    self.do_favicons()

            except:
                pass

        if self.prefs_dialog and feed.url in self.feeds:
            self.prefs_dialog.update_liststore()

    #Download the favicon if it hasn't been downloaded OR is more than a week old
    def fetch_favicon(self, cb, data, siteid, url=None, error_callback=None):
        if siteid in override_icons:
            url = override_icons[siteid]

        elif url is None:
            url = 'http://%s/favicon.ico' % siteid

        #Twitter's favicon is ugly, so override it with an included one
        #(This is the icon that the Twitter feed source uses)
        if siteid == 'twitter.com':
            return

        if siteid in self.favicons:
            #Check if the favion is less than a week old
            if self.favicons[siteid] + 604800L > long(time.time()):
                return

        #Fetch the icon
        self.network_handler.get_data(url, callback=cb, error=error_callback, user_data=data)

    def get_favicon(self, icon, override=False):
        if icon is None:
            return self.web_image

        if not override and not self.client.get_value(GROUP_DEFAULT, 'show_favicons'):
            return self.web_image

        if icon in self.pixbufs:
            return self.pixbufs[icon]

        if icon.find('/') != 0 and icon.find('file:///') != 0:
            path = cache_dir + '/' + icon + '.ico'

        else:
            path = icon

        if icon in override_icons:
            if override_icons[icon][0] == '/':
                path = override_icons[icon]

        try:
            if icon.find('gtk://') == 0:
                pb = self.icon_theme.load_icon(icon[6:], 16, 0)
                pb = classes.get_16x16(pb)

            else:
                pb = gtk.gdk.pixbuf_new_from_file_at_size(path, 16, 16)

        except:
            pb = self.web_image

        if pb != self.web_image:
            self.pixbufs[icon] = pb

        return pb

    def feed_updated(self, feed):
        self.num_notify_while_updating += feed.num_notify

        if feed.url in self.displays:
            self.feed_throbbers[feed.url].props.active = False

            for widget in self.displays[feed.url].get_children():
                widget.destroy()

            for i, entry in enumerate(feed.entries[:5]):
                image = gtk.Image()

                button = gtk.Button('')
                button.child.set_text(classes.safify(shortify(entry['title'])))
                button.child.set_use_underline(False)
                button.set_relief(gtk.RELIEF_NONE)
                if len(entry['title']) > 25:
                    button.set_tooltip_text(classes.safify(entry['title']))
                button.connect('clicked', self.feed_item_clicked, (feed, i))
                button.show_all()

                if entry['new'] == True:
                    classes.boldify(button, True)

                self.displays[feed.url].pack_start(button, False)

            feed_title = [feed.title, _("Error")][feed.io_error]

            self.feed_labels[feed.url].set_text(shortify(feed_title))

            if feed.num_new > 0:
                classes.boldify(self.feed_labels[feed.url])

            #If all the feeds have been updated...
            self.finished_feeds += 1
            if len(self.urls) == self.finished_feeds:
                self.all_feeds_updated()

        if self.prefs_dialog:
            self.prefs_dialog.update_liststore()

        self.show_only_new(feed.url)

    def all_feeds_updated(self):
        self.set_tooltip_text(_("Feeds Applet"))
        self.loading_feeds.hide()

        self.throbber.props.active = False

        self.error_icon.props.active = False
        for feed in self.feeds.values():
            if feed.io_error:
                self.error_icon.props.active = True

        self.show_notification()

        self.do_favicons()

        self.show_only_new()

    def do_favicons(self, override=False):
        for icon in [self.error_icon, self.favicon1, self.favicon2, self.favicon3]:
            icon.props.active = False

        if not override:
            if not self.client.get_value(GROUP_DEFAULT, 'show_favicons'):
                return

        num_icons_shown = 0
        for url in self.urls:
            if num_icons_shown < 3:
                feed = self.feeds[url]
                if not feed.io_error and feed.num_new > 0:
                    icon = [self.favicon1, self.favicon2, self.favicon3][num_icons_shown]
                    icon.props.active = True

                    try:
                        icon.props.pixbuf = self.get_favicon(feed.icon)
                        num_icons_shown += 1

                    except:
                        pass

                elif feed.io_error:
                    self.error_icon.props.active = False

    def show_notification(self):
        if not self.client.get_value(GROUP_DEFAULT, 'notify'):
            return

        msg = ''
        only_greader = True
        num_messages = 0
        if self.num_notify_while_updating != 0:
            for url, feed in self.feeds.items():
                if not isinstance(feed, classes.GoogleReader):
                    if feed.num_notify > 0:
                        only_greader = False

                notify_entries = []
                for entry in feed.entries:
                    if entry['notify'] == True:
                        notify_entries.append(entry)
                        num_messages += 1

                if len(notify_entries) == 0:
                    continue

                if feed.num_notify == 1:
                    msg += "%s\n  <a href=\"%s\">%s</a>\n" % (shortify(feed.title),
                        notify_entries[0]['url'], shortify(notify_entries[0]['title']))

                elif feed.num_notify == 2:
                    msg += "%s\n  <a href='%s'>%s</a>\n  <a href='%s'>%s</a>\n" % \
                        (shortify(feed.title),
                        notify_entries[0]['url'], shortify(notify_entries[0]['title']),
                        notify_entries[1]['url'], shortify(notify_entries[1]['title']))

                elif feed.num_notify > 2:
                    msg += _("%s\n  <a href='%s'>%s</a>\n  <a href='%s'>%s</a>\n(%s More)\n") % \
                        (shortify(feed.title),
                        notify_entries[0]['url'], shortify(notify_entries[0]['title']),
                        notify_entries[1]['url'], shortify(notify_entries[1]['title']),
                        (feed.num_notify - 2))

                feed.num_notify = 0

            if num_messages != 0:
                pynotify.init(_("Feeds Applet"))
                s = gettext.ngettext("%s New Item - Feeds Applet", "%s New Items - Feeds Applet",
                  self.num_notify_while_updating) % self.num_notify_while_updating
                notification = pynotify.Notification(s, msg,
                  [icon_path, greader_path][only_greader])
                notification.set_timeout(5000)
                notification.show()

    #Set up initial widgets, frame for each feed
    def setup_dialog(self):
        self.feed_labels = {}
        self.feed_icons = {}
        self.feed_throbbers = {}
        self.feed_toggles = {}

        self.toggles = []

        self.widget = gtk.VBox(False, 6)

        #This is mainly for reordering of the feeds in the dialog
        #(The only way to get the drag-motion signal on a widget is
        #for the widget to be a drag destination)
        self.widget.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
          [('STRING', 0, 0), ('text/plain', 0, 0), ('text/uri-list', 0, 0)], \
          gtk.gdk.ACTION_COPY)
        self.widget.connect('drag-data-received', self.dialog_drag_received)
        self.widget.connect('drag-motion', self.dialog_drag_motion)
        self.widget.connect('drag-leave', self.dialog_drag_leave)

        #User has no feeds
        if len(self.urls) == 0:
            self.no_feeds.show()

        #User has feeds
        else:
            for i, url in enumerate(self.urls):
                self.add_feed_row(url, i)

        #+Add Feed button
        button = gtk.Button(_("_Add Feed"))
        image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
        button.set_image(image)
        button.connect('clicked', self.add_feed_dialog)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(button, True, False)

        self.widget.pack_end(hbox, False)

        self.widget.show_all()

        self.main_vbox.pack_end(self.widget, False, False, 0)

    #Setup the widgets for the feed
    def add_feed_row(self, url, i):
        feed_vbox = gtk.VBox(False, 6)
        feed_items_vbox = gtk.VBox(False, 6)
        self.displays[url] = feed_items_vbox
        feed_items_vbox.set_no_show_all(True)

        feed_hbox = gtk.HBox(False, 6)
        feed_vbox.pack_start(feed_hbox, False)
        feed_vbox.pack_start(feed_items_vbox, False)
        self.widget.pack_start(feed_vbox)

        #Get the icon as a pixbuf
        pb = None
        if self.feeds[url].icon != '' and self.client.get_value(GROUP_DEFAULT, 'show_favicons'):
            pb = self.get_favicon(self.feeds[url].icon)

        else:
            pb = self.web_image

        #Pretty icon for button
        image = awn.Image()
        image.set_size_request(16, 16)
        image.set_from_pixbuf(pb)
        throbber = awn.OverlayThrobber()
        throbber.props.active = True
        throbber.props.scale = 1.0
        image.add_overlay(throbber)
        self.feed_icons[url] = image
        self.feed_throbbers[url] = throbber

        #Button for opening the feed's website
        button = gtk.Button()
        button.add(image)
        button.set_relief(gtk.RELIEF_NONE)
        button.set_tooltip_text(_("Open this feed's website"))
        button.connect('clicked', self.feed_icon_clicked, url)
        button.show_all()

        feed_hbox.pack_start(button, False)

        #ToggleButton for showing/hiding the feed's items
        arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)

        label = gtk.Label(_("Loading..."))
        self.feed_labels[url] = label

        toggle_hbox = gtk.HBox(False, 3)
        toggle_hbox.pack_start(arrow, False)
        toggle_hbox.pack_start(label, False)

        toggle = gtk.ToggleButton()
        toggle.add(toggle_hbox)
        toggle.set_relief(gtk.RELIEF_NONE)
        toggle.connect('toggled', self.toggle_display, url)
        toggle.url = url
        self.toggles.append(toggle)
        self.feed_toggles[url] = toggle

        toggle.arrow = arrow
        toggle.web_url = ''
        toggle.url = url
        toggle.web = button
        toggle.position = i
        toggle.placeholder = None
        toggle.size_group = None

        #Drag and Drop to reorder
        #or drop an e.g. a web browser to go to that feed's url
        toggle.drag_source_set(gtk.gdk.BUTTON1_MASK, \
          [("text/plain", 0, 0), ("STRING", 0, 0)], \
          gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE)
        toggle.connect('drag-begin', self.toggle_drag_begin)
        toggle.connect('drag-data-get', self.toggle_drag_get)
        toggle.connect('drag-end', self.toggle_drag_end)

        #If there's only one feed, show its most recent items
        if len(self.urls) == 1:
            toggle.set_active(True)

        #Not showing, set appropriate tooltip text
        else:
            toggle.set_tooltip_text(_("Show this feed's items"))

        feed_hbox.pack_start(toggle)

    #Toggle buttons drag and drop
    def toggle_drag_begin(self, toggle, context):
        toggle.set_active(False)

        #Literally drag the toggle around!
        #(Since Gtk 2.14)
        try:
            toggle.drag_source_set_icon(toggle.get_screen().get_rgba_colormap(), \
              toggle.parent.get_snapshot(), None)

        except:
            pass

        if len(self.toggles) > 1:
            for other_toggle in self.toggles:
                if other_toggle != toggle:
                    break

            toggle.hide()
            toggle.web.hide()
            toggle.placeholder = classes.PlaceHolder()
            toggle.size_group = gtk.SizeGroup(gtk.SIZE_GROUP_BOTH)
            toggle.size_group.add_widget(other_toggle.parent)
            toggle.size_group.add_widget(toggle.placeholder)
            toggle.parent.pack_start(toggle.placeholder)
            toggle.placeholder.show()

            self.dragged_toggle = toggle

    #When the toggle is dragged onto something
    def toggle_drag_get(self, toggle, context, data, info, time):
        data.set(data.target, 8, self.feeds[toggle.url].web_url)

    #When the toggle dragging is done
    def toggle_drag_end(self, toggle, context):
        if toggle.placeholder:
            toggle.placeholder.destroy()
        if toggle.size_group:
            del toggle.size_group
        toggle.show()
        toggle.web.show()
        self.dragged_toggle = None

        #Save in case the feeds were reordered
        urls = ''
        self.urls = []
        new_toggles = []
        children = toggle.parent.parent.parent.get_children()
        for vbox in children[:-1]:
            hbox = vbox.get_children()[0]
            urls += hbox.get_children()[1].url + '\n'
            self.urls.append(hbox.get_children()[1].url)
            new_toggles.append(hbox.get_children()[1])

        self.toggles = new_toggles

        #Remove the last newline
        urls = urls[:-1]

        fp = open(config_path, 'w+')
        fp.write(urls)
        fp.close()

        if self.prefs_dialog:
            self.prefs_dialog.update_liststore()
        self.do_favicons()

    def dialog_drag_received(self, *args):
        pass

    def dialog_drag_motion(self, widget, context, x, y, time):
        if self.dragged_toggle is not None:
            toggles_xywh = {}
            for i, toggle in enumerate(self.toggles):
                if toggle != self.dragged_toggle:
                    a = toggle.parent.allocation
                    children = toggle.parent.parent.parent.get_children()
                    toggle.drag_pos = children.index(toggle.parent.parent)
                    toggles_xywh[i] = {'x': a.x, 'y': a.y, 'w': a.width, 'h': a.height, 't': toggle}

            for coord in toggles_xywh.values():
                if x >= coord['x'] and y >= coord['y']:
                    if x <= (coord['x'] + coord['w']):
                        if y <= (coord['y'] + coord['h']):
                            pos = coord['t'].drag_pos
                            vbox = self.dragged_toggle.parent.parent.parent
                            vbox.reorder_child(self.dragged_toggle.parent.parent, pos)

                            break

        return False

    def dialog_drag_leave(self, widget, context, time):
        return True

    #Applet drag and drop
    def applet_drag_data_received(self, w, context, x, y, data, info, time):
        if data and data.format == 8 and self.dragged_toggle is None:
            context.finish(True, False, time)

            url = data.data.strip()

            #The file was downloaded
            def got_file(selfurl, content):
                self, url = selfurl

                #The file was parsed
                def got_parsed(user_data, parsed):
                    self, url, original = user_data
                    if not parsed['bozo'] and len(parsed['entries']) > 0:
                        self.add_feed(url, parsed)

                    else:
                        opml = parse_opml(original, self.urls)

                        if len(opml) != 0:
                            self.add_opml_dialog(opml)

                #Feedparser can cause a short delay, so thread it
                self.network_handler.run_feedparser(content, user_data=(self, url, content), \
                    callback=got_parsed)

                #Otherwise, nothing will be done.

            if url not in self.urls:
                self.network_handler.get_data(url, user_data=(self, url), callback=got_file)

        else:
            context.finish(False, False, time)

    def applet_drag_motion(self, widget, context, x, y, time):
        if self.dragged_toggle is None:
            self.get_effects().start(awn.EFFECT_LAUNCHING)

        return True

    def applet_drag_leave(self, widget, context, time):
        self.get_effects().stop(awn.EFFECT_LAUNCHING)

        return True

    #Toggle the showing of a feed's most recent items
    def toggle_display(self, toggle, url):
        if toggle.get_active():
            self.displays[url].show()
            toggle.set_tooltip_text(_("Hide this feed's items"))
            toggle.arrow.set(gtk.ARROW_DOWN, gtk.SHADOW_NONE)

            #Only show one feed at a time
            for other_toggle in self.toggles:
                if other_toggle != toggle:
                    other_toggle.set_active(False)

        else:
            self.displays[url].hide()
            toggle.set_tooltip_text(_("Show this feed's items"))
            toggle.arrow.set(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)

    def scroll(self, widget, event):
        open_toggle = None
        for toggle in self.toggles:
            if toggle.get_active():
                open_toggle = toggle
                break

        if open_toggle is None:
            return False

        show_only_new = self.client.get_value(GROUP_DEFAULT, 'show_only_new')

        toggle_index = self.toggles.index(open_toggle)
        if event.direction in (gtk.gdk.SCROLL_UP, gtk.gdk.SCROLL_LEFT):
            if show_only_new:
                while toggle_index != 0:
                    if self.feeds[self.urls[toggle_index - 1]].num_new != 0:
                        self.toggles[toggle_index - 1].set_active(True)
                        break

                    else:
                        toggle_index -= 1

            else:
                if toggle_index != 0:
                    self.toggles[toggle_index - 1].set_active(True)

        else:
            if show_only_new:
                while toggle_index + 1 != len(self.toggles):
                    if self.feeds[self.urls[toggle_index + 1]].num_new != 0:
                        self.toggles[toggle_index + 1].set_active(True)
                        break

                    else:
                        toggle_index += 1

            else:
                if open_toggle != self.toggles[-1]:
                    self.toggles[toggle_index + 1].set_active(True)

        return False

    #Show the Add Feed dialog
    def add_feed_dialog(self, widget):
        import prefs
        self.addfeed = prefs.AddFeed(applet=self)

    def feed_icon_clicked(self, button, feedurl):
        self.open_url(None, self.feeds[feedurl].web_url)

        self.feeds[feedurl].icon_clicked()

    def feed_item_clicked(self, button, data):
        feed, i = data

        if isinstance(feed, classes.StandardNew):
            if feed.entries[i]['new']:
                #Deboldify the button
                classes.deboldify(self.displays[feed.url].get_children()[i], True)
                feed.num_new -= 1

                if feed.num_new == 0:
                    classes.deboldify(self.feed_labels[feed.url])

                    self.show_only_new(feed.url)

        self.open_url(None, feed.entries[i]['url'])

        feed.item_clicked(i)

        if isinstance(feed, classes.StandardNew):
            if feed.entries[i].basic() in feed.last_new:
                feed.last_new.remove(feed.entries[i].basic())

        if feed.num_new == 0:
            self.do_favicons()

    #Open a URL
    def open_url(self, widget, url):
        if url.strip() != '':
            try:
                gtk.show_uri(None, url, gtk.get_current_event_time())

            #For GTK < 2.14
            except:
                os.system('xdg-open "%s" &' % url)

    #Remove a feed
    def remove_feed(self, url):
        #Remove the url from the text file...
        fp = open(config_path, 'r')
        f = fp.read()
        fp.close()

        newtext = ''
        for line in f.split('\n'):
            if line not in ('', url):
                newtext += line + '\n'

        fp = open(config_path, 'w')
        fp.write(newtext)
        fp.close()

        #User is removing the last feed
        if len(self.feeds.keys()) == 1:
            self.no_feeds.show()

        #Clean up widgets
        self.toggles.remove(self.feed_toggles[url])
        self.displays[url].parent.destroy()
        self.displays[url].destroy()
        self.feed_labels[url].destroy()
        self.feed_icons[url].destroy()
        self.feed_toggles[url].destroy()
        del self.displays[url]
        del self.feed_labels[url]
        del self.feed_icons[url]
        del self.feed_throbbers[url]
        del self.feed_toggles[url]

        if isinstance(self.feeds[url], classes.GoogleFeed):
            username = self.feeds[url].url.split('-')[-1]
            if username in self.google_logins:
                self.google_logins[username]['count'] -= 1
                if self.google_logins[username]['count'] == 0:
                    del self.google_logins[username]

        #Clean up non-widgets
        self.feeds[url].delete()
        self.urls.remove(url)
        try:
            del self.feeds[url]
            del self.newest[url]
        except:
            pass

        #If the only remaining feed is Google Reader
        #(self.feeds hasn't been changed yet)
        all_greader = bool(len(self.urls))
        for url, feed in self.feeds.items():
            if not isinstance(feed, classes.GoogleReader):
                all_greader = False
                break

        self.set_icon_name(['awn-feeds', 'awn-feeds-greader'][all_greader])

        self.do_favicons()
        self.throbber.props.active = False

    #Actually add a feed
    def add_feed(self, url, parsed=None, *data):
        if url in self.urls:
            return False

        if url not in self.written_urls:
            fp = open(config_path, 'r')
            f = fp.read()
            fp.close()

            if len(self.urls) > 0:
                f += '\n' + url

            else:
                f = url

            fp = open(config_path, 'w')
            fp.write(f)
            fp.close()

        self.urls.append(url)

        _base_url = '-'.join(url.split('-')[:-1])

        if _base_url == 'google-reader':
            self.feeds[url] = classes.GoogleReader(self, *data)

        elif _base_url == 'google-wave':
            self.feeds[url] = classes.GoogleWave(self, *data)

        elif _base_url == 'reddit':
            self.feeds[url] = classes.Reddit(self, *data)

        elif _base_url in ('twitter-timeline', 'twitter-both', 'twitter-replies'):
            self.feeds[url] = classes.Twitter(self, *(data + (_base_url, )))

        else:
            self.feeds[url] = classes.WebFeed(self, url, parsed)

        if not isinstance(self.feeds[url], classes.GoogleReader):
            self.set_icon_name('awn-feeds')

        else:
            only_greader = True
            for feed in self.feeds.values():
                if not isinstance(feed, classes.GoogleReader):
                    only_greader = False

            if only_greader:
                self.set_icon_name('awn-feeds-greader')

        self.add_feed_row(url, len(self.urls))

        for toggle in self.toggles:
            toggle.set_active(False)

        self.feeds[url].update()

        self.feed_throbbers[url].props.active = True
        self.widget.show_all()

        self.no_feeds.hide()

        self.do_favicons()

        if len(self.feeds) == 1:
          self.do_timer()

    #When a button is released on the applet
    def button_release(self, widget, event):
        if event.button == 1:
            if self.dialog.flags() & gtk.VISIBLE:
                self.dialog.hide()

            else:
                self.dialog.show()

        elif event.button == 2:
            if len(self.urls) > 0:
                if self.urls[0] in self.feeds:
                    web_url = self.feeds[self.urls[0]].web_url

                    self.open_url(None, web_url)

        elif event.button == 3:
            self.dialog.hide()
            self.show_menu(event)

    #Right click menu
    def show_menu(self, event):
        #Create the menu and menu items if they don't exist
        if not self.menu:
            #Create the items
            add_feed = awn.image_menu_item_new_with_label(_("Add Feed"))
            update = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
            self.show_only_new_check = gtk.CheckMenuItem(_("Show Only _New Feeds"))
            sep = gtk.SeparatorMenuItem()
            prefs_item = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
            about = gtk.ImageMenuItem(_("_About %s") % _("Feeds Applet"))
            if awnlib.is_required_version(gtk.gtk_version, (2, 16, 0)):
                about.props.always_show_image = True
            about.set_image(gtk.image_new_from_stock(gtk.STOCK_ABOUT, gtk.ICON_SIZE_MENU))

            #Add icon for "Add Feed"
            add_icon = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
            add_feed.set_image(add_icon)

            if self.client.get_value(GROUP_DEFAULT, 'show_only_new'):
                self.show_only_new_check.set_active(True)

            add_feed.connect('activate', self.add_feed_dialog)
            update.connect('activate', self.update_feeds)
            self.show_only_new_check.connect('toggled', self.toggle_show_only_new)
            prefs_item.connect('activate', self.open_prefs)
            about.connect('activate', self.show_about)

            #Create the menu
            self.menu = self.create_default_menu()
            for item in (add_feed, update, self.show_only_new_check, sep, prefs_item, about):
                self.menu.append(item)

        self.menu.show_all()
        self.popup_gtk_menu (self.menu, event.button, event.time)

    def toggle_show_only_new(self, item):
        self.client.set_value(GROUP_DEFAULT, "show_only_new", item.get_active())

        if self.prefs_dialog:
            if self.prefs_dialog.show_only_new_check is not None:
                self.prefs_dialog.show_only_new_check.set_active(item.get_active())

            else:
                self.show_only_new()

        else:
            self.show_only_new()

    def show_only_new(self, url=None):
        if self.client.get_value(GROUP_DEFAULT, "show_only_new"):
            if url is not None:
                if self.feeds[url].num_new == 0:
                    self.feed_toggles[url].parent.parent.hide()

                else:
                    self.feed_toggles[url].parent.parent.show()

            else:
                for url, widget in self.feed_toggles.items():
                    if self.feeds[url].num_new == 0:
                        widget.parent.parent.hide()

                    else:
                        widget.parent.parent.show()

        else:
            for widget in self.feed_toggles.values():
                widget.parent.parent.show()

    #Show the preferences window
    def open_prefs(self, widget):
        if not self.prefs_dialog:
            import prefs
            self.prefs_dialog = prefs.Prefs(self)

        else:
            self.prefs_dialog.present()

    #Show the about window
    def show_about(self, widget):
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, 48, 48)

        win = gtk.AboutDialog()
        win.set_name(_("Feeds Applet"))
        win.set_copyright('Copyright \xc2\xa9 2009 Sharkbaitbobby')
        win.set_authors(['Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>'])
        win.set_artists(['Victor C.', '  (Icon modified by Sharkbaitbobby)', \
            'Jakub Szypulka'])
        win.set_comments(_("Applet to monitor web feeds"))
        win.set_license("This program is free software; you can redistribute it "+\
            "and/or modify it under the terms of the GNU General Public License "+\
            "as published by the Free Software Foundation; either version 2 of "+\
            "the License, or (at your option) any later version.\n\nThis program is "+\
            "distributed in the hope that it will be useful, but WITHOUT ANY "+\
            "WARRANTY; without even the implied warranty of MERCHANTABILITY or "+\
            "FITNESS FOR A PARTICULAR PURPOSE.    See the GNU General Public "+\
            "License for more details.\n\nYou should have received a copy of the GNU "+\
            "General Public License along with this program; if not, write to the "+\
            "Free Software Foundation, Inc., "+\
            "51 Franklin St, Fifth Floor, Boston, MA 02110-1301, USA.")
        win.set_wrap_license(True)
        win.set_logo(pixbuf)
        win.set_icon_from_file(icon_path)
        win.set_website('http://wiki.awn-project.org/Feeds_Applet')
        win.set_website_label('wiki.awn-project.org')
        win.set_version(__version__)
        win.run()
        win.destroy()

    def get_urls(self):
        if not os.path.exists(config_path):
            fp = open(config_path, 'w+')
            fp.write('http://planet.awn-project.org/?feed=atom')
            fp.close()

            self.urls = ['http://planet.awn-project.org/?feed=atom']

        else:
            fp = open(config_path, 'r')
            urltext = fp.read()
            fp.close()

            self.urls = []
            for url in urltext.split('\n'):
                if url != '':
                    self.urls.append(url)

    #OPML stuff...

    #Confirmation dialog, from dragging and dropping
    def add_opml_dialog(self, urls):
        dialog = gtk.Dialog(_("OPML Import"), None, gtk.DIALOG_NO_SEPARATOR, \
          (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))

        message = gettext.ngettext("Do you want to add %d feed?",
          "Do you want to add %d feeds?", len(urls)) % len(urls)

        dialog.get_content_area().pack_start(gtk.Label(message))

        if self.icon_theme.has_icon('text-x-opml'):
            dialog.set_icon_name('text-x-opml')

        else:
            dialog.set_icon_from_file(icon_path)

        dialog.show_all()

        resp = dialog.run()
        dialog.destroy()

        if resp == gtk.RESPONSE_ACCEPT:
            self.add_opml(urls)

        #Not sure why this is necessary...
        gtk.main()

    #Actually add each feed
    def add_opml(self, urls):
        try:
            with open(config_path, 'r') as fp:
                f = fp.read()
        except IOError, e:
            dialog = classes.ErrorDialog(self, _("Could not open '%s'") % config_path, e)
            dialog.run()
            dialog.destroy()
            return

        for url in urls:
            f += '\n' + url
            self.written_urls.append(url)

        try:
            with open(config_path, 'w') as fp:
                fp.write(f)
        except IOError, e:
            dialog = classes.ErrorDialog(self, _("Could not save '%s'") % config_path, e)
            dialog.run()
            dialog.destroy()
            return

        for url in urls:
            self.add_feed(url)

        self.written_urls = []

    def load_opml(self, uri):
        try:
            with open(uri, 'r') as fp:
                f = fp.read()
        except IOError, e:
            dialog = classes.ErrorDialog(self, _("Could not open '%s'") % uri, e)
            dialog.run()
            dialog.destroy()
            return

        urls = parse_opml(f, self.urls)

        self.add_opml_dialog(urls)

    def icon_theme_changed(self, *args):
        #Get a 16x16 icon representing the Internet/web
        self.web_image = self.icon_theme.load_icon('applications-internet', 16, 0)

        #Force a size of 16x16
        if self.web_image.get_width() != 16 or self.web_image.get_height() != 16:
            self.web_image = self.web_image.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)

    def show_favicons(self):
        for url, icon in self.feed_icons.items():
            self.got_favicon(self.feeds[url], True, True)

        #Override the config value because sometimes we get this before the client has the new value
        #At least I think that's what's happening.
        self.do_favicons(True)

        if self.prefs_dialog:
            self.prefs_dialog.update_liststore()

    def hide_favicons(self):
        for url, icon in self.feed_icons.items():
            self.feed_icons[url].set_from_pixbuf(self.web_image)

        self.do_favicons()

        if self.prefs_dialog:
            self.prefs_dialog.update_liststore()

    def size_changed(self, applet, new_size):
        for overlay in (self.throbber, self.error_icon, self.favicon1, self.favicon2, self.favicon3):
            if new_size > 48:
                overlay.props.scale = 16.0 / new_size
            else:
                overlay.props.scale = 0.33

        if new_size > 48:
            self.favicon2.props.x_adj = 0.5 - 24.0 / new_size
            self.favicon3.props.y_adj = 0.5 - 24.0 / new_size

        else:
            self.favicon2.props.x_adj = 0.0
            self.favicon3.props.y_adj = 0.0

    #timeout is currently ignored because Python 2.5 doesn't support it.
    class NetworkHandler(ThreadQueue):
        class NetworkException(Exception):
            pass

        class ParseException(Exception):
            pass

        @async_method
        def get_data(self, uri, headers={}, parse=False, timeout=60, user_data=None, opener=None):
            try:
                req = urllib2.Request(uri)
                for key, val in headers.items():
                    req.add_header(key, val)
                req.add_header('HTTP_USER_AGENT', user_agent)

                if opener is None:
                    fp = urllib2.urlopen(req)
                else:
                    fp = opener.open(req)

                data = fp.read()
                fp.close()
            except:
                raise self.NetworkException("Couldn't fetch file")
            else:
                if parse:
                    data = feedparser.parse(data)

                if user_data is not None:
                    return user_data, data
                else:
                    return data

        @async_method
        def post_data(self, uri, headers={}, data=None, timeout=60, server_headers=False, opener=None):
            try:
                req = urllib2.Request(uri, data)
                for key, val in headers.items():
                    req.add_header(key, val)
                req.add_header('HTTP_USER_AGENT', user_agent)

                if opener is None:
                    fp = urllib2.urlopen(req)
                else:
                    fp = opener.open(req)

                headers = fp.info()
                data = fp.read()
                fp.close()
            except:
                raise self.NetworkException("Couldn't post data")
            else:
                if server_headers:
                    return data, headers
                else:
                    return data

        #Feedparser can take up to a second parsing a feed.
        #Several feeds trying to run feedparser at the same time locks up the interface
        #So do this in a separate thread
        @async_method
        def run_feedparser(self, data, user_data=None):
            try:
                parsed = feedparser.parse(data)
            except:
                raise self.ParseException("Parsing error")
            else:
                if user_data is not None:
                    return user_data, parsed
                else:
                    return parsed

#Utility functions...

#Shorten and ellipsize long strings
def shortify(string):
    string = string.replace('\n', ' ')
    if len(string) > 33:
        return string[:30] + '...'

    else:
        return string

#Parses an OPML file and returns a list of feed URLs
def parse_opml(data, existing_urls):
    children = []
    urls = []

    try:
        doc = minidom.parseString(data)

        nodes = doc.documentElement.childNodes

        #Narrow it down to <outline> elements
        for node in nodes:
            if isinstance(node, minidom.Element):
                if node.tagName == 'body':
                    for child in node.childNodes:
                        if isinstance(child, minidom.Element):
                            children.append(child)

        #Go through each <outline> element
        for node in children:
            #Individual feed
            if node.hasAttribute('xmlUrl'):
                url = node.getAttribute('xmlUrl')
                if url not in existing_urls:
                    urls.append(url)

            #It's a category; ignore it and just get its feeds
            else:
                for child in node.childNodes:
                    if isinstance(child, minidom.Element):
                        if child.hasAttribute('xmlUrl'):
                            url = child.getAttribute('xmlUrl')
                            if url not in existing_urls:
                                urls.append(url)

        doc.unlink()

    except:
        pass

    return urls


if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = App(awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
