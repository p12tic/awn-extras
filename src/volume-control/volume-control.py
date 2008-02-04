"""
--------------------------------------------------------------------------------
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License version 2 as
 published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA    02111-1307    USA
--------------------------------------------------------------------------------

 The icons of the "Black" icon theme are licensed under a
 Creative Commons Attribution-Share Alike 3.0 License.
--------------------------------------------------------------------------------

Name:                volume-control.py
Version:         0.5.
Date:                September/October 2007
Description: A python Applet for the avant-windows-navigator to control the volume.

Authors:         Richard "nazrat" Beyer
                         Jeff "Jawbreaker" Hubbard
                         Pavel Panchekha <pavpanchekha@gmail.com>
"""

#!/usr/bin/python
import sys, os
import gobject
import gtk
from gtk import gdk
import AWNLib

alsaaudio = None

class VolumeApplet:
    def __init__(self, awn):
        self.awn = awn
        self.awn.settings.require()

        self.theme = "Black"
        self.backend = Backend(self)

        try:
            self.backend.setChannel(self.awn.settings["channel"])
        except:
            self.awn.settings["channel"] = self.backend.setChannel()

        try:
            self.theme = self.awn.settings["theme"]
        except:
            self.theme = "Tango"
            self.awn.settings["theme"] = "Tango"

        self.awn.connect("scroll-event", self.wheel)

        self.awn.module.get("alsaaudio", {"Ubuntu": "python-alsaaudio"}, self.init2)

    def init2(self, module):
        global alsaaudio
        alsaaudio = module
        self.drawMainDlog()
        self.drawPrefDlog()
        self.backend.setVolume(self.backend.getVolume())

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
        bSettings.connect("button-press-event", self.showSettings)
        volume.connect("value-changed", lambda x: self.backend.setVolume(volume.get_value()))
        volume.connect("scroll-event", self.wheel)

    def drawPrefDlog(self):
        self.prefs = self.awn.dialog.new("secondary", focus=False)
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

        device.connect("changed", lambda x: self.deviceRefresh(device.get_active_text()))
        theme.connect("changed", lambda x: self.themeRefresh(theme.get_active_text()))

    def setIcon(self):
        volume = self.backend.getVolume()
        if volume > 60 :
            icon = self.getIcon("high")
        elif volume > 30 :
            icon = self.getIcon("medium")
        elif volume > 0 :
            icon = self.getIcon("low")
        else:
            icon = self.getIcon("muted")
        self.awn.icon.set(icon)

    def wheel(self, widget=None, event=None):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.backend.up()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.backend.down()

    def showSettings(self, x=None, y=None):
        self.main.hide()
        self.prefs.show_all()

    def deviceRefresh(self, channel):
        self.backend.setChannel(channel)
        self.backend.setVolume(self.backend.getVolume())
        self.awn.settings["channel"] = channel

    def themeRefresh(self, theme):
        self.theme = theme
        self.backend.setVolume(self.backend.getVolume())
        self.awn.settings["theme"] = theme

    def themePath(self):
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), "Themes", self.theme)

    def getIcon(self, name):
        return self.awn.icon.getFile(os.path.join(self.themePath(), "audio-volume-%s.svg" % name))

class Backend:
    def __init__(self, parent):
        self.tmpVolume = 0
        self.parent = parent

    def setChannel(self, channel=None):
        if channel:
            self.channel = alsaaudio.mixers().index(channel)
        else:
            try:
                self.channel = alsaaudio.mixers()[0]
            except:
                self.channel = "PCM"
        return self.channel

    def getVolume(self):
        return alsaaudio.Mixer(self.channel).getvolume()[0]

    def setVolume(self, value):
        alsaaudio.Mixer(self.channel).setvolume(value)
        self.parent.awn.title.set("Volume: " + str(self.getVolume()) + "%")
        self.parent.setIcon()
        self.parent.main.volume.set_value(value/1.0)

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
    applet = AWNLib.initiate({"name": "Volume Control Applet", "short": "volume"})
    VolumeApplet(applet)
    AWNLib.start(applet)
