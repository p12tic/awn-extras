#! /usr/bin/python
#
#         Dialect Applet, v 09.12.09
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
import gtk
import awn

# APPLET required modules
import gobject
awn.check_dependencies(globals(), 'xklavier')
from xklavier import *
from desktopagnostic.config import GROUP_DEFAULT as group
from desktopagnostic.config import BIND_METHOD_FALLBACK as bind_fb
from awn.extras import _

# DEFINE applet class


class Dialect(awn.AppletSimple):

# INITIALISE

    # PREFERENCES properties
    left = gobject.property(type = int, default = 2)
    middle = gobject.property(type = int, default = 1)
    scroll = gobject.property(type = bool, default = False)
    overlay = gobject.property(type = bool, default = True)
    scale = gobject.property(type = float, default = 0.5)
    opacity = gobject.property(type = float, default = 0.9)
    toggle = gobject.property(type = int, default = 0)

    # GLOBAL Variables
    layout = []
    variant = []

    # CONFIG variables
    widgets = ['about', 'prefs', 'tlist', 'left', \
      'middle', 'scroll', 'stree', 'utree', 'slist', 'ulist', \
      'add', 'remove', 'overlay', 'scale', 'opacity', 'toggle']
    schema = {'left': 'active', 'middle': 'active', 'scroll': 'active', \
      'scale': 'value', 'opacity': 'value', 'overlay': 'active'}
    ctitle = ['Preferences', 'About']
    cdata = [['gtk-preferences', 'prefs'], ['gtk-about', 'about']]
    wheel = [gtk.gdk.SCROLL_DOWN, None, gtk.gdk.SCROLL_UP]
    watch = '/var/lib/xkb'
    ui = 'dialect.ui'
    theme_icon = 'input-keyboard'
    app_name = _('Dialect Applet')

    # INITIALISE applet
    def __init__(self, canonical, uid, panel_id):
        super(Dialect, self).__init__(canonical, uid, panel_id)

        # BEGIN initialisation
        self.init = True

        # GLOBAL methods
        self.effects = self.get_effects()
        self.config = awn.config_get_default_for_applet(self)
        self.path = os.path.dirname(__file__)
        self.theme = gtk.icon_theme_get_default()

        # DEFAULT icon and tooltip
        self.image = self.set_icon_name(self.theme_icon)
        self.flag = awn.OverlayPixbufFile(None)
        self.overlays = False
        self.set_tooltip_text(self.app_name)
        self.get_icon().get_tooltip().props.toggle_on_click = False

        # Initialise XKLAVIER
        self.xklavier_init()

        # Load GTK widgets
        self.gtk_init()

        # Create CONTEXT menu
        self.context_init()

        # Generate LAYOUT and KEY TOGGLE lists
        self.layout_init()

        # Load PREFERENCES
        self.prefs_init()

        # Set User MENU items
        self.set_umenu()

        # Set GTK widgets
        self.gtk_status()

        # Set Default LAYOUT
        self.set_layout(0)

        # Connect applet SIGNALS
        self.connect('clicked', self.on_click)
        self.connect('middle-clicked', self.on_click)
        self.connect('context-menu-popup', self.on_click)
        self.connect('scroll-event', self.on_scroll)

        # COMPLETE initialisation
        self.init = False
        
        # Set timer to monitor HOTKEY changes
        gobject.timeout_add(500, self.external_config)

