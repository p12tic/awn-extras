#! /usr/bin/python
#
# Copyright (c) 2009 Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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

from desktopagnostic.config import GROUP_DEFAULT
import awn
from awn.extras import defs
from awn.extras import awnlib

APP = "awn-extras-applets"
gettext.bindtextdomain(APP, defs.GETTEXTDIR)
gettext.textdomain(APP)
_ = gettext.gettext

icon_path = '%s/share/avant-window-navigator/applets/feeds/icons/awn-feeds.svg'
icon_path = icon_path % defs.PREFIX

greader_path = '%s/share/avant-window-navigator/applets/feeds/icons/awn-feeds-greader.svg'
greader_path = greader_path % defs.PREFIX

config_path = '%s/.config/awn/applets/feeds.txt' % os.environ['HOME']

feed_search_url = 'http://www.google.com/reader/directory/search?'

reader_url = 'http://www.google.com/reader/'


class Prefs(gtk.Window):
    def __init__(self, applet):
        self.applet = applet

        gtk.Window.__init__(self)
        self.set_title(_("Feeds Applet Preferences"))
        self.set_icon_from_file(icon_path)
        self.set_border_width(12)

        vbox = gtk.VBox(False, 6)

        #Feeds: Add/Remove, with a TreeView for displaying
        feeds_title_label = gtk.Label()
        feeds_title_label.set_markup('<b>' + _("Feeds") + '</b>')
        feeds_title_label.set_alignment(0.0, 0.5)

        vbox.pack_start(feeds_title_label, False)

        self.liststore = gtk.ListStore(str, str)

        self.update_liststore()

        renderer = gtk.CellRendererText()

        column = gtk.TreeViewColumn(' ')
        column.pack_start(renderer, True)
        column.add_attribute(renderer, 'markup', 0)

        self.treeview = gtk.TreeView(self.liststore)
        self.treeview.append_column(column)
        self.treeview.set_headers_visible(False)
        self.treeview.get_selection().connect('changed', self.selection_changed)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.treeview)
        sw.set_size_request(-1, 125)

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

        feeds_vbox = gtk.VBox(False, 6)
        feeds_vbox.pack_start(sw, False)
        feeds_vbox.pack_start(buttons_hbox, False)

        feeds_align = gtk.Alignment(0.0, 0.5, 1.0, 1.0)
        feeds_align.set_padding(0, 0, 12, 0)
        feeds_align.add(feeds_vbox)

        vbox.pack_start(feeds_align, False)

        #Updating section (enable/disable automatically updating and change how often)
        auto_title_label = gtk.Label()
        auto_title_label.set_markup('<b>' + _("Updating") + '</b>')
        auto_title_label.set_alignment(0.0, 0.5)

        vbox.pack_start(auto_title_label, False)

        #Checkbox: Notify for updated feeds
        check_notify = gtk.CheckButton(_("_Notify for updated feeds"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'notify'):
            check_notify.set_active(True)
        check_notify.connect('toggled', self.check_toggled, 'notify')

        #Checkbox: Update automatically
        check_auto = gtk.CheckButton(_("_Update automatically"))
        if self.applet.client.get_bool(GROUP_DEFAULT, 'auto_update'):
            check_auto.set_active(True)
        check_notify.connect('toggled', self.check_toggled, 'auto_update')

        #Update every [SpinButton] minutes
        label_auto1 = gtk.Label(_("Update every "))
        label_auto2 = gtk.Label(_(" minutes"))

        interval = self.applet.client.get_int(GROUP_DEFAULT, 'update_interval')
        auto_adj = gtk.Adjustment(interval, 3, 60, 1, 5, 1)
        auto_spin = gtk.SpinButton(auto_adj, 1)
        auto_spin.connect('focus-out-event', self.spin_focusout)

        hbox_auto = gtk.HBox(False, 0)
        hbox_auto.pack_start(label_auto1, False)
        hbox_auto.pack_start(auto_spin, False)
        hbox_auto.pack_start(label_auto2, False)

        auto_vbox = gtk.VBox(False, 6)
        auto_vbox.pack_start(check_notify, False)
        auto_vbox.pack_start(check_auto, False)
        auto_vbox.pack_start(hbox_auto, False)

        auto_align = gtk.Alignment(0.0, 0.5, 1.0, 1.0)
        auto_align.set_padding(0, 0, 12, 0)
        auto_align.add(auto_vbox)

        vbox.pack_start(auto_align, False)

        #Close button in the bottom right corner
        close = gtk.Button(stock=gtk.STOCK_CLOSE)
        close.connect('clicked', self.close_clicked)

        close_hbox = gtk.HBox(False, 0)
        close_hbox.pack_end(close, False)

        vbox.pack_end(close_hbox, False)

        #HSeparator
        hsep = gtk.HSeparator()
        vbox.pack_end(hsep, False)

        self.add(vbox)

        self.show_all()

    #Feeds section
    def show_add(self, button):
        AddFeed(self)

    def remove_feed(self, button):
        sel = self.treeview.get_selection()
        url = self.liststore[sel.get_selected()[1]][1]

        self.applet.remove_feed(url)

        #This returns True if the iter is still valid
        #(i.e. the removed feed wasn't the bottom one)
        if not self.liststore.remove(sel.get_selected()[1]):
            self.remove_button.set_sensitive(False)

    def selection_changed(self, sel):
        self.remove_button.set_sensitive(bool(sel.get_selected()))

    #Updating section
    def check_toggled(self, check, key):
        self.applet.client.set_value(GROUP_DEFAULT, key, check.get_active())

        #If user had disabled automatically updating and just turned it on now,
        #start the timeout to update
        if key == 'auto_update':
            self.applet.do_timer()

    def spin_focusout(self, spin, event):
        self.client.set_value(GROUP_DEFAULT, 'update_interval', spin.get_value())

    #Etc...
    def close_clicked(self, button):
        self.destroy()

    def update_liststore(self):
        self.liststore.clear()

        for url in self.applet.urls:
            if url == 'google-reader':
                self.liststore.append([_("Google Reader"), url])

            else:
                try:
                    self.liststore.append([self.applet.feeds[url].feed.title, url])

                except:
                    self.liststore.append([url, url])

class AddFeed(gtk.Window):
    prefs = None
    def __init__(self, prefs=None, applet=None):
        gtk.Window.__init__(self)

        if prefs is not None:
            self.prefs = prefs
            self.applet = prefs.applet
            self.set_transient_for(prefs)

        elif applet is not None:
            self.applet = applet

        self.set_border_width(12)
        self.set_title(_("Add Feed"))
        self.set_icon_from_file(icon_path)

        #Source: label and combo box
        source_label = gtk.Label(_("Source:"))
        source_label.set_alignment(1.0, 0.5)

        #TODO: This would only allow one Google Reader instance
        #Change?
        source_combo = gtk.combo_box_new_text()
        if self.applet.SID != '':
            source_combo.append_text(_("Feed Search"))
        source_combo.append_text(_("RSS/Atom"))
        if 'google-reader' not in self.applet.urls:
            source_combo.append_text(_("Google Reader"))
        source_combo.set_active(0)
        source_combo.connect('changed', self.combo_changed)
        self.combo = source_combo

        source_hbox = gtk.HBox(False, 6)
        source_hbox.pack_start(source_label, False, False)
        source_hbox.pack_start(source_combo)

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
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(greader_path, 16, 16)
        image = gtk.image_new_from_pixbuf(pixbuf)
        label = gtk.Label(_("Feed search by "))
        button = gtk.LinkButton(reader_url, _("Google Reader"))

        image.show()
        label.show()
        button.show()

        hbox = gtk.HBox()
        hbox.pack_start(image, False, False, 6)
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

        if self.applet.SID != '':
            self.search_button.show()
            self.search_hbox.show()
            self.search_msg.show()

        else:
            self.add_button.show()
            self.url_hbox.show()

        button_hbox = gtk.HBox(False, 6)
        button_hbox.pack_end(self.add_button, False, False)
        button_hbox.pack_end(self.search_button, False, False)
        button_hbox.pack_end(cancel, False, False)

        self.widget = gtk.VBox(False, 6)
        self.widget.pack_start(source_hbox, False, False)
        self.widget.pack_start(self.search_hbox, False, False)
        self.widget.pack_start(self.url_hbox, False, False)
        self.widget.pack_start(self.user_hbox, False, False)
        self.widget.pack_start(self.pass_hbox, False, False)
        self.widget.pack_start(self.search_msg, False, False)
        self.widget.pack_start(self.results_sw)
        self.widget.pack_start(button_hbox, False, False)
        self.widget.show_all()

        self.add(self.widget)
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

    def almost_add_feed(self, button):
        active = self.combo.get_active()

        #URL for RSS/Atom
        if (self.applet.SID != '' and active == 1) or (self.applet.SID == '' and active == 0):
            url = self.url_entry.get_text()

            self.applet.add_feed(url)

        #Signing in to Google Reader
        elif self.applet.SID == '' and active == 1:
            username = self.user_entry.get_text()
            password = self.pass_entry.get_text()

            self.applet.get_google_key(username, password)

            self.applet.add_feed('google-reader')

        self.hide()

        if self.prefs:
            self.prefs.update_liststore()

    def entry_changed(self, entry):
        #Feed Search
        if entry == self.search_entry:
            self.search_button.set_sensitive((entry.get_text().replace(' ', '') != ''))

        #RSS/Atom by URL
        elif entry == self.url_entry:
            self.add_button.set_sensitive((entry.get_text().replace(' ', '') != ''))

        #Google Reader
        else:
            if self.user_entry.get_text().replace(' ', '') != '':
                if self.pass_entry.get_text().replace(' ', '') != '':
                    self.add_button.set_sensitive(True)

                else:
                    self.add_button.set_sensitive(False)

            else:
                self.add_button.set_sensitive(False)

    def combo_changed(self, combo):
        active = combo.get_active()

        #Logged in to Google Reader
        if self.applet.SID != '':
            #Feed Search through Google Reader
            if active == 0:
                self.search_button.show()
                self.search_hbox.show()
                self.search_msg.show()
                self.add_button.hide()
                self.url_hbox.hide()
                self.user_hbox.hide()
                self.pass_hbox.hide()

                if self.search_entry.get_text().replace(' ', '') != '':
                    self.search_button.set_sensitive(True)

                else:
                    self.search_button.set_sensitive(False)

            #URL for RSS/Atom feed
            elif active == 1:
                self.search_button.hide()
                self.search_hbox.hide()
                self.search_msg.hide()
                self.results_sw.hide()
                self.add_button.show()
                self.url_hbox.show()

                if self.url_entry.get_text().replace(' ', '') != '':
                    self.add_button.set_sensitive(True)

                else:
                    self.add_button.set_sensitive(False)

        #Not logged in to Google Reader
        else:
            #URL for RSS/Atom feed
            if active == 0:
                self.url_hbox.show()
                self.user_hbox.hide()
                self.pass_hbox.hide()

                if self.url_entry.get_text().replace(' ', '') != '':
                    self.add_button.set_sensitive(True)

                else:
                    self.add_button.set_sensitive(False)

            #Signing in to Google Reader
            else:
                self.url_hbox.hide()
                self.user_hbox.show()
                self.pass_hbox.show()

                self.add_button.set_sensitive(False)

                if self.user_entry.get_text().replace(' ', '') != '':
                    if self.pass_entry.get_text().replace(' ', '') != '':
                        self.add_button.set_sensitive(True)
                    

    def close(self, button):
        self.destroy()

    def do_search(self, button):
        #Clear the results vbox
        for child in self.results_vbox.get_children():
            child.destroy()

        search_url = feed_search_url + urllib.urlencode({'q': self.search_entry.get_text()})

        req = urllib2.Request(search_url)
        req.add_header('Cookie', 'SID=' + self.applet.SID)

        try:
            fp = urllib2.urlopen(req)
            f = fp.read()
            fp.close()

        except IOError:
            image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)

            label = gtk.Label(_("There was an error while searching.\nMake sure you have added the Google Reader feed."))

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

            return

        try:
            json = f.split('_DIRECTORY_SEARCH_DATA =')[1].split('</script>')[0].strip()
            json = json.replace(':false', ':False').replace(':true', ':True')
            results = eval(json)['results']

        #Parsing error
        except:
            image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_MENU)

            label = gtk.Label(_("There was an error while searching.\nMake sure you have added the Google Reader feed."))
            label.set_line_wrap(True)

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

            return

        hsep = None

        for result in results:
            #For some reason 'streamid' starts with 'feed/'
            url = result['streamid'][5:]

            #TODO: this is wrong.
            #Some strings have \uxxxx in them, but python sees them as "\\uxxxx"
            #the following line fixes some results, but this sometimes
            #doesn't work or gets a SyntaxError or makes the text even worse.
            #url = eval('u"%s"' % url.replace('"', '\\"'))

            if url not in self.applet.urls:
                add = gtk.Button(stock=gtk.STOCK_ADD)
                add.url = url
                add.connect('clicked', self.add_search_result)

                add_vbox = gtk.VBox(False, 0)
                add_vbox.pack_start(add, True, False)

                #TODO: this is also wrong
                #eval('u"%s"' % result['title'].replace('"', '\\"')))
                label = gtk.Label(result['title'])
                label.set_line_wrap(True)

                hbox = gtk.HBox(False, 6)
                hbox.set_border_width(6)
                hbox.pack_start(add_vbox, False)
                hbox.pack_start(label, False)
                self.results_vbox.pack_start(hbox, False)

                if add.url in self.applet.urls:
                    hbox.set_sensitive(False)

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
