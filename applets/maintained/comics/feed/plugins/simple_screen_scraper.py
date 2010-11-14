# -*- coding: utf-8 -*-

# Copyright (c) 2010 Gabor Karsay
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

import feedparser
import re

from ..basic import URL, TITLE, LINK, DATE, Feed
from ..rss import IMAGES


def get_class():
    '''Mandatory for plugins.'''
    return SimpleScreenScraper


def matches_url(url):
    '''Mandatory for plugins.
    Return True if we want to read a comic from this url, else return False.
    SimpleScreenScraper accepts all urls that are not feeds.'''
    try:
        feed = feedparser.parse(url)
        if feed.version == '':
            return True
    except Exception:
        return True
    return False


class SimpleScreenScraper(Feed):
    """A SimpleScreenScraper class."""

    def __init__(self, settings=None, url=None):
        super(SimpleScreenScraper, self).__init__(settings, url)
        if settings:
            self.img_index = settings.get_int('img_index', 1) - 1
        else:
            self.img_index = 0

    def parse_file(self, filename):
        '''Mandatory for plugins.
        Parses given file (a downloaded feed) and puts all found items
        into self.items. An item must have an url (path to the image), a link
        (to the homepage), a title for that link and a date (timestamp).'''
        try:
            with open(filename, 'r') as f:
                data = f.read()
        except IOError:
            return Feed.DOWNLOAD_FAILED

        # Update properties
        if self.name is None:
            title_re = re.compile("<title>(.*?)<\/title>", re.DOTALL | re.M)
            self.name = self.unescape_html(title_re.findall(data)[0])

        images = []
        images += [self.make_absolute_url(u, self.url)
                   for u in Feed.IMG_SRC_RE.findall(data)]

        item = {}
        try:
            item[URL] = images[self.img_index]
        except IndexError:
            print "Comics!: img_index out of range in '%s'." % self.name
            return Feed.DOWNLOAD_NOT_FEED
        item[LINK] = self.url
        item[TITLE] = self.name

        # Set date. We have only one item, so the date is not that important.
        # It's only needed to determine whether the feed has been updated.
        # TODO For the time being we set it always to 1.0, maybe a real time
        # stamp could be generated from feedparser.parse(url).headers['date']
        item[DATE] = 1.0
        item[IMAGES] = images

        self.items[item[DATE]] = item

        if self.newest == 0.0:
            self.newest = item[DATE]
            self.updated = True
        return Feed.DOWNLOAD_OK

    def get_unique_images(self):
        """Mandatory for plugins.
        Returns a list of (index, url) tuples for the images."""
        if len(self.items) == 0:
            return None
        items = self.items.itervalues()
        item = items.next()
        return list(enumerate(item[IMAGES]))

    def get_plugin_name(self):
        """Mandatory for plugins."""
        return __name__[13:]  # strips 'feed.plugins.'
