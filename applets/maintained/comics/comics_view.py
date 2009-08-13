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
import cairo
import dbus
import gobject
import gtk
import gtk.glade
import os
import rsvg
import tempfile
import time

# Symbols used
from locale import gettext as _
from math import pi

# Local
from feed import FeedContainer
from feed.basic import URL, TITLE, LINK, DATE, Feed
from downloader import Downloader
from feed.settings import Settings

from widgets import ScalableWindow, WWWLink, Ticker
from shared import *

STRIPS_DIR = USER_DIR
CACHE_FILE = os.path.join(USER_DIR, '%s.cache')
GLADE_FILE = os.path.join(GLADE_DIR, 'view.glade')

BROWSER_COMMAND = 'xdg-open'

session_bus = None


# Constants
TICKER_LINK_SEPARATION = 4
LINK_BORDER = (2, 2, 2, 26)			# The border widths when the link is visible
BORDER = (2, 2, 2, 2)				# The border widths
LINK_BORDER_RADII = (0, 0, 26, 26)	# The radii of the corners when the link is
									# visible
BORDER_RADII = (0, 0, 0, 0)			# The radii of the corners
WINDOW_COLOR = (1.0, 1.0, 1.0)		# The rgb colour of the window
BORDER_COLOR = (0.0, 0.0, 0.0)		# The rgb colour of the border
LINK_FONTSIZE = 10 * 1000			# The size of the font
TICKER_DISTANCE = 8					# The distance from the ticker to the border
COMPIZ_WIDGET = '_COMPIZ_WIDGET'	# The WM atom for a Compiz widget

# Common images
DEFAULT_IMAGE = rsvg.Handle(os.path.join(ICONS_DIR, 'default.svg'))
ERROR_IMAGE = rsvg.Handle(os.path.join(ICONS_DIR, 'error.svg'))


def compiz_widget_set(widget, value):
	"""Sets or unsets the Compiz widget property."""
	if widget.window:
		if value:
			widget.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_UTILITY)
			widget.window.property_change(COMPIZ_WIDGET, 
				gtk.gdk.SELECTION_TYPE_WINDOW, 32, gtk.gdk.PROP_MODE_REPLACE,
					(True,))
		else:
			widget.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)
			widget.window.property_delete(COMPIZ_WIDGET)

def compiz_widget_get(widget):
	if widget.window:
		return widget.window.property_get(COMPIZ_WIDGET, 
			gtk.gdk.SELECTION_TYPE_WINDOW)

def has_widget_layer():
	"""Queries Compiz over DBus whether the Widget plugin is enabled."""
	global session_bus
	
	try:
		if session_bus is None:
			session_bus = dbus.SessionBus()
		return 'widget' in session_bus.get_object('org.freedesktop.compiz',
			'/org/freedesktop/compiz/core/allscreens/active_plugins').get()
	except:
		return False


