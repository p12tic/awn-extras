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
import gobject
import pango
import gconf
import awn
import cairo
import gnome.ui
import gnomedesktop
import time
import locale
import gettext
import math

import override

from stacks_backend import *
from stacks_backend_file import *
from stacks_backend_folder import *
from stacks_backend_plugger import *
from stacks_backend_trasher import *
from stacks_config import StacksConfig
from stacks_launcher import LaunchManager
from stacks_icons import IconFactory
from stacks_vfs import VfsUri


APP="Stacks"
DIR="locale"
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext


def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)


"""
Main Applet class
"""
class StacksGuiCurved():

    # Structures
    dialog = None
    stack_container = None
    navbuttons = None
    
    maxquantity = None
    stack_height = 100    
    angle_interval = 0.5
    radius = 7000
    direction = "RIGHT"
    text_distance = 50    

    applet = None
    config = None
    store = None
    current_page = 0
    gui_visible = False

    # Status values
    context_menu_visible = False
    just_dragged = False

    def __init__ (self, applet):
        # connect to events
        self.applet = applet
        applet.connect("stacks-gui-hide", self._stacks_gui_hide_cb)
        applet.connect("stacks-gui-show", self._stacks_gui_show_cb)
        applet.connect("stacks-gui-toggle", self._stacks_gui_toggle_cb)
        applet.connect("stacks-config-changed", self._stacks_config_changed_cb)
        applet.connect("stacks-item-removed", self._item_removed_cb)
        applet.connect("stacks-item-created", self._item_created_cb)

    def _stacks_gui_hide_cb(self, widget):
        if self.dialog:
            self.dialog.hide()
        self.gui_visible = False
        

    def _stacks_gui_show_cb(self, widget):
    	
        self.dialog_show_new(self.current_page)
        self.gui_visible = True

    def _stacks_gui_toggle_cb(self, widget):
    	
        if self.gui_visible: return self._stacks_gui_hide_cb(None)
        return self._stacks_gui_show_cb(None)

    def _stacks_config_changed_cb(self, widget, config):
        self.config = config

    def _item_removed_cb(self, widget, store, iter):
        self.store = store
        if self.gui_visible:
            return self._stacks_gui_show_cb(None)

    # launches the command for a stack icon
    # -distinguishes desktop items
    def item_button_cb(self, widget, event, user_data):
        uri, mimetype = user_data
        if event.button == 3:
            self.context_menu_visible = True
            self.item_context_menu(uri).popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            if self.just_dragged:
                self.just_dragged = False
            else:
                self.item_activated_cb(None, user_data)


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


    def item_drag_data_get(
            self, widget, context, selection, info, time, vfs_uri):
        selection.set_uris([vfs_uri.as_string()])


    def item_drag_begin(self, widget, context):
        self.just_dragged = True

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


    def _item_created_cb(self, widget, store, iter, angle = 0, direction = "LEFT"):
        if store:
            self.store = store
        # get values from store
        vfs_uri, lbl_text, mime_type, icon, button = self.store.get(
                iter, COL_URI, COL_LABEL, COL_MIMETYPE, COL_ICON, COL_BUTTON)

        icon_size = self.config['icon_size']
        # create new button
        
        #button = gtk.Button()
        ## using a gtk.EventBox because we want a transparent button        
        button = gtk.EventBox()
        button.set_visible_window(True)
        
        #button.set_relief(gtk.RELIEF_NONE)
        
        button.drag_source_set( gtk.gdk.BUTTON1_MASK,
                                self.applet.dnd_targets,
                                self.config['fileops'])
        button.drag_source_set_icon_pixbuf(icon)
        button.connect( "button-release-event",
                        self.item_button_cb,
                        (vfs_uri, mime_type))
        #button.connect( "activate",
        #                self.item_activated_cb,
        #                (vfs_uri, mime_type))
        ## activate event disabled because it's incompatible with the gtk.EventBox 
        button.connect( "drag-data-get",
                        self.item_drag_data_get,
                        vfs_uri)
        button.connect( "drag-begin",
                        self.item_drag_begin)
                        
                        
                        
        width = 210
        height = 50
        
        offset = int(round(width * math.sin(angle)+3))
        CC = cairoItem(lbl_text,icon,150, 17, angle, direction, offset)  
        CC.set_size_request(width , height + offset ) 
        
        button.add(CC)  
        
        self.store.set_value(iter, COL_BUTTON, button)
        return button


    def dialog_show_prev_page(self, widget, t):
        self.dialog_show_new(self.current_page-1)


    def dialog_show_next_page(self, widget, t):
        self.dialog_show_new(self.current_page+1)

    def dialog_focus_out(self, widget, event):
        if self.context_menu_visible: return
        self._stacks_gui_hide_cb(widget)

    def dialog_show_new(self, page=0):
        assert page >= 0
        self.current_page = page
        

        # create new dialog if it does not exists yet
        if not self.dialog:
            
            self.dialog = awn.AppletDialog (self.applet)
            self.dialog = override.Dialog (self.applet)
            self.dialog.set_focus_on_map(True)
            self.dialog.connect("focus-out-event", self.dialog_focus_out)
            
        # create stack container
        if self.stack_container:
            #for item in self.stack_container.get_children():
            #    self.stack_container.remove(item)
            self.stack_container.destroy()        	
		
        self.stack_container = gtk.Fixed()
        self.dialog.add(self.stack_container)
        
        # create dialog's internals
        new_direction = self.detect_stack_position()
        
        if new_direction != self.direction:
        	self.direction = new_direction
        	direction_change = True
        	print "direction changed to "
        	print self.direction
        else:
        	direction_change = False
        
        if not self.maxquantity:
        	self.maxquantity = self.get_maxquantity()
        self.store = self.applet.backend.get_store()
        iter = self.store.iter_nth_child(None, page * self.maxquantity)
        
        #print page
        
        x=y=0
        theres_more = False
        i = 0
        totalcount= self.maxquantity   #!!!!!!!!! --> self.maxquantity isn't correct, it must be the actual quantity of items

        maxx = int(round(self.radius - self.radius * math.cos(math.radians(self.angle_interval * (totalcount)))))
    
        maxy = self.calc_y_position (totalcount, self.angle_interval, self.radius)        
        
        
        while iter:
        	
            i = i + 1
        	
            x = self.calc_x_position (i, self.angle_interval, self.radius, self.direction, maxx)
            y = self.calc_y_position (i, self.angle_interval, self.radius, maxy)
            angle = self.calc_angle (i, self.angle_interval, self.radius)
            button = self._item_created_cb(None, None, iter, angle, self.direction)
            #t = button.get_parent()
            #if t:
            #    t.remove(button)
            self.stack_container.add(button)  
            if self.direction == "LEFT":
            	self.stack_container.move(button,x + maxx,y)  	
            else:
            	self.stack_container.move(button,x - maxx,y)  	

            
            if i == self.maxquantity:
            	iter = self.store.iter_next(iter)
            	if iter:
                	theres_more = True
                break
            iter = self.store.iter_next(iter)

        
        # if we have more than 1 page and browsing is enabled
        if self.config['browsing'] and (theres_more or page > 0):
        	
			# enable appropriate navigation buttons
			if page > 0:
				enable_left_arrow = True
			else:
				enable_left_arrow = False
			if theres_more:
				enable_right_arrow = True
			else:
				enable_right_arrow = False
				
			icon_size = self.config['icon_size']
			arrow_size = int(round(icon_size / 2))
			
			if self.direction == "LEFT":
				arrow_x_offset = maxx
			else:
				arrow_x_offset = -maxx
			
			if enable_left_arrow:
				bt_left = gtk.EventBox()
				bt_left.set_visible_window(True)
				bt_left.connect( "button-release-event", self.dialog_show_prev_page)
				
				bt_left_cairoArrow = cairoArrow(arrow_size, "LEFT")  
				bt_left_cairoArrow.set_size_request(arrow_size , arrow_size) 
				
				bt_left.add(bt_left_cairoArrow)  
				
				self.stack_container.add(bt_left)  
				self.stack_container.move(bt_left,maxx - arrow_size + maxx,maxy )
				
			if enable_right_arrow:
				bt_right = gtk.EventBox()
				bt_right.set_visible_window(True)
				bt_right.connect( "button-release-event", self.dialog_show_next_page)

				bt_right_cairoArrow  = cairoArrow(arrow_size, "RIGHT") 
				bt_right_cairoArrow.set_size_request(arrow_size , arrow_size) 
				
				bt_right.add(bt_right_cairoArrow)  
				
				self.stack_container.add(bt_right)  
				self.stack_container.move(bt_right,maxx + arrow_size + maxx,maxy )
			
				


        self.dialog.show_all()
        
        

    ##
    # Calculate stack item x coordinate
    #  	
    def calc_x_position (self, i, angle_interval, radius, direction, adjustment = 0):
  		if direction == "RIGHT":
  			x = radius - radius * math.cos(math.radians(angle_interval * i)) + adjustment
  		else:
	  		x = radius - radius * math.cos(math.radians(angle_interval * i))
  			if adjustment != 0:
  				x = adjustment - x
  		return int(round(x))

    ##
    # Calculate stack item y coordinate
    #  	
    def calc_y_position (self, i, angle_interval, radius, adjustment = 0):
  		y = radius * math.sin(math.radians(angle_interval * i)) 
  		if adjustment != 0:
  			y = adjustment -y
  		return int(round(y))

    ##
    # Calculate stack item angle
    #  	
    def calc_angle (self, i, angle_interval, radius):
  		a = math.radians(angle_interval * i)
  		return a        
        
    def get_maxquantity(self):
  		display_manager = gtk.gdk.display_manager_get()
  		default_display = display_manager.get_default_display()
  		screen, wx, wy, modifier = default_display.get_pointer()
  		active_monitor_number = screen.get_monitor_at_point(wx, wy)
  		active_monitor_geometry = screen.get_monitor_geometry(active_monitor_number)
  		active_monitor_height = active_monitor_geometry.height    	
  		maxquantity = int(round((active_monitor_height / (self.config['icon_size'] * 1.5))))
  		return maxquantity
    
    def detect_stack_position(self):
  		display_manager = gtk.gdk.display_manager_get()
  		default_display = display_manager.get_default_display()
  		screen, wx, wy, modifier = default_display.get_pointer()
  		active_monitor_number = screen.get_monitor_at_point(wx, wy)
  		active_monitor_geometry = screen.get_monitor_geometry(active_monitor_number)
  		active_monitor_width = active_monitor_geometry.width
  		mid = int(round(active_monitor_width / 2))
  		
  		if wx < mid:
  			new_direction = "LEFT"
  		else:
  			new_direction = "RIGHT"
  			
  		return new_direction


