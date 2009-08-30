#
# Copyright Ryan Rushton  ryan@rrdesign.ca
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA

import os
import re
import subprocess
import time

import gobject
from desktopagnostic import Color, config
import gtk
import awn


class ClockPrefs(gobject.GObject):

    # not using gobject.property because of
    # http://bugzilla.gnome.org/show_bug.cgi?id=593241
    __gproperties__ = {
        'date_before_time': (bool, 'date before time',
                             'Whether to show the date next to the time, instead of below it.',
                             False,
                             gobject.PARAM_READWRITE),
        'twelve_hour': (bool, '12 hour mode',
                        'Whether to show the time in 12 hour mode (as opposed to 24 hour mode).',
                        False,
                        gobject.PARAM_READWRITE),
        'font_face': (str, 'Font face',
                      'The font face for the date and time text.',
                      'Sans 10',
                      gobject.PARAM_READWRITE),
        'font_color': (Color, 'Font color',
                       'The text color of the date and time.',
                       gobject.PARAM_READWRITE),
        'font_shadow_color': (Color, 'Font shadow color',
                              'The font shadow color of the date and time.',
                              gobject.PARAM_READWRITE),
        'panel_size': (int, 'Panel size',
                       'The size of the panel (needed for rendering the date/time).',
                       0, 1000, 48, # FIXME use realistic min/max values
                       gobject.PARAM_READWRITE)}

    __alpha = {
        'font_color': 0,
        'font_shadow_color': 0xcccc
        }

    pref_map = {
      'dbt': 'date-before-time',
      'hour12': 'twelve-hour',
      'font_face': 'font-face',
      'font_color': 'font-color',
      'font_shadow_color': 'font-shadow-color'}

    def do_get_property(self, param):
        attr = '__%s' % param.name.replace('-', '_')
        return getattr(self, attr, None)

    def do_set_property(self, param, value):
        attr = '__%s' % param.name.replace('-', '_')
        setattr(self, attr, value)

    def __init__(self, applet):
        super(ClockPrefs, self).__init__()
        self.applet = applet
        self.config = awn.config_get_default_for_applet(self.applet)
        for key, prop in self.pref_map.iteritems():
            self.config.bind(config.GROUP_DEFAULT, key,
                             self, prop, False, config.BIND_METHOD_FALLBACK)
        self.panel_config = awn.config_get_default(awn.PANEL_ID_DEFAULT)
        self.panel_config.bind('panel', 'size', self, 'panel_size', True,
                               config.BIND_METHOD_FALLBACK)
        self.menu = self.build_menu()
        self.window = None

    def build_image_menu_item(self, menu, icon_name, activate_callback, label=None):
        if label is None:
            item = gtk.ImageMenuItem(icon_name)
        else:
            item = awn.image_menu_item_new_with_label(label)
            item.set_image(gtk.image_new_from_stock(icon_name, gtk.ICON_SIZE_MENU))
        item.connect('activate', activate_callback)
        menu.append(item)

    def build_menu(self):
        popup_menu = self.applet.create_default_menu()

        self.build_image_menu_item(popup_menu, gtk.STOCK_COPY,
                                   self.copy_time,
                                   'Copy Time')
        self.build_image_menu_item(popup_menu, gtk.STOCK_COPY,
                                   self.copy_date,
                                   'Copy Date')
        self.build_image_menu_item(popup_menu, gtk.STOCK_PREFERENCES,
                                   self.show_prefs)
        self.build_image_menu_item(popup_menu, gtk.STOCK_EDIT,
                                   self.time_admin,
                                   'Adjust Date & Time')

        popup_menu.show_all()
        return popup_menu

    def show_prefs(self, widget):
        if self.window is None:
            self.window = PrefsDialog(self)
        self.window.show_all()

    def color_changed(self, color_btn, prop):
        # alpha is not used yet
        #clr = Color(color_btn.get_color(), color_btn.get_alpha())
        clr = Color(color_btn.get_color(), self.__alpha[prop])
        setattr(self.props, prop, clr)

    def copy_date(self, widget):
        cb = gtk.Clipboard()
        txt = time.strftime('%A, %B %d, %Y')
        cb.set_text(txt)

    def copy_time(self, widget):
        cb = gtk.Clipboard()
        if self.props.twelve_hour:
            h = time.strftime('%I').lstrip('0')
            txt = h + time.strftime(':%M:%S %p')
        else:
            txt = time.strftime('%H:%M:%S')
        cb.set_text(txt)

    def time_admin(self, widget):
        subprocess.Popen('gksudo time-admin', shell=True)


