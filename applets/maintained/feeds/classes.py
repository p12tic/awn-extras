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
import cStringIO
import base64

try:
    import json
except:
    import simplejson as json

import dbus
import dbus.service
import dbus.glib
import feedparser

from awn import extras
from awn.extras import _, awnlib

pickle_path = '%s/.config/awn/applets/.feeds-tokens' % os.environ['HOME']

twitter_path = extras.PREFIX + '/share/avant-window-navigator/applets/feeds/icons/twitter-16x16.png'

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

#Just to standardize everything
class Entry(dict):
    def __init__(self, url='', title='', new=False, notify=False):
        dict.__init__(self)
        self['url'] = url
        self['title'] = title
        self['new'] = new
        self['notify'] = notify

#Base class for all types of sources
class FeedSource:
    io_error = False
    login_error = False
    applet = None
    icon = None
    title = ''
    base_id = '' #e.g. google-reader
    url = '' #         google-reader-username
    web_url = '' #     http://www.google.com/reader/
    entries = []
    num_new = 0
    num_notify = 0

    def __init__(self):
        pass

    def error(self, *args):
        self.io_error = True

        self.applet.got_favicon(self, True)

        self.applet.feed_updated(self)

    def update(self):
        self.applet.feed_updated(self)

    def delete(self):
        if self.url in self.applet.tokens:
            self.applet.tokens.remove_key(self.url)

    def callback(self, *args):
        pass

    def post_data(self, uri, data=None, timeout=30, server_headers=False, cb=None, error_cb=None):
        if cb is None:
            cb = self.callback

        if error_cb is None:
            error_cb = self.error

        if self.applet:
            self.applet.network_handler.post_data(uri, data, timeout, server_headers, \
                callback=cb, error=error_cb)

    #Also convenience
    def get_data(self, uri, headers={}, parse=False, timeout=30, user_data=None, cb=None, error_cb=None):
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

        #Twitter's favicon is ugly, so override it with an included one
        #(This is the icon that the Twitter feed source uses)

        if siteid == 'twitter.com':
            self.icon = twitter_path
            self.applet.got_favicon(self)

            return

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

    #Do something if the feed icon was clicked.
    def icon_clicked(self):
        pass

    #Do something if an item was clicked.
    def item_clicked(self, i):
        pass

#TODO: Still need a better name. This is used if the feed may have items that are not considered new.
class StandardNew:
    newest = None
    notified = []

    #Call this after getting the entries, but before calling applet.feed_updated()
    def get_new(self):
        #See if the feed was updated, etc...
        if self.newest is not None and self.newest['url'] != self.entries[0]['url'] and \
          self.newest['title'] != self.entries[0]['title']:
            got_it = False
            for i, entry in enumerate(self.entries):
                self.num_new = i
                if self.newest['url'] == entry['url'] and self.newest['title'] == entry['title']:
                    break

                else:
                    self.num_new += 1

        if len(self.entries) > 0:
            self.newest = self.entries[0]

        self.num_notify = 0

        #Mark the new feeds as new
        for i, entry in enumerate(self.entries):
            entry['new'] = bool(i < self.num_new)

            if entry['new'] and [entry['url'], entry['title']] not in self.notified:
                self.notified.append([entry['url'], entry['title']])
                entry['notify'] = True
                self.num_notify += 1

            else:
                entry['notify'] = False

#Used for logging in
class KeySaver:
    key = None
    password = None

    def get_key(self, username, password):
        if self.key is None:
            if not self.applet.keyring:
                self.applet.keyring = awnlib.Keyring()

            token = self.applet.tokens[self.url]

            #Username and password provided, e.g. from the add feed dialog
            if username and password:
                self.password = password
                if token is None or token == 0:
                    #No for i18n because if the user changes the language, he
                    #could lose the password (and most users won't even see this)
                    self.key = self.applet.keyring.new('Feeds - ' + self.url,
                        password,
                        {'username': username, 'network': self.base_id},
                        'network')

                    self.applet.tokens[self.url] = int(self.key.token)

                else:
                    self.key = self.applet.keyring.from_token(token)

            #No password provided, e.g. on applet startup
            else:
                if token is None or token == 0:
                    self.key = None
                    self.error()

                else:
                    self.key = self.applet.keyring.from_token(token)
                    self.password = self.key.password

        return self.key

