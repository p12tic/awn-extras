#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
#
#To-Do List Applet
#Applet file

#Gtk, etc. stuff
import gobject
import pygtk
pygtk.require('2.0')
import gtk
import cairo

#This applet stuff
import settings
import icon

#Awn stuff
import sys
import awn
from awn.extras import detach

#TODO: Preferences dialog

class App(awn.AppletSimple):
  last_num_items = -1
  def __init__(self, uid, orient, height):
    self.uid = uid
    self.height = height
    
    #Values that will be referenced later
    self.displayed = False
    self.detached = False
    
    #AWN Applet Configuration
    awn.AppletSimple.__init__(self,uid,orient,height)
    self.title = awn.awn_title_get_default()
    self.dialog = awn.AppletDialog(self)
    
    #Give the dialog an AccelGroup (is this all that necessary)
    self.accel = gtk.AccelGroup()
    self.dialog.add_accel_group(self.accel)
    
    #Set up Settings
    #TODO: Switch to AwnConfigClient
    self.settings = settings.Settings('to-do', uid)
    self.settings.register({'items':[str],'details':[str],'progress':[int],\
      'priority':[int],'color':str,'title':str,'icon-type':str,'colors':[int],\
      'category':[int],'category_name':[str],'expanded':[int],\
      'icon-opacity':int})
    print self.settings._values
    
    
