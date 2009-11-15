#! /usr/bin/python
#
#         Dialect Applet, v 09.11.03
#
#         Copyright (C) 2009, Lachlan Turner (Denham2010) <lochjt@hotmail.com>
#         Watch signal code patch provided by Michal Hruby (mhr3)
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
import gtk
import awn

# APPLET required modules
import gobject
import subprocess
import fcntl
import signal
import glib
from xml.dom.minidom import parse
from desktopagnostic.config import GROUP_DEFAULT as group
from desktopagnostic.config import BIND_METHOD_FALLBACK as bind_fb

# DEFINE applet class


class Dialect(awn.AppletSimple):

# INITIALISE
    left = gobject.property(type = int, default = 2, minimum = 0, maximum = 3)
    middle = gobject.property(type = int, default = 1, minimum = 0, maximum = 3)
    scroll = gobject.property(type = bool, default = False)
    overlay = gobject.property(type = bool, default = True)
    scale = gobject.property(type = float, default = 0.5, minimum = 0.1, \
      maximum = 0.9)
    opacity = gobject.property(type = float,  default = 0.9, minimum = 0.0, \
      maximum = 0.9)

    # INITIALISE applet
    def __init__(self, canonical, uid, panel_id):
        super(Dialect, self).__init__(canonical, uid, panel_id)

        # GLOBAL variables
        self.effects = self.get_effects()
        self.config = awn.config_get_default_for_applet(self)
        self.path = os.path.dirname(__file__)
        self.theme = gtk.icon_theme_get_default()
        self.init = True

        # CONFIG and COMPARE variables
        self.watch = '/var/lib/xkb'
        self.base = '/usr/share/X11/xkb/rules/base.xml'
        self.widgets = ['about', 'error', 'help', 'help_page', 'prefs', \
          'left', 'middle', 'scroll', 'sys_tree', 'user_tree', 'sys_list', \
          'user_list', 'add', 'remove', 'overlay', 'scale', 'opacity']
        self.schema = {'left': 'active', 'middle': 'active', 'scroll': \
          'active', 'scale': 'value', 'opacity': 'value', 'overlay': 'active'}
        self.context_title = ['Preferences', 'Help', 'Separator', 'About']
        self.context_data = [['gtk-preferences', 'prefs'], \
          ['gtk-help', 'help'], None, ['gtk-about', 'about']]
        self.wheel = [gtk.gdk.SCROLL_DOWN, None, gtk.gdk.SCROLL_UP]

        # DEFAULT icon and tooltip
        self.image = self.set_icon_name('input-keyboard')
        self.flag = awn.OverlayPixbufFile(None)
        self.over = False
        self.set_tooltip_text('Dialect Applet')
        self.get_icon().get_tooltip().props.toggle_on_click = False

        # GTK load interface
        self.gtk_init()

        # CONTEXT menu
        self.context_init()

        # PREFERENCES load
        self.prefs_init()

        # DEPENDENCIES and INITIALISE complete check
        self.error_check()

        # CONNECT applet events
        self.connect('clicked', self.on_applet_clicked)
        self.connect('middle-clicked', self.on_applet_clicked)
        self.connect('context-menu-popup', self.on_applet_clicked)
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
        self.gtk['sys_menu'] = gtk.Menu()
        for key in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            icon = gtk.image_new_from_stock(gtk.STOCK_DIRECTORY, \
              gtk.ICON_SIZE_MENU)
            self.gtk['item_' + key] = gtk.ImageMenuItem(key, key)
            self.gtk['item_' + key].set_image(icon)
            self.gtk['menu_' + key] = gtk.Menu()
            self.gtk['item_' + key].set_submenu(self.gtk['menu_' + key])
            self.gtk['item_' + key].show()
            self.gtk['sys_menu'].append(self.gtk['item_' + key])
        builder.connect_signals(self)

    # CONTEXT menu
    def context_init(self):
        self.context_menu = self.create_default_menu()
        item = []
        for menu in range(len(self.context_title)):
            title = self.context_title[menu]
            data = self.context_data[menu]
            if not data:
                item.append(gtk.SeparatorMenuItem())
            else:
                item.append(gtk.ImageMenuItem(data[0], title))
                item[-1].connect('activate', self.on_context_response, data[1])
            self.context_menu.append(item[-1])
            item[-1].show()

    # PREFERENCES load
    def prefs_init(self):
        for item in self.schema.keys():
            self.config.bind(group, item, self, item, True, bind_fb)
        if self.left < 0 or self.left > 3:
            self.left = 2
        if self.middle < 0 or self.middle > 3:
            self.middle = 1
        if self.opacity < 0 or self.opacity > 0.9:
            self.opacity = 0.9
        if self.scale < 0.1 or self.scale > 0.9:
            self.scale = 0.5
        self.user = self.config.get_list(group, 'user_list')
        self.current = self.config.get_list(group, 'current')

    # DEPENDENCIES check and complete INITIALISE
    def error_check(self):
        self.depend_check()
        if self.depend:
            if self.init:
                self.layout_init()
                self.gtk_default()
                self.set_layout()
        else:
            self.effects.start_ex(awn.EFFECT_ATTENTION, 2)
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
                    break

    #LAYOUTS list
    def layout_init(self):
        self.layout = {}
        self.variant = {}
        data = parse(self.base)
        layout_list = data.getElementsByTagName('layoutList')
        layouts = layout_list[0].getElementsByTagName('layout')
        for layout in layouts:
            l_config = layout.getElementsByTagName('configItem')
            l_name = l_config[0].getElementsByTagName('name')\
              [0].childNodes[0].nodeValue
            l_desc = l_config[0].getElementsByTagName('description')\
              [0].childNodes[0].nodeValue
            v_list = {}
            variant_list = layout.getElementsByTagName('variantList')
            if len(variant_list):
                variants = variant_list[0].getElementsByTagName('variant')
                for variant in variants:
                    v_config = variant.getElementsByTagName('configItem')
                    v_name = v_config[0].getElementsByTagName('name')\
                      [0].childNodes[0].nodeValue
                    v_desc = v_config[0].getElementsByTagName('description')\
                      [0].childNodes[0].nodeValue
                    v_list[v_name] = v_desc
            self.layout[l_name] = l_desc
            self.variant[l_name] = v_list
        if len(self.current) == 2:
            bad_key = True
            if self.current[0] in self.layout.keys():
                bad_key = False
                if self.current[1] not in self.variant[self.current[0]].keys():
                    if self.current[1] != '':
                        bad_key = True
            if bad_key:
                self.current = []
                self.config.set_list(group, 'current', self.current)
        if len(self.user) > 0:
            user = self.user[:]
            while (len(user) > 0):
                item = user.pop()
                if len(item.split(',')) != 2:
                    item += ','
                parent, child = item.split(',')
                if item[-1] == ',':
                    item = item.split(',')[0]
                bad_key = True
                if parent in self.layout.keys():
                    bad_key = False
                    if child not in self.variant[parent].keys():
                        if child != '':
                            bad_key = True
                if bad_key:
                    index = self.user.index(item)
                    self.user.pop(index)
            self.config.set_list(group, 'user_list', self.user)

    # GTK initialise widgets
    def gtk_default(self):
        menu_list = []
        item_list = []
        icon_list = []
        menu_hide = ''
        for item in self.schema.keys():
            self.config.bind(group, item, self.gtk[item], self.schema[item], \
              False, bind_fb)
        if len(self.user) > 0:
            for item in self.user:
                parent = item.split(',')[0]
                child = item.split(',')[1]
                desc = self.layout[parent]
                if child != '':
                    desc = desc + ' - ' + self.variant[parent][child]
                icon = self.load_icon(parent, gtk.ICON_SIZE_SMALL_TOOLBAR)
                self.gtk['user_list'].append([icon, desc, parent, child])
        layouts = self.layout.values()
        layouts.sort()
        for layout in layouts:
            parent = self.layout.items()[self.layout.values().index(layout)][0]
            icon = self.load_icon(parent, gtk.ICON_SIZE_SMALL_TOOLBAR)
            index = self.gtk['sys_list'].append(None, \
              [icon, layout, parent, ''])
            item_list.append(gtk.ImageMenuItem(layout, layout))
            icon_list.append(gtk.image_new_from_pixbuf(\
              self.load_icon(parent, gtk.ICON_SIZE_MENU)))
            item_list[-1].set_image(icon_list[-1])
            item_list[-1].show()
            self.gtk['menu_' + layout[0].upper()].append(item_list[-1])
            if layout[0].upper() not in menu_hide:
                menu_hide += layout[0].upper()
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
                self.gtk['sys_list'].append(index, \
                  [None, variant, parent, child])
                item_list.append(gtk.MenuItem(variant))
                item_list[-1].show()
                menu_list[-1].append(item_list[-1])
                item_list[-1].connect('activate', self.on_menu_response, \
                  parent, child)
        for hide in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            if hide not in menu_hide:
                self.gtk['item_' + hide].hide()

    # SET the current LAYOUT
    def set_layout(self):
        if len(self.current) == 2:
            layout, variant = self.current
            command = 'setxkbmap -layout ' + layout
            if variant != '':
                command += ' -variant ' + variant
            self.unset_watch()
            retcode = subprocess.call(command, shell=True)
            self.update_applet(layout, variant, False)
            self.set_watch()
        else:
            self.get_layout(False)

    # GET the current layout
    def get_layout(self, effect=False):
        self.unset_watch()
        pipe = subprocess.Popen('setxkbmap -print -v 10', shell=True, \
          bufsize=0, stdout=subprocess.PIPE).stdout
        data = pipe.read()
        pipe.close()
        self.set_watch()
        result = data.split('\n')
        layout = ''
        variant = ''
        for line in result:
            if line.startswith('layout:'):
                layout = line.split(':')[1].lstrip()
            if line.startswith('variant'):
                variant = line.split(':')[1].lstrip()
        self.current = [layout, variant]
        self.config.set_list(group, 'current', self.current)
        self.update_applet(layout, variant, effect)

    # UPDATE the applet icon on a get or set layout call
    def update_applet(self, layout, variant, effect=False):
        tooltip = self.layout[layout]
        if variant != '':
            tooltip += ' - ' + self.variant[layout][variant]
        self.set_tooltip_text(tooltip)
        if self.over:
            self.remove_overlay(self.flag)
            self.over = False
        if self.overlay:
            path = os.path.join(self.path, 'icons', layout + '.png')
            if os.path.isfile(path):
                self.flag = awn.OverlayPixbufFile(path)
                self.flag.set_property('alpha', self.opacity)
                self.flag.set_property('scale', self.scale)
                self.flag.set_property('gravity', gtk.gdk.GRAVITY_SOUTH_EAST)
                self.over = True
                self.add_overlay(self.flag)
        if effect:
            self.effects.start_ex(awn.EFFECT_ATTENTION, 2)

    # Add WATCH for layout changes
    def set_watch(self):
        monitor = os.open(self.watch, os.O_RDONLY)
        fcntl.fcntl(monitor, fcntl.F_NOTIFY, fcntl.DN_ACCESS | \
          fcntl.DN_MODIFY | fcntl.DN_CREATE)
        signal.signal(signal.SIGIO, self.watch_event)

    # Remove WATCH for layout changes on IO operations
    def unset_watch(self):
        signal.signal(signal.SIGIO, signal.SIG_IGN)

    # ITERATE through user_list
    def iter_user_list(self, increment):
        if len(self.user) > 0:
            try:
                layout, variant = self.current
                index = self.user.index(layout + ',' + variant)
                index += increment
                if index < 0:
                    index = len(self.user) - 1
                else:
                    if index == len(self.user):
                        index = 0
            except:
                index = 0
            self.current = self.user[index].split(',')
            self.config.set_list(group, 'current', self.current)
            self.set_layout()
            return False
        else:
            return True

    # LOAD icon image file
    def load_icon(self, icon, sz):
        size = gtk.icon_size_lookup(sz)[1]
        path = os.path.join(self.path, 'icons', icon + '.png')
        if os.path.isfile(path):
            image = gtk.gdk.pixbuf_new_from_file(path)
        else:
            image = self.theme.load_icon('input-keyboard', size, 0)
        y = image.get_height()
        x = image.get_width()
        if size != y:
            x = int(float(x) * (float(size) / float(y)))
            y = size
        image = image.scale_simple(x, y, gtk.gdk.INTERP_BILINEAR)
        return image

