#!/usr/bin/env python

# Copyright (c) 2007-2008 Randal Barlow <im.tehk at gmail.com>
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

import sys
import awn

python_version = (2, 5, 0, 'final', 0)

if sys.version_info < python_version:
    print("It looks like you are using a python version "
          "older then python2.5.0\n"
          "Please report any bugs at https://launchpad.net/awn-extras")
    awn.check_dependencies(globals(), 'sqlalchemy', 'feedparser', 'sqlite')
else:
    awn.check_dependencies(globals(), 'sqlalchemy', 'feedparser')

"""FeedParser Database

Works in conjunction with Universal Feed Parser and SQLAlchemy by providing an
interface with which a developer can create, manage, and update a group of
feeds.

Required: feedparser, sqlalchemy 0.40 or greater, python2.5

Recommended: sqlalchemy 0.40, sqlite3

"""

__version__ = "0.0.2" # base on revision 493 of awn-extras
__license__ = """Copyright (c) 2007-2008 Randal Barlow <im.tehk at gmail.com>

 This library is free software; you can redistribute it and/or
 modify it under the terms of the GNU Lesser General Public
 License as published by the Free Software Foundation; either
 version 2 of the License, or (at your option) any later version.

 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 Lesser General Public License for more details.

 You should have received a copy of the GNU Lesser General Public
 License along with this library; if not, write to the
 Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 Boston, MA 02111-1307, USA.
"""

from sqlalchemy import create_engine, Table, Column
from sqlalchemy import Integer, String, MetaData, ForeignKey, PickleType
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker
import feedparser


FEED_HARD_ERROR_WARNING = '\nWARNING error in feed: "%s" \n "%s"'
FEED_SOFT_ERROR_WARNING = 'Soft error "%s" in "%s" , doesnt seem to be major'


def compare_by(fieldname):
    """compares a dictionary by a fieldname"""

    def compare_two_dicts(a, b):
        return cmp(b[fieldname], a[fieldname])
    return compare_two_dicts


def check_if_new(lastchecked, newentries):
    """Used by _updatefeed to return all entries that were after a given date

    Arguments

    * lastchecked: a struct time tuple representing the lastest entries time

    * newentries: a list of feeds entries from a new call
    of feedparser.parse(uri).entries
    """
    newentries.sort(compare_by('updated_parsed'))
    if cmp(lastchecked, newentries[0]['updated_parsed']) == -1:
        # The new entry is truly new
        # time to return a list of entries which are newer
        # then lastchecked
        entries = []
        for entry in newentries:
            if cmp(lastchecked, entry['updated_parsed']) == -1:
                entries.append(entry)
        return entries
    else:
        # Returned either 1 or 0, which means the feed is either
        # the same(or older)?
        return []


def  _publication_date_check(entries):
    isupdatable = True
    while isupdatable == True:
        for entry in entries:
            if 'updated_parsed' not in entry.keys():
                isupdatable = False
        break
    return isupdatable


def _nettest(fn):
    """Used by _updatefeed to test the quality of the feed and its entries"""

    def _decorate(lastchecked, oldentries, uri, echofeederros = False):
        newfeedobj = feedparser.parse(uri)
        if newfeedobj.bozo == 0:
            entries = fn(lastchecked, oldentries, newfeedobj.entries)
            return entries
        elif newfeedobj.bozo == 1 and newfeedobj.entries == []:
            print FEED_HARD_ERROR_WARNING % (uri,
                                             newfeedobj.bozo_exception.message)
            return oldentries
        else:
            print FEED_SOFT_ERROR_WARNING % (newfeedobj.bozo_exception.message,
                                             uri)
            entries = fn(lastchecked, oldentries, newfeedobj.entries)
            return entries
    return _decorate


@_nettest
def _updatefeed(lastchecked, oldentries, newentries):
    """Currently it can be used to merge two feeds using check_if_new

    Arguments

    * lastchecked: a struct time tuple representing the lastest entries time

    * oldentries: the Feed objects current Entries attribute

    * newentries(without decorator): a list of feeds entries from a new call
    of feedparser.parse(uri).entries

    * newentries(with decorator): the feeds uri
    """
    if oldentries != []:
        entries = check_if_new(oldentries[0]['updated_parsed'], newentries)
        entries = entries + oldentries
    else:
        entries = check_if_new(lastchecked, newentries)
    entries.sort(compare_by('updated_parsed'))
    return entries


