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


from os import getenv
from os.path import join, split
import urllib
from xdg import BaseDirectory

# Data locations
SHARE_DIR		= join(split(__file__)[0])
ALT_USER_DIR	= join(getenv('HOME'), '.comics')
USER_DIR		= join(BaseDirectory.xdg_config_home, 'awn', 'applets',
	'comics')

SYS_FEEDS_DIR	= join(SHARE_DIR, 'feeds')
USER_FEEDS_DIR	= join(USER_DIR, 'feeds')
PLUGINS_DIR		= join(SHARE_DIR, 'feed', 'plugins')
GLADE_DIR		= join(SHARE_DIR, 'glade')
ICONS_DIR		= join(SHARE_DIR, 'icons')
LOCALE_DIR		= join(SHARE_DIR, 'locale')

STRIPS_DIR		= USER_DIR
CACHE_FILE		= join(USER_DIR, '%s.cache')

