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
import subprocess
import time

import gobject
from desktopagnostic import Color, config
import gtk
from gtk import glade
import awn


class ClockPrefs(gobject.GObject):

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

    # glade path
    glade_path = os.path.join((os.path.dirname(__file__)), 'pref.glade')

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
            self.config.bind(awn.CONFIG_GROUP_DEFAULT, key,
                             self, prop, False, config.BIND_METHOD_FALLBACK)
        self.panel_config = awn.config_get_default(awn.PANEL_ID_DEFAULT)
        self.panel_config.bind('panel', 'size', self, 'panel_size', True,
                               config.BIND_METHOD_FALLBACK)
        self.menu = self.build_menu()

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
        if not hasattr(self, 'wTree'):
            self.create_prefs_dialog()
        self.window.show_all()

    def create_prefs_dialog(self):
        self.wTree = glade.XML(self.glade_path)
        self.window = self.wTree.get_widget('main_window')

        close = self.wTree.get_widget('close_button')
        close.connect('clicked', self.close_prefs)

        font_btn = self.wTree.get_widget('fontface')
        font_btn.set_font_name(self.prefs['fontFace'])
        font_btn.connect('font-set', self.font_changed, 'font_face')

        color_btn = self.wTree.get_widget('fontcolor')
        color_btn.set_color(self.prefs['fontColor'])
        color_btn.connect('color-set', self.color_changed, 'font_color')

        scolor_btn = self.wTree.get_widget('shadowcolor')
        scolor_btn.set_color(self.prefs['fontShadowColor'])
        scolor_btn.set_use_alpha(False) # Not used yet
        scolor_btn.connect('color-set', self.color_changed,
                           'font_shadow_color')

        h12 = self.wTree.get_widget('hour12')
        h12.set_active(self.props.twelve_hour)
        h12.connect('toggled', self.set_bool, 'hour12')

        tbd = self.wTree.get_widget('timebesidedate')
        tbd.set_active(self.prefs['dateBeforeTime'])
        tbd.connect('toggled', self.set_bool, 'dbt')

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

    def close_prefs(self, btn):
        self.window.hide_all()

    def set_bool(self, check, prop):
        setattr(self.props, prop, check.get_active())

    def font_changed(self, font_btn, prop):
        font = self.clean_font_name(font_btn.get_font_name())
        setattr(self.props, prop, font)

    def color_changed(self, color_btn, prop):
        # alpha is not used yet
        #clr = Color(color_btn.get_color(), color_btn.get_alpha())
        clr = Color(color_btn.get_color(), self.__alpha[prop])
        setattr(self.props, prop, clr)

    def clean_font_name(self, fontface):
        rem = ['Condensed', 'Book', 'Oblique', 'Bold', 'Italic', 'Regular',
               'Medium', 'Light']
        for r in rem:
            fontface = fontface.replace(r, '')
            fontface = fontface.rstrip('0123456789 ')
        return fontface
