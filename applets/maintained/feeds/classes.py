#! /usr/bin/python
#
# Copyright (c) 2009 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import os
import cPickle as pickle
import urllib
import time

import dbus
import dbus.service
import dbus.glib
import feedparser

from awn.extras import _, awnlib

pickle_path = '%s/.config/awn/applets/.feeds-tokens' % os.environ['HOME']

cache_dir = os.environ['HOME'] + '/.cache/awn-feeds-applet'


#A D-Bus service; external apps can tell feeds to update or add a feed
class DBusService(dbus.service.Object):
    def __init__(self, applet):
        self.applet = applet

        bus_name = dbus.service.BusName('org.awnproject.Feeds', bus=dbus.SessionBus())

        dbus.service.Object.__init__(self, bus_name, '/org/awnproject/Feeds')

    @dbus.service.method('org.awnproject.Feeds')
    def Update(self):
        self.applet.update_feeds()

        return 'OK'

    @dbus.service.method('org.awnproject.Feeds')
    def AddFeed(self, url):
        if url not in self.applet.urls:
            self.applet.add_feed(url)

        return 'OK'

#Used for storing tokens for service logins
#(Also works as a conventient pickle wraparound)
class Tokens:
    def __init__(self, uri=pickle_path):
        self.uri = uri
        fp = None

        try:
            fp = open(uri, 'r')
            self.tokens = pickle.load(fp)
        except:
            self.tokens = {}

        if fp:
            fp.close()

    def set_key(self, key, value):
        self.tokens[key] = value

        fp = open(self.uri, 'w+')
        pickle.dump(self.tokens, fp)
        fp.close()

    def remove_key(self, key):
        del self.tokens[key]

        fp = open(self.uri, 'w+')
        pickle.dump(self.tokens, fp)
        fp.close()

    def __getitem__(self, key):
        try:
            return self.tokens[key]
        except:
            return None

    def __setitem__(self, key, value):
        return self.set_key(key, value)

    def __iter__(self):
        return self.tokens.__iter__()

#Base class for all types of sources
class FeedSource:
    io_error = False
    login_error = False
    applet = None
    icon = None
    title = ''
    base_id = '' #e.g. google-reader
    url = '' #     google-reader-username
    web_url = '' #     http://www.google.com/reader/
    entries = []
    num_new = 0

    def __init__(self):
        pass

    def error(self, *args):
        self.io_error = True

        self.icon = 'gtk://gtk-dialog-error'
        self.applet.got_favicon(self, True)

        self.title = _("Error")
        self.applet.feed_updated(self)

    def update(self):
        pass

    def delete(self):
        if self.url in self.applet.tokens:
            self.applet.tokens.remove_key(self.url)

    def callback(self, *args):
        pass

    def post_data(self, uri, data=None, timeout=60, cb=None, error_cb=None):
        if cb is None:
            cb = self.callback

        if error_cb is None:
            error_cb = self.error

        if self.applet:
            self.applet.network_handler.post_data(uri, data, timeout, callback=cb, error=error_cb)

    #Also convenience
    def get_data(self, uri, headers={}, parse=False, timeout=60, user_data=None, cb=None, error_cb=None):
        if cb is None:
            cb = self.callback

        if error_cb is None:
            error_cb = self.error

        if self.applet:
            self.applet.network_handler.get_data(uri, headers, parse, timeout, \
                user_data=user_data, callback=cb, error=error_cb)

    def get_favicon(self, siteid=None, url=None):
        #web_url is used by default because many sites use, e.g., rss.example.com,
        #instead of just example.com, and these might not have favicons.
        if siteid is None:
            siteid = self.web_url.replace('http://', '').replace('https://', '')
            siteid = siteid.split('/')[0]

        if url is None:
            url = 'http://' + siteid + '/favicon.ico'

        self._favicon_siteid = siteid

        if siteid in self.applet.favicons:
            #Check if the favion is less than a week old
            if self.applet.favicons[siteid] + 604800L > long(time.time()):
                self.icon = os.path.join(cache_dir, siteid + '.ico')
                self.applet.got_favicon(self)
                return

        #Either the icon does not exist or it's more than a week old; fetch it
        self.get_data(url, timeout=15, cb=self.got_favicon, error_cb=self.callback)

    def got_favicon(self, data):
        self.applet.favicons[self._favicon_siteid] = long(time.time())

        fp = open(os.path.join(cache_dir, self._favicon_siteid + '.ico'), 'w+')
        fp.write(data)
        fp.close()

        self.icon = os.path.join(cache_dir, self._favicon_siteid + '.ico')
        self.applet.got_favicon(self)

        del self._favicon_siteid

#TODO: Need a better name. This is used if the feed may have items that are not considered new.
class CheckingForNew:
    newest = None

    #Call this after getting the entries, but before calling applet.feed_updated()
    def get_new(self):
        #See if the feed was updated, etc...
        if self.newest is not None and self.newest != self.entries[0]:
            #Find out how many items are new
            if self.newest in self.entries:
                self.num_new = self.entries.index(self.newest)

            #So many new items that the last loaded item doesn't show up
            else:
                self.num_new = len(self.entries)

        elif self.newest == self.entries[0]:
            self.num_new = 0

        if len(self.entries) > 0:
            self.newest = self.entries[0]

