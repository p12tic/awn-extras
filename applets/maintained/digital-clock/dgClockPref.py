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
        'orientation': (gtk.Orientation, 'dock orientation',
                        'The orientation of the dock (horizontal/vertical)',
                        gtk.ORIENTATION_HORIZONTAL,
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
        self.on_applet_pos_changed(self.applet, self.applet.props.position)
        self.applet.connect('position-changed', self.on_applet_pos_changed)
        self.menu = self.build_menu()
        self.window = None

    def on_applet_pos_changed(self, applet, pos):
        if pos in (gtk.POS_TOP, gtk.POS_BOTTOM):
           self.props.orientation = gtk.ORIENTATION_HORIZONTAL
        else:
           self.props.orientation = gtk.ORIENTATION_VERTICAL

    def date_before_time_enabled(self):
        return self.props.date_before_time and \
               self.props.orientation == gtk.ORIENTATION_HORIZONTAL

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


class HRadioGroup(gtk.Frame):

    def __init__(self, label=None):
        super(HRadioGroup, self).__init__(label)
        self.hbox = gtk.HBox(5, False)
        super(HRadioGroup, self).add(self.hbox)
        self.buttons = []
        self.connect('notify::sensitive', self.on_sensitive_changed)

    def add_radio(self, label=None, use_underline=True, signals={},
                  active=None):
        group = None
        if len(self.buttons) > 0:
            group = self.buttons[0]
        radio = gtk.RadioButton(group=group, label=label, use_underline=use_underline)
        for signal, args in signals.iteritems():
            radio.connect(signal, *args)
        self.hbox.add(radio)
        self.buttons.append(radio)
        return radio

    def on_sensitive_changed(self, pspec):
        for button in self.buttons:
            button.props.sensitive = self.props.sensitive


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
        self.prefs.connect('notify::orientation', self.on_orient_changed)

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
        clock_type = HRadioGroup('Clock Type')
        clock_type.add_radio('_12 Hour',
                signals={'toggled': (self.radiobutton_changed,
                                     'twelve_hour')})
        clock_type.add_radio('_24 Hour',
                active=not self.prefs.props.twelve_hour)
        table.attach(clock_type, 0, 2, 3, 4)
        # * clock style: time beside date
        self.clock_style = HRadioGroup('Date Position')
        self.clock_style.add_radio('_Left',
               signals={'toggled': (self.radiobutton_changed,
                                    'date_before_time')})
        self.clock_style.add_radio('_Bottom',
               active=not self.prefs.props.date_before_time)
        table.attach(self.clock_style, 0, 2, 4, 5)
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

    def on_orient_changed(self, prefs, pspec):
        self.clock_style.props.sensitive = \
                (prefs.props.orientation == gtk.ORIENTATION_HORIZONTAL)

# vim:ts=4:sts=4:sw=4:et:ai:cindent
