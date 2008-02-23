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
import threading
import urllib


class Downloader(gobject.GObject, threading.Thread):
	__gsignals__ = dict(
		completed = (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE,
			(gobject.TYPE_INT,)))
	
	DOWNLOAD_OK = 0
	DOWNLOAD_TRANSFER_ERROR = 1
	DOWNLOAD_OTHER_ERROR = 2
	
	def __init__(self, url, filename = None):
		"""Create a new downloader for the specified URL."""
		threading.Thread.__init__(self)
		gobject.GObject.__init__(self)
		
		self.url = url
		self.filename = filename
	
	def emit(self, *args):
		gobject.idle_add(gobject.GObject.emit, self, *args)
	
	def run(self):
		try:
			self.filename, headers = urllib.urlretrieve(self.url, self.filename)
			self.emit('completed', Downloader.DOWNLOAD_OK)
		except:
			self.emit('completed', Downloader.DOWNLOAD_TRANSFER_ERROR)
		
	def download(self):
		self.setDaemon(True)
		self.start()

