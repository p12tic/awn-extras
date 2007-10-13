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
import gobject
import gtk
from gtk import gdk
import pango
import gconf
import awn
import time
import random
import gnome.ui
import gnomevfs
import shutil
APP="Stacks"
DIR="locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

# Import our own stuff
import stacksconfig
import stackslauncher
import stacksmonitor
import stacksicons

# Columns in the ListStore
COL_URI = 0
COL_LABEL = 1
COL_MIMETYPE = 2
COL_ICON = 3
COL_FILEMON = 4

# Visual layout parameters
ICON_VBOX_SPACE = 4
ICON_TEXT_HEIGHT = 28
ICON_ICON_SIZE = 48
ICON_TEXT_WIDTH = 60
ROW_SPACING = 8
COL_SPACING = 8

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)

class App (awn.AppletSimple):
    """
    Main Applet class
    """
    gconf_path = "/apps/avant-window-navigator/applets/"
    dnd_targets = [("text/uri-list", 0, 0)]
    launch_manager = stackslauncher.LaunchManager()
    dialog_visible = False
    just_dragged = False
    backend_type = None
    config_cols = 5
    config_rows = 4
    config_fileops = gtk.gdk.ACTION_COPY | gtk.gdk.ACTION_MOVE | gtk.gdk.ACTION_LINK

    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__(self, uid, orient, height)
        
        self.height = height
        self.title = awn.awn_title_get_default()
        self.effects = self.get_effects()
        self.gconf_path += str(uid)
 
        self.connect("button-press-event", self.button_press)
        self.connect("enter-notify-event", self.enter_notify)
        self.connect("leave-notify-event", self.leave_notify)
        self.connect("drag-data-received", self.received_callback)
        
        # Setup popup menu
        self.popup_menu = gtk.Menu()
        open_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_OPEN)
        clear_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
        self.popup_menu.append(open_item)
        self.popup_menu.append(clear_item)
        self.popup_menu.append(pref_item)
        self.popup_menu.append(about_item)
        open_item.connect_object("activate", self.open_callback, self)
        clear_item.connect_object("activate",self.clear_callback,self)
        pref_item.connect_object("activate",self.pref_callback,self)
        about_item.connect_object("activate",self.about_callback,self)
        self.popup_menu.show_all()

        # Setup file tracker
        self.store = gtk.ListStore( gobject.TYPE_STRING, 
                                    gobject.TYPE_STRING, 
                                    gobject.TYPE_STRING,
                                    gtk.gdk.Pixbuf,
                                    gobject.TYPE_OBJECT )
        self.store.set_sort_column_id(COL_URI, gtk.SORT_ASCENDING)
        self.store.set_sort_func(COL_URI, self.file_sort)

        self.gconf_client = gconf.client_get_default()
        self.gconf_client.notify_add(self.gconf_path, self.config_event)
        self.get_config()

    # if backend is folder: use specified file operations
    # else: only enable link action
    def setup_drag_drop(self):
        # Setup drag area
        if self.backend_type != None and self.backend_type == gnomevfs.FILE_TYPE_DIRECTORY:
            actions = self.config_fileops
        else:
            actions = gtk.gdk.ACTION_LINK

        self.drag_dest_set( gtk.DEST_DEFAULT_MOTION |
                            gtk.DEST_DEFAULT_HIGHLIGHT | 
                            gtk.DEST_DEFAULT_DROP,
                            self.dnd_targets, 
                            actions)

    def file_sort(self, model, iter1, iter2):
        f1 = model.get_value(iter1, 0)
        f2 = model.get_value(iter2, 0)
        t1 = gnomevfs.get_file_info(f1).type
        t2 = gnomevfs.get_file_info(f2).type

        if t1 == gnomevfs.FILE_TYPE_DIRECTORY and not t2 == gnomevfs.FILE_TYPE_DIRECTORY:
            return -1
        elif t2 == gnomevfs.FILE_TYPE_DIRECTORY and not t1 == gnomevfs.FILE_TYPE_DIRECTORY:
            return 1
        
        r1,e1 = os.path.splitext(os.path.basename(f1).lower())
        r2,e2 = os.path.splitext(os.path.basename(f2).lower())
        
        if cmp(r1, r2) == 0:
            return cmp (e1, e2)
        else:
            return cmp(r1, r2)

    def dialog_hide(self):
        if self.dialog_visible != False:
            self.title.hide(self)
            self.dialog.hide()
            self.dialog_visible = False

    def dialog_show(self):
        if self.dialog_visible != True:
            self.dialog_visible = True
            self.title.hide(self)
            self.build_stack_dialog()
            self.dialog.show_all()

    def stack_add(self, uri):
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            # check for duplicates
            if(store_uri == uri):
                return None
            iter = self.store.iter_next(iter)     
        mime_type = gnomevfs.get_mime_type(uri)
        thumbnailer = stacksicons.Thumbnailer(uri, mime_type)
        pixbuf = thumbnailer.get_icon(ICON_ICON_SIZE)
        filemon = stacksmonitor.FileMonitor(uri)
        filemon.connect("deleted", self.dialog_monitor_deleted)
        self.store.append([ uri, 
                            os.path.basename(uri), 
                            mime_type,
                            pixbuf,
                            filemon ])       
        filemon.open()
        return pixbuf

    # TODO: remove does not work correctly yet
    def stack_remove(self, uri):
        iter = self.store.get_iter_first()
        while iter:
            store_uri = self.store.get_value(iter, COL_URI)
            if(store_uri == uri):
                self.store.remove(iter)
                return True
            iter = self.store.iter_next(iter)     
        return False

    # For direct feedback "feeling"
    # add drop source to stack immediately,
    # and prevent duplicates @ monitor callback
    def received_callback(self, widget, context, x, y, selection, targetType, time):
        pixbuf = None
        for uri in (selection.data).split("\r\n"):
            if uri:
                uri = uri.replace("file://", "")
                if self.backend_type == gnomevfs.FILE_TYPE_DIRECTORY:
                    dest = os.path.join(self.config_backend, os.path.basename(uri))
                    if context.suggested_action == gtk.gdk.ACTION_LINK:
                        os.symlink(uri, dest)
                    elif context.suggested_action == gtk.gdk.ACTION_COPY:
                        shutil.copy(uri, dest)
                    elif context.suggested_action == gtk.gdk.ACTION_MOVE:
                        shutil.move(uri, dest)
                    else:
                        print "Suggested drop action not specified for: ", uri
                    
                    pixbuf = self.stack_add("file://" + dest)
        context.finish(True, False, time)
        if pixbuf != None:
            self.set_full_icon(pixbuf)
        if self.dialog_visible == True:
            self.dialog_hide()
            self.dialog_show()

        return True

    def open_callback(self, widget):
        if self.config_backend:
            self.launch_manager.launch_uri(self.config_backend, None)

    def clear_callback(self, widget):
        if self.store:
            self.store.clear()
        self.set_empty_icon()
 
    def pref_callback(self, widget):
        cfg = stacksconfig.StacksConfig(self)

    def about_callback(self, widget):
        cfg = stacksconfig.StacksConfig(self)
        cfg.notebook.set_current_page(-1)

    def button_press(self, widget, event):
        if event.button == 3:
            # right click
            self.dialog_hide()
            self.popup_menu.popup(None, None, None, event.button, event.time)
        else:
            if self.dialog_visible != True and self.store.get_iter_first() != None:
                self.dialog_show()
            else:
                self.dialog_hide()

    def dialog_monitor_created(self, something, uri):
        print "created: ", uri
        pixbuf = self.stack_add(uri)
        # if we do not have that file already:
        if pixbuf != None:
            self.get_attention_effect()

    def dialog_monitor_deleted(self, something, uri):
        print "deleted: ", uri
        if self.stack_remove(uri):
            self.get_attention_effect()
       
    def get_attention_effect(self):
        awn.awn_effect_start(self.effects, "attention")
        time.sleep(1.0)
        awn.awn_effect_stop(self.effects, "attention")

    def dialog_button_released(self, widget, event, user_data):
        if self.just_dragged == True:
            self.just_dragged = False
        else:
            uri, mimetype = user_data
            self.launch_manager.launch_uri(uri, mimetype) 

    def dialog_focus_out(self, widget, event):
        self.dialog_hide()

    def dialog_drag_data_delete(self, widget, context):
        return

    def dialog_drag_data_get(self, widget, context, selection, info, time, user_data):
        selection.set_uris([user_data])

    def dialog_drag_begin(self, widget, context):
        self.just_dragged = True

    def enter_notify (self, widget, event):
        if self.config_backend != None:
            self.title.show(self, os.path.basename(self.config_backend))
        else:
            self.title.show(self, _("Stacks"))

    def leave_notify (self, widget, event):
        self.title.hide(self)

    def set_empty_icon(self):
        height = self.height
        drop_icon = _to_full_path("icons/stacks-drop.svg")
        icon = gdk.pixbuf_new_from_file (drop_icon)
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_temp_icon(icon)

    def set_full_icon(self, pixbuf):
        height = self.height
        full_icon = _to_full_path("icons/stacks-full.svg") 
        icon = gdk.pixbuf_new_from_file(full_icon)
        if pixbuf:
            # scale with aspect ratio:
            if pixbuf.get_width() > height:
                new_w = height
                new_h = int(height * pixbuf.get_height() / pixbuf.get_width())
            else:
                new_w = int(height * pixbuf.get_width() / pixbuf.get_height())
                new_h = height

            pixbuf = pixbuf.scale_simple(new_w, new_h, gtk.gdk.INTERP_BILINEAR)

            # determine center of composite
            cx = (height - pixbuf.get_width())/2
            if not cx >= 0:
                cx = 0
            cy = (height - pixbuf.get_height())/2
            if not cy >= 0:
                cy = 0

            # video previews (for example) have artifacts (therefor this solution)
            # create transparent pixbuf of correct size
            mythumb = gtk.gdk.Pixbuf(pixbuf.get_colorspace(),
                                     True,
                                     pixbuf.get_bits_per_sample(),
                                     height,
                                     height)
            mythumb.fill(0x00000000)

            # copy pixbuf into transparent to center
            pixels = mythumb.get_pixels_array()
            bufs = pixbuf.get_pixels_array()
            for row in range(pixbuf.get_height()):
                for pix in range(pixbuf.get_width()):
                    pixels[row+cy][pix+cx][0] = bufs[row][pix][0]
                    pixels[row+cy][pix+cx][1] = bufs[row][pix][1]
                    pixels[row+cy][pix+cx][2] = bufs[row][pix][2]
                    pixels[row+cy][pix+cx][3] = bufs[row][pix][3]

            # composite result over "full" icon
            mythumb.composite(   
                    icon, 0, 0,
                    height, height,
                    0, 0, 1, 1,
                    gtk.gdk.INTERP_BILINEAR,
                    255)
        self.set_temp_icon(icon)

    def config_event(self, gconf_client, *args, **kwargs):
        self.dialog_hide()
        self.get_config()
     
    def get_config(self):
        # TODO: clear existing file monitors?
        self.store.clear()
        self.config_backend = self.gconf_client.get_string(self.gconf_path + "/backend")
        if self.config_backend == None or len(self.config_backend) == 0:
            self.config_backend = "/tmp"

        _config_cols = self.gconf_client.get_int(self.gconf_path + "/cols")
        _config_rows = self.gconf_client.get_int(self.gconf_path + "/rows")
        if _config_cols > 0:
            self.config_cols = _config_cols
        if _config_rows > 0:
            self.config_rows = _config_rows

        _config_fileops = self.gconf_client.get_int(self.gconf_path + "/file_operations")
        if _config_fileops > 0:
            self.config_fileops = _config_fileops

        self.backend_type = gnomevfs.get_file_info(self.config_backend).type
        # read items from backend
        if self.backend_type == gnomevfs.FILE_TYPE_DIRECTORY:
            self._read_folder_backend(self.config_backend)
        else:
            self._read_file_backend(self.config_backend)   

        self.setup_drag_drop()

        # get random pixbuf
        iter = self.store.get_iter_first()
        if iter:
            rand = random.Random()
            pick = rand.randint(0, 10)
            start = 0
            pixbuf = None
            while iter:
                pixbuf = self.store.get_value(iter, COL_ICON)
                if pick == start:
                    break
                iter = self.store.iter_next(iter)
                start += 1

            self.set_full_icon(pixbuf)
        else:
            self.set_empty_icon()

    def _read_file_backend(self, uri):
        # TODO: parse file
        return

    def _read_folder_backend(self, uri):
        for name in os.listdir(uri):
            self.stack_add("file://" + os.path.join(uri, name))
        # add monitor for folder
        print "add monitor for folder: ", uri
        filemon = stacksmonitor.FileMonitor(uri)
        filemon.open()
        filemon.connect("created", self.dialog_monitor_created)
        filemon.connect("deleted", self.dialog_monitor_deleted)

    def build_stack_dialog(self):
        if not self.store:
            return

        self.dialog = awn.AppletDialog (self)
        self.dialog.set_focus_on_map(True)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)

        if self.config_backend != None:
            self.dialog.set_title(os.path.basename(self.config_backend))
        else:
            self.dialog.set_title(_("Stacks"))

        table = gtk.Table(1,1,True)
        table.set_row_spacings(ROW_SPACING)
        table.set_col_spacings(COL_SPACING)

        iter = self.store.get_iter_first()
        x=0
        y=0
        while iter:
            button = gtk.Button()
            button.set_relief(gtk.RELIEF_NONE)
            button.connect( "button-release-event", 
                            self.dialog_button_released, 
                            self.store.get(iter, COL_URI, COL_MIMETYPE))
            button.connect( "drag-data-get",
                            self.dialog_drag_data_get,
                            self.store.get_value(iter, COL_URI))
            button.connect( "drag-begin",
                            self.dialog_drag_begin)
            button.drag_source_set( gtk.gdk.BUTTON1_MASK,
                                    self.dnd_targets,
                                    self.config_fileops )

            vbox = gtk.VBox(False, ICON_VBOX_SPACE)
            icon = self.store.get_value(iter, COL_ICON)

            if icon:
                button.drag_source_set_icon_pixbuf(icon)
                image = gtk.Image()
                image.set_from_pixbuf(icon)
                image.set_size_request(ICON_ICON_SIZE, ICON_ICON_SIZE)
                vbox.pack_start(image, False, False, 0)
            label = gtk.Label(self.store.get_value(iter, COL_LABEL))
            if label:
                label.set_justify(gtk.JUSTIFY_CENTER)
                label.set_line_wrap(True)
                label.set_size_request(ICON_TEXT_WIDTH, ICON_TEXT_HEIGHT)
                label.set_ellipsize(pango.ELLIPSIZE_END)
                vbox.pack_start(label, True, False, 0)
      
            vbox.set_size_request(ICON_TEXT_WIDTH, ICON_ICON_SIZE + ICON_VBOX_SPACE + ICON_TEXT_HEIGHT)
            button.add(vbox)
            table.attach(button, x, x+1, y, y+1)
            x += 1
            if x == self.config_cols:
                y += 1
                x=0
            if y == self.config_rows:
                break
            iter = self.store.iter_next(iter)

        table.show_all()
        self.dialog.add(table)


if __name__ == "__main__":
    awn.init (sys.argv[1:])
    
    applet = App (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