# FUNCTIONS

    # Initialise XKLAVIER
    def xklavier_init(self):
        self.engine = Engine(gtk.gdk.display_get_default())
        self.registry = ConfigRegistry(self.engine)
        self.registry.load(True)
        self.server = ConfigRec()
        self.server.get_from_server(self.engine)

    # XKLAVIER max number of layouts
    def maximum(self):
        return int(self.engine.get_max_num_groups())

    # XKLAVIER get server layout list
    def get_layouts(self):
        self.server.get_from_server(self.engine)
        return self.server.get_layouts()

    # XKLAVIER get server variant list
    def get_variants(self, layouts):
        self.server.get_from_server(self.engine)
        variants = self.server.get_variants()
        length = len(variants)
        if length != len(layouts):
            for item in range(len(layouts)-length):
                variants.append('')
        return variants

    # XKLAVIER get server options list
    def get_options(self):
        self.server.get_from_server(self.engine)
        options = self.server.get_options()
        index = -1
        if len(options) > 0:
            for item in options:
                if len(item) == 0: continue
                option, value = item.split(':')
                if option == 'grp':
                    index = options.index(item)
                    break
        return options, index

    # XKLAVIER change selected group
    def change_group(self, direc):
        if len(self.layout) > 1:
            self.server.get_from_server(self.engine)
            self.engine.start_listen(XKLL_TRACK_KEYBOARD_STATE)
            if direc > 0:
                self.set_layout(self.engine.get_next_group())
            else:
                self.set_layout(self.engine.get_prev_group())
            self.engine.stop_listen(XKLL_TRACK_KEYBOARD_STATE)

    # Load GTK widgets
    def gtk_init(self):
        self.gtk = {}
        builder = gtk.Builder()
        builder.add_from_file(os.path.join(self.path, self.ui))
        for key in self.widgets:
            self.gtk[key] = builder.get_object(key)
        for key in ['u', 's']:
            self.gtk[key + 'select'] = self.gtk[key + 'tree'].get_selection()
            self.gtk[key + 'select'].set_mode(gtk.SELECTION_SINGLE)
        builder.connect_signals(self)
        self.gtk['umenu'] = gtk.Menu()
        for item in range(self.maximum()):
            self.gtk[item] = gtk.ImageMenuItem(str(item))
            self.gtk['umenu'].append(self.gtk[item])
            self.gtk[item].connect('activate', self.on_umenu, item)
        layout_info = builder.get_object('layout_info')
        layout_info.set_tooltip_markup(_('<b>User List:</b> The list of ' +\
            'layouts you commonly use. The maximum number of layouts is ' +\
            'restricted by the X11 xkb system (currently 4). Select an item ' +\
            'and click the remove button to delete from your user list. You ' +\
            'can order the list by drag and drop.\n' +\
            '<b>System List:</b> The complete list of layouts and variants ' +\
            'available. Select an item and click the add button to include ' +\
            'in your user list.'))  # glade3 doesn't support translatable markup

    # Create CONTEXT menu
    def context_init(self):
        self.cmenu = self.create_default_menu()
        item = []
        for menu in range(len(self.ctitle)):
            title = self.ctitle[menu]
            data = self.cdata[menu]
            if not data:
                item.append(gtk.SeparatorMenuItem())
            else:
                item.append(gtk.ImageMenuItem(data[0], title))
                item[-1].connect('activate', self.on_cmenu, data[1])
            self.cmenu.append(item[-1])
            item[-1].show()

    # Generate LAYOUT and KEY TOGGLE lists
    def layout_init(self):
        def iter_layouts(registry, item):
            def iter_variants(registry, item):
                variant = item.get_name()
                desc = item.get_description()
                self.vlist[variant] = desc
            layout = item.get_name()
            desc = item.get_description()
            self.layouts[layout] = desc
            self.vlist = {}
            self.registry.foreach_layout_variant(layout, iter_variants)
            self.variants[layout] = self.vlist.copy()
        def iter_options(registry, item):
            option = item.get_name()
            desc = item.get_description()
            self.toggles[desc] = option
        self.layouts = {}
        self.variants = {}
        self.toggles = {}
        self.registry.foreach_layout(iter_layouts)
        self.registry.foreach_option('grp', iter_options)
        self.options = self.toggles.keys()
        self.options.sort()
        self.options.insert(0, 'None')
        self.toggles['None'] = ''

    # Load PREFERENCES
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
        self.layout = self.config.get_list(group, 'layout')
        self.variant = self.config.get_list(group, 'variant')
        self.toggle = self.config.get_int(group, 'toggle')
        bad_key = False
        if len(self.layout) > 0 and len(self.layout) == len(self.variant):
            if len(self.layout) > self.maximum():
                bad_key = True
            else:
                for item in range(len(self.layout)):
                    if self.layout[item] not in self.layouts.keys():
                        bad_key = True
                        break
                    else:
                        if self.variant[item] not in \
                          self.variants[self.layout[item]].keys():
                            if self.variant[item] != '':
                                bad_key = True
                                break
        else:
            bad_key = True
        if bad_key:
            self.layout = self.get_layouts()
            self.variant = self.get_variants(self.layout)
            self.config.set_list(group, 'layout', self.layout)
            self.config.set_list(group, 'variant', self.variant)
        options, index = self.get_options()
        if self.toggle < 0 or self.toggle > len(self.options):
            if index < 0:
                self.toggle = 0
            else:
                key = self.toggles.values().index(options[index])
                self.toggle = self.options.index(self.toggles.items()[key][0])
            self.config.set_int(group, 'toggle', self.toggle)
        else:
            if self.toggle > 0:
                if index < 0:
                    options.append(self.toggles[self.options[self.toggle]])
                else:
                    options[index] = self.toggles[self.options[self.toggle]]
            else:
                if index > -1:
                    options[index] = ''
        self.server.set_layouts(self.layout)
        self.server.set_variants(self.variant)
        self.server.set_options(options)
        self.server.activate(self.engine)

    # Set User MENU items
    def set_umenu(self):
        for item in range(self.maximum()):
            if item < len(self.layout):
                layout = self.layouts[self.layout[item]]
                if self.variant[item] == '':
                    variant = ''
                else:
                    variant = ' - ' + \
                      self.variants[self.layout[item]][self.variant[item]]
                self.gtk[item].set_label(layout + variant)
                self.gtk[item].set_image(gtk.image_new_from_pixbuf\
                  (self.load_icon(self.layout[item], gtk.ICON_SIZE_MENU)))
                self.gtk[item].show()
            else:
                self.gtk[item].hide()

    # Set GTK widgets
    def gtk_status(self):
        for item in self.schema.keys():
            self.config.bind(group, item, self.gtk[item], self.schema[item], \
              False, bind_fb)
        for item in range(len(self.layout)):
            layout = self.layout[item]
            variant = self.variant[item]
            desc = self.layouts[layout]
            if variant != '':
                desc = desc + ' - ' + self.variants[layout][variant]
            icon = self.load_icon(layout, gtk.ICON_SIZE_SMALL_TOOLBAR)
            self.gtk['ulist'].append([icon, desc, layout, variant])
        layouts = self.layouts.values()
        layouts.sort()
        for layout in layouts:
            parent = self.layouts.items()[self.layouts.values().index(layout)][0]
            icon = self.load_icon(parent, gtk.ICON_SIZE_SMALL_TOOLBAR)
            index = self.gtk['slist'].append(None, \
              [icon, layout, parent, ''])
            var = self.variants[parent]
            variants = var.values()
            variants.sort()
            for variant in variants:
                child = var.items()[var.values().index(variant)][0]
                self.gtk['slist'].append(index, \
                  [None, variant, parent, child])
        for option in self.options:
            self.gtk['tlist'].append([option])
        self.gtk['toggle'].set_active(self.toggle)
        if len(self.layout) == self.maximum():
            self.gtk['add'].set_sensitive(False)
        if len(self.layout) == 1:
            self.gtk['remove'].set_sensitive(False)

    # Set current LAYOUT
    def set_layout(self, layout):
        self.engine.lock_group(layout)
        self.current = layout
        self.update_applet(self.layout[layout], self.variant[layout], False)

    # Get current LAYOUT
    def get_layout(self, effect):
        self.engine.start_listen(XKLL_TRACK_KEYBOARD_STATE)
        layout = self.engine.get_current_state()['group']
        self.engine.stop_listen(XKLL_TRACK_KEYBOARD_STATE)
        if layout != self.current:
            self.current = layout
            self.update_applet(self.layout[layout], self.variant[layout], effect)

    # Update applet ICON
    def update_applet(self, layout, variant, effect):
        tooltip = self.layouts[layout]
        if variant != '':
            tooltip += '\n' + self.variants[layout][variant]
        self.set_tooltip_text(tooltip)
        if self.overlays:
            self.remove_overlay(self.flag)
            self.overlays = False
        if self.overlay:
            path = os.path.join(self.path, 'icons', layout + '.png')
            if os.path.isfile(path):
                self.flag = awn.OverlayPixbufFile(path)
                self.flag.set_property('alpha', self.opacity)
                self.flag.set_property('scale', self.scale)
                self.flag.set_property('gravity', gtk.gdk.GRAVITY_SOUTH_EAST)
                self.overlays = True
                self.add_overlay(self.flag)
        if effect:
            self.effects.start_ex(awn.EFFECT_ATTENTION, 2)

    # Load an ICON file
    def load_icon(self, icon, sz):
        size = gtk.icon_size_lookup(sz)[1]
        path = os.path.join(self.path, 'icons', icon + '.png')
        if os.path.isfile(path):
            image = gtk.gdk.pixbuf_new_from_file(path)
        else:
            image = self.theme.load_icon(self.theme_icon, size, 0)
        y = image.get_height()
        x = image.get_width()
        if size != y:
            x = int(float(x) * (float(size) / float(y)))
            y = size
        image = image.scale_simple(x, y, gtk.gdk.INTERP_BILINEAR)
        return image

    # EXTERNAL config change
    def external_config(self):
        self.server.get_from_server(self.engine)
        layouts = self.get_layouts()
        variants = self.get_variants(layouts)
        options, index = self.get_options()
        effect = False
        self.init = True
        if self.toggle > 0 and index > -1:
            key = self.toggles.values().index(options[index])
            self.toggle = self.options.index(self.toggles.items()[key][0])
        else:
            if index < 0:
                self.toggle = 0
            else:
                key = self.toggles.values().index(options[index])
                self.toggle = self.options.index(self.toggles.items()[key][0])
        self.config.set_int(group, 'toggle', self.toggle)
        self.gtk['toggle'].set_active(self.toggle)
        if self.layout != layouts or self.variant != variants:
            effect = True
            self.current = -1
            self.gtk['ulist'].clear()
            for item in range(len(layouts)):
                layout = layouts[item]
                variant = variants[item]
                desc = self.layouts[layout]
                if variant != '':
                    desc = desc + ' - ' + self.variants[layout][variant]
                icon = self.load_icon(layout, gtk.ICON_SIZE_SMALL_TOOLBAR)
                self.gtk['ulist'].append([icon, desc, layout, variant])
            self.layout = layouts
            self.variant = variants
            self.config.set_list(group, 'layout', self.layout)
            self.config.set_list(group, 'variant', self.variant)
            if len(self.layout) == 1:
                self.gtk['remove'].set_sensitive(False)
            else:
                self.gtk['remove'].set_sensitive(True)
            if len(self.layout) == self.maximum():
                self.gtk['add'].set_sensitive(False)
            else:
                self.gtk['add'].set_sensitive(True)
            self.set_umenu()
        self.init = False
        self.get_layout(effect)
        return True