class ComicsViewer(ScalableWindow):
	"""A program to display image feeds."""
	
	__name__ = 'Comics!'
	__version__ = '1.0'
	__author__ = 'Moses'
	
	__gsignals__ = dict(
		removed = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
		updated = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_STRING,)))
			
	########################################################################
	# Helper methods                                                       #
	########################################################################
	
	def set_visibility(self, visible):
		"""Hides or unhides the window. If Compiz is running and the Widget
		plugin is loaded, the window is sent to the widget layer. Makes sure
		that the window is visible on screen."""
		if visible:
			screen = self.get_screen()
			screen_width, screen_height = (screen.get_width(),
				screen.get_height())
			
			# Show the window first...
			self.show()
			
			x, y = self.get_position()
			x %= screen_width
			if x < 0:
				x += screen_width
			y %= screen_height
			if y < 0:
				y += screen_height
			
			# ...and then move it
			self.move(x, y)
			
			self.__settings['x'] = x
			self.__settings['y'] = y
			
			if has_widget_layer():
				compiz_widget_set(self, False)
		else:
			if has_widget_layer():
				self.show()
				compiz_widget_set(self, True)
			else:
				self.hide()
		
		self.__settings.save()
	
	def close(self):
		self.emit('removed')
		self.__settings.delete()
		self.destroy()
	
	def get_menu_item_name(self, item):
		"""Return the menu item name of item."""
		if item[DATE] > 0:
			tt = time.localtime(item[DATE])
			return time.strftime(_('%A %d %B'), tt)
		else:
			return item[TITLE]
	
	def get_link_name(self, item):
		"""Return the link name of item."""
		return item[TITLE]
	
	def get_link_dimensions(self):
		"""Return the dimensions of the link."""
		if self.__link and self.show_link:
			size = self.__link.rsize
			if -1 in size:
				return (0, 0)
			else:
				return size
		else:
			return (0, 0)
	
	def get_ticker_dimensions(self):
		"""Return the dimensions of the ticker."""
		if self.__ticker:
			return self.__ticker.rsize
		else:
			return (0, 0)
	
	def get_image_dimensions(self):
		"""Return the dimensions of the current image."""
		if self.__pixbuf:
			return (self.__pixbuf.get_width(), self.__pixbuf.get_height())
		elif self.__is_error:
			return ERROR_IMAGE.get_dimension_data()[:2]
		else:
			return DEFAULT_IMAGE.get_dimension_data()[:2]
	
	def get_window_dimensions(self):
		"""Get the required size of the window."""
		l_dim = self.get_link_dimensions()
		t_dim = self.get_ticker_dimensions()
		i_dim = self.get_image_dimensions()
		c_dim = max(i_dim[0],
			l_dim[0] + 2.0 * (t_dim[0] + TICKER_LINK_SEPARATION)), i_dim[1]
		
		return (c_dim[0] + self.__border[0] + self.__border[2],
			c_dim[1] + self.__border[1] + self.__border[3])
	
	def rescale_window(self):
		"""Change the scale of the window so that the window will fit on
		screen."""
		screen = self.get_screen()
		screen_size = screen.get_width(), screen.get_height()
		w_dim = self.canvas_size
		scale = None
		if w_dim[0] > screen_size[0]:
			scale = 0.95 * float(screen_size[0]) / w_dim[0]
		if w_dim[1] > screen_size[1]:
			if not scale or scale > screen_size[1] / w_dim[1]:
				scale = 0.95 * float(screen_size[1]) / w_dim[1]
		if scale:
			self.set_scale(scale)
	
	def update_size(self):
		"""Update the size of the window and place controls."""
		l_dim = self.get_link_dimensions()
		t_dim = self.get_ticker_dimensions()
		i_dim = self.get_image_dimensions()
		c_dim = (max(i_dim[0],
			l_dim[0] + 2.0 * (t_dim[0] + TICKER_LINK_SEPARATION)), i_dim[1])
		w_dim = (c_dim[0] + self.__border[0] + self.__border[2],
			c_dim[1] + self.__border[1] + self.__border[3])
		
		# Resize window
		self.set_canvas_size(w_dim)
		self.rescale_window()
		
		# Place link
		if self.__link:
			self.move_child(self.__link,
				(w_dim[0] - l_dim[0]) / 2,
				w_dim[1] - (self.__border[3] + l_dim[1]) / 2 - 1)
		
		# Place ticker
		if self.__ticker:
			self.move_child(self.__ticker,
				TICKER_DISTANCE,
				w_dim[1] - t_dim[1] - TICKER_DISTANCE)
	
	def select_item(self, item):
		"""Select a strip for downloading."""
		self.__ticker.set_ticking(True)
		if self.__download_id and self.__downloader:
			self.__downloader.disconnect(self.__download_id)
			self.__download_id = None
		self.__downloader = Downloader(item[URL], self.__settings['cache-file'])
		self.__download_id = self.__downloader.connect('completed',
			self.on_download_completed, item)
		self.__downloader.download()
		
	def draw_frame(self, ctx, p1, p2, rad):
		"""Trace a rectangle with rounded corners."""
		ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
		
		# Top-left
		if rad[0] > 0:
			ctx.arc(p1[0] + rad[0], p1[1] + rad[0], rad[0], pi, 3 * pi / 2)
		else:
			ctx.move_to(*p1)
		
		# Top-right
		if rad[1] > 0:
			ctx.arc(p2[0] - rad[1], p1[1] + rad[1], rad[1], 3 * pi / 2, 0)
		else:
			ctx.line_to(p2[0], p1[1])
		
		# Bottom-right
		if rad[2] > 0:
			ctx.arc(p2[0] - rad[2], p2[1] - rad[2], rad[2], 0, pi / 2)
		else:
			ctx.line_to(*p2)
		
		# Bottom-left
		if rad[3] > 0:
			ctx.arc(p1[0] + rad[3], p2[1] - rad[3], rad[3], pi / 2, pi)
		else:
			ctx.line_to(p1[0], p2[1])

		# Close the path to draw the last line
		ctx.close_path()
	
	def draw_window(self, ctx):
		"""Draw the window on which the image is painted."""
		ctx.save()
		
		# Define shape
		w_dim = self.get_window_dimensions()
		self.draw_frame(ctx, (1, 1), (w_dim[0] - 1, w_dim[1] - 1),
			self.__border_radii)
		
		ctx.set_source_rgb(*WINDOW_COLOR)
		ctx.fill_preserve()
		ctx.set_source_rgb(*BORDER_COLOR)
		ctx.stroke()
		
		ctx.restore()
	
	def draw_image(self, ctx):
		"""Draw the image."""
		ctx.save()
		
		w_dim = self.get_window_dimensions()
		i_dim = self.get_image_dimensions()
		x = (w_dim[0] - i_dim[0]) / 2
		
		# Has an image been downloaded?
		if self.__pixbuf:
			dim = self.get_image_dimensions()
			ctx.set_source_pixbuf(self.__pixbuf, x, self.__border[1])
			ctx.rectangle(x, self.__border[1], dim[0], dim[1])
			ctx.clip()
			ctx.paint()
		# Has an error occurred?
		elif self.__is_error:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.translate(x, self.__border[1])
			ERROR_IMAGE.render_cairo(ctx)
		# Otherwise draw the default image
		else:
			ctx.set_operator(cairo.OPERATOR_OVER)
			ctx.translate(x, self.__border[1])
			DEFAULT_IMAGE.render_cairo(ctx)
		
		ctx.restore()
	
	def make_file_type_chooser(self):
		"""Add the possible image types to the file chooser dialog."""
		combo = self.__xml.get_widget('file_format_combo')
		model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING,
			gobject.TYPE_STRING)
		for format in gtk.gdk.pixbuf_get_formats():
			if format['is_writable']:
				text = '%s (*.%s)' % (format['description'],
					format['extensions'][0])
				model.append((format['description'], format['name'],
					format['extensions'][0]))
		combo.set_model(model)
		combo.set_active(0)
	
	def make_menu(self):
		"""Create the context menu."""
		# Generate history menu
		history_menu = self.__xml.get_widget('history_menu')
		history_menu.foreach(lambda child: history_menu.remove(child))
		items = self.feeds.feeds[self.feed_name].items.items()
		items.sort(reverse = True)
		for date, item in items:
			label = gtk.Label()
			text = self.get_menu_item_name(item)
			if self.__current_timestamp == date:
				label.set_markup('<b>' + text + '</b>')
			else:
				label.set_markup(text)
			align = gtk.Alignment(xalign = 0.0)
			align.add(label)
			menu_item = gtk.MenuItem()
			menu_item.data = item
			menu_item.connect('activate', self.on_history_activated)
			menu_item.add(align)
			history_menu.append(menu_item)
		history_menu.show_all()
		self.__xml.get_widget('show_link_item').set_active(self.show_link)
		self.__xml.get_widget('history_container').set_sensitive(
			len(self.feeds.feeds[self.feed_name].items) > 0)
		self.__xml.get_widget('save_as_item').set_sensitive(not self.__pixbuf \
			is None)
		
		return self.__xml.get_widget('menu')
	
	########################################################################
	# Standard python methods                                              #
	########################################################################
	
	def __init__(self, applet, settings, visible = False):
		"""Create a new ComicsView instance."""
		super(ComicsViewer, self).__init__()
		self.applet = applet
		self.__settings = settings
		
		# Initialize fields
		self.feeds = applet.feeds
		self.__update_id = None
		self.__download_id = None
		self.__downloader = None
		try:
			self.__pixbuf = gtk.gdk.pixbuf_new_from_file(settings['cache-file'])
		except:
			self.__pixbuf = None
		self.__is_error = False
		self.__xml = gtk.glade.XML(GLADE_FILE)
		self.make_file_type_chooser()
		self.__link = WWWLink('', '', LINK_FONTSIZE)
		self.__link.connect('size-allocate', self.on_link_size_allocate)
		self.__ticker = Ticker((20.0, 20.0))
		self.__current_timestamp = 0.0
		self.__border = BORDER
		self.__border_radii = BORDER_RADII
		
		# Connect events
		self.connect('destroy', self.on_destroy)
		self.feeds.connect('feed-changed', self.on_feed_changed)
		self.__xml.signal_autoconnect(self)
		
		# Build UI
		self.__link.connect('button-press-event', self.on_link_clicked)
		self.put_child(self.__link, 0, 0)
		self.put_child(self.__ticker, 0, 0)
		self.__ticker.show()
		
		self.set_skip_taskbar_hint(True)
		self.set_skip_pager_hint(True)
		self.set_visibility(visible)
		
		self.load_settings()
		
	########################################################################
	# Property updating methods                                            #
	########################################################################
	
	def load_settings(self):
		"""Load the settings."""
		screen = self.get_screen()
		w, h = self.get_size()
		
		self.set_show_link(self.__settings.get_bool('show_link',
			False))
		self.set_feed_name(self.__settings.get_string('feed_name', ''))
		self.move(self.__settings.get_int('x', (screen.get_width() - w) / 2),
			self.__settings.get_int('y', (screen.get_height() - h) / 2))
	
	def save_settings(self):
		"""Save the settings."""
		x, y = self.get_position()
		self.__settings['x'] = x
		self.__settings['y'] = y
		self.__settings.save()
	
	def set_feed_name(self, new_feed_name):
		"""Set the name of the feed to use."""
		if self.__update_id:
			self.feeds.feeds[self.feed_name].disconnect(self.__update_id)
			self.__update_id = None
		
		if new_feed_name in self.feeds.feeds:
			self.feed_name = new_feed_name
			self.__update_id = self.feeds.feeds[self.feed_name] \
				.connect('updated', self.on_feed_updated)
			if self.feeds.feeds[self.feed_name].ready:
				self.on_feed_updated(self.feeds.feeds[self.feed_name],
					Feed.OK)
			self.__settings['feed_name'] = str(new_feed_name)
		elif len(self.feeds.feeds) > 0:
			self.set_feed_name(self.feeds.feeds.keys()[0])
	
	def set_show_link(self, new_show_link):
		"""Show or hide the link label."""
		self.show_link = new_show_link
		if self.show_link:
			self.__link.show()
			self.__border = LINK_BORDER
			self.__border_radii = LINK_BORDER_RADII
		else:
			self.__link.hide()
			self.__border = BORDER
			self.__border_radii = BORDER_RADII
		self.__settings['show_link'] = str(new_show_link)
		self.update_size()
		
	########################################################################
	# Event hooks                                                          #
	########################################################################
	
	def on_destroy(self, widget):
		if self.__update_id:
			self.feeds.feeds[self.feed_name].disconnect(self.__update_id)
			self.__update_id = None
		if self.__download_id and self.__downloader:
			self.__downloader.disconnect(self.__download_id)
			self.__download_id = None
		del self.__pixbuf
	
	def on_link_clicked(self, widget, e):
		# Start the web browser in another process
		os.system('%s %s &' % (BROWSER_COMMAND, widget.url))
	
	def on_history_activated(self, widget):
		# The widget is a GtkMenuItem, where data is a str
		self.select_item(widget.data)
	
	def on_normal_activated(self, widget):
		self.set_scale(1.0)
	
	def on_larger_activated(self, widget):
		self.set_scale(self.scale * 1.2)
	
	def on_smaller_activated(self, widget):
		self.set_scale(self.scale / 1.2)
	
	def on_show_link_toggled(self, widget):
		self.set_show_link(widget.get_active())
	
	def on_close_activated(self, widget):
		self.close()
	
	def on_save_as_activated(self, widget):
		dialog = self.__xml.get_widget('save_as_dialog')
		dialog.set_title(self.feed_name)
		combo = self.__xml.get_widget('file_format_combo')
		model, iterator = combo.get_model(), combo.get_active_iter()
		format = model.get_value(iterator, 1)
		ext = model.get_value(iterator, 2)
		dialog.set_current_name('%s.%s' % (self.__link.text, ext))
		if dialog.run():
			model, iterator = combo.get_model(), combo.get_active_iter()
			format = model.get_value(iterator, 1)
			try:
				self.__pixbuf.save(dialog.get_filename(), format)
			except:
				self.applet.show_message(_('Failed to save <i>%s</i>.') %
					dialog.get_filename(), gtk.STOCK_DIALOG_ERROR)
		
		dialog.hide()
	
	def on_file_format_combo_changed(self, widget):
		dialog = self.__xml.get_widget('save_as_dialog')
		current_name = dialog.get_filename().rsplit('.', 1)
		if len(current_name) == 2:
			combo = widget
			model, iterator = combo.get_model(), combo.get_active_iter()
			ext = model.get_value(iterator, 2)
			dialog.set_current_name('%s.%s' % (
				os.path.basename(current_name[0]), ext))
	
	def on_link_size_allocate(self, widget, e):
		i_dim = self.get_image_dimensions()
		l_dim = self.get_link_dimensions()
		t_dim = self.get_ticker_dimensions()
		c_dim = (max(i_dim[0],
			l_dim[0] + 2.0 * (t_dim[0] + TICKER_LINK_SEPARATION)), i_dim[1])
		w_dim = (c_dim[0] + self.__border[0] + self.__border[2],
			c_dim[1] + self.__border[1] + self.__border[3])
		
		# Place link
		if self.show_link:
			self.move_child(self.__link,
				(w_dim[0] - l_dim[0]) / 2,
				w_dim[1] - (self.__border[3] + l_dim[1]) / 2 - 1)
		
		# Does the window need to be resized?
		if l_dim[0] > i_dim[0]:
			self.set_canvas_size(w_dim)
	
	def on_widget_show(self, widget):
		"""Set the compiz widget property on all top-level windows."""
		compiz_widget_set(widget, compiz_widget_get(self))
	
	def on_draw_background(self, ctx):
		"""Draw the window."""
		self.draw_window(ctx)
		self.draw_image(ctx)
		
	def on_feed_updated(self, feed, result):
		"""The feed has been updated."""
		if result == Feed.DOWNLOAD_OK:
			# Only emit the updated signal when there actually is an update
			if self.__current_timestamp != 0.0:
				self.emit('updated', feed.items[feed.newest][TITLE])
			self.select_item(feed.items[feed.newest])
	
	def on_download_completed(self, o, code, item):
		"""A new image has been downloaded."""
		self.__ticker.set_ticking(False)
		self.__is_error = code != Downloader.OK
		
		self.__current_timestamp = item[DATE]
		self.__link.set_text(self.get_link_name(item))
		self.__link.set_url(item[LINK])
		
		self.__downloader = None
		self.__download_id = None
		
		if not self.__is_error:
			del self.__pixbuf
			try:
				self.__pixbuf = gtk.gdk.pixbuf_new_from_file(o.filename)
			except gobject.GError:
				self.__pixbuf = None
				self.__is_error = True
		
		self.update_size()
	
	def on_feed_changed(self, feeds, feed_name, action):
		"""A feed has been changed."""
		if action == FeedContainer.FEED_REMOVED:
			if self.feed_name == feed_name:
				self.__settings.delete()
				self.destroy()

