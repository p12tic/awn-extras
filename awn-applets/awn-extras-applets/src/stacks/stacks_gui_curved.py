#!/usr/bin/env python

# stacks_gui_curved  version 0.2
# Copyright (c) 2007 SilentStorm aka Wim Wauters
# based on stacks_gui_dialog.py by Randal Barlow
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

detected_errors = None

try:
 	import sys
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + detected_errors + " * Error importing sys \n"
try:
	import os
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing os \n"
try:
	import gtk
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gtk \n"
try:
	from gtk import gdk
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gdk \n"
try:
	import gobject
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gobject \n"
try:
	import pango
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing pango \n"
try:
	import gconf
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gconf \n"
try:
	import awn
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing awn \n"
try:
	import cairo
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing cairo \n"
try:
	import gnome.ui
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gnome.ui \n"
try:
	import gnomedesktop
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gnomedesktop \n"
try:
	import time
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing time \n"
try:
	import locale
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing locale \n"
try:
	import gettext
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing gettext \n"
try:
	import math
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing math \n"	
try:
	import pangocairo
except ImportError:
	if not detected_errors: detected_errors = ""
	detected_errors = detected_errors + " * Error importing pangocairo \n"	


from stacks_backend import *
from stacks_backend_file import *
from stacks_backend_folder import *
from stacks_backend_plugger import *
from stacks_backend_trasher import *
from stacks_config import StacksConfig
from stacks_launcher import LaunchManager
from stacks_icons import IconFactory
from stacks_vfs import VfsUri
from stacks_glade import GladeWindow

APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext



#constants
stack_item_x = 1

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)