# SIGNAL handlers

    # SYSTEM menu response
    def on_menu_response(self, obj, layout=None, variant=None):
        if not variant:
            variant = ''
        self.current = [str(layout), str(variant)]
        self.config.set_list(group, 'current', self.current)
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

    # OVERLAY flag option changed
    def on_overlay_toggled(self, obj):
        if not self.init:
            self.get_layout(False)

    # OVERLAY opacity changed
    def on_opacity_changed(self, obj):
        self.flag.set_property('alpha', obj.get_value())

    # OVERLAY scale changed
    def on_scale_changed(self, obj):
        self.flag.set_property('scale', obj.get_value())

    # ADD to or REMOVE from user list
    def on_list_changed(self, obj):
        if not self.init:
            key = self.gtk.items()[self.gtk.values().index(obj)][0]
            if key == 'remove':
                (model, iter) = self.gtk['user_select'].get_selected()
                if iter:
                    model.remove(iter)
            else:
                (model, iter) = self.gtk['sys_select'].get_selected()
                if iter:
                    row = model[model.get_path(iter)]
                    parent = row[2]
                    child = row[3]
                    desc = self.layout[parent]
                    if child != '':
                        desc = desc + ' - ' + self.variant[parent][child]
                    icon = self.load_icon(parent, gtk.ICON_SIZE_SMALL_TOOLBAR)
                    self.gtk['user_list'].append([icon, desc, parent, child])
                    self.on_order_changed()

    # USER list order changed
    def on_order_changed(self, obj=None, data=None, iter=None):
        if not self.init:
            if not iter:
                self.user = []
                if len(self.gtk['user_list']) > 0:
                    for item in range(len(self.gtk['user_list'])):
                        row = self.gtk['user_list'][item]
                        self.user.append(str(row[2]) + ',' + str(row[3]))
                self.config.set_list(group, 'user_list', self.user)

    # CLICKED on applet icon
    def on_applet_clicked(self, obj, event=None):
        if not event:
            event = gtk.get_current_event()
        if event.button < 3:
            self.error_check()
            if self.depend and not self.init:
                button = self.left
                if event.button == 2:
                    button = self.middle
                if button == 1:
                    self.gtk['sys_menu'].popup(None, None, None, 0, event.time)
                    return True
                elif button < 3:
                    if self.iter_user_list(button - 1):
                        self.gtk['sys_menu'].popup(None, None, None, 0, \
                          event.time)
                        return True
        else:
            self.context_menu.popup(None, None, None, 0, event.time)
            return True
        return False

    # SCROLL wheel event
    def on_scroll_event(self, obj, data):
        if not self.init:
            self.error_check()
            if self.depend:
                if self.scroll:
                    self.iter_user_list(self.wheel.index(data.direction) - 1)

    # UPDATE layout on watch signal triggered
    def update_layout(self):
        if self.init:
            self.get_layout(False)
        else:
            self.get_layout(True)
        self.set_watch()
        return False

    # WATCH event triggered
    def watch_event(self, signum, frame):
        glib.idle_add(self.update_layout)

# LAUNCH applet
if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = Dialect('dialect', awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
