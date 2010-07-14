#!/usr/bin/env python

# Copyright (c) 2007 Timon ter Braak
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

import os
import re

import gtk
from xdg import DesktopEntry

# Pattern to extract the part of the path that doesn't end with %<a-Z>
exec_pattern = re.compile("^(.*?)\s+\%[a-zA-Z]$")

class LaunchManager:

    """A program lauching utility which handles opening a URI or executing a
    program or .desktop launcher, handling variable expansion in the Exec
    string.

    Adds the launched URI or launcher to the ~/.recently-used log.  Sets a
    DESKTOP_STARTUP_ID environment variable containing useful information such
    as the URI which caused the program execution and a timestamp.

    See the startup notification spec for more information on
    DESKTOP_STARTUP_IDs.

    """

    def launch_uri(self, uri, mimetype=None):
        assert uri, "Must specify URI to launch"

        child = os.fork()
        if not child:
            # Inside forked child
            os.setsid()
            os.environ['STACKS_LAUNCHER'] = uri
            os.environ['DESKTOP_STARTUP_ID'] = self.make_startup_id(uri)
            os.spawnlp(os.P_NOWAIT, "xdg-open", "xdg-open", uri)
            os._exit(0)
        else:
            os.wait()
        return child
 
    def get_local_path(self, uri):
        scheme, path = urllib.splittype(uri)
        if scheme == None:
            return uri
        elif scheme == "file":
            path = urllib.url2pathname(path)
            if path[:3] == "///":
                path = path[2:]
            return path
        return None

    def make_startup_id(self, key, ev_time=None):
        if not ev_time:
            ev_time = gtk.get_current_event_time()
        if not key:
            return "STACKS_TIME%d" % ev_time
        else:
            return "STACKS:%s_TIME%d" % (key, ev_time)

    def launch_command(self, command, launcher_uri=None):
        startup_id = self.make_startup_id(launcher_uri)
        child = os.fork()
        if not child:
            # Inside forked child
            os.setsid()
            os.environ['DESKTOP_STARTUP_ID'] = startup_id
            if launcher_uri:
                os.environ['STACKS_LAUNCHER'] = launcher_uri
            os.popen2(command)
            os._exit(0)
        else:
            os.wait()
            return (child, startup_id)

    def launch_dot_desktop(self, desktop_path):
        assert desktop_path.startswith("file://")
        desktop_path = desktop_path[7:]
        if not os.path.exists(desktop_path):
            return

        item = DesktopEntry.DesktopEntry(desktop_path)

        type = item.getType()
        if type == "Application":
            path = item.getExec()
            # Strip last part of path if it contains %<a-Z>
            match = exec_pattern.match(path)
            if match is not None:
                path = match.group(1)
            self.launch_command(path, desktop_path)
        elif type == "Link":
            command = "xdg-open %s" % item.getURL()
            self.launch_command(command, desktop_path)
