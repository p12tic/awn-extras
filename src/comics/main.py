#!/usr/bin/env python
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


# Import standard modules
import gettext
import gobject
import gtk
import locale
import os
import re
import sys
import tempfile
import threading
from locale import gettext as _
from os.path import join

# Import Comics! modules
import comics_add
import comics_manage
import comics_view
from feed.settings import Settings
from feed import FeedContainer
from shared import *


"""This is the path to the named pipe that is used to send commands to the
application."""
COMMAND_PIPE = os.path.join(STRIPS_DIR, 'commands')

"""If no commands are passed on the command line, this command will be
executed."""
DEFAULT_COMMAND = 'toggle_visibility'

"""When this command is passed to the application, the command pipe will be
removed."""
CLEAN_COMMAND = 'clean'


class Command(object):
	"""A class that describes a command."""
	
	"""The regular expression that matches an entire command line. A command
	line is on the format 'a_command [parameter...]' or
	simply 'another_command'."""
	LINE_RE = re.compile(r'(?P<command>\w*)(?:\s+(?P<parameters>.+))?')
	
	"""The regular expression that matches a single parameter value. A parameter
	value is on the format 123 or "a string"."""
	PARAMETER_RE = re.compile(r''
		+ r'(?P<int>-?\d+)|'
		+ r'(?:"(?P<str>(?:(?:\\")|.)*?)")|'
		+ r'(?P<token>\S+)')
	
	"""Parameter tokens with any of these values are interpreted as the boolean
	value True."""
	TRUE_VALUES = ['true', 'yes', 'on']
	
	"""Parameter tokens with any of these values are interpreted as the boolean
	value False."""
	FALSE_VALUES = ['false', 'no', 'off']
	
	def __init__(self, command = None):
		self.command = ''
		self.parameters = []
		
		# Do not parse empty command lines
		if command is None:
			return
		
		# Extract the command verb and its parameters
		line = self.LINE_RE.match(command)
		if line is None:
			return
		self.command = line.group('command')
		
		# There may be no parameters, and re.finditer does not like this
		if line.group('parameters') is None:
			return
		
		for parameter in self.PARAMETER_RE.finditer(line.group('parameters')):
			if parameter.group('int'):
				# Interpret all-digit tokens as numbers
				self.parameters.append(int(parameter.group('int')))
			elif parameter.group('str'):
				# Interpret quoted tokens as strings
				self.parameters.append(parameter.group('str'))
			elif parameter.group('token'):
				token = parameter.group('token')
				if token in self.TRUE_VALUES:
					self.parameters.append(True)
				elif token in self.FALSE_VALUES:
					self.parameters.append(False)
				else:
					# Interpret unknown tokens a simple strings
					self.parameters.append(token)
	
	def value_to_string(self, value):
		"""Converts a value to a string."""
		if isinstance(value, int):
			return str(value)
		elif isinstance(value, bool):
			if value:
				return self.TRUE_VALUES[0]
			else:
				return self.FALSE_VALUES
		elif ' ' in value:
			return '"%s"' % value
		else:
			return value
	
	def __str__(self):
		return ' '.join(map(self.value_to_string,
			[self.command] + self.parameters))


class Application(object):
	def command_listener(self):
		"""Reads commands from a stream until the exit command is received."""
		stream = open(COMMAND_PIPE, 'r+')
		
		try:
			while True:
				command = Command(stream.readline())
				gobject.idle_add(self.execute_command, command)
				if command.command == 'exit':
					break
		finally:
			stream.close()
	
	def execute_command(self, command):
		"""Invoked by the command listening thread whenever a command is sent to
		the application."""
		try:
			# Execute the requested command
			getattr(self, 'do_' + command.command)(*command.parameters)
		except AttributeError:
			print _('Unknown command sent: %s') % str(command)
		except TypeError, e:
			print e
		
		# Make sure this callback is not called again
		return False
	
	def __init__(self, paths, cache):
		"""Creates an application instance by loading feed descriptors from all
		paths in paths and strip caches from the directory cache."""
		self.feeds = FeedContainer()
		for path in paths:
			self.feeds.load_directory(path)
		
		# Create the comics
		self.comics = []
		for filename in filter(lambda f: f.endswith('.strip'),
				os.listdir(cache)):
			filename = os.path.join(cache, filename)
			settings = Settings(filename)
			settings['cache-file'] = filename.rsplit('.', 1)[0] + '.cache'
			self.comics.append(comics_view.ComicsViewer(self, settings, False))
		
		# The comics are initially hidden
		self.do_hide()
		
		# Start listening for commands
		self.command_thread = threading.Thread(target = self.command_listener)
		self.command_thread.start()
	
	def show_message(self, message, icon):
		print message
	
	def do_exit(self):
		"""Causes the application to terminate."""
		gtk.main_quit()
	
	def do_set_visibility(self, visibility):
		"""Shows or hides all comic strips depending of the value of
		visibility."""
		for comic in self.comics:
			comic.set_visibility(visibility)
		self.visible = visibility
	
	def do_show(self):
		"""Shows all comic strips."""
		self.do_set_visibility(True)
	
	def do_hide(self):
		"""Hides all comic strips."""
		self.do_set_visibility(False)
	
	def do_toggle_visibility(self):
		"""Shows or hides all comic strips."""
		self.do_set_visibility(not self.visible)
	
	def do_manage(self):
		"""Shows the configuration interface."""
		manager = comics_manage.ComicsManager(self.feeds)
		manager.show()


if __name__ == '__main__':
	# Read the command
	command = Command()
	if len(sys.argv) > 1:
		command.command = sys.argv[1]
	else:
		command.command = DEFAULT_COMMAND
	if len(sys.argv) > 2:
		command.parameters = sys.argv[2:]
	
	# If the named pipe exists, another instance is running and we just pass the
	# command line on
	if os.access(COMMAND_PIPE, os.F_OK):
		# If we receive the clean command, we have to remove the command pipe
		if command.command == CLEAN_COMMAND:
			os.unlink(COMMAND_PIPE)
			sys.exit(0)
		else:
			out = open(COMMAND_PIPE, 'w+')
			try:
				out.write(str(command) + '\n')
			finally:
				out.close()
			sys.exit(0)
	
	# Initialise internationalisation
	locale.setlocale(locale.LC_ALL, '')
	locale.bindtextdomain('comics', LOCALE_DIR)
	locale.textdomain('comics')
	
	# Initialise GObject and GTK
	gobject.threads_init()
	gobject.set_application_name(_('Comics!'))
	gtk.gdk.threads_init()
	gtk.window_set_default_icon_from_file(os.path.join(ICONS_DIR,
		'comics-icon.svg'))
	
	# Initialize user agent string
	import urllib
	class ComicURLOpener(urllib.FancyURLopener):
		version = 'Mozilla/3.0'
	urllib._urlopener = ComicURLOpener()
	
	# Make sure that all required directories exist
	if not os.access(USER_DIR, os.W_OK):
		if os.access(ALT_USER_DIR, os.W_OK):
			os.symlink(ALT_USER_DIR, USER_DIR)
		else:
			os.makedirs(USER_DIR)
	if not os.access(USER_FEEDS_DIR, os.W_OK):
		os.makedirs(USER_FEEDS_DIR)
	
	# Create the command pipe
	os.mkfifo(COMMAND_PIPE)
	
	# Create the application and start the main loop
	application = Application([SYS_FEEDS_DIR, USER_FEEDS_DIR], STRIPS_DIR)
	application.execute_command(command)
	gtk.main()
	
	# Remove the command pipe
	os.unlink(COMMAND_PIPE)

