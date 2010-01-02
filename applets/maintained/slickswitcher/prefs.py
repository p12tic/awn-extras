#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2010 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import pygtk
pygtk.require('2.0')
import gtk
import pango
import awn

from desktopagnostic.config import GROUP_DEFAULT
from desktopagnostic.ui import ColorButton
from desktopagnostic import Color

from awn.extras import _


class Prefs:
    defaults = {}
    defaults['icon_border'] = '000000C0'
    defaults['width'] = 160
    defaults['height'] = 120
    defaults['normal_border'] = 'FFFFFF80'
    defaults['active_border'] = 'FFFFFFFF'
    defaults['window_main'] = 'CCCCCC66'
    defaults['window_border'] = '333333CC'
    defaults['use_custom'] = False
    defaults['custom_back'] = '000000'
    defaults['custom_border'] = 'FFFFFF'
    defaults['shine_top'] = 'FFFFFF5E'
    defaults['shine_bottom'] = 'FFFFFF3B'
    defaults['shine_hover_top'] = 'FFFFFF80'
    defaults['shine_hover_bottom'] = 'FFFFFF65'
    defaults['text_color'] = 'FFFFFFF3'
    defaults['shadow_color'] = '000000E6'
    defaults['background_mode'] = 'gnome'
    defaults['background_file'] = ''

    def __init__(self, applet):
        self.applet = applet

        #Get AwnConfigClient
        self.config = awn.config_get_default_for_applet(applet)

        #Make the main window
        self.win = gtk.Window()
        self.win.set_title(_("SlickSwitcher Preferences"))
        self.win.set_border_width(6)

        #Get the default icon theme
        self.icon_theme = gtk.icon_theme_get_default()

        #Get the window's icon
        image_path = '/'.join(__file__.split('/')[:-1]) + '/icons/'
        icon = gtk.gdk.pixbuf_new_from_file(image_path + 'done.png')
        self.win.set_icon(icon)

        #Main Widgets
        main_vbox = gtk.VBox(False, 6)
        colors_vbox = gtk.VBox(False, 6)
        other_colors_vbox = gtk.VBox(False, 6)
        advanced_vbox = gtk.VBox(False, 6)
        notebook = gtk.Notebook()

        colors_vbox.set_border_width(6)
        other_colors_vbox.set_border_width(6)
        advanced_vbox.set_border_width(6)

        #Colors: Borders, Windows, and Dialog

        #Border Colors
        label_border_colors = gtk.Label(_("Border Colors"))
        label_border_colors.set_alignment(0.0, 0.5)
        boldify(label_border_colors)
        image_border_colors = gtk.image_new_from_file(image_path + 'border.png')

        #Icon Border
        icon_border = self.make_hbox(_("Icon border:"), 'icon_border')

        #Normal Border
        normal_border = self.make_hbox(_("Normal border:"), 'normal_border')

        #Hovered Border
        active_border = self.make_hbox(_("Hovered border:"), 'active_border')

        #Window Colors
        label_window_colors = gtk.Label(_("Window Colors"))
        label_window_colors.set_alignment(0.0, 0.5)
        boldify(label_window_colors)
        image_window_colors = gtk.image_new_from_file(image_path + 'windows.png')

        #Main Color
        window_main = self.make_hbox(_("Main color:"), 'window_main')

        #Border Color
        window_border = self.make_hbox(_("Border color:"), 'window_border')

        #Dialog Colors
        label_dialog_colors = gtk.Label(_("Dialog colors"))
        label_dialog_colors.set_alignment(0.0, 0.5)
        boldify(label_dialog_colors)
        image_dialog_colors = gtk.image_new_from_file(image_path + 'dialog.png')

        #Use custom colors (CheckButton)
        check_dialog_colors = gtk.CheckButton(_("Use custom colors"))
        check_dialog_colors.key = 'use_custom'
        if self.config.get_value(GROUP_DEFAULT, 'use_custom') == True:
            check_dialog_colors.set_active(True)
        check_dialog_colors.connect('toggled', self.check_toggled)

        #Background Color
        dialog_back = self.make_hbox(_("Background color:"), 'custom_back')

        #Border Color
        dialog_border = self.make_hbox(_("Border color:"), 'custom_border')

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(icon_border)
        vbox.pack_start(normal_border)
        vbox.pack_start(active_border)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(image_border_colors, False)
        hbox.pack_start(vbox, True)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_border_colors, False)
        vbox.pack_start(hbox, False)

        colors_vbox.pack_start(vbox, False)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(window_main)
        vbox.pack_start(window_border)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(image_window_colors, False)
        hbox.pack_start(vbox, True)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_window_colors, False)
        vbox.pack_start(hbox, False)

        colors_vbox.pack_start(vbox, False)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(dialog_back, False)
        vbox.pack_start(dialog_border, False)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(image_dialog_colors, False)
        hbox.pack_start(vbox, True)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_dialog_colors, False)
        vbox.pack_start(check_dialog_colors, False)
        vbox.pack_start(hbox, False)

        colors_vbox.pack_start(vbox, False)

        notebook.append_page(colors_vbox, gtk.Label(_("Colors")))

        #Other colors: text and shine
        #Number Colors
        label_number_colors = gtk.Label(_("Number Colors"))
        label_number_colors.set_alignment(0.0, 0.5)
        boldify(label_number_colors)
        image_number_colors = gtk.image_new_from_file(image_path + 'number.png')

        #Use custom colors (CheckButton)
        check_text_colors = gtk.CheckButton(_("Use custom colors"))
        check_text_colors.key = 'use_custom_text'
        if self.config.get_value(GROUP_DEFAULT, 'use_custom_text') == True:
            check_text_colors.set_active(True)
        check_text_colors.connect('toggled', self.check_toggled)

        #Main Color
        text_color = self.make_hbox(_("Main color:"), 'text_color')

        #Drop-Shadow Color
        shadow_color = self.make_hbox(_("Drop-shadow color:"), 'shadow_color')

        #Shine Colors
        label_shine_colors = gtk.Label(_("Shine Colors"))
        label_shine_colors.set_alignment(0.0, 0.5)
        boldify(label_shine_colors)
        image_shine_colors = gtk.image_new_from_file(image_path + 'shine.png')

        #Top Color
        shine_top = self.make_hbox(_("Top color:"), 'shine_top')

        #Bottom Color
        shine_bottom = self.make_hbox(_("Bottom color:"), 'shine_bottom')

        #Hover Top Color
        shine_hover_top = self.make_hbox(_("Hover top color:"), 'shine_hover_top')

        #Hover Bottom Color
        shine_hover_bottom = self.make_hbox(_("Hover bottom color:"), 'shine_hover_bottom')

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(text_color)
        vbox.pack_start(shadow_color)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(image_number_colors, False)
        hbox.pack_start(vbox, True)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_number_colors, False)
        vbox.pack_start(check_text_colors, False)
        vbox.pack_start(hbox, False)

        other_colors_vbox.pack_start(vbox, False)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(shine_top)
        vbox.pack_start(shine_bottom)
        vbox.pack_start(shine_hover_top)
        vbox.pack_start(shine_hover_bottom)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(image_shine_colors, False)
        hbox.pack_start(vbox, True)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_shine_colors, False)
        vbox.pack_start(hbox, False)

        other_colors_vbox.pack_start(vbox, False)

        notebook.append_page(other_colors_vbox, gtk.Label(_("Other colors")))

        #Advanced: Workspace width & height, Background mode/file

        #Workspace Size...
        vbox = gtk.VBox(False, 3)

        #Width
        label_width = gtk.Label(_("Width:"))
        label_width.set_alignment(0.0, 0.5)
        width = self.config.get_value(GROUP_DEFAULT, 'width')
        if width < 24 or width > 250:
            width = 160
        width_adj = gtk.Adjustment(float(width), 24, 250, 5, 10, 0)
        width = gtk.SpinButton(width_adj, 1, 0)
        width.key = 'width'
        width.connect('focus-out-event', self.spinbutton_focusout)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(label_width, False)
        hbox.pack_end(width, False)

        vbox.pack_start(hbox, False)

        #Height
        label_height = gtk.Label(_("Height:"))
        label_height.set_alignment(0.0, 0.5)
        height = self.config.get_value(GROUP_DEFAULT, 'height')
        if height < 24 or height > 250:
            height = 110
        height_adj = gtk.Adjustment(float(height), 24, 250, 5, 10, 0)
        height = gtk.SpinButton(height_adj, 1, 0)
        height.key = 'height'
        height.connect('focus-out-event', self.spinbutton_focusout)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(label_height, False)
        hbox.pack_end(height, False)

        vbox.pack_start(hbox, False)

        align = gtk.Alignment(xscale=1.0)
        align.set_padding(0, 0, 12, 0)
        align.add(vbox)

        label_workspace_size = gtk.Label(_("Workspace Size"))
        label_workspace_size.set_alignment(0.0, 0.5)
        boldify(label_workspace_size)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_workspace_size, False)
        vbox.pack_start(align, False)

        advanced_vbox.pack_start(vbox, False)

        #Background...
        vbox = gtk.VBox(False, 3)

        size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        #Mode
        label_mode = gtk.Label(_("Mode:"))

        self.combo_mode = gtk.combo_box_new_text()
        self.combo_mode.append_text(_("GNOME"))
        self.combo_mode.append_text(_("Compiz Wallpaper Plugin"))
        self.combo_mode.append_text(_("File"))

        size_group.add_widget(self.combo_mode)

        mode = self.config.get_value(GROUP_DEFAULT, 'background_mode')
        if mode == 'compiz':
            self.combo_mode.set_active(1)
        elif mode == 'file':
            self.combo_mode.set_active(2)
        else:
            self.combo_mode.set_active(0)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(label_mode, False)
        hbox.pack_end(self.combo_mode, False)

        vbox.pack_start(hbox, False)

        #File
        label_file = gtk.Label(_("File:"))

        file_chooser = gtk.FileChooserButton(_("Choose a Background Image"))
        file_chooser.set_filename('')

        size_group.add_widget(file_chooser)

        self.file_hbox = gtk.HBox(False, 6)
        self.file_hbox.pack_start(label_file, False)
        self.file_hbox.pack_end(file_chooser, False)

        vbox.pack_start(self.file_hbox, False)

        align = gtk.Alignment(xscale=1.0)
        align.set_padding(0, 0, 12, 0)
        align.add(vbox)

        label_background = gtk.Label(_("Background"))
        label_background.set_alignment(0.0, 0.5)
        boldify(label_background)

        vbox = gtk.VBox(False, 3)
        vbox.pack_start(label_background, False)
        vbox.pack_start(align, False)

        vbox.set_sensitive(False)

        advanced_vbox.pack_start(vbox, False)

        notebook.append_page(advanced_vbox, gtk.Label(_("Advanced")))

        #Close button in an HButtonBox
        close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
        close_button.connect('clicked', self.close)
        hbox = gtk.HBox()
        hbox.pack_end(close_button, False)

        #Put it all together
        main_vbox.pack_start(notebook)
        main_vbox.pack_start(hbox, False)
        self.win.add(main_vbox)
        self.win.show_all()

    #A value was updated
    def update(self, widget, event):
        self.config.set_value(GROUP_DEFAULT, widget.key, widget.get_text())

    #The close button was clicked
    def close(self, widget):
        self.win.destroy()
        del self.win

    #A color was set
    def color_set(self, button):
        #Get the key and color
        key = button.key
        color = self.convert_color(button)

        #Set the new value
        self.config.set_value(GROUP_DEFAULT, key, color)

    #GtkColorButton -> 'RRGGBBAA'
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

        if button.use_alpha == True:
            #AA
            if button.get_alpha() == 0:
                s += '00'
            else:
                s += '%0.2X' % (button.get_alpha() / 256.0)

        return s

    def make_button(self, key):
        button = ColorButton.with_color(Color.from_string('#' + self.applet.settings[key]))

        button.key = key
        button.use_alpha = True
        button.connect('color-set', self.color_set)

        return button

    def make_hbox(self, text, key):
        label = gtk.Label(text)
        label.set_alignment(0.0, 0.5)
        button = self.make_button(key)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(label, False)
        hbox.pack_end(button, False)

        return hbox

    #A SpinButton widget has lost focus
    def spinbutton_focusout(self, widget, event):
        self.config.set_value(GROUP_DEFAULT, widget.key, int(widget.get_value()))

    #A CheckButton has been toggled
    def check_toggled(self, widget):
        self.config.set_value(GROUP_DEFAULT, widget.key, widget.get_active())

def boldify(label):
    label.modify_font(pango.FontDescription('bold'))
