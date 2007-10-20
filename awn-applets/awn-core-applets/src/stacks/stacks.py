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

import sys
import os
import gtk
from gtk import gdk
import pango
import gconf
import awn
import gnome.ui
import gnomedesktop
import locale
import gettext
import stacksconfig
import stackslauncher
import stacksbackend
import stacksicons
import stacksvfs

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

# Visual layout parameters
ICON_VBOX_SPACE = 4
ROW_SPACING = 0
COL_SPACING = 0

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)
           
"""
Main Applet class
"""
class Stacks (awn.AppletSimple):
    # Some initialization values
    gconf_path = "/apps/avant-window-navigator/applets/"
    dnd_targets = [("text/uri-list", 0, 0), ("text/plain", 0, 1)]
    dialog_visible = False
    context_menu_visible = False
    just_dragged = False
    backend = None

    # Default configuration values, are overruled while reading config
    config_backend = "file://" +    os.path.join(
                                    os.path.expanduser("~"), 
                                    ".config", "awn", "stacks")
                                    
    config_cols = 5
    config_rows = 4
    config_fileops = gtk.gdk.ACTION_COPY
    config_fileops |= gtk.gdk.ACTION_MOVE
    config_fileops |= gtk.gdk.ACTION_LINK
    config_icon_size = 48
    config_composite_icon = True
    config_icon_empty = _to_full_path("icons/stacks-drop.svg")
    config_icon_full = _to_full_path("icons/stacks-full.svg")

    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__(self, uid, orient, height)

        # initalize variables
        self.height = height
        self.title = awn.awn_title_get_default()
        self.effects = self.get_effects()
        self.gconf_path += str(uid)
        # ensure config path (dir) exists
        try:
            os.mkdir(self.config_backend[7:])
        except OSError: # if file exists
            pass
        self.config_backend = os.path.join(self.config_backend, uid)
 
        # connect to events
        self.connect("button-press-event", self.applet_button_cb)
        self.connect("enter-notify-event", self.applet_enter_cb)
        self.connect("leave-notify-event", self.applet_leave_cb)
        self.connect("drag-data-received", self.applet_drop_cb)
        
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
        open_item.connect_object("activate", self.applet_menu_open_cb, self)
        clear_item.connect_object("activate",self.applet_menu_clear_cb,self)
        pref_item.connect_object("activate",self.applet_menu_pref_cb,self)
        about_item.connect_object("activate",self.applet_menu_about_cb,self)
        self.popup_menu.show_all()

        # get GConf client and read configuration
        self.gconf_client = gconf.client_get_default()
        self.gconf_client.notify_add(self.gconf_path, self.backend_gconf_cb)
        self.backend_get_config()

    """
    Functions concerning the Applet
    """
    def applet_menu_open_cb(self, widget):
        self.backend.open()

    def applet_menu_clear_cb(self, widget):
        self.backend.clear()
        self.applet_set_empty_icon()
 
    def applet_menu_pref_cb(self, widget):
        cfg = stacksconfig.StacksConfig(self)

    def applet_menu_about_cb(self, widget):
        cfg = stacksconfig.StacksConfig(self)
        cfg.notebook.set_current_page(-1)

    def applet_enter_cb (self, widget, event):
        self.title.show(self, self.backend.get_title())

    def applet_leave_cb (self, widget, event):
        self.title.hide(self)
 
    def applet_button_cb(self, widget, event):
        if event.button == 3:
            # right click
            self.dialog_hide()
            self.popup_menu.popup(None, None, None, event.button, event.time)
        elif event.button == 2:
            # middle click
            self.backend.open()
        else:
            # left click
            if self.dialog_visible:
               self.dialog_hide()
            else:
               if not self.backend.is_empty():
                    self.dialog_show()

    # For direct feedback "feeling"
    # add drop source to stack immediately,
    # and prevent duplicates @ monitor callback
    def applet_drop_cb(self, widget, context, x, y, 
                            selection, targetType, time):
        for uri in (selection.data).split("\r\n"):
            if uri:
                pixbuf = self.backend.add(uri, context.action)
        context.finish(True, False, time)
        if pixbuf:
            self.applet_set_full_icon(pixbuf)
        if self.dialog_visible == True:
            self.dialog_hide()
            self.dialog_show()
        return True

    def applet_set_empty_icon(self):
        height = self.height
        icon = gdk.pixbuf_new_from_file (self.config_icon_empty)
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_temp_icon(icon)

    def applet_set_full_icon(self, pixbuf):
        height = self.height
        icon = gdk.pixbuf_new_from_file(self.config_icon_full)
        if self.config_composite_icon and pixbuf:
            try:
                # scale with aspect ratio:
                pixbuf = stacksicons.IconFactory().scale_to_bounded(pixbuf, height)
                # determine center of composite
                cx = (height - pixbuf.get_width())/2
                if not cx >= 0:
                    cx = 0
                cy = (height - pixbuf.get_height())/2
                if not cy >= 0:
                    cy = 0

                # video previews (for example) have artifacts, so copy manually
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
                        try:
                            pixels[row+cy][pix+cx][0] = bufs[row][pix][0]
                            pixels[row+cy][pix+cx][1] = bufs[row][pix][1]
                            pixels[row+cy][pix+cx][2] = bufs[row][pix][2]
                            if pixbuf.get_has_alpha():
                                pixels[row+cy][pix+cx][3] = bufs[row][pix][3]
                            else:
                                pixels[row+cy][pix+cx][3] = 255
                        except:
                            pass
                
                # composite result over "full" icon
                mythumb.composite(   
                        icon, 0, 0,
                        height, height,
                        0, 0, 1, 1,
                        gtk.gdk.INTERP_BILINEAR,
                        255)
            except:
                pass
        self.set_temp_icon(icon)

    # if backend is folder: use specified file operations
    # else: only enable link action
    def applet_setup_drag_drop(self):
        if self.backend.get_type() == stacksbackend.BACKEND_TYPE_FOLDER:
            actions = self.config_fileops
        elif self.backend.get_type() == stacksbackend.BACKEND_TYPE_FILE:
            actions = gtk.gdk.ACTION_LINK
        else:
            return
        self.drag_dest_set( gtk.DEST_DEFAULT_ALL,
                            self.dnd_targets, 
                            actions)

    """
    Functions concerning items in the stack
    """
    def item_clear_cb(self, widget, user_data):
        self.backend.remove(user_data)

    def item_menu_hide_cb(self, widget):
        self.context_menu_visible = False

    # launches the command for a stack icon
    # -distinguishes desktop items
    def item_button_cb(self, widget, event, user_data):
        uri, mimetype = user_data
        if event.button == 3:
            self.item_context_menu(uri).popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            if self.just_dragged:
                self.just_dragged = False
            else:
                if uri.to_string().endswith(".desktop"):
                    item = gnomedesktop.item_new_from_uri(
                            uri.to_string(), gnomedesktop.LOAD_ONLY_IF_EXISTS)
                    if item:
                        command = item.get_string(gnomedesktop.KEY_EXEC)
                        launch_manager.launch_command(command, uri.to_string())    
                else:
                    launch_manager.launch_uri(uri.to_string(), mimetype) 

    def item_drag_data_get(
            self, widget, context, selection, info, time, user_data):
        selection.set_uris([user_data])

    def item_drag_begin(self, widget, context):
        self.just_dragged = True

    def item_context_menu(self, uri):
        self.context_menu_visible = True
        context_menu = gtk.Menu()
        del_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        context_menu.append(del_item)
        del_item.connect_object("activate", self.item_clear_cb, self, uri)     
        context_menu.connect("hide", self.item_menu_hide_cb)
        context_menu.show_all()
        return context_menu

    """
    Functions concerning the Dialog
    """
    # hide the dialog
    def dialog_hide(self):
        if self.dialog_visible is True:
            self.title.hide(self)
            self.dialog.hide()
            self.dialog_visible = False

    # show the dialog
    def dialog_show(self):
        if self.dialog_visible is False:
            self.dialog_visible = True
            self.title.hide(self)
            self.dialog_show_new()

    def dialog_focus_out(self, widget, event):
        if self.context_menu_visible is False:
            self.dialog_hide()

    def dialog_drag_data_delete(self, widget, context):
        return

    def dialog_show_new(self, page=1):
        if self.backend.is_empty():
            return
        self.dialog = awn.AppletDialog (self)
        self.dialog.set_focus_on_map(True)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)
        if self.backend.get_type() == stacksbackend.BACKEND_TYPE_FOLDER:
            self.dialog.set_title(self.backend.get_title())

        store = self.backend.get_store()
        iter = store.get_iter_first()
        new_table=True
        pages = 0
        while iter:
            if new_table:
                x=0
                y=0
                table = gtk.Table(1,1,True)
                table.set_row_spacings(ROW_SPACING)
                table.set_col_spacings(COL_SPACING)
                new_table = False
                pages += 1
                if pages == page:
                    self.dialog.add(table)
                if pages > page:
                    break

            button = gtk.Button()
            button.set_relief(gtk.RELIEF_NONE)

            button.connect( "button-release-event", 
                            self.item_button_cb,
                            store.get(iter, stacksbackend.COL_URI, stacksbackend.COL_MIMETYPE))
            # TODO: connect on enter key
            button.connect( "drag-data-get",
                            self.item_drag_data_get,
                            store.get_value(iter, stacksbackend.COL_URI).to_string())
            button.connect( "drag-begin",
                            self.item_drag_begin)
            button.drag_source_set( gtk.gdk.BUTTON1_MASK,
                                    self.dnd_targets,
                                    self.config_fileops )

            vbox = gtk.VBox(False, ICON_VBOX_SPACE)
            vbox.set_size_request(int(1.5 * self.config_icon_size), -1)
            icon = store.get_value(iter, stacksbackend.COL_ICON)

            if icon:
                button.drag_source_set_icon_pixbuf(icon)
                image = gtk.Image()
                image.set_from_pixbuf(icon)
                image.set_size_request(self.config_icon_size, 
                        self.config_icon_size)
                vbox.pack_start(image, False, False, 0)
            label = gtk.Label(store.get_value(iter, stacksbackend.COL_LABEL))
            if label:
                label.set_justify(gtk.JUSTIFY_CENTER)
                label.set_line_wrap(True)
                layout = label.get_layout()
                lw, lh = layout.get_size()
                layout.set_width(int(1.2 * self.config_icon_size) * pango.SCALE)
                layout.set_wrap(pango.WRAP_WORD_CHAR)
                _lbltext = label.get_text()
                lbltext = ""
                for i in range(layout.get_line_count()):
                    length = layout.get_line(i).length
                    lbltext += str(_lbltext[0:length]) + '\n'
                    _lbltext = _lbltext[length:]
                label.set_text(lbltext)
                label.set_size_request(-1, lh*2/pango.SCALE)
                vbox.pack_start(label, True, True, 0)
      
            button.add(vbox)
            table.attach(button, x, x+1, y, y+1)
            x += 1
            if x == self.config_cols:
                y += 1
                x=0
            if y == self.config_rows:
                new_table = True
            iter = store.iter_next(iter)

        self.dialog.show_all()

    """
    Functions concerning the Backend
    """
    def backend_gconf_cb(self, gconf_client, *args, **kwargs):
        self.dialog_hide()
        self.backend_get_config()
               
    def backend_attention_cb(self, widget, backend_type):
        awn.awn_effect_start(self.effects, "attention")
        time.sleep(1.0)
        awn.awn_effect_stop(self.effects, "attention")

    def backend_restructure_cb(self, widget, type):
        print "some item is removed from stack"

    def backend_get_config(self):
        if self.backend:
            self.backend.destroy()
        
        _config_backend = self.gconf_client.get_string(
                self.gconf_path + "/backend")
        if _config_backend:
            self.config_backend = _config_backend
           
        _config_cols = self.gconf_client.get_int(self.gconf_path + "/cols")
        if _config_cols > 0:
            self.config_cols = _config_cols

        _config_rows = self.gconf_client.get_int(self.gconf_path + "/rows")
        if _config_rows > 0:
            self.config_rows = _config_rows

        _config_icon_size = self.gconf_client.get_int(
                self.gconf_path + "/icon_size")
        if _config_icon_size > 0:
            self.config_icon_size = _config_icon_size

        _config_fileops = self.gconf_client.get_int(
                self.gconf_path + "/file_operations")
        if _config_fileops > 0:
            self.config_fileops = _config_fileops

        _config_composite_icon = self.gconf_client.get_bool(
                self.gconf_path + "/composite_icon")
        if _config_composite_icon:
            self.config_composite_icon = True
        else:
            self.config_composite_icon = False

        _config_icon_empty = self.gconf_client.get_string(
                self.gconf_path + "/applet_icon_empty")
        if _config_icon_empty:
            self.config_icon_empty = _config_icon_empty

        _config_icon_full = self.gconf_client.get_string(
                self.gconf_path + "/applet_icon_full")
        if _config_icon_full:
            self.config_icon_full = _config_icon_full      

        _config_backend_type = self.gconf_client.get_int(
                self.gconf_path + "/backend_type")
        
        if _config_backend_type == stacksbackend.BACKEND_TYPE_FOLDER:
            self.backend = stacksbackend.FolderBackend(self.config_backend, 
                    self.config_icon_size)
        elif _config_backend_type == stacksbackend.BACKEND_TYPE_FILE:
            self.backend = stacksbackend.FileBackend(self.config_backend,
                    self.config_icon_size)
        self.backend.read()
        self.backend.connect("attention", self.backend_attention_cb)
        self.backend.connect("restructure", self.backend_restructure_cb)
        self.applet_setup_drag_drop()
        
        if self.backend.is_empty():
            self.applet_set_empty_icon()
        else:
            pixbuf = self.backend.get_random_pixbuf()
            self.applet_set_full_icon(pixbuf)


launch_manager = stackslauncher.LaunchManager()
gnome.ui.authentication_manager_init()
           
if __name__ == "__main__":
    awn.init (sys.argv[1:]) 
    applet = Stacks (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