#    #Get the title or default to "To-Do List"
#    if self.settings['title'] in ['',None]:
#      self.settings['title'] = 'To-Do List'
#    
#    #Set up the keys for item progress, priorities, and details
#    #Details
#    tmp_list = []
#    if len(self.settings['details'])!=len(self.settings['items']):
#      for x in self.settings['items']:
#        tmp_list.append('')
#      self.settings['details'] = tmp_list
#    
#    #Progress
#    tmp_list = []
#    if len(self.settings['progress'])!=len(self.settings['items']):
#      for x in self.settings['items']:
#        tmp_list.append(0)
#      self.settings['progress'] = tmp_list
#    
#    #Priority
#    tmp_list = []
#    if len(self.settings['priority'])!=len(self.settings['items']):
#      for x in self.settings['items']:
#        tmp_list.append(0)
#      self.settings['priority'] = tmp_list
#    
#    #Categories
#    tmp_list = []
#    if len(self.settings['category'])!=len(self.settings['items']):
#      for x in self.settings['items']:
#        tmp_list.append(-1)
#      self.settings['category'] = tmp_list
#    
#    #Category names
#    tmp_list = []
#    if len(self.settings['category_name'])!=len(self.settings['items']):
#      for x in self.settings['items']:
#        tmp_list.append('')
#      self.settings['category_name'] = tmp_list
    
    #Icon Type
    if self.settings['icon-type'] not in ['progress','progress-items','items']:
      self.settings['icon-type'] = 'items'
    
    #Icon opacity
    if self.settings['icon-opacity'] < 10 or \
      self.settings['icon-opacity'] > 100:
      self.settings['icon-opacity'] = 90
    
    #Get the Icon Theme - used for the "X" to remove an item
    #and the > arrow to edit details of an item
    self.icon_theme = gtk.icon_theme_get_default()
    
    #Set up the drawn icon - colors and stuff
    
    #Get the icon color
    #One of the Tango Desktop Project Color Palatte colors
    if self.settings['color'] in ['butter','chameleon','orange','skyblue',\
      'plum','chocolate','scarletred','aluminium1','aluminium2']:
      self.color = icon.colors[self.settings['color']]
    
    #Custom colors
    elif self.settings['color'] == 'custom':
      #Get the colors of the custom icon color
      self.color = []
      
      #Outer border - red, green, blue
      self.color[0] = [self.settings['colors'][0],self.settings['colors'][1],\
        self.settings['colors'][2]]
      
      #Inner border - red, green, blue
      self.color[1] = [self.settings['colors'][3],self.settings['colors'][4],\
        self.settings['colors'][5]]
      
      #Main color - red, green, blue
      self.color[2] = [self.settings['colors'][6],self.settings['colors'][7],\
        self.settings['colors'][8]]
      
      #Text color - reg, green, blue
      self.color[3] = [self.settings['colors'][9],self.settings['colors'][10],\
        self.settings['color'][11]]
    
    #Gtk Theme colors
    elif self.settings['color'] == 'gtk':
      self.update_icon_theme()
    
    #No or invalid color set
    #Default to "Sky Blue" (My Favorite ;)
    else:
      self.settings['color'] = 'skyblue'
      self.color = icon.colors['skyblue']
    
    #Set up detach (settings, etc. is done a little later)
    self.detach = detach.Detach()
    
    #Setup the icon
    self.update_icon()
    
    #Set some settings
    self.detach['applet-right-click'] = 'signal'
    self.detach['right-click'] = 'signal'
    
    #Connect to some signals
    self.detach.connect('hide-awn-icon',self.hide_icon)
    self.detach.connect('attach',self.was_attached)
    self.detach.connect('detach',self.was_detached)
    self.detach.connect('applet-toggle-dialog',self.toggle_dialog)
    self.detach.connect('show-dialog',self.show_dialog)
    self.detach.connect('hide-dialog',self.hide_dialog)
    self.detach.connect('applet-right-click',self.show_menu)
    self.detach.connect('right-click',self.show_menu)
    self.detach.connect(['scroll-up','scroll-right'],self.opacity,True)
    self.detach.connect(['scroll-down','scroll-left'],self.opacity,False)
    
    #Prepare the applet for dragging from Awn
    self.detach.prepare_awn_drag_drop(self)
    
    #Connect to events
    self.connect('enter-notify-event',\
      lambda *a: self.title.show(self,self.settings['title']))
    self.connect('leave-notify-event',\
      lambda *a: self.title.hide(self))
    self.dialog.connect('focus-out-event',self.hide_dialog)
    self.settings.connect('items',self.update_icon,'settings')
    self.settings.connect('progress',self.update_icon,'settings')
  
  #Remove anything shown in the dialog - does not hide the dialog
  def clear_dialog(self,*args):
    try:
      self.dialog_widget.destroy()
    except:
      pass
  
  #Add a widget to the dialog - detached or not
  def add_to_dialog(self,widget):
    self.dialog_widget = widget
    if self.detached == True:
      self.detach.add(self.dialog_widget)
    else:
      self.dialog.add(self.dialog_widget)
  
  #Display a right-click context menu
  def show_menu(self,event):
    #Hide the dialog if it's shown
    self.hide_dialog()
    
    #Create the items for Preferences, Detach, and About
    #prefs_menu = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
    detach_menu = self.detach.menu_item(self.do_detach,self.do_attach)
    about_menu = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
    
    #Connect the two items to functions when selected
    #prefs_menu.connect('activate',self.show_prefs)
    about_menu.connect('activate',self.show_about)
    
    #Now create the menu to put the items in and show it
    menu = self.create_default_menu()
    #menu.append(prefs_menu)
    menu.append(detach_menu)
    menu.append(about_menu)
    menu.show_all()
    menu.popup(None, None, None, event.button, event.time)
  
  #Detach the applet
  def do_detach(self,*args):
    self.detach.detach()
    self.displayed = False
    self.detached = True
  
  #The applet was detached
  #Do NOT hide the icon; hide the dialog (just in case)
  def was_detached(self):
    self.detached = True
    self.update_icon()
    self.hide_dialog()
  
  #Show the preferences menu
  def show_prefs(self,*args):
    pass
  
  #Attach the applet
  def do_attach(self,*args):
    self.detach.attach()
  
  #The applet was attached
  def was_attached(self,*args):
    #Show the regular icon
    self.detached = False
    self.last_num_items = -1
    self.update_icon()
  
  #Show the about dialog
  def show_about(self,*args):
    win = gtk.AboutDialog()
    win.set_name("To-Do List")
    win.set_copyright("Copyright 2008 sharkbaitbobby "+\
      "<sharkbaitbobby+awn@gmail.com>")
    win.set_authors(["sharkbaitbobby <sharkbaitbobby+awn@gmail.com>"])
    win.set_comments("A simple To-Do List")
    win.set_license("This program is free software; you can redistribute it "+\
      "and/or modify it under the terms of the GNU General Public License "+\
      "as published by the Free Software Foundation; either version 2 of "+\
      "the License, or (at your option) any later version. This program is "+\
      "distributed in the hope that it will be useful, but WITHOUT ANY "+\
      "WARRANTY; without even the implied warranty of MERCHANTABILITY or "+\
      "FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public "+\
      "License for more details. You should have received a copy of the GNU "+\
      "General Public License along with this program; if not, write to the "+\
      "Free Software Foundation, Inc.,"+\
      "51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.")
    win.set_wrap_license(True)
    win.set_documenters(["sharkbaitbobby <sharkbaitbobby+awn@gmail.com>"])
    win.set_artists(["Cairo"])
    win.run()
    win.destroy()
  
  #Hide the icon
  def hide_icon(self):
    self.set_icon(self.detach.empty_pixbuf())
    self.hide()
  
  #Hide the dialog
  def hide_dialog(self,*args):
    #The dialog is no longer displayed
    self.displayed = False
    
    #Clear the dialog
    self.clear_dialog()
    
    #Hide the Awn Dialog if necessary
    self.dialog.hide()
  
  #Attached:
  #  Displayed: Hide
  #  Otherwide: Show
  #Detached:
  #  Not displayed: Show
  #  Displayed: This won't be called
  def toggle_dialog(self,*args):
    if self.detached==False and self.displayed==True:
      self.hide_dialog()
    
    elif (self.detached==True and self.displayed==False) or\
      self.detached==False:
      #Make the dialog
      self.make_dialog()
      
      #Deal with the dialog as appropriate
      if self.detached==False:
        self.dialog.show_all()
        if self.settings['title']!='To-Do List':
          self.dialog.set_title(self.settings['title'])
      else:
        self.dialog_widget.show_all()
      
      #Fix the first item selected bug (?)
      try:
        self.dialog_widgets[0][1].select_region(1,2)
        self.dialog_widgets[0][1].set_position(0)
      except:
        pass
      
      #Give the Add button focus
      self.dialog_add.grab_focus()
      self.displayed = True
  
  #Show the dialog - detached only
  def show_dialog(self,*args):
    if self.detached==True and self.detach['displayed']==False:
      self.make_dialog()
      self.dialog_widget.show_all()
  
  #Make the dialog - don't show it
  def make_dialog(self,*args):
    #Remove any previous dialog widgets
    self.clear_dialog()
    
    self.dialog_widgets = []
    
    
    #Make the main table
    dialog_table = gtk.Table(1,1)
    
    #Go through the list of to-do items
    y = 0
    for x in self.settings['items']:
      if x!='':
        #This is a normal item
        #Make an "X" button to clear the item
        dialog_x = gtk.Button()
        dialog_x_icon = gtk.image_new_from_pixbuf(\
          self.icon_theme.load_icon('gtk-cancel',16,16))
        dialog_x.set_image(dialog_x_icon)
        dialog_x.set_relief(gtk.RELIEF_NONE)
        dialog_x.iterator = y
        dialog_x.connect('clicked',self.remove_item_from_list)
        
        #Make an entry widget for the item
        dialog_entry = gtk.Entry()
        dialog_entry.set_text(x)
        dialog_entry.iterator = y
        dialog_entry.type = 'items'
        dialog_entry.connect('focus-out-event',self.item_updated)
        
        #Try to colorize the entry widget based on its priority
        try:
          #High: Red
          if self.settings['priority'][y]==3:
            dialog_entry.modify_base(\
              gtk.STATE_NORMAL,gtk.gdk.color_parse('#aa0000'))
            dialog_entry.modify_text(\
              gtk.STATE_NORMAL,gtk.gdk.color_parse('#dddddd'))
            dialog_entry.modify_bg(\
              gtk.STATE_SELECTED,gtk.gdk.color_parse('#ffbbbb'))
          #Medium: Yellow
          elif self.settings['priority'][y]==2:
            dialog_entry.modify_base(\
              gtk.STATE_NORMAL,gtk.gdk.color_parse('#c0c000'))
            dialog_entry.modify_text(\
              gtk.STATE_NORMAL,gtk.gdk.color_parse('#000000'))
            dialog_entry.modify_bg(\
              gtk.STATE_SELECTED,gtk.gdk.color_parse('#ffff88'))
          #Low: Green
          elif self.settings['priority'][y]==1:
            dialog_entry.modify_base(\
              gtk.STATE_NORMAL,gtk.gdk.color_parse('#009900'))
            dialog_entry.modify_text(\
              gtk.STATE_NORMAL,gtk.gdk.color_parse('#000000'))
            dialog_entry.modify_bg(\
              gtk.STATE_SELECTED,gtk.gdk.color_parse('#88ff88'))
        
        except:
          pass
        
        #Make a right arrow button to edit/add details about the item
        dialog_details = gtk.Button()
        dialog_details_icon = gtk.image_new_from_pixbuf(\
          self.icon_theme.load_icon('go-next',16,16))
        dialog_details.set_image(dialog_details_icon)
        dialog_details.set_relief(gtk.RELIEF_NONE)
        dialog_details.iterator = y
        dialog_details.connect('clicked',self.edit_details)
        
        #Put the widgets in the table
        if self.settings['category'][y]!=-1:
          dialog_table.attach(dialog_x,0,1,y,(y+1),\
            xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
          dialog_table.attach(dialog_entry,2,3,y,(y+1),\
            yoptions=gtk.SHRINK)
          dialog_table.attach(dialog_details,3,4,y,(y+1),\
            xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        else:
          dialog_table.attach(dialog_x,0,1,y,(y+1),\
            xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
          dialog_table.attach(dialog_entry,1,3,y,(y+1),\
            yoptions=gtk.SHRINK)
          dialog_table.attach(dialog_details,3,4,y,(y+1),\
            xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        
        
        #Put the widgets in a list of widgets - used for expanding categories
        self.dialog_widgets.append([dialog_x,dialog_entry,dialog_details])
        
        #If this item is in a category - don't show it automatically (show_all)
        if self.settings['category'][y] not in [-1]+self.settings['expanded']:
          dialog_x.set_no_show_all(True)
          dialog_entry.set_no_show_all(True)
          dialog_details.set_no_show_all(True)
        
        y+=1
      
      #This is a category - show an Expander widget
      else:
        #Make a normal X button
        dialog_x = gtk.Button()
        dialog_x_icon = gtk.image_new_from_pixbuf(\
          self.icon_theme.load_icon('gtk-cancel',16,16))
        dialog_x.set_image(dialog_x_icon)
        dialog_x.set_relief(gtk.RELIEF_NONE)
        dialog_x.iterator = y
        dialog_x.connect('clicked',self.remove_item_from_list)
        
        #Make the Expander widget
        dialog_expander = gtk.Expander(self.settings['category_name'][y])
        dialog_expander.iterator = y
        if y in self.settings['expanded']:
          dialog_expander.set_expanded(True)
        dialog_expander.connect('notify::expanded',self.expanded)
        
        #Make a normal -> button - but different function
        #for the category
        dialog_details = gtk.Button()
        dialog_details_icon = gtk.image_new_from_pixbuf(\
          self.icon_theme.load_icon('go-next',16,16))
        dialog_details.set_image(dialog_details_icon)
        dialog_details.set_relief(gtk.RELIEF_NONE)
        dialog_details.iterator = y
        dialog_details.connect('clicked',self.category_details)
        
        #Now figure out how many items are in this category
        num_items = 0
        for x in self.settings['category']:
          if x == y:
            num_items += 1
        
        #Now make a vertical separator and add it to the dialog
        dialog_vsep = gtk.VSeparator()
        if y not in self.settings['expanded']:
          dialog_vsep.set_no_show_all(True)
        
        #Put the widgets in the table
        dialog_table.attach(dialog_x,0,1,y,(y+1),\
          xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        dialog_table.attach(dialog_expander,1,3,y,(y+1),\
          yoptions=gtk.SHRINK)
        dialog_table.attach(dialog_details,3,4,y,(y+1),\
          xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
        if num_items > 0:
          dialog_table.attach(dialog_vsep,1,2,y+1,(y+1+num_items),\
            xoptions=gtk.SHRINK,xpadding=7)
        
        #Put the widgets in a list of widgets - used for expanding categories
        self.dialog_widgets.append([dialog_x,dialog_expander,dialog_details,\
          dialog_vsep])
        
        y+=1
    
    #Make a button to display a dialog to add an item
    self.dialog_add = gtk.Button(stock=gtk.STOCK_ADD)
    self.dialog_add.connect('clicked',self.add_item)
    
    if len(self.settings['items'])==0:
      #If # items is 0, make the button take up all the width
      dialog_table.attach(self.dialog_add,0,4,y,(y+1),\
        yoptions=gtk.SHRINK)
    
    else:
      #Otherwise, just add it normally; center aligned
      dialog_table.attach(self.dialog_add,0,4,y,(y+1),\
        xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
    
    #Put the table in the dialog
    dialog_table.show_all()
    self.add_to_dialog(dialog_table)
  
  #Called when an item has been edited by the default dialog
  #(or the edit details dialog)
  def item_updated(self,widget,event):
    if widget.get_text()!='':
      tmp_list_names = []
      y = 0
      for x in self.settings[widget.type]:
        if y!=widget.iterator:
          tmp_list_names.append(x)
        else:
          tmp_list_names.append(widget.get_text())
        y+=1
      self.settings[widget.type] = tmp_list_names
  
  #An Expander widget was expanded or un-expanded
  def expanded(self,widget,expanded):
    
    #Show the category's widgets
    if widget.get_property('expanded'):
      #Show the separator
      self.dialog_widgets[widget.iterator][3].show()
      
      #Find the items that are in this category
      y = 0
      for x in self.settings['category']:
        if x == widget.iterator:
          for x in self.dialog_widgets[y]:
            x.show()
        y+=1
      
      tmp_list_expanded = []
      for x in self.settings['expanded']:
        tmp_list_expanded.append(x)
      tmp_list_expanded.append(widget.iterator)
      self.settings['expanded'] = tmp_list_expanded
    
    #Hide the category's widgets
    else:
      #Hide the separator
      self.dialog_widgets[widget.iterator][3].hide()
      
      #Find the items tat are in this category
      y = 0
      for x in self.settings['category']:
        if x == widget.iterator:
          for x in self.dialog_widgets[y]:
            x.hide()
        y+=1
      
      tmp_list_expanded = []
      for x in self.settings['expanded']:
        tmp_list_expanded.append(x)
      tmp_list_expanded.remove(widget.iterator)
      self.settings['expanded'] = tmp_list_expanded
  
  #Display dialog to add an item to the To-Do list
  def add_item(self,*args):
    #Clear the dialog
    self.clear_dialog()
    
    self.add_category = -1
    self.add_mode = 'to-do'
    
    #Make the main widget - VBox
    self.add_vbox = gtk.VBox()
    
    #Make the RadioButtons for each category
    #First category: No category! (Uncategorized)
    uncategorized = gtk.RadioButton(label='_Uncategorized')
    uncategorized.id = -1
    uncategorized.connect('toggled',self.add_radio_changed)
    self.add_vbox.pack_start(uncategorized,False)
    
    #Now through each category
    y = 0#For each item OR category
    for x in self.settings['category_name']:
      if x!='':
        category = gtk.RadioButton(uncategorized,x)
        category.id = y
        category.connect('toggled',self.add_radio_changed)
        self.add_vbox.pack_start(category,False)
      y+=1
    
    #Simple horizontal separator
    add_hsep = gtk.HSeparator()
    self.add_vbox.pack_start(add_hsep,False,False,3)
    
    #HBox for the two RadioButtons - ( )Category (-)To-Do item
    radio_hbox = gtk.HBox()
    self.add_vbox.pack_start(radio_hbox,False)
    
    #First RadioButton - ( )Category
    category_radio = gtk.RadioButton(label='_Category')
    category_radio.id = 'category'
    category_radio.connect('toggled',self.add_radio_changed)
    radio_hbox.pack_start(category_radio,False)
    
    #Second RadioButton - (-)To-Do item
    #TODO: better text than "To-Do item"?
    item_radio = gtk.RadioButton(category_radio,'_To-Do item')
    item_radio.set_active(True)
    item_radio.id = 'to-do'
    item_radio.connect('toggled',self.add_radio_changed)
    radio_hbox.pack_end(item_radio,False)
    
    #HBox for the entry and button widgets
    add_hbox = gtk.HBox()
    self.add_vbox.pack_start(add_hbox,False)
    
    #Entry for the name
    self.add_entry = gtk.Entry()
    self.add_entry.connect('key-press-event',self.key_press_event,\
      self.add_item_to_list)
    add_hbox.pack_start(self.add_entry)
    
    #OK Button
    add_button = gtk.Button(stock=gtk.STOCK_OK)
    add_button.connect('clicked',self.add_item_to_list)
    add_hbox.pack_start(add_button,False)
    
    #Put it all together
    self.add_vbox.show_all()
    self.add_to_dialog(self.add_vbox)
    self.add_entry.grab_focus()
  
  #When a RadioButton is toggled
  #Either a category radio OR the "Category" or "To-Do item" radios
  def add_radio_changed(self,button):
    if button.get_active()==True:
      #New item will be a category
      if button.id == 'category':
        self.add_mode = 'category'
        for x in self.add_vbox.get_children()[:-2]:
          x.hide()
      #New item will be a normal to-do item
      elif button.id == 'to-do':
        self.add_mode = 'to-do'
        for x in self.add_vbox.get_children()[:-2]:
          x.show()
      #A specific category was selected
      else:
        self.add_category = button.id
  
  #When a key is pressed on a connected entry widget
  #checks for enter key pressed and calls a passed function
  #if the enter key is pressed
  def key_press_event(self,widget,event,func,*args):
    if event.keyval in [65293,65421] or event.hardware_keycode in [36,108]:
      func(*args)
  
  #Edit the details of an item
  def edit_details(self,num):
    if type(num)==gtk.Button:
      num = num.iterator
    
    #Get data
    name = self.settings['items'][num]
    priority = self.settings['priority'][num]
    progress = self.settings['progress'][num]
    details = self.settings['details'][num]
    
    #Main widget
    widget = gtk.VBox()
    
    #Name Entry
    name_entry = gtk.Entry()
    name_entry.set_text(name)
    name_entry.iterator = num
    name_entry.type = 'items'
    name_entry.connect('focus-out-event',self.item_updated)
    
    #HBoxes for Priority Label and RadioButtons
    priority_hbox0 = gtk.HBox()
    priority_hbox1 = gtk.HBox()
    
    #Label: Priority: 
    priority_label = gtk.Label('Priority: ')
    
    #Neutral, Low, Medium, and High priority RadioButtons
    priority_neutral = gtk.RadioButton(label='_Neutral')
    priority_neutral.id = [0,num]
    priority_low = gtk.RadioButton(priority_neutral,'_Low')
    priority_low.id = [1,num]
    priority_med = gtk.RadioButton(priority_neutral,'_Medium')
    priority_med.id = [2,num]
    priority_high = gtk.RadioButton(priority_neutral,'_High')
    priority_high.id = [3,num]
    
    #Select the right RadioButton (Neutral is selected by default)
    if priority==1:
      priority_low.set_active(True)
    elif priority==2:
      priority_med.set_active(True)
    elif priority==3:
      priority_high.set_active(True)
    
    #Connect the radio buttons to the radio_selected function
    priority_neutral.connect('toggled',self.radio_selected)
    priority_low.connect('toggled',self.radio_selected)
    priority_med.connect('toggled',self.radio_selected)
    priority_high.connect('toggled',self.radio_selected)
    
    #Pack the widgets to the HBoxes
    priority_hbox0.pack_start(priority_label)
    priority_hbox0.pack_start(priority_neutral,False)
    priority_hbox1.pack_start(priority_low,True,False)
    priority_hbox1.pack_start(priority_med,True,False)
    priority_hbox1.pack_start(priority_high,True,False)
    
    #HBox for Progress label and SpinButton
    progress_hbox = gtk.HBox()
    
    #Label: Progress(%): 
    progress_label = gtk.Label('Progress(%): ')
    
    #SpinButton and Adjustment for the SpinButton
    progress_adj = gtk.Adjustment(float(progress),0,100,5,10,1)
    progress_spin = gtk.SpinButton(progress_adj,1,0)
    progress_spin.iterator = num
    progress_spin.connect('focus-out-event',self.spin_focusout)
    
    #Pack the widgets to the HBox
    progress_hbox.pack_start(progress_label,False)
    progress_hbox.pack_start(progress_spin)
    
    #Make a TextView to edit the details of the the item
    details_scrolled = gtk.ScrolledWindow()
    details_scrolled.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    details_textbuffer = gtk.TextBuffer()
    details_textbuffer.set_text(details)
    details_textview = gtk.TextView(details_textbuffer)
    details_textview.set_wrap_mode(gtk.WRAP_WORD)
    details_textview.iterator = num
    details_textview.connect('focus-out-event',self.textview_focusout)
    details_scrolled.add_with_viewport(details_textview)
    details_scrolled.set_size_request(0,100)
    
    #Simple "OK" button - display the main dialog
    ok_button = gtk.Button(stock=gtk.STOCK_OK)
    ok_button.connect('clicked',self.make_dialog)
    
    #Pack the widgets to the main VBox
    widget.pack_start(name_entry,False)
    widget.pack_start(priority_hbox0,False)
    widget.pack_start(priority_hbox1,False)
    widget.pack_start(progress_hbox,False)
    widget.pack_start(details_scrolled,True,True,3)
    widget.pack_start(ok_button,False)
    
    #Put everything together
    widget.show_all()
    self.clear_dialog()
    self.add_to_dialog(widget)
    ok_button.grab_focus()
  
  #When a RadioButton from the edit details dialog has been selected
  def radio_selected(self,widget):
    if widget.get_active()==True:
      tmp_list_priority = []
      y = 0
      for x in self.settings['priority']:
        if y==widget.id[1]:
          tmp_list_priority.append(widget.id[0])
        else:
          tmp_list_priority.append(x)
        y+=1
      self.settings['priority'] = tmp_list_priority
  
  #When the SpinButton for progress has lost focus
  def spin_focusout(self,widget,event):
    tmp_list_progress = []
    y = 0
    for x in self.settings['progress']:
      if y==widget.iterator:
        tmp_list_progress.append(widget.get_value())
      else:
        tmp_list_progress.append(x)
      y+=1
    self.settings['progress'] = tmp_list_progress
  
  #When the TextView for details has lost focus
  def textview_focusout(self,widget,event):
    tmp_list_details = []
    y = 0
    for x in self.settings['details']:
      if y==widget.iterator:
        tmp_list_details.append(widget.get_buffer().get_text(\
          widget.get_buffer().get_start_iter(),\
          widget.get_buffer().get_end_iter(),False))
      else:
        tmp_list_details.append(x)
      y+=1
    self.settings['details'] = tmp_list_details
  
  #Edit the details of a category
  def category_details(self,catid):
    if type(catid) != int:#Could be GtkButton
      catid = catid.iterator
    
    #Get data
    name = self.settings['category_name'][catid]
    details = self.settings['details'][catid]
    
    #Main widget
    widget = gtk.VBox()
    
    #Name Entry
    name_entry = gtk.Entry()
    name_entry.set_text(name)
    name_entry.iterator = catid
    name_entry.type = 'category_name'
    name_entry.connect('focus-out-event',self.item_updated)
    
    #Make a TextView to edit the details of the the item
    details_scrolled = gtk.ScrolledWindow()
    details_scrolled.set_policy(gtk.POLICY_AUTOMATIC,gtk.POLICY_AUTOMATIC)
    details_textbuffer = gtk.TextBuffer()
    details_textbuffer.set_text(details)
    details_textview = gtk.TextView(details_textbuffer)
    details_textview.set_wrap_mode(gtk.WRAP_WORD)
    details_textview.iterator = catid
    details_textview.connect('focus-out-event',self.textview_focusout)
    details_scrolled.add_with_viewport(details_textview)
    details_scrolled.set_size_request(0,100)
    
    #Simple "OK" button - displays the main dialog
    ok_button = gtk.Button(stock=gtk.STOCK_OK)
    ok_button.connect('clicked',self.make_dialog)
    
    #Pack the widgets to the main VBox
    widget.pack_start(name_entry,False)
    widget.pack_start(details_scrolled,True,True,3)
    widget.pack_start(ok_button,False)
    
    #Put everything together
    widget.show_all()
    self.clear_dialog()
    self.add_to_dialog(widget)
    ok_button.grab_focus()
  
  #Called when the list of items has been changed - change the icon
  def update_icon(self,*args):
    if self.last_num_items!=len(self.settings['items']) or\
      self.settings['icon-type'] in ['progress','progress-items']:
      
      #Change the detached icon first
      try:
        assert len(self.settings['items']) == 0
        self.detach['icon-mode'] = 'pixbuf'
        self.detach.set_pixbuf(self.icon_theme.load_icon(\
          'view-sort-descending',self.height,self.height))
      except:
        self.detach['icon-mode'] = 'surface'
        self.detach.set_surface(icon.icon(self.height,self.settings,\
          self.color))
      
      #Change the attached applet icon second
      if self.detached == False:
        self.show_all()
      
      try:
        assert len(self.settings['items']) == 0
        self.set_icon(self.icon_theme.load_icon(\
          'view-sort-descending',self.height,self.height))
      except:
        
        #If Awn supports setting the icon as a cairo context
        if hasattr(self, 'set_icon_context'):
          surface = icon.icon(self.height, self.settings, self.color)
          self.context = cairo.Context(surface)
          self.set_icon_context(self.context)
        
        #It doesn't; use surface->pixbuf via detach
        else:
          surface = icon.icon(self.height, self.settings, self.color)
          if self.pixbuf is None:
            self.pixbuf = self.detach.surface_to_pixbuf(surface)
          else:
            self.detach.surface_to_pixbuf(surface, self.pixbuf)
          self.set_icon(self.pixbuf)
      
      self.last_num_items = len(self.settings['items'])
  
  #Update the colors for the icon if the current icon theme
  #if the current GTK theme ('gtk')
  #Does NOT update the icon
  def update_icon_theme(self):
    if self.settings['color'] == 'gtk':
      #Get the colors from a temporary window
      self.color = [None,None,None,None]
      tmp_window = gtk.Window()
      tmp_window.realize()
      
      #Outer and inner borders - rgb
      tmp_innerborder = tmp_window.get_style().bg[gtk.STATE_SELECTED]
      self.color[2] = [tmp_innerborder.red/256.0,\
        tmp_innerborder.green/256.0,tmp_innerborder.blue/256.0]
      self.color[0] = [tmp_innerborder.red/256.0,\
        tmp_innerborder.green/256.0,tmp_innerborder.blue/256.0]
      
      #Main color - rgb
      tmp_maincolor = tmp_window.get_style().bg[gtk.STATE_NORMAL]
      self.color[1] = [tmp_maincolor.red/256.0,\
        tmp_maincolor.green/256.0,tmp_maincolor.blue/256.0]
      
      #Text color - rgb
      tmp_textcolor = tmp_window.get_style().text[gtk.STATE_PRELIGHT]
      self.color[3] = [tmp_textcolor.red/256.0,\
        tmp_textcolor.green/256.0,tmp_textcolor.blue/256.0]
      
      #Save some memory (is this necessary?)
      tmp_window.destroy()
  
  #Change the opacity of the icon by 5%
  def opacity(self,event,more):
    old_opacity = self.settings['icon-opacity']
    new_opacity = False
    
    #Increase opacity
    if more:
      
      #Make sure it won't go too far
      if old_opacity + 5 >= 100:
        new_opacity = 100
      #Increase by 5%
      else:
        new_opacity = old_opacity + 5
    
    #Decrease opacity
    else:
      
      #Make sure it won't go too far
      if old_opacity - 5 <= 10:
        new_opacity = 10
      #Decrease by 5%
      else:
        new_opacity = old_opacity - 5
    
    #Update the icon if necessary
    if old_opacity != new_opacity:
      self.settings['icon-opacity'] = new_opacity
      self.last_num_items = -1
      self.update_icon()
  
  #Actually add the item to the list of items
  def add_item_to_list(self,*args):
    #Make sure that the item name is not empty
    if self.add_entry.get_text().replace(' ','')!='':
      #Find out what to do based on category things
      if self.add_mode == 'to-do':
        if self.add_category == -1:
          #Just append
          tmp_list_names = []
          tmp_list_priority = []
          tmp_list_progress = []
          tmp_list_details = []
          tmp_list_category = []
          tmp_list_category_name = []
          for x in self.settings['items']:
            tmp_list_names.append(x)
          for x in self.settings['priority']:
            tmp_list_priority.append(x)
          for x in self.settings['progress']:
            tmp_list_progress.append(x)
          for x in self.settings['details']:
            tmp_list_details.append(x)
          for x in self.settings['category']:
            tmp_list_category.append(x)
          for x in self.settings['category_name']:
            tmp_list_category_name.append(x)
          
          
          tmp_list_names.append(self.add_entry.get_text())
          tmp_list_priority.append(0)
          tmp_list_progress.append(0)
          tmp_list_details.append('')
          tmp_list_category.append(-1)
          tmp_list_category_name.append('')
          
          self.settings['items'] = tmp_list_names
          self.settings['priority'] = tmp_list_priority
          self.settings['progress'] = tmp_list_progress
          self.settings['details'] = tmp_list_details
          self.settings['category'] = tmp_list_category
          self.settings['category_name'] = tmp_list_category_name
          
          #Re-show the main dialog
          self.displayed = False#Is this necessary?
          self.clear_dialog()
          self.edit_details(len(tmp_list_names)-1)
        
        #A category was selected; add this item to the end of that category!
        else:
          #Find where to put the new item
          z = -1
          y = 0
          for x in self.settings['category']:
            if x == self.add_category:
              z = y
            y += 1
          
          if z==-1:
            #This means that there are no items in the category
            z = self.add_category
          
          tmp_list_names = []
          tmp_list_priority = []
          tmp_list_progress = []
          tmp_list_details = []
          tmp_list_category = []
          tmp_list_category_name = []
          
          y = 0
          for x in self.settings['items']:
            tmp_list_names.append(x)
            if y == z:
              tmp_list_names.append(self.add_entry.get_text())
            y+=1
          
          y = 0
          for x in self.settings['priority']:
            tmp_list_priority.append(x)
            if y == z:
              tmp_list_priority.append(0)
            y+=1
          
          y = 0
          for x in self.settings['progress']:
            tmp_list_progress.append(x)
            if y == z:
              tmp_list_progress.append(0)
            y+=1
          
          y = 0
          for x in self.settings['details']:
            tmp_list_details.append(x)
            if y == z:
              tmp_list_details.append('')
            y+=1
          
          y = 0
          for x in self.settings['category']:
            if y == z:
              tmp_list_category.append(self.add_category)
            elif y > z and x != -1:
              tmp_list_category.append(x+1)
            else:
              tmp_list_category.append(x)
            y+=1
          
          y = 0
          for x in self.settings['category_name']:
            tmp_list_category_name.append(x)
            if y == z:
              tmp_list_category_name.append('')
            y+=1
          
          self.settings['items'] = tmp_list_names
          self.settings['priority'] = tmp_list_priority
          self.settings['progress'] = tmp_list_progress
          self.settings['details'] = tmp_list_details
          self.settings['category'] = tmp_list_category
          self.settings['category_name'] = tmp_list_category_name
          
          #Re-show the main dialog
          self.displayed = False#TODO:Is this necessary?
          self.clear_dialog()
          self.edit_details(z+1)
      
      #The new item is a category
      else:
        #Append to the list
        tmp_list_names = []
        tmp_list_priority = []
        tmp_list_progress = []
        tmp_list_details = []
        tmp_list_category = []
        tmp_list_category_name = []
        for x in self.settings['items']:
          tmp_list_names.append(x)
        for x in self.settings['priority']:
          tmp_list_priority.append(x)
        for x in self.settings['progress']:
          tmp_list_progress.append(x)
        for x in self.settings['details']:
          tmp_list_details.append(x)
        for x in self.settings['category']:
          tmp_list_category.append(x)
        for x in self.settings['category_name']:
          tmp_list_category_name.append(x)
        
        
        tmp_list_names.append('')
        tmp_list_priority.append(0)
        tmp_list_progress.append(0)
        tmp_list_details.append('')
        tmp_list_category.append(-1)
        tmp_list_category_name.append(self.add_entry.get_text())
        
        self.settings['items'] = tmp_list_names
        self.settings['priority'] = tmp_list_priority
        self.settings['progress'] = tmp_list_progress
        self.settings['details'] = tmp_list_details
        self.settings['category'] = tmp_list_category
        self.settings['category_name'] = tmp_list_category_name
        
        #Re-show the main dialog
        self.displayed = False#TODO:Is this necessary?
        self.clear_dialog()
        self.category_details(len(tmp_list_names)-1)
    
    #The item name is empty; display the main dialog
    else:
      self.displayed = False
      self.toggle_dialog()
  
  #Remove an item from the list of items
  def remove_item_from_list(self,itemid):
    
    if type(itemid)!=int:
      itemid = itemid.iterator
    
    #List of items in this category
    list_of_items = [itemid]
    
    #If this is a category and it has items in it,
    #remove its items first
    if self.settings['items'][itemid]=='':#Means it's a category
      
      #Remove this category's items
      y = 0
      for x in self.settings['category']:
        if x == itemid:
          list_of_items.append(y)
        y+=1
      
      #Remove this category from the list of expanded categories
      if itemid in self.settings['expanded']:
        tmp_list_expanded = self.settings['expanded']
        tmp_list_expanded.remove(itemid)
        self.settings['expanded'] = tmp_list_expanded
    
    tmp_list_names = []
    tmp_list_priority = []
    tmp_list_progress = []
    tmp_list_details = []
    tmp_list_category = []
    tmp_list_category_name = []
    
    y = 0
    for x in self.settings['items']:
      if y not in list_of_items:
        tmp_list_names.append(x)
      y+=1
    
    y = 0
    for x in self.settings['priority']:
      if y not in list_of_items:
        tmp_list_priority.append(x)
      y+=1
    
    y = 0
    for x in self.settings['progress']:
      if y not in list_of_items:
        tmp_list_progress.append(x)
      y+=1
    
    y = 0
    for x in self.settings['details']:
      if y not in list_of_items:
        tmp_list_details.append(x)
      y+=1
    
    y = 0
    for x in self.settings['category']:
      if y not in list_of_items:
        if y > list_of_items[-1] and y != -1:
          tmp_list_category.append(x-1)
        else:
          tmp_list_category.append(x)
      y+=1
    
    y = 0
    for x in self.settings['category_name']:
      if y not in list_of_items:
        tmp_list_category_name.append(x)
      y+=1
    
    self.settings['items'] = tmp_list_names
    self.settings['priority'] = tmp_list_priority
    self.settings['progress'] = tmp_list_progress
    self.settings['details'] = tmp_list_details
    self.settings['category'] = tmp_list_category
    self.settings['category_name'] = tmp_list_category_name
    
    #The icon is automatically changed, but the dialog is not
    self.displayed = False
    self.toggle_dialog()
    

if __name__ == '__main__':
  awn.init(sys.argv[1:])
  applet = App(awn.uid,awn.orient,awn.height)
  awn.init_applet(applet)
  applet.show_all()
  gtk.main()
