#!/usr/bin/python
import sys
import gobject
import gtk
from gtk.glade import *
from gtk import gdk
import os
import locale
import gettext
        
#from stacks_applet import StacksApplet
from stacks_backend import *
from stacks_glade import GladeWindow
from stacks_icons import IconFactory

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

PREF_BACKEND_FOLDER = 1
PREF_APPLET_ICON = 2
PREF_COMPOSITE_ICON = 4
PREF_ICON_SIZE = 8
PREF_DIMENSION = 16
PREF_FILE_OPERATIONS = 32
PREF_BROWSING = 64
PREF_TITLE = 128
PREF_ITEM_COUNT = 256


STACKS_GUI_DIALOG=1
STACKS_GUI_CURVED=2
STACKS_GUI_TRASHER=3

LAYOUT_PREFS =  PREF_APPLET_ICON + \
                PREF_COMPOSITE_ICON + \
                PREF_ICON_SIZE + \
                PREF_DIMENSION + \
                PREF_TITLE + \
                PREF_ITEM_COUNT
BEHAVE_PREFS =  PREF_FILE_OPERATIONS + \
                PREF_BROWSING
ALL_PREFS = PREF_BACKEND_FOLDER + LAYOUT_PREFS + BEHAVE_PREFS


def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)

class StacksConfig(GladeWindow):
    glade_file = _to_full_path('stacks_preferences.glade')
    backend_type = BACKEND_TYPE_INVALID
    applet = None

    backend = None
    config = None

    def __init__(self, applet):
        GladeWindow.__init__(self)
        self.applet = applet
        self.backend_type = applet.backend.get_type()

        config = get_config_from_gconf(
                self.applet.gconf_client,
                self.applet.gconf_path,
                self.applet.uid)
        self.config = config

        preferences = ALL_PREFS
        if self.backend_type == BACKEND_TYPE_FILE:
            pass
        elif self.backend_type == BACKEND_TYPE_FOLDER:
            pass
        elif self.backend_type == BACKEND_TYPE_PLUGGER:
            preferences -= PREF_BACKEND_FOLDER
        elif self.backend_type == BACKEND_TYPE_TRASHER:
            preferences -= PREF_BACKEND_FOLDER
            preferences -= PREF_FILE_OPERATIONS
        else:
            print "Stacks Config: Backend type unkown\nCannot continue."
            return None

        # PAGE 1

        if (preferences & PREF_BACKEND_FOLDER) == 0:
            page = self.widgets['main_notebook'].page_num(self.widgets['page1'])
            self.widgets['main_notebook'].remove_page(page)

        # PAGE 2

        if (preferences | LAYOUT_PREFS) == 0:
            page = self.widgets['main_notebook'].page_num(self.widgets['page2'])
            self.widgets['main_notebook'].remove_page(page)

        if (preferences & PREF_APPLET_ICON) == 0:
            self.widgets['icons_label'].set_sensitive(False)
            self.widgets['icons_hbbox'].set_sensitive(False)
        else:
            # get empty icon
            try:
                empty_image = IconFactory().load_image(config['icon_empty'], 24)
                self.widgets['empty_button'].set_image(empty_image)
            except:
                pass
            # get full icon
            try:
                full_image = IconFactory().load_image(config['icon_full'], 24)
                self.widgets['full_button'].set_image(full_image)
            except:
                pass

        if (preferences & PREF_COMPOSITE_ICON) == 0:
            self.widgets['composite_label'].set_sensitive(False)
            self.widgets['composite_hbox'].set_sensitive(False)
        else:
            # get composite
            self.widgets['composite_checkb'].set_active(config['composite_icon'])

        if (preferences & PREF_ICON_SIZE) == 0:
            self.widgets['iconsize_label'].set_sensitive(False)
            self.widgets['iconsize_spin'].set_sensitive(False)
        else:
            # get icon size
            self.widgets['iconsize_spin'].set_value(config['icon_size'])

        if (preferences) == 0:
            self.widgets['layout_combobox'].set_sensitive(False)
        else:
            self.widgets['layout_combobox'].set_active(config['gui_type']-1)
            
        if config['gui_type'] == 2:
        	self.widgets['layout_settings_button'].set_sensitive(True)
        	self.widgets['dimension_label'].hide_all()
        	self.widgets['dimension_hbox'].hide_all()
        else:
        	self.widgets['layout_settings_button'].set_sensitive(False)                        
        	self.widgets['dimension_label'].show_all()
        	self.widgets['dimension_hbox'].show_all()
            

        if (preferences & PREF_DIMENSION) == 0:
            self.widgets['dimension_label'].set_sensitive(False)
            self.widgets['dimension_hbox'].set_sensitive(False)
        else:
            # get dimension
            self.widgets['cols_entry'].set_text(str(config['cols']))
            self.widgets['rows_entry'].set_text(str(config['rows']))

        if (preferences & PREF_TITLE) == 0:
            self.widgets['title_label'].set_sensitive(False)
            self.widgets['title_entry'].set_sensitive(False)
            self.widgets['title_sep'].set_sensitive(False)
        else:
            self.widgets['title_entry'].set_text(
                    self.applet.backend.get_title())

        if (preferences & PREF_ITEM_COUNT) == 0:
            self.widgets['count_label'].set_sensitive(False)
            self.widgets['count_hbox'].set_sensitive(False)
        else:
            self.widgets['count_checkbx'].set_active(config['item_count'])

        # PAGE 3

        if (preferences | BEHAVE_PREFS) == 0:
            page = self.widgets['main_notebook'].page_num(self.widgets['page3'])
            self.widgets['main_notebook'].remove_page(page)

        if (preferences & PREF_FILE_OPERATIONS) == 0:
            self.widgets['operations_label'].set_sensitive(False)
            self.widgets['operations_info_label'].set_sensitive(False)
            self.widgets['operations_hbox'].set_sensitive(False)
            
        else:
            # get file oprations
            actions = config['fileops']
            if actions > 0:
                if (actions & gtk.gdk.ACTION_COPY) == 0:
                    self.widgets['copy_check'].set_active(False)
                if (actions & gtk.gdk.ACTION_MOVE) == 0:
                    self.widgets['move_check'].set_active(False)
                if (actions & gtk.gdk.ACTION_LINK) == 0:
                    self.widgets['link_check'].set_active(False)

        if (preferences & PREF_BROWSING) == 0:
            self.widgets['browse_enabled'].set_sensitive(False)
        else:
            # get browsing
            self.widgets['browse_enabled'].set_active(config['browsing'])
            

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
            filesel.set_filename(self.config['icon_empty'])
        else:
            filesel.set_filename(self.config['icon_full'])
        if filesel.run() == gtk.RESPONSE_OK and filesel.get_filename():
            image = IconFactory().load_image(filesel.get_filename(), 24)
            if image != None:
                if type == "empty":
                    self.config['icon_empty'] = filesel.get_filename()
                    self.widgets['empty_button'].set_image(image)
                else:
                    self.config['icon_full'] = filesel.get_filename()
                    self.widgets['full_button'].set_image(image)
        filesel.destroy()

    def on_empty_button_clicked(self, *args):
        self._select_icon("empty")

    def on_full_button_clicked(self, *args):
        self._select_icon("full")

    def on_cancel_button_clicked(self, *args):
        gui_type = self.widgets['layout_combobox'].get_active() +1
        if gui_type <> self.config['gui_type']:
        	gui_type = self.config['gui_type']
        	if gui_type < 1 or gui_type > 3:
        		gui_type = STACKS_GUI_DIALOG
        	self.applet.set_gui(gui_type)   
        	print "Reverted to previous gui settings" 	    	
        	
        self.destroy()
        
    def on_layout_settings_button_clicked(self, *args):

        self.applet.emit("stacks-gui-config")
        
    def on_layout_combobox_changed(self, *args):
        #the stack gui is changed, we must update it.
    	gui_type = self.widgets['layout_combobox'].get_active() +1
    	if gui_type == 2:
    		self.widgets['layout_settings_button'].set_sensitive(True)
    		self.widgets['dimension_label'].hide_all()
        	self.widgets['dimension_hbox'].hide_all()
    	else:
    		self.widgets['layout_settings_button'].set_sensitive(False)        
    		self.widgets['dimension_label'].show_all()
        	self.widgets['dimension_hbox'].show_all()

        if self.widgets['layout_combobox'].get_active() <> -1:
        	gui_type = self.widgets['layout_combobox'].get_active() +1
        	if gui_type < 1 or gui_type > 3:
				gui_type = STACKS_GUI_DIALOG

        	self.applet.set_gui(gui_type)   
        			

    def on_ok_button_clicked(self, *args):
        # set backend (and type)
        if self.backend is not None:
            self.applet.gconf_client.set_int(
                    self.applet.gconf_path + "/backend_type",
                    BACKEND_TYPE_FOLDER)
            self.applet.gconf_client.set_string(
                    self.applet.gconf_path + "/backend",
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
                self.widgets['composite_checkb'].get_active())
        # set title
        self.applet.gconf_client.set_string(
                self.applet.gconf_path + "/title",
                self.widgets['title_entry'].get_text())
        # set item count
        self.applet.gconf_client.set_bool(
                self.applet.gconf_path + "/item_count",
                self.widgets['count_checkbx'].get_active())
        # set browsing
        self.applet.gconf_client.set_bool(
                self.applet.gconf_path + "/browsing",
                self.widgets['browse_enabled'].get_active())
        # set icons
        self.applet.gconf_client.set_string(
                self.applet.gconf_path + "/applet_icon_empty",
                self.config['icon_empty'])
        self.applet.gconf_client.set_string(
                self.applet.gconf_path + "/applet_icon_full",
                self.config['icon_full'])
        # set stack layout
        if self.widgets['layout_combobox'].get_active() <> -1:
        	gui_type = self.widgets['layout_combobox'].get_active() +1
        	if gui_type <> self.config['gui_type']:
        		
        		if gui_type < 1 or gui_type > 3:
        			gui_type = STACKS_GUI_DIALOG
        		self.config['gui_type'] = gui_type
        		
        		self.applet.gconf_client.set_int(
                    self.applet.gconf_path + "/gui_type", int(gui_type) )
        		
        		self.applet.set_gui(gui_type)

        		
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
        

    def set_current_page(self, page):
        self.widgets['main_notebook'].set_current_page(page)

