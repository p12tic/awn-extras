# Copyright (C) 2007 Aren Olson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 1, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.

import plugins, dbus, time, threading

PLUGIN_NAME = "AWN"
PLUGIN_AUTHORS = ['Aren Olson <reacocard@gmail.com>', 'Bryan Forbes <bryan@reigndropsfall.net>', 'Alberto Pagliarini <batopa@gmail.com>']
PLUGIN_VERSION = '0.5'
PLUGIN_DESCRIPTION = r"""Displays the current album's cover art and progress in AWN."""

PLUGIN_ENABLED = False
PLUGIN_ICON = None

SHOW_PROGRESS = False
SHOW_COVER = True

class mainloop(threading.Thread):
    """
        Runs every second, updates cover, progress.
    """
    def __init__(self):
        threading.Thread.__init__(self)
        self.setup_awn()
        self.cover = None
        self.setDaemon(True)

    def run(self):
        while 1:
            if not self.connected:
                self.setup_awn()
            try:
                #Set album cover
                newcover = APP.cover.loc
                if SHOW_COVER:
                    if 'nocover' in newcover:
                        self.awn.UnsetTaskIconByName(APP.window.get_title())
                        self.cover = None
                    else:
                        self.awn.SetTaskIconByName(APP.window.get_title(), newcover)
                        self.cover = newcover

                #Update progress meter.
                if SHOW_PROGRESS:
                    if APP.player.is_playing():
                        position = int(round(APP.player.get_current_position(),0))
                        self.awn.SetProgressByName(APP.window.get_title(), position)
                    else:
                        self.awn.SetProgressByName(APP.window.get_title(), 100)

            except:
                self.connected = False
            time.sleep(1)

    def setup_awn(self):
        try:
            bus_obj = dbus.SessionBus().get_object("com.google.code.Awn",
                "/com/google/code/Awn")
            self.awn = dbus.Interface(bus_obj, "com.google.code.Awn")
            self.connected = True
        except:
            self.connected = False
            self.awn = None

def initialize():
    """
        Set up the main loop thread that does everything.
    """
    loop = mainloop()
    loop.start()

    return True

def destroy():
    """
        Disconnect from AWN.
    """
    try:
        loop.awn.UnsetTaskIconByName(APP.window.get_title())
        loop.awn.SetProgressByName(APP.window.get_title(), 100)
    except:
        pass
    loop = None