"""
Main Applet class
"""
class StacksGuiCurved(gtk.Window):
	
    #default values
    width = 200
    height = 50
    active_button = None
    dragged_button = None
    stack_items = []
    maxquantity = 3
    
    tooltips_enabled = True
    

    base_angle_interval = 0.85
    currentwidth = 10
    currentheight = 10
 
    angle_interval = 0.02
    radius = 5000
    direction = "RIGHT"
    text_distance = 10    
    icon_padding = 5
    right_arrow_active = False
    left_arrow_active = False
    not_selected_draw_background = False
    tooltip_timer = None
    tooltip_timeout = 800
    
    display_manager = gtk.gdk.display_manager_get()
    default_display = display_manager.get_default_display()
    
    
    # Structures
    dialog = None
    hbox = None
    table = None
    navbuttons = None

    applet = None
    config = None
    store = None
    start_icon = 0

    gui_visible = False

    # Status values
    context_menu_visible = False
    tooltip_visible = False
    just_dragged = False
    gconf_client = None

    signal_ids = []

    def __init__ (self, applet):
    	if detected_errors:
    		print "-------------------------------------------------------------"
    		print "Curved stack couldn't start, Import errors:"
    		print detected_errors
    		print "-------------------------------------------------------------"
    		detected_errors_text = "The curved stack couldn't start, Import errors:\n\n" + detected_errors
    		detected_errors_text = detected_errors_text+ "\nPlease resolve these dependencies"
    		self.errorwindow = gtk.Window()
    		self.errorwindow.set_app_paintable(True)
    		self.errorwindow.set_decorated(True)
    		self.errorwindow.set_focus_on_map(True)
    		self.errorwindow.set_keep_above(True)
    		self.errorwindow.set_skip_pager_hint(False)
    		self.errorwindow.set_skip_taskbar_hint(False)
    		self.errorwindow.set_size_request(-1, -1)
    		#self.errorwindow.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
    		
    		screen, wx, wy, modifier = self.default_display.get_pointer()
    		active_monitor_number = screen.get_monitor_at_point(wx, wy)
    		eww , ewh = self.errorwindow.get_size()
    		active_monitor_geometry = screen.get_monitor_geometry(active_monitor_number)
    		x = int(round((active_monitor_geometry.width - eww)/2))
    		y = int(round((active_monitor_geometry.height - ewh)/2))

    		
    		self.error_image = gtk.Image()
    		
    		self.error_label = gtk.Label(detected_errors_text)
    		hbox = gtk.HBox(False, 0)
    		hbox.pack_start(self.error_image, False, False, 5)  
    		hbox.pack_start(self.error_label, False, False, 10)  
    		self.errorwindow.add(hbox)
    		self.errorwindow.move(x,y)
    		self.errorwindow.show_all()
    		
    		return None

        self.applet = applet
        
        curved_config = get_curved_gui_config(
                self.applet.gconf_client,
                self.applet.gconf_path,
                self.applet.uid)
        self.curved_config = curved_config
    		
        # connect to events
        self.signal_ids.append(applet.connect("stacks-gui-hide", self._stacks_gui_hide_cb))
        self.signal_ids.append(applet.connect("stacks-gui-show", self._stacks_gui_show_cb))
        self.signal_ids.append(applet.connect("stacks-gui-toggle", self._stacks_gui_toggle_cb))
        self.signal_ids.append(applet.connect("stacks-gui-destroy", self._destroy_cb))
        self.signal_ids.append(applet.connect("stacks-config-changed", self._stacks_config_changed_cb))
        self.signal_ids.append(applet.connect("stacks-item-removed", self._item_removed_cb))
        self.signal_ids.append(applet.connect("stacks-item-created", self._item_created_cb))
        self.signal_ids.append(applet.connect("stacks-gui-config", self.show_config))
        
        

        # Init the window
        gtk.Window.__init__(self)
        # set window properties
        self.set_rgba_collormap(self)
        self.set_app_paintable(True)
        self.set_decorated(False)
        self.set_focus_on_map(True)
        self.set_keep_above(True)
        self.set_skip_pager_hint(True)
        self.set_skip_taskbar_hint(True)
        self.set_size_request(self.width, self.height)

        # add events and connect them to some functions
        self.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK)        
        

                                
        #self.connect('screen-changed',

        self.connect('focus-out-event', self._stacks_gui_hide_cb)
        self.connect('expose-event', self.draw_dialog)
        self.connect('leave-notify-event', self.focus_out)
        
        

        self.hbox = gtk.HBox(False, 0)
        self.add(self.hbox)
        self.evb = gtk.EventBox()
        self.evb.set_visible_window(False)
        self.hbox.add(self.evb)
        
        
        self.tooltip_window = gtk.Window()
        gtk.Window.__init__(self.tooltip_window)
        
        self.set_tooltip_window_rgba_collormap(self.tooltip_window)
        self.tooltip_window.set_app_paintable(True)
        self.tooltip_window.set_decorated(False)
        self.tooltip_window.set_focus_on_map(True)
        self.tooltip_window.set_keep_above(True)
        self.tooltip_window.set_skip_pager_hint(True)
        self.tooltip_window.set_skip_taskbar_hint(True)        
        
        self.tooltip_window.set_size_request(-1, 15)
        self.tooltip_window.connect('expose-event', self.draw_tooltip_window)
        
        self.tooltip_window.hide()
        
        self.tooltip_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        
        self.tooltip_image = gtk.Image()
        
        self.tooltip_label = gtk.Label("")
        
        hbox = gtk.HBox(False, 0)
        
        hbox.pack_start(self.tooltip_image, False, False, 5)  
        hbox.pack_start(self.tooltip_label, False, False, 10)  
        self.tooltip_window.add(hbox)
        
        
        
        self.evb.add_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.LEAVE_NOTIFY)      
        self.evb.connect('button-release-event', self.button_release)
        self.evb.connect('motion-notify-event', self.mouse_moved)
        self.evb.connect('leave-notify-event', self.focus_out)
        
        self.connect("scroll_event", self.scroll_stack)
        


    def show_tooltip (self):
    	if self.tooltip_timer:
    		gobject.source_remove(self.tooltip_timer)
    	self.tooltip_timer = None;
    	
    	if self.tooltips_enabled and self.active_button <> None and self.stack_items[self.active_button-1].lbl_text <> self.stack_items[self.active_button-1].displayed_lbl_text:
    		self.tooltip_visible = True

    		screen, mx, my, modifier = self.default_display.get_pointer()
    		active_monitor_number = screen.get_monitor_at_point(mx, my)
    		active_monitor_geometry = screen.get_monitor_geometry(active_monitor_number)
    		sw = active_monitor_geometry.width
    		sh = active_monitor_geometry.height
    		
    		

    		icon = self.stack_items[self.active_button-1].icon
    		size = int(round(self.config['icon_size'] / 2))
    		icon = icon.scale_simple(size,size,gtk.gdk.INTERP_BILINEAR)

    		self.tooltip_window.resize(size, size)
    		#self.tooltip_window.set_size_request(-1, -1)    		
    		self.tooltip_label.set_size_request(-1, -1)
    		
    		self.tooltip_image.set_from_pixbuf(icon)
    		self.tooltip_image.set_size_request(size, size)
    		
    		text = '<i><span foreground="white" >' + self.stack_items[self.active_button-1].lbl_text + '</span></i>'
    		
    		self.tooltip_label.set_text(text)
    		self.tooltip_label.set_justify(gtk.JUSTIFY_CENTER)
    		
    		self.tooltip_label.set_use_markup(True)
    		self.tooltip_label.set_line_wrap(True)
    		# pango layout
    		layout = self.tooltip_label.get_layout()
    		lw, lh = layout.get_size()
    		layout.set_width(int(200) * pango.SCALE)
    		layout.set_wrap(pango.WRAP_WORD_CHAR)
    		
    		layout.set_alignment(pango.ALIGN_CENTER)
    		_lbltxt = self.tooltip_label.get_text()
    		lbltxt = ""
    		for i in range(layout.get_line_count()):
    			length = layout.get_line(i).length
    			lbltxt += str(_lbltxt[0:length]) + '\n'
    			_lbltxt = _lbltxt[length:]
    			
    		self.tooltip_label.set_text(text)
    		self.tooltip_label.set_use_markup(True)
    		self.tooltip_window.resize(lw /pango.SCALE, lh*2/pango.SCALE)
    		
    		tw = lw /pango.SCALE + icon.get_width() + 30 
    		th = lh*2/pango.SCALE
    		
    		
    		if mx+tw > sw: mx = sw - tw    		
    		if my+th > sh: my = sh - th    		
    		
    		self.tooltip_window.move(mx,my)
    		self.tooltip_window.show_all()
    		

    		return False
    	
    	self.tooltip_window.hide()
    	self.tooltip_visible = False
    	
    	return False
 
    def hide_tooltip (self):
    	#if self.tooltip_timer:
    	#	gobject.timeout_remove(self.tooltip_timer)
    	if self.tooltip_timer:
    		gobject.source_remove(self.tooltip_timer)
    	self.tooltip_timer = None;
    	self.tooltip_window.hide()
    	self.tooltip_visible = False
    	
    	    
    def scroll_stack (self, widget, event):
    	if self.config['browsing']:
			if event.direction == gtk.gdk.SCROLL_DOWN and self.theres_more:
				self.dialog_show_new(self.start_icon +1)
			if event.direction == gtk.gdk.SCROLL_UP and self.start_icon > 0:
				self.dialog_show_new(self.start_icon -1)
    
    
    def item_drag_data_get(self, widget, context, selection, info, time):
        #selection.set_uris([vfs_uri.as_string()])
        if self.dragged_button <> None:
        	uri = self.stack_items[self.dragged_button-1].vfs_uri
        	selection.set_uris([uri.as_string()])
        	
        	
        


    def item_drag_begin(self, widget, context):
        self.just_dragged = True

                
    def button_release(self, widget, event):
    	
        if event.button == 3:
            self.context_menu_visible = True
            self.item_context_menu(self.stack_items[self.active_button-1].vfs_uri).popup(None, None, None, event.button, event.time)
        elif event.button == 1 and self.active_button <> None:
        	uri = self.stack_items[self.active_button-1].vfs_uri
        	mimetype = self.stack_items[self.active_button-1].mime_type
        	
        	user_data = uri , mimetype
        	
        	if self.just_dragged:
        		self.just_dragged = False
        	else:
        		self.item_activated_cb(None, user_data)
        elif event.button == 1 and self.left_arrow_active:

        	start = self.start_icon - self.maxquantity
        	if start < 0: start = 0
        	self.dialog_show_new(start)
        	self.queue_draw()
        elif event.button == 1 and self.right_arrow_active:
        	self.dialog_show_new(self.start_icon + self.maxquantity)
        	self.queue_draw()
       
        self.just_dragged = False
        return True        
        
    def focus_out(self, widget, event):
    	
    	self.queue_draw()

    def mouse_moved(self, widget, event):
    	#print "mouse moved: active button -> " + str(self.active_button)
    	if not self.just_dragged:
			icon_size = self.config['icon_size']
			self.right_arrow_active = False
			self.left_arrow_active = False
			
			for si in self.stack_items[:]:
				y = si.icon_y
				yt = si.icon_y + icon_size + self.icon_padding
				if y < event.y and yt > event.y:

					if (event.x > si.label_position and self.direction == "RIGHT") or (event.x < (self.maxx - si.x + icon_size *5 / 4+ self.text_distance + si.label_width) and self.direction == "LEFT"):
						
						if self.active_button <> si.id:
							self.active_button = si.id
							self.dragged_button = self.active_button
							self.evb.drag_source_set_icon_pixbuf(si.icon)    
							self.queue_draw()							

							self.hide_tooltip ()
							self.tooltip_timer = gobject.timeout_add (self.tooltip_timeout, self.show_tooltip)
						return True
						
			
			if self.left_arrow_enabled:
				ax, ay, aw, ah = self.left_arrow_position
				if event.x > ax and event.x < ax+aw and event.y > ay and event.y < ay+ah:
					self.active_button = None
					self.left_arrow_active = True
					self.queue_draw()
					return True

			if self.right_arrow_enabled:
				ax, ay, aw, ah = self.right_arrow_position
				if event.x > ax and event.x < ax+aw and event.y > ay and event.y < ay+ah:
					self.active_button = None
					self.right_arrow_active = True
					self.queue_draw()
					
					return True
					
			if self.active_button != None:
				self.active_button = None
				self.queue_draw()

    	self.hide_tooltip()
    	return False


    def set_rgba_collormap(self, widget):
        screen = self.get_screen()
        color_map = screen.get_rgba_colormap()
        if not color_map:
            print "Your screen doesn't support alpha channels!"
            color_map = screen.get_rgb_colormap()
        self.set_colormap(color_map)
        return False        

    def set_tooltip_window_rgba_collormap(self, widget):
        screen = self.tooltip_window.get_screen()
        color_map = screen.get_rgba_colormap()
        if not color_map:
            print "Your screen doesn't support alpha channels!"
            color_map = screen.get_rgb_colormap()
        self.tooltip_window.set_colormap(color_map)
        return False     
        

    def _destroy_cb(self, widget):
        for id in self.signal_ids: self.applet.disconnect(id)

        
    def show_config(self, widget):
    	curved_cfg = CurvedStacksConfig(self.applet)


    def _stacks_gui_hide_cb(self, widget, event = None):
    	if self.context_menu_visible: return
    	self.hide_tooltip()
    	self.hide()
    	self.start_icon = 0
    	
        self.gui_visible = False

    def _stacks_gui_show_cb(self, widget):
        self.dialog_show_new()
        self.gui_visible = True

    def _stacks_gui_toggle_cb(self, widget):
        if self.gui_visible: return self._stacks_gui_hide_cb(None)
        return self._stacks_gui_show_cb(None)

    def _stacks_config_changed_cb(self, widget, config):
        self.config = config
        curved_config = get_curved_gui_config(
                self.applet.gconf_client,
                self.applet.gconf_path,
                self.applet.uid)
        self.curved_config = curved_config

    def _item_created_cb(self, widget, store, iter, angle = 0, direction = "LEFT",id = 0):
        if store:
            self.store = store
        # get values from store
        vfs_uri, lbl_text, mime_type, icon, button = self.store.get(
                iter, COL_URI, COL_LABEL, COL_MIMETYPE, COL_ICON, COL_BUTTON)

        icon_size = self.config['icon_size']


        return button

    def _item_removed_cb(self, widget, store, iter):
        self.store = store
        if self.gui_visible:
            return self._stacks_gui_show_cb(None)


    def item_activated_cb(self, widget, user_data):
        uri, mimetype = user_data
        if uri.as_string().endswith(".desktop"):
            item = gnomedesktop.item_new_from_uri(
                    uri.as_string(), gnomedesktop.LOAD_ONLY_IF_EXISTS)
            if item:
                command = item.get_string(gnomedesktop.KEY_EXEC)
                LaunchManager().launch_command(command, uri.as_string())
        else:
            LaunchManager().launch_uri(uri.as_string(), mimetype)

    def item_clear_cb(self, widget, uri):
        self.applet.backend.remove([uri])

    def item_menu_hide_cb(self, widget):
        self.context_menu_visible = False

    def item_context_menu(self, uri):
        self.context_menu_visible = True
        context_menu = gtk.Menu()
        del_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_CLEAR)
        context_menu.append(del_item)
        del_item.connect_object("activate", self.item_clear_cb, self, uri)
        context_menu.connect("hide", self.item_menu_hide_cb)
        context_menu.show_all()
        return context_menu

    def dialog_show_prev_page(self, widget):
        self.dialog_show_new(self.start_icon- self.maxquantity)


    def dialog_show_next_page(self, widget):
    	
        self.dialog_show_new(self.start_icon+ self.maxquantity)

    def dialog_focus_out(self, widget, event):
        if self.context_menu_visible or self.tooltip_visible : return
        self._stacks_gui_hide_cb(widget)
        
    def reposition(self, w, h):
        # borrowed from awn-applet-dialog.c: awn_applet_dialog_position_reset
        ax, ay = self.applet.window.get_origin()
        aw, ah = self.applet.get_size_request()
        
        display_manager = gtk.gdk.display_manager_get()
        default_display = display_manager.get_default_display()
        screen, wx, wy, modifier = default_display.get_pointer()
        active_monitor_number = screen.get_monitor_at_point(ax, ay)
        active_monitor_geometry = screen.get_monitor_geometry(active_monitor_number)
        sw = active_monitor_geometry.width
        
        icon_size = self.config['icon_size']
        if self.direction == "RIGHT":
        	x = ax + aw/2  - self.text_distance - self.curved_config['label_length'] - icon_size / 2;
        else:
        	x = ax + aw/2  - icon_size / 2 - self.maxx - icon_size / 4;
        y = ay - h + 50
        if x < 0:
            x = 2
        if x+w > sw:
            x = sw - w - 20
        self.move(int(x), int(y))        
        
        screen_mid = sw / 2
        if ax > screen_mid:
        	self.direction = "RIGHT"
        else:
        	self.direction = "LEFT"
        	

    # Calculate stack item x coordinate
    def calc_x_position (self, i):
  		x = self.radius - self.radius * math.cos(math.radians(self.angle_interval * i))
  		return x


    # Calculate stack item y coordinate
    def calc_y_position (self, i):
  		y = self.radius * math.sin(math.radians(self.angle_interval * i)) 
  		return y

    # Calculate stack item angle
    def calc_angle (self, i):
  		a = math.radians(self.angle_interval * i)
  		return a        


    def new_stack_item(self, iter, x=0, y=0, angle = 0, id = 0):

        # get values from store
        vfs_uri, lbl_text, mime_type, icon, button = self.store.get(
                iter, COL_URI, COL_LABEL, COL_MIMETYPE, COL_ICON, COL_BUTTON)

        icon_size = self.config['icon_size']
        # create new stackitem
        si = [0]
        return si

    # prepare and show the stack
    def dialog_show_new(self, start_icon=None):

        self.store = self.applet.backend.get_store()
        self.item_count=len(self.store)
        
        if start_icon == None:
        	start_icon=0
         
        if start_icon < 0:
        	start_icon=0
        	
        
        
        self.start_icon = start_icon
        self.active_button = None
       
        self.evb.connect( "drag-data-get",self.item_drag_data_get)
        self.evb.connect( "drag-begin",self.item_drag_begin)
        self.evb.drag_source_set( gtk.gdk.BUTTON1_MASK,
                                self.applet.dnd_targets,
                                self.config['fileops'])
         
                
        icon_size = self.config['icon_size']
        ax, ay = self.applet.window.get_origin()
        max_height = ay
        
        self.angle_interval = self.base_angle_interval * icon_size / 50
        
        #prepare the stack data to display
        self.theres_more = False
        iter = self.store.iter_nth_child(None, self.start_icon)
        
        i = 0
        self.stack_items = []
        while iter:
        	i = i +1
        	
        	x = self.calc_x_position (i)
        	y = self.calc_y_position (i)
        	angle = self.calc_angle (i)
        	#angle = math.radians(self.angle_interval)
        	
        	vfs_uri, lbl_text, mime_type, icon, button = self.store.get(
                iter, COL_URI, COL_LABEL, COL_MIMETYPE, COL_ICON, COL_BUTTON)

        	si = stack_item(x,y,angle,vfs_uri, lbl_text, mime_type, icon, i)
        	
        	if si.y+icon_size * 5 /4 > max_height:
        		#iter = self.store.iter_next(iter)
        		#self.height = self.maxy
        		        		
        		self.theres_more = True
        		break

        	self.stack_items.append(si)
        	iter = self.store.iter_next(iter)
        	self.maxx = si.x
        	self.maxy = si.y   
        	if self.maxquantity < i: self.maxquantity = i
        

  
        self.width = int(round( self.text_distance + self.curved_config['label_length'] + icon_size + self.maxx + icon_size / 4))
        
        self.right_arrow_enabled = False
        self.left_arrow_enabled = False
        self.icon_vertical_offset = 0
        
        if (self.theres_more or self.start_icon > 0) and self.config['browsing']:
        	self.icon_vertical_offset = icon_size / 2
        	if self.theres_more:
        		self.right_arrow_enabled = True
        	if self.start_icon > 0:
        		self.left_arrow_enabled = True

        self.height = int(round(self.maxy + icon_size))       
        #and finally show the stuff
        self.show_all()
        
    def draw_tooltip_window(self, widget, event):    
            
        # create the cairo context
        tooltip_context = self.tooltip_window.window.cairo_create()
        
        rx = 1
        ry = 1
        rw, rh = self.tooltip_window.get_size()
        
        rw = rw -2
        rh = rh -2

        # draw a transparent background
        tooltip_context.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        tooltip_context.set_operator(cairo.OPERATOR_SOURCE)

        tooltip_context.paint ()
        tooltip_context.set_operator (cairo.OPERATOR_OVER)
        
        
        self.linear = cairo.LinearGradient(rx, ry, rx, ry+rh)
        self.linear.add_color_stop_rgba(0, 0, 0, 0, 0.75)
        self.linear.add_color_stop_rgba(0.5, 0, 0, 0, 0.55)
        self.linear.add_color_stop_rgba(1, 0, 0, 0, 0.75)
        tooltip_context.set_source(self.linear)
        
        self.draw_rounded_rect(tooltip_context,rx,ry,rw,rh,15)
        tooltip_context.fill()
        tooltip_context.set_source_rgba (1,1,1,0.45)
        self.draw_rounded_rect(tooltip_context,rx,ry,rw,rh,15)
        tooltip_context.set_line_width (2);
        tooltip_context.stroke()
        
        self.linear = cairo.LinearGradient(rx, ry, rx, ry+rh/4+15)
        self.linear.add_color_stop_rgba(0, 1, 1, 1, 0.45)
        self.linear.add_color_stop_rgba(0.5, 1, 1, 1, 0.15)
        self.linear.add_color_stop_rgba(1, 0, 0, 0, 0.05)
        tooltip_context.set_source(self.linear)
        
        self.draw_top_rounded_rect(tooltip_context,rx,ry,rw,rh,15)
        tooltip_context.fill()
        
    def draw_dialog(self, widget, event):    
    
        #print " > dialog exposed, redrawing < "
        self.reposition(self.width, self.height)
        if self.currentwidth <> self.width or self.currentheight <> self.height:
        	self.currentwidth = self.width
        	self.currentheight = self.height
        	#self.set_size_request(self.width, self.height)
        	self.resize(self.width, self.height)
        
        # create the cairo context
        context = self.window.cairo_create()

        # draw a transparent background
        #context.set_source_rgba(1.0, 1.0, 1.0, 0.4)
        context.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        context.set_operator(cairo.OPERATOR_SOURCE)
        #cr.set_operator(cairo.OPERATOR_CLEAR)
        context.paint()

        context.set_operator(cairo.OPERATOR_OVER)
        context.set_source_rgba(0.1, 0.1, 0.1, 0.8)
        
        icon_size = self.config['icon_size']
        
        for si in self.stack_items[:]:
        	self.draw_stack_item(context, si)
        	
        
        	
        if self.right_arrow_enabled:
        	if self.direction == "RIGHT":
        		self.right_arrow_position = self.drawArrow ( context, self.text_distance + self.curved_config['label_length'] + icon_size *3 / 4, self.height - icon_size / 2, icon_size / 4, "RIGHT", self.right_arrow_active)
        	else:
        		self.right_arrow_position = self.drawArrow ( context,  self.maxx + icon_size , self.height - icon_size / 2, icon_size / 4, "RIGHT", self.right_arrow_active)
        if self.left_arrow_enabled:
        	if self.direction == "RIGHT":
        		self.left_arrow_position = self.drawArrow ( context, self.text_distance + self.curved_config['label_length'] + icon_size / 4, self.height - icon_size / 2, icon_size / 4, "LEFT", self.left_arrow_active)
        	else:
        		self.left_arrow_position = self.drawArrow ( context, self.maxx + icon_size / 2, self.height - icon_size / 2, icon_size / 4, "LEFT", self.left_arrow_active)
        	
        	
        self.reposition(self.width, self.height)
        	
    def draw_stack_item(self, context, si, selected = False):
    	
    	if self.active_button == si.id:
    		selected = True
    	
    	icon_size = self.config['icon_size']
    	
    	mtrx = context.get_matrix()

    	icon_y = (self.height - si.y - self.icon_vertical_offset ) / math.cos(si.angle)
    	si.icon_y = icon_y

    	
    	if self.direction == "RIGHT":
    		icon_x = si.x + self.text_distance + self.curved_config['label_length']
    		label_x = 0
    		angle = si.angle
    	else:
    		icon_x = self.maxx - si.x + icon_size / 4 
    		label_x = icon_size
    		angle = -si.angle
    		
    	
    	label_y = icon_y + icon_size / 2
    	context.translate(icon_x,icon_y)
    	context.rotate(angle)
     	
    	self.drawBackground(context, 0, 0, selected)
    	self.drawIcon(context, 0, 0, si.icon, selected)
    	si.label_position, si.label_width, si.displayed_lbl_text = self.drawLabel(context, label_x, icon_size / 2, si.lbl_text, selected)
    	self.drawForeground(context, 0, 0, selected)
    	
    	si.label_position = si.label_position + icon_x + label_x
    	
    	context.set_matrix (mtrx)
    	"""
    	if self.direction == "RIGHT":
    		context.rotate(-si.angle)
    	else:
    		context.rotate(si.angle)
    		"""
    	
    def drawBackground(self, context, x, y, selected = False):
		icon_size = self.config['icon_size']
		
		if selected:
			context.set_source_rgba (0,0,0,0.45)
			
			rx = x-self.icon_padding/2
			ry = y-self.icon_padding/2
			rw = icon_size+self.icon_padding
			rh = icon_size+self.icon_padding
			
			self.linear = cairo.LinearGradient(rx, ry+rh, rx+rw, ry)
			self.linear.add_color_stop_rgba(0, 0, 0, 0, 0.55)
			self.linear.add_color_stop_rgba(0.5, 0.5, 0.5, 0.5, 0.25)
			self.linear.add_color_stop_rgba(1, 0, 0, 0, 0.45)
			context.set_source(self.linear)
			
			self.draw_rounded_rect(context,rx,ry,rw,rh,15)
			context.fill()
			context.set_source_rgba (1,1,1,0.45)
			self.draw_rounded_rect(context,rx,ry,rw,rh,15)
			context.set_line_width (2);
			context.stroke()
		elif self.not_selected_draw_background:
			
			rx = x-self.icon_padding/2
			ry = y-self.icon_padding/2
			rw = icon_size+self.icon_padding
			rh = icon_size+self.icon_padding
			
			context.set_source_rgba (1,1,1,0.25)
			self.draw_rounded_rect(context,rx,ry,rw,rh,15)
			context.fill()
			context.set_source_rgba (0,0,0,0.35)
			self.draw_rounded_rect(context,rx,ry,rw,rh,15)
			context.set_line_width (2);
			context.stroke()    	
    	
    
    def drawIcon(self, context, x, y, icon, selected = False):
		icon_size = self.config['icon_size']
		
		iw = icon.get_width()
		ih = icon.get_height()
		
		# adjust the icon position if it is smaller than the icon size. 
		x_adjust = 0
		y_adjust = 0
		if iw < icon_size: x_adjust = (icon_size - iw) / 2
		if ih < icon_size: y_adjust = (icon_size - ih) / 2
		
		context.set_source_pixbuf(icon,x+x_adjust,y+y_adjust)
		context.fill()
		context.paint()
		
    	
    def drawForeground(self, context, x, y, selected = False):
		icon_size = self.config['icon_size']
		
		if selected:
			context.set_source_rgba (1,1,1,0.25)

			rx = x-self.icon_padding/2
			ry = y-self.icon_padding/2
			rw = icon_size+self.icon_padding
			rh = icon_size+self.icon_padding
			
			self.linear = cairo.LinearGradient(rx, ry, rx, ry+rh/4+15)
			self.linear.add_color_stop_rgba(0, 1, 1, 1, 0.45)
			self.linear.add_color_stop_rgba(0.5, 1, 1, 1, 0.15)
			self.linear.add_color_stop_rgba(1, 0, 0, 0, 0.05)
			context.set_source(self.linear)
			
			self.draw_top_rounded_rect(context,rx,ry,rw,rh,15)
			context.fill()

		elif self.not_selected_draw_background:
			print "forground"

    def drawLabel (self, context, x, y, labletext, selected = False):
    	
		pango_context = pangocairo.CairoContext (context)
		
		pango_layout = pango_context.create_layout ()
		
		
		pango_layout.set_font_description(pango.FontDescription("sans 10"))
		
		#fontmap = pangocairo.cairo_font_map_get_default()
		
		#font.set_size(10)
		#pango_layout.set_font_description(pango.FontDescription("10"))
		
		y = y -7 # compensating for lable height of 16

		if selected:
			context.set_source_rgba (1,1,1,0.65)
		else:
			context.set_source_rgba (0,0,0,0.65)
		
		label_width = 10
		labletext, label_width = self.get_text_width(pango_layout, labletext,self.curved_config['label_length'])
		label_width = label_width + 10
		
		if self.direction == "RIGHT":
			x = x - label_width - self.text_distance
		else:
			x = x + self.text_distance
		
		self.draw_rounded_rect(context, x, y,label_width,16,7)
		context.fill()
		
		if selected:
			context.set_source_rgba(0,0,0,1)
		else:
			context.set_source_rgba(1,1,1,1)		
		
		#context.set_source_rgba (1,1,1,0.65)
		self.draw_rounded_rect(context, x, y,label_width,16,7)
		context.set_line_width (0.5);
		context.stroke()    	

		context.move_to(x+5,y)


		pango_layout.set_text(labletext)
		
		
		pango_context.show_layout (pango_layout)
				
		return x, label_width, labletext

    def get_text_width(self, pango_layout, text, maxwidth):
		potential_text = text
		maxwidth = maxwidth - 50 
		pango_layout.set_text(potential_text)
		text_width = pango_layout.get_pixel_size()[0]
		end = -1
		while text_width > maxwidth:
			end -= 1
			potential_text = text[:end] + '...'
			pango_layout.set_text(potential_text)
			text_width = pango_layout.get_pixel_size()[0]
		return potential_text, text_width		

    def draw_top_rounded_rect(self,ct,x,y,w,h,r = 16):
		#   A-----BQ
		#  F       C
		#  |     /-D
		#  |  /-/   
		#  E-/ 
		ct.move_to(x+r,y)                      # Move to A
		ct.line_to(x+w-r,y)                    # Straight line to B
		ct.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
		ct.line_to(x+w,y+h/3)                  # Move to D
		ct.curve_to(x,y+h/3,x+w,y+h/4+r,x,y+h/4+r) # Curve to E

		ct.line_to(x,y+r)                    # Line to F
		ct.curve_to(x,y,x,y,x+r,y)             # Curve to A
		return        

    def draw_rounded_rect(self,ct,x,y,w,h,r = 16):
		#   A****BQ
		#  H      C
		#  *      *
		#  G      D
		#   F****E
		ct.move_to(x+r,y)                      # Move to A
		ct.line_to(x+w-r,y)                    # Straight line to B
		ct.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
		ct.line_to(x+w,y+h-r)                  # Move to D
		ct.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
		ct.line_to(x+r,y+h)                    # Line to F
		ct.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
		ct.line_to(x,y+r)                      # Line to H
		ct.curve_to(x,y,x,y,x+r,y)             # Curve to A
		return        
        	
    def drawArrow (self, context, x, y, size, direction, selected = False):
    	
		if selected:
			context.set_source_rgba (1,1,1,0.35)
		else:
			context.set_source_rgba (0,0,0,0.75)
			
		context.arc (x, y, size, 0., 2 * math.pi);
		context.fill()
		context.set_source_rgba (1,1,1,0.65)
		context.arc (x, y, size, 0., 2 * math.pi);
		context.set_line_width (1);

		context.stroke()
			
		if direction == "LEFT":
			if selected:
				context.set_source_rgba (0,0,0,0.85)
			else:
				context.set_source_rgba (1,1,1,0.85)
			
			context.move_to(x-size/2,y )
			context.line_to(x+size/2,y+size/2)       
			context.line_to(x+size/2,y-size/2)       
			context.line_to(x-size/2,y )
		else:
			if selected:
				context.set_source_rgba (0,0,0,0.85)
			else:
				context.set_source_rgba (1,1,1,0.85)			

			context.move_to(x+size/2,y )
			context.line_to(x-size/2,y+size/2)       
			context.line_to(x-size/2,y-size/2)       
			context.line_to(x+size/2,y )
		context.fill()
		
		xt = x - size
		yt = y - size
		w = size * 2
		h = size * 2
		arrow_position = xt, yt, w, h	
		
		return arrow_position
 	
        	        