def get_config_from_gconf(gconf_client, gconf_path, uid):
    # store config in dict
    config = {}
    # try to get backend from gconf
    _config_backend = gconf_client.get_string(gconf_path + "/backend")
    try:
        config['backend'] = VfsUri(_config_backend)
    except:
        file_backend_prefix = "file://" + os.path.join(
                os.path.expanduser("~"),
                ".config", "awn", "applets", "stacks")
        back_uri = VfsUri(file_backend_prefix).as_uri()
        config['backend'] = VfsUri(back_uri.append_path(uid))

    # get dimension
    _config_cols = gconf_client.get_int(gconf_path + "/cols")
    if _config_cols <= 0:
        _config_cols = 5
    config['cols'] = _config_cols

    _config_rows = gconf_client.get_int(gconf_path + "/rows")
    if _config_rows <= 0:
        _config_rows = 4
    config['rows'] = _config_rows

    # get icon size
    _config_icon_size = gconf_client.get_int(
            gconf_path + "/icon_size")
    if _config_icon_size <= 0:
        _config_icon_size = 48
    config['icon_size'] = _config_icon_size

    # get file operations
    _config_fileops = gconf_client.get_int(
            gconf_path + "/file_operations")

    if _config_fileops <= 0:
        _config_fileops = gtk.gdk.ACTION_LINK

    config['fileops'] = _config_fileops

    # get composite icon
    if gconf_client.get_bool(gconf_path + "/composite_icon"):
        config['composite_icon'] = True
    else:
        config['composite_icon'] = False

    # get browsing
    if gconf_client.get_bool(gconf_path + "/browsing"):
        config['browsing'] = True
    else:
        config['browsing'] = False

    # get icons
    _config_icon_empty = gconf_client.get_string(
            gconf_path + "/applet_icon_empty")
    if _config_icon_empty is None or len(_config_icon_empty) == 0:
        _config_icon_empty = _to_full_path("icons/stacks-drop.svg")
    config['icon_empty'] = _config_icon_empty

    _config_icon_full = gconf_client.get_string(
            gconf_path + "/applet_icon_full")
    if _config_icon_full is None or len(_config_icon_full) == 0:
        _config_icon_full = _to_full_path("icons/stacks-full.svg")
    config['icon_full'] = _config_icon_full

    # get item count
    if gconf_client.get_bool(gconf_path + "/item_count"):
        config['item_count'] = True
    else:
        config['item_count'] = False
        
    
    if gconf_client.get_int(gconf_path + "/gui_type"):
    	config['gui_type'] = gconf_client.get_int(gconf_path + "/gui_type")
    else:
    	config['gui_type'] = STACKS_GUI_DIALOG 
    	

    
    return config
