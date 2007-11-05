# !/usr/bin/env python
import sys, os
import os.path as check
import gobject
import pygtk
import gtk
from gtk import gdk
import string
import gmenu
class MenuDateStore:
    MENUCORE = gmenu.lookup_tree('applications.menu')
    MENUROOT = MENUCORE.get_root_directory()
    SYSTEMMENUCORE = gmenu.lookup_tree('settings.menu')
    SYSTEMMENUROOT = SYSTEMMENUCORE.get_root_directory()
    PATH = []
def get_places(theme):
    """
    this method parses the gtk bookmarks file and serves it back as a list
    """
    model = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING)
    book_loc = os.path.expanduser("~") + "/.gtk-bookmarks"
    bookmark_list = open(book_loc,"r")
    bookmarks = {}
    model_list = []
    home = [theme.load_icon('user-home',24,0),"Home"]
    bookmarks["Home"] = [0,"file://" + os.path.expanduser("~")]
    model.append(home)
    home = [theme.load_icon('drive-harddisk',24,0),"File System"]
    bookmarks["File System"] = [0,"file:///"]
    model.append(home)
    for item in bookmark_list:
        tempitem = item[::-1]
        tempitem = tempitem[:tempitem.index('/')]
        tempitem = tempitem[::-1]
        tempitem = string.rstrip(tempitem)
        ico = 'folder'
        if string.rstrip(item) == "network:///":
            tempitem = "Network"
            ico = 'network-server'
        item = string.rstrip(item)
        # Is dir check
        dirCheck = True
        item = item.replace('file://','')
        if check.isdir(item) == False:
            if ' ' in item:
                itemOLD = item
                item = string.rstrip(item[:item.index(' ')])
                if check.isdir(item) == False:
                    dirCheck = False
                else:
                    tempitem = itemOLD[itemOLD.index(' '):]
        if '%20' in tempitem:
            tempitem = tempitem.replace('%20',' ')
        item = 'file://' + item
        if dirCheck == True:
            thing = [theme.load_icon(ico,24,0),tempitem]
            model.append(thing)
            bookmarks[tempitem] = [0,item]
    return model,bookmarks
    bookmark_list.close()
def set_model(treeview,lst,theme,location_icon):
    """
    This item produces a complete model from a treeview,
    a model base, and a list
    """
    model = gtk.ListStore(gtk.gdk.Pixbuf, gobject.TYPE_STRING)
    for row in lst:
        i = None
        try:
            if '/' in row[0]:
                if check.exists(row[0]) == True:
                    row[0] = gdk.pixbuf_new_from_file (row[0])
                else:row[0] = gdk.pixbuf_new_from_file (location_icon)
            elif '.' in row[0] and '/' not in row[0]:
                location = "/usr/share/pixmaps/" + row[0]
                if check.exists(location) == True:
                    row[0] = gdk.pixbuf_new_from_file (location)
                else:row[0] = gdk.pixbuf_new_from_file (location_icon)
            elif row[0] == None:
                row[0] = gdk.pixbuf_new_from_file (location_icon)
            else:
                row[0] = theme.load_icon(row[0],22,0)
        except:
            row[0] = gdk.pixbuf_new_from_file (location_icon)
        
        try:
            if 22 != row[0].get_height():
                row[0] = row[0].scale_simple(22,22,gtk.gdk.INTERP_BILINEAR)
        except:print row[0]
        model.append(row)
    return model
def get_menus(root,root2=None):
    """
    returns a list of menus from root and root2
    """
    listall = []
    listobj = {}
    for menu in root.contents:
        if menu.get_type() == gmenu.TYPE_SEPARATOR:pass
        elif menu.get_type() == gmenu.TYPE_DIRECTORY:
            name = menu.get_name()
            if len(name) >= 21:
                name = name[:21] + '...'
            lst = []
            lst.append(menu.get_icon())
            lst.append(name)
            listall.append(lst)
            listobj[name] = [2,menu]
        elif menu.get_type() == gmenu.TYPE_ENTRY:
            if menu.get_name() == 'Add/Remove...':pass
            else:
                name = menu.get_name()
                if len(name) >= 21:
                    name = name[:21] +'..' 
                lst = []
                lst.append(menu.get_icon())
                lst.append(name)
                listall.append(lst)
                listobj[name] = [1,menu.exec_info]
    if root2 != None:
        for menu in root2.contents:
            if menu.get_type() == gmenu.TYPE_SEPARATOR:pass
            elif menu.get_type() == gmenu.TYPE_DIRECTORY:
                name = menu.get_name()
                if len(name) >= 21:
                    name = name[:21] +'...'
                lst = []
                lst.append(menu.get_icon())
                lst.append(name)
                listall.append(lst)
                listobj[name] = [2,menu]
            elif menu.get_type() == gmenu.TYPE_ENTRY:
                name = menu.get_name()
                if len(name) >= 21:
                    name = name[:21] + '...' 
                lst = []
                lst.append(menu.get_icon())
                lst.append(name)
                listall.append(lst)
                listobj[name] = [1,menu.exec_info]
        lst = []
        lst.append('folder')
        lst.append('Places')
        listall.append(lst)
        listobj['Places'] = [4,'Places']
    return listall,listobj
data = MenuDateStore()
