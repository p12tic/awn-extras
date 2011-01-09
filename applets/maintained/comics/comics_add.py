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

from __future__ import with_statement

# Libraries used
import gobject
import gtk
import os
import re
import tempfile

# Symbols used
from awn.extras import _

# Local
from downloader import Downloader
from feed import FeedContainer
from feed.basic import Feed, NAME, URL, PLUGIN
from feed.settings import Settings
from feed.rss import IMG_INDEX
from shared import (UI_DIR, USER_FEEDS_DIR, SYS_FEEDS_DIR)

UI_FILE = os.path.join(UI_DIR, 'add.ui')

URL_RE = re.compile('(?:http)|(?:https)://.*?/.*', re.IGNORECASE)


class ComicsAdder:
    """A program to add image feeds."""

    __name__ = 'Comics!'
    __version__ = '1.0'
    __author__ = 'Moses'

    ########################################################################
    # Helper methods                                                       #
    ########################################################################

    def process_error(self, result):
        label = self.ui.get_object('intro_label')
        if result == Feed.DOWNLOAD_FAILED:
            label.set_text(_('''\
Failed to download %s. Press "next" to try again.''') % self.url)
            self.assistant.set_current_page(0)
            return False

        elif result == Feed.DOWNLOAD_NOT_FEED:
            label.set_text(_('''\
The URL is not a valid comic feed. Press "next" to try again'''))
            self.assistant.set_current_page(0)
            return False

        return True

    def load_sys_list(self):
        if not self.sys:
            self.sys = FeedContainer()
            self.sys.load_directory(SYS_FEEDS_DIR)
        self.sys_model.clear()
        names = self.sys.feeds.keys()
        names.sort(key=str.lower)
        for feed in names:
            self.sys_model.append((feed, self.sys.feeds[feed].filename))

    def on_screen(self):
        return len(self.assistant) != 0

    def present(self):
        self.assistant.present()

    ########################################################################
    # Standard python methods                                              #
    ########################################################################

    def __init__(self, parent):
        """Create a new ComicsAdder instance."""
        self.__parent = parent
        self.feeds = parent.feeds
        self.name = ''
        self.url = ''
        self.feed = None
        self.__update = None

        # Connect dialogue events
        self.ui = gtk.Builder()
        self.ui.add_from_file(UI_FILE)
        self.ui.connect_signals(self)
        self.assistant = self.ui.get_object('add_assistant')
        self.image_list = self.ui.get_object('image_list')

        self.sys = None
        self.sys_list = self.ui.get_object('pre_list')
        self.sys_model = gtk.ListStore(gobject.TYPE_STRING,
                                       gobject.TYPE_STRING)
        self.sys_col = self.ui.get_object('pre_col')
        self.load_sys_list()
        self.sys_list.set_model(self.sys_model)

        self.from_list = True
        self.radio_button = self.ui.get_object('list_radio')
        self.radio_button.set_active(self.from_list)

        self.model = gtk.ListStore(gobject.TYPE_PYOBJECT, gtk.gdk.Pixbuf)
        self.image_list.set_model(self.model)

        selection = self.sys_list.get_selection()
        selection.connect('changed', self.on_list_selection_changed)
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        # Show window
        self.assistant.set_page_complete(self.ui.get_object('intro_page'),
            True)
        self.assistant.set_page_complete(self.ui.get_object('last_page'),
            True)
        self.assistant.show()

    ########################################################################
    # Event hooks                                                          #
    ########################################################################

    def on_add_assistant_close(self, widget):
        if self.__update:
            self.feed.disconnect(self.__update)
        self.assistant.destroy()

    def on_add_assistant_cancel(self, widget):
        if self.__update:
            self.feed.disconnect(self.__update)
        self.assistant.destroy()

    def on_add_assistant_apply(self, widget):
        try:
            os.mkdir(USER_FEEDS_DIR)
        except Exception:
            pass

        if self.from_list:
            model, paths = self.sys_list.get_selection().get_selected_rows()
            for path in paths:
                self.name = model.get_value(model.get_iter(path), 0)
                src = model.get_value(model.get_iter(path), 1)
                filename = USER_FEEDS_DIR + src[len(SYS_FEEDS_DIR):]
                with open(src, 'r') as fp:
                    src_content = fp.read()
                try:
                    with open(filename, 'r') as fp:
                        f = fp.read()
                except IOError:
                    f = None
                if f:
                    if cmp(src_content, f) == 0:
                        continue
                    msg = _("Overwrite comic \"%s\"?") % self.name
                    sec = _(
                 "This comic is already installed with different settings.")
                    dialog = gtk.MessageDialog(parent=self.assistant,
                                   flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_WARNING,
                                   message_format=msg)
                    dialog.format_secondary_markup(sec)
                    if path != paths[-1]:
                        dialog.add_buttons(
                                       gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
                    dialog.add_buttons(gtk.STOCK_NO, gtk.RESPONSE_NO,
                                       gtk.STOCK_YES, gtk.RESPONSE_YES)
                    response = dialog.run()
                    dialog.destroy()
                    if response == gtk.RESPONSE_NO:
                        continue
                    if response != gtk.RESPONSE_YES:
                        return
                with open(filename, 'w') as fp:
                    fp.write(src_content)
                self.feeds.add_feed(filename)
                self.feeds.update()
                self.__parent.toggle_feed(self.name, True)
        else:
            self.name = self.ui.get_object('name_entry').get_text()
            f, filename = tempfile.mkstemp('.feed', '', USER_FEEDS_DIR, True)
            os.close(f)
            settings = Settings(filename)
            settings.description = 'Automatically generated by comics'
            settings[NAME] = self.name
            settings[URL] = self.url
            settings[IMG_INDEX] = self.image[0] + 1
            settings.comments[IMG_INDEX] = \
                'The index of the image in the HTML-code'
            if self.feed.__module__.startswith('feed.plugins.'):
                settings[PLUGIN] = self.feed.__module__[13:]
            settings.save()
            self.feeds.add_feed(filename)
            self.feeds.update()
            self.__parent.toggle_feed(self.name, True)

    def on_add_assistant_prepare(self, widget, page):
        if page is self.ui.get_object('url_page'):
            if self.from_list:
                self.ui.get_object('list_box').show()
                self.ui.get_object('url_box').hide()
            else:
                self.ui.get_object('list_box').hide()
                self.ui.get_object('url_box').show()

        elif page is self.ui.get_object('wait_page'):
            if self.from_list:
                self.ui.get_object('name_box').hide()
                last_label = self.ui.get_object('last_label')
                last_label.set_markup(_('''\
This guide has finished.\n\
Press "apply" to add the comic.'''))
                self.assistant.set_current_page(4)
            else:
                self.assistant.set_page_complete(page, False)
                self.url = self.ui.get_object('url_entry').get_text()

                self.ui.get_object('wait_label').set_markup(
                    _('Connecting to <i>%s</i>...') % self.url)

                # Download feed
                self.feed = self.feeds.get_feed_for_url(self.url)
                self.__update = self.feed.connect('updated',
                                                  self.on_feed_updated)
                self.feed.update()

    def on_radio_button_toggled(self, widget):
        self.from_list = self.radio_button.get_active()

    def on_url_entry_changed(self, widget):
        text = widget.get_text()
        if not self.from_list:
            self.assistant.set_page_complete(self.ui.get_object('url_page'),
                not URL_RE.match(text) is None)

    def on_list_selection_changed(self, widget):
        if self.from_list:
            self.assistant.set_page_complete(self.ui.get_object('url_page'),
                self.sys_list.get_selection().count_selected_rows() > 0)

    def on_name_entry_changed(self, widget):
        text = widget.get_text()
        self.assistant.set_page_complete(self.ui.get_object('last_page'),
            not text == '')

    def on_image_list_unselect_all(self, widget):
        self.assistant.set_page_complete(self.ui.get_object('image_page'),
            False)

    def on_image_list_selection_changed(self, widget):
        selection = self.image_list.get_selected_items()
        if len(selection) == 1:
            self.assistant.set_page_complete(self.ui.get_object('image_page'),
                True)
            self.image = self.model.get_value(
                self.model.get_iter(selection[0]), 0)
        else:
            self.assistant.set_page_complete(self.ui.get_object('image_page'),
                False)

    def on_feed_updated(self, feed, result):
        if not self.process_error(result):
            return

        self.name = feed.name

        last_label = self.ui.get_object('last_label')
        last_label.set_markup(_('''\
This guide has finished.\n\
You can change the name of this comic. Press "apply" to add it.'''))
        name_entry = self.ui.get_object('name_entry')
        name_entry.set_text(self.name)

        # Can we skip the image page?
        images = feed.get_unique_images()
        if len(images) > 1:
            # Download images for the image list
            self.model.clear()
            for image in images:
                iterator = self.model.append((image, None))
                downloader = Downloader(image[1])
                downloader.connect('completed',
                    self.on_image_download_completed, iterator)
                downloader.download()
            self.ui.get_object('image_page').show()
        else:
            self.ui.get_object('image_page').hide()
            try:
                self.image = images[0]
            except IndexError:
                self.process_error(Feed.DOWNLOAD_NOT_FEED)
                return

        # Complete page
        self.assistant.set_page_complete(self.ui.get_object('wait_page'),
                                         True)
        self.ui.get_object('wait_label').set_markup(
                _('Found <b>%(name)s</b>!\n\n<i>%(description)s</i>')
                % {'name': self.name,
                    'description': self.feed.description})

    def on_image_download_completed(self, o, code, iterator):
        """Update the image list with a newly downloaded image."""
        if code != Downloader.OK:
            self.model.remove(iterator)
        else:
            try:
                pixbuf = gtk.gdk.pixbuf_new_from_file(o.filename)
                self.model.set_value(iterator, 1, pixbuf)
            except Exception:
                self.model.remove(iterator)
            os.remove(o.filename)
