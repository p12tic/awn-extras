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
	LINK, DATE, DOWNLOADER, NAME, TIME_FORMAT, IMG_INDEX, ALT_TEXT, has_title, \
	has_link, has_enclosures, has_description, get_time_stamp
from settings import Settings

IMAGES = 'images'
IMG_ALT_RE = re.compile('<img .*?alt=["\'](.*?)["\'].*?>', re.IGNORECASE)


class QueryFeed(Feed):
	def detect_images(self):
		alist = items[0][IMAGES]
		blist = items[1][IMAGES]
		
		# List unique
		unique = []
		for i, img in enumerate(alist):
			if not img in blist:
				unique.append(i, img)
		
		# Generate images and alt texts
		self.images = []
		self.alt_texts = []
		for i, img in unique:
			src = IMG_SRC_RE.search(img).group(1)
			alt = None
			
			amatch = IMG_ALT_RE.search(img)
			bmatch = IMG_ALT_RE.search(blist[i])
			if amatch and bmatch:
				# Find the longest common string of the alt texts not containing
				# a digit---a digit probably comes from a date
				length = 0
				aalt = amatch.group(1)
				balt = bmatch.group(1)
				for j, letter in enumerate(aalt):
					if letter.isdigit() or j >= len(balt) \
							or balt[j] != letter:
						# Stop when there is a mismatch or a digit
						break
					length = length + 1
				
				if length > 0:
					alt = aalt[:length].strip()
			
			self.images.append((i + 1, src))
			self.alt_texts.append((i + 1, alt))
	
	def __init__(self, url):
		"""Initialize a parser."""
		settings = Settings()
		settings['name'] = None
		settings['url'] = url
		super(QueryFeed, self).__init__(None, settings)
		
		self.images = []
		self.alt_texts = []
	
	def process_entry(self, index, entry):
		item = {}
		
		if has_title(entry):
			item[TITLE] = entry.title
		else:
			item[TITLE] = self.name
		
		if has_link(entry):
			item[LINK] = entry.link
		
		if has_enclosures(entry) and len(entry.enclosures) == 1:
			item[URL] = entry.enclosures[0].href
		elif has_description(entry):
			item[IMAGES] = IMG_SRC_RE.findall(data)
			if len(self.items) == 2:
				self.detect_images()
		elif LINK in item:
			self.download_indirect(item)
		else:
			return
		
		time_stamp = get_time_stamp(index, entry)
		item[DATE] = time_stamp
		self.items[time_stamp] = item
		self.updated = True
		
		if time_stamp > self.newest:
			self.newest = time_stamp
	
	def on_indirect_download_completed(self, o, code, item):
		self.files_pending -= 1
		
		if code != Downloader.DOWNLOAD_OK:
			del self.items[item[DATE]]
			return
		
		f = open(o.filename)
		data = f.read()
		f.close()
		os.remove(o.filename)
		
		item[IMAGES] = IMG_SRC_RE.findall(data)
		
		if self.files_pending == 0:
			self.detect_images()
			self.finalize()
			if self.updated:
				self.emit('updated', Feed.DOWNLOAD_OK)

