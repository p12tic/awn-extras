#!/usr/bin/python

#--------------------------------------------------------------------------------
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA    02111-1307    USA
#--------------------------------------------------------------------------------

# The icons of the "Black" icon theme are licensed under a
# Creative Commons Attribution-Share Alike 3.0 License.
#--------------------------------------------------------------------------------

# Name:                volume-control.py
# Version:             1.0
# Date:                March 2008
# Description: An applet for awn to control the computer's volume.
# Authors:        Richard "nazrat" Beyer
#                 Jeff "Jawbreaker" Hubbard
#                 Pavel Panchekha <pavpanchekha@gmail.com>

# Listing theme directories and showing icons
import os

# Drawing the GUI
import gtk

# Interaction with AWN
from awn.extras import AWNLib

# To later import alsaaudio
alsaaudio = None

class VolumeApplet:
    def __init__(self, awn):
        self.awn = awn
        self.awn.settings.require()

        # Scroll to change volume
        self.awn.connect("scroll-event", self.wheel)

        self.awn.module.get("alsaaudio", {"Ubuntu": "python-alsaaudio",
            "Gentoo": "dev-python/pyalsaaudio",
            "Mandriva": "python-alsaaudio"}, self.__init2)

    def __init2(self, module):
        # Store alsaaudio module
        global alsaaudio
        alsaaudio = module

        self.__readSettings()

        self.drawMainDlog()
        self.drawPrefDlog()
        self.backend.refresh()

    def __readSettings(self):
        # Theme
        try:
            self.theme = self.awn.settings["theme"]
        except:
            self.theme = "Tango"
            self.awn.settings["theme"] = "Tango"

        # Backend
        self.backend = Backend(self)

        try:
            self.backend.setChannel(self.awn.settings["channel"])
        except:
            self.awn.settings["channel"] = self.backend.setChannel()

    def __getIcon(self, name):
        themepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), \
            "Themes", self.theme)
        return self.awn.icon.file(os.path.join(themepath, \
            "audio-volume-%s.svg" % name))

    def setIcon(self):
        volume = self.backend.getVolume()
        if volume > 60 :
            icon = "high"
        elif volume > 30 :
            icon = "medium"
        elif volume > 0 :
            icon = "low"
        else:
            icon = "muted"

        themepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), \
            "Themes", self.theme)
        self.awn.icon.file(os.path.join(themepath, \
            "audio-volume-%s.svg" % icon))

    def wheel(self, widget=None, event=None):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.backend.up()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.backend.down()

    def setDevice(self, channel):
        self.backend.setChannel(channel)
        self.backend.refresh()
        self.awn.settings["channel"] = channel

    def setTheme(self, theme):
        self.theme = theme
        self.backend.refresh()
        self.awn.settings["theme"] = theme

    def drawMainDlog(self):
        self.main = self.awn.dialog.new("main")
        cont = gtk.HBox()
        cont.set_spacing(4)
        vCont = gtk.VBox ()
        vCont.set_spacing(4)

        self.main.volume = volume = gtk.VScale()
        volume.set_range(0, 100)
        volume.set_digits(0)
        volume.set_inverted(True)
        volume.set_value(self.backend.getVolume())

        bUp = gtk.Button ()
        bUp.set_relief(gtk.RELIEF_NONE)
        bUp.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_UP, \
            gtk.ICON_SIZE_BUTTON))

        bDown = gtk.Button ()
        bDown.set_relief(gtk.RELIEF_NONE)
        bDown.set_image(gtk.image_new_from_stock(gtk.STOCK_GO_DOWN, \
            gtk.ICON_SIZE_BUTTON))

        bMute = gtk.ToggleButton()
        bMute.set_relief(gtk.RELIEF_NONE)
        bMute.set_image(gtk.image_new_from_stock(gtk.STOCK_NO, \
            gtk.ICON_SIZE_BUTTON))

        bSettings = gtk.Button("Config")
        bSettings.set_relief(gtk.RELIEF_NONE)

        label = gtk.Label("Volume:")

        vCont.add(label)
        vCont.add(bUp)
        vCont.add(bDown)
        vCont.add(bMute)
        vCont.add(bSettings)
        cont.add(vCont)
        cont.add(volume)

        self.main.add(cont)

        bUp.connect("button-press-event", lambda x, y: self.backend.up())
        bDown.connect("button-press-event", lambda x, y: self.backend.down())
        bMute.connect("button-press-event", lambda x, y: self.backend.mute())
        bSettings.connect("button-press-event", lambda x, y: self.awn.dialogs.toggle("prefs"))
        volume.connect("value-changed", lambda x: self.backend.setVolume(volume.get_value()))
        volume.connect("scroll-event", self.wheel)

    def drawPrefDlog(self):
        self.prefs = self.awn.dialog.new("prefs", focus=False)
        cont = gtk.VBox()
        cont.set_spacing(4)

        # Device-Combo-Box:
        dLabel = gtk.Label("Mixer Channel:")

        device = gtk.combo_box_new_text()
        device.set_title("Mixer Channel")
        for m in alsaaudio.mixers():
            device.append_text(m)

        # Theme-Combo-Box:
        tLabel = gtk.Label("Theme:")

        theme = gtk.combo_box_new_text()
        theme.set_title("Theme")
        themes = [i for i in os.listdir(os.path.join(os.path.dirname( \
            os.path.abspath(__file__)), "Themes"))]
        for i in themes:
            theme.append_text(i)

        cont.add(dLabel)
        cont.add(device)
        cont.add(tLabel)
        cont.add(theme)

        self.prefs.add(cont)

        theme.connect("changed", lambda x: self.setTheme(theme.get_active_text()))
        device.connect("changed", lambda x: self.setDevice(device.get_active_text()))

class Backend:
    def __init__(self, parent):
        self.tmpVolume = 0
        self.parent = parent

    def setChannel(self, channel=None):
        if channel:
            self.channel = channel
        else:
            try:
                self.channel = alsaaudio.mixers()[0]
            except:
                self.channel = "PCM"

        return self.channel

    def getVolume(self):
        return alsaaudio.Mixer(self.channel).getvolume()[0]

    def setVolume(self, value):
        alsaaudio.Mixer(self.channel).setvolume(int(value))
        self.parent.awn.title.set("Volume: " + str(self.getVolume()) + "%")
        self.parent.setIcon()
        self.parent.main.volume.set_value(value)

    def refresh(self):
        self.setVolume(self.getVolume())

    def up(self):
        self.setVolume(min(100, self.getVolume() + 4))
        self.parent.setIcon()

    def down(self):
        self.setVolume(max(0, self.getVolume() - 4))
        self.parent.setIcon()

    def mute(self):
        volume = self.getVolume()
        if volume > 0:
            self.tmpVolume = volume
            self.setVolume(0)
        else:
            self.setVolume(self.tmpVolume)
        self.parent.setIcon()

if __name__ == "__main__":
    # Initiation and metadata
    applet = AWNLib.initiate({"name": "Volume Control Applet",
        "short": "volume",
        "author": "Pavel Panchekha",
        "email": "pavpanchekha@gmail.com",
        "description": "An applet to control the computer's volume"})

    # Applet creating
    VolumeApplet(applet)

    # Applet starts
    AWNLib.start(applet)
