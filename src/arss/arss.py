#!/usr/bin/env python

# Copyright (c) 2007 Randal Barlow
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

import sys, os
import awn
import gtk
from gtk import gdk
import menus
import feedparserdb
import arssconfig
userpath = os.path.expanduser('~/')
_location = __file__[::-1][__file__[::-1].index('/'):][::-1]


if 'AWNDEV' in os.environ.keys() and os.environ['AWNDEV'] == 'TRUE':
    import pango
    print "Entering development mode!"
    from ipython_view import *
    def IPythonWindow(vars):
        W = gtk.Window()
        W.set_size_request(750,550)
        W.set_resizable(True)
        S = gtk.ScrolledWindow()
        S.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
        V = IPythonView()
        font = "Luxi Mono 10"
        V.modify_font(pango.FontDescription(font))
        V.set_wrap_mode(gtk.WRAP_CHAR)
        V.show()
        S.add(V)
        S.show()
        W.add(S)
        W.show()
        W.connect('delete_event',lambda x,y:False)
        W.connect('destroy',lambda x:gtk.main_quit())
        V.updateNamespace(vars)

def get_icon(name, size):
    """
    returns a pixbuf from a file
    """
    return gdk.pixbuf_new_from_file(name).scale_simple(size, size, gtk.gdk.INTERP_BILINEAR)

class App(awn.AppletSimple):
    """
    Main Applet Thing
    """
    def __init__(self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
        self.size = height
        self.set_icon(get_icon(_location + 'Icons/feed-icon.svg', self.size))
        self.connect("button-press-event", self.clicked ,) # set icon clicks
        self.get_feeds()
        
    def get_feeds(self):
        listoffeeds = arssconfig.get_feeds()
        self.Database = feedparserdb.FeedDatabase("sqlite:///"+userpath+"/.config/awn/arsstest.db", echo=False)
        self.Database.update_feeds(arssconfig.get_feeds())
        self.feeds = self.Database.get_feed_objects()
        
    def update_menu(self):
        self.menu = menus.RssMenu()
        self.menu.build_children(self.feeds, self)
    def clicked(self, widget, event):
        """
        This Method Handles awn icon clicks
        """
        if event.button == 1:
            # Primary click to launch the feed list/menu
            if hasattr(self, 'menu') == False:
                self.menu = menus.RssMenu()
                self.menu.build_children(self.feeds, self)
            self.menu.popup(None, None, None, event.button, event.time)
        elif event.button == 3:
            # Right click to show option menu
            if hasattr(self, 'option_menu') == False:
                self.option_menu = menus.OptionMenu(self)
            self.option_menu.popup(None, None, None, event.button, event.time)
        else:
            pass
            #print event.button
            #for feed in self.feeds:
                #feed.update_feed()
            
    def clicks(self, widget, url, feed, index, feedindex):
        """
        Handles the feed clicks by launching the browser
        """
        widget.set_image(gtk.Image())
        os.system("xdg-open %s &" % url) # Opens the url in your browser
        self.feeds[feedindex].get_entries()[index]['read'] = True # Metadata for future support
        
if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    gtk.gdk.threads_init()
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    if 'AWNDEV' in os.environ.keys() and os.environ['AWNDEV'] == 'TRUE':
        IPythonWindow({'applet': applet})
    gtk.main                      ()