class stack_item:
	#objet with all stack data 
	
	def __init__ (self,x,y,angle,vfs_uri, lbl_text, mime_type, icon, id = -1):
		self.x=x
		self.y=y
		self.angle=angle
		self.vfs_uri=vfs_uri
		self.lbl_text = lbl_text
		self.mime_type = mime_type
		self.icon = icon
		self.id = id
		self.label_position = 0
		self.displayed_lbl_text = lbl_text
		self.label_width = 150
		self.icon_y = 0


class CurvedStacksConfig(GladeWindow):
    glade_file = _to_full_path('curved_stacks_preferences.glade')
    backend_type = BACKEND_TYPE_INVALID
    applet = None

    backend = None
    config = None

    def __init__(self, applet):
        GladeWindow.__init__(self)
        self.applet = applet
        
        config = get_curved_gui_config(
                self.applet.gconf_client,
                self.applet.gconf_path,
                self.applet.uid)
        self.config = config


        #set label length
        self.widgets['label_length_box'].set_value(config['label_length'])
    
    def on_cancel_button_clicked(self, *args):
    	self.destroy()

    def on_ok_button_clicked(self, *args):
    	#save configuration to gconf
    	label_length = self.widgets['label_length_box'].get_value()
        if int(label_length) > 0:
            self.applet.gconf_client.set_int(
                    self.applet.gconf_path + "/curved_gui/label_length", int(label_length) )
    	self.destroy()
    	
def get_curved_gui_config(gconf_client, gconf_path, uid):
    # store config in dict
    config = {}
    # try to get backend from gconf

    # get dimension
    _config_label_length = gconf_client.get_int(gconf_path + "/curved_gui/label_length")
    if _config_label_length <= 0:
        _config_label_length = 200
    config['label_length'] = _config_label_length

	
    
    
    return config
