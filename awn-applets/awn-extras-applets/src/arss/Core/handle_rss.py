#!/usr/bin/env python

# Copyright (c) 2007 Randal Barlow
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

try:
    import feedparser
except:
    error_name = ("This applet requires the universal " +
                   "feedparser(deb:python-feedparser)")
    raise ImportError(error_name)
import time
from settings_rss import *
import os.path

def compare_by(fieldname):
    def compare_two_dicts (a, b):
        return cmp(a[fieldname], b[fieldname])
    return compare_two_dicts

def update(database):
    return database

def file_check(file):
    if os.path.isfile(file) == True:
        pass
    else:
        os.system(('touch ' + file))
        print 'please add feeds to ' + file

def add_feed_to_file(feeds, fileloc = Settings.__feedsfile__):
    file_check(fileloc)
    file = open(fileloc, 'a')
    for feed in feeds:
        file.write((feed + '\n'))
    file.close()

def build_feedlist(file):
    feeds = []
    file_check(file)
    feeddata = open(file)
    for feed in feeddata:
        if feed[0] in ('#',' ',''):
            pass
        elif feed == '\n':pass
        else:
            feeds.append(feed)
    if len(feeds) == 0:
        print 'please add feeds to ' + file
        print 'loading temp feeds'
        feeds = []
        feeddata.close()
        feeddata = open((Settings.__location__ + 'feedlist-default'))
        for feed in feeddata:
            feeds.append(feed)
    feeddata.close()
    return feeds

def get_feeds(url):
    feed = feedparser.parse(url)
    name = feed.feed.title
    for story in feed.entries:
        story['meta_read'] = False
    try:
        feed.entries.sort(compare_by('updated_parsed'))
    except:
        feed.entries.sort(compare_by('title'))
        print feed.feed.title
    feed.entries = feed.entries[::-1]
    if len(feed.entries) > Settings.__MAX_ENTRIES__:
        feed.entries = feed.entries[:Settings.__MAX_ENTRIES__]
    name = feed.feed.title
    return feed, name

def build_db(file = Settings.__feedsfile__):
    database = {}
    urls = build_feedlist(file)
    for url in urls:
        url = url.replace('\n','')
        try:
            feed, name = get_feeds(url)
            database[name] = [feed.entries, name]
        except AttributeError:
            print url + ' is not a proper feed'
            pass
    return database

def update_all(database):
    return build_db()
