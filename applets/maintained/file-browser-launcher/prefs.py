#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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

import awn
from awn.extras import _

group = awn.CONFIG_DEFAULT_GROUP

class Prefs:
  ignore_all = False
  no_check_all = False
  def __init__(self, applet):
    self.applet = applet
    self.uid = applet.uid
    
    #Initiate what is needed
    self.window = gtk.Window()
    self.window.set_title(_("File Browser Launcher Preferences"))
    self.nbook = gtk.Notebook()
    self.theme = gtk.icon_theme_get_default()
    self.initializing = True
    
    #AwnConfigClient instance
    self.client = awn.Config('file-browser-launcher', None)
    
    #File browser
    self.fb = self.client.get_string(group, 'fb')
    
    #Left mouse button action
    self.lmb = self.client.get_int(group, 'lmb')
    
    #Left mouse button path
    self.lmb_path = self.client.get_string(group, 'lmb_path')
    
    #Middle mouse button action
    self.mmb = self.client.get_int(group, 'mmb')
    
    #Middle mouse button path
    self.mmb_path = self.client.get_string(group, 'mmb_path')
    
    #Places: show bookmarks, home, local, network
    self.show_bookmarks = self.client.get_int(group, 'show_bookmarks')
    self.show_home = self.client.get_int(group, 'show_home')
    self.show_local = self.client.get_int(group, 'show_local')
    self.show_network = self.client.get_int(group, 'show_network')
    self.show_connect = self.client.get_int(group, 'show_connect')
    self.show_filesystem = self.client.get_int(group, 'show_filesystem')
    
    #Open the places item when clicked
    self.places_open = self.client.get_int(group, 'places_open')
    
    #Focus the location entry widget
    self.focus_entry = self.client.get_int(group, 'focus_entry')
    
    #Set the icon approiately
    self.window.set_icon(applet.icon)
    
    #Make the "General" tab
    self.general_tab = gtk.Label(_("General"))
    self.general_vbox = gtk.VBox()
    
    #Next section: File Browser
    #Bold text: File Browser with an HSeparator under it
    self.general_fb_label = gtk.Label(_("File Browser"))
    self.general_fb_label.modify_font(pango.FontDescription('bold'))
    self.general_separator1 = gtk.HSeparator()
    
    #Make the table for the file browser selection
    self.general_fb_table = gtk.Table(2,2)
    
    #First row: () xdg-open (default)
    self.general_fb_default_radio = gtk.RadioButton(label='xdg-open ' + _("(default)"))
    self.general_fb_default_radio.identifier = 'general.fb.default'
    self.general_fb_default_radio.connect('toggled',self.radio_changed)
    self.general_fb_table.attach(self.general_fb_default_radio,0,2,0,1,yoptions=gtk.SHRINK)
    
    #Go through short list of common file managers, include them in a list just like nautilus
    self.general_fb_list = ['nautilus','thunar','konqueror','dolphin']
    self.general_fb_other_radios = []
    self.general_fb_other_labels = []
    self.general_fb_y = 0
    for fb in self.general_fb_list:
      if os.path.exists('/usr/bin/'+fb) or os.path.exists('/usr/local/bin/'+fb):
        self.general_fb_other_radios.append(gtk.RadioButton(self.general_fb_default_radio, fb.capitalize()))
        self.general_fb_other_radios[self.general_fb_y].identifier = 'general.fb.%s' % fb
        self.general_fb_other_radios[self.general_fb_y].connect('toggled',self.radio_changed)
        if self.fb==fb:
          self.general_fb_other_radios[self.general_fb_y].set_active(True)
        self.general_fb_table.attach(self.general_fb_other_radios[self.general_fb_y],0,2,\
          (self.general_fb_y+1),(self.general_fb_y+2),yoptions=gtk.SHRINK)
        self.general_fb_y = self.general_fb_y+1
    
    #Last option: custom with an entry for the app name
    self.general_fb_custom_radio = gtk.RadioButton(self.general_fb_default_radio, _("Other"))
    self.general_fb_custom_radio.identifier = 'general.fb.custom'
    self.general_fb_custom_radio.connect('toggled',self.radio_changed)
    self.general_fb_custom_entry = gtk.Entry()
    if self.fb in ['xdg-open','nautilus','thunar','konqueror','dolphin']:
      self.general_fb_custom_entry.set_sensitive(False)
    else:
      self.general_fb_custom_radio.set_active(True)
    self.general_fb_custom_entry.set_text(self.fb)
    self.general_fb_custom_entry.connect('changed',\
    lambda w:self.client.set_string(group, 'fb', w.get_text()))
    if self.fb in ['xdg-open','nautilus','thunar','konqueror','dolphin']:
      self.general_fb_custom_entry.set_sensitive(False)
    self.general_fb_table.attach(self.general_fb_custom_radio,0,2,\
    (self.general_fb_y+1),(self.general_fb_y+2),yoptions=gtk.SHRINK)
    self.general_fb_table.attach(self.general_fb_custom_entry,0,2,\
    (self.general_fb_y+2),(self.general_fb_y+3),yoptions=gtk.SHRINK)
    
    #Put ALL of the general tab together
    self.general_vbox.pack_start(self.general_fb_label, False, False, 5)
    self.general_vbox.pack_start(self.general_separator1, False, False, 5)
    self.general_vbox.pack_start(self.general_fb_table, False, False, 5)
    self.general_vbox.show_all()
    self.nbook.append_page(self.general_vbox,self.general_tab)
    
    #Dialog tab: options for places and basic behavior
    self.dialog_tab = gtk.Label(_("Dialog"))
    self.dialog_vbox = gtk.VBox()
    
    #Bold text: Places with an hseparator under it
    self.dialog_places_label = gtk.Label(_("Places"))
    self.dialog_places_label.modify_font(pango.FontDescription('bold'))
    self.dialog_separator0 = gtk.HSeparator()
    
    #VBox for the check buttons
    self.dialog_places_vbox = gtk.VBox()

    #Show all places
    self.dialog_places_all = gtk.CheckButton(_("Show all places"))
    self.dialog_places_all.identifier = 'dialog.places.all'
    self.dialog_places_all.connect('toggled', self.check_changed)
    if self.show_home == 2 and self.show_filesystem == 2 and self.show_local \
      == 2 and self.show_network == 2 and self.show_connect and \
      self.show_bookmarks == 2:
      self.dialog_places_all.set_active(True)

    #Home Folder
    self.dialog_places_home = gtk.CheckButton(_("Home folder"))
    self.dialog_places_home.identifier = 'dialog.places.home'
    self.dialog_places_home.connect('toggled',self.check_changed)
    if self.show_home==2:
      self.dialog_places_home.set_active(True)

    #Filesystem
    self.dialog_places_filesystem = gtk.CheckButton(_("Filesystem"))
    self.dialog_places_filesystem.identifier = 'dialog.places.filesystem'
    self.dialog_places_filesystem.connect('toggled', self.check_changed)
    if self.show_filesystem == 2:
      self.dialog_places_filesystem.set_active(True)
    
    #Mounted local drives
    self.dialog_places_local = gtk.CheckButton(_("Mounted local drives"))
    self.dialog_places_local.identifier = 'dialog.places.local'
    self.dialog_places_local.connect('toggled',self.check_changed)
    if self.show_local==2:
      self.dialog_places_local.set_active(True)
    
    #Mounted network drives
    self.dialog_places_network = gtk.CheckButton(_("Mounted network drives"))
    self.dialog_places_network.identifier = 'dialog.places.network'
    self.dialog_places_network.connect('toggled',self.check_changed)
    if self.show_network==2:
      self.dialog_places_network.set_active(True)

    #Connect to server
    self.dialog_places_connect = gtk.CheckButton(_("Connect to server"))
    self.dialog_places_connect.identifier = 'dialog.places.connect'
    self.dialog_places_connect.connect('toggled', self.check_changed)
    if not applet.nautilus_connect_server:
      self.dialog_places_connect.set_sensitive(False)
    if self.show_connect == 2:
      self.dialog_places_connect.set_active(True)

    #Bookmarks
    self.dialog_places_bookmarks = gtk.CheckButton(_("Bookmarks"))
    self.dialog_places_bookmarks.identifier = 'dialog.places.bookmarks'
    self.dialog_places_bookmarks.connect('toggled',self.check_changed)
    if self.show_bookmarks==2:
      self.dialog_places_bookmarks.set_active(True)
    
    #Put the places checkbuttons together
    self.dialog_places_vbox.pack_start(self.dialog_places_all)
    self.dialog_places_vbox.pack_start(self.dialog_places_home)
    self.dialog_places_vbox.pack_start(self.dialog_places_filesystem)
    self.dialog_places_vbox.pack_start(self.dialog_places_local)
    self.dialog_places_vbox.pack_start(self.dialog_places_network)
    self.dialog_places_vbox.pack_start(self.dialog_places_connect)
    self.dialog_places_vbox.pack_start(self.dialog_places_bookmarks)
    
    #Bold text: Behavior with hseparator under it
    self.dialog_behavior_label = gtk.Label(_("Behavior"))
    self.dialog_behavior_label.modify_font(pango.FontDescription('bold'))
    self.dialog_separator1 = gtk.HSeparator()
    
    #[] Focus the location text box
    self.dialog_behavior_focus = gtk.CheckButton(_("Focus the location text box"))
    self.dialog_behavior_focus.identifier = 'dialog.behavior.focus'
    self.dialog_behavior_focus.connect('toggled',self.check_changed)
    if self.focus_entry==2:
      self.dialog_behavior_focus.set_active(True)
    
    #[] Open the selected place when clicked
    self.dialog_behavior_open = gtk.CheckButton(_("Open the selected place when clicked"))
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
    self.lmb_tab = gtk.Label(_("Left Mouse Button"))
    self.lmb_vbox = gtk.VBox()
    
    #When clicked, (in bold with hseparator under it)
    self.lmb_clicked_label = gtk.Label(_("When clicked, ..."))
    self.lmb_clicked_label.modify_font(pango.FontDescription('bold'))
    self.lmb_separator0 = gtk.HSeparator()
    
    #Table
    self.lmb_clicked_table = gtk.Table(3,2)
    
    #Row 1: () Display the dialog (default) (awncc:0)
    self.lmb_clicked_display_radio = gtk.RadioButton(label=_("Display the dialog"))
    self.lmb_clicked_display_radio.identifier = 'lmb.clicked.display'
    self.lmb_clicked_display_radio.connect('toggled',self.radio_changed)
    self.lmb_clicked_table.attach(self.lmb_clicked_display_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Open the folder (awncc:1)
    self.lmb_clicked_open_radio = gtk.RadioButton(self.lmb_clicked_display_radio,_("Open the folder"))
    if self.lmb==2:
      self.lmb_clicked_open_radio.set_active(True)
    self.lmb_clicked_open_radio.identifier = 'lmb.clicked.open'
    self.lmb_clicked_open_radio.connect('toggled',self.radio_changed)
    self.lmb_clicked_open_label = gtk.Label(_("Open the folder"))
    self.lmb_clicked_table.attach(self.lmb_clicked_open_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: () Do nothing (awncc:2)
    self.lmb_clicked_nothing_radio = gtk.RadioButton(self.lmb_clicked_display_radio,_("Do nothing"))
    if self.lmb==3:
      self.lmb_clicked_nothing_radio.set_active(True)
    self.lmb_clicked_nothing_radio.identifier = 'lmb.clicked.nothing'
    self.lmb_clicked_nothing_radio.connect('toggled',self.radio_changed)
    self.lmb_clicked_table.attach(self.lmb_clicked_nothing_radio,0,1,2,3,yoptions=gtk.SHRINK)
    
    #Bold: Default Folder & separator under it
    self.lmb_folder_label = gtk.Label(_("Default Folder"))
    self.lmb_folder_label.modify_font(pango.FontDescription('bold'))
    self.lmb_separator1 = gtk.HSeparator()
    
    #Table
    self.lmb_folder_table = gtk.Table(3,2)
    
    #Row 1: () Home Folder ($HOME, default)
    self.lmb_folder_default_radio = gtk.RadioButton(label=_("Home Folder (%s, default)") % os.path.expanduser('~'))
    self.lmb_folder_default_radio.identifier = 'lmb.folder.default'
    self.lmb_folder_default_radio.connect('toggled',self.radio_changed)
    self.lmb_folder_table.attach(self.lmb_folder_default_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Custom
    self.lmb_folder_custom_radio = gtk.RadioButton(self.lmb_folder_default_radio,_("Other"))
    self.lmb_folder_custom_radio.identifier = 'lmb.folder.custom'
    self.lmb_folder_custom_radio.connect('toggled',self.radio_changed)
    self.lmb_folder_table.attach(self.lmb_folder_custom_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: _______________________[Browse]
    self.lmb_folder_custom_entry = gtk.Entry()
    self.lmb_folder_custom_browse = gtk.Button(stock=gtk.STOCK_OPEN)
    self.lmb_folder_custom_browse.get_children()[0].get_children()[0].get_children()[1].set_text(_("Browse"))
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
    self.mmb_tab = gtk.Label(_("Middle Mouse Button"))
    self.mmb_vbox = gtk.VBox()
    
    #When clicked, (in bold with hseparator under it)
    self.mmb_clicked_label = gtk.Label(_("When clicked, ..."))
    self.mmb_clicked_label.modify_font(pango.FontDescription('bold'))
    self.mmb_separator0 = gtk.HSeparator()
    
    #Table
    self.mmb_clicked_table = gtk.Table(3,2)
    
    #Row 1: () Display the dialog (default) (awncc:1)
    self.mmb_clicked_display_radio = gtk.RadioButton(label=_("Display the dialog"))
    self.mmb_clicked_display_radio.identifier = 'mmb.clicked.display'
    self.mmb_clicked_display_radio.connect('toggled',self.radio_changed)
    self.mmb_clicked_table.attach(self.mmb_clicked_display_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Open the folder (awncc:2)
    self.mmb_clicked_open_radio = gtk.RadioButton(self.mmb_clicked_display_radio,_("Open the folder"))
    if self.mmb==2:
      self.mmb_clicked_open_radio.set_active(True)
    self.mmb_clicked_open_radio.identifier = 'mmb.clicked.open'
    self.mmb_clicked_open_radio.connect('toggled',self.radio_changed)
    self.mmb_clicked_table.attach(self.mmb_clicked_open_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: () Do nothing (awncc:3)
    self.mmb_clicked_nothing_radio = gtk.RadioButton(self.mmb_clicked_display_radio,_("Do nothing"))
    if self.mmb==3:
      self.mmb_clicked_nothing_radio.set_active(True)
    self.mmb_clicked_nothing_radio.identifier = 'mmb.clicked.nothing'
    self.mmb_clicked_nothing_radio.connect('toggled',self.radio_changed)
    self.mmb_clicked_table.attach(self.mmb_clicked_nothing_radio,0,1,2,3,yoptions=gtk.SHRINK)
    
    #Bold: Default Folder & separator under it
    self.mmb_folder_label = gtk.Label(_("Default Folder"))
    self.mmb_folder_label.modify_font(pango.FontDescription('bold'))
    self.mmb_separator1 = gtk.HSeparator()
    
    #Table
    self.mmb_folder_table = gtk.Table(3,2)
    
    #Row 1: () Home Folder ($HOME, default)
    self.mmb_folder_default_radio = gtk.RadioButton(label=_("Home Folder (%s, default)") % os.path.expanduser('~'))
    self.mmb_folder_default_radio.identifier = 'mmb.folder.default'
    self.mmb_folder_default_radio.connect('toggled',self.radio_changed)
    self.mmb_folder_table.attach(self.mmb_folder_default_radio,0,1,0,1,yoptions=gtk.SHRINK)
    
    #Row 2: () Custom
    self.mmb_folder_custom_radio = gtk.RadioButton(self.mmb_folder_default_radio,_("Other"))
    self.mmb_folder_custom_radio.identifier = 'mmb.folder.custom'
    self.mmb_folder_custom_radio.connect('toggled',self.radio_changed)
    self.mmb_folder_table.attach(self.mmb_folder_custom_radio,0,1,1,2,yoptions=gtk.SHRINK)
    
    #Row 3: _______________________[Browse]
    self.mmb_folder_custom_entry = gtk.Entry()
    self.mmb_folder_custom_browse = gtk.Button(stock=gtk.STOCK_OPEN)
    self.mmb_folder_custom_browse.get_children()[0].get_children()[0].get_children()[1].set_text(_("Browse"))
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
    close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
    close_button.connect('clicked',lambda a:self.window.destroy())

    #HButtonBox
    hbbox = gtk.HButtonBox()
    hbbox.set_layout(gtk.BUTTONBOX_END)
    hbbox.pack_end(close_button, False, False, 5)

    #Now for a main table
    main_vbox = gtk.VBox(False, 6)
    main_vbox.pack_start(self.nbook, True, True)
    main_vbox.pack_start(hbbox, False, False)
    
    #Put it all together
    self.window.add(main_vbox)
    self.window.set_border_width(6)
    self.window.show_all()
    self.initializing = False
  
  #Browses for a directory/folder - for the left button
  def browse_dir_lmb(self,widget):
    self.dir_chooser = gtk.FileChooserDialog(_("Choose a folder"),buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,\
    gtk.STOCK_OPEN,gtk.RESPONSE_OK),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    self.dir_chooser_response = self.dir_chooser.run()
    self.dir_chooser_dirname = self.dir_chooser.get_filename()
    self.dir_chooser.destroy()
    if self.dir_chooser_dirname==None:
      return False
    self.lmb_folder_custom_entry.set_text(self.dir_chooser_dirname)
    self.lmb_folder_custom_entry.set_sensitive(True)
    self.lmb_folder_custom_browse.set_sensitive(True)
    self.client.set_string(group, 'lmb_path', self.dir_chooser_dirname)
  
  #Browses for a directory/folder - for the middle button
  def browse_dir_mmb(self,widget):
    self.dir_chooser = gtk.FileChooserDialog(_("Choose a folder"),buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,\
    gtk.STOCK_OPEN,gtk.RESPONSE_OK),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    self.dir_chooser_response = self.dir_chooser.run()
    self.dir_chooser_dirname = self.dir_chooser.get_filename()
    self.dir_chooser.destroy()
    if self.dir_chooser_dirname==None:
      return False
    self.mmb_folder_custom_entry.set_text(self.dir_chooser_dirname)
    self.mmb_folder_custom_entry.set_sensitive(True)
    self.mmb_folder_custom_browse.set_sensitive(True)
    self.client.set_string(group, 'mmb_path', self.dir_chooser_dirname)
  
  #Determines what radio button was selected and changes awncc and other important things
  def radio_changed(self,radio):
    
    #No need to do this when everything is loaded
    if self.initializing==True:
      return False
    
    #No need to do anything if a radio is unselected
    if radio.get_active()==False:
      return False
    
    #Now do what is needed based on the radio's identifier
    #Tab: General; Section: File Browser; Radio: xdg-open (default)
    if radio.identifier=='general.fb.default':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('xdg-open')
      self.client.set_string(group, 'fb','xdg-open')
    #Tab: General; Section: File Browser; Radio: Nautilus
    elif radio.identifier=='general.fb.nautilus':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('nautilus')
      self.client.set_string(group, 'fb','nautilus')
    #Tab: General; Section: File Browser; Radio: Thunar
    elif radio.identifier=='general.fb.thunar':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('thunar')
      self.client.set_string(group, 'fb','thunar')
    #Tab: General; Section: File Browser; Radio: Konqueror
    elif radio.identifier=='general.fb.konqueror':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('konqueror')
      self.client.set_string(group, 'fb','konqueror')
    #Tab: General; Section: File Browser; Radio: Dolphin
    elif radio.identifier=='general.fb.dolphin':
      self.general_fb_custom_entry.set_sensitive(False)
      self.general_fb_custom_entry.set_text('dolphin')
      self.client.set_string(group, 'fb','dolphin')
    #Tab: General; Section: File Browser; Radio: Custom
    elif radio.identifier=='general.fb.custom':
      self.general_fb_custom_entry.set_sensitive(True)
      self.client.set_string(group, 'fb',\
      self.general_fb_custom_entry.get_text())
    #Tab: LMB; Section: When clicked; Radio: Display
    elif radio.identifier=='lmb.clicked.display':
      self.client.set_int(group, 'lmb',1)
    #Tab: LMB; Section: When clicked; Radio: Open
    elif radio.identifier=='lmb.clicked.open':
      self.client.set_int(group, 'lmb',2)
    #Tab: LMB; Section: When clicked; Radio: Nothing
    elif radio.identifier=='lmb.clicked.nothing':
      self.client.set_int(group, 'lmb',3)
    #Tab: LMB; Section: Default Folder; Radio: Home Folder
    elif radio.identifier=='lmb.folder.default':
      self.client.set_string(group, 'lmb_path',os.path.expanduser('~'))
      self.lmb_folder_custom_entry.set_sensitive(False)
      self.lmb_folder_custom_browse.set_sensitive(False)
    #Tab: LMB; Section: Default Folder; Radio: Custom
    elif radio.identifier=='lmb.folder.custom':
      if self.lmb_folder_custom_entry.get_text()=='':
        self.browse_dir_lmb(None)
      elif os.path.exists(self.lmb_folder_custom_entry.get_text()):
        self.client.set_string(group, 'lmb_path',\
        self.lmb_folder_custom_entry.get_text())
        self.lmb_folder_custom_entry.set_sensitive(True)
        self.lmb_folder_custom_browse.set_sensitive(True)
      else:
        self.browse_dir_lmb(None)
    #Tab: MMB; Section: When clicked; Radio: Display
    elif radio.identifier=='mmb.clicked.display':
      self.client.set_int(group, 'mmb',1)
    #Tab: MMB; Section: When clicked; Radio: Open
    elif radio.identifier=='mmb.clicked.open':
      self.client.set_int(group, 'mmb',2)
    #Tab: MMB; Section: When clicked; Radio: Nothing
    elif radio.identifier=='mmb.clicked.nothing':
      self.client.set_int(group, 'mmb',3)
    #Tab: MMB; Section: Default Folder; Radio: Home Folder
    elif radio.identifier=='mmb.folder.default':
      self.client.set_string(group, 'mmb_path',os.path.expanduser('~'))
      self.mmb_folder_custom_entry.set_sensitive(False)
      self.mmb_folder_custom_browse.set_sensitive(False)
    #Tab: MMB; Section: Default Folder; Radio: Custom
    elif radio.identifier=='mmb.folder.custom':
      if self.mmb_folder_custom_entry.get_text()=='':
        self.browse_dir_mmb(None)
      elif os.path.exists(self.mmb_folder_custom_entry.get_text()):
        self.client.set_string(group, 'mmb_path',\
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
    

    #Tab: Dialog; Section: Places; Checkbox: Show all places
    if check.identifier == 'dialog.places.all':
      if check.get_active():
        self.dialog_places_home.set_active(True)
        self.dialog_places_filesystem.set_active(True)
        self.dialog_places_local.set_active(True)
        self.dialog_places_network.set_active(True)
        self.dialog_places_connect.set_active(True)
        self.dialog_places_bookmarks.set_active(True)
      else:
        if not self.ignore_all:
          self.no_check_all = True
          self.dialog_places_home.set_active(False)
          self.dialog_places_filesystem.set_active(False)
          self.dialog_places_local.set_active(False)
          self.dialog_places_network.set_active(False)
          self.dialog_places_connect.set_active(False)
          self.dialog_places_bookmarks.set_active(False)
          self.no_check_all = False
        else:
          if self.dialog_places_home.get_active() and \
            self.dialog_places_filesystem.get_active() and \
            self.dialog_places_local.get_active() and \
            self.dialog_places_network.get_active() and \
            self.dialog_places_connect.get_active() and \
            self.dialog_places_bookmarks.get_active():

            self.dialog_places_home.set_active(False)
            self.dialog_places_filesystem.set_active(False)
            self.dialog_places_local.set_active(False)
            self.dialog_places_network.set_active(False)
            self.dialog_places_connect.set_active(False)
            self.dialog_places_bookmarks.set_active(False)
          self.ignore_all = False

    #Tab: Dialog; Section: Places; Checkbox: Home Folder
    elif check.identifier=='dialog.places.home':
      if check.get_active()==True:
        self.client.set_int(group, 'show_home',2)
      else:
        self.client.set_int(group, 'show_home',1)
      self.check_all()

    #Tab: Dialog; Section: Places; Checkbox: Filesystem
    elif check.identifier == 'dialog.places.filesystem':
      if check.get_active():
        self.client.set_int(group, 'show_filesystem', 2)
      else:
        self.client.set_int(group, 'show_filesystem', 1)
      self.check_all()

    #Tab: Dialog; Section: Places; Checkbox: Local drives
    elif check.identifier=='dialog.places.local':
      if check.get_active()==True:
        self.client.set_int(group, 'show_local',2)
      else:
        self.client.set_int(group, 'show_local',1)
      self.check_all()

    #Tab: Dialog; Section: Places; Checkbox: Network drives
    elif check.identifier=='dialog.places.network':
      if check.get_active()==True:
        self.client.set_int(group, 'show_network',2)
      else:
        self.client.set_int(group, 'show_network',1)
      self.check_all()

    #Tab: Dialog; Section: Places; Checkbox: Connect to server
    elif check.identifier == 'dialog.places.connect':
      if check.get_active():
        self.client.set_int(group, 'show_connect', 2)
      else:
        self.client.set_int(group, 'show_connect', 1)
      self.check_all()

    #Tab: Dialog; Section: Places; Checkbox: Bookmarks
    elif check.identifier=='dialog.places.bookmarks':
      if check.get_active()==True:
        self.client.set_int(group, 'show_bookmarks',2)
      else:
        self.client.set_int(group, 'show_bookmarks',1)
      self.check_all()

    #Tab: Dialog; Section: Behavior; Checkbox: Focus
    elif check.identifier=='dialog.behavior.focus':
      if check.get_active()==True:
        self.client.set_int(group, 'focus_entry',2)
      else:
        self.client.set_int(group, 'focus_entry',1)

    #Tab: Dialog; Section: Behavior; Checkbox: Open place
    elif check.identifier=='dialog.behavior.open':
      if check.get_active()==True:
        self.client.set_int(group, 'places_open',2)
      else:
        self.client.set_int(group, 'places_open',1)

  #Determine if all the places checkboxes are the same state
  def check_all(self):
    if self.no_check_all:
      return

    li = []
    li.append(self.dialog_places_home.get_active())
    li.append(self.dialog_places_filesystem.get_active())
    li.append(self.dialog_places_local.get_active())
    li.append(self.dialog_places_network.get_active())
    li.append(self.dialog_places_connect.get_active())
    li.append(self.dialog_places_bookmarks.get_active())

    all_true = True
    all_false = True

    for i in li:
      if not i:
        all_true = False

    for i in li:
      if i:
        all_false = False


    if all_true:
      self.dialog_places_all.set_active(True)

    else:
      self.ignore_all = True
      self.dialog_places_all.set_active(False)
