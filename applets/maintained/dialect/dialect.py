#! /usr/bin/python
#
#         Dialect Applet, v 09.11.03
#
#         Copyright (C) 2009, Lachlan Turner (Denham2010) <lochjt@hotmail.com>
#
#         This program is free software; you can redistribute it and/or modify
#         it under the terms of the GNU General Public License as published by
#         the Free Software Foundation; either version 2 of the License, or
#         (at your option) any later version.
#
#         This program is distributed in the hope that it will be useful,
#         but WITHOUT ANY WARRANTY; without even the implied warranty of
#         MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#         GNU General Public License for more details.
#
#         You should have received a copy of the GNU General Public License
#         along with this program; if not, write to the Free Software
#         Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
#         02110-1301 USA

# AWN required modules
import sys
import os
import gobject
import gtk
import awn
import pygtk
pygtk.require('2.0')

# APPLET required modules
awn.check_dependencies(globals(), 'subprocess', 'fcntl', 'signal', 'xml', \
'desktopagnostic')
import subprocess
import fcntl
import signal
from xml.dom.minidom import parse
from desktopagnostic.config import GROUP_DEFAULT as group

# DEFINE applet class

class dialect(awn.AppletSimple):

# INITIALISE

    # INITIALISE applet
    def __init__(self, canonical, uid, panel_id):
        super(dialect, self).__init__(canonical, uid, panel_id)

        # GLOBAL variables
        self.size = self.get_size()
        self.pos = self.get_pos_type()
        self.effects = self.get_effects()
        self.config = awn.config_get_default_for_applet(self)
        self.path = os.path.dirname(__file__)
        self.theme = gtk.icon_theme_get_default()
        self.init = True

        # CONFIG and COMPARE variables
        self.watch = '/var/lib/xkb'
        self.base = '/etc/X11/xkb/base.xml'
        self.widgets = ['about', 'error', 'help', 'help_page', 'prefs', \
        'left', 'middle', 'scroll', 'sys_tree', 'user_tree', 'sys_list', \
        'user_list', 'add', 'remove', 'sys_menu']
        self.pos_type = [gtk.POS_BOTTOM, gtk.POS_TOP, gtk.POS_LEFT, \
        gtk.POS_RIGHT]
        self.icon_rotate = [None, None, gtk.gdk.PIXBUF_ROTATE_CLOCKWISE, \
        gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE]
        self.schema = {'left': int, 'middle': int, 'scroll': bool, 'current': \
        list, 'user_list': list}
        self.context = {'Preferences': ['gtk-preferences', 'prefs'], 'Help': \
        ['gtk-help', 'help'], 'About': ['gtk-about', 'about']}
        self.scroll = [gtk.gdk.SCROLL_DOWN, None, gtk.gdk.SCROLL_UP]

        # DEFAULT icon and tooltip
        self.set_icon_name('input-keyboard')
        self.set_tooltip_text('Dialect Applet')

        # GTK load interface
        self.gtk_init()

        # CONTEXT menu
        self.context_init()

        # PREFERENCES load
        self.prefs_init()

        # DEPENDENCIES and INITIALISE complete check
        self.error_check()

        # CONNECT applet events
        self.connect('button-press-event', self.on_applet_clicked)
        self.connect('size-changed', self.on_size_changed)
        self.connect('position-changed', self.on_position_changed)
        self.connect('scroll-event', self.on_scroll_event)

        # COMPLETE initialisation
        if self.depend:
            self.init = False