#Thank you http://code.google.com/p/pyrfeed/wiki/GoogleReaderAPI
class GoogleReader(FeedSource, StandardNew, KeySaver):
    base_id = 'google-reader'
    web_url = 'http://www.google.com/reader/'
    title = _("Google Reader")
    login = 'https://www.google.com/accounts/ClientLogin'
    fetch_url = 'http://www.google.com/reader/atom/user/-/state/com.google/reading-list?n=5'
    favicon_url = 'http://www.google.com/reader/ui/favicon.ico'
    feed_search_url = 'http://www.google.com/reader/directory/search?'

    def __init__(self, applet, username, password=None):
        self.applet = applet
        self.username = username
        self.url = self.base_id + '-' + username

        self.should_update = False
        self.SID = ''
        self.init_network_error = False

        #Get ready to update/fetch feed, but don't actually do so.
        self.get_key(username, password)
        self.get_google_sid()
        self.get_favicon('google-reader', self.favicon_url)

    #Login to Google (Reader) and get an SID, a magic string that
    #lets us get the user's Google Reader items
    def get_google_sid(self):
        if self.key is not None:
            #Get the magic SID from Google to login, if we haven't already
            if self.SID == '':
                try:
                    #Format the request
                    data = urllib.urlencode({'service': 'reader',
                        'Email': self.key.attrs['username'],
                        'Passwd': self.key.password,
                        'source': 'awn-feeds-applet-' + extras.__version__,
                        'continue': 'http://www.google.com/'})
                except:
                    self.error()
                    return

                #Send the data to get the SID
                self.post_data(self.login, data, 15, cb=self.got_google_sid, error_cb=self.sid_error)

    def sid_error(self, *args):
        self.init_network_error = True
        self.error()

    def got_google_sid(self, data):
        self.init_network_error = False

        #Check if wrong password/username
        if data.find('BadAuthentication') != -1:
            self.login_error = True
            self.error()
            return

        #Save the SID so we don't have to re-login every update
        self.SID = data.split('=')[1].split('\n')[0]

        if self.should_update:
            self.update()
            self.should_update = False

    #Update the Google Reader feed
    def update(self):
        if self.SID == '' and not self.init_network_error:
            self.should_update = True

        elif self.init_network_error:
            self.should_update = True
            self.get_google_sid()

        else:
            #Load the reading list with that magic SID as a cookie
            self.get_data(self.fetch_url, {'Cookie': 'SID=' + self.SID}, True, cb=self.got_parsed)

    def got_parsed(self, parsed):
        self.entries = []
        for entry in parsed.entries[:5]:
            self.entries.append(Entry(entry.link, entry.title))

        self.get_new()

        self.applet.feed_updated(self)
        self.get_favicon('google-reader', self.favicon_url)

    def get_search_results(self, query, cb, _error_cb):
        search_url = self.feed_search_url + urllib.urlencode({'q': query})

        self.get_data(search_url, {'Cookie': 'SID=' + self.SID}, False, user_data=(cb, _error_cb), \
            cb=self.got_search_results, error_cb=_error_cb)

    def got_search_results(self, cbs, data):
        cb, error_cb = cbs

        try:
            data = data.split('_DIRECTORY_SEARCH_DATA =')[1].split('</script>')[0].strip()
            data = json.loads(data)

            results = data['results']

            feeds = []
            for result in results:
                #For some reason 'streamid' starts with 'feed/'
                url = result['streamid'][5:]
                feeds.append({'url': url, 'title': result['title']})

        except:
            error_cb()

        else:
            cb(feeds)

