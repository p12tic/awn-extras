#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, 2010 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
#
#File Browser Launcher
#About File

import pygtk
pygtk.require('2.0')
import gtk
import os

from awn.extras import _, __version__

def url_hook(about, url):
  os.system('xdg-open %s &' % url)

#Simple about dialog window
class About:
  def __init__(self):
    gtk.about_dialog_set_url_hook(url_hook)
    win = gtk.AboutDialog()
    win.set_name(_("File Browser Launcher"))
    win.set_copyright('Copyright 2009, 2010 sharkbaitbobby')
    win.set_authors(['sharkbaitbobby <sharkbaitbobby+awn@gmail.com>'])
    win.set_comments(_("A customizable launcher for browsing your files."))
    win.set_license('This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.')
    win.set_wrap_license(True)
    win.set_documenters(["sharkbaitbobby <sharkbaitbobby+awn@gmail.com>"])
    win.set_website('http://wiki.awn-project.org/File_Browser_Launcher')
    win.set_website_label('wiki.awn-project.org')
    win.set_logo_icon_name('stock_folder')
    win.set_icon_name('stock_folder')
    win.set_version(__version__)
    win.run()
    win.destroy()