class Feed(object):
    """
    This is the generic Feed class used by the database to store feeds

    It has the following proprieties:
    Title = The feeds title
    Entries = The list of entries(stories)
    URI = The feeds uri/url
    LastChecked* = The struct time date of the latest entry(used for updating)

    *Optional
    """

    def __init__(self, Title, URI, Entries, LastChecked = None):
        """
        Arguments

        * Title: The feeds title

        * URI: The feeds URI

        * Entries: The feeds entries
        """
        self.Title = Title
        self.URI = URI.replace(' ', '')
        self.Entries = Entries
        if LastChecked == None:
            try:
                self.LastChecked = self.Entries[0]['updated_parsed']
            except KeyError:
                self.LastChecked = False

    def __repr__(self):
        return "<Feed('%s', '%s', 'Entries:%d')>" % (self.Title, self.URI,
                                                     len(self.Entries))

    def get_entries(self):
        """
        A wrapper function that is used to get a
        list of entries from a feed object
        """
        return self.Entries

    def update_feed(self):
        """
        A per feed updater which updates a feed and sets the LastChecked value
        """
        if _publication_date_check(self.Entries) == True:
            self.Entries = _updatefeed(self.LastChecked,
                                       self.Entries,
                                       self.URI)
            if len(self.Entries) != 0:
                self.LastChecked = self.Entries[0]['updated_parsed']
        else:
            #Legacy updating
            self.Entries = feedparser.parse(self.URI).entries

    def clear_feed(self):
        """
        Sets the feeds as 'empty'
        """
        if self.LastChecked != False:
            self.LastChecked = self.Entries[0]['updated_parsed']
        self.Entries = []


def BuildFeed(uri):
    """
    A wrapper to manually create a feed from a URI

    Arguments

    * uri: the uri/url to the rss feed

    Returns a contructed Feed object
    """
    tmp = feedparser.parse(uri)
    if tmp.bozo == 0:
        return Feed(tmp.feed.title, uri, tmp.entries)
    elif tmp.bozo == 1 and tmp.entries == []:
        print FEED_HARD_ERROR_WARNING % (uri, tmp.bozo_exception.message)
        return None
    else:
        print FEED_SOFT_ERROR_WARNING % (tmp.bozo_exception.message, uri)
        return Feed(tmp.feed.title, uri, tmp.entries)


class FeedDatabase(object):
    """
    The database which stores feed objects

    It has the following instances:
    Session the sessio class
    session the session instance
    engine the engine

    Arguments

    * dblocation: the location of the database on the file system
    It defaults to a memory store

    * echo*: True/False, if True sqlalchemy will act vocally
    """

    def __init__(self, dblocation='sqlite:///:memory:',
                 echo = True):
        """
        Arguments

        * dblocation: the location of the database on the file system
        It defaults to a memory store

        * echo: True/False, if True sqlalchemy will act vocally
        """
        self.engine = create_engine(dblocation, echo=echo)
        metadata = MetaData()
        feeds_table = Table('feeds', metadata,
                            Column('id', Integer, primary_key=True),
                            Column('Title', String(40)),
                            Column('URI', String(100)),
                            Column('Entries', PickleType),
                            Column('LastChecked', PickleType))
        metadata.create_all(self.engine)
        mapper(Feed, feeds_table)
        CustomSessionMaker = sessionmaker(bind=self.engine, autoflush=True,
                                    transactional=True)
        self.session = CustomSessionMaker()

    def save_all_objects(self):
        """
        Saves all Feed objects in their current state
        """
        self.session.commit()

    def get_feed_objects(self):
        """
        Returns all the Feed objects in this database
        """
        return self.session.query(Feed).all()

    def save_new_feed(self, feed):
        """
        Saves a built Feed object(use BuildFeed) to the database

        Arguments

        * feed: A Feed object typically retrieved from BuildFeed
        """
        if feed != None:
            self.session.save(feed)

    def update_feeds(self, feeduris):
        """
        Updates all Feed objects using their update_feed method

        Arguments

        * feeduris: a list of feed URIs. With that list it will
        update existing feeds and add any feed which is in the list but
        not yet in the database
        """

        def __test(new, olds):
            for old in olds:
                if old.URI == new:
                    return True
        currentFeedObjects = self.get_feed_objects()
        for feed in feeduris:
            if __test(feed, currentFeedObjects) != True:
                self.save_new_feed(BuildFeed(feed))
        # Add in remove orphan
        feeds = self.get_feed_objects()
        for feed in feeds:
            if feed.URI not in feeduris:
                print feed
                self.session.delete(feed)
                # Remove?
        for feed in feeds:
            feed.update_feed()
        self.save_all_objects()

    def close_database(self):
        self.session.commit()
        self.session.close()