class HFrame(gtk.Frame):
    def __init__(self, label=None):
        super(HFrame, self).__init__(label)
        self.hbox = gtk.HBox(5, False)
        super(HFrame, self).add(self.hbox)

    def add(self, child):
        self.hbox.add(child)


def mnemonic_label(mnemonic, widget):
    label = gtk.Label()
    label.set_text_with_mnemonic(mnemonic)
    label.set_mnemonic_widget(widget)
    return label


class PrefsDialog(gtk.Dialog):
    def __init__(self, prefs):
        title = '%s Preferences' % prefs.applet.props.display_name
        super(PrefsDialog, self).__init__(title, prefs.applet)
        self.prefs = prefs
        self.font_replace = None
        self.create_ui()
        # action button
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        self.connect('response', lambda dialog, response: dialog.hide())

    def create_ui(self):
        table = gtk.Table(5, 2)
        table.props.row_spacing = 5
        table.props.column_spacing = 5
        # * font face
        text_font_button = gtk.FontButton(self.prefs.props.font_face)
        text_font_button.connect('font-set', self.font_changed, 'font_face')
        text_font_label = mnemonic_label('Font _Face:', text_font_button)
        table.attach(text_font_label, 0, 1, 0, 1)
        table.attach(text_font_button, 1, 2, 0, 1)
        # * font color
        text_color = gtk.gdk.Color()
        self.prefs.props.font_color.get_color(text_color)
        text_color_button = gtk.ColorButton(text_color)
        text_color_button.connect('color-set', self.prefs.color_changed,
                                  'font_color')
        # TODO enable alpha support
        text_color_label = mnemonic_label('Font _Color:', text_color_button)
        table.attach(text_color_label, 0, 1, 1, 2)
        table.attach(text_color_button, 1, 2, 1, 2)
        # * font shadow color
        text_shadow_color = gtk.gdk.Color()
        self.prefs.props.font_shadow_color.get_color(text_shadow_color)
        text_shadow_color_button = gtk.ColorButton(text_shadow_color)
        text_shadow_color_button.connect('color-set', self.prefs.color_changed,
                                         'font_shadow_color')
        # TODO enable alpha support
        text_shadow_color_label = mnemonic_label('Font _Shadow Color:',
                                                 text_color_button)
        table.attach(text_shadow_color_label, 0, 1, 2, 3)
        table.attach(text_shadow_color_button, 1, 2, 2, 3)
        # * clock type: 12/24 hour
        clock_type_frame = HFrame('Clock Type')
        clock_type_12 = gtk.RadioButton(label='_12 Hour')
        clock_type_frame.add(clock_type_12)
        clock_type_12.connect('toggled', self.radiobutton_changed,
                              'twelve_hour')
        clock_type_24 = gtk.RadioButton(clock_type_12, '_24 Hour')
        clock_type_frame.add(clock_type_24)
        clock_type_24.props.active = not self.prefs.props.twelve_hour
        table.attach(clock_type_frame, 0, 2, 3, 4)
        # * clock style: time beside date
        clock_style_frame = HFrame('Date Position')
        clock_style_side = gtk.RadioButton(label='_Left')
        clock_style_frame.add(clock_style_side)
        clock_style_side.connect('toggled', self.radiobutton_changed,
                                 'date_before_time')
        clock_style_bottom = gtk.RadioButton(clock_style_side, '_Bottom')
        clock_style_frame.add(clock_style_bottom)
        clock_style_bottom.props.active = not self.prefs.props.date_before_time
        table.attach(clock_style_frame, 0, 2, 4, 5)
        self.vbox.add(table)

    def radiobutton_changed(self, check, prop):
        setattr(self.prefs.props, prop, check.get_active())

    def font_changed(self, font_btn, prop):
        font = self.clean_font_name(font_btn.get_font_name())
        setattr(self.prefs.props, prop, font)

    def clean_font_name(self, font_face):
        if self.font_replace is None:
            attrs = ['Condensed', 'Book', 'Oblique', 'Bold', 'Italic',
                     'Regular', 'Medium', 'Light']
            self.font_replace = re.compile('(?:%s ?)*[\d ]*$' % '|'.join(attrs))
        return self.font_replace.sub('', font_face)
