# !/usr/bin/python
# -*- coding: utf-8 -*-

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
import os.path
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import thread
import time
import Core.handle_rss as handle_rss
from Core.settings_rss import *
from Core.filechooser_rss import * 
from Core.opml_rss import * 
import Core.join_rss as Join
import Core.saveout as saveout
import Core.other_rss as other_rss
try:
    import Core.simplenotify as notify
except:
    print 'Notifications Disabled'

def get_icon(name, size):
    return gdk.pixbuf_new_from_file(name).scale_simple(size,
                                                       size,
                                                       gtk.gdk.INTERP_BILINEAR)

def compare_by(fieldname):
    def compare_two_dicts (a, b):
        return cmp(a[fieldname], b[fieldname])
    return compare_two_dicts

def clicked(widget, url):
    print url
    if url != None:
        url = 'xdg-open ' + repr(str(url))
        os.system(url)

class App (awn.AppletSimple):
    """
    """
    def __init__ (self, uid, orient, height):   
        """
        Creating the applets core
        """
        self.count = 0
        self.unread = 0
        self.database = []
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.theme = gtk.icon_theme_get_default()
        self.height = height
        self.size = height
        #icon = gdk.pixbuf_new_from_file()
        self.set_icon(get_icon(Settings.__feed_icon_gray__, self.size))
        self.title = awn.awn_title_get_default ()
        self.resultToolTip = "aRsS"
        self.connect("button-press-event", self.button_press)
        self.connect("enter-notify-event", self.enter_notify)
        self.connect("leave-notify-event", self.leave_notify)
        thread.start_new_thread(self.build_db_threaded_clocked,())

    def import_opml(*none):
        chosen = new_chooser()
        if chosen != False:
            if '.opml' in chosen.lower():
                newlist = feeds_from_opml(chosen)
                handle_rss.add_feed_to_file(newlist)
            print (chosen +'\n')*8

    def build_db(self,*unused):
        print 'loading...'
        # See what situation we are starting with
        if self.database != []:
            # Merge the old with the new
            self.database = Join.merge_db(self.database, handle_rss.build_db())
        elif self.database == []:
            # Get a new Database
            test = saveout.load_database()
            if test == False:
                self.database = handle_rss.build_db()
            else:
                print 'loading stored database'
                self.database = test
                #self.database = \
                #    Join.merge_db(self.database, handle_rss.build_db())
        # change icon back
        self.set_icon(get_icon(Settings.__feed_icon__, self.size))
        # cut the database size
        for feed in self.database:
            self.database[feed][0] = \
                self.database[feed][0][:Settings.__MAX_ENTRIES__]
        
        saveout.save_database(self.database) # Save the database


        self.count = other_rss.get_new_count(self.database, None)
        self.unread = other_rss.get_new_count(self.database, False)
        message = str(self.count) + " New Feeds" + '\n' +\
            str(self.unread) + ' Unread'
        try: # A test to attempt to send a message to the notification daemon
            notify.send(body = message,
                        app_name = "AWN _rss",
                        title = 'aRSS has been updated')
                        #icon = Settings.__feed_icon__)
        except:
            print message

    def build_db_threaded(self,*unused):
        """
        A non looping threaded handler for the update button
        """
        self.set_icon(get_icon(Settings.__feed_icon_gray__, self.size))
        thread.start_new_thread(self.build_db,())

    def build_db_threaded_clocked(self):          
        """
        A looping handler for the update_db system, Non threaded
        """
        self.set_icon(get_icon(Settings.__feed_icon_gray__, self.size))
        self.build_db()
        time.sleep(Settings.__reload_time__)
        self.build_db_threaded_clocked()

    def clicked_handler(self,widget, url, feed, index):
        """
        Changes the widgets metadata based on its state, while adjusting the
        global meta data
        """
        if self.database[feed][0][index]['meta_read'] == None:
            self.count -= 1
        if self.database[feed][0][index]['meta_read'] == False:
            self.unread -= 1
        self.database[feed][0][index]['meta_read'] = True
        clicked(widget, url)

    def mark_feed_as_read(self, widget, feed):
        for story in self.database[feed][0]:
            story['meta_read'] = True

    def get_menu(self, widget, event):
        # Updating info entries
        self.unread = other_rss.get_new_count(self.database, False)
        self.count = other_rss.get_new_count(self.database, None)
        # Building the info entries
        menu_root = gtk.Menu()
        menu_unread = gtk.ImageMenuItem(('New: ' + str(self.count)))
        unread_image = gtk.Image()
        unread_image.set_from_file(Settings.__feed_icon_new__)
        menu_unread.set_image(unread_image)
        menu_root.append(menu_unread)
        menu_unread = gtk.ImageMenuItem(('Unread: ' + str(self.unread)))
        unread_image = gtk.Image()
        unread_image.set_from_file(Settings.__feed_icon_unread__)
        menu_unread.set_image(unread_image)
        menu_root.append(menu_unread)
        # Menu seperator
        menu_sep = gtk.SeparatorMenuItem()
        menu_root.append(menu_sep)
        # Iterating over the database of feeds
        for feed in self.database:
            # icons for menu
            subunread = other_rss.get_new_count({'fakedict':
                                                    [self.database[feed][0],
                                                     None]}, False)
            subcount = other_rss.get_new_count({'fakedict':
                                                   [self.database[feed][0],
                                                    None]}, None)
            feed_title_image = gtk.Image()
            if subunread > 0 and subcount < 1:
                feed_title_image.set_from_file(Settings.__feed_icon_unread__)
            if subcount > 0:
                feed_title_image.set_from_file(Settings.__feed_icon_new__)
            menu_root_item = gtk.ImageMenuItem(self.database[feed][1])
            menu_root_item.set_image(feed_title_image)
            menu_root.append(menu_root_item)
            menu_sub = gtk.Menu()
            menu_root_item.set_submenu(menu_sub)
            # Iterating over the stories
            for story in self.database[feed][0]:
                if 'meta_read' in story.keys():
                    if story['meta_read'] == True:
                        menu_sub_item = gtk.MenuItem(story.title)
                    elif story['meta_read'] == None:
                        menu_sub_item = gtk.ImageMenuItem(story.title[:50])
                        sub_image = gtk.Image()
                        sub_image.set_from_file(Settings.__feed_icon_new__)
                        menu_sub_item.set_image(sub_image)
                    elif story['meta_read'] == False:
                        menu_sub_item = gtk.ImageMenuItem(story.title[:50])
                        sub_image = gtk.Image()
                        sub_image.set_from_file(Settings.__feed_icon_unread__)
                        menu_sub_item.set_image(sub_image)
                try:menu_sub_item.connect("activate", self.clicked_handler,
                                      story.link, feed,
                                      self.database[feed][0].index(story))
                except:
                    pass
                menu_sub.append(menu_sub_item)
            # Mark as read button
            # Menu seperator
            menu_sep = gtk.SeparatorMenuItem()
            menu_sub.append(menu_sep)
            menu_sub_item = gtk.ImageMenuItem("Mark All As Read")
            sub_image = gtk.Image()
            sub_image.set_from_file(Settings.__feed_icon_unread__)
            menu_sub_item.set_image(sub_image)
            menu_sub.append(menu_sub_item)
            menu_sub_item.connect("activate", self.mark_feed_as_read, feed)
        menu_root.show_all()
        menu_root.popup(None, None, None, event.button, event.get_time())
        return True

    def get_option_menu(self, widget, event):
        menu_root = gtk.Menu()
        # Import opml
        menu_root_item = gtk.MenuItem("Import OPML")
        menu_root.append(menu_root_item)
        menu_root_item.connect("activate", self.import_opml)
        menu_sep = gtk.SeparatorMenuItem()
        menu_root.append(menu_sep)
        # Update
        menu_root_item = gtk.MenuItem("Update")
        menu_root.append(menu_root_item)
        menu_root_item.connect("activate", self.build_db_threaded)
        menu_root.show_all()
        menu_root.popup(None, None, None, event.button, event.get_time())
        return True

    def button_press(self, widget, event):
        if event.button == 1:
            self.get_menu(widget, event)
        if event.button == 3:
            self.get_option_menu(widget, event)

    def enter_notify(self, widget, event):
        self.title.show(self, ("New: " + str(self.count) + "  Unread: " +
                               str(self.unread)))

    def leave_notify(self, widget, event):
        self.title.hide(self)

if __name__ == "__main__":
    if os.path.exists('/usr/bin/xdg-open') == False:
        print 'Please install xdg-utils'
    awn.init                      (sys.argv[1:])
    gtk.gdk.threads_init()
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