# FUNCTIONS

    # GTK load interface
    def gtk_init(self):
        self.gtk = {}
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(self.path, 'dialect.ui'))
        for key in self.widgets:
            self.gtk[key] = builder.get_object(key)
        for key in ['user_', 'sys_']:
            self.gtk[key + 'select'] = self.gtk[key + 'tree'].get_selection()
            self.gtk[key + 'select'].set_mode(gtk.SELECTION_SINGLE)
        for key in 'abcdefghijklmnopqrstuvwxyz':
            self.gtk['item_' + key] = builder.get_object('item_' + key)
            self.gtk['menu_' + key] = gtk.Menu()
            self.gtk['item_' + key].set_submenu(self.gtk['menu_' + key])
        builder.connect_signals(self)

    # CONTEXT menu
    def context_init(self):
        self.context_menu = self.create_default_menu()
        item = []
        for menu in self.context.keys():
            item.append(gtk.ImageMenuItem(self.context[menu][0], menu))
            self.context_menu.append(item[-1])
            item[-1].show()
            item[-1].connect('activate', self.on_context_response, \
            self.context[menu][1])

    # PREFERENCES load
    def prefs_init(self):
        self.prefs = {}
        for key in self.schema.keys():
            if self.schema[key] == bool:
                self.prefs[key] = self.config.get_bool(group, key)
            elif self.schema[key] == int:
                self.prefs[key] = self.config.get_int(group, key)
            else:
                self.prefs[key] = self.config.get_list(group, key)

    # DEPENDENCIES check and complete INITIALISE
    def error_check(self):
        self.depend_check()
        if self.depend:
            if self.init:
                self.layout_init()
                self.gtk_default()
                self.set_layout()
                self.set_watch()
        else:
            self.effects.start_ex('attention', 2)
            response = self.gtk['error'].run()
            self.gtk['error'].hide()

    # DEPENDENCIES confirmation
    def depend_check(self):
        self.depend = False
        if os.path.isfile(self.base):
            paths = os.environ.get('PATH').split(os.pathsep)
            for path in paths:
                if os.path.isfile(os.path.join(path, 'setxkbmap')):
                    self.depend = True

    #LAYOUTS list
    def layout_init(self):
        self.layout = {}
        self.variant = {}
        data = parse(self.base)
        layout_list = data.getElementsByTagName('layoutList')
        layouts = layout_list[0].getElementsByTagName('layout')
        for layout in layouts:
            l_config = layout.getElementsByTagName('configItem')
            l_name = l_config[0].getElementsByTagName('name')[0].\
            childNodes[0].nodeValue
            l_desc = l_config[0].getElementsByTagName('description')[0].\
            childNodes[0].nodeValue
            v_list = {}
            variant_list = layout.getElementsByTagName('variantList')
            if len(variant_list):
                variants = variant_list[0].getElementsByTagName('variant')
                for variant in variants:
                    v_config = variant.getElementsByTagName('configItem')
                    v_name = v_config[0].getElementsByTagName('name')[0].\
                    childNodes[0].nodeValue
                    v_desc = v_config[0].getElementsByTagName('description')[\
                    0].childNodes[0].nodeValue
                    v_list[v_name] = v_desc
            self.layout[l_name] = l_desc
            self.variant[l_name] = v_list

    # GTK initialise widgets
    def gtk_default(self):
        menu_list = []
        item_list = []
        icon_list = []
        menu_hide = ''
        self.gtk['left'].set_active(self.prefs['left'] + 1)
        self.gtk['middle'].set_active(self.prefs['middle'] + 1)
        self.gtk['scroll'].set_active(self.prefs['scroll'])
        if len(self.prefs['user_list']) > 0:
            for item in self.prefs['user_list']:
                parent = item.split(',')[0]
                child = item.split(',')[1]
                desc = self.layout[parent]
                if child != '':
                    desc = desc + ' - ' + self.variant[parent][child]
                icon = self.load_icon(parent, 16)
                self.gtk['user_list'].append(None, [icon, desc, parent, child])
        layouts = self.layout.values()
        layouts.sort()
        for layout in layouts:
            parent = self.layout.items()[self.layout.values().index(layout)][0]
            icon = self.load_icon(parent, 16)
            index = self.gtk['sys_list'].append(None, [icon, layout, parent, \
            ''])
            item_list.append(gtk.ImageMenuItem(layout, layout))
            icon_list.append(gtk.image_new_from_pixbuf(self.load_icon(parent, \
            16)))
            item_list[-1].set_image(icon_list[-1])
            item_list[-1].show()
            self.gtk['menu_' + layout[0].lower()].append(item_list[-1])
            if layout[0].lower() not in menu_hide:
                menu_hide += layout[0].lower()
            if len(self.variant[parent]):
                menu_list.append(gtk.Menu())
                item_list[-1].set_submenu(menu_list[-1])
                item_list.append(gtk.MenuItem(layout))
                item_list[-1].show()
                menu_list[-1].append(item_list[-1])
            item_list[-1].connect('activate', self.on_menu_response, parent)
            var = self.variant[parent]
            variants = var.values()
            variants.sort()
            for variant in variants:
                child = var.items()[var.values().index(variant)][0]
                self.gtk['sys_list'].append(index, [None, variant, parent, \
                child])
                item_list.append(gtk.MenuItem(variant))
                item_list[-1].show()
                menu_list[-1].append(item_list[-1])
                item_list[-1].connect('activate', self.on_menu_response, \
                parent, child)
        for hide in 'abcdefghijklmnopqrstuvwxyz':
            if hide not in menu_hide:
                self.gtk['item_' + hide].hide()

    # SET the current LAYOUT
    def set_layout(self):
        if len(self.prefs['current']) > 0 and len(self.prefs['current'][\
        0]) == 2:
            layout, variant = self.prefs['current']
            command = 'setxkbmap -layout ' + layout
            tooltip = self.layout[layout]
            if variant != '':
                command += ' -variant ' + variant
                tooltip += ' - ' + self.variant[layout][variant]
            self.set_tooltip_text(tooltip)
            self.set_icon_pixbuf(self.load_icon(layout, self.size, self.pos))
            self.effects.start_ex('attention', 2)
        else:
            self.get_layout()

    # Get the current layout
    def get_layout(self):
        pipe = subprocess.Popen('setxkbmap -print -v 10', shell=True, \
        bufsize=0, stdout=subprocess.PIPE).stdout
        data = pipe.read()
        pipe.close()
        result = data.split('\n')
        layout = ''
        variant = ''
        for line in result:
            if line.startswith('layout:'):
                layout = line.split(':')[1].lstrip()
            if line.startswith('variant'):
                variant = line.split(':')[1].lstrip()
        tooltip = self.layout[layout]
        if variant != '':
            tooltip += ' - ' + self.variant[layout][variant]
        self.prefs['current'] = [layout, variant]
        self.config.set_list(group, 'current', self.prefs['current'])
        self.set_tooltip_text(tooltip)
        self.set_icon_pixbuf(self.load_icon(layout, self.size, self.pos))
        self.effects.start_ex('attention', 2)

    # WATCH for layout changes
    def set_watch(self):
        monitor = os.open(self.watch, os.O_RDONLY)
        fcntl.fcntl(monitor, fcntl.F_NOTIFY, fcntl.DN_ACCESS|fcntl.DN_MODIFY|\
        fcntl.DN_CREATE)
        signal.signal(signal.SIGIO, self.watch_event)

    # ITERATE through user_list
    def iter_user_list(self, increment):
        if len(self.prefs['user_list']) > 0:
            try:
                layout, variant = self.prefs['current']
                index = self.prefs['user_list'].index(layout + ',' + variant)
                index += increment
                if index < 0:
                    index = len(self.prefs['user_list']) - 1
                else:
                    if index == len(self.prefs['user_list']):
                        index = 0
            except:
                index = 0
            self.prefs['current'] = self.prefs['user_list'][index].split(',')
            self.config.set_list(group, 'current', self.prefs['current'])
            self.set_layout()
            return False
        else:
            return True

    # LOAD icon image file
    def load_icon(self, icon, size, pos=None):
            index = 0
            if pos != None:
                index = self.pos_type.index(pos)
            path = os.path.join(self.path, 'icons', icon + '.png')
            if os.path.isfile(path):
                image = gtk.gdk.pixbuf_new_from_file(path)
                if self.icon_rotate[index] != None:
                    image = image.rotate_simple(self.icon_rotate[index])
            else:
                image = self.theme.load_icon('input-keyboard', size, 0)
            y = image.get_height()
            x = image.get_width()
            if not self.icon_rotate[index]:
                if size != y:
                    x = int(float(x) * (float(size) / float(y)))
                    y = size
            else:
                if size != x:
                    y = int(float(y) * (float(size) / float(x)))
                    x = size
            image = image.scale_simple(x, y, gtk.gdk.INTERP_BILINEAR)
            return image

