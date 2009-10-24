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

    def __init__(self, applet):
        self.applet = applet

        #Get AwnConfigClient
        self.config = awn.config_get_default_for_applet(applet)

        #Make the main window
        self.win = gtk.Window()
        self.win.set_title(_('SlickSwitcher Preferences'))
        self.win.set_border_width(6)

        #Get the default icon theme
        self.icon_theme = gtk.icon_theme_get_default()

        #Get the window's icon
        image_path = '/'.join(__file__.split('/')[:-1]) + '/icons/'
        icon = gtk.gdk.pixbuf_new_from_file(image_path + 'done.png')
        self.win.set_icon(icon)

        #Main Widgets
        vbox = gtk.VBox(False, 6)
        colors_table = gtk.Table(2, 7)
        other_colors_table = gtk.Table(2, 8)
        size_table = gtk.Table(2, 3)
        notebook = gtk.Notebook()

        colors_table.set_border_width(6)
        other_colors_table.set_border_width(6)
        size_table.set_border_width(6)

        #Page 1 of notebook: Colors
        label_colors = gtk.Label(_('Colors'))

        #Border Colors
        label_border_colors = gtk.Label(_('Border Colors'))
        boldify(label_border_colors)
        image_border_colors = gtk.image_new_from_file(image_path + 'border.png')
        #Icon Border
        label_icon_border = gtk.Label(_('Icon Border'))
        icon_border = self.make_button('icon_border')
        #Normal Border
        label_normal_border = gtk.Label(_('Normal Border'))
        normal_border = self.make_button('normal_border')
        #Hovered Border
        label_active_border = gtk.Label(_('Hovered Border'))
        active_border = self.make_button('active_border')

        #Window Colors
        label_window_colors = gtk.Label(_('Window Colors'))
        boldify(label_window_colors)
        image_window_colors = gtk.image_new_from_file(image_path + 'windows.png')
        #Main Color
        label_window_main = gtk.Label(_('Main Color'))
        window_main = self.make_button('window_main')
        #Border Color
        label_window_border = gtk.Label(_('Border Color'))
        window_border = self.make_button('window_border')

        #Dialog Colors
        label_dialog_colors = gtk.Label(_('Dialog Colors'))
        boldify(label_dialog_colors)
        image_dialog_colors = gtk.image_new_from_file(image_path + 'dialog.png')
        #Use custom colors (CheckButton)
        check_dialog_colors = gtk.CheckButton(_('Use custom colors'))
        check_dialog_colors.key = 'use_custom'
        if self.config.get_value(GROUP_DEFAULT, 'use_custom') == True:
            check_dialog_colors.set_active(True)
        check_dialog_colors.connect('toggled', self.check_toggled)
        #Background Color
        label_dialog_back = gtk.Label(_('Background Color'))
        dialog_back = self.make_button('custom_back',)
        #Border Color
        label_dialog_border = gtk.Label(_('Border Color'))
        dialog_border = self.make_button('custom_border')

        #Add the first page to the notebook
        colors_table.attach(image_border_colors, 0, 1, 1, 4, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        colors_table.attach(label_border_colors, 0, 3, 0, 1, yoptions=gtk.SHRINK)
        colors_table.attach(label_icon_border, 1, 2, 1, 2, yoptions=gtk.SHRINK)
        colors_table.attach(icon_border, 2, 3, 1, 2, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        colors_table.attach(label_normal_border, 1, 2, 2, 3, yoptions=gtk.SHRINK)
        colors_table.attach(normal_border, 2, 3, 2, 3, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        colors_table.attach(label_active_border, 1, 2, 3, 4, yoptions=gtk.SHRINK)
        colors_table.attach(active_border, 2, 3, 3, 4, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        colors_table.attach(image_window_colors, 0, 1, 5, 7, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        colors_table.attach(label_window_colors, 0, 3, 4, 5, yoptions=gtk.SHRINK)
        colors_table.attach(label_window_main, 1, 2, 5, 6, yoptions=gtk.SHRINK)
        colors_table.attach(window_main, 2, 3, 5, 6, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        colors_table.attach(label_window_border, 1, 2, 6, 7, yoptions=gtk.SHRINK)
        colors_table.attach(window_border, 2, 3, 6, 7, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        colors_table.attach(label_dialog_colors, 0, 3, 7, 8, yoptions=gtk.SHRINK)
        colors_table.attach(image_dialog_colors, 0, 1, 8, 11, xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        colors_table.attach(check_dialog_colors, 1, 3, 8, 9, yoptions=gtk.SHRINK)
        colors_table.attach(label_dialog_back, 1, 2, 9, 10, yoptions=gtk.SHRINK)
        colors_table.attach(dialog_back, 2, 3, 9, 10, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        colors_table.attach(label_dialog_border, 1, 2, 10, 11, yoptions=gtk.SHRINK)
        colors_table.attach(dialog_border, 2, 3, 10, 11, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        notebook.append_page(colors_table, label_colors)

        #Other Colors
        label_other_colors = gtk.Label(_('Other Colors'))

        #Number Colors
        label_number_colors = gtk.Label(_('Number Colors'))
        boldify(label_number_colors)
        image_number_colors = gtk.image_new_from_file(image_path + 'number.png')
        #Main Color
        label_text_color = gtk.Label(_('Main Color'))
        text_color = self.make_button('text_color')
        #Drop-Shadow Color
        label_shadow_color = gtk.Label(_('Drop-Shadow Color'))
        shadow_color = self.make_button('shadow_color')

        #Shine Colors
        label_shine_colors = gtk.Label(_('Shine Colors'))
        boldify(label_shine_colors)
        image_shine_colors = gtk.image_new_from_file(image_path + 'shine.png')
        #Top Color
        label_shine_top = gtk.Label(_('Top Color'))
        shine_top = self.make_button('shine_top')
        #Bottom Color
        label_shine_bottom = gtk.Label(_('Bottom Color'))
        shine_bottom = self.make_button('shine_bottom')

        #Hover Top Color
        label_shine_hover_top = gtk.Label(_('Hover Top Color'))
        shine_hover_top = self.make_button('shine_hover_top')

        #Hover Bottom Color
        label_shine_hover_bottom = gtk.Label(_('Hover Bottom Color'))
        shine_hover_bottom = self.make_button('shine_hover_bottom')

        #Put the other colors together
        other_colors_table.attach(image_number_colors, 0, 1, 1, 3, \
            xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        other_colors_table.attach(label_number_colors, 0, 3, 0, 1, yoptions=gtk.SHRINK)
        other_colors_table.attach(label_text_color, 1, 2, 1, 2, yoptions=gtk.SHRINK)
        other_colors_table.attach(text_color, 2, 3, 1, 2, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        other_colors_table.attach(label_shadow_color, 1, 2, 2, 3, yoptions=gtk.SHRINK)
        other_colors_table.attach(shadow_color, 2, 3, 2, 3, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        other_colors_table.attach(image_shine_colors, 0, 1, 4, 8, \
            xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        other_colors_table.attach(label_shine_colors, 0, 3, 3, 4, yoptions=gtk.SHRINK)
        other_colors_table.attach(label_shine_top, 1, 2, 4, 5, yoptions=gtk.SHRINK)
        other_colors_table.attach(shine_top, 2, 3, 4, 5, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        other_colors_table.attach(label_shine_bottom, 1, 2, 5, 6, yoptions=gtk.SHRINK)
        other_colors_table.attach(shine_bottom, 2, 3, 5, 6, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        other_colors_table.attach(label_shine_hover_top, 1, 2, 6, 7, yoptions=gtk.SHRINK)
        other_colors_table.attach(shine_hover_top, 2, 3, 6, 7, \
            xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        other_colors_table.attach(label_shine_hover_bottom, 1, 2, 7, 8, yoptions=gtk.SHRINK)
        other_colors_table.attach(shine_hover_bottom, 2, 3, 7, 8, \
            xoptions=gtk.SHRINK, yoptions=gtk.SHRINK)
        notebook.append_page(other_colors_table, label_other_colors)

        #Size
        label_size = gtk.Label(_('Size'))

        #Width
        label_width = gtk.Label(_('Width'))
        width = self.config.get_value(GROUP_DEFAULT, 'width')
        if width < 24 or width > 250:
            width = 160
        width_adj = gtk.Adjustment(float(width), 24, 250, 5, 10, 0)
        width = gtk.SpinButton(width_adj, 1, 0)
        width.key = 'width'
        width.connect('focus-out-event', self.spinbutton_focusout)

        #Height
        label_height = gtk.Label(_('Height'))
        height = self.config.get_value(GROUP_DEFAULT, 'height')
        if height < 24 or height > 250:
            height = 110
        height_adj = gtk.Adjustment(float(height), 24, 250, 5, 10, 0)
        height = gtk.SpinButton(height_adj, 1, 0)
        height.key = 'height'
        height.connect('focus-out-event', self.spinbutton_focusout)

        #Note
        label_note = gtk.Label(_('Note: This does not affect\nthe size of the ' + \
            'applet icon.'))

        #Put the Size tab together
        size_table.attach(label_width, 0, 1, 0, 1, yoptions=gtk.SHRINK)
        size_table.attach(width, 1, 2, 0, 1, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        size_table.attach(label_height, 0, 1, 1, 2, yoptions=gtk.SHRINK)
        size_table.attach(height, 1, 2, 1, 2, xoptions=gtk.SHRINK, \
            yoptions=gtk.SHRINK)
        size_table.attach(label_note, 0, 2, 2, 3, yoptions=gtk.SHRINK)
        notebook.append_page(size_table, label_size)

        #Close button in an HButtonBox
        close_button = gtk.Button(stock=gtk.STOCK_CLOSE)
        close_button.connect('clicked', self.close)
        hbox = gtk.HBox()
        hbox.pack_end(close_button, False)

        #Put it all together
        vbox.pack_start(notebook)
        vbox.pack_start(hbox, False)
        self.win.add(vbox)
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

    #'RRGGBBAA' -> GtkColorButton
    def make_button(self, key):
        button = ColorButton.with_color(Color.from_string('#' + self.applet.settings[key]))

        button.key = key
        button.use_alpha = True
        button.connect('color-set', self.color_set)

        return button

    #A SpinButton widget has lost focus
    def spinbutton_focusout(self, widget, event):
        self.config.set_value(GROUP_DEFAULT, widget.key, int(widget.get_value()))

    #A CheckButton has been toggled
    def check_toggled(self, widget):
        self.config.set_value(GROUP_DEFAULT, widget.key, widget.get_active())

def boldify(label):
    label.modify_font(pango.FontDescription('bold'))
