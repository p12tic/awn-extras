#!/usr/bin/env python

import os
import gtk
import feedparserdb
import arssconfig

_location = __file__[::-1][__file__[::-1].index('/'):][::-1]

def _unread(feed, Value=True):
    """
    !!!Future use!!! Number of unread stories in a feed
    """
    unread = 0
    for entry in feed.get_entries():
        if 'read' in entry.keys() and entry['read'] == Value:
            if Value == False:unread+=1
            pass
        else:
            if Value != False:unread+=1
    return unread
def _unread_list(feeds, Value=True):
    """
    !!!Future use!!! Number of unread stories in a list of feeds
    """
    unread = 0
    for feed in feeds:
        unread += _unread(feed, Value)
    return unread

class MenuItem(gtk.ImageMenuItem):
    """
    A simple subclass of ImageMenuItem
    
    title = The label of the item
    image = the items images(optional)
    """
    def __init__(self, title, image=None):
        super(MenuItem, self).__init__(title)
        if image != None:
            unread_image = gtk.Image()
            unread_image.set_from_file(image)
            self.set_image(unread_image)
        
class RssMenu(gtk.Menu):
    """
    Parses thru a list of Feed objects and displays them
    """
    def __init__(self, *args):
        super(RssMenu, self).__init__()
    def build_children(self, feeds, obj):
        def _clear_feed(widget, feed):
            feed.clear_feed()
        def _mark_feed_as_read(widget, feed):
            for entry in feed.Entries:
                entry['read'] = True
        feedindex = 0
        unread = MenuItem('Unread: %d' % _unread_list(feeds), _location + 'Icons/feed-icon-unread.png')
        self.append(unread)
        seperator = gtk.SeparatorMenuItem()
        self.append(seperator)
        for feed in feeds:
            feedmenu = MenuItem(feed.Title)
            self.append(feedmenu)
            submenu = gtk.Menu()
            feedmenu.set_submenu(submenu)
            asread = MenuItem('Mark Feed As Read')
            submenu.append(asread)
            asread.connect("activate", _mark_feed_as_read, feed)
            clearfeed = MenuItem('Clear/Empty Feed')
            submenu.append(clearfeed)
            clearfeed.connect("activate", _clear_feed, feed)
            unread = MenuItem('Unread: %d' % _unread(feed),  _location + 'Icons/feed-icon-unread.png')
            submenu.append(unread)
            seperator = gtk.SeparatorMenuItem()
            submenu.append(seperator)
            for entry in feed.get_entries():
                #image= _location + 'Icons/feed-icon-unread.png'
                if 'read' in entry.keys() and entry['read'] == True:
                    entrymenu = MenuItem(entry.title[:60])
                else:
                    entrymenu = MenuItem(entry.title[:60], _location + 'Icons/feed-icon-unread.png')
                submenu.append(entrymenu)
                try:entrymenu.connect("activate",obj.clicks, entry.link, feed, feed.get_entries().index(entry),feedindex)
                except AttributeError:
                    print entry.title + " is malformed and all objects do not have links"
            feedindex+=1
        self.show_all()

class OptionMenu(gtk.Menu):
    """
    Draws the option window normally shown when you right click
    """
    def __init__(self, applet, *args):
        super(OptionMenu, self).__init__()
        self.applet = applet
        AddFeedItem = MenuItem('Add Feed')
        self.append(AddFeedItem)
        ConfigWindowItem = MenuItem('Config Window')
        self.append(ConfigWindowItem)
        ConfigWindowItem.connect("activate", self._config_window)
        UpdateItem = MenuItem('Update')
        self.append(UpdateItem)
        AddFeedItem.connect("activate", self._launch_add_feed)
        UpdateItem.connect("activate", self._update_feed)
        self.show_all()
        self.args = args
        print self.args
    def _config_window(self, *args):
        arssconfig.config_window()
    def _launch_add_feed(self, *args):
        arssconfig.add_feed_dialog()
    def _update_feed(self, *args):
        """
        Updates the feeds by replacing them  with a new set
        """
        self.applet.Database.update_feeds(arssconfig.get_feeds())
        self.applet.feeds = self.applet.Database.get_feed_objects()
        self.applet.updated = True