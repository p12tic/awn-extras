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
import gtk

#Borrowed LaunchManager from "gimmie"
class LaunchManager:
    '''
    A program lauching utility which handles opening a URI or executing a
    program or .desktop launcher, handling variable expansion in the Exec
    string.

    Adds the launched URI or launcher to the ~/.recently-used log.  Sets a
    DESKTOP_STARTUP_ID environment variable containing useful information such
    as the URI which caused the program execution and a timestamp.

    See the startup notification spec for more information on
    DESKTOP_STARTUP_IDs.
    '''
    def __init__(self):
        return

    def launch_uri(self, uri, mimetype = None):
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

    def launch_command_with_uris(self, command, uri_list, launcher_uri = None):
        if command.rfind("%U") > -1:
            uri_str = ""
            for uri in uri_list:
                uri_str = uri_str + " " + uri
            return self.launch_command(command.replace("%U", uri_str), launcher_uri)
        elif command.rfind("%F") > -1:
            file_str = ""
            for uri in uri_list:
                uri = self.get_local_path(self, uri)
                if uri:
                    file_str = file_str + " " + uri
                else:
                    print " !!! Command does not support non-file URLs: ", command
            return self.launch_command(command.replace("%F", file_str), launcher_uri)
        elif command.rfind("%u") > -1:
            startup_ids = []
            for uri in uri_list:
                startup_ids.append(self.launch_command(command.replace("%u", uri), launcher_uri))
            else:
                return self.launch_command(command.replace("%u", ""), launcher_uri)
            return startup_ids
        elif command.rfind("%f") > -1:
            startup_ids = []
            for uri in uri_list:
                uri = self.get_local_path(self, uri)
                if uri:
                    startup_ids.append(self.launch_command(command.replace("%f", uri),
                                                          launcher_uri))
                else:
                    print " !!! Command does not support non-file URLs: ", command
            else:
                return self.launch_command(command.replace("%f", ""), launcher_uri)
            return startup_ids
        else:
            return self.launch_command(command, launcher_uri)

    def make_startup_id(self, key, ev_time = None):
        if not ev_time:
            ev_time = gtk.get_current_event_time()
        if not key:
            return "STACKS_TIME%d" % ev_time
        else:
            return "STACKS:%s_TIME%d" % (key, ev_time)

    def parse_startup_id(self, id):
        if id and id.startswith("STACKS:"):
            try:
                uri = id[len("STACKS:"):id.rfind("_TIME")]
                timestamp = id[id.rfind("_TIME") + len("_TIME"):]
                return (uri, timestamp)
            except IndexError:
                pass
        return (None, None)

    def launch_command(self, command, launcher_uri = None):
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

