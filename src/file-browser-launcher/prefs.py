#! /usr/bin/env python
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
#File Browser Launcher
#Preferences file

import pygtk
pygtk.require('2.0')
import gtk
import pango
import os
import gconfwrapper as awnccwrapper

class Prefs:
  def __init__(self,set_icon,uid):
    self.uid = uid
    
    #Initiate what is needed
    self.window = gtk.Window()
    self.window.set_title('File Browser Launcher Preferences')
    self.set_icon = set_icon
    self.nbook = gtk.Notebook()
    self.theme = gtk.icon_theme_get_default()
    self.initializing = True
    
    #Get default icon path (not awncc)
    self.default_icon_path = '/'.join(__file__.split('/')[:-1])+'/folder.png'
    
    #Get ALL the awncc stuff
    self.client = awnccwrapper.AwnCCWrapper(self.uid)
    
    #File browser
    self.fb = self.client.get_string('fb','xdg-open')
    
    #Left mouse button action
    self.lmb = self.client.get_int('lmb',1)
    
    #Left mouse button path
    self.lmb_path = self.client.get_string('lmb_path',\
    os.path.expanduser('~'))
    
    #Middle mouse button action
    self.mmb = self.client.get_int('mmb',2)
    
    #Middle mouse button path
    self.mmb_path = self.client.get_string('mmb_path',\
    os.path.expanduser('~'))
    
    #Icon path or default
    self.icon = self.client.get_string('icon',\
    '/dev/null')
    
    #Places: show bookmarks, home, local, network
    self.show_bookmarks = self.client.get_int('places_bookmarks',2)
    self.show_home = self.client.get_int('places_home',2)
    self.show_local = self.client.get_int('places_local',2)
    self.show_network = self.client.get_int('places_network',2)
    
    #Open the places item when clicked
    self.places_open = self.client.get_int('places_open',2)
    
    #Focus the location entry widget
    self.focus_entry = self.client.get_int('focus_entry',2)
    
    #Set the icon approiately
    if self.icon=='/dev/null':
      self.awn_new_icon = self.theme.load_icon('folder',48,48)
      self.window.set_icon(self.awn_new_icon)
    elif os.path.exists(self.icon):
      self.awn_new_icon = gtk.gdk.pixbuf_new_from_file(self.icon)
      self.window.set_icon(self.awn_new_icon)
      self.awn_new_icon = self.awn_new_icon.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
    else:
      self.awn_new_icon = self.theme.load_icon('folder',48,48)
      self.window.set_icon(self.awn_new_icon)
    
    #Make the "General" tab
    self.general_tab = gtk.Label('General')
    self.general_vbox = gtk.VBox()
    
    #Bold text: "Icon" with HSeparator under it
    self.general_icon_label = gtk.Label('Icon')
    self.general_icon_label.modify_font(pango.FontDescription('bold'))
    self.general_separator0 = gtk.HSeparator()
    
    #Table for selecting which icon to use: default or custom(by path)
    self.general_icon_table = gtk.Table(3,2)
    
    #First row: default icon
    self.general_icon_default_radio = gtk.RadioButton()
    self.general_icon_default_radio.identifier = 'general.icon.default'
    self.general_icon_default_radio.connect('toggled',self.radio_changed)
    self.general_icon_default_img = gtk.image_new_from_file(self.default_icon_path)
    self.general_icon_default_label = gtk.Label('Default')
    if self.icon in ['default','','/dev/null']:
      self.general_icon_default_radio.set_active(True)
    
    #Second row: theme default icon
    self.general_icon_theme_radio = gtk.RadioButton(self.general_icon_default_radio)
    self.general_icon_theme_radio.identifier = 'general.icon.theme'
    self.general_icon_theme_radio.connect('toggled',self.radio_changed)
    self.general_icon_theme_pixbuf = self.theme.load_icon('folder',48,48)
    self.general_icon_theme_img = gtk.image_new_from_pixbuf(self.general_icon_theme_pixbuf)
    self.general_icon_theme_label = gtk.Label('Theme default')
    if self.icon=='theme':
      self.general_icon_theme_radio.set_active(True)
    
    #Attach the widgets to the table
    self.general_icon_table.attach(self.general_icon_default_radio,0,1,0,1,yoptions=gtk.SHRINK)
    self.general_icon_table.attach(self.general_icon_default_img,1,2,0,1,yoptions=gtk.SHRINK)
    self.general_icon_table.attach(self.general_icon_default_label,2,3,0,1,yoptions=gtk.SHRINK)
    self.general_icon_table.attach(self.general_icon_theme_radio,0,1,1,2,yoptions=gtk.SHRINK)
    self.general_icon_table.attach(self.general_icon_theme_img,1,2,1,2,yoptions=gtk.SHRINK)
    self.general_icon_table.attach(self.general_icon_theme_label,2,3,1,2,yoptions=gtk.SHRINK)
    
    #Third row: custom icon
    self.general_icon_custom_radio = gtk.RadioButton(self.general_icon_default_radio)
    self.general_icon_custom_radio.identifier = 'general.icon.custom'
    self.general_icon_custom_radio.connect('toggled',self.radio_changed)
    if self.icon not in ['/dev/null','','default','theme']:
      self.general_icon_custom_radio.set_active(True)
    if self.icon!='/dev/null' and os.path.exists(self.icon):
      self.general_icon_custom_pixbuf = gtk.gdk.pixbuf_new_from_file(self.icon)
      self.general_icon_custom_pixbuf = self.general_icon_custom_pixbuf.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
      self.general_icon_custom_img = gtk.image_new_from_pixbuf(self.general_icon_custom_pixbuf)
    else:
      self.general_icon_custom_img = gtk.image_new_from_pixbuf(None)
    
    #Fourth row: text box and browse button
    self.general_icon_custom_label = gtk.Label('Custom')
    self.general_icon_custom_entry = gtk.Entry()
    self.general_icon_custom_browse = gtk.Button(stock=gtk.STOCK_OPEN)
    self.general_icon_custom_browse.get_children()[0].get_children()[0].get_children()[1].set_text('Browse')
    self.general_icon_custom_browse.connect('clicked',lambda a: self.browse_file('Choose an icon'))
    if self.icon not in ['/dev/null','','default','theme'] and os.path.exists(self.icon):
      self.general_icon_custom_entry.set_text(self.icon)
    else:
      self.general_icon_custom_entry.set_sensitive(False)
      self.general_icon_custom_browse.set_sensitive(False)
    
    #Put the 3rd and 4th rows in the table
    self.general_icon_table.attach(self.general_icon_custom_radio,0,1,2,3,yoptions=gtk.SHRINK)
    try:
      self.general_icon_table.attach(self.general_icon_custom_img,1,2,2,3,yoptions=gtk.SHRINK)
    except:
      pass
    self.general_icon_table.attach(self.general_icon_custom_label,2,3,2,3,yoptions=gtk.SHRINK)
    self.general_icon_custom_hbox = gtk.HBox()
    self.general_icon_custom_hbox.pack_start(self.general_icon_custom_entry)
    self.general_icon_custom_hbox.pack_end(self.general_icon_custom_browse,False)
    self.general_icon_table.attach(self.general_icon_custom_hbox,0,3,3,4,yoptions=gtk.SHRINK)
    
    #Next section: File Browser
    #Bold text: File Browser with an HSeparator under it
    self.general_fb_label = gtk.Label('File Browser')
    self.general_fb_label.modify_font(pango.FontDescription('bold'))
    self.general_separator1 = gtk.HSeparator()
    
    #Make the table for the file browser selection
    self.general_fb_table = gtk.Table(2,2)
    
    #First row: () xdg-open (default)
    self.general_fb_default_radio = gtk.RadioButton()
    self.general_fb_default_radio.identifier = 'general.fb.default'
    self.general_fb_default_radio.connect('toggled',self.radio_changed)
    self.general_fb_default_label = gtk.Label('xdg-open (default)')
    self.general_fb_table.attach(self.general_fb_default_radio,0,1,0,1,yoptions=gtk.SHRINK)
    self.general_fb_table.attach(self.general_fb_default_label,1,2,0,1,yoptions=gtk.SHRINK)
    
    #Go through short list of common file managers, include them in a list just like nautilus
    self.general_fb_list = ['nautilus','thunar','konqueror','dolphin']
    self.general_fb_other_radios = []
    self.general_fb_other_labels = []
    self.general_fb_y = 0
    for self.general_fb_x in self.general_fb_list:
      if os.path.exists('/usr/bin/'+self.general_fb_x):
        self.general_fb_other_radios.append(gtk.RadioButton(self.general_fb_default_radio))
        self.general_fb_other_radios[self.general_fb_y].identifier = 'general.fb.%s' % self.general_fb_x
        self.general_fb_other_radios[self.general_fb_y].connect('toggled',self.radio_changed)
        if self.fb==self.general_fb_x:
          self.general_fb_other_radios[self.general_fb_y].set_active(True)
        self.general_fb_other_labels.append(gtk.Label(self.general_fb_x.capitalize()))
        self.general_fb_table.attach(self.general_fb_other_radios[self.general_fb_y],0,1,\
          (self.general_fb_y+1),(self.general_fb_y+2),yoptions=gtk.SHRINK)
        self.general_fb_table.attach(self.general_fb_other_labels[self.general_fb_y],1,2,\
          (self.general_fb_y+1),(self.general_fb_y+2),yoptions=gtk.SHRINK)
        self.general_fb_y = self.general_fb_y+1
    
    #Last option: custom with an entry for the app name
    self.general_fb_custom_radio = gtk.RadioButton(self.general_fb_default_radio)
    self.general_fb_custom_radio.identifier = 'general.fb.custom'
    self.general_fb_custom_radio.connect('toggled',self.radio_changed)
    self.general_fb_custom_label = gtk.Label('Custom')
    self.general_fb_custom_entry = gtk.Entry()
    if self.fb in ['xdg-open','nautilus','thunar','konqueror','dolphin']:
      self.general_fb_custom_entry.set_sensitive(False)
    else:
      self.general_fb_custom_radio.set_active(True)
    self.general_fb_custom_entry.set_text(self.fb)
    self.general_fb_custom_entry.connect('changed',\
    lambda w:self.client.set_string('fb',w.get_text()))
    if self.fb in ['xdg-open','nautilus','thunar','konqueror','dolphin']:
      self.general_fb_custom_entry.set_sensitive(False)
    self.general_fb_table.attach(self.general_fb_custom_radio,0,1,\
    (self.general_fb_y+1),(self.general_fb_y+2),yoptions=gtk.SHRINK)
    self.general_fb_table.attach(self.general_fb_custom_label,1,2,\
    (self.general_fb_y+1),(self.general_fb_y+2),yoptions=gtk.SHRINK)
    self.general_fb_table.attach(self.general_fb_custom_entry,0,2,\
    (self.general_fb_y+2),(self.general_fb_y+3),yoptions=gtk.SHRINK)
    
    #Put ALL of the general tab together
    self.general_vbox.pack_start(self.general_icon_label)
    self.general_vbox.pack_start(self.general_separator0)
    self.general_vbox.pack_start(self.general_icon_table)
    self.general_vbox.pack_start(self.general_fb_label)
    self.general_vbox.pack_start(self.general_separator1)
    self.general_vbox.pack_start(self.general_fb_table)
    self.general_vbox.show_all()
    self.nbook.append_page(self.general_vbox,self.general_tab)
    
    #Dialog tab: options for places and basic behavior
    self.dialog_tab = gtk.Label('Dialog')
    self.dialog_vbox = gtk.VBox()
    
    #Bold text: Places with an hseparator under it
    self.dialog_places_label = gtk.Label('Places')
    self.dialog_places_label.modify_font(pango.FontDescription('bold'))
    self.dialog_separator0 = gtk.HSeparator()
    
    #VBox for the check buttons
    self.dialog_places_vbox = gtk.VBox()
    
    #Home Folder
    self.dialog_places_home = gtk.CheckButton('Show Home Folder')
    self.dialog_places_home.identifier = 'dialog.places.home'
    self.dialog_places_home.connect('toggled',self.check_changed)
    if self.show_home==2:
      self.dialog_places_home.set_active(True)
    
    #Mounted local drives
    self.dialog_places_local = gtk.CheckButton('Show mounted local drives')
    self.dialog_places_local.identifier = 'dialog.places.local'
    self.dialog_places_local.connect('toggled',self.check_changed)
    if self.show_local==2:
      self.dialog_places_local.set_active(True)
    
    #Mounted network drives
    self.dialog_places_network = gtk.CheckButton('Show mounted network drives')
    self.dialog_places_network.identifier = 'dialog.places.network'
    self.dialog_places_network.connect('toggled',self.check_changed)
    if self.show_network==2:
      self.dialog_places_network.set_active(True)
    
    #Bookmarks
    self.dialog_places_bookmarks = gtk.CheckButton('Show Bookmarks')
    self.dialog_places_bookmarks.identifier = 'dialog.places.bookmarks'
    self.dialog_places_bookmarks.connect('toggled',self.check_changed)
    if self.show_bookmarks==2:
      self.dialog_places_bookmarks.set_active(True)
    
    #Put the places checkbuttons together
    self.dialog_places_vbox.pack_start(self.dialog_places_home)
    self.dialog_places_vbox.pack_start(self.dialog_places_local)
    self.dialog_places_vbox.pack_start(self.dialog_places_network)
    self.dialog_places_vbox.pack_start(self.dialog_places_bookmarks)
    
    #Bold text: Behavior with hseparator under it
    self.dialog_behavior_label = gtk.Label('Behavior')
    self.dialog_behavior_label.modify_font(pango.FontDescription('bold'))
    self.dialog_separator1 = gtk.HSeparator()
    
    #[] Focus the location text box
    self.dialog_behavior_focus = gtk.CheckButton('Focus the location text box')
    self.dialog_behavior_focus.identifier = 'dialog.behavior.focus'
    self.dialog_behavior_focus.connect('toggled',self.check_changed)
    if self.focus_entry==2:
      self.dialog_behavior_focus.set_active(True)
    
    #[] Open the selected place when clicked
    self.dialog_behavior_open = gtk.CheckButton('Open the selected place when clicked')
    self.dialog_behavior_open.identifier = 'dialog.behavior.open'
    self.dialog_behavior_open.connect('toggled',self.check_changed)
    if self.places_open==2:
      self.dialog_behavior_open.set_active(True)
    
    #Make a VBox for the focus location text box and open the selected place when clicked checkbuttons
    self.dialog_behavior_vbox = gtk.VBox()
    self.dialog_behavior_vbox.pack_start(self.dialog_behavior_focus)
    self.dialog_behavior_vbox.pack_start(self.dialog_behavior_open)
    
    #Put ALL of the dialog tab together
    self.dialog_vbox.pack_start(self.dialog_places_label,False,False,5)
    self.dialog_vbox.pack_start(self.dialog_separator0,False,False,5)
    self.dialog_vbox.pack_start(self.dialog_places_vbox,False,False,5)
    self.dialog_vbox.pack_start(self.dialog_behavior_label,False,False,5)
    self.dialog_vbox.pack_start(self.dialog_separator1,False,False,5)
    self.dialog_vbox.pack_start(self.dialog_behavior_vbox,False,False,5)
    self.nbook.append_page(self.dialog_vbox,self.dialog_tab)
    
    #Left mouse button tab: two options: when clicked, do ... and the default folder (to display in entry widget or to launch)
    self.lmb_tab = gtk.Label('Left Mouse Button')
    self.lmb_vbox = gtk.VBox()
    
    #When clicked, (in bold with hseparator under it)
    self.lmb_clicked_label = gtk.Label('When clicked, ...')
    self.lmb_clicked_label.modify_font(pango.FontDescription('bold'))
    self.lmb_separator0 = gtk.HSeparator()
    
    #Table
    self.lmb_clicked_table = gtk.Table(3,2)
    
    #Row 1: () Display the dialog (default) (awncc:0)
    self.lmb_clicked_display_radio = gtk.RadioButton(label='Display the dialog')
    self.lmb_clicked_display_radio.identifier = 'lmb.clicked.display'
    self.lmb_clicked_display_radio.connect('toggled',self.radio_changed)
    self.lmb_clicked_table.attach(self.lmb_clicked_display_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Open the folder (awncc:1)
    self.lmb_clicked_open_radio = gtk.RadioButton(self.lmb_clicked_display_radio,'Open the folder')
    if self.lmb==2:
      self.lmb_clicked_open_radio.set_active(True)
    self.lmb_clicked_open_radio.identifier = 'lmb.clicked.open'
    self.lmb_clicked_open_radio.connect('toggled',self.radio_changed)
    self.lmb_clicked_open_label = gtk.Label('Open the folder')
    self.lmb_clicked_table.attach(self.lmb_clicked_open_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: () Do nothing (awncc:2)
    self.lmb_clicked_nothing_radio = gtk.RadioButton(self.lmb_clicked_display_radio,'Do nothing')
    if self.lmb==3:
      self.lmb_clicked_nothing_radio.set_active(True)
    self.lmb_clicked_nothing_radio.identifier = 'lmb.clicked.nothing'
    self.lmb_clicked_nothing_radio.connect('toggled',self.radio_changed)
    self.lmb_clicked_table.attach(self.lmb_clicked_nothing_radio,0,1,2,3,yoptions=gtk.SHRINK)
    
    #Bold: Default Folder & separator under it
    self.lmb_folder_label = gtk.Label('Default Folder')
    self.lmb_folder_label.modify_font(pango.FontDescription('bold'))
    self.lmb_separator1 = gtk.HSeparator()
    
    #Table
    self.lmb_folder_table = gtk.Table(3,2)
    
    #Row 1: () Home Folder ($HOME, default)
    self.lmb_folder_default_radio = gtk.RadioButton(label='Home Folder (%s, default)' % os.path.expanduser('~'))
    self.lmb_folder_default_radio.identifier = 'lmb.folder.default'
    self.lmb_folder_default_radio.connect('toggled',self.radio_changed)
    self.lmb_folder_table.attach(self.lmb_folder_default_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Custom
    self.lmb_folder_custom_radio = gtk.RadioButton(self.lmb_folder_default_radio,'Custom')
    self.lmb_folder_custom_radio.identifier = 'lmb.folder.custom'
    self.lmb_folder_custom_radio.connect('toggled',self.radio_changed)
    self.lmb_folder_table.attach(self.lmb_folder_custom_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: _______________________[Browse]
    self.lmb_folder_custom_entry = gtk.Entry()
    self.lmb_folder_custom_browse = gtk.Button(stock=gtk.STOCK_OPEN)
    self.lmb_folder_custom_browse.get_children()[0].get_children()[0].get_children()[1].set_text('Browse')
    self.lmb_folder_custom_browse.connect('clicked',self.browse_dir_lmb)
    self.lmb_folder_custom_hbox = gtk.HBox()
    self.lmb_folder_custom_hbox.pack_start(self.lmb_folder_custom_entry)
    self.lmb_folder_custom_hbox.pack_end(self.lmb_folder_custom_browse,False)
    if self.lmb_path!=os.path.expanduser('~'):
      self.lmb_folder_custom_entry.set_text(self.lmb_path)
      self.lmb_folder_custom_radio.set_active(True)
    else:
      self.lmb_folder_custom_entry.set_sensitive(False)
      self.lmb_folder_custom_browse.set_sensitive(False)
    self.lmb_folder_table.attach(self.lmb_folder_custom_hbox,0,2,2,3,yoptions=gtk.SHRINK)
    
    #Now put ALL of the LMB Tab together
    self.lmb_vbox.pack_start(self.lmb_clicked_label,False,False,5)
    self.lmb_vbox.pack_start(self.lmb_separator0,False,False,5)
    self.lmb_vbox.pack_start(self.lmb_clicked_table,False,False,5)
    self.lmb_vbox.pack_start(self.lmb_folder_label,False,False,5)
    self.lmb_vbox.pack_start(self.lmb_separator1,False,False,5)
    self.lmb_vbox.pack_start(self.lmb_folder_table,False,False,5)
    self.nbook.append_page(self.lmb_vbox,self.lmb_tab)
    
    #Middle mouse button tab: two options: when clicked, do ... and the default folder (to display in entry widget or to launch)
    self.mmb_tab = gtk.Label('Middle Mouse Button')
    self.mmb_vbox = gtk.VBox()
    
    #When clicked, (in bold with hseparator under it)
    self.mmb_clicked_label = gtk.Label('When clicked, ...')
    self.mmb_clicked_label.modify_font(pango.FontDescription('bold'))
    self.mmb_separator0 = gtk.HSeparator()
    
    #Table
    self.mmb_clicked_table = gtk.Table(3,2)
    
    #Row 1: () Display the dialog (default) (awncc:1)
    self.mmb_clicked_display_radio = gtk.RadioButton(label='Display the dialog')
    self.mmb_clicked_display_radio.identifier = 'mmb.clicked.display'
    self.mmb_clicked_display_radio.connect('toggled',self.radio_changed)
    self.mmb_clicked_table.attach(self.mmb_clicked_display_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Open the folder (awncc:2)
    self.mmb_clicked_open_radio = gtk.RadioButton(self.mmb_clicked_display_radio,'Open the folder')
    if self.mmb==2:
      self.mmb_clicked_open_radio.set_active(True)
    self.mmb_clicked_open_radio.identifier = 'mmb.clicked.open'
    self.mmb_clicked_open_radio.connect('toggled',self.radio_changed)
    self.mmb_clicked_table.attach(self.mmb_clicked_open_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: () Do nothing (awncc:3)
    self.mmb_clicked_nothing_radio = gtk.RadioButton(self.mmb_clicked_display_radio,'Do nothing')
    if self.mmb==3:
      self.mmb_clicked_nothing_radio.set_active(True)
    self.mmb_clicked_nothing_radio.identifier = 'mmb.clicked.nothing'
    self.mmb_clicked_nothing_radio.connect('toggled',self.radio_changed)
    self.mmb_clicked_table.attach(self.mmb_clicked_nothing_radio,0,1,2,3,yoptions=gtk.SHRINK)
    
    #Bold: Default Folder & separator under it
    self.mmb_folder_label = gtk.Label('Default Folder')
    self.mmb_folder_label.modify_font(pango.FontDescription('bold'))
    self.mmb_separator1 = gtk.HSeparator()
    
    #Table
    self.mmb_folder_table = gtk.Table(3,2)
    
    #Row 1: () Home Folder ($HOME, default)
    self.mmb_folder_default_radio = gtk.RadioButton(label='Home Folder (%s, default)' % os.path.expanduser('~'))
    self.mmb_folder_default_radio.identifier = 'mmb.folder.default'
    self.mmb_folder_default_radio.connect('toggled',self.radio_changed)
    self.mmb_folder_table.attach(self.mmb_folder_default_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Custom
    self.mmb_folder_custom_radio = gtk.RadioButton(self.mmb_folder_default_radio,'Custom')
    self.mmb_folder_custom_radio.identifier = 'mmb.folder.custom'
    self.mmb_folder_custom_radio.connect('toggled',self.radio_changed)
    self.mmb_folder_table.attach(self.mmb_folder_custom_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: _______________________[Browse]
    self.mmb_folder_custom_entry = gtk.Entry()
    self.mmb_folder_custom_browse = gtk.Button(stock=gtk.STOCK_OPEN)
    self.mmb_folder_custom_browse.get_children()[0].get_children()[0].get_children()[1].set_text('Browse')
    self.mmb_folder_custom_browse.connect('clicked',self.browse_dir_mmb)
    self.mmb_folder_custom_hbox = gtk.HBox()
    self.mmb_folder_custom_hbox.pack_start(self.mmb_folder_custom_entry)
    self.mmb_folder_custom_hbox.pack_end(self.mmb_folder_custom_browse,False)
    if self.mmb_path!=os.path.expanduser('~'):
      self.mmb_folder_custom_entry.set_text(self.mmb_path)
      self.mmb_folder_custom_radio.set_active(True)
    else:
      self.mmb_folder_custom_entry.set_sensitive(False)
      self.mmb_folder_custom_browse.set_sensitive(False)
    self.mmb_folder_table.attach(self.mmb_folder_custom_hbox,0,2,2,3,yoptions=gtk.SHRINK)
    
    #Now put ALL of the mmb Tab together
    self.mmb_vbox.pack_start(self.mmb_clicked_label,False,False,5)
    self.mmb_vbox.pack_start(self.mmb_separator0,False,False,5)
    self.mmb_vbox.pack_start(self.mmb_clicked_table,False,False,5)
    self.mmb_vbox.pack_start(self.mmb_folder_label,False,False,5)
    self.mmb_vbox.pack_start(self.mmb_separator1,False,False,5)
    self.mmb_vbox.pack_start(self.mmb_folder_table,False,False,5)
    self.nbook.append_page(self.mmb_vbox,self.mmb_tab)
    
    #Now for a close button - no apply button needed since everything is done instantly
    self.close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
    self.close_button.connect('clicked',lambda a:self.window.destroy())
    
    #Now for a main table
    self.main_table = gtk.Table(2,1)
    self.main_table.attach(self.nbook,0,1,0,1)
    self.main_table.attach(self.close_button,0,1,1,2,xoptions=gtk.SHRINK,yoptions=gtk.SHRINK)
    
    #Put it all together
    self.window.add(self.main_table)
    self.window.show_all()
    self.initializing = False
  
  #Browses for a FILE
  def browse_file(self,title):
    self.file_chooser = gtk.FileChooserDialog(title,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
    self.file_chooser_response = self.file_chooser.run()
    self.file_chooser_filename = self.file_chooser.get_filename()
    self.file_chooser.destroy()
    if self.file_chooser_filename==None:
      return False
    try:
      self.awn_new_icon = gtk.gdk.pixbuf_new_from_file(self.file_chooser_filename)
      self.general_icon_custom_entry.set_text(self.file_chooser_filename)
      self.awn_new_icon = self.awn_new_icon.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
      self.window.set_icon(self.awn_new_icon)
      self.set_icon(self.awn_new_icon)
      self.general_icon_custom_img.set_from_pixbuf(self.awn_new_icon)
      self.client.set_string('icon',self.file_chooser_filename)
    except:
      self.browse_err_dialog = gtk.Dialog('Error',self.window,gtk.DIALOG_DESTROY_WITH_PARENT,(gtk.STOCK_OK,gtk.RESPONSE_OK))
      self.browse_err_dialog_label = gtk.Label('The file you selected is not a compatible image.')      self.browse_err_dialog_label.show()
      self.browse_err_dialog.vbox.pack_start(self.browse_err_dialog_label,False,True,15)
      self.browse_err_dialog.run()
      self.browse_err_dialog.destroy()
      return False
  
  #Browses for a directory/folder - for the left button
  def browse_dir_lmb(self,widget):
    self.dir_chooser = gtk.FileChooserDialog('Choose a folder',buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,\
    gtk.STOCK_OPEN,gtk.RESPONSE_OK),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    self.dir_chooser_response = self.dir_chooser.run()
    self.dir_chooser_dirname = self.dir_chooser.get_filename()
    self.dir_chooser.destroy()
    if self.dir_chooser_dirname==None:
      return False
    self.lmb_folder_custom_entry.set_text(self.dir_chooser_dirname)
    self.lmb_folder_custom_entry.set_sensitive(True)
    self.lmb_folder_custom_browse.set_sensitive(True)
    self.client.set_string('lmb_path',self.dir_chooser_dirname)
  
  #Browses for a directory/folder - for the middle button
  def browse_dir_mmb(self,widget):
    self.dir_chooser = gtk.FileChooserDialog('Choose a folder',buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,\
    gtk.STOCK_OPEN,gtk.RESPONSE_OK),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    self.dir_chooser_response = self.dir_chooser.run()
    self.dir_chooser_dirname = self.dir_chooser.get_filename()
    self.dir_chooser.destroy()
    if self.dir_chooser_dirname==None:
      return False
    self.mmb_folder_custom_entry.set_text(self.dir_chooser_dirname)
    self.mmb_folder_custom_entry.set_sensitive(True)
    self.mmb_folder_custom_browse.set_sensitive(True)
    self.client.set_string('mmb_path',self.dir_chooser_dirname)
  
  #Determines what radio button was selected and changes awncc and other important things
  def radio_changed(self,radio):
    
    #No need to do this when everything is loaded
    if self.initializing==True:
      return False
    
    #No need to do anything if a radio is unselected
    if radio.get_active()==False:
      return False
    
    #Now do what is needed based on the radio's identifier
    #Tab: General; Section: Icon; Radio: Default
    if radio.identifier=='general.icon.default':
      self.client.set_string('icon','default')
      self.general_icon_custom_entry.set_sensitive(False)
      self.general_icon_custom_browse.set_sensitive(False)
      self.awn_new_icon = gtk.gdk.pixbuf_new_from_file(self.default_icon_path)
      self.awn_new_icon = self.awn_new_icon.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
      self.window.set_icon(self.awn_new_icon)
      self.set_icon(self.awn_new_icon)
    #Tab: General; Section: Icon; Radio: Theme default
    elif radio.identifier=='general.icon.theme':
      self.client.set_string('icon','theme')
      self.general_icon_custom_entry.set_sensitive(False)
      self.general_icon_custom_browse.set_sensitive(False)
      self.awn_new_icon = self.theme.load_icon('folder',48,48)
      self.awn_new_icon = self.awn_new_icon.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
      self.window.set_icon(self.awn_new_icon)
      self.set_icon(self.awn_new_icon)
    #Tab: General; Section: Icon; Radio: Custom
    elif radio.identifier=='general.icon.custom':
      if self.general_icon_custom_entry.get_text()!='':
        self.awn_new_icon = gtk.gdk.pixbuf_new_from_file(self.general_icon_custom_entry.get_text())
        self.awn_new_icon = self.awn_new_icon.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
        self.window.set_icon(self.awn_new_icon)
        self.set_icon(self.awn_new_icon)
        self.general_icon_custom_entry.set_sensitive(True)
        self.general_icon_custom_browse.set_sensitive(True)
      else:
        self.radio_browse = self.browse_file('Choose an icon')
        if self.radio_browse != False:
          self.general_icon_custom_entry.set_sensitive(True)
          self.general_icon_custom_browse.set_sensitive(True)
          self.awn_new_icon = gtk.gdk.pixbuf_new_from_file(self.general_icon_custom_entry.get_text())
          self.awn_new_icon = self.awn_new_icon.scale_simple(48,48,gtk.gdk.INTERP_BILINEAR)
          self.window.set_icon(self.awn_new_icon)
          self.set_icon(self.awn_new_icon)
        else:
          self.general_icon_default_radio.set_active(True)
    #Tab: General; Section: File Browser; Radio: xdg-open (default)
    elif radio.identifier=='general.fb.default':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('xdg-open')
      self.client.set_string('fb','xdg-open')
    #Tab: General; Section: File Browser; Radio: Nautilus
    elif radio.identifier=='general.fb.nautilus':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('nautilus')
      self.client.set_string('fb','nautilus')
    #Tab: General; Section: File Browser; Radio: Thunar
    elif radio.identifier=='general.fb.thunar':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('thunar')
      self.client.set_string('fb','thunar')
    #Tab: General; Section: File Browser; Radio: Konqueror
    elif radio.identifier=='general.fb.konqueror':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('konqueror')
      self.client.set_string('fb','konqueror')
    #Tab: General; Section: File Browser; Radio: Dolphin
    elif radio.identifier=='general.fb.dolphin':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('dolphin')
      self.client.set_string('fb','dolphin')
    #Tab: General; Section: File Browser; Radio: Custom
    elif radio.identifier=='general.fb.custom':
      self.general_fb_custom_entry.set_sensitive(True)
      self.client.set_string('fb',\
      self.general_fb_custom_entry.get_text())
    #Tab: LMB; Section: When clicked; Radio: Display
    elif radio.identifier=='lmb.clicked.display':
      self.client.set_int('lmb',1)
    #Tab: LMB; Section: When clicked; Radio: Open
    elif radio.identifier=='lmb.clicked.open':
      self.client.set_int('lmb',2)
    #Tab: LMB; Section: When clicked; Radio: Nothing
    elif radio.identifier=='lmb.clicked.nothing':
      self.client.set_int('lmb',3)
    #Tab: LMB; Section: Default Folder; Radio: Home Folder
    elif radio.identifier=='lmb.folder.default':
      self.client.set_string('lmb_path',os.path.expanduser('~'))
      self.lmb_folder_custom_entry.set_sensitive(False)
      self.lmb_folder_custom_browse.set_sensitive(False)
    #Tab: LMB; Section: Default Folder; Radio: Custom
    elif radio.identifier=='lmb.folder.custom':
      if self.lmb_folder_custom_entry.get_text()=='':
        self.browse_dir_lmb(None)
      elif os.path.exists(self.lmb_folder_custom_entry.get_text()):
        self.client.set_string('lmb_path',\
        self.lmb_folder_custom_entry.get_text())
        self.lmb_folder_custom_entry.set_sensitive(True)
        self.lmb_folder_custom_browse.set_sensitive(True)
      else:
        self.browse_dir_lmb(None)
    #Tab: MMB; Section: When clicked; Radio: Display
    elif radio.identifier=='mmb.clicked.display':
      self.client.set_int('mmb',1)
    #Tab: MMB; Section: When clicked; Radio: Open
    elif radio.identifier=='mmb.clicked.open':
      self.client.set_int('mmb',2)
    #Tab: MMB; Section: When clicked; Radio: Nothing
    elif radio.identifier=='mmb.clicked.nothing':
      self.client.set_int('mmb',3)
    #Tab: MMB; Section: Default Folder; Radio: Home Folder
    elif radio.identifier=='mmb.folder.default':
      self.client.set_string('mmb_path',os.path.expanduser('~'))
      self.mmb_folder_custom_entry.set_sensitive(False)
      self.mmb_folder_custom_browse.set_sensitive(False)
    #Tab: MMB; Section: Default Folder; Radio: Custom
    elif radio.identifier=='mmb.folder.custom':
      if self.mmb_folder_custom_entry.get_text()=='':
        self.browse_dir_mmb(None)
      elif os.path.exists(self.mmb_folder_custom_entry.get_text()):
        self.client.set_string('mmb_path',\
        self.mmb_folder_custom_entry.get_text())
        self.mmb_folder_custom_entry.set_sensitive(True)
        self.mmb_folder_custom_browse.set_sensitive(True)
      else:
        self.browse_dir_mmb(None)
  
  #Determines what check button was selected and changes awncc and other important things
  def check_changed(self,check):
    
    #No need to do this when everything is loaded
    if self.initializing==True:
      return False
    
    #Tab: Dialog; Section: Places; Checkbox: Home Folder
    if check.identifier=='dialog.places.home':
      if check.get_active()==True:
        self.client.set_int('places_home',2)
      else:
        self.client.set_int('places_home',1)
    #Tab: Dialog; Section: Places; Checkbox: Local drives
    elif check.identifier=='dialog.places.local':
      if check.get_active()==True:
        self.client.set_int('places_local',2)
      else:
        self.client.set_int('places_local',1)
    #Tab: Dialog; Section: Places; Checkbox: Network drives
    elif check.identifier=='dialog.places.network':
      if check.get_active()==True:
        self.client.set_int('places_network',2)
      else:
        self.client.set_int('places_network',1)
    #Tab: Dialog; Section: Places; Checkbox: Bookmarks
    elif check.identifier=='dialog.places.bookmarks':
      if check.get_active()==True:
        self.client.set_int('places_bookmarks',2)
      else:
        self.client.set_int('places_bookmarks',1)
    #Tab: Dialog; Section: Behavior; Checkbox: Focus
    elif check.identifier=='dialog.behavior.focus':
      if check.get_active()==True:
        self.client.set_int('focus_entry',2)
      else:
        self.client.set_int('focus_entry',1)
    #Tab: Dialog; Section: Behavior; Checkbox: Open place
    elif check.identifier=='dialog.behavior.open':
      if check.get_active()==True:
        self.client.set_int('places_open',2)
      else:
        self.client.set_int('places_open',1)
