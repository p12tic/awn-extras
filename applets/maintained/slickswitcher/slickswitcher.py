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

import awn, sys
import pygtk
pygtk.require('2.0')
import gtk
import gobject

import cairo
import drawing, switch, settings
from os.path import exists, isdir

from desktopagnostic.config import GROUP_DEFAULT

from awn.extras import _

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
    displayed = False
    last_size = 0

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
        self.update_background()
        self.draw_background = False
        self.number = self.switch.get_current_workspace_num()
        num_columns = self.switch.get_num_columns()
        self.row = int((self.number) / float(num_columns)) + 1
        self.column = int((self.number) % num_columns) + 1

        #Connect to signals
        #Applet signals
        self.connect('realize', self.realize_event)
        self.connect('size-changed', self.size_changed)
        self.connect('clicked', self.toggle_dialog)
        self.connect('context-menu-popup', self.show_menu)
        self.connect('scroll-event', self.scroll)
        self.dialog.connect('focus-out-event', self.hide_dialog)
        #Any relevant signal from Wnck
        self.switch.connect(self.update_icon)

        #Start updating the icon every 2 second, in 2 seconds
        gobject.timeout_add_seconds(2, self.timeout_icon)

        #Force the widget to get the background color from the dialog
        #self.dialog.realize()
        self.widget.update_color()

    #Make the icon when the window is first realized
    def realize_event(self, *args):
        #Actually get the icon
        self.icon = drawing.ViewportSurface(self, self.size)
        self.icon.width, self.icon.height = self.size, self.size
        self.icon.applet_mode = True
        self.icon.line_width = 4.0

        #"Update" the icon
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
        self.update_icon()

    #Update the icon
    def update_icon(self):
        self.number = self.switch.get_current_workspace_num()

        #Tell the icon to update
        self.icon.update()

    #The icon was updated
    def updated(self):
        #Set the icon
        self.contexts.append(cairo.Context(self.icon.surface))
        self.set_icon_context(self.contexts[-1])
        if len(self.contexts) >= 4:
            del self.contexts[0]

    #Called only from gobject every 2 seconds
    def timeout_icon(self):
        self.update_background()
        self.update_icon()
        gobject.timeout_add_seconds(2, self.timeout_icon)

    #Show the dialog.
    def show_dialog(self):
        self.displayed = True

        self.dialog.show_all()

    #Hide the dialog.
    def hide_dialog(self, *args):
        self.displayed = False

        self.dialog.hide()

    #Toggle the dialog
    def toggle_dialog(self, *args):
        if self.displayed:
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
        prefs_menu.connect('activate',self.show_prefs)
        about_menu.connect('activate',self.show_about)

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
        win.set_copyright('Copyright 2009 Sharkbaitbobby')
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
        win.run()
        win.destroy()
        del icon

    #Get the background image as a surface
    def update_background(self, *args):

        #See if gconf is installed
        if gconf:

            #Check if we have a client yet
            if self.client is None:

                #We don't. Get one
                self.client = gconf.client_get_default()

            #It is; get the path to the background image
            bg_path = self.client.get_string('/desktop/gnome/background/' + \
                'picture_filename')

            #Check if the path:
            #    isn't None
            #    isn't ''
            #    exists
            #    isn't a directory
            #    hasn changed
            #Also check if the size hasn't changed

            #Hooray parentheses!
            if (self.last_size != self.size) or ((bg_path is not None)    and \
                (bg_path != self.bg_path) and (bg_path != '') and exists(bg_path) and \
                (not isdir(bg_path))):

                #Save the background image's path
                self.bg_path = bg_path

                #Save the current size
                self.last_size = self.size

                #Try to get the background image as a surface
                try:
                    assert self.bg_path[-4:].lower() == '.png'

                    #Create the surface
                    surface = cairo.ImageSurface.create_from_png(self.bg_path)

                    #Get the dimensions of the image
                    width, height = float(surface.get_width()), \
                        float(surface.get_height())

                    #Resize the surface
                    cr = cairo.Context(surface)
                    cr.save()
                    cr.scale(self.size / width, self.size / height)
                    cr.set_source_surface(surface, 0, 0)
                    cr.paint()
                    cr.restore()

                    #All went well; save the surface
                    if self.background is not None:
                        del self.background

                    self.background = surface

                #Something went wrong
                except:
                    #Now try to get the image from a pixbuf
                    try:

                        pixbuf = gtk.gdk.pixbuf_new_from_file(self.bg_path)
                        pixbuf = pixbuf.scale_simple(self.size, self.size, \
                            gtk.gdk.INTERP_BILINEAR)

                        #All went well; save the pixbuf
                        if self.background is not None:
                            del self.background

                        self.background = pixbuf

                    #Something went wrong
                    except:
                        #Get a blank image as a surface
                        if self.background is not None:
                            del self.background

                        self.background = self.no_background()

            #Either the path is None, is '', doesn't exist, is a directory, or hasn't
            #changed. If it's one of the first four, get a blank image as a surface
            #If it's the last, just do nothing, as it is already saved
            else:

                if (bg_path is None) or (bg_path == '') or (not exists(bg_path)) or \
                    isdir(bg_path):

                    #Get a blank image as a surface
                    if self.background is not None:
                        del self.background

                    self.background = self.no_background()

        #GConf is not installed
        else:
            #Get a blank image as a surface
            if self.background is not None:
                del self.background

            self.background = self.no_background()

    #Return a blank image as a surface
    def no_background(self):
        #Get a surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.size, self.size)

        #Get a Cairo context
        cr = cairo.Context(surface)

        #Draw blackness
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.9)
        cr.paint()

        #Return the surface
        return surface

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
