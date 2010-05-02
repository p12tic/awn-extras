#! /usr/bin/python
#
# Copyright (c) 2009, 2010 Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
import time

import pygtk
pygtk.require('2.0')
import gtk
import gobject

from desktopagnostic.config import GROUP_DEFAULT
import awn
from awn import extras
from awn.extras import _, awnlib

import classes

icon_dir = extras.PREFIX + '/share/avant-window-navigator/applets/feeds/icons'
icon_path = os.path.join(icon_dir, 'awn-feeds.svg')
greader_path = os.path.join(icon_dir, 'awn-feeds-greader.svg')
twitter_path = os.path.join(icon_dir, 'twitter-16x16.png')

config_path = '%s/.config/awn/applets/feeds.txt' % os.environ['HOME']

cache_dir = os.environ['HOME'] + '/.cache/awn-feeds-applet'
greader_ico = os.path.join(cache_dir, 'google-reader.ico')

reader_url = 'http://www.google.com/reader/'


class Prefs(gtk.Window):
    icon_theme = gtk.icon_theme_get_default()
    show_only_new_check = None

    def __init__(self, applet):
        self.applet = applet

        gtk.Window.__init__(self)
        self.set_title(_("Feeds Applet Preferences"))
        self.set_icon_from_file(icon_path)
        self.set_border_width(12)

        vbox = gtk.VBox(False, 12)

        tab_feeds_vbox = gtk.VBox(False, 6)
        tab_updating_vbox = gtk.VBox(False, 6)

        self.notebook = gtk.Notebook()
        self.notebook.append_page(tab_feeds_vbox, gtk.Label(_("Feeds")))
        self.notebook.append_page(tab_updating_vbox, gtk.Label(_("Updating")))
        vbox.pack_start(self.notebook, True, True, 0)

        #Feeds: Add/Remove, with a TreeView for displaying
        self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, str)

        pb_renderer = gtk.CellRendererPixbuf()

        text_renderer = gtk.CellRendererText()

        column = gtk.TreeViewColumn(' ')
        column.pack_start(pb_renderer, False)
        column.pack_start(text_renderer, True)
        column.add_attribute(pb_renderer, 'pixbuf', 0)
        column.add_attribute(text_renderer, 'markup', 1)

        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.append_column(column)
        self.treeview.set_headers_visible(False)
        self.treeview.get_selection().connect('changed', self.selection_changed)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.treeview)
        sw.set_size_request(225, 200)

        #Remove and add buttons
        self.remove_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        self.remove_button.set_sensitive(False)
        self.remove_button.connect('clicked', self.remove_feed)

        add_button = gtk.Button(stock=gtk.STOCK_ADD)
        add_button.connect('clicked', self.show_add)

        buttons_hbox = gtk.HButtonBox()
        buttons_hbox.set_layout(gtk.BUTTONBOX_EDGE)
        buttons_hbox.pack_end(add_button, False)
        buttons_hbox.pack_end(self.remove_button, False)

        show_favicons_check = gtk.CheckButton(_("_Show website icons"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'show_favicons'):
            show_favicons_check.set_active(True)
        show_favicons_check.connect('toggled', self.check_toggled, 'show_favicons')

        self.show_only_new_check = gtk.CheckButton(_("Show _only new feeds"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'show_only_new'):
            self.show_only_new_check.set_active(True)
        self.show_only_new_check.connect('toggled', self.check_toggled, 'show_only_new')

        #TODO: this position is a little ugly, but I don't know how to do it better.
        #Import and export buttons (OPML)
        import_button = gtk.Button(_("Import"))
        import_button.connect('clicked', self.do_import)

        self.export_button = gtk.Button(_("Export"))
        self.export_button.connect('clicked', self.do_export)

        sensitive = False
        for url, feed in self.applet.feeds.items():
            if isinstance(feed, classes.WebFeed):
                sensitive = True
                break
        self.export_button.set_sensitive(sensitive)

        buttons_hbox2 = gtk.HButtonBox()
        buttons_hbox2.set_layout(gtk.BUTTONBOX_EDGE)
        buttons_hbox2.pack_end(import_button, False)
        buttons_hbox2.pack_end(self.export_button, False)

        feeds_vbox = gtk.VBox(False, 6)
        feeds_vbox.pack_start(sw)
        feeds_vbox.pack_start(buttons_hbox, False)
        feeds_vbox.pack_start(show_favicons_check, False)
        feeds_vbox.pack_start(self.show_only_new_check, False)
        feeds_vbox.pack_start(buttons_hbox2, False)
        feeds_vbox.set_border_width(12)

        tab_feeds_vbox.pack_start(feeds_vbox)

        #Updating section (enable/disable automatically updating and change how often)
        #Checkbox: Notify for updated feeds
        check_notify = gtk.CheckButton(_("_Notify for updated feeds"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'notify'):
            check_notify.set_active(True)
        check_notify.connect('toggled', self.check_toggled, 'notify')

        #Checkbox: Update automatically
        check_auto = gtk.CheckButton(_("_Update automatically"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'auto_update'):
            check_auto.set_active(True)
        check_auto.connect('toggled', self.check_toggled, 'auto_update')

        #Update every [SpinButton] minutes
        label_auto1 = gtk.Label(_("Update every "))
        label_auto2 = gtk.Label(_(" minutes"))

        interval = self.applet.client.get_int(GROUP_DEFAULT, 'update_interval')
        auto_adj = gtk.Adjustment(interval, 3, 60, 1, 5, 0)
        auto_spin = gtk.SpinButton(auto_adj, 1)
        auto_spin.connect('focus-out-event', self.spin_focusout)

        hbox_auto = gtk.HBox(False, 0)
        hbox_auto.pack_start(label_auto1, False)
        hbox_auto.pack_start(auto_spin, False)
        hbox_auto.pack_start(label_auto2, False)

        keep_unread_check = gtk.CheckButton(_("Keep items unread when updating"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'keep_unread'):
            keep_unread_check.set_active(True)
        keep_unread_check.connect('toggled', self.check_toggled, 'keep_unread')

        auto_vbox = gtk.VBox(False, 6)
        auto_vbox.pack_start(check_notify, False)
        auto_vbox.pack_start(check_auto, False)
        auto_vbox.pack_start(hbox_auto, False)
        auto_vbox.pack_start(keep_unread_check, False)
        auto_vbox.set_border_width(12)

        tab_updating_vbox.pack_start(auto_vbox)

        #Close button in the bottom right corner
        close = gtk.Button(stock=gtk.STOCK_CLOSE)
        close.connect('clicked', self.deleted)

        close_hbox = gtk.HBox(False, 0)
        close_hbox.pack_end(close, False)

        vbox.pack_end(close_hbox, False)

        self.add(vbox)

        self.update_liststore()

        self.show_all()

        self.connect('delete-event', self.deleted)

    def deleted(self, widget, event=None):
        self.hide()
        self.notebook.set_current_page(0)

        return True

    #Feeds section
    def show_add(self, button):
        AddFeed(self)

    def remove_feed(self, button):
        sel = self.treeview.get_selection()
        url = self.liststore[sel.get_selected()[1]][2]

        self.applet.remove_feed(url)

        #This returns True if the iter is still valid
        #(i.e. the removed feed wasn't the bottom one)
        if not self.liststore.remove(sel.get_selected()[1]):
            self.remove_button.set_sensitive(False)

        sensitive = False
        for url, feed in self.applet.feeds.items():
            if isinstance(feed, classes.WebFeed):
                sensitive = True
                break
        self.export_button.set_sensitive(sensitive)

    def selection_changed(self, sel):
        self.remove_button.set_sensitive(bool(sel.get_selected()))

    #Updating section
    def check_toggled(self, check, key):
        self.applet.client.set_value(GROUP_DEFAULT, key, check.get_active())

        #If user had disabled automatically updating and just turned it on now,
        #start the timeout to update
        if key == 'auto_update':
            self.applet.do_timer()

        elif key == 'show_favicons':
            if check.get_active():
                self.applet.show_favicons()
            else:
                self.applet.hide_favicons()

        elif key == 'show_only_new':
            self.applet.show_only_new()

            if self.applet.show_only_new_check is not None:
                self.applet.show_only_new_check.set_active(check.get_active())

    def spin_focusout(self, spin, event):
        self.applet.client.set_value(GROUP_DEFAULT, 'update_interval', int(spin.get_value()))

    def update_liststore(self):
        self.liststore.clear()

        sensitive = False
        for url in self.applet.urls:
            feed = self.applet.feeds[url]

            if isinstance(feed, classes.WebFeed):
                sensitive = True

            pb = self.applet.get_favicon(feed.icon)
            if pb == self.applet.web_image:
                pb = None

            title = [feed.title, _("Loading...")][feed.title == '']

            self.liststore.append([pb, title, url])

        self.export_button.set_sensitive(sensitive)

    def do_import(self, button):
        file_chooser = gtk.FileChooserDialog(_("Open OPML File"), \
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK), \
            action=gtk.FILE_CHOOSER_ACTION_OPEN)
        file_chooser.set_icon_from_file(icon_path)
        response = file_chooser.run()
        filename = file_chooser.get_filename()
        file_chooser.destroy()

        if filename is None:
            return False

        self.applet.load_opml(filename)

    def do_export(self, button):
        file_chooser = gtk.FileChooserDialog(_("Save OPML File"), \
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK), \
            action=gtk.FILE_CHOOSER_ACTION_SAVE)
        file_chooser.set_icon_from_file(icon_path)
        file_chooser.set_do_overwrite_confirmation(True)
        #Note: the following string is used as an exmaple filename
        file_chooser.set_current_name(_("feeds.opml"))
        response = file_chooser.run()
        filename = file_chooser.get_filename()
        file_chooser.destroy()

        if filename is None:
            return False

        initial_text = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<opml version="1.0">',
            '    <head>',
            '        <title>%s</title>' % _("Awn Feeds Applet Items"),
            '    </head>',
            '    <body>']
        each_text = '        <outline title="%s" text="%s" htmlUrl="%s" type="rss" xmlUrl="%s" />'
        end_text = ['    </body>',
            '</opml>']

        feeds_text = []

        for url, feed in self.applet.feeds.items():
            if isinstance(feed, classes.WebFeed):
                title = html_safe(feed.title)
                web_url = html_safe(feed.web_url)
                url = html_safe(feed.url)
                feeds_text.append(each_text % (title, title, web_url, url))

        fp = open(filename, 'w+')
        fp.write('\n'.join(initial_text + feeds_text + end_text))
        fp.close()

class AddFeed(gtk.Window):
    prefs = None
    icon_theme = gtk.icon_theme_get_default()
    got_results = False
    num = 0

    def __init__(self, prefs=None, applet=None):
        gtk.Window.__init__(self)

        if prefs is not None:
            self.prefs = prefs
            self.applet = prefs.applet
            self.set_transient_for(prefs)

        elif applet is not None:
            self.applet = applet

        self.google_source = None
        for source in self.applet.feeds.values():
            if isinstance(source, classes.GoogleFeed):
                self.google_source = source
                break

        self.site_images = {}

        self.set_border_width(12)
        self.set_title(_("Add Feed"))
        self.set_icon_from_file(icon_path)

        #Source: label and radio buttons
        source_label = gtk.Label(_("Source:"))
        source_label.set_alignment(1.0, 0.0)

        source_vbox = gtk.VBox(False, 3)

        #Search via Google Reader
        pb = self.icon_theme.load_icon('search', 16, 0)
        pb = classes.get_16x16(pb)

        search_radio = gtk.RadioButton(None)
        search_radio.add(self.get_radio_hbox(pb, _("Search")))
        if not self.google_source:
            search_radio.set_sensitive(False)
            search_radio.set_tooltip_text(_("You must sign in to a Google service to search for feeds."))

        #Regular RSS/Atom feed
        try:
            pb = self.icon_theme.load_icon('application-rss+xml', 16, 0)
            pb = classes.get_16x16(pb)
        except:
            pb = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, 16, 16)
        webfeed_radio = gtk.RadioButton(search_radio, None)
        webfeed_radio.add(self.get_radio_hbox(pb, _("RSS/Atom")))

        #Google (Reader and Wave)
        pb = self.applet.get_favicon('www.google.com', True)

        google_radio = gtk.RadioButton(search_radio, None)
        google_radio.add(self.get_radio_hbox(pb, classes.GoogleFeed.title, 'www.google.com'))

        #Google Reader (CheckButton)
        pb = get_greader_icon()

        self.greader_check = gtk.CheckButton()
        self.greader_check.add(self.get_radio_hbox(pb, classes.GoogleReader.title, 'google-reader'))
        self.greader_check.set_active(True)
        self.greader_check.connect('toggled', self.check_toggled)

        #Google Wave
        pb = self.applet.get_favicon('wave.google.com', True)

        self.gwave_check = gtk.CheckButton()
        self.gwave_check.add(self.get_radio_hbox(pb, classes.GoogleWave.title, 'wave.google.com'))
        self.gwave_check.connect('toggled', self.check_toggled)

        google_vbox = gtk.VBox(False, 3)
        google_vbox.pack_start(self.greader_check, False)
        google_vbox.pack_start(self.gwave_check, False)
        google_vbox.show_all()

        self.google_align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
        self.google_align.set_padding(0, 0, 12, 0)
        self.google_align.add(google_vbox)
        self.google_align.set_no_show_all(True)

        #Reddit Inbox
        pb = self.applet.get_favicon('www.reddit.com', True)

        reddit_radio = gtk.RadioButton(search_radio, None)
        reddit_radio.add(self.get_radio_hbox(pb, classes.Reddit.title, 'www.reddit.com'))

        #Twitter Timeline and/or Replies
        pb = gtk.gdk.pixbuf_new_from_file_at_size(twitter_path, 16, 16)

        twitter_radio = gtk.RadioButton(search_radio, None)
        twitter_radio.add(self.get_radio_hbox(pb, _("Twitter")))

        self.twitter_timeline_check = gtk.CheckButton(_("Timeline"))
        self.twitter_timeline_check.set_active(True)
        self.twitter_timeline_check.connect('toggled', self.check_toggled)
        self.twitter_timeline_check.show()

        self.twitter_replies_check = gtk.CheckButton(_("Replies"))
        self.twitter_replies_check.connect('toggled', self.check_toggled)
        self.twitter_replies_check.show()

        twitter_vbox = gtk.VBox(False, 3)
        twitter_vbox.pack_start(self.twitter_timeline_check, False)
        twitter_vbox.pack_start(self.twitter_replies_check, False)
        twitter_vbox.show_all()

        self.twitter_align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
        self.twitter_align.set_padding(0, 0, 12, 0)
        self.twitter_align.add(twitter_vbox)
        self.twitter_align.set_no_show_all(True)

        num = 0
        for widget in (search_radio, webfeed_radio, google_radio, self.google_align, reddit_radio,
            twitter_radio, self.twitter_align):
            if isinstance(widget, gtk.RadioButton):
                widget.connect('toggled', self.radio_toggled)
                widget.num = num
                num += 1

            source_vbox.pack_start(widget, False, False, 0)

        source_hbox = gtk.HBox(False, 6)
        source_hbox.pack_start(source_label, False, False)
        source_hbox.pack_start(source_vbox)

        #"Search for" label and entry
        search_label = gtk.Label(_("Search for"))
        search_label.set_alignment(1.0, 0.5)
        search_label.show()

        self.search_entry = gtk.Entry()
        self.search_entry.show()
        self.search_entry.connect('changed', self.entry_changed)

        self.search_hbox = gtk.HBox(False, 6)
        self.search_hbox.pack_start(search_label, False)
        self.search_hbox.pack_start(self.search_entry)
        self.search_hbox.set_no_show_all(True)

        #URL: label and entry
        url_label = gtk.Label(_("URL:"))
        url_label.set_alignment(1.0, 0.5)
        url_label.show()

        self.url_entry = gtk.Entry()
        self.url_entry.show()
        self.url_entry.connect('changed', self.entry_changed)

        self.url_hbox = gtk.HBox(False, 6)
        self.url_hbox.pack_start(url_label, False, False)
        self.url_hbox.pack_start(self.url_entry)
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

        #Feed search by [Google Reader] message
        pb = get_greader_icon()
        image = awn.Image()
        image.set_from_pixbuf(pb)
        image.set_size_request(16, 16)
        self.search_throbber = awn.OverlayThrobber()
        self.search_throbber.props.scale = 1.0
        self.search_throbber.props.active = False
        image.add_overlay(self.search_throbber)

        image_align = gtk.Alignment(0.5, 0.5, 0.0, 0.0)
        image_align.add(image)

        label = gtk.Label(_("Feed search by "))
        button = gtk.LinkButton(reader_url, _("Google Reader"))

        image.show()
        image_align.show()
        label.show()
        button.show()

        hbox = gtk.HBox()
        hbox.pack_start(image_align, False, False, 6)
        hbox.pack_start(label, False)
        hbox.pack_start(button, False)
        hbox.show()

        self.search_msg = gtk.HBox()
        self.search_msg.pack_start(hbox, True, False)
        self.search_msg.set_no_show_all(True)

        #Results VBox and ScrolledWindow for Feed Search
        self.results_vbox = gtk.VBox(False, 3)
        self.results_vbox.show()

        self.results_sw = gtk.ScrolledWindow()
        self.results_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.results_sw.add_with_viewport(self.results_vbox)
        self.results_sw.set_no_show_all(True)

        #Cancel and Add buttons
        cancel = gtk.Button(stock=gtk.STOCK_CLOSE)
        cancel.connect('clicked', self.close)

        self.add_button = gtk.Button(stock=gtk.STOCK_ADD)
        self.add_button.set_flags(gtk.CAN_DEFAULT)
        self.add_button.set_sensitive(False)
        self.add_button.set_no_show_all(True)
        self.add_button.connect('clicked', self.almost_add_feed)

        #If signed in to Google Reader
        self.search_button = gtk.Button(_("_Search"))
        image = gtk.image_new_from_icon_name('search', gtk.ICON_SIZE_BUTTON)
        self.search_button.set_image(image)
        self.search_button.set_flags(gtk.CAN_DEFAULT)
        self.search_button.set_sensitive(False)
        self.search_button.set_no_show_all(True)
        self.search_button.connect('clicked', self.do_search)

        if self.google_source is not None:
            self.search_button.show()
            self.search_hbox.show()
            self.search_msg.show()

        else:
            self.add_button.show()
            self.url_hbox.show()
            webfeed_radio.set_active(True)

        button_hbox = gtk.HBox(False, 6)
        button_hbox.pack_end(self.add_button, False, False)
        button_hbox.pack_end(self.search_button, False, False)
        button_hbox.pack_end(cancel, False, False)

        main_vbox = gtk.VBox(False, 6)
        main_vbox.pack_start(source_hbox, False, False)
        main_vbox.pack_start(self.search_hbox, False, False)
        main_vbox.pack_start(self.url_hbox, False, False)
        main_vbox.pack_start(self.user_hbox, False, False)
        main_vbox.pack_start(self.pass_hbox, False, False)
        main_vbox.pack_start(self.search_msg, False, False)
        main_vbox.pack_start(self.results_sw)
        main_vbox.pack_end(button_hbox, False, False)
        main_vbox.show_all()

        self.add(main_vbox)
        self.add_button.grab_default()

        #Make the labels the same size
        sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        sg.add_widget(source_label)
        sg.add_widget(search_label)
        sg.add_widget(url_label)
        sg.add_widget(user_label)
        sg.add_widget(pass_label)

        #Make the buttons the same size
        sg = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        sg.add_widget(cancel)
        sg.add_widget(self.add_button)
        sg.add_widget(self.search_button)

        self.show_all()

        #Update any downloaded favicons if necessary
        for siteid in ('www.google.com', 'google-reader', 'wave.google.com', 'www.reddit.com'):
            self.applet.fetch_favicon(self.fetched_favicon, siteid, siteid)

    #The favicon was fetched
    def fetched_favicon(self, siteid, data):
        self.applet.favicons[siteid] = long(time.time())

        fp = open(os.path.join(cache_dir, siteid + '.ico'), 'w+')
        fp.write(data)
        fp.close()

        pb = self.applet.get_favicon(siteid, True)

        if siteid in self.site_images:
            self.site_images[siteid].set_from_pixbuf(pb)

    #Add button clicked
    def almost_add_feed(self, button):
        #URL for RSS/Atom
        if self.num == 1:
            url = self.url_entry.get_text()

            self.applet.add_feed(url)

        #Signing in to Google Reader or Reddit
        else:
            username = self.user_entry.get_text()
            password = self.pass_entry.get_text()

            #Google
            if self.num == 2:
                if self.greader_check.get_active():
                    self.applet.add_feed('google-reader-' + username, None, username, password)

                if self.gwave_check.get_active():
                    self.applet.add_feed('google-wave-' + username, None, username, password)

            #Reddit
            if self.num == 3:
                self.applet.add_feed('reddit-' + username, None, username, password)

            elif self.num == 4:
                timeline = self.twitter_timeline_check.get_active()
                replies = self.twitter_replies_check.get_active()

                if timeline and replies:
                    self.applet.add_feed('twitter-both-' + username, None, username, password)

                elif timeline:
                    self.applet.add_feed('twitter-timeline-' + username, None, username, password)

                elif replies:
                    self.applet.add_feed('twitter-replies-' + username, None, username, password)

        if self.prefs:
            self.prefs.update_liststore()

        self.destroy()

    def entry_changed(self, entry):
        #RSS/Atom or Search
        if entry == self.search_entry:
            self.do_sensitive(self.search_button, (entry, ))

        elif entry == self.url_entry:
            self.do_sensitive(self.add_button, (entry, ))

        elif self.num == 2:
            self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry),
                (self.greader_check, self.gwave_check))

        elif self.num == 4:
            self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry),
                (self.twitter_timeline_check, self.twitter_replies_check))

        else:
            self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry))

    def radio_toggled(self, radio):
        if not radio.get_active():
            return False

        self.num = radio.num

        if self.num == 0:
            self.hide_widgets()
            self.search_button.show()
            self.search_hbox.show()
            self.search_msg.show()

            self.do_sensitive(self.search_button, (self.search_entry, ))

            if self.got_results:
                self.results_sw.show()

        elif self.num == 1:
            self.hide_widgets()
            self.add_button.show()
            self.url_hbox.show()

            self.do_sensitive(self.add_button, (self.url_entry, ))

        elif self.num in (2, 3, 4):
            self.hide_widgets()
            self.add_button.show()
            self.user_hbox.show()
            self.pass_hbox.show()

            if self.num == 2:
                self.google_align.show()

                self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry),
                    (self.greader_check, self.gwave_check))

            elif self.num == 4:
                self.twitter_align.show()

                self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry),
                    (self.twitter_timeline_check, self.twitter_replies_check))

            else:
                self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry))

    def check_toggled(self, check):
        if check in (self.greader_check, self.gwave_check):
            self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry),
                (self.greader_check, self.gwave_check))

        elif check in (self.twitter_timeline_check, self.twitter_replies_check):
            self.do_sensitive(self.add_button, (self.user_entry, self.pass_entry),
                (self.twitter_timeline_check, self.twitter_replies_check))

    def close(self, button):
        self.destroy()

    def do_search(self, button):
        #Clear the results vbox
        for child in self.results_vbox.get_children():
            child.destroy()

        query = self.search_entry.get_text()
        self.search_throbber.props.active = True
        self.google_source.get_search_results(query, self.got_search, self.search_error)

    def search_error(self, *args):
        self.got_results = False
        self.search_throbber.props.active = False

        image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)

        label = gtk.Label(_("There was an error while searching.\nPlease try again later."))

        hbox = gtk.HBox(False, 6)
        hbox.set_border_width(6)
        hbox.pack_start(image, False)
        hbox.pack_start(label, False)

        #Center the box
        hboxbox = gtk.HBox(False, 0)
        hboxbox.pack_start(hbox, True, False)
        self.results_vbox.pack_start(hboxbox, False)

        self.results_sw.show()
        self.results_vbox.show_all()


    def got_search(self, results):
        hsep = None
        self.got_results = True
        self.search_throbber.props.active = False

        for result in results:
            if result['url'] not in self.applet.urls:
                add = gtk.Button(stock=gtk.STOCK_ADD)
                add.url = result['url']
                add.connect('clicked', self.add_search_result)

                add_vbox = gtk.VBox(False, 0)
                add_vbox.pack_start(add, True, False)

                label = gtk.Label(result['title'])
                label.set_line_wrap(True)

                hbox = gtk.HBox(False, 6)
                hbox.set_border_width(6)
                hbox.pack_start(add_vbox, False)
                hbox.pack_start(label, False)
                self.results_vbox.pack_start(hbox, False)

                hsep = gtk.HSeparator()
                self.results_vbox.pack_start(hsep, False)

        #Destroy the last hseparator
        if hsep:
            hsep.destroy()

        #No results at all
        else:
            image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)

            label = gtk.Label(_("No results found.\nTry checking your spelling or using different search terms."))
            label.set_line_wrap(True)

            hbox = gtk.HBox(False, 6)
            hbox.pack_start(image, False)
            hbox.pack_start(label, False)

            #Center the box
            hboxbox = gtk.HBox(False, 0)
            hboxbox.pack_start(hbox, True, False)
            self.results_vbox.pack_start(hboxbox, False)

        self.results_sw.set_size_request(300, 200)
        self.results_sw.show()
        self.results_vbox.show_all()

    def add_search_result(self, button):
        button.parent.set_sensitive(False)

        self.applet.add_feed(button.url)

        if self.prefs is not None:
            self.prefs.update_liststore()

    def hide_widgets(self):
        self.search_button.hide()
        self.search_hbox.hide()
        self.search_msg.hide()

        self.add_button.hide()
        self.url_hbox.hide()
        self.user_hbox.hide()
        self.pass_hbox.hide()

        self.results_sw.hide()

        self.google_align.hide()
        self.twitter_align.hide()

    #All entries need to have non-empty text
    #At least one check needs to be active
    def do_sensitive(self, button, entries=[], checks=[]):
        button.set_sensitive(True)
        for entry in entries:
            if entry.get_text().strip() == '':
                button.set_sensitive(False)

                return

        if len(checks) == 0:
            return

        for check in checks:
            if check.get_active():
                return

        button.set_sensitive(False)

    def get_radio_hbox(self, pb, text, siteid=None):
        image = gtk.image_new_from_pixbuf(pb)

        if siteid is not None:
            self.site_images[siteid] = image

        label = gtk.Label(text)

        hbox = gtk.HBox(False, 3)
        hbox.pack_start(image, False)
        hbox.pack_start(label, False)

        return hbox

#Try the downloaded favicon first. If it doesn't work, use the blue RSS icon
def get_greader_icon():
    try:
        pb = gtk.gdk.pixbuf_new_from_file_at_size(greader_ico, 16, 16)
    except:
        pb = gtk.gdk.pixbuf_new_from_file_at_size(greader_path, 16, 16)

    return pb

def html_safe(s):
    s = s.replace('&', '&amp;').replace('<', '&lt;')
    s = s.replace('>', '&gt;').replace('"', '&quot;')

    return s
