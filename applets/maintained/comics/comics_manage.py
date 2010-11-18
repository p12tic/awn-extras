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
import os

# Symbols used
from gettext import ngettext
from awn.extras import _

# Local
from comics_add import ComicsAdder
from shared import UI_DIR

UI_FILE = os.path.join(UI_DIR, 'manage.ui')


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
        names = self.feeds.feeds.keys()
        names.sort(key=str.lower)
        for feed in names:
            self.model.append(
                (len([w for w in self.__parent.windows
                    if w.feed_name == feed]) > 0,
                feed, self.feeds.feeds[feed].filename))

    def show(self):
        self.manage_window.show()

    ########################################################################
    # Standard python methods                                              #
    ########################################################################

    def __init__(self, parent):
        """Create a new ComicsManage instance."""
        # Connect dialogue events
        self.ui = gtk.Builder()
        self.ui.add_from_file(UI_FILE)
        self.ui.connect_signals(self)

        self.__parent = parent
        self.feeds = parent.feeds

        self.manage_window = self.ui.get_object('manage_window')

        self.model = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)

        self.comics_list = self.ui.get_object('comics_list')
        selection = self.comics_list.get_selection()
        selection.connect('changed', self.on_comics_list_selection_changed)
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        self.comics_list.set_model(self.model)
        # Translators: checkbox to show comic
        self.ui.get_object('toggle_col').set_title(_('Show'))
        self.ui.get_object('name_col').set_title(_('Comic'))

        self.load_feeds()
        x, y = self.comics_list.size_request()
        if x > 475:
            x = 475
        if y > 400:
            y = 400
        self.manage_window.set_default_size(x + 25, y + 100)

    ########################################################################
    # Event hooks                                                          #
    ########################################################################

    def on_comics_list_selection_changed(self, widget):
        rows = self.comics_list.get_selection().count_selected_rows()
        button = self.ui.get_object('remove_button')
        button.set_sensitive(rows > 0)

    def on_feed_toggled(self, widget, path):
        self.model[path][0] = not self.model[path][0]
        self.__parent.toggle_feed(self.model[path][1], self.model[path][0])

    def on_add_button_clicked(self, widget):
        adder = ComicsAdder(self.__parent)
        adder.assistant.set_transient_for(self.manage_window)
        adder.assistant.connect('destroy', self.on_adder_destroy)

    def on_remove_button_clicked(self, widget):
        model, path = self.comics_list.get_selection().get_selected_rows()
        msg = ngettext(
            "Are you sure you want to remove the comic \"%(name)s\"?",
            "Are you sure you want to remove the %(number)d selected comics?",
            len(path)) % {'number': len(path),
            'name': self.model.get_value(self.model.get_iter(path[0]), 1)}
        sec = ngettext(
            "This will remove the comic from your personal comics list.",
            "This will remove these comics from your personal comics list.",
            len(path))
       
        dialog = gtk.MessageDialog(parent=self.manage_window,
                                   flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                   type=gtk.MESSAGE_WARNING,
                                   message_format=msg)
        dialog.format_secondary_markup(sec)
        dialog.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                           gtk.STOCK_REMOVE, gtk.RESPONSE_OK)
        response = dialog.run()
        dialog.destroy()

        if response != gtk.RESPONSE_OK:
            return

        def remove(model, path, iterator):
            feed_name = model.get_value(iterator, 1)
            filename = model.get_value(iterator, 2)
            self.__parent.toggle_feed(feed_name, False)
            try:
                self.feeds.remove_feed(feed_name)
                os.remove(filename)
            except Exception:
                msg = _("Failed to remove '%s'.") % filename
                dialog = gtk.MessageDialog(parent=self.manage_window,
                                          flags=gtk.DIALOG_DESTROY_WITH_PARENT,
                                          type=gtk.MESSAGE_INFO,
                                          buttons=gtk.BUTTONS_CLOSE,
                                          message_format=msg)
                dialog.set_title(_('Error'))
                dialog.run()
                dialog.destroy()
                return

        self.comics_list.get_selection().selected_foreach(remove)
        self.load_feeds()

    def on_close_button_clicked(self, widget):
        self.manage_window.destroy()

    def on_adder_destroy(self, widget):
        self.load_feeds()
