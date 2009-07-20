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

import gettext
import locale

import awn
from awn.extras import defs
from awn.extras import awnlib

awn.check_dependencies(globals(), 'feedparser', 'pynotify')

APP = "awn-extras-applets"
gettext.bindtextdomain(APP, defs.GETTEXTDIR)
gettext.textdomain(APP)
_ = gettext.gettext

group = awn.CONFIG_DEFAULT_GROUP

icon_path = '%s/share/avant-window-navigator/applets/feeds/icons/awn-feeds.svg'
icon_path = icon_path % defs.PREFIX

greader_path = '%s/share/avant-window-navigator/applets/feeds/icons/' + \
    'awn-feeds-greader.svg'
greader_path = greader_path % defs.PREFIX

config_path = '%s/.config/awn/applets/feeds.txt' % os.environ['HOME']

google_login = 'https://www.google.com/accounts/ClientLogin'
google_list = 'http://www.google.com/reader/atom/user/-/state/com.google' + \
    '/reading-list?n=10'

reader_url = 'http://www.google.com/reader/'


class App(awn.AppletSimple):
    displays = {}
    toggles = {}
    feeds = {}
    newest = {}
    focuses = 0
    timer = 0
    widget = None
    menu = None
    keyring = None
    google_key = None
    SID = ''

    def __init__(self, uid, panel_id):
        self.uid = uid

        #AWN Applet Configuration
        awn.AppletSimple.__init__(self, 'feeds', uid, panel_id)
        self.set_tooltip_text(_("Feeds Applet"))
        self.dialog = awn.Dialog(self)

        #AwnConfigClient instance
        self.client = awn.Config('feeds', None)

        #Set the icon
        self.set_icon_name('awn-feeds')

        #Connect to signals
        self.connect('button-release-event', self.button_release)
        self.dialog.connect('focus-out-event', self.dialog_focus_out)

        #Update the feeds
        self.update_feeds()

        #Update the feeds every 5 minutes,
        #unless the user does right click->refresh
        self.timer = gobject.timeout_add_seconds(300, self.update_feeds)

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
                            continue

                        #Check if wrong password/username
                        if f.find('BadAuthentication') != -1:
                            self.google_error = True
                            continue

                        #Save the SID so we don't have to re-login every update
                        self.SID = f.split('=')[1].split('\n')[0]

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
        try:
            if 'google-reader' in self.urls > 0:
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

        if total_new > 0:
            msg = ""
            for url, num in num_new.items():
                if url == 'google-reader':
                    title = _("Google Reader")
                else:
                    title = self.feeds[url].feed.title

                if num > 2:
                    msg += _("%s\n        %s\n        %s\n(%s More)\n") % (title,
                        self.shortify(self.feeds[url].entries[0]['title']),
                        self.shortify(self.feeds[url].entries[1]['title']),
                        (num - 2))

                elif num == 2:
                    msg += '%s\n        %s\n        %s\n' % (title,
                        self.shortify(self.feeds[url].entries[0]['title']),
                        self.shortify(self.feeds[url].entries[1]['title']))

                elif num == 1:
                    msg += '%s\n        %s\n' % (title,
                        self.shortify(self.feeds[url].entries[0]['title']))

            pynotify.init(_("Feeds Applet"))
            notification = pynotify.Notification(_("%s New Items - Feeds Applet") % \
                total_new, msg, [icon_path, greader_path][only_google])
            notification.set_timeout(5000)
            notification.show()
            pynotify.uninit()

        #Update the feeds every 5 minutes
        if self.timer:
            gobject.source_remove(self.timer)

        self.timer = gobject.timeout_add_seconds(300, self.update_feeds)

        #Refresh the dialog
        self.setup_dialog()

        return False

    def setup_dialog(self, *args):
        #Clear the dialog
        if self.widget:
            self.widget.destroy()

        #Get the feeds
        self.get_urls()

        self.widget = gtk.VBox(False, 6)

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
            for url in self.feeds.keys():
                feed_vbox = gtk.VBox(False, 6)
                feed_vbox.set_no_show_all(True)
                self.displays[url] = feed_vbox

                for entry in self.feeds[url].entries[:5]:
                    image = gtk.image_new_from_icon_name('applications-internet', \
                        gtk.ICON_SIZE_MENU)
                    label = gtk.Label(self.shortify(entry['title']))

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

                    feed_vbox.pack_start(button, False)

                feed_hbox = gtk.HBox(False, 6)

                #Remove button
                image = gtk.image_new_from_stock(gtk.STOCK_REMOVE, gtk.ICON_SIZE_MENU)
                button = gtk.Button()
                button.set_image(image)
                button.set_relief(gtk.RELIEF_NONE)
                button.set_tooltip_text(_("Remove feed"))
                button.connect('clicked', self.remove_feed, url)

                feed_hbox.pack_start(button, False)

                if url != 'google-reader':
                    toggle = gtk.ToggleButton(self.feeds[url].feed.title)

                else:
                    toggle = gtk.ToggleButton(_("Google Reader"))

                toggle.set_relief(gtk.RELIEF_NONE)
                toggle.connect('toggled', self.toggle_display, url)

                #If there's only one feed, show its most recent items
                if len(self.urls) == 1:
                    toggle.set_active(True)

                #Not showing, set appropriate tooltip text
                else:
                    toggle.set_tooltip_text(_("Show this feed's items"))

                feed_hbox.pack_start(toggle)

                image = gtk.image_new_from_icon_name('applications-internet', \
                    gtk.ICON_SIZE_MENU)
                button = gtk.Button()
                button.set_image(image)
                button.set_relief(gtk.RELIEF_NONE)
                button.set_tooltip_text(_("Open this feed's website"))

                if url != 'google-reader':
                    button.connect('clicked', self.open_url, self.feeds[url].feed.link)

                else:
                    button.connect('clicked', self.open_url, reader_url)

                feed_hbox.pack_start(button, False)

                self.widget.pack_start(feed_hbox, False)
                self.widget.pack_start(feed_vbox, False)

            button = gtk.Button(_("_Add Feed"))
            image = gtk.image_new_from_stock(gtk.STOCK_ADD, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)
            button.connect('clicked', self.add_feed_dialog)

            hbox = gtk.HBox(False, 6)
            hbox.pack_start(button, True, False)

            self.widget.pack_start(hbox, False)

            self.widget.show_all()

            self.dialog.add(self.widget)

    #Toggle the showing of a feed's most recent items
    def toggle_display(self, toggle, url):
        if toggle.get_active():
            self.displays[url].show()
            toggle.set_tooltip_text(_("Hide this feed's items"))

            #Only show one feed at a time
            for other_toggle in self.toggles:
                if other_toggle != toggle:
                    other_toggle.set_active(False)

        else:
            self.displays[url].hide()
            toggle.set_tooltip_text(_("Show this feed's items"))

    #User cleared Google Reader error
    def cancel_google_error(self, button):
        self.google_error = False

        self.remove_feed(None, 'google-reader')

        self.set_icon_name('awn-feeds')

    #Open a URL
    def open_url(self, widget, url):
        try:
            gtk.show_uri(None, url, gtk.get_current_event_time())

        #For GTK < 2.14
        except:
            os.system('xdg-open "%s" &' % url)

    #Remove a feed
    def remove_feed(self, x, url):
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
            self.client.set_int(group, 'google-token', 0)
            self.SID = ''
            self.google_key = None

        #If the only remaining feed is Google Reader
        elif len(self.feeds.keys()) == 1 and 'google-reader' in self.feeds:
            self.set_icon_name('awn-feeds-greader')

        #Clean up
        try:
            del self.feeds[url]
            del self.newest[url]
        except:
            pass

        self.setup_dialog()

    #Actually add a feed
    def add_feed(self, *args):
        #RSS/Atom
        if self.combo.get_active() == 0:
            if self.url_entry.get_text() not in self.feeds.keys():
                fp = open(config_path, 'r')
                f = fp.read()
                fp.close()

                f = self.url_entry.get_text() + '\n' + f

                fp = open(config_path, 'w')
                fp.write(f)
                fp.close()

                self.update_feeds()
                self.setup_dialog()

        #Google Reader
        elif self.combo.get_active() == 1:
            username = self.user_entry.get_text()
            password = self.pass_entry.get_text()

            self.get_google_key(username, password)

            fp = open(config_path, 'r')
            f = fp.read()
            fp.close()

            f = 'google-reader\n' + f

            fp = open(config_path, 'w')
            fp.write(f)
            fp.close()

            self.update_feeds()
            self.setup_dialog()

    #Show the dialog to add a feed
    def add_feed_dialog(self, *args):
        #Clear the dialog
        if self.widget:
            self.widget.destroy()

        #Source: label and combo box
        source_label = gtk.Label(_("Source:"))
        source_label.set_alignment(1.0, 0.5)

        #TODO: This would only allow one Google Reader instance
        #Change?
        source_combo = gtk.combo_box_new_text()
        source_combo.append_text(_("RSS/Atom"))
        if 'google-reader' not in self.urls:
            source_combo.append_text(_("Google Reader"))
        #source_combo.append_text(_("Twitter")) #...?
        source_combo.set_active(0)
        source_combo.connect('notify::popup-shown', self.combo_popup_shown)
        source_combo.connect('changed', self.combo_changed)
        self.combo = source_combo

        source_hbox = gtk.HBox(False, 6)
        source_hbox.pack_start(source_label, False, False)
        source_hbox.pack_start(source_combo)

        #URL: label and entry
        url_label = gtk.Label(_("URL:"))
        url_label.set_alignment(1.0, 0.5)

        self.url_entry = gtk.Entry()
        self.url_entry.connect('changed', self.entry_changed)

        self.url_hbox = gtk.HBox(False, 6)
        self.url_hbox.pack_start(url_label, False, False)
        self.url_hbox.pack_start(self.url_entry)
        self.url_hbox.show_all()
        self.url_hbox.set_no_show_all(True)

        #Username: label and entry
        user_label = gtk.Label(_("Username:"))
        user_label.set_alignment(1.0, 0.5)
        user_label.show()

        self.user_entry = gtk.Entry()
        self.user_entry.show()
        self.user_entry.connect('changed', self.entry_changed)

        self.user_hbox = gtk.HBox(False, 6)
        self.user_hbox.pack_start(user_label, False, False)
        self.user_hbox.pack_start(self.user_entry)
        self.user_hbox.set_no_show_all(True)

        #Password: label and entry
        pass_label = gtk.Label(_("Password:"))
        pass_label.set_alignment(1.0, 0.5)
        pass_label.show()

        self.pass_entry = gtk.Entry()
        self.pass_entry.set_visibility(False)
        self.pass_entry.show()
        self.pass_entry.connect('changed', self.entry_changed)

        self.pass_hbox = gtk.HBox(False, 6)
        self.pass_hbox.pack_start(pass_label, False, False)
        self.pass_hbox.pack_start(self.pass_entry)
        self.pass_hbox.set_no_show_all(True)

        #Cancel and Add buttons
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect('clicked', self.setup_dialog)

        self.add_button = gtk.Button(stock=gtk.STOCK_ADD)
        self.add_button.set_flags(gtk.CAN_DEFAULT)
        self.add_button.set_sensitive(False)
        self.add_button.connect('clicked', self.add_feed)

        button_hbox = gtk.HBox(False, 6)
        button_hbox.pack_end(self.add_button, False, False)
        button_hbox.pack_end(cancel, False, False)

        self.widget = gtk.VBox(False, 6)
        self.widget.pack_start(source_hbox, False, False)
        self.widget.pack_start(self.url_hbox, False, False)
        self.widget.pack_start(self.user_hbox, False, False)
        self.widget.pack_start(self.pass_hbox, False, False)
        self.widget.pack_start(button_hbox, False, False)
        self.widget.show_all()

        self.dialog.add(self.widget)
        self.add_button.grab_default()

        #Make the labels the same size
        sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        sg.add_widget(source_label)
        sg.add_widget(url_label)
        sg.add_widget(user_label)
        sg.add_widget(pass_label)

        #Make the buttons the same size
        sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        sg.add_widget(cancel)
        sg.add_widget(self.add_button)

    #Get the key for the Google Reader password
    def get_google_key(self, username=None, password=None):
        if self.google_key is None:
            if not self.keyring:
                self.keyring = awnlib.Keyring()

            token = self.client.get_int(group, 'google-token')

            #Username and password provided, e.g. from the add feed dialog
            if username and password:
                if token is None or token == 0:
                    #TODO: i18n?
                    self.google_key = self.keyring.new('Feeds Applet - %s' % username,
                        password,
                        {'username': username, 'network': 'google-reader'},
                        'network')

                    self.client.set_int(group, 'google-token', self.google_key.token)

                else:
                    self.google_key = self.keyring.from_token(token)

            #No username or password provided, e.g. while loading feeds
            else:
                if token is None or token == 0:
                    self.google_key = None

                else:
                    self.google_key = self.keyring.from_token(token)

    #When the user presses a key on the URL/username/password entries,
    #disable/enable the add button based on if there's any text in the
    #appropriate entries
    def entry_changed(self, entry):
        #RSS/Atom
        if self.combo.get_active() == 0:
            if self.url_entry.get_text().replace(' ', '') != '':
                self.add_button.set_sensitive(True)

            else:
                self.add_button.set_sensitive(False)

        #Google Reader (/Twitter?)
        else:
            if self.user_entry.get_text().replace(' ', '') != '':
                if self.pass_entry.get_text().replace(' ', '') != '':
                    self.add_button.set_sensitive(True)

                else:
                    self.add_button.set_sensitive(False)

            else:
                self.add_button.set_sensitive(False)

    #When the combo box in the dialog is pressed, don't hide the dialog
    def combo_popup_shown(self, combo, param):
        if combo.get_property('popup-shown'):
            self.focuses += 1

        return False

    #When the source in the combo box is changed
    def combo_changed(self, combo):
        #RSS/Atom
        if combo.get_active() == 0:
            self.url_hbox.show()
            self.user_hbox.hide()
            self.pass_hbox.hide()

        #Google Reader
        elif combo.get_active() == 1:
            self.url_hbox.hide()
            self.user_hbox.show()
            self.pass_hbox.show()

        #Twitter (TODO?)
        else:
            self.url_hbox.hide()
            self.user_hbox.hide()
            self.pass_hbox.hide()

        #Enable/disable the Add button appropriately
        self.entry_changed(None)

    #When the dialog loses focus
    def dialog_focus_out(self, widget, event):
        if self.focuses:
            self.focuses -= 1

        else:
            self.dialog.hide()

            self.setup_dialog()

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
            prefs_item = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
            update = gtk.ImageMenuItem(gtk.STOCK_REFRESH)
            about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)

            #TODO: let user change update frequency... more?
            prefs_item.set_sensitive(False)

            prefs_item.connect('activate', self.open_prefs)
            update.connect('activate', self.update_feeds)
            about.connect('activate', self.show_about)

            #Create the menu
            self.menu = self.create_default_menu()
            self.menu.append(prefs_item)
            self.menu.append(update)
            self.menu.append(about)

        self.menu.show_all()
        self.menu.popup(None, None, None, event.button, event.time)

    #Show the preferences window
    def open_prefs(self, widget):
        import prefs
        prefs.Prefs(self)
        gtk.main()

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
            "the License, or (at your option) any later version. This program is "+\
            "distributed in the hope that it will be useful, but WITHOUT ANY "+\
            "WARRANTY; without even the implied warranty of MERCHANTABILITY or "+\
            "FITNESS FOR A PARTICULAR PURPOSE.    See the GNU General Public "+\
            "License for more details. You should have received a copy of the GNU "+\
            "General Public License along with this program; if not, write to the "+\
            "Free Software Foundation, Inc.,"+\
            "51 Franklin St, Fifth Floor, Boston, MA 02110-1301    USA.")
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

    def shortify(self, string):
        if len(string) > 25:
            return string[:25] + '...'

        else:
            return string

    #It looks like Google Reader inserts something into every entry,
    #which messes up update_feeds() and makes it think that all 10 items
    #are new.    However, we only need the title and URL of the entry
    #But include the (probably) unique published time and date, if 2+
    #Google Reader sources have the same title + URL
    #TODO: imagine a case where this would happen normally
    def simplify(self, feed):
        i = 0
        for entry in feed.entries:
            feed.entries[i] = {'title': entry.title,
                'link': entry.link,
                'published': entry.published}

            i += 1


if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = App(awn.uid, awn.panel_id)
    awn.init_applet(applet)
    applet.show_all()
    gtk.main()
