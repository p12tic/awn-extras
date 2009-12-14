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
import sys
import urllib
import urllib2

import dbus

config_dir = os.environ['HOME'] + '/.config/awn/applets/'
config_path = os.environ['HOME'] + '/.config/awn/applets/feeds.txt'

tmp_dir = '/tmp/awn-feeds-applet'

url_list = []


#Get the list of feeds
if not os.path.exists(config_path):
    os.makedirs(config_dir)

try:
    fp = open(config_path)
    pre_list = fp.read().split()

    for url in pre_list:
        url = url.strip()

        if url != '':
            url_list.append(url)

#Default to the Planet Awn feed
except:
    url_list = ['http://planet.awn-project.org/?feed=atom']
    fp = open(config_path, 'w+')
    fp.write('http://planet.awn-project.org/?feed=atom')
    fp.close()


#Download and save the feeds to the /tmp dir
if not os.path.exists(tmp_dir):
    os.mkdir(tmp_dir)

i = 0
for url in url_list:
    feed = ''

    if url == 'google-reader':
        feed = url

    else:
        try:
            fp = urllib2.urlopen(url, timeout=60)
            feed = fp.read()
            fp.close()

        except IOError:
            fp = open(tmp_dir + '/ioerror', 'w+')
            fp.write(' ')
            fp.close()

    fp = open(tmp_dir + '/%s.xml' % i, 'w+')
    fp.write(feed)
    fp.close()

    i += 1

#Notify the applet of our done-ness via D-Bus
bus = dbus.SessionBus()

service = bus.get_object('org.awnproject.Feeds', '/org/awnproject/Feeds')

service.get_dbus_method('DoneUpdating', 'org.awnproject.Feeds')()
