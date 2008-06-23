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


import awn
import awn.extras.AWNLib
import gettext
import gobject
import gtk
import gtk.glade
import locale
import os
import sys
import tempfile

from locale import gettext as _
from os.path import join
from settings import Settings

import comics_add
import comics_manage
import comics_view

from feed import FeedContainer
from shared import SHARE_DIR, USER_DIR, SYS_FEEDS_DIR, USER_FEEDS_DIR, \
	ALT_USER_DIR, GLADE_DIR, PIXMAPS_DIR, LOCALE_DIR, STRIPS_DIR

GLADE_FILE = join(GLADE_DIR, 'main.glade')


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
	
	def create_window(self, filename = None, template = None):
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
		if not feed_name in self.feeds.feeds:
			return
		
		if not visible:
			windows = filter(lambda w: w.feed_name == feed_name, self.windows)
			if not windows:
				return
			
			for window in windows:
				window.close()
				window.destroy()
		
		else:
			template = Settings()
			template['feed_name'] = feed_name
			self.create_window(template = template)
	
	def update_icon(self):
		"""Update the icon of the applet, scaling it if necessary."""
		if self.height != self.icon.get_height():
			self.set_icon(self.icon.scale_simple(self.height, self.height,
				gtk.gdk.INTERP_BILINEAR))
		else:
			self.set_icon(self.icon)
	
	def make_menu(self):
		"""Generate the menu listing the comics."""
		# Generate comics menu
		feed_menu = self.__xml.get_widget('comics_menu')
		feed_menu.foreach(lambda child: feed_menu.remove(child))
		for feed in self.feeds.feeds:
			label = gtk.Label()
			label.set_markup(self.feeds.feeds[feed].name)
			align = gtk.Alignment(xalign = 0.0)
			align.add(label)
			menu_item = gtk.CheckMenuItem()
			menu_item.data = feed
			menu_item.add(align)
			menu_item.set_active(len(filter(lambda w: w.feed_name == feed,
				self.windows)) > 0)
			menu_item.connect('toggled', self.on_comics_toggled)
			feed_menu.append(menu_item)
		feed_menu.show_all()
		self.__xml.get_widget('comics_container').set_sensitive(
			len(self.feeds.feeds) > 0)
		
		return self.__xml.get_widget('menu')
	
	def show_message(self, message, icon_id):
		self.message_label.set_markup(message)
		self.message_icon.set_from_stock(icon_id, gtk.ICON_SIZE_DIALOG)
		self.dialog.show_all()
		gobject.timeout_add(self.DIALOG_DURATION, self.on_dialog_timer)
	
	def __init__(self, uid, orient, height, feeds):
		awn.AppletSimple.__init__(self, uid, orient, height)
		
		self.feeds = feeds
		
		self.height = height
		self.icon = gtk.gdk.pixbuf_new_from_file(join(SHARE_DIR, 'icon.svg'))
		self.update_icon()
		self.notify = awn.extras.AWNLib.Notify(self)
		self.notify.require()
		self.dialog = awn.AppletDialog(self)
		self.dialog.connect('button-press-event', self.on_dialog_button_press)
		
		hbox = gtk.HBox(False)
		self.message_icon = gtk.Image()
		self.message_label = gtk.Label()
		hbox.pack_start(self.message_icon, expand = False, fill = False)
		hbox.pack_end(self.message_label)
		hbox.show_all()
		self.dialog.add(hbox)
		
		self.connect('destroy', self.on_destroy)
		self.connect('button-press-event', self.on_button_press)
		self.connect('scroll-event', self.on_scroll)
		
		self.__xml = gtk.glade.XML(GLADE_FILE)
		self.__xml.signal_autoconnect(self)
		
		self.visible = False
		self.windows = []
		self.window_iterator = BidirectionalIterator(self.windows)
		self.current_window = None
		
		try:
			for filename in filter(lambda f: f.endswith('.strip'),
					os.listdir(STRIPS_DIR)):		
				strip = self.create_window(os.path.join(STRIPS_DIR, filename))
		except OSError:
			return
	
		self.feeds.update()
	
	def on_window_updated(self, widget, title):
		self.notify.send(title,
			_('There is a new strip of %s!') % widget.feed_name,
			os.path.join(SHARE_DIR, 'icon.svg'))
	
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
			menu.popup(None, None, None, event.button, event.time)
		
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
		manager = comics_manage.ComicsManager()
		manager.show()


if __name__ == '__main__':
	# Initialise internationalisation
	locale.setlocale(locale.LC_ALL, '')
	locale.bindtextdomain('comics', LOCALE_DIR)
	locale.textdomain('comics')
	
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
	applet = ComicApplet(awn.uid, awn.orient, awn.height, feeds)
	awn.init_applet(applet)
	applet.show_all()
	
	gtk.main()

