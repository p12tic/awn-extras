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


import re
import os

from downloader import Downloader
from feed import Feed, IMG_RE, IMG_SRC_RE, URL, TITLE, TYPE, \
	LINK, DATE, DOWNLOADER, DATA, NAME, IMG_INDEX, has_title, has_link, \
	get_time_stamp, type_is_image, extract_urls, make_absolute_url
from settings import Settings

IMAGES = 'images'
IMG_ALT_RE = re.compile('<img .*?alt=["\'](.*?)["\'].*?>', re.IGNORECASE)


class ImageEntry:
	def __init__(self, url, img_index, is_indirect):
		self.url = url
		self.img_index = img_index
		self.is_indirect = is_indirect
	
	def __cmp__(self, other):
		return cmp(self.url, other.url)

def generate_images(urls, is_indirect):
	result = []
	for i, url in enumerate(urls):
		result.append(ImageEntry(url, i, is_indirect))
	return result


class QueryFeed(Feed):
	def count_occurrences(self, image):
		result = 0
		for i in self.items.itervalues():
			if image in i[IMAGES]:
				result += 1
		return result
	
	def detect_images(self):
		keys = self.items.keys()
		if not keys:
			return
		
		images = self.items[keys[0]][IMAGES]
		
		# List unique
		for image in images:
			if self.count_occurrences(image) == 1 and not image in self.images:
				self.images.append(image)
	
	def __init__(self, url):
		"""Initialize a parser."""
		settings = Settings()
		settings['name'] = None
		settings['url'] = url
		super(QueryFeed, self).__init__(None, settings)
		
		self.images = []
	
	def process_entry(self, index, entry):
		item = {}
		
		if has_title(entry):
			item[TITLE] = entry.title
		else:
			item[TITLE] = self.name
		
		if has_link(entry):
			item[LINK] = entry.link
		
		time_stamp = get_time_stamp(index, entry)
		item[DATE] = time_stamp
		self.items[time_stamp] = item
		self.updated = True
		
		if time_stamp > self.newest:
			self.newest = time_stamp
		
		# Always prefer image enclosures
		if 'enclosures' in entry and len(entry.enclosures) == 1 \
				and type_is_image(entry.enclosures[0].type):
			item[URL] = entry.enclosures[0].href
			self.images = [ImageEntry(None, 0, False)]
		else:
			images, link = extract_urls(entry)
			item[IMAGES] = generate_images(images, False)
			self.download_indirect(item, link)
	
	def on_indirect_download_completed(self, o, code, item):
		self.files_pending -= 1
		
		if code != Downloader.DOWNLOAD_OK:
			del self.items[item[DATE]]
			return
		
		f = open(o.filename)
		data = f.read()
		f.close()
		os.remove(o.filename)
		
		urls = map(lambda u: make_absolute_url(u, item[LINK]),
			IMG_SRC_RE.findall(data))
		item[IMAGES].extend(generate_images(urls, True))
		
		if self.files_pending == 0:
			self.detect_images()
			self.finalize()
			if self.updated:
				self.emit('updated', Feed.DOWNLOAD_OK)

