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


from feed import FeedContainer
from os import access, getenv, mkdir, W_OK
from os.path import join, split

# Data locations
SHARE_DIR		= join(split(__file__)[0])
USER_DIR		= join(getenv('HOME'), '.comics')

SYS_FEEDS_DIR	= join(SHARE_DIR, 'feeds')
USER_FEEDS_DIR	= join(USER_DIR, 'feeds')
GLADE_DIR		= join(SHARE_DIR, 'glade')
PIXMAPS_DIR		= join(SHARE_DIR, 'pixmaps')
LOCALE_DIR		= join(SHARE_DIR, 'locale')

STRIPS_DIR		= USER_DIR
CACHE_FILE		= join(USER_DIR, '%s.cache')

if not access(USER_DIR, W_OK):
	mkdir(USER_DIR)
if not access(USER_FEEDS_DIR, W_OK):
	mkdir(USER_FEEDS_DIR)

feeds = FeedContainer()
feeds.load_directory(SYS_FEEDS_DIR)
feeds.load_directory(USER_FEEDS_DIR)