# SIGNAL handlers

    # USER menu response
    def on_umenu(self, obj, data):
        self.set_layout(data)

    # CONTEXT menu response
    def on_cmenu(self, obj, data):
        response = self.gtk[data].run()
        self.gtk[data].hide()

    # DIALOG response
    def on_dialog(self, obj, data):
        obj.hide()

    # OVERLAY flag option changed
    def on_overlay(self, obj):
        if not self.init:
            self.overlay = not self.overlay
            self.update_applet(self.layout[self.current], \
              self.variant[self.current], False)

    # OVERLAY opacity changed
    def on_opacity(self, obj):
        self.flag.set_property('alpha', obj.get_value())

    # OVERLAY scale changed
    def on_scale(self, obj):
        self.flag.set_property('scale', obj.get_value())

    # ADD to or REMOVE from user list
    def on_ulist(self, obj):
        if not self.init:
            key = self.gtk.items()[self.gtk.values().index(obj)][0]
            if key == 'remove':
                (model, iter) = self.gtk['uselect'].get_selected()
                if iter:
                    model.remove(iter)
            else:
                (model, iter) = self.gtk['sselect'].get_selected()
                if iter:
                    row = model[model.get_path(iter)]
                    layout = row[2]
                    variant = row[3]
                    desc = self.layouts[layout]
                    if variant != '':
                        desc = desc + ' - ' + self.variants[layout][variant]
                    icon = self.load_icon(layout, gtk.ICON_SIZE_SMALL_TOOLBAR)
                    self.gtk['ulist'].append([icon, desc, layout, variant])
                    self.on_order()

    # USER list order changed
    def on_order(self, obj = None, data = None, iter = None):
        if not self.init:
            if not iter:
                self.layout = []
                self.variant = []
                for item in range(len(self.gtk['ulist'])):
                    row = self.gtk['ulist'][item]
                    self.layout.append(str(row[2]))
                    self.variant.append(str(row[3]))
                self.config.set_list(group, 'layout', self.layout)
                self.config.set_list(group, 'variant', self.variant)
                self.server.set_layouts(self.layout)
                self.server.set_variants(self.variant)
                self.server.activate(self.engine)
            if len(self.layout) == 1:
                self.gtk['remove'].set_sensitive(False)
            else:
                self.gtk['remove'].set_sensitive(True)
            if len(self.layout) == self.maximum():
                self.gtk['add'].set_sensitive(False)
            else:
                self.gtk['add'].set_sensitive(True)
            self.current = -1
            self.set_umenu()
            self.get_layout(False)
        
    # CLICKED on applet icon
    def on_click(self, obj, event = None):
        if not event:
            event = gtk.get_current_event()
        if event.button < 3:
            if not self.init:
                button = self.left
                if event.button == 2:
                    button = self.middle
                if button == 1:
                    self.popup_gtk_menu (self.gtk['umenu'], 0, event.time)
                    return True
                elif button < 3:
                    self.change_group(button - 1)
        else:
            self.popup_gtk_menu (self.cmenu, 0, event.time)
            return True
        return False

    # SCROLL wheel event
    def on_scroll(self, obj, data):
        if not self.init:
            if self.scroll:
                self.change_group(self.wheel.index(data.direction) - 1)

    # TOGGLE option changed
    def on_toggle(self, obj):
        if not self.init:
            self.toggle = obj.get_active()
            options, index = self.get_options()
            if self.toggle > 0:
                if index < 0:
                    options.append(self.toggles[self.options[self.toggle]])
                else:
                    options[index] = self.toggles[self.options[self.toggle]]
            else:
                if index > -1:
                    options[index] = ''
            self.config.set_int(group, 'toggle', self.toggle)
            self.server.set_options(options)
            self.server.activate(self.engine)

# LAUNCH applet
if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = Dialect('dialect', awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
