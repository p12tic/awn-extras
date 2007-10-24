#!/usr/bin/python
import sys
import gobject
import gtk
from gtk.glade import *
from gtk import gdk
import os
import locale
import gettext
import stacksglade
APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

BACKEND_TYPE_FOLDER = 1

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)

class StacksConfig(stacksglade.GladeWindow):
    glade_file = _to_full_path('stacks_preferences.glade')
   
    def __init__(self, applet):
        stacksglade.GladeWindow.__init__(self)

        self.applet = applet
        self.backend = None
        self.applet_icon_empty = None
        self.applet_icon_full = None
        # get empty icon
        self.applet_icon_empty = self.applet.gconf_client.get_string(
                self.applet.gconf_path + "/applet_icon_empty")
        if self.applet_icon_empty is None:
            self.applet_icon_empty = _to_full_path("icons/stacks-drop.svg")
        try:
            empty_icon = gdk.pixbuf_new_from_file(self.applet_icon_empty)
        except:
            pass
        if empty_icon:
            empty_image = gtk.Image()
            empty_image.set_from_pixbuf(empty_icon)
            self.widgets['empty_button'].set_image(empty_image)
        # get full icon
        self.applet_icon_full = self.applet.gconf_client.get_string(
            self.applet.gconf_path + "/applet_icon_full")
        if self.applet_icon_full is None:
            self.applet_icon_full = _to_full_path("icons/stacks-full.svg")      
        try:
            full_icon = gdk.pixbuf_new_from_file(self.applet_icon_full)
        except:
            pass
        if full_icon:
            full_image = gtk.Image()
            full_image.set_from_pixbuf(full_icon)
            self.widgets['full_button'].set_image(full_image)
        # get dimension
        gconf_cols = self.applet.gconf_client.get_int(
                self.applet.gconf_path + "/cols")
        if gconf_cols > 0:
            self.widgets['cols_entry'].set_text(str(gconf_cols))       
        gconf_rows = self.applet.gconf_client.get_int(
                self.applet.gconf_path + "/rows")
        if gconf_rows > 0:
            self.widgets['rows_entry'].set_text(str(gconf_rows))
        # get icon size
        gconf_icon_size = self.applet.gconf_client.get_int(
                self.applet.gconf_path + "/icon_size")
        if gconf_icon_size > 0:
            self.widgets['iconsize_spin'].set_value(gconf_icon_size)
        # get composite
        composite = self.applet.gconf_client.get_bool(
                self.applet.gconf_path + "/composite_icon")
        if composite is False:
            self.widgets['nocomposite_radio'].set_active(True)
        # get file oprations
        actions = self.applet.gconf_client.get_int(
                self.applet.gconf_path + "/file_operations")
        if actions > 0:
            if (actions & gtk.gdk.ACTION_COPY) == 0:
                self.widgets['copy_check'].set_active(False)
            if (actions & gtk.gdk.ACTION_MOVE) == 0:
                self.widgets['move_check'].set_active(False)
            if (actions & gtk.gdk.ACTION_LINK) == 0:
                self.widgets['link_check'].set_active(False)
        # get browsing  
        browsing = self.applet.gconf_client.get_bool(
                self.applet.gconf_path + "/browsing")
        if browsing is False:
            self.widgets['nobrowse_radio'].set_active(True)
           
    def on_backendselect_button_clicked(self, *args):
        filesel = gtk.FileChooserDialog(
                _("Select backend destination:"), 
                None, 
                gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER |
                gtk.FILE_CHOOSER_ACTION_SAVE, 
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_APPLY, gtk.RESPONSE_OK), 
                None)
        filesel.set_default_response(gtk.RESPONSE_OK)
        gconf_backend = self.applet.gconf_client.get_string(
            self.applet.gconf_path + "/backend")
        if gconf_backend is None:
            filesel.set_current_folder(os.path.expanduser("~"))
        else:
            filesel.set_current_folder(gconf_backend)
        if filesel.run() == gtk.RESPONSE_OK:
            self.backend = filesel.get_filename()
        filesel.destroy()

    def _select_icon(self, type):
        filesel = gtk.FileChooserDialog(
                "Select applet icon:", 
                None, 
                gtk.FILE_CHOOSER_ACTION_OPEN, 
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_APPLY, gtk.RESPONSE_OK), 
                None)
        filesel.set_default_response(gtk.RESPONSE_OK)
        img_filter = gtk.FileFilter()
        img_filter.set_name(_("Supported image types"))
        img_filter.add_pixbuf_formats()
        filesel.add_filter(img_filter)
        if type == "empty":
            filesel.set_filename(self.applet_icon_empty)
        else:
            filesel.set_filename(self.applet_icon_full)
        if filesel.run() == gtk.RESPONSE_OK:
            icon = gdk.pixbuf_new_from_file(filesel.get_filename())
            if icon != None:
                image = gtk.Image()
                image.set_from_pixbuf(icon)
                if type == "empty":
                    self.applet_icon_empty = filesel.get_filename()
                    self.widgets['empty_button'].set_image(image)
                else:
                    self.applet_icon_full = filesel.get_filename()
                    self.widgets['full_button'].set_image(image)
        filesel.destroy()

    def on_empty_button_clicked(self, *args):
        self._select_icon("empty")

    def on_full_button_clicked(self, *args):
        self._select_icon("full")

    def on_cancel_button_clicked(self, *args):
        self.destroy()

    def on_ok_button_clicked(self, *args):
        # set backend (and type)
        if self.backend is not None:
            self.applet.gconf_client.set_int(self.applet.gconf_path + "/backend_type",
                                                BACKEND_TYPE_FOLDER)
            self.applet.gconf_client.set_string(self.applet.gconf_path + "/backend", 
                                                self.backend )
        # set dimension
        cols = self.widgets['cols_entry'].get_text()
        if int(cols) > 0:
            self.applet.gconf_client.set_int(
                    self.applet.gconf_path + "/cols", int(cols) )
        rows = self.widgets['rows_entry'].get_text()
        if int(rows) > 0:
            self.applet.gconf_client.set_int(
                    self.applet.gconf_path + "/rows", int(rows) )
        # set icon size
        iconsize = self.widgets['iconsize_spin'].get_value()
        if int(iconsize) > 0:
            self.applet.gconf_client.set_int(
                    self.applet.gconf_path + "/icon_size", int(iconsize) )
        # set composite
        self.applet.gconf_client.set_bool(
                self.applet.gconf_path + "/composite_icon", 
                self.widgets['composite_radio'].get_active())
        # set browsing
        self.applet.gconf_client.set_bool(
                self.applet.gconf_path + "/browsing",
                self.widgets['browse_radio'].get_active())
        # set icons
        self.applet.gconf_client.set_string(
                self.applet.gconf_path + "/applet_icon_empty",
                self.applet_icon_empty)
        self.applet.gconf_client.set_string(
                self.applet.gconf_path + "/applet_icon_full",
                self.applet_icon_full)
        # set file operations
        actions = 0
        if self.widgets['copy_check'].get_active():
            actions |= gtk.gdk.ACTION_COPY
        if self.widgets['move_check'].get_active():
            actions |= gtk.gdk.ACTION_MOVE
        if self.widgets['link_check'].get_active():
            actions |= gtk.gdk.ACTION_LINK
        self.applet.gconf_client.set_int(
                self.applet.gconf_path + "/file_operations", actions)
        # destroy window
        self.window.destroy()
