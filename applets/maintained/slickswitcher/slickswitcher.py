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

import awn, sys
import pygtk
pygtk.require('2.0')
import gtk
import gobject

import cairo
import drawing, switch, settings
from os.path import exists, isdir
import os

from desktopagnostic.config import GROUP_DEFAULT

from awn.extras import _
import gc

try:
    import gconf
except ImportError:
    gconf = False


class App(awn.AppletSimple):
    client = None
    bg_path = None
    background = None
    contexts = []
    timeout = None
    last_size = 0
    self_pixbufs = []
    dialog_pixbufs = []
    last_w = 0
    last_h = 0
    last_mode = -1
    last_file = ''

    def __init__(self, uid, panel_id):
        #Awn Applet configuration
        awn.AppletSimple.__init__(self, 'slickswitcher', uid, panel_id)
        self.dialog = awn.Dialog(self)
        self.dialog.set_skip_pager_hint(True)

        self.set_tooltip_text(_("SlickSwitcher"))

        self.size = self.get_size()

        #Set up Switch - does wnck stuff
        self.switch = switch.Switch()

        #Set up Settings - does awn.Config stuff
        self.settings = settings.Settings(self)
        for key in ['use_custom', 'custom_back', 'custom_border']:
            self.settings.config.notify_add(GROUP_DEFAULT, key, self.update_custom)

        #Set up the dialog colors
        self.dialog_style = self.dialog.get_style()
        self.unmodified_style = self.dialog_style.copy()
        self.dialog.connect('style-set', self.style_set)

        #Set up Drawing - does the shiny drawing stuff
        self.widget = drawing.Drawing(self.switch, self.settings, self)
        self.dialog.add(self.widget)

        #Set up the values for the ViewportSurface
        self.update_backgrounds()
        self.draw_background = False
        self.number = self.switch.get_current_workspace_num()
        num_columns = self.switch.get_num_columns()
        self.row = int((self.number) / float(num_columns)) + 1
        self.column = int((self.number) % num_columns) + 1

        #Set up the text overlay
        self.overlay = awn.OverlayText()
        self.add_overlay(self.overlay)
        self.overlay.props.font_sizing = 21.0
        self.overlay.props.text = str(self.number)
        self.overlay.props.active = not self.settings['use_custom_text']
        self.overlay.props.apply_effects = True
        self.overlay.connect('notify::text-color', self.overlay_notify)
        self.overlay.connect('notify::text-outline-color', self.overlay_notify)
        self.overlay.connect('notify::font-mode', self.overlay_notify)
        self.overlay.connect('notify::text-outline-width', self.overlay_notify)

        self.settings.config.notify_add(GROUP_DEFAULT, 'use_custom_text', self.toggle_custom_text)

        #Connect to signals
        #Applet signals
        self.connect('realize', self.realize_event)
        self.connect('size-changed', self.size_changed)
        self.connect('clicked', self.toggle_dialog)
        self.connect('context-menu-popup', self.show_menu)
        self.connect('scroll-event', self.scroll)
        self.dialog.props.hide_on_unfocus = True
        #Any relevant signal from Wnck
        self.switch.connect(self.update_icon)

        #Start updating the icon every 2 second, in 2 seconds
        gobject.timeout_add_seconds(2, self.timeout_icon)

        #Force the widget to get the background color from the dialog
        #self.dialog.realize()
        self.widget.update_color()

    def overlay_notify(self, overlay, param):
        self.widget.queue_draw()

    def toggle_custom_text(self, group, key, val):
        self.overlay.props.active = not val

        self.update_icon()

    #Make the icon when the window is first realized
    def realize_event(self, *args):
        #Actually get the icon
        self.icon = drawing.ViewportSurface(self, self.size)
        self.icon.width, self.icon.height = self.size, self.size
        self.icon.applet_mode = True
        self.icon.line_width = 4.0

        #Update the icon
        self.update_icon()

    #When the style is set
    def style_set(self, widget, old_style):
        #Get the styles
        self.dialog_style = widget.get_style()
        self.unmodified_style = self.dialog_style.copy()

        if self.settings.config.get_bool(GROUP_DEFAULT, 'use_custom') == True:
            #If the user is using custom colors, set them now
            self.update_custom()

        else:
            self.widget.update_color()

    #When the custom colors have been updated (enabled/disabled/changed)
    def update_custom(self, *args):
        #Custom colors are currently enabled
        if self.settings.config.get_bool(GROUP_DEFAULT, 'use_custom') == True:

            #Set the custom background color
            custom_back = self.settings.config.get_string(GROUP_DEFAULT, 'custom_back')
            if custom_back is None:
                custom_back = '000000'
                self.settings.config.set_string(GROUP_DEFAULT, 'custom_back', custom_back)

            try:
                back = '#' + custom_back
                self.dialog_style.base[gtk.STATE_NORMAL] = gtk.gdk.color_parse(back)
            except:
                pass

            #Set the custom border color
            custom_border = self.settings.config.get_string(GROUP_DEFAULT, \
                'custom_border')
            if custom_border is None:
                custom_border = 'FFFFFF'
                self.settings.config.set_string(GROUP_DEFAULT, 'custom_border', \
                    custom_border)

            try:
                border = '#' + custom_border
                self.dialog_style.bg[gtk.STATE_SELECTED] = gtk.gdk.color_parse(border)
            except:
                pass

            #Set the new style
            self.dialog.set_style(self.dialog_style)

        #Custom colors are currently disabled
        else:
            self.dialog.set_style(self.unmodified_style)

        #Make the widget update the background color
        self.widget.update_color()

    #When the size of Awn's icons has changed
    def size_changed(self, applet, new_size):
        self.size = new_size
        self.overlay.props.font_sizing = 21.0
        self.update_icon()

    #Update the icon
    def update_icon(self, force=False):
        self.number = self.switch.get_current_workspace_num()

        #Tell the icon to update
        self.icon.update(force)

    #The icon was updated
    def updated(self):
        #Set the icon
        self.contexts.append(cairo.Context(self.icon.surface))
        self.set_icon_context(self.contexts[-1])
        if len(self.contexts) >= 4:
            del self.contexts[0]

        self.overlay.props.text = str(self.number)

    #Called only from gobject every 2 seconds
    def timeout_icon(self):
        if self.update_backgrounds():
            self.update_icon()

        gobject.timeout_add_seconds(2, self.timeout_icon)

        return False

    #Show the dialog.
    def show_dialog(self):
        self.dialog.show_all()

    #Hide the dialog.
    def hide_dialog(self, *args):
        self.dialog.hide()

    #Toggle the dialog
    def toggle_dialog(self, *args):
        if (self.dialog.flags() & gtk.VISIBLE) != 0:
            self.hide_dialog()

        else:
            self.show_dialog()

    def show_menu(self, applet, event):
        #Hide the dialog if it's shown
        self.hide_dialog()

        #Create the items for Preferences, and About
        prefs_menu = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        about_menu = gtk.ImageMenuItem(gtk.STOCK_ABOUT)

        #Connect the two items to functions when selected
        prefs_menu.connect('activate', self.show_prefs)
        about_menu.connect('activate', self.show_about)

        #Now create the menu to put the items in and show it
        menu = self.create_default_menu()
        menu.append(prefs_menu)
        menu.append(about_menu)
        menu.show_all()
        menu.popup(None, None, None, event.button, event.time)

    #When the user scrolls on the applet icon (switch viewport)
    def scroll(self, applet, event):
        self.switch.move(event.direction in (gtk.gdk.SCROLL_DOWN, gtk.gdk.SCROLL_RIGHT))
        self.update_icon()

    #Show the wonderful 'About' dialog
    def show_about(self, *args):
        win = gtk.AboutDialog()
        win.set_name(_('SlickSwitcher'))
        image_path = '/'.join(__file__.split('/')[:-1]) + '/icons/'
        icon = gtk.gdk.pixbuf_new_from_file(image_path + 'done.png')
        win.set_logo(icon)
        win.set_icon(icon)
        win.set_copyright('Copyright 2010 Sharkbaitbobby')
        win.set_authors(['Original Author:', '    diogodivision', \
            'Rewriters:', '    Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>', \
            '    isaacj87 <isaac_j87@yahoo.com>', '    Nonozerobo'])
        win.set_comments(_('A visual workspace switcher'))
        win.set_license('This program is free software; you can redistribute it '+ \
            'and/or modify it under the terms of the GNU General Public License '+ \
            'as published by the Free Software Foundation; either version 2 of '+ \
            'the License, or (at your option) any later version. This program is '+ \
            'distributed in the hope that it will be useful, but WITHOUT ANY '+ \
            'WARRANTY; without even the implied warranty of MERCHANTABILITY or '+ \
            'FITNESS FOR A PARTICULAR PURPOSE.    See the GNU General Public '+ \
            'License for more details. You should have received a copy of the GNU '+ \
            'General Public License along with this program; if not, write to the '+ \
            'Free Software Foundation, Inc.,'+\
            '51 Franklin St, Fifth Floor, Boston, MA 02110-1301    USA.')
        win.set_wrap_license(True)
        win.set_artists(['Original design by diogodivision', \
            'Redone by sharkbaitbobby'])
        win.set_website('http://wiki.awn-project.org/SlickSwitcher')
        win.set_website_label('wiki.awn-project.org')
        win.set_version(awn.extras.__version__)
        win.run()
        win.destroy()

        gc.set_debug(gc.DEBUG_LEAK)
        gc.get_count()
        gc.collect()
        del icon

    #Get the background image as a surface
    def update_backgrounds(self, force=False, obj=None):
        bgs = {}
        ok = False
        if obj is None:
            obj = self
            w, h = self.size, self.size

            if self.size != self.last_size:
                ok = True
                self.last_size = self.size

        else:
            w, h = self.settings['width'], self.settings['height']
            if w != obj.last_w or h != obj.last_h:
                ok = True
                obj.last_w, obj.last_h = w, h

        if self.settings['background_mode'] != obj.last_mode:
            ok = True
            obj.last_mode = self.settings['background_mode']

        elif self.settings['background_mode'] == 'file':
            if self.settings['background_file'] != obj.last_file:
                ok = True
                obj.last_file = self.settings['background_file']

        if not ok and not force:
            return

        if self.settings['background_mode'] == 'file':
            path = self.settings['background_file']
            bgs = [self.background_from_file(path, w, h)]

        elif self.settings['background_mode'] == 'compiz':
            fp = open(os.environ['HOME'] + '/.config/compiz/compizconfig/config')
            f = fp.read()
            fp.close()

            backend = 'gconf'

            for line in f.split('\n'):
                if line.find('backend = ') == 0:
                    backend = line.split('backend = ')[1]

            if backend == 'gconf':
                if gconf:
                    if self.client is None:
                        self.client = gconf.client_get_default()

                    paths = self.client.get_list( \
                        '/apps/compiz/plugins/wallpaper/screen0/options/bg_image', \
                        gconf.VALUE_STRING)

                    if len(paths) == 0:
                        bgs[0] = self.no_background(w, h)

                    else:
                        for i, path in enumerate(paths):
                            bgs[i] = self.background_from_file(path, w, h)

                else:
                    bgs = [self.no_background(w, h)]

            elif backend == 'ini':
                for line in f.split('\n'):
                    if line.find('profile = ') == 0:
                        profile = line.split('profile = ')[1]

                if profile.strip() == '':
                    profile = 'Default'

                fp = open(os.environ['HOME'] + '/.config/compiz/compizconfig/%s.ini' % profile)
                f = fp.read()
                fp.close()

                wallpaper = False
                for line in f.split('\n'):
                    if line == '[wallpaper]':
                        wallpaper = True
                    elif wallpaper and line.find('s0_bg_image = ') == 0:
                        paths = line.split('s0_bg_image = ')[1].split(';')
                        break

                if len(paths) == 0:
                    bgs[0] = self.no_background(w, h)

                else:
                    for i, path in enumerate(paths):
                        if path.strip() != '':
                            bgs[i] = self.background_from_file(path, w, h)

            else:
                bgs = [self.no_background(w, h)]

        else:
            #See if gconf is installed
            if gconf:
                #Check if we have a client yet
                if self.client is None:
                    #We don't. Get one
                    self.client = gconf.client_get_default()

                #It is; get the path to the background image
                path = self.client.get_string('/desktop/gnome/background/picture_filename')

                bgs = [self.background_from_file(path, w, h)]

            #GConf is not installed.
            else:
                bgs = [self.no_background(w, h)]

        if obj == self:
            self.backgrounds = bgs
            return (ok or force)

        else:
            return bgs

    #Return a blank image as a surface
    def no_background(self, w=48, h=48):
        #Get a surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)

        #Get a Cairo context
        cr = cairo.Context(surface)

        #Draw blackness
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.9)
        cr.paint()

        del cr

        #Return the surface
        return surface

    #Get a background image from file
    def background_from_file(self, path, w=48, h=48):
        #Try to get the image from a pixbuf
        try:
            pixbuf = gtk.gdk.pixbuf_new_from_file(path)
            pixbuf = pixbuf.scale_simple(w, h, gtk.gdk.INTERP_BILINEAR)

            return pixbuf

        #Something went wrong
        except:
            return self.no_background(w, h)

    #Show a Preferences dialog
    def show_prefs(self, *args):
        import prefs
        prefs.Prefs(self)

if __name__ == '__main__':
    awn.init(sys.argv[1:])
    applet = App(awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
