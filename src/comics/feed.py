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


import feedparser
import gobject
import locale
import os
import re
import time
import urllib
import urlparse

from downloader import Downloader
from settings import Settings


IMG_RE = re.compile('(<img .*?>)', re.IGNORECASE)
IMG_SRC_RE = re.compile('<img .*?src=["\'](.*?)["\'].*?>', re.IGNORECASE)
IMG_ALT_TEMPLATE = '(<img .*?alt=["\']%s.*?["\'].*?>)'

URL = 'url'
TITLE = 'title'
TYPE = 'type'
LINK = 'link'
DATE = 'date'
DOWNLOADER = 'downloader'
DATA = 'data'

NAME = 'name'
IMG_INDEX = 'img_index'

def has_title(entry):
	return 'title' in entry

def has_link(entry):
	return 'link' in entry

def has_enclosures(entry):
	return 'enclosures' in entry

def has_description(entry):
	return 'description' in entry

def get_time_stamp(index, entry):
	if 'published' in entry:
		return time.mktime(entry.published_parsed)
	elif 'created' in entry:
		return time.mktime(entry.created_parsed)
	elif 'updated' in entry:
		return time.mktime(entry.updated_parsed)
	else:
		return -float(index + 1)

def type_is_image(type_descriptor):
	return type_descriptor.startswith('image/')

def extract_urls(entry):
	"""Returns a tuple containg all URLS in the entry: the first item is a list
	containing URLs pointing directly to images and the second is a URL
	pointing to a web page."""
	images = []
	
	if 'link' in entry:
		link = entry.link
	else:
		link = None
	
	if 'description' in entry:
		images.extend(IMG_SRC_RE.findall(entry.description))
	
	if 'enclosures' in entry:
		for enclosure in entry.enclosures:
			if type_is_image(enclosure.type):
				images.append(enclosure.href)
	
	return (images, link)

def make_absolute_url(url, from_doc):
	"""Convert a relative URL to an absolute one."""
	if url is None or len(url) == 0:
		return None
	parsed = (urlparse.urlparse(url), urlparse.urlparse(from_doc))
	if len(parsed[0][1]) > 0:
		return url
	elif parsed[0][2][0] == '/':
		return parsed[1][0] + '://' + parsed[1][1] + parsed[0][2]
	else:
		return parsed[1][0] + '://' + parsed[1][1] \
			+ parsed[1][2].rsplit('/', 1)[0] + parsed[0][2]


class Feed(gobject.GObject):
	"""A feed class."""
	
	DOWNLOAD_OK = 0
	DOWNLOAD_FAILED = -1
	DOWNLOAD_NOT_FEED = -2
	
	__gsignals__ = dict(
		updated = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_INT,)))
	
	def download_indirect(self, item, url):
		self.is_indirect = True
		self.files_pending += 1
		item[DOWNLOADER] = Downloader(url)
		item[DOWNLOADER].connect('completed',
			self.on_indirect_download_completed, item)
		item[DOWNLOADER].download()
	
	def __init__(self, filename, settings):
		"""Initialize a feed.
		
		name is the name initially displayed for the feed.
		
		url is the URL of the feed."""
		super(Feed, self).__init__()
		self.filename = filename
		self.feed = None
		self.items = {}
		self.name = settings.get_string('name', '---')
		self.description = ''
		self.url = settings.get_string('url')
		self.is_indirect = settings.get_string('type', '') == 'indirect'
		self.img_index = settings.get_int('img_index', 1) - 1
		self.newest = 0.0
		self.ready = False
		self.__timeout = gobject.timeout_add(20 * 60 * 1000, self.on_timeout)
	
	def process_entry(self, index, entry):
		item = {}
		
		if has_title(entry):
			item[TITLE] = entry.title
		else:
			item[TITLE] = self.name
		
		images, link = extract_urls(entry)
		if link:
			item[LINK] = link
		if self.is_indirect:
			self.download_indirect(item, link)
		else:
			if len(images) > self.img_index:
				item[URL] = images[self.img_index]
			else:
				return
				
		time_stamp = get_time_stamp(index, entry)
		item[DATE] = time_stamp
		self.items[time_stamp] = item
		
		if time_stamp > self.newest or self.newest == 0.0:
			self.newest = time_stamp
			self.updated = True
	
	def finalize(self):
		self.updated = False
		for (index, entry) in enumerate(self.feed.entries):
			self.process_entry(index, entry)
	
	def update(self):
		"""Reload the feed."""
		downloader = Downloader(self.url)
		downloader.connect('completed', self.on_download_completed)
		downloader.download()
		self.files_pending = 1
	
	def on_download_completed(self, o, code):
		self.files_pending -= 1
		
		if code != Downloader.DOWNLOAD_OK:
			self.emit('updated', Feed.DOWNLOAD_FAILED)
			return
		
		try:
			try:
				self.feed = feedparser.parse(o.filename)
			except:
				self.emit('updated', Feed.DOWNLOAD_NOT_FEED)
				return
		finally:
			os.remove(o.filename)
		
		if 'description' in self.feed:
			self.description = self.feed.description
		if 'title' in self.feed.feed:
			self.name = self.feed.feed.title
		self.finalize()
		if not self.is_indirect and len(self.items) == 0:
			self.emit('updated', Feed.DOWNLOAD_NOT_FEED)
		elif self.files_pending == 0:
			self.ready = True
			if self.updated:
				self.emit('updated', Feed.DOWNLOAD_OK)
	
	def on_indirect_download_completed(self, o, code, item):
		self.files_pending -= 1
		
		if code != Downloader.DOWNLOAD_OK:
			del self.items[item[DATE]]
			return
		
		f = open(o.filename)
		data = f.read()
		f.close()
		os.remove(o.filename)
		
		urls = map(lambda u: make_absolute_url(u, o.url),
			IMG_SRC_RE.findall(data))
		if len(urls) > self.img_index:
			item[URL] = urls[self.img_index]
		else:
			del self.items[item[DATE]]
		
		if self.files_pending == 0:
			self.ready = True
			if self.updated:
				self.emit('updated', Feed.DOWNLOAD_OK)
	
	def on_timeout(self):
		self.update()
		return True


class FeedContainer(gobject.GObject):
	FEED_ADDED = 0
	FEED_REMOVED = 1
	
	__gsignals__ = dict(
		feed_changed = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_STRING, gobject.TYPE_INT)))
	
	def add_feed(self, filename):
		"""Loads a feed description from a file."""
		# Read file
		settings = Settings(filename)
		
		# Check whether all required parameters have been supplied
		if NAME in settings and URL in settings \
				and not settings[NAME] in self.feeds:
			try:
				feed = Feed(filename, settings)
				feed.filename = filename
				self.feeds[settings[NAME]] = feed
				self.emit('feed-changed', feed, FeedContainer.FEED_ADDED)
			except:
				pass
		
		del settings
	
	def remove_feed(self, feed_name):
		if feed_name in self.feeds:
			self.emit('feed-changed', feed_name, FeedContainer.FEED_REMOVED)
			del self.feeds[feed_name]
	
	def __init__(self):
		super(FeedContainer, self).__init__()
		self.directories = []
		self.feeds = {}
	
	def load_directory(self, directory):
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
		for feed in self.feeds.values():
			feed.update()