class Reddit(FeedSource, KeySaver):
    base_id = 'reddit'
    web_url = 'http://www.reddit.com/message/inbox/'
    title = _("Reddit Inbox")
    orangered_url = 'http://www.reddit.com/static/mail.png'
    login = 'https://www.reddit.com/api/login/%s' # % username
    #RSS uses slightly less bandwidth, but JSON provides newness info
    messages_url = 'http://www.reddit.com/message/inbox/.json?mark=false'
    mark_as_read = 'http://www.reddit.com/message/inbox/.rss?mark=true'
    inbox_url = 'http://www.reddit.com/message/messages/'

    def __init__(self, applet, username, password=None):
        self.applet = applet
        self.username = username
        self.url = self.base_id + '-' + username

        self.cookie = None
        self.should_update = False
        self.already_notified_about = []
        self.init_network_error = False

        #Get ready to update the feed, but don't actually do so.
        self.get_key(username, password)
        self.get_favicon('www.reddit.com')
        self.get_reddit_cookie()

    def get_reddit_cookie(self):
        if self.key is not None:
            if self.cookie is None:
                try:
                    data = urllib.urlencode({'user': self.username.lower(),
                        'passwd': self.key.password,
                        'op': 'login-main',
                        'id': '#login_login-main',
                        'r': 'reddit.com'})

                except:
                    self.error()

                else:
                    self.post_data(self.login % self.username.lower(), data,
                        server_headers = True, cb=self.got_reddit_cookie, error_cb=self.cookie_error)

    def cookie_error(self, *args):
        self.init_network_error = True
        self.error()

    def got_reddit_cookie(self, data, headers):
        self.init_network_error = False
        headers = str(headers).split('\n')

        #Save the cookie
        for line in headers:
            if line.find('Set-Cookie: ') == 0:
                cookie = urllib.unquote(line[12:].split(';')[0])

                #This happens if the username/password is wrong
                if cookie.find('reddit_first=') == 0:
                    self.error()
                    return

                self.cookie = urllib.unquote(line[12:].split(';')[0])

        if self.cookie is None:
            self.error()

        elif self.should_update:
            self.update()
            self.should_update = False

    def update(self):
        if self.cookie is None and not self.init_network_error:
            self.should_update = True

        elif self.init_network_error:
            self.should_update = True
            self.get_reddit_cookie()

        else:
            #Load the reading list with that magic SID as a cookie
            self.get_data(self.messages_url, {'Cookie': self.cookie}, cb=self.got_data)

    def got_data(self, data):
        try:
            parsed = json.loads(data)
        except:
            self.error()
            return

        self.entries = []
        self.num_new = 0
        self.num_notify = 0

        for message in parsed['data']['children'][:5]:
            #If it's a private message
            if message['data']['context'].strip() == '':
                url = self.inbox_url
                title = message['data']['subject']

            else:
                url = 'http://www.reddit.com' + message['data']['context']

                if message['data']['subject'] == 'comment reply':
                    title = _("Comment reply from %s") % message['data']['author']

                else:
                    title = _("Post reply from %s") % message['data']['author']

            new = message['data']['new']

            if new:
                self.num_new += 1

            notify = False
            if new and message['data']['id'] not in self.already_notified_about:
                self.already_notified_about.append(message['data']['id'])
                notify = True
                self.num_notify += 1

            self.entries.append(Entry(url, title, new, notify))

        self.applet.feed_updated(self)

        if self.num_new > 0:
            self.get_favicon('www.reddit.com-orangered', self.orangered_url)

        else:
            self.get_favicon('www.reddit.com')

    #If an item was clicked and it was the only unread one,
    #tell Reddit that we've read every message
    #Unfortunately, we can only mark all messages as read, not individual ones.
    def item_clicked(self, i):
        if self.entries[i]['new'] == True:
            if self.num_new == 1:
                self.num_new = 0
                deboldify(self.applet.feed_labels[self.url])
                deboldify(self.applet.displays[self.url].get_children()[i], True)
                self.get_favicon('www.reddit.com')

                self.get_data(self.mark_as_read, {'Cookie': self.cookie})

            else:
                self.num_new -= 1

