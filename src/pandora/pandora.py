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


URL = 'https://www.pandora.com/radio/tuner_8_5_0_1_pandora.swf'


import os
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
applet_version = "0.3.1"
applet_description = "Listen to Pandora from Awn"
applet_theme_logo = "pandora"

class PandoraApplet:
    """ Listens to Pandora from Awn """
    def __init__(self, applet):
        self.applet = applet
        
        applet.title.set("Pandora")
        
        self.dialog = applet.dialog.new("main")
        
        self.moz = gtkmozembed.MozEmbed()
        self.moz.set_size_request(640, 535)
        self.moz.load_url(URL)
        
        self.dialog.add(self.moz)

if __name__ == "__main__":
    awnlib.init_start(PandoraApplet, {"name": applet_name,
        "short": "pandora",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_theme_logo,
        "author": "Sharkbaitbobby",
        "copyright-year": 2008,
        "authors": ["Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>"]})
