#!/usr/bin/python

# Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


import sys, os, re
import gobject
import gtk
from gtk import gdk
import awn


class App (awn.AppletSimple):
    """an applet which calls a defined quit/logout command"""

    def __init__ (self, uid, orient, height):
        self.location = __file__.replace('quit-applet.py','')
        self.client = awn.Config('QuitApplet', None)
        self.defaults = {
            'IconLocation': os.path.join(self.location, 'icons', 'application-exit.svg'),
            'LogoutCommand': 'gnome-session-save --kill'
            }
        self.load_keys()
        self.client.notify_add(awn.CONFIG_DEFAULT_GROUP, 'IconLocation', self.load_config)
        self.client.notify_add(awn.CONFIG_DEFAULT_GROUP, 'LogoutCommand', self.load_config)
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height

        if hasattr(self, 'set_awn_icon'):
            self.set_awn_icon('quit-applet', uid, 'application-exit')
        else:
            self.theme = gtk.IconTheme ()
            try:
                icon = gdk.pixbuf_new_from_file (self.icon_location)
            except: icon = gdk.pixbuf_new_from_file (self.location + "icons/scalable/apps/application-exit.svg")
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
            self.set_temp_icon (icon)

        self.title = awn.awn_title_get_default ()
        self.connect ("button-press-event", self.button_press)
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)

        # Setup popup menu
        self.popup_menu = self.create_default_menu()
        pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        self.popup_menu.append(pref_item)
        pref_item.connect_object("activate", self.pref_callback, self)
        pref_item.show()

    def pref_callback(self, widget):
        window = PreferenceDialog(self)
        window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        window.set_destroy_with_parent(True)
        window.show_all()

    def button_press (self, widget, event):
        self.title.hide(self)
        if event.button == 3:
            # right click
            self.popup_menu.popup(None, None, None, event.button, event.time)
        else:
            os.system(self.logout_command)

    def enter_notify (self, widget, event):
        self.title.show (self, "Quit/Logout?")

    def leave_notify (self, widget, event):
        self.title.hide (self)

    def attr_from_key(self, key):
        return key[0].lower() + re.sub(r'[A-Z]', lambda m: '_' + m.group(0).lower(), key[1:])

    def load_config(self, entry, arg):
        setattr(self, self.attr_from_key(entry['key']), self.get_pref(entry['key'], self.defaults[entry['key']]))

    def load_keys(self):
        for key, default in self.defaults.iteritems():
            setattr(self, self.attr_from_key(key), self.get_pref(key, default))

    def get_pref(self, key, default):
        try:
            value = self.client.get_string(awn.CONFIG_DEFAULT_GROUP, key)
            if value is None:
                value = default
                self.client.set_string(awn.CONFIG_DEFAULT_GROUP, key, value)
        except NameError:
            value = default
        return value


class PreferenceDialog(gtk.Window):

    def __init__(self,applet):
        super(PreferenceDialog, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.applet = applet
        self.set_title("Preferences")
        vbox = gtk.VBox(True, 0)
        self.add(vbox)
        vbox1 = gtk.VBox(True, 0)
        label1 = gtk.Label("Logout command:")
        self.logout_command = gtk.Entry(max=0)
        self.logout_command.set_text(applet.logout_command)
        vbox1.pack_start(label1)
        vbox1.pack_end(self.logout_command)
        vbox.pack_start(vbox1,True,False,2)
        hbox4 = gtk.HBox(True, 0)
        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", self.ok_button, "ok")
        hbox4.add(ok)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.cancel_button, "cancel")
        hbox4.add(cancel)
        vbox.pack_end(hbox4,True,False,2)

    def ok_button(self, widget, event):
        self.applet.client.set_string(awn.CONFIG_DEFAULT_GROUP, 'LogoutCommand', self.logout_command.get_text().strip())
        self.destroy()

    def cancel_button(self, widget, event):
        self.destroy()


if __name__ == "__main__":
    awn.init (sys.argv[1:])
    applet = App (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
