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
from desktopagnostic.gtk import ColorButton
import gtk
import awn
from awn.extras import _


class ClockPrefs(gobject.GObject):

    # not using gobject.property because of
    # http://bugzilla.gnome.org/show_bug.cgi?id=593241
    __gproperties__ = {
        'date_before_time': (bool, _('Date before time'),
                             _('Whether to show the date next to the time, instead of below it.'),
                             False,
                             gobject.PARAM_READWRITE),
        'twelve_hour': (bool, _('12 hour mode'),
                        _('Whether to show the time in 12 hour mode (as opposed to 24 hour mode).'),
                        False,
                        gobject.PARAM_READWRITE),
        'font_face': (str, _('Font face'),
                      _('The font face for the date and time text.'),
                      'Sans 10',
                      gobject.PARAM_READWRITE),
        'font_color': (Color, _('Font color'),
                       _('The text color of the date and time.'),
                       gobject.PARAM_READWRITE),
        'font_shadow_color': (Color, _('Font shadow color'),
                              _('The font shadow color of the date and time.'),
                              gobject.PARAM_READWRITE),
        'calendar_command': (str, _('Calendar command'),
                             _('Command to execute when a calendar day is double-clicked.'),
                             '', gobject.PARAM_READWRITE),
        'adjust_datetime_command': (str, _('Adjust date/time command'),
                                    _('Command to execute when the user wishes to adjust the date/time.'),
                                    '', gobject.PARAM_READWRITE),
        'orientation': (gtk.Orientation, _('dock orientation'),
                        _('The orientation of the dock (horizontal/vertical)'),
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

    cmd_pref_map = {
        'calendar': 'calendar_command',
        'adjust_datetime': 'adjust_datetime_command'
        }

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
        for key, prop in self.cmd_pref_map.iteritems():
            self.config.bind('commands', key, self, prop, False,
                             config.BIND_METHOD_FALLBACK)
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
                                   _('Copy Time'))
        self.build_image_menu_item(popup_menu, gtk.STOCK_COPY,
                                   self.copy_date,
                                   _('Copy Date'))
        self.build_image_menu_item(popup_menu, gtk.STOCK_PREFERENCES,
                                   self.show_prefs)
        self.build_image_menu_item(popup_menu, gtk.STOCK_EDIT,
                                   self.time_admin,
                                   _('Adjust Date & Time'))

        popup_menu.show_all()
        return popup_menu

    def show_prefs(self, widget):
        if self.window is None:
            self.window = PrefsDialog(self)
        self.window.show_all()

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
        subprocess.Popen(self.props.adjust_datetime_command, shell=True)


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


class CommandSelector:
    def __init__(self, label, prefs, options, property_name):
        model = gtk.ListStore(str, str)
        self.prefs = prefs
        self.prop = property_name
        self.dropdown = gtk.ComboBox(model)
        cell = gtk.CellRendererText()
        self.dropdown.pack_start(cell, True)
        self.dropdown.add_attribute(cell, 'text', 0)
        self.options = options
        self.option_map = {}
        value = getattr(prefs.props, self.prop)
        active_set = False
        idx = 0
        for option in options:
            model.append(option)
            self.option_map[option[1]] = idx
            if option[1] == value:
                self.dropdown.props.active = idx
                active_set = True
            idx += 1
        model.append([_('Custom'), None])
        self.custom = gtk.Entry()
        self.custom.props.sensitive = not active_set
        if not active_set:
            self.dropdown.props.active = len(self.options)
            self.custom.props.text = value
        self.label = mnemonic_label(label, self.dropdown)
        prefs.connect('notify::%s' % self.prop, self.on_prop_changed)
        self.dropdown.connect('changed', self.on_dropdown_changed)
        self.custom.connect('changed', self.on_custom_changed)

    def on_prop_changed(self, obj, pspec):
        value = getattr(self.prefs.props, self.prop)
        self.dropdown.active = self.option_map.get(value, len(self.options))

    def on_dropdown_changed(self, dropdown):
        idx = dropdown.props.active
        self.custom.props.sensitive = (idx == len(self.options))
        if self.custom.props.sensitive:
            if self.custom.props.text == '':
                self.custom.props.text = getattr(self.prefs.props, self.prop)
            self.custom.select_region(0, len(self.custom.props.text))
        else:
            active_iter = self.dropdown.get_active_iter()
            value = self.dropdown.props.model.get_value(active_iter, 1)
            setattr(self.prefs.props, self.prop, value)

    def on_custom_changed(self, entry):
        setattr(self.prefs.props, self.prop, entry.props.text)

    def attach_to_table(self, table, row):
        table.attach(self.label, 0, 1, row, row + 1, yoptions=gtk.SHRINK)
        table.attach(self.dropdown, 1, 2, row, row + 1, yoptions=gtk.SHRINK)
        table.attach(self.custom, 1, 2, row + 1, row + 2, yoptions=gtk.SHRINK)


def mnemonic_label(mnemonic, widget):
    label = gtk.Label()
    label.set_text_with_mnemonic(mnemonic)
    label.set_mnemonic_widget(widget)
    return label


class PrefsDialog(gtk.Dialog):
    def __init__(self, prefs):
        title = _('%s Preferences') % prefs.applet.props.display_name
        super(PrefsDialog, self).__init__(title, prefs.applet)
        self.props.icon_name = 'gtk-preferences'
        self.prefs = prefs
        self.font_replace = None
        self.create_ui()
        # action button
        self.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        self.connect('response', lambda dialog, response: dialog.hide())
        self.prefs.connect('notify::orientation', self.on_orient_changed)

    def create_ui(self):
        notebook = gtk.Notebook()
        # appearance
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
        text_color_button = ColorButton.with_color(self.prefs.props.font_color)
        text_color_button.connect('color-set', self.color_changed,
                                  'font_color')
        text_color_label = mnemonic_label(_('Font _Color:'), text_color_button)
        table.attach(text_color_label, 0, 1, 1, 2)
        table.attach(text_color_button, 1, 2, 1, 2)
        # * font shadow color
        text_shadow_color_button = \
                ColorButton.with_color(self.prefs.props.font_shadow_color)
        text_shadow_color_button.connect('color-set', self.color_changed,
                                         'font_shadow_color')
        text_shadow_color_label = mnemonic_label(_('Font _Shadow Color:'),
                                                 text_color_button)
        table.attach(text_shadow_color_label, 0, 1, 2, 3)
        table.attach(text_shadow_color_button, 1, 2, 2, 3)
        # * clock type: 12/24 hour
        clock_type = HRadioGroup(_('Clock Type'))
        clock_type.add_radio(_('_12 Hour'),
                signals={'toggled': (self.radiobutton_changed,
                                     'twelve_hour')})
        clock_type.add_radio(_('_24 Hour'),
                active=not self.prefs.props.twelve_hour)
        table.attach(clock_type, 0, 2, 3, 4)
        # * clock style: time beside date
        self.clock_style = HRadioGroup(_('Date Position'))
        self.clock_style.add_radio(_('_Left'),
               signals={'toggled': (self.radiobutton_changed,
                                    'date_before_time')})
        self.clock_style.add_radio(_('_Bottom'),
               active=not self.prefs.props.date_before_time)
        table.attach(self.clock_style, 0, 2, 4, 5)
        appearance_label = mnemonic_label(_('_Appearance'), table)
        notebook.append_page(table, appearance_label)
        # commands
        cmd_table = gtk.Table(4, 2)
        cmd_table.props.row_spacing = 5
        cmd_table.props.column_spacing = 5
        cmd_label = mnemonic_label(_('C_ommands'), cmd_table)
        # * calendar
        cal_options = [[_('Evolution (default)'), 'evolution calendar:///?startdate=%02(year)d%02(month)d%02(day)dT120000']]
        calendar_cmd = CommandSelector(_('Run Cal_endar:'), self.prefs,
                                       cal_options, 'calendar-command')
        calendar_cmd.attach_to_table(cmd_table, 0)
        # * time admin
        time_options = [[_('GNOME System Tools (default)'), 'gksudo time-admin']]
        time_cmd = CommandSelector(_('Run _Time Admin:'), self.prefs,
                                   time_options, 'adjust-datetime-command')
        time_cmd.attach_to_table(cmd_table, 2)
        notebook.append_page(cmd_table, cmd_label)
        self.vbox.add(notebook)

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

    def color_changed(self, color_btn, prop):
        setattr(self.prefs.props, prop, color_btn.props.da_color)

    def on_orient_changed(self, prefs, pspec):
        self.clock_style.props.sensitive = \
                (prefs.props.orientation == gtk.ORIENTATION_HORIZONTAL)

# vim: set ts=4 sts=4 sw=4 et ai cindent :
