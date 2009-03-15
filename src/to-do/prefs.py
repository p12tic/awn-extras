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
#To-Do List Applet
#Preferences dialog file

import pygtk
pygtk.require('2.0')
import gtk
import pango
import gettext
import locale

from awn.extras import defs

APP = "awn-extras-applets"
gettext.bindtextdomain(APP, defs.GETTEXTDIR)
gettext.textdomain(APP)
_ = gettext.gettext

icon_colors_real = ['custom', 'gtk', 'butter', 'chameleon', 'orange', \
  'skyblue', 'plum', 'chocolate', 'scarletred', 'aluminium1', 'aluminium2']
icon_colors_human = [_('Custom'), _('Current Theme'), _('Butter'), \
  _('Chameleon'), _('Orange'), _('Sky Blue'), _('Plum'), _('Chocolate'), \
  _('Scarlet Red'), _('Aluminium 1'), _('Aluminium 2')]

icon_types_real = ['items', 'progress', 'progress-items']
icon_types_human = [_('Number of Items'), _('Progress'), _('Both')]

class Prefs:
  def __init__(self, settings):
    self.settings = settings
    
    #Make the main window
    self.win = gtk.Window()
    self.win.set_title(_('To-Do List Preferences'))
    
    #Get the default icon [theme]
    self.icon_theme = gtk.icon_theme_get_default()
    self.icon_theme.connect('changed', self.icon_theme_changed)
    icon = self.icon_theme.load_icon('view-sort-descending', 48, 48)
    
    #Get the window's icon
    self.win.set_icon(icon)
    
    #Make the main GtkNotebook along with three main widgets and two Labels
    notebook = gtk.Notebook()
    general_align = gtk.Alignment(xscale=1.0)
    priority_align = gtk.Alignment(xscale=1.0)
    icon_align = gtk.Alignment(xscale=1.0)
    general_label = gtk.Label(_('General'))
    priority_label = gtk.Label(_('Priority'))
    icon_label = gtk.Label(_('Icon'))

    notebook.append_page(general_align, general_label)
    notebook.append_page(priority_align, priority_label)
    notebook.append_page(icon_align, icon_label)

    main_vbox = gtk.VBox(False, 6)
    main_vbox.pack_start(notebook)
    
    #Label: Title (bold)
    title_label = gtk.Label(_('Title'))
    title_label.modify_font(pango.FontDescription('bold'))
    title_label.set_alignment(0.0, 0.5)

    #GtkAlignment for the entry
    title_align = gtk.Alignment(xscale=1.0)
    title_align.set_padding(0, 0, 10, 0)

    #Entry for Title
    title_entry = gtk.Entry()
    title_entry.set_text(self.settings['title'])
    title_entry.connect('focus-out-event', self.update)
    
    #Label: Confirm when removing... (bold)
    confirm_label = gtk.Label(_('Confirm when removing...'))
    confirm_label.modify_font(pango.FontDescription('bold'))
    confirm_label.set_alignment(0.0, 0.5)

    #GtkAlignment for the checkbuttons
    confirm_align = gtk.Alignment()
    confirm_align.set_padding(0, 0, 10, 0)

    #CheckButton: Items
    confirm_items = gtk.CheckButton(_('_Items'))
    confirm_items.key = 'confirm-items'
    if self.settings['confirm-items']:
      confirm_items.set_active(True)
    confirm_items.connect('toggled', self.check_toggled)
    
    #CheckButton: Categories
    confirm_cats = gtk.CheckButton(_('C_ategories'))
    confirm_cats.key = 'confirm-categories'
    if self.settings['confirm-categories']:
      confirm_cats.set_active(True)
    confirm_cats.connect('toggled', self.check_toggled)
    
    #Label: Width (bold)
    width_label = gtk.Label(_('Width'))
    width_label.modify_font(pango.FontDescription('bold'))
    width_label.set_alignment(0.0, 0.5)

    #GtkAlignment for the widgets
    width_align = gtk.Alignment(xscale=1.0)
    width_align.set_padding(0, 0, 10, 0)

    #CheckButton: Use Custom Width
    width_check = gtk.CheckButton(_('_Use Custom Width'))
    if self.settings['use_custom_width'] == True:
      width_check.set_active(True)
    width_check.key = 'use_custom_width'
    width_check.connect('toggled', self.check_toggled)
    
    #Label: Width (pixels)
    width_label2 = gtk.Label(_('Width (pixels)'))
    width_label2.set_alignment(0.0, 0.5)
    
    #SpinButton for custom width in pixels
    width_adj = gtk.Adjustment(float(self.settings['custom_width']), 25, 500, \
      1, 5, 1)
    width_spin = gtk.SpinButton(width_adj, 1, 0)
    width_spin.key = 'custom_width'
    width_spin.connect('focus-out-event', self.spin_focusout)
    
    #Put the General tab together
    title_align.add(title_entry)

    title_vbox = gtk.VBox()
    title_vbox.pack_start(title_label, False)
    title_vbox.pack_start(title_align, False)

    confirm_align_vbox = gtk.VBox()
    confirm_align_vbox.pack_start(confirm_items, False)
    confirm_align_vbox.pack_start(confirm_cats, False)
    confirm_align.add(confirm_align_vbox)

    confirm_vbox = gtk.VBox()
    confirm_vbox.pack_start(confirm_label, False)
    confirm_vbox.pack_start(confirm_align, False)

    width_hbox = gtk.HBox()
    width_hbox.pack_start(width_label2)
    width_hbox.pack_end(width_spin, False)

    width_align_vbox = gtk.VBox()
    width_align_vbox.pack_start(width_check)
    width_align_vbox.pack_start(width_hbox)
    width_align.add(width_align_vbox)

    width_vbox = gtk.VBox()
    width_vbox.pack_start(width_label, False)
    width_vbox.pack_start(width_align, False)

    general_vbox = gtk.VBox()
    general_vbox.pack_start(title_vbox, False, False, 6)
    general_vbox.pack_start(confirm_vbox, False, False, 6)
    general_vbox.pack_start(width_vbox, False, False, 6)

    general_align.set_padding(0, 0, 12, 12)
    general_align.add(general_vbox)
    
    #Label: Low Priority (bold)
    priority_low_label = gtk.Label(_('Low Priority'))
    priority_low_label.modify_font(pango.FontDescription('bold'))
    priority_low_label.set_alignment(0.0, 0.5)

    #GtkAlignment
    priority_low_align = gtk.Alignment(xscale=1.0)
    priority_low_align.set_padding(0, 0, 10, 0)

    #Low Priority Colors
    priority_low_background = self.color2('low')
    priority_low_text = self.color2('low', True)
    
    #Label: Medium Priority (bold)
    priority_med_label = gtk.Label(_('Medium Priority'))
    priority_med_label.modify_font(pango.FontDescription('bold'))
    priority_med_label.set_alignment(0.0, 0.5)

    #GtkAlignment
    priority_med_align = gtk.Alignment(xscale=1.0)
    priority_med_align.set_padding(0, 0, 10, 0)

    #Medium Priority Colors
    priority_med_background = self.color2('med')
    priority_med_text = self.color2('med', True)
    
    #Label: High Priority (bold)
    priority_high_label = gtk.Label(_('High Priority'))
    priority_high_label.modify_font(pango.FontDescription('bold'))
    priority_high_label.set_alignment(0.0, 0.5)

    #GtkAlignment
    priority_high_align = gtk.Alignment(xscale=1.0)
    priority_high_align.set_padding(0, 0, 10, 0)

    #High Priority Colors
    priority_high_background = self.color2('high')
    priority_high_text = self.color2('high', True)
    
    #Put the Priority tab together
    low_align_vbox = gtk.VBox()
    low_align_vbox.pack_start(priority_low_background, False)
    low_align_vbox.pack_start(priority_low_text, False)
    priority_low_align.add(low_align_vbox)

    low_vbox = gtk.VBox()
    low_vbox.pack_start(priority_low_label, False)
    low_vbox.pack_start(priority_low_align, False)

    med_align_vbox = gtk.VBox()
    med_align_vbox.pack_start(priority_med_background, False)
    med_align_vbox.pack_start(priority_med_text, False)
    priority_med_align.add(med_align_vbox)

    med_vbox = gtk.VBox()
    med_vbox.pack_start(priority_med_label, False)
    med_vbox.pack_start(priority_med_align, False)

    high_align_vbox = gtk.VBox()
    high_align_vbox.pack_start(priority_high_background, False)
    high_align_vbox.pack_start(priority_high_text, False)
    priority_high_align.add(high_align_vbox)

    high_vbox = gtk.VBox()
    high_vbox.pack_start(priority_high_label, False)
    high_vbox.pack_start(priority_high_align, False)

    priority_vbox = gtk.VBox()
    priority_vbox.pack_start(low_vbox, False, False, 6)
    priority_vbox.pack_start(med_vbox, False, False, 6)
    priority_vbox.pack_start(high_vbox, False, False, 6)

    priority_align.set_padding(0, 0, 12, 12)
    priority_align.add(priority_vbox)

    #Set up the GtkAlignment for this tab
    icon_align.set_padding(0, 0, 12, 12)

    #Label: Icon Color (bold)
    icon_color_label = gtk.Label(_('Icon Color'))
    icon_color_label.modify_font(pango.FontDescription('bold'))
    icon_color_label.set_alignment(0.0, 0.5)

    #GtkAlignment
    icon_color_align = gtk.Alignment(xscale=1.0)
    icon_color_align.set_padding(0, 0, 10, 0)

    #ComboBox for Icon Color
    liststore = gtk.ListStore(str)
    for color in icon_colors_human:
      liststore.append([color])
    index = icon_colors_real.index(self.settings['color'])
    
    color_cb = gtk.ComboBox(liststore)
    color_cb.set_active(index)
    cell = gtk.CellRendererText()
    color_cb.pack_start(cell, True)
    color_cb.add_attribute(cell, 'text', 0)
    color_cb.key = 'color'
    color_cb.connect('changed', self.cb_changed)
    
    #Label: Custom Colors (bold)
    custom_colors_label = gtk.Label(_('Custom Colors'))
    custom_colors_label.modify_font(pango.FontDescription('bold'))
    custom_colors_label.set_alignment(0.0, 0.5)

    #GtkAlignment
    custom_colors_align = gtk.Alignment(xscale=1.0)
    custom_colors_align.set_padding(0, 0, 10, 0)

    #Colors: Outer Border, Inner Border, Main Color, Text Color
    outer_border = self.color(_('Outer Border'), 0)
    inner_border = self.color(_('Inner Border'), 3)
    main_color = self.color(_('Main'), 6)
    text_color = self.color(_('Text'), 9)
    
    #Label: Icon Type (bold)
    icon_type_label = gtk.Label(_('Icon Type'))
    icon_type_label.modify_font(pango.FontDescription('bold'))
    icon_type_label.set_alignment(0.0, 0.5)

    #GtkAlignment
    icon_type_align = gtk.Alignment(xscale=1.0)
    icon_type_align.set_padding(0, 0, 10, 0)

    #ComboBox: Icon Type: Number of Items, Progress, Both
    liststore = gtk.ListStore(str)
    for _type in icon_types_human:
      liststore.append([_type])
    index = icon_types_real.index(self.settings['icon-type'])
    
    _type_cb = gtk.ComboBox(liststore)
    _type_cb.set_active(index)
    cell = gtk.CellRendererText()
    _type_cb.pack_start(cell, True)
    _type_cb.add_attribute(cell, 'text', 0)
    _type_cb.key = 'icon-type'
    _type_cb.connect('changed', self.cb_changed)
    
    #Put the Icon tab together
    icon_color_align.add(color_cb)

    icon_color_vbox = gtk.VBox()
    icon_color_vbox.pack_start(icon_color_label, False)
    icon_color_vbox.pack_start(icon_color_align, False)

    custom_colors_align_vbox = gtk.VBox()
    custom_colors_align_vbox.pack_start(outer_border, False)
    custom_colors_align_vbox.pack_start(inner_border, False)
    custom_colors_align_vbox.pack_start(main_color, False)
    custom_colors_align_vbox.pack_start(text_color, False)
    custom_colors_align.add(custom_colors_align_vbox)

    custom_colors_vbox = gtk.VBox()
    custom_colors_vbox.pack_start(custom_colors_label, False)
    custom_colors_vbox.pack_start(custom_colors_align, False)

    icon_type_align.add(_type_cb)

    icon_type_vbox = gtk.VBox()
    icon_type_vbox.pack_start(icon_type_label, False)
    icon_type_vbox.pack_start(icon_type_align, False)

    icon_vbox = gtk.VBox()
    icon_vbox.pack_start(icon_color_vbox, False, False, 6)
    icon_vbox.pack_start(custom_colors_vbox, False, False, 6)
    icon_vbox.pack_start(icon_type_vbox, False, False, 6)
    icon_align.add(icon_vbox)

    #Close button
    close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
    close_button.connect('clicked', self.close)
    
    #HButtonBox so the close button doesn't take the entire width
    close_hbbox = gtk.HButtonBox()
    close_hbbox.set_layout(gtk.BUTTONBOX_END)
    close_hbbox.pack_end(close_button, False)
    
    #Show the window
    main_vbox.pack_start(close_hbbox)
    self.win.add(main_vbox)
    self.win.set_border_width(6)
    self.win.show_all()
  
  #A value was updated
  def update(self, widget, event):
    self.settings['title'] = widget.get_text()
  
  #A color was set from a GtkColorButton
  def color_set(self, button):
    #Get the color from the button
    color = button.get_color()
    red, blue, green = color.red, color.blue, color.green
    
    #Set the color appropriately
    li = self.settings['colors'][0:]
    li[button.index] = red / 256
    li[(button.index+1)] = green / 256
    li[(button.index+2)] = blue / 256
    self.settings['colors'] = li
  
  #A color was set from a different GtkColorButton
  def color_set2(self, button):
    #Get the color from the button
    self.settings[button.key] = self.convert_color(button)
  
  #The icon theme has changed
  def icon_theme_changed(self, *args):
    icon = self.icon_theme.load_icon('view-sort-descending', 48, 48)
    self.win.set_icon(icon)
  
  #A color or icon type was selected from the ComboBox
  def cb_changed(self, widget):
    index = widget.get_active()
    if widget.key == 'color':
      self.settings['color'] = icon_colors_real[index]
    else:
      self.settings['icon-type'] = icon_types_real[index]
  
  #A CheckButton was toggled
  def check_toggled(self, widget):
    self.settings[widget.key] = widget.get_active()
  
  #A SpinButton has lost focus
  def spin_focusout(self, widget, event):
    self.settings[widget.key] = int(widget.get_value())
  
  #The close button was clicked
  def close(self, widget):
    self.win.destroy()
    del self.win
  
  #Return an HBox of: GtkLabel, GtkColorButton
  def color(self, human, index):
    
    #Make a GtkLabel
    label = gtk.Label(human)
    label.set_alignment(0.0, 0.5)
    
    #Get the default color
    if len(self.settings['colors']) < 12:
      self.settings['colors'] = [255, 255, 255, 127, 127, 127, 0, 0, 0, \
        255, 255, 255]
    
    color = self.settings['colors'][index:(index+3)]
    color[0] *= 256
    color[1] *= 256
    color[2] *= 256
    color = gtk.gdk.Color(*color)
    
    #Make a GtkColorButton
    button = gtk.ColorButton(color)
    button.index = index
    button.connect('color-set', self.color_set)
    
    #HBox for the two widgets
    hbox = gtk.HBox()
    hbox.pack_start(label)
    hbox.pack_end(button, False)
    
    #Return the HBox
    return hbox
  
  #Return an HBox of: GtkLabel, GtkColorButton
  def color2(self, key, text=False):
    
    key = 'color_' + key
    if text:
      key += '_text'
    
    #Make a GtkLabel
    if not text:
      label = gtk.Label(_('Background'))
    else:
      label = gtk.Label(_('Text'))

    label.set_alignment(0.0, 0.5)

    #Get a GdkColor
    color = gtk.gdk.color_parse(self.settings[key])
    
    #Make a GtkColorButton
    button = gtk.ColorButton(color)
    button.key = key
    button.connect('color-set', self.color_set2)
    
    #HBox for the two widgets
    hbox = gtk.HBox()
    hbox.pack_start(label)
    hbox.pack_end(button, False)
    
    #Return it
    return hbox
  
  #GtkColorButton -> 'RRGGBB'
  def convert_color(self, button):
    color = button.get_color()
    
    #RR
    if color.red == 0:
      s = '00'
    else:
      s = '%0.2X' % (color.red / 256.0)
    
    #GG
    if color.green == 0:
      s += '00'
    else:
      s += '%0.2X' % (color.green / 256.0)
    
    #BB
    if color.blue == 0:
      s += '00'
    else:
      s += '%0.2X' % (color.blue / 256.0)
    
    return '#' + s
