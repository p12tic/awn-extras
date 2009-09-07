#! /usr/bin/python
#
# Copyright (c) 2009 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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

import sys
import os
import urllib
import urllib2

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from desktopagnostic.config import GROUP_DEFAULT
import awn
from awn import extras
from awn.extras import _, awnlib

awn.check_dependencies(globals(), 'feedparser', 'pynotify')

icondir = os.path.join(extras.APPLET_BASEDIR, 'feeds', 'icons')

icon_path = os.path.join(icondir, 'awn-feeds.svg')

greader_path = os.path.join(icondir, 'awn-feeds-greader.svg')

config_path = '%s/.config/awn/applets/feeds.txt' % os.environ['HOME']

google_login = 'https://www.google.com/accounts/ClientLogin'
google_list = 'http://www.google.com/reader/atom/user/-/state/com.google' + \
    '/reading-list?n=10'

reader_url = 'http://www.google.com/reader/'


class App(awn.AppletSimple):
    displays = {}
    toggles = []
    feeds = {}
    newest = {}
    timer = 0
    widget = None
    menu = None
    keyring = None
    google_key = None
    dragged_toggle = None
    SID = ''

    def __init__(self, uid, panel_id):
        self.uid = uid

        #AWN Applet Configuration
        awn.AppletSimple.__init__(self, 'feeds', uid, panel_id)
        self.set_tooltip_text(_("Feeds Applet"))
        self.dialog = awn.Dialog(self)

        #AwnConfigClient instance
        self.client = awn.config_get_default_for_applet(self)

        #Set the icon
        self.set_icon_name('awn-feeds')

        #Need icon theme
        self.icon_theme = gtk.icon_theme_get_default()

        #Connect to signals
        self.connect('button-release-event', self.button_release)
        self.dialog.connect('focus-out-event', self.dialog_focus_out)

        #Update the feeds
        self.update_feeds()

        #Update the feeds every 5 minutes,
        #unless the user does right click->refresh
        self.timer = gobject.timeout_add_seconds(300, self.update_feeds)

        #Allow user to drag and drop feed URLs onto the applet icon
        #E.g. In a browser, user drags and drops a link to an Atom feed onto the applet
        self.get_icon().drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
          [("STRING", 0, 0), ("text/plain", 0, 0), ("text/uri-list", 0, 0)], \
          gtk.gdk.ACTION_COPY)
        self.get_icon().connect('drag_data_received', self.applet_drag_data_received)
        self.get_icon().connect('drag-motion', self.applet_drag_motion)
        self.get_icon().connect('drag-leave', self.applet_drag_leave)

    #Update the feeds
    def update_feeds(self, *args):
        self.get_urls()

        num_new = {}
        total_new = 0
        self.io_error = False
        self.google_error = False

        for url in self.urls:
            feed = None

            #Normal RSS/Atom feed
            if url != 'google-reader':
                #TODO: instead download with urllib and threading or something
                #then run feedparser.parse on the string
                try:
                    feed = feedparser.parse(url)

                except IOError:
                    self.io_error = True
                    continue

            #Google Reader feed
            else:
                #Thank you http://code.google.com/p/pyrfeed/wiki/GoogleReaderAPI

                self.get_google_key()

                if self.get_google_sid():
                    #Load the reading list with that magic SID as a cookie
                    req = urllib2.Request(google_list)
                    req.add_header('Cookie', 'SID=' + self.SID)

                    try:
                        fp = urllib2.urlopen(req)
                        f = fp.read()
                        fp.close()

                    except IOError:
                        self.io_error = True
                        continue

                    feed = feedparser.parse(f)

            self.simplify(feed)

            #Deal with the feed...
            if feed is not None:
                if url in self.newest.keys() and (self.newest[url] != feed.entries[0]):
                    #Find out how many items are new
                    if self.newest[url] in feed.entries:
                        num_new[url] = feed.entries.index(self.newest[url])

                    #So many new items that the last loaded item doesn't show up
                    else:
                        num_new[url] = len(feed.entries)

                    total_new += num_new[url]

                if len(feed.entries) > 0:
                    self.newest[url] = feed.entries[0]
                self.feeds[url] = feed

            gtk.main_iteration_do()

        #Make the icon blue if Google Reader is the only (updated) source
        #TODO: change this exact behavior???
        only_google = False
        try:
            if 'google-reader' in self.urls:
                only_google = True
                for url in self.urls:
                    if url != 'google-reader':
                        if num_new[url] > 0:
                            only_google = False

                if only_google:
                    self.set_icon_name('awn-feeds-greader')

                else:
                    self.set_icon_name('awn-feeds')

        except:
            self.set_icon_name('awn-feeds')

        #Notifications - only show if there are any new items and if the user wants them shown
        if total_new > 0 and self.client.get_value(GROUP_DEFAULT, 'notify') == True:
            msg = ""
            for url, num in num_new.items():
                if url == 'google-reader':
                    title = _("Google Reader")
                else:
                    title = self.feeds[url].feed.title

                if url == 'google-reader':
                    title = "<a href='%s'>%s</a>" % (reader_url, title)

                else:
                    title = "<a href='%s'>%s</a>" % (self.feeds[url].feed.link, title)

                if num > 2:
                    msg += _("%s\n  <a href='%s'>%s</a>\n  <a href='%s'>%s</a>\n(%s More)\n") % \
                        (title,
                        self.feeds[url].entries[0]['link'],
                        shortify(self.feeds[url].entries[0]['title']),
                        self.feeds[url].entries[1]['link'],
                        shortify(self.feeds[url].entries[1]['title']),
                        (num - 2))

                elif num == 2:
                    msg += "%s\n  <a href='%s'>%s</a>\n  <a href='%s'>%s</a>\n" % (title,
                        self.feeds[url].entries[0]['link'],
                        shortify(self.feeds[url].entries[0]['title']),
                        self.feeds[url].entries[1]['link'],
                        shortify(self.feeds[url].entries[1]['title']))

                elif num == 1:
                    msg += "%s\n  <a href='%s'>%s</a>\n" % (title,
                        self.feeds[url].entries[0]['link'],
                        shortify(self.feeds[url].entries[0]['title']))

            pynotify.init(_("Feeds Applet"))
            notification = pynotify.Notification(_("%s New Items - Feeds Applet") % \
                total_new, msg, [icon_path, greader_path][only_google])
            notification.set_timeout(5000)
            notification.show()
            pynotify.uninit()

        self.do_timer()

        #Refresh the dialog
        self.setup_dialog()

        return False

    #"Login" to Google (Reader) and get an SID, a magic string that
    #lets us get the user's Google Reader items
    def get_google_sid(self):
        if self.google_key is not None:
            #Get the magic SID from Google to login, if we haven't already
            if self.SID == '':
                #Format the request
                postdata = urllib.urlencode({'service': 'reader',
                    'Email': self.google_key.attrs['username'],
                    'Passwd': self.google_key.password,
                    'source': 'awn-feeds-applet',
                    'continue': 'http://www.google.com/'})

                #Send the data to get the SID
                try:
                    fp = urllib.urlopen(google_login, postdata)
                    f = fp.read()
                    fp.close()

                except IOError:
                    self.io_error = True
                    return False

                #Check if wrong password/username
                if f.find('BadAuthentication') != -1:
                    self.google_error = True
                    return False

                #Save the SID so we don't have to re-login every update
                self.SID = f.split('=')[1].split('\n')[0]

            #We have SIDnal
            return True

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

    #Widgets, etc.
    def setup_dialog(self, *args):
        #Clear the dialog
        if self.widget:
            self.widget.destroy()

        #Clear the list of toggle buttons
        self.toggles = []

        #Get the feeds
        self.get_urls()

        self.widget = gtk.VBox(False, 6)

        #This is mainly for reordering of the feeds in the dialog
        #(The only way to get the drag-motion signal on a widget is
        #for the widget to be a drag destination
        self.widget.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
          [('STRING', 0, 0), ('text/plain', 0, 0), ('text/uri-list', 0, 0)], \
          gtk.gdk.ACTION_COPY)
        self.widget.connect('drag-data-received', self.dialog_drag_received)
        self.widget.connect('drag-motion', self.dialog_drag_motion)
        self.widget.connect('drag-leave', self.dialog_drag_leave)

        #Couldn't connect
        if self.io_error:
            label = gtk.Label(_("Feeds Applet could not load all of your feeds.\nCheck your Internet connection and\nclick Refresh to try again."))
            self.widget.pack_start(label, False)

            button = gtk.Button(stock=gtk.STOCK_REFRESH)
            button.connect('clicked', self.update_feeds)

            button_hbox = gtk.HBox(False, 0)
            button_hbox.pack_start(button, True, False)

            self.widget.pack_start(button_hbox, False)

            self.widget.pack_start(gtk.HSeparator(), False, False, 6)

        #Wrong username/password
        if self.google_error:
            button = gtk.Button()
            image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
            button.set_image(image)
            button.set_relief(gtk.RELIEF_NONE)
            button.set_tooltip_text(_("Hide Error"))
            button.connect('clicked', self.cancel_google_error)

            button_vbox = gtk.VBox(False, 0)
            button_vbox.pack_start(button, True, False)

            label = gtk.Label(_("Feeds Applet could not login to Google Reader.\nCheck your username and password."))

            hbox = gtk.HBox(False, 6)
            hbox.pack_start(button_vbox, False)
            hbox.pack_start(label, True)

            self.widget.pack_start(hbox, False)

        #User has no feeds
        if len(self.urls) == 0:
            label = gtk.Label(_("You don't have any feeds."))

            button = gtk.Button(_("_Add Feed"))
            image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)
            button.connect('clicked', self.add_feed_dialog)

            hbox = gtk.HBox(False, 6)
            hbox.pack_start(button, True, False)

            self.widget.pack_start(label, False)
            self.widget.pack_start(hbox, False)
            self.widget.show_all()

            self.dialog.add(self.widget)

        #User has feeds
        else:
            i = 0
            for url in self.feeds.keys():
                feed_vbox = gtk.VBox(False, 6)
                feed_items_vbox = gtk.VBox(False, 6)
                self.displays[url] = feed_items_vbox
                feed_items_vbox.set_no_show_all(True)

                if url == 'google-reader':
                    weburl = reader_url

                else:
                    try:
                        weburl = self.feeds[url].feed.link
                    except:
                        weburl = url

                for entry in self.feeds[url].entries[:5]:
                    image = self.web_image()
                    label = gtk.Label(shortify(entry['title']))

                    hbox = gtk.HBox(False, 6)
                    hbox.pack_start(image, False, False)
                    hbox.pack_start(label, True, False)

                    button = gtk.Button()
                    button.add(hbox)
                    button.set_relief(gtk.RELIEF_NONE)
                    if len(entry['title']) > 25:
                        button.set_tooltip_text(entry['title'])
                    button.connect('clicked', self.open_url, entry['link'])
                    button.show_all()

                    feed_items_vbox.pack_start(button, False)

                feed_hbox = gtk.HBox(False, 6)
                feed_vbox.pack_start(feed_hbox, False)
                feed_vbox.pack_start(feed_items_vbox, False)
                self.widget.pack_start(feed_vbox)

                #Button for opening the feed's website
                image = self.web_image()
                button = gtk.Button()
                button.set_image(image)
                button.set_relief(gtk.RELIEF_NONE)
                button.set_tooltip_text(_("Open this feed's website"))

                if url != 'google-reader':
                    button.connect('clicked', self.open_url, weburl)

                else:
                    button.connect('clicked', self.open_url, reader_url)

                feed_hbox.pack_start(button, False)

                #ToggleButton for showing/hiding the feed's items
                arrow = gtk.Arrow(gtk.ARROW_RIGHT, gtk.SHADOW_NONE)

                if url != 'google-reader':
                    label = gtk.Label(self.feeds[url].feed.title)

                else:
                    label = gtk.Label(_("Google Reader"))

                toggle_hbox = gtk.HBox(False, 3)
                toggle_hbox.pack_start(arrow, False)
                toggle_hbox.pack_start(label, False)

                toggle = gtk.ToggleButton()
                toggle.add(toggle_hbox)
                toggle.set_relief(gtk.RELIEF_NONE)
                toggle.connect('toggled', self.toggle_display, url)
                self.toggles.append(toggle)

                toggle.arrow = arrow
                toggle.weburl = weburl
                toggle.url = url
                toggle.web = button
                toggle.position = i
                toggle.label = None
                toggle.size_group = None

                #Drag and Drop to reorder
                #or drop an e.g. a web browser to go to that feeds' url
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

                i += 1

            button = gtk.Button(_("_Add Feed"))
            image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)
            button.connect('clicked', self.add_feed_dialog)

            hbox = gtk.HBox(False, 6)
            hbox.pack_start(button, True, False)

            self.widget.pack_start(hbox, False)

            self.widget.show_all()

            self.dialog.add(self.widget)

    #Toggle buttons drag and drop
    def toggle_drag_begin(self, toggle, context):
        toggle.set_active(False)

        #Literally drag the toggle around!
        #(Since Gtk 2.14)
        try:
            toggle.drag_source_set_icon(toggle.get_screen().get_rgba_colormap(), \
              toggle.get_snapshot(), None)

        except:
            pass

        if len(self.toggles) > 1:
            for other_toggle in self.toggles:
                if other_toggle != toggle:
                    break

            toggle.hide()
            toggle.web.hide()
            toggle.label = gtk.Label(' ')
            toggle.size_group = gtk.SizeGroup(gtk.SIZE_GROUP_BOTH)
            toggle.size_group.add_widget(other_toggle.parent)
            toggle.size_group.add_widget(toggle.label)
            toggle.parent.pack_start(toggle.label)
            toggle.label.show()

            self.dragged_toggle = toggle

    #When the toggle is dragged onto something
    def toggle_drag_get(self, toggle, context, data, info, time):
        data.set(data.target, 8, toggle.weburl)

    #When the toggle dragging is done
    def toggle_drag_end(self, toggle, context):
        if toggle.label:
            toggle.label.destroy()
        if toggle.size_group:
            del toggle.size_group
        toggle.show()
        toggle.web.show()
        self.dragged_toggle = None

        #Save in case the feeds were reordered
        urls = ''
        self.urls = []
        children = toggle.parent.parent.parent.get_children()
        for vbox in children[:-1]:
            hbox = vbox.get_children()[0]
            urls += hbox.get_children()[1].url + '\n'
            self.urls.append(hbox.get_children()[1].url)

        #Remove the last newline
        urls = urls[:-1]

        fp = open(config_path, 'w+')
        fp.write(urls)
        fp.close()

    def dialog_drag_received(self, *args):
        #TODO: anything here?
        pass

    def dialog_drag_motion(self, widget, context, x, y, time):
        if self.dragged_toggle is not None:
            toggles_xywh = {}
            i = 0
            for toggle in self.toggles:
                if toggle != self.dragged_toggle:
                    a = toggle.allocation
                    children = toggle.parent.parent.parent.get_children()
                    toggle.drag_pos = children.index(toggle.parent.parent)
                    toggles_xywh[i] = {'x': a.x, 'y': a.y, 'w': a.width, 'h': a.height, 't': toggle}
                i += 1

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

            if url.find('http://') == 0 or url.find('https://') == 0:
                if url.find('\n') == -1:
                    if url not in self.urls:
                        self.add_feed(url)

        else:
            context.finish(False, False, time)

    def applet_drag_motion(self, widget, context, x, y, time):
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

    #User cleared Google Reader error
    def cancel_google_error(self, button):
        self.google_error = False

        self.remove_feed(None, 'google-reader')

        self.set_icon_name('awn-feeds')

    #Show the Add Feed dialog
    def add_feed_dialog(self, widget):
        import prefs
        prefs.AddFeed(applet=self)

    #Open a URL
    def open_url(self, widget, url):
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

        #Sign out of Google Reader, if we're removing it
        if url == 'google-reader':
            self.client.set_value(GROUP_DEFAULT, 'google_token', 0)
            self.SID = ''
            self.google_key = None

        #If the only remaining feed is Google Reader
        #(self.feeds hasn't been changed yet)
        elif len(self.feeds.keys()) == 2 and 'google-reader' in self.feeds:
            self.set_icon_name('awn-feeds-greader')

        #Clean up
        try:
            del self.feeds[url]
            del self.newest[url]
        except:
            pass

        self.setup_dialog()

    #Actually add a feed
    def add_feed(self, url):
        fp = open(config_path, 'r')
        f = fp.read()
        fp.close()

        f += '\n' + url

        fp = open(config_path, 'w')
        fp.write(f)
        fp.close()

        self.update_feeds()
        self.setup_dialog()

    #Get/set the key for the Google Reader username and password
    def get_google_key(self, username=None, password=None):
        if self.google_key is None:
            if not self.keyring:
                self.keyring = awnlib.Keyring()

            token = self.client.get_value(GROUP_DEFAULT, 'google_token')

            #Username and password provided, e.g. from the add feed dialog
            if username and password:
                if token is None or token == 0:
                    self.google_key = self.keyring.new('Feeds Applet - %s' % username,
                        password,
                        {'username': username, 'network': 'google-reader'},
                        'network')

                    self.client.set_value(GROUP_DEFAULT, 'google_token', int(self.google_key.token))

                else:
                    self.google_key = self.keyring.from_token(token)

            #No username or password provided, e.g. while loading feeds
            else:
                if token is None or token == 0:
                    self.google_key = None

                else:
                    self.google_key = self.keyring.from_token(token)

    #When the dialog loses focus
    def dialog_focus_out(self, widget, event):
        if self.dragged_toggle is None:
            self.dialog.hide()

    #When a button is released on the applet
    def button_release(self, widget, event):
        if event.button in (1, 2):
            if self.dialog.flags() & gtk.VISIBLE:
                self.dialog.hide()

            else:
                self.dialog.show_all()

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
            sep = gtk.SeparatorMenuItem()
            prefs_item = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
            about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)

            #Add icon for "Add Feed"
            add_icon = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_MENU)
            add_feed.set_image(add_icon)

            add_feed.connect('activate', self.add_feed_dialog)
            update.connect('activate', self.update_feeds)
            prefs_item.connect('activate', self.open_prefs)
            about.connect('activate', self.show_about)

            #Create the menu
            self.menu = self.create_default_menu()
            self.menu.append(add_feed)
            self.menu.append(update)
            self.menu.append(sep)
            self.menu.append(prefs_item)
            self.menu.append(about)

        self.menu.show_all()
        self.menu.popup(None, None, None, event.button, event.time)

    #Show the preferences window
    def open_prefs(self, widget):
        import prefs
        prefs.Prefs(self)

    #Show the about window
    def show_about(self, widget):
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, 48, 48)

        win = gtk.AboutDialog()
        win.set_name(_("Feeds Applet"))
        win.set_copyright('Copyright 2009 Sharkbaitbobby')
        win.set_authors(['Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>'])
        win.set_artists(['Victor C.', '(Icon modified by Sharkbaitbobby)'])
        win.set_comments(_("Monitor Web Feeds"))
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
        win.run()
        win.destroy()

    def get_urls(self):
        if not os.path.exists(config_path):
            fp = open(config_path, 'w+')
            fp.write('http://planet.awn-project.org/?feed=atom')
            fp.close()

            self.urls = ('http://planet.awn-project.org/?feed=atom', )

        else:
            fp = open(config_path, 'r')
            urltext = fp.read()
            fp.close()

            self.urls = []
            for url in urltext.split('\n'):
                if url != '':
                    self.urls.append(url)

    #It looks like Google Reader inserts something into every entry,
    #which messes up update_feeds() and makes it think that all 10 items are new
    #Only keep the title and URL; they should be unique often enough
    def simplify(self, feed):
        i = 0
        try:
            for entry in feed.entries:
                feed.entries[i] = {'title': entry.title,
                    'link': entry.link}

                i += 1

        except:
            self.io_error = True

    #Returns a 16x16 applications-internet GtkImage
    def web_image(self):
        pixbuf = self.icon_theme.load_icon('applications-internet', 16, 0)

        #Force a size of 16x16
        if pixbuf.get_width() != 16 or pixbuf.get_height() != 16:
            pixbuf = pixbuf.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)

        image = gtk.image_new_from_pixbuf(pixbuf)

        return image


#Utility functions...

#Shorten and ellipsize long strings
def shortify(string):
    if len(string) > 25:
        return string[:25] + '...'

    else:
        return string

if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = App(awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