# Create a GTK+ widget to draw the label
class cairoItem(gtk.DrawingArea):

    def __init__(self, labletext, icon, width, height, rotation, direction = "LEFT", y_offset = 0,  x_offset = 0):
		
		self.labletext = labletext
		self.width = width
		self.height= height
		self.icon = icon
		self.direction = direction
		
		self.x_offset = x_offset
		self.y_offset = y_offset
		
		if direction == "LEFT":
			self.icon_xpos = 0
			self.icon_ypos = 0
			self.label_xpos = 60
			self.label_ypos = 13
			self.rotation = rotation
			self.x_offset = x_offset
			self.y_offset = y_offset
		else: 
			self.icon_xpos = width + 5
			self.icon_ypos = 0
			self.label_xpos = width
			
			self.label_ypos = 13		
			self.rotation = - rotation
			self.x_offset = x_offset
			self.y_offset = 0 #(y_offset + 3)
			
		
		gtk.DrawingArea.__init__(self)
		super(cairoItem, self).__init__()
		self.connect("expose_event", self.expose) 
		
    def expose(self, widget, event):
		self.context = self.new_transparent_cairo_window(self)
		#self.draw_box(self.context)
		#self.days(self.context)
		
		self.drawLabel(self.context)
		self.drawIcon(self.context)
		#self.bottom_text(self.context)
		return True

    def new_transparent_cairo_window(self,widget):
		cr = widget.window.cairo_create()
		cr.save()
		cr.set_operator(cairo.OPERATOR_CLEAR)
		cr.paint()
		cr.restore()
		return cr		
	
    def drawLabel (self, context):
		context.set_font_size(12)
		context.select_font_face("Sans",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
		context.rotate(-self.rotation)
		context.set_source_rgba (0,0,0,0.65)
		
		label_width = context.text_extents(self.labletext)[2] + 10
		
		self.labletext, label_width = self.get_text_width(context, self.labletext, 120)
		
		label_width = label_width + 10
		
		
		if self.direction == "LEFT":
			xpos = self.label_xpos + self.x_offset + 5
			xpos_rect = self.label_xpos + self.x_offset
		else:
			xpos = self.label_xpos + self.x_offset-label_width
			xpos_rect = self.label_xpos + self.x_offset-label_width -5
		
		self.draw_rounded_rect(context,xpos_rect ,self.label_ypos + self.y_offset,label_width,self.height,15)
		context.fill()
		context.save()
		

		context.move_to(xpos, self.label_ypos + self.y_offset + 13 )

			
		context.set_source_rgba(1,1,1)
		
		context.show_text(self.labletext )	
		
    def drawIcon(self, context):
		icon = self.icon
		#scaled = icon.scale_simple(60,60,gdk.INTERP_BILINEAR)
		context.set_source_pixbuf(icon,self.icon_xpos + self.x_offset,self.icon_ypos + self.y_offset)
		context.fill()
		context.paint()

    def get_text_width(self, context, text, maxwidth):
		potential_text = text
		text_width = context.text_extents(potential_text)[2]
		end = -1
		while text_width > maxwidth:
			end -= 1
			potential_text = text[:end] + '...'
			text_width = context.text_extents(potential_text)[2]

		return potential_text, text_width		

    def draw_rounded_rect(self,ct,x,y,w,h,r = 14):
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


class cairoArrow(gtk.DrawingArea):

    def __init__(self, size, direction = "LEFT"):
		
		self.size = size
		self.direction = direction
		self.r = int(round(size/2))
		
		gtk.DrawingArea.__init__(self)
		super(cairoArrow, self).__init__()
		self.connect("expose_event", self.expose) 
		
    def expose(self, widget, event):
		self.context = self.new_transparent_cairo_window(self)
		#self.draw_box(self.context)
		#self.days(self.context)
		
		self.drawArrow(self.context)
		#self.bottom_text(self.context)
		return True

    def new_transparent_cairo_window(self,widget):
		cr = widget.window.cairo_create()
		cr.save()
		cr.set_operator(cairo.OPERATOR_CLEAR)
		cr.paint()
		cr.restore()
		return cr		
	
    def drawArrow (self, context):
    	context.set_source_rgba (0,0,0,0.65)
    	
    	context.arc (self.r, self.r, self.r, 0., 2 * math.pi);
    	context.fill()
    	context.save()
    	
    	if self.direction == "LEFT":
			context.set_source_rgba (1,1,1,0.85)
			context.move_to(1.4 * self.r,1.5  * self.r)
			context.line_to(1.4 * self.r,self.r/2)       
			context.line_to(0.4 * self.r,self.r)       
			context.line_to(1.4 * self.r,1.5  * self.r)
			context.fill()
			context.save()
    	else:
			context.set_source_rgba (1,1,1,0.85)
			context.move_to(0.6 * self.r,1.5  * self.r)
			context.line_to(0.6 * self.r,self.r/2)       
			context.line_to(1.5 * self.r,self.r)       
			context.line_to(0.6 * self.r,1.5  * self.r)
			context.fill()
			context.save()
			
		