# SIGNAL handlers

    # SYSTEM menu response
    def on_menu_response(self, obj, layout=None, variant=None):
        if variant == None:
            variant = ''
        self.prefs['current'] = [str(layout), str(variant)]
        self.config.set_list(group, 'current', self.prefs['current'])
        self.set_layout()

    # CONTEXT menu response
    def on_context_response(self, obj, data):
        allow = True
        if data == 'prefs':
            self.error_check()
            if not self.depend:
                allow = False
        if allow:
            if data == 'help':
                self.gtk['help_page'].set_current_page(0)
            response = self.gtk[data].run()
            self.gtk[data].hide()

    # DIALOG response
    def on_dialog_response(self, obj, data):
        obj.hide()

    # CLICK action changed
    def on_action_changed(self, obj):
        if not self.init:
            key = self.gtk.items()[self.gtk.values().index(obj)][0]
            value = obj.get_active() - 1
            self.prefs[key] = value
            self.config.set_int(group, key, value)

    # SCROLL action changed
    def on_scroll_toggled(self, obj):
        if not self.init:
            self.prefs['scroll'] = obj.get_active()
            self.config.set_bool(group, 'scroll', self.prefs['scroll'])

    # ADD to or REMOVE from user list
    def on_list_changed(self, obj):
        if not self.init:
            key = self.gtk.items()[self.gtk.values().index(obj)][0]
            if key == 'remove':
                (model, iter) = self.gtk['user_select'].get_selected()
                if iter != None:
                    model.remove(iter)
            else:
                (model, iter) = self.gtk['sys_select'].get_selected()
                if iter != None:
                    row = model[model.get_path(iter)]
                    parent = row[2]
                    child = row[3]
                    desc = self.layout[parent]
                    if child != '':
                        desc = desc + ' - ' + self.variant[parent][child]
                    icon = self.load_icon(parent, 16)
                    self.gtk['user_list'].append(None, [icon, desc, parent, \
                    child])
                    self.on_order_changed()

    # USER list order changed
    def on_order_changed(self, obj=None, data=None, iter=None):
        if not self.init:
            if not iter:
                self.prefs['user_list'] = []
                if len(self.gtk['user_list']) > 0:
                    for item in range(len(self.gtk['user_list'])):
                        row = self.gtk['user_list'][item]
                        self.prefs['user_list'].append(str(row[2]) + ',' + \
                        str(row[3]))
                self.config.set_list(group, 'user_list', self.\
                prefs['user_list'])

    # SIZE change
    def on_size_changed(self, obj, data):
        self.size = data
        if not self.init:
            self.set_icon_pixbuf(self.load_icon(self.prefs['current'][0], \
            self.size, self.pos))

    # POSITION changed
    def on_position_changed(self, obj, data):
        self.pos = data
        if not self.init:
            self.set_icon_pixbuf(self.load_icon(self.prefs['current'][0], \
            self.size, self.pos))

    # CLICKED on applet icon
    def on_applet_clicked(self, obj, data):
        if data.button < 3:
            self.error_check()
            if self.depend and not self.init:
                button = 'left'
                if data.button == 2:
                    button = 'middle'
                if self.prefs[button] == 0:
                    self.gtk['sys_menu'].popup(None, None, None, data.button, \
                    data.time)
                    return True
                elif self.prefs[button] < 2:
                    if self.iter_user_list(self.prefs[button]):
                        self.gtk['sys_menu'].popup(None, None, None, \
                        data.button, data.time)
                        return True
        else:
            self.context_menu.popup(None, None, None, data.button, data.time)
            return True
        return False

    # SCROLL wheel event
    def on_scroll_event(self, obj, data):
        if not self.init:
            self.error_check()
            if self.depend:
                if self.prefs['scroll']:
                    self.iter_user_list(self.scroll.index(data.direction) - 1)

    # WATCH event
    def watch_event(self, signum, frame):
        self.get_layout()
        self.set_watch()

# LAUNCH applet
if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = dialect('dialect', awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
