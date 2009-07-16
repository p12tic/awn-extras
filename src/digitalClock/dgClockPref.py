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
import gtk
import gtk.glade
from gtk import gdk
import time
import subprocess
import awn

class dgClockPref:

    #glade path
    glade_path = os.path.join((os.path.dirname(__file__)), "pref.glade")

    pref_map = {
      'dbt': ('bool', 'dateBeforeTime'),
      'hour12': ('bool', 'hour12'),
      'font_face': ('string', 'fontFace'),
      'font_color': ('color', 'fontColor'),
      'font_shadow_color': ('color', 'fontShadowColor')
      }
    prefs = {}

    def __init__(self, config, applet):
        self.config = config
        self.applet = applet
        for key, details in self.pref_map.iteritems():
            self.config.notify_add(awn.CONFIG_DEFAULT_GROUP, key, self.config_notify, details)
        self.menu = self.buildMenu()
        self.get_prefs()

    def buildMenu(self):
        popup_menu = self.applet.create_default_menu()
        pref = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)

        timeadj = awn.image_menu_item_new_with_label('Adjust Date & Time')
        timeadj.set_image(gtk.image_new_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU))

        ctime = awn.image_menu_item_new_with_label('Copy Time')
        ctime.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))

        cdate = awn.image_menu_item_new_with_label('Copy Date')
        cdate.set_image(gtk.image_new_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU))

        popup_menu.append(ctime)
        popup_menu.append(cdate)
        popup_menu.append(pref)
        popup_menu.append(timeadj)

        pref.connect_object("activate",self.show_prefs, self)
        timeadj.connect_object("activate",self.time_admin, self)
        ctime.connect_object("activate",self.copy_time, self)
        cdate.connect_object("activate",self.copy_date, self)
        popup_menu.show_all()
        return popup_menu

    def update_pref(self, key, ptype, pkey):
        if ptype == 'bool':
            value = self.config.get_bool(awn.CONFIG_DEFAULT_GROUP, key)
        else:
            value = self.config.get_string(awn.CONFIG_DEFAULT_GROUP, key)
            if ptype == 'color':
                value = self.parseColors(value)
        self.prefs[pkey] = value

    def config_notify(self, entry, pref):
        self.update_pref(entry['key'], pref[0], pref[1])

    def get_prefs(self):
        for key, details in self.pref_map.iteritems():
            self.update_pref(key, details[0], details[1])

    def show_prefs(self, widget):
        if not hasattr(self, 'wTree'):
            self.wTree = gtk.glade.XML(self.glade_path)
            self.window = self.wTree.get_widget("main_window")

            close = self.wTree.get_widget("close_button")
            close.connect("clicked", self.close_prefs)

            font_btn = self.wTree.get_widget("fontface")
            font_btn.set_font_name(self.prefs['fontFace'])
            font_btn.connect("font-set", self.font_changed, 'font_face')

            color_btn = self.wTree.get_widget("fontcolor")
            color_btn.set_color(self.prefs['fontColor'])
            color_btn.connect("color-set", self.color_changed, 'font_color', self.prefs['fontColor'])

            scolor_btn = self.wTree.get_widget("shadowcolor")
            scolor_btn.set_color(self.prefs['fontShadowColor'])
            scolor_btn.set_use_alpha(False) #Not used yet
            scolor_btn.connect("color-set", self.color_changed, 'font_shadow_color', self.prefs['fontShadowColor'])

            h12 = self.wTree.get_widget("hour12")
            h12.set_active(self.prefs['hour12'])
            h12.connect("toggled", self.set_bool, 'hour12')

            tbd = self.wTree.get_widget("timebesidedate")
            tbd.set_active(self.prefs['dateBeforeTime'])
            tbd.connect("toggled", self.set_bool, 'dbt')

        self.window.show_all()

    def copy_date(self, widget):
        cb = gtk.Clipboard()
        txt = time.strftime("%A, %B %d, %Y")
        cb.set_text(txt)

    def copy_time(self, widget):
        cb = gtk.Clipboard()
        if self.prefs['hour12']:
            h = time.strftime("%I").lstrip('0')
            txt = h + time.strftime(":%M:%S %p")
        else:
            txt = time.strftime("%H:%M:%S")
        cb.set_text(txt)

    def time_admin(self, widget):
        subprocess.Popen('gksudo time-admin', shell=True)

    def close_prefs(self, btn):
        self.window.hide_all()

    def set_bool(self, check, key):
        self.config.set_bool(awn.CONFIG_DEFAULT_GROUP, key, check.get_active())

    def font_changed(self, font_btn, key):
        self.clean_font_name(font_btn.get_font_name())
        self.config.set_string(awn.CONFIG_DEFAULT_GROUP, key, self.prefs['fontFace'])

    def color_changed(self, color_btn, key, var):
        var = color_btn.get_color()
        if color_btn.get_use_alpha():
            alpha = color_btn.get_alpha() #Not used yet
        self.config.set_string(awn.CONFIG_DEFAULT_GROUP, key, '%s,%s,%s' % (var.red, var.green, var.blue))

    def clean_font_name(self, fontface):
        rem = ["Condensed", "Book", "Oblique", "Bold", "Italic", "Regular", "Medium", "Light"]
        for r in rem:
            fontface = fontface.replace(r, '')
            fontface = fontface.rstrip('0123456789 ')
        self.prefs['fontFace'] = fontface

    def parseColors(self, color):
        colors = [int(p) for p in color.split(',')]
        return gdk.Color(*colors[:3])