class Twitter(FeedSource, StandardNew, KeySaver):
    base_id = 'twitter'
    web_url = 'http://twitter.com/'
    title = _("Twitter")
    timeline_url = 'https://twitter.com/statuses/friends_timeline.rss'
    replies_url = 'https://twitter.com/statuses/replies.rss'

    def __init__(self, applet, username, password=None, base_url='twitter-timeline'):
        self.applet = applet
        self.username = username
        self.url = base_url + '-' + username

        self.get_favicon('twitter.com')

        try:
            self.get_key(username, password)
            self.auth = base64.encodestring(username + ':' + self.password)
            self.auth = {'Authorization': 'Basic ' + self.auth}

        except:
            self.error()

        if base_url.find('twitter-timeline') == 0:
            self.use_timeline = True
            self.use_replies = False

        elif base_url.find('twitter-both') == 0:
            self.use_timeline = True
            self.use_replies = True

        else:
            self.use_timeline = False
            self.use_replies = True

    def update(self):
        if self.use_timeline and self.use_replies:
            self.have_timeline = False
            self.have_replies = False

        if self.use_timeline:
            self.get_data(self.timeline_url, self.auth, True, cb=self.got_timeline)

        if self.use_replies:
            self.get_data(self.replies_url, self.auth, True, cb=self.got_replies)

    def got_timeline(self, parsed):
        self.timeline = parsed

        if self.use_timeline and self.use_replies:
            self.have_timeline = True

            if self.have_replies:
                self.do_entries()

        else:
            self.do_entries()

    def got_replies(self, parsed):
        self.replies = parsed

        if self.use_timeline and self.use_replies:
            self.have_replies = True

            if self.have_timeline:
                self.do_entries()

        else:
            self.do_entries()

    def do_entries(self):
        self.entries = []
        urls = []

        if self.use_timeline:
            for entry in self.timeline.entries:
                parsed_entry = Entry(entry.link, entry.title)
                parsed_entry['time'] = entry.updated_parsed

                urls.append(entry.link)
                self.entries.append(parsed_entry)

        if self.use_replies:
            for entry in self.replies.entries:
                #Don't add a reply if it's in the user's timeline
                #Many (if not most) replies will also be in the user's timeline
                if entry.link not in urls:
                    parsed_entry = Entry(entry.link, entry.title)
                    parsed_entry['time'] = entry.updated_parsed

                    self.entries.append(parsed_entry)

        #Sort the (combined) feeds, newest first
        self.entries.sort(lambda a, b: cmp(b['time'], a['time']))

        self.entries = self.entries[:5]

        self.get_new()
        self.applet.feed_updated(self)
        self.applet.got_favicon(self)

class WebFeed(FeedSource, StandardNew):
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

        try:
            self.web_url = parsed.feed.link
        except:
            self.web_url = ''

        try:
            for entry in parsed.entries[:5]:
                self.entries.append(Entry(entry.link, entry.title))
        except:
            self.error()
            return

        self.get_new()

        self.applet.feed_updated(self)

        self.get_favicon()


def get_16x16(pb):
    if pb.get_width() != 16 or pb.get_height() != 16:
        pb2 = pb.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)
        del pb
        pb = pb2

    return pb

def boldify(widget, button=False):
    if button:
        widget = widget.child

    widget.set_markup('<span font_weight="bold">%s</span>' % widget.get_text())

def deboldify(widget, button=False):
    if button:
        widget = widget.child

    widget.set_markup(widget.get_text())
