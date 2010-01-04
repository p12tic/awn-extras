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


import feedparser
import threading
import time
import urllib

from basic import URL, TITLE, LINK, DATE, Feed

IMAGES = 'images'

TYPE = 'type'
IMG_INDEX = 'img_index'


class RSSFeed(Feed):
    """A feed class."""

    def type_is_image(self, mime_type):
        """Returns whether a MIME type is an image."""
        return mime_type.startswith('image/')

    def get_time_stamp(self, index, entry):
        """Returns a unique time stamp for entry."""
        if 'published' in entry:
            return time.mktime(entry.published_parsed)
        elif 'created' in entry:
            return time.mktime(entry.created_parsed)
        elif 'updated' in entry:
            return time.mktime(entry.updated_parsed)
        else:
            return -1 * float(index + 1)

    def extract_urls(self, entry):
        """Returns a tuple containg all URLS in the entry: the first item is a
        list containing URLs pointing directly to images and the second is a
        URL pointing to a web page."""
        images = []

        if 'link' in entry:
            link = entry.link
        else:
            link = None

        if 'description' in entry:
            images.extend(Feed.IMG_SRC_RE.findall(entry.description))

        if 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if self.type_is_image(enclosure.type):
                    images.append(enclosure.href)

        return (images, link)

    def __init__(self, settings=None, url=None):
        """Initialize an RSS feed."""
        super(RSSFeed, self).__init__(settings, url)
        if settings:
            self.img_index = settings.get_int('img_index', 1) - 1
            self.is_legacy_indirect = \
                settings.get_string('type', '') == 'indirect'
        else:
            self.img_index = 0
            self.is_legacy_indirect = False

    def parse_file(self, filename):
        try:
            feed = feedparser.parse(filename)
        except Exception, e:
            return Feed.DOWNLOAD_NOT_FEED

        # Update properties
        if 'description' in feed:
            self.description = feed.description
        if 'title' in feed.feed:
            self.name = feed.feed.title

        # Create an item-thread tuple for every entry
        threads = []
        for (index, entry) in enumerate(feed.entries):
            item = {}
            thread = threading.Thread(target=self.process_entry,
                                      args=(item, index, entry))
            threads.append((item, thread))
            thread.start()

        # Wait for all threads to finish
        for item, thread in threads:
            thread.join()
            if URL in item:
                self.items[item[DATE]] = item

        if len(self.items) == 0:
            return Feed.DOWNLOAD_NOT_FEED
        else:
            return Feed.DOWNLOAD_OK

    def process_entry(self, item, index, entry):
        """This function adds attributes to item. It runs in its own thread."""
        if 'title' in entry:
            item[TITLE] = entry.title
        else:
            item[TITLE] = self.name

        images, link = self.extract_urls(entry)
        item[IMAGES] = images
        if link:
            item[LINK] = link
            # If the requested image has an index greater than what we
            # currently have, download indirect images
            if len(item[IMAGES]) < self.img_index or self.is_query \
                    or self.is_legacy_indirect:
                self.extend_images(item)

        # If is_legacy_indirect is set, we have to use a different img_index
        if self.is_legacy_indirect:
            img_index = self.img_index + len(images)
        else:
            img_index = self.img_index
        if len(item[IMAGES]) > img_index:
            item[URL] = item[IMAGES][img_index]

        time_stamp = self.get_time_stamp(index, entry)
        if time_stamp > self.newest or self.newest == 0.0:
            self.newest = time_stamp
            self.updated = True
        item[DATE] = time_stamp

    def extend_images(self, item):
        """Downloads item[LINK], parses it for img tags and adds them to
        item[IMAGES]."""
        try:
            f = urllib.urlopen(item[LINK])
            data = f.read()
            f.close()
            item[IMAGES].extend(map(lambda u: self.make_absolute_url(u,
                item[LINK]), Feed.IMG_SRC_RE.findall(data)))
        except:
            pass

    def get_unique_images(self):
        """Returns a list of (index, url) tuples for the images of one item
        that are not present in another. If there are no items present, None
        is returned."""
        if len(self.items) == 0:
            return None

        items = self.items.itervalues()
        item = items.next()
        result = list(enumerate(item[IMAGES]))
        for i in items:
            for index, value in enumerate(result):
                if value[1] in i[IMAGES]:
                    del result[index]

        return result
