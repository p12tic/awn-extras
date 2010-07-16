#!/usr/bin/env python
# Copyright (C) 2010  onox <denkpadje@gmail.com>
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
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import os

import gtk
from desktopagnostic import fdo, vfs


class LaunchManager:

    """A program lauching utility which handles opening a URI or
    executing a program or .desktop launcher.

    Sets a DESKTOP_STARTUP_ID environment variable containing useful
    information such as the URI which caused the program execution and
    a timestamp.

    See the startup notification spec for more information on
    DESKTOP_STARTUP_IDs.

    """

    def launch_uri(self, uri, mimetype=None):
        file = vfs.File.for_uri(uri)

        if file is not None and file.exists():
            try:
                file.launch()
            except glib.GError:
                print "Error when opening: %s" % e
        else:
            print "File at URI not found (%s)" % uri

    def launch_dot_desktop(self, desktop_uri):
        file = vfs.File.for_uri(desktop_uri)

        if file is not None and file.exists():
            entry = fdo.DesktopEntry.for_file(file)

            if entry.key_exists("Exec"):
                if entry.key_exists("StartupNotify"):
                    ev_time = gtk.get_current_event_time()
                    os.environ['DESKTOP_STARTUP_ID'] = "STACKS:%s_TIME%d" % (desktop_uri, ev_time)

                try:
                    entry.launch(0, None)
                except glib.GError:
                    print "Error when launching: %s" % e

                if entry.key_exists("StartupNotify"):
                    del os.environ['DESKTOP_STARTUP_ID']
        else:
            print "File not found (%s)" % desktop_uri
