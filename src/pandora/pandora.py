#!/usr/bin/python
"""
Copyright 2008 Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import htmllib, formatter
import urllib2
import gtk
import pygtk
import awn
from awn.extras import awnlib

# workaround for weirdness with regards to Ubuntu + gtkmozembed
if os.path.exists('/etc/issue'):
  import re
  fp = open('/etc/issue')
  os_version = fp.read()
  fp.close()
  if re.search(r'7\.(?:04|10)', os_version): # feisty or gutsy
    os.putenv('LD_LIBRARY_PATH', '/usr/lib/firefox')
    os.putenv('MOZILLA_FIVE_HOME', '/usr/lib/firefox')

try:
  import gtkmozembed
except ImportError:
  print '       #####################################'
  print 'Gtkmozembed is needed to run Pandora, please install.'
  print ' * On Debian or Ubuntu based systems, install python-gnome2-extras'
  print ' * On Gentoo based systems, install dev-python/gnome-python-extras'
  print ' * On Fedora based systems, install gnome-python2-gtkmozembed'
  print ' * On SUSE based systems, install python-gnome-extras'
  print ' * On Mandriva based systems, install gnome-python-gtkmozembed'
  print 'See: http://wiki.awn-project.org/Awn_Extras:Dependency_Matrix'
  print '       #####################################'

# Add pop up if gtkmozembed isn't found
awn.check_dependencies(globals(), 'gtkmozembed')

applet_name = "Pandora"
applet_version = "0.3.3"
applet_description = "Listen to Pandora from Awn"
applet_theme_logo = "pandora"

class GetPandoraUrl(htmllib.HTMLParser):
    def __init__(self, formatterinit) :
        htmllib.HTMLParser.__init__(self, formatterinit)
        self.values = []

    def start_param(self, attrs) :
        if len(attrs) > 0 :
            for attr in attrs :
                if attr[0] == "value" :
                    self.values.append(attr[1])

    def get_values(self) :
        return self.values

class PandoraApplet:
    """ Listens to Pandora from Awn """
    def __init__(self, applet):
        self.applet = applet
        
        applet.tooltip.set("Pandora")
        
        self.dialog = applet.dialog.new("main")
        
        self.moz = gtkmozembed.MozEmbed()
        try:
            pandurl=self.applet.settings["url"]
        except:
            pandurl=self.returnurl()
            self.applet.settings["url"] = pandurl
        self.moz.set_size_request(640, 250)
        try:
            site = urllib2.urlopen(pandurl)
            meta=site.info()
            if meta['Content-Type'] == 'application/x-shockwave-flash':
                self.moz.load_url(pandurl)
            else:
                return Error
        except:
            pandurl=self.returnurl()
            self.applet.settings["url"] = pandurl
            self.moz.load_url(pandurl)
        self.dialog.add(self.moz)

        self.setup_context_menu()

        applet.connect("button-press-event", self.button_press_event_cb)

    def setup_context_menu(self):
        menu = self.applet.dialog.menu
        self.play = gtk.ImageMenuItem(stock_id=gtk.STOCK_MEDIA_PLAY)
        self.play.connect("activate", self.playMusic)
        menu.insert(self.play, 3)
        self.stop = gtk.ImageMenuItem(stock_id=gtk.STOCK_STOP)
        self.stop.connect("activate", self.stopMusic)
        menu.insert(self.stop, 4)

    def stopMusic(self,inp):
       self.moz.load_url("about:blank")

    def playMusic(self,inp):
       self.moz.go_back()

    def returnurl(self):
        try:
            page=urllib2.urlopen('http://www.pandora.com/?cmd=mini')
            format = formatter.NullFormatter()
            paramvalues = GetPandoraUrl(format)
            paramvalues.feed(page.read())
            paramvalues.close()
            urlvalues=paramvalues.get_values()
            panurl=urlvalues[0]
            return panurl
        except urllib2.URLError:
            print 'Pandora Applet: No network connection'
            self.pandurl=self.applet.settings["url"]
            return self.pandurl

    def button_press_event_cb(self, widget, event):
        if event.button == 1:  
            if self.dialog.flags & gtk.VISIBLE:
                self.dialog.hide()
            else:
                self.dialog.show_all()
                if self.moz.get_location() == 'about:blank':
                    self.moz.go_back()

if __name__ == "__main__":
    awnlib.init_start(PandoraApplet, {"name": applet_name,
        "short": "pandora",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_theme_logo,
        "author": "Sharkbaitbobby",
        "copyright-year": 2009,
        "authors": ["Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>"]})
