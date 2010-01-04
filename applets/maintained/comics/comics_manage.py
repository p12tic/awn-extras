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


# Libraries used
import gobject
import gtk
from gtk import glade
import os

# Symbols used
from awn.extras import _

# Local
from comics_add import ComicsAdder
from shared import GLADE_DIR

GLADE_FILE = os.path.join(GLADE_DIR, 'manage.glade')


class ComicsManager:
    """A program to add image feeds."""

    __name__ = 'Comics!'
    __version__ = '1.0'
    __author__ = 'Moses'

    ########################################################################
    # Helper methods                                                       #
    ########################################################################

    def load_feeds(self):
        """Load the descriptions of all installed feeds."""
        self.model.clear()

        shared_iterator = self.model.append(None, (_('Shared comics'), ''))
        user_iterator = self.model.append(None, (_('Your comics'), ''))
        for feed_name, feed in self.feeds.feeds.items():
            if os.access(os.path.dirname(feed.filename), os.W_OK):
                self.model.append(user_iterator, (feed_name, feed.filename))
            else:
                self.model.append(shared_iterator, (feed_name, feed.filename))

        self.comics_list.expand_all()

    def show(self):
        self.manage_window.show()

    ########################################################################
    # Standard python methods                                              #
    ########################################################################

    def __init__(self, feeds):
        """Create a new ComicsManage instance."""
        # Connect dialogue events
        self.xml = glade.XML(GLADE_FILE)
        self.xml.signal_autoconnect(self)

        self.feeds = feeds

        self.manage_window = self.xml.get_widget('manage_window')

        self.model = gtk.TreeStore(gobject.TYPE_STRING, gobject.TYPE_STRING)

        self.comics_list = self.xml.get_widget('comics_list')
        selection = self.comics_list.get_selection()
        selection.connect('changed', self.on_comics_list_selection_changed)
        cr = gtk.CellRendererText()
        column = gtk.TreeViewColumn()
        column.pack_start(cr)
        column.set_attributes(cr, text=0)
        self.comics_list.append_column(column)
        self.comics_list.set_model(self.model)

        self.load_feeds()

    ########################################################################
    # Event hooks                                                          #
    ########################################################################

    def on_comics_list_selection_changed(self, widget):
        model, iterator = self.comics_list.get_selection().get_selected()
        if iterator:
            directory = os.path.dirname(self.model.get_value(iterator, 1))
            self.xml.get_widget('remove_button').set_sensitive(
                os.access(directory, os.W_OK))
        else:
            self.xml.get_widget('remove_button').set_sensitive(False)

    def on_add_button_clicked(self, widget):
        adder = ComicsAdder(self.feeds)
        adder.assistant.set_transient_for(self.manage_window)
        adder.assistant.connect('destroy', self.on_adder_destroy)

    def on_remove_button_clicked(self, widget):
        model, iterator = self.comics_list.get_selection().get_selected()
        feed_name = self.model.get_value(iterator, 0)
        filename = self.model.get_value(iterator, 1)
        try:
            self.feeds.remove_feed(feed_name)
            os.remove(filename)
        except:
            msg = _('Failed to remove <i>%s</i>.') % filename
            dialog = gtk.MessageDialog(parent=self.manage_window,
                                       flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                       type=gtk.MESSAGE_INFO,
                                       buttons=gtk.BUTTONS_CLOSE,
                                       message_format=msg)
            dialog.set_title(_('Error'))
            dialog.run()
            dialog.hide()
            del dialog
            return
        self.load_feeds()

    def on_close_button_clicked(self, widget):
        self.manage_window.destroy()

    def on_adder_destroy(self, widget):
        self.load_feeds()
