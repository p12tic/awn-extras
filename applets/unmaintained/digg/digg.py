#!/usr/bin/python
#
#Copyright 2008, 2009 Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import awn
from awn.extras import _, awnlib

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
    print 'Gtkmozembed is needed to run Digg Applet, please install.'
    print ' * On Debian or Ubuntu based systems, install python-gnome2-extras'
    print ' * On Gentoo based systems, install dev-python/gnome-python-extras'
    print ' * On Fedora based systems, install gnome-python2-gtkmozembed'
    print ' * On SUSE based systems, install python-gnome-extras'
    print ' * On Mandriva based systems, install gnome-python-gtkmozembed'
    print 'See: http://wiki.awn-project.org/Awn_Extras:Dependency_Matrix'
    print '       #####################################'

# Add pop up if gtkmozembed isn't found
awn.check_dependencies(globals(), 'gtkmozembed')

applet_name = _("Digg Applet")
applet_version = "0.3.3"
applet_description = _("Browse Digg from Awn")
applet_theme_logo = "digg"


class DiggApplet:

    """Browses Digg from AWN.

    """

    def __init__(self, applet):
        self.applet = applet

        applet.tooltip.set(_("Digg"))

        self.dialog = applet.dialog.new("main")

        self.moz = gtkmozembed.MozEmbed()
        self.moz.set_size_request(450, 580)
        self.moz.load_url('http://digg.com/iphone#_stories')

        self.dialog.add(self.moz)


if __name__ == "__main__":
    awnlib.init_start(DiggApplet, {"name": applet_name,
        "short": "digg",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_theme_logo,
        "author": "Sharkbaitbobby",
        "artists": ["Jakub Szypulka"],
        "copyright-year": "2008, 2009",
        "authors": ["Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>"]})
