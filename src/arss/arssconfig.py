#!/usr/bin/env python

## Complete
## The goal of this module is to be handle any and all configuartion inside of
## Arss and its associated modules inside using arss.py

import awn
import gtk, gtk.glade

try:_location = __file__[::-1][__file__[::-1].index('/'):][::-1]
except:pass


awn.CONFIG_LIST_BOOL, awn.CONFIG_LIST_FLOAT, awn.CONFIG_LIST_INT, awn.CONFIG_LIST_STRING = range(4)
awn.CONFIG_DEFAULT_GROUP = 'DEFAULT'


def get_feeds():
    """
    Gets a list of feeds
    """
    config = awn.Config('arss', None)
    return config.get_list(awn.CONFIG_DEFAULT_GROUP, "feeds", awn.CONFIG_LIST_STRING)


def save_feeds(feedlist):
    """
    saves a list of feeds
    
    Arguments: feedlist = a list of feed URIs
    """
    config = awn.Config('arss', None)
    config.set_list(awn.CONFIG_DEFAULT_GROUP, 'feeds', awn.CONFIG_LIST_STRING, feedlist)

    
def add_feed(feed):
    """
    adds a single feed to the list of feeds
    
    Arguments: feed =  a feed uri
    """
    if feed not in ['',None]:
        feeds = get_feeds()
        feeds.append(feed)
        save_feeds(feeds)
        return feeds
    else:
        print 'NO FEED ADDED'
        return None

    
def add_feed_dialog():
    """
    A simple gtk dialog to add a feed
    """
    interface = gtk.glade.XML(_location+"adddialog.glade")
    AddDialog = interface.get_widget('AddDialog')
    OkButton = interface.get_widget('Ok')
    CancelButton = interface.get_widget('Cancel')
    EntryBox = interface.get_widget('Entry')
    AddDialog.show_all()
    def clicked_add_feed(widget, *args, **kwargs):
        add_feed(EntryBox.get_text().replace(' ',''))
        widget.get_toplevel().destroy()
    OkButton.connect("clicked", clicked_add_feed)
    def clicked_close(widget, *args, **kwargs):
        widget.get_toplevel().destroy()
    CancelButton.connect("clicked", clicked_close)

def _build_tree(columns, data):
    liststore = gtk.ListStore(str, object)
    treeview = gtk.TreeView(liststore)
    i = 0
    for column in columns:
        textrenderer = gtk.CellRendererText()
        column_obj = gtk.TreeViewColumn(column, textrenderer, text=0)
        treeview.append_column(column_obj)
        i+=1
    for row in data:
        print len(row)
        liststore.append([row, None])
    treeview.set_headers_visible(False)
    return treeview, liststore

def config_window():
    feeds = get_feeds()
    tree, liststore = _build_tree(["URI"],feeds)
    interface = gtk.glade.XML(_location+"configwindow.glade")
    dialogwindow = interface.get_widget("DialogWindow")
    viewport = interface.get_widget("Port")
    viewport.add(tree)
    def _clicked_close(widget, *args, **kwargs):
        widget.get_toplevel().destroy()
    closebutton = interface.get_widget("Close-Button")
    closebutton.connect("clicked", _clicked_close)
    
    def _addfeedwrapper(*args, **kwargs):
        add_feed_dialog()
    addbutton = interface.get_widget("Add-Button")
    addbutton.connect("clicked", _addfeedwrapper)
    def _remove_feed(widget, treeview, store):
        poreference = treeview.get_selection().get_selected_rows()[-1][-1][0]
        selected = store[poreference][0]
        print selected
        feeds = get_feeds()
        feeds.remove(selected)
        save_feeds(feeds)
        treeiter = treeview.get_selection().get_selected()[-1]
        store.remove(treeiter)
        
    removebutton = interface.get_widget("Remove-Button")
    removebutton.connect("clicked", _remove_feed, tree, liststore)

    dialogwindow.show_all()
    return liststore