#Thank you http://code.google.com/p/pyrfeed/wiki/GoogleReaderAPI
class GoogleReader(FeedSource, CheckingForNew):
    base_id = 'google-reader'
    web_url = 'http://www.google.com/reader/'
    title = _("Google Reader")
    should_update = False
    google_key = None
    SID = ''
    login = 'https://www.google.com/accounts/ClientLogin'
    fetch_url = 'http://www.google.com/reader/atom/user/-/state/com.google/reading-list?n=5'
    favicon_url = 'http://www.google.com/reader/ui/favicon.ico'
    feed_search_url = 'http://www.google.com/reader/directory/search?'

    def __init__(self, applet, username, password=None):
        self.applet = applet
        self.username = username
        self.password = password
        self.url = self.base_id + '-' + username

        #Get ready to update/fetch feed, but don't actually do so.
        self.get_google_key(username, password)
        self.get_google_sid()
        self.get_favicon('google-reader', self.favicon_url)

    #Get/set the key for the Google Reader username and password
    def get_google_key(self, username=None, password=None):
        if self.google_key is None:
            if not self.applet.keyring:
                self.applet.keyring = awnlib.Keyring()

            token = self.applet.tokens['google-reader-' + username]

            #Username and password provided, e.g. from the add feed dialog
            if username and password:
                if token is None or token == 0:
                    self.google_key = self.applet.keyring.new('Feeds - google-reader-%s' % username,
                        password,
                        {'username': username, 'network': 'google-reader'},
                        'network')

                    self.applet.tokens['google-reader-' + username] = int(self.google_key.token)

                else:
                    self.google_key = self.applet.keyring.from_token(token)

            #No username or password provided, e.g. while loading feeds
            else:
                if token is None or token == 0:
                    self.google_key = None

                else:
                    self.google_key = self.applet.keyring.from_token(token)

    #Login to Google (Reader) and get an SID, a magic string that
    #lets us get the user's Google Reader items
    def get_google_sid(self):
        if self.google_key is not None:
            #Get the magic SID from Google to login, if we haven't already
            if self.SID == '':
                #Format the request
                data = urllib.urlencode({'service': 'reader',
                    'Email': self.google_key.attrs['username'],
                    'Passwd': self.google_key.password,
                    'source': 'awn-feeds-applet',
                    'continue': 'http://www.google.com/'})

                #Send the data to get the SID
                self.post_data(self.login, data, 15, cb=self.got_google_sid)

    def got_google_sid(self, data):
        #Check if wrong password/username
        if data.find('BadAuthentication') != -1:
            self.login_error = True

        #Save the SID so we don't have to re-login every update
        self.SID = data.split('=')[1].split('\n')[0]

        if self.should_update:
            self.update()
            self.should_update = False

    #Update the Google Reader feed
    def update(self):
        if self.SID == '':
            self.should_update = True

        else:
            #Load the reading list with that magic SID as a cookie
            self.get_data(self.fetch_url, {'Cookie': 'SID=' + self.SID}, True, cb=self.got_parsed)

    def got_parsed(self, parsed):
        self.entries = []
        for entry in parsed.entries[:5]:
            self.entries.append({'title': entry.title, 'url': entry.link})

        self.get_new()

        self.applet.feed_updated(self)

    def get_search_results(self, query, cb, _error_cb):
        search_url = self.feed_search_url + urllib.urlencode({'q': query})

        self.get_data(search_url, {'Cookie': 'SID=' + self.SID}, False, user_data=(cb, _error_cb), \
            cb=self.got_search_results, error_cb=_error_cb)

    def got_search_results(self, cbs, data):
        cb, error_cb = cbs

        try:
            json = data.split('_DIRECTORY_SEARCH_DATA =')[1].split('</script>')[0].strip()
            json = json.replace(':false', ':False').replace(':true', ':True')
            json = json.replace('"streamid":"feed/http', '"streamid":u"feed/http')
            json = json.replace('"title":"', '"title":u"')
            results = eval(json)['results']#It's a list of dictionaries!

            data = []
            for result in results:
                #For some reason 'streamid' starts with 'feed/'
                url = result['streamid'][5:]
                data.append({'url': url, 'title': result['title']})

        except:
            error_cb()

        else:
            cb(data)

class WebFeed(FeedSource, CheckingForNew):
    fetched = False
    parsed = None

    #Parsed is not None if a link to a feed is dragged onto the dialog. When that happens,
    #the link is downloaded and parsed. If it is a valid feed, the feedparser-parsed object
    #comes here, so we don't have to download and parse it a second time.
    def __init__(self, applet, url, parsed=None):
        self.applet = applet
        self.base_id = self.url = url
        self.parsed = parsed

        if parsed is not None:
            self.fetched = True

    def update(self):
        if self.fetched:
            self.got_parsed(self.parsed)
            self.fetched = False
            self.parsed = None

        else:
            self.get_data(self.url, parse=True, cb=self.got_parsed)

    def got_parsed(self, parsed):
        self.entries = []
        try:
            self.title = parsed.feed.title
        except:
            self.title = _("Untitled")
        self.web_url = parsed.feed.link
        for entry in parsed.entries[:5]:
            self.entries.append({'title': entry.title, 'url': entry.link})

        self.get_new()

        self.applet.feed_updated(self)

        self.get_favicon()
