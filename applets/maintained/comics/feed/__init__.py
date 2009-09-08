# -*- coding: utf-8 -*-

# Copyright (c) 2009 Moses Palmér
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


import gobject
import os

from basic import NAME, URL
from rss import RSSFeed
from settings import Settings
from shared import PLUGINS_DIR


class FeedContainer(gobject.GObject):
	FEED_ADDED = 0
	FEED_REMOVED = 1
	
	__gsignals__ = dict(
		feed_changed = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_STRING, gobject.TYPE_INT)))
	
	def _add_feed_factory(self, name):
		"""Dynamically loads a feed factory from a file and adds it to the list
		of factories. If filename does not contain a feed factory, it is not
		added."""
		try:
			module = __import__('plugins.%s' % name, fromlist = [name])
			if hasattr(module, 'matches_url') and hasattr(module, 'get_class'):
				self.feed_factories.append(module)
				return True
			else:
				del module
		except:
			pass
		
		return False
	
	def _load_feed_factories(self):
		"""Loads all feed factories found in the plugin directory."""
		try:
			for filename in filter(lambda f: f.endswith('.py'),
					os.listdir(PLUGINS_DIR)):
				self._add_feed_factory(filename.rpartition('.')[0])
		except OSError:
			pass
	
	def add_feed(self, filename):
		"""Loads a feed description from a file."""
		# Read file
		settings = Settings(filename)
		
		# Check whether all required parameters have been supplied
		if NAME in settings and URL in settings:
			if settings[NAME] in self.feeds:
				return True
			try:
				plugin = settings.get_string('plugin', '')
				if plugin:
					if self.feed_factories.has_key(plugin):
						factory = self.feed_factories[plugin].get_class()
					else:
						return False
				else:
					factory = RSSFeed
				feed = factory(settings)
				self.feeds[settings[NAME]] = feed
				self.emit('feed-changed', feed, FeedContainer.FEED_ADDED)
			except:
				pass
		
		return False
	
	def get_feed_for_url(self, url):
		"""Creates a feed suitable for a given URL. If no plugin matches the
		URL, an RSSFeed is returned."""
		for factory in self.feed_factories:
			if factory.matches_url(url):
				return factory.get_class()(url = url)
		return RSSFeed(url = url)
	
	def remove_feed(self, feed_name):
		"""Removes the feed feed_name."""
		if feed_name in self.feeds:
			self.emit('feed-changed', feed_name, FeedContainer.FEED_REMOVED)
			del self.feeds[feed_name]
	
	def __init__(self):
		super(FeedContainer, self).__init__()
		self.directories = []
		self.feed_factories = {}
		self.feeds = {}
		
		self._load_feed_factories()
	
	def load_directory(self, directory):
		"""Loads all feeds found in directory."""
		# Traverse .feed-files in the directory
		if not directory in self.directories:
			self.directories.append(directory)
		try:
			for filename in filter(lambda f: f.endswith('.feed'),
					os.listdir(directory)):
				self.add_feed(os.path.join(directory, filename))
		except OSError:
			pass
	
	def update(self):
		"""Updates all feeds."""
		for feed in self.feeds.values():
			feed.update()

