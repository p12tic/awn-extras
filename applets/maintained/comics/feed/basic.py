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


import gobject
import re
import urllib
import urlparse
import threading
import htmlentitydefs
import httplib
import time

from settings import Settings

NAME = 'name'
URL = 'url'
PLUGIN = 'plugin'
TITLE = 'title'
LINK = 'link'
DATE = 'date'

month = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
         'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
         'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}


class Feed(gobject.GObject):
    """A feed class."""

    DOWNLOAD_OK = 0
    DOWNLOAD_FAILED = -1
    DOWNLOAD_NOT_FEED = -2

    # Convenient regular expressions
    IMG_RE = re.compile('(<img[\n ].*?>)', re.IGNORECASE)
    IMG_SRC_RE = re.compile('<img[\n ].*?src=["\'](.*?)["\'].*?>', re.IGNORECASE)

    __gsignals__ = {
        'updated': (gobject.SIGNAL_RUN_FIRST, None, (int,)),
        }

    def make_absolute_url(self, url, from_doc):
        """Convert a relative URL to an absolute one."""
        if url is None or len(url) == 0:
            return None
        parsed = (urlparse.urlparse(url), urlparse.urlparse(from_doc))
        if len(parsed[0][1]) > 0:
            return url
        elif parsed[0][2][0] == '/':
            return parsed[1][0] + '://' + parsed[1][1] + parsed[0][2]
        else:
            # TODO this didn't work for some (or all?) urls,
            # like http://www.gwscomic.com - test more thoroughly whether
            # there should be an elif for that
            #return parsed[1][0] + '://' + parsed[1][1] \
            #    + parsed[1][2].rsplit('/', 1)[0] + parsed[0][2]
            return parsed[1][0] + '://' + parsed[1][1] \
                + '/' + parsed[0][2]

    def get_timestamp_for_url(self, url):
        """Request the "Last-Modified" header from url without downloading
        any data and return a timestamp or None"""
        if url is None or len(url) == 0:
            return None
        p = urlparse.urlparse(url)
        try:
            if p.scheme == 'http':
                conn = httplib.HTTPConnection(p.netloc)
            elif p.scheme == 'https':
                conn = httplib.HTTPSConnection(p.netloc)
            else:
                raise Exception
            conn.request("HEAD", p.path)
            res = conn.getresponse()
            htime = res.getheader("Last-Modified")
        except Exception:
            return None
        if htime is None:
            return None

        # Based on a posting by Philip Semanchuk, Nov 2009 on
        # http://mail.python.org/mailman/listinfo/python-list

        try:
            if not htime.endswith("GMT"):
                # ASCTIME format
                # Work around locale problems: remove weedays,
                # convert month names to decimals
                htime = htime[4:]
                htime = month[htime[0:3]] + htime[3:]
                timestamp = time.strptime(htime, "%m %d %H:%M:%S %Y")
            else:
                # RFC 850 Format
                if "-" in htime:
                    htime = htime.split(" ", 1)[1]
                    htime = htime[:3] + month[htime[3:6]] + htime[6:]
                    timestamp = time.strptime(htime, "%d-%m-%y %H:%M:%S GMT")
                else:
                    # RFC 1123 Format
                    htime = htime[5:]
                    htime = htime[:3] + month[htime[3:6]] + htime[6:]
                    timestamp = time.strptime(htime, "%d %m %Y %H:%M:%S GMT")
            timestamp = time.mktime(timestamp)
        except Exception, err:
            print "Comics!: %s" % err
            return None
        return timestamp

    def unescape_html(self, text):
        """Taken from Fredrik Lundh -
        http://effbot.org/zone/re-sub.htm#unescape-html"""
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text  # leave as is
        return re.sub("&#?\w+;", fixup, text)

    def __init__(self, settings=None, url=None):
        """Initialize a feed."""
        super(Feed, self).__init__()

        if settings is None:
            self.is_query = True
            settings = Settings()
            settings['name'] = None
            settings['url'] = url
        else:
            self.is_query = False
        self.filename = settings.filename
        self.description = settings.get_string('description', '')
        self.name = settings.get_string('name', '---')
        self.url = settings.get_string('url')
        self.timeout = settings.get_int('timeout', 20)
        self.items = {}
        self.newest = 0.0
        self.status = None
        self.__lock = threading.Lock()
        self.__timeout = gobject.timeout_add(self.timeout * 60 * 1000,
            self.on_timeout)

    def run(self):
        """The thread body."""
        if not self.__lock.acquire(False):
            return
        old_status = self.status
        self.updated = False
        try:
            filename, headers = urllib.urlretrieve(self.url)
            self.status = self.parse_file(filename)
            # If the status has changed, the feed is considered updated
            if self.updated or old_status != self.status:
                gobject.idle_add(gobject.GObject.emit, self, 'updated',
                    self.status)
        except IOError:  # Network is down
            self.status = Feed.DOWNLOAD_FAILED
        except Exception, err:
            self.status = Feed.DOWNLOAD_FAILED
            print "Comics!: Parsing error: %s" % err
        self.__lock.release()

    def update(self):
        """Reload the feed."""
        thread = threading.Thread(target=self.run, name=self.name)
        thread.setDaemon(True)
        thread.start()

    def parse_file(self, o):
        """This method is called when the file pointer to by settings.url has
        been correctly downloaded.

        It returns an error code."""
        raise NotImplementedError()

    def on_timeout(self):
        self.update()

        # Return True to keep the timer running
        return True
