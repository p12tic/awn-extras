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

from desktopagnostic.config import GROUP_DEFAULT as group
import awn
from awn.extras import _


class Prefs:
  ignore_all = False
  no_check_all = False

  def __init__(self, applet):
    self.applet = applet

    #Initiate what is needed
    self.window = gtk.Window()
    self.window.set_title(_("File Browser Launcher Preferences"))
    self.nbook = gtk.Notebook()
    self.theme = gtk.icon_theme_get_default()
    self.initializing = True

    #AwnConfigClient instance
    self.client = awn.config_get_default_for_applet(applet)

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

    #Set the icon appropriately
    self.window.set_icon(self.theme.load_icon('stock_folder', 48, 0))

    #Make the General tab
    general_vbox = gtk.VBox(False, 12)
    general_vbox.set_border_width(12)

    #First section: File Browser
    fb_vbox = gtk.VBox()
    general_vbox.pack_start(fb_vbox, False)

    label = gtk.Label()
    label.set_markup('<b>%s</b>' % _("File Browser"))
    label.set_alignment(0.0, 0.5)

    vbox = gtk.VBox()

    align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
    align.set_padding(0, 0, 6, 0)
    align.add(vbox)

    #xdg-open (aka system default)
    default_radio = gtk.RadioButton(None, _("System Default"))
    default_radio.identifier = 'general.fb.default'
    default_radio.connect('toggled', self.radio_toggled)
    vbox.pack_start(default_radio, False)

    #Go through short list of common file managers
    fb_list = {'nautilus': "Nautilus",
      'thunar': "Thunar",
      'konqueror': "Konqueror",
      'dolphin': "Dolphin"}

    keys = fb_list.keys()
    keys.sort()

    for name in keys:
      if os.path.exists('/usr/bin/' + name) or os.path.exists('/usr/local/bin/' + name):
        radio = gtk.RadioButton(default_radio, fb_list[name])
        radio.identifier = 'general.fb.' + name
        radio.connect('toggled', self.radio_toggled)
        vbox.pack_start(radio, False)
        if self.fb == name:
          radio.set_active(True)

    #Last option: custom with an entry for the app name
    radio = gtk.RadioButton(default_radio, _("Other"))
    radio.identifier = 'general.fb.custom'

    self.custom_entry = gtk.Entry()
    if self.fb in fb_list.keys() + ['xdg-open']:
      self.custom_entry.set_sensitive(False)

    else:
      radio.set_active(True)

    radio.connect('toggled', self.radio_toggled)

    self.custom_entry.set_text(self.fb)
    self.custom_entry.connect('focus-out-event', \
      lambda w, e:self.client.set_string(group, 'fb', w.get_text()))

    vbox.pack_start(radio, False)
    vbox.pack_start(self.custom_entry, False)

    fb_vbox.pack_start(label, False)
    fb_vbox.pack_start(align, False)

    #Second section: Behavior
    behavior_vbox = gtk.VBox()
    general_vbox.pack_start(behavior_vbox, False)

    label = gtk.Label()
    label.set_markup('<b>%s</b>' % _("Behavior"))
    label.set_alignment(0.0, 0.5)

    vbox = gtk.VBox()

    align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
    align.set_padding(0, 0, 6, 0)
    align.add(vbox)

    check = gtk.CheckButton(_("Use docklet"))
    check.identifier = 'general.docklet'
    if self.client.get_bool(group, 'docklet'):
      check.set_active(True)
    check.connect('toggled', self.check_toggled)
    vbox.pack_start(check, False)

    self.focus_check = gtk.CheckButton(_("Focus text entry"))
    self.focus_check.identifier = 'general.focus'
    if self.focus_entry == 2:
      self.focus_check.set_active(True)
    self.focus_check.connect('toggled', self.check_toggled)
    vbox.pack_start(self.focus_check, False)
    if self.client.get_bool(group, 'docklet'):
      self.focus_check.set_sensitive(False)

    self.open_check = gtk.CheckButton(_("Open place when clicked"))
    self.open_check.identifier = 'general.open'
    if self.places_open:
      self.open_check.set_active(True)
    self.open_check.connect('toggled', self.check_toggled)
    vbox.pack_start(self.open_check, False)
    if self.client.get_bool(group, 'docklet'):
      self.open_check.set_sensitive(False)

    behavior_vbox.pack_start(label, False)
    behavior_vbox.pack_start(align, False)

    #Put the general tab together
    self.nbook.append_page(general_vbox, gtk.Label(_("General")))

    #Places tab
    places_vbox = gtk.VBox()
    places_vbox.set_border_width(12)

    #Show all places
    self.places_all = gtk.CheckButton(_("Show all places"))
    self.places_all.identifier = 'places.all'
    self.places_all.set_active(True)
    for x in (self.show_home, self.show_filesystem, self.show_local, self.show_network,
      self.show_connect):
      if x != 2:
        self.places_all.set_active(False)
        break
    self.places_all.connect('toggled', self.check_toggled)
    places_vbox.pack_start(self.places_all, False)

    self.places_checks = {}
    places = {'home': _("Home folder"), 'filesystem': _("Filesystem"),
      'local': _("Mounted local drives"), 'network': _("Mounted network drives"),
      'connect': _("Connect to server"), 'bookmarks': _("Bookmarks")}
    keys = {'home': self.show_home, 'filesystem': self.show_filesystem,
      'local': self.show_local, 'network': self.show_network,
      'connect': self.show_connect, 'bookmarks': self.show_bookmarks}
    places_in_order = ('home', 'filesystem', 'local', 'network', 'connect', 'bookmarks')

    for place in places_in_order:
      check = gtk.CheckButton(places[place])
      check.identifier = 'places.' + place
      if keys[place] == 2:
        check.set_active(True)
      check.connect('toggled', self.check_toggled)
      self.places_checks[place] = check
      places_vbox.pack_start(check, False)

    if not applet.nautilus_connect_server:
      self.places_checks['connect'].set_sensitive(False)

    self.nbook.append_page(places_vbox, gtk.Label(_("Places")))

    #Left click
    left_vbox = gtk.VBox(False, 12)
    left_vbox.set_border_width(12)

    action_vbox = gtk.VBox()
    left_vbox.pack_start(action_vbox, False)

    label = gtk.Label()
    label.set_markup('<b>%s</b>' % _("Action"))
    label.set_alignment(0.0, 0.5)
    action_vbox.pack_start(label, False)

    vbox = gtk.VBox()

    align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
    align.set_padding(0, 0, 6, 0)
    align.add(vbox)
    action_vbox.pack_start(align, False)

    keys = {'display': _("Display dialog/docklet"), 'open': _("Open the folder"),
      'nothing': _("Nothing")}
    radios = []

    for key in ('display', 'open', 'nothing'):
      radio = gtk.RadioButton(None, keys[key])
      radios.append(radio)
      radio.identifier = 'lmb.' + key
      vbox.pack_start(radio)

      if key == 'open':
        radio.set_group(radios[0])
        radio.set_active(self.lmb == 2)

      elif key == 'nothing':
        radio.set_group(radios[0])
        radio.set_active(self.lmb == 3)

      radio.connect('toggled', self.radio_toggled)

    #Folder
    folder_vbox = gtk.VBox()
    left_vbox.pack_start(folder_vbox, False)

    label = gtk.Label()
    label.set_markup('<b>%s</b>' % _("Folder"))
    label.set_alignment(0.0, 0.5)
    folder_vbox.pack_start(label, False)

    vbox = gtk.VBox()

    align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
    align.set_padding(0, 0, 6, 0)
    align.add(vbox)
    folder_vbox.pack_start(align, False)

    file_chooser = gtk.FileChooserButton(_("Choose a folder"))
    self.lmb_chooser = file_chooser
    file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

    if self.lmb_path is None or self.lmb_path.strip() == '' or not os.path.exists(self.lmb_path):
      file_chooser.set_filename(os.environ['HOME'] + '/')

    else:
      file_chooser.set_filename(self.lmb_path)

    vbox.pack_start(file_chooser, False)
    file_chooser.connect('current-folder-changed', self.file_chooser_set)

    self.nbook.append_page(left_vbox, gtk.Label(_("Left Click")))

    #Middle click
    mid_vbox = gtk.VBox(False, 12)
    mid_vbox.set_border_width(12)

    action_vbox = gtk.VBox()
    mid_vbox.pack_start(action_vbox, False)

    label = gtk.Label()
    label.set_markup('<b>%s</b>' % _("Action"))
    label.set_alignment(0.0, 0.5)
    action_vbox.pack_start(label, False)

    vbox = gtk.VBox()

    align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
    align.set_padding(0, 0, 6, 0)
    align.add(vbox)
    action_vbox.pack_start(align, False)

    keys = {'display': _("Display dialog/docklet"), 'open': _("Open the folder"),
      'nothing': _("Nothing")}
    radios = []

    for key in ('display', 'open', 'nothing'):
      radio = gtk.RadioButton(None, keys[key])
      radios.append(radio)
      radio.identifier = 'mmb.' + key
      vbox.pack_start(radio)

      if key == 'open':
        radio.set_group(radios[0])
        radio.set_active(self.mmb == 2)

      elif key == 'nothing':
        radio.set_group(radios[0])
        radio.set_active(self.mmb == 3)

      radio.connect('toggled', self.radio_toggled)

    #Folder
    folder_vbox = gtk.VBox()
    mid_vbox.pack_start(folder_vbox, False)

    label = gtk.Label()
    label.set_markup('<b>%s</b>' % _("Folder"))
    label.set_alignment(0.0, 0.5)
    folder_vbox.pack_start(label, False)

    vbox = gtk.VBox()

    align = gtk.Alignment(0.0, 0.0, 1.0, 0.0)
    align.set_padding(0, 0, 6, 0)
    align.add(vbox)
    folder_vbox.pack_start(align, False)

    file_chooser = gtk.FileChooserButton(_("Choose a folder"))
    self.mmb_chooser = file_chooser
    file_chooser.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)

    if self.mmb_path is None or self.mmb_path.strip() == '' or not os.path.exists(self.mmb_path):
      file_chooser.set_filename(os.environ['HOME'] + '/')

    else:
      file_chooser.set_filename(self.mmb_path)

    vbox.pack_start(file_chooser, False)
    file_chooser.connect('current-folder-changed', self.file_chooser_set)

    self.nbook.append_page(mid_vbox, gtk.Label(_("Middle Click")))

    #Now for a close button - no apply button needed since everything is done instantly
    close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
    close_button.connect('clicked',lambda a:self.window.destroy())

    #HButtonBox
    hbbox = gtk.HButtonBox()
    hbbox.set_layout(gtk.BUTTONBOX_END)
    hbbox.pack_end(close_button, False, False, 5)

    #Now for a main table
    main_vbox = gtk.VBox(False, 12)
    main_vbox.pack_start(self.nbook, True, True)
    main_vbox.pack_start(hbbox, False, False)

    #Put it all together
    self.window.add(main_vbox)
    self.window.set_border_width(12)
    self.window.show_all()
    self.initializing = False

  def file_chooser_set(self, widget):
    if widget == self.lmb_chooser:
      self.client.set_string(group, 'lmb_path', widget.get_filename())

    else:
      self.client.set_string(group, 'mmb_path', widget.get_filename())

  #Determines what radio button was selected and changes awncc and other important things
  def radio_toggled(self,radio):
    if self.initializing:
      return False

    #No need to do anything if a radio is unselected
    if not radio.get_active():
      return False

    #Now do what is needed based on the radio's identifier
    #Tab: General; Section: File Browser; Radio: xdg-open (default)
    fbs = {'general.fb.default': 'xdg-open', 'general.fb.nautilus': 'nautilus',
      'general.fb.thunar': 'thunar', 'general.fb.konqueror': 'konqueror',
      'general.fb.dolphin': 'dolphin'}
    if radio.identifier in fbs:
      self.custom_entry.set_sensitive(False)
      self.custom_entry.set_text(fbs[radio.identifier])
      self.client.set_string(group, 'fb', fbs[radio.identifier])

    #custom file browser
    elif radio.identifier == 'general.fb.custom':
      self.custom_entry.set_sensitive(True)
      self.client.set_string(group, 'fb', self.custom_entry.get_text())

    elif radio.identifier == 'lmb.display':
      self.client.set_int(group, 'lmb', 1)

    elif radio.identifier == 'lmb.open':
      self.client.set_int(group, 'lmb', 2)

    elif radio.identifier == 'lmb.nothing':
      self.client.set_int(group, 'lmb', 3)

    elif radio.identifier == 'mmb.display':
      self.client.set_int(group, 'mmb', 1)

    elif radio.identifier == 'mmb.open':
      self.client.set_int(group, 'mmb', 2)

    elif radio.identifier == 'mmb.nothing':
      self.client.set_int(group, 'mmb', 3)

  #Determines what check button was selected and changes awncc and other important things
  def check_toggled(self, check):
    #No need to do this when everything is loading
    if self.initializing:
      return False

    keys = ('home', 'filesystem', 'local', 'network', 'connect', 'bookmarks')

    #Tab: Dialog; Section: Places; Checkbox: Show all places
    if check.identifier == 'places.all':
      if check.get_active():
        for widget in self.places_checks.values():
          widget.set_active(True)

      else:
        if not self.ignore_all:
          self.no_check_all = True
          for widget in self.places_checks.values():
            widget.set_active(False)
          self.no_check_all = False

        else:
          all_active = True
          for widget in self.places_checks.values():
            if not widget.get_active():
              all_active = False
              break

          if all_active:
            for widget in self.places_checks.values():
              widget.set_active(False)
          self.ignore_all = False

    elif check.identifier[:7] == 'places.':
      key = check.identifier[7:]
      if self.places_checks[key].get_active():
        self.client.set_int(group, 'show_' + key, 2)

        all_active = True
        for widget in self.places_checks.values():
          if not widget.get_active():
            all_active = False
            break

        if all_active:
          self.places_all.set_active(True)

      else:
        self.client.set_int(group, 'show_' + key, 1)
        self.ignore_all = True
        self.places_all.set_active(False)
        self.ignore_all = False

    elif check.identifier == 'general.docklet':
      self.client.set_bool(group, 'docklet', check.get_active())
      self.focus_check.set_sensitive(not check.get_active())
      self.open_check.set_sensitive(not check.get_active())

    #Tab: Dialog; Section: Behavior; Checkbox: Focus
    elif check.identifier == 'general.focus':
      if check.get_active():
        self.client.set_int(group, 'focus_entry', 2)
      else:
        self.client.set_int(group, 'focus_entry', 1)

    #Tab: Dialog; Section: Behavior; Checkbox: Open place
    elif check.identifier == 'general.open':
      if check.get_active():
        self.client.set_int(group, 'places_open', 2)
      else:
        self.client.set_int(group, 'places_open', 1)
