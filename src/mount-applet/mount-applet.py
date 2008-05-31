#!/usr/bin/python

# Copyright (c) 2007 Arvind Ganga
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

import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import gconf
import locale
import gettext

class MountApplet(awn.AppletSimple):
    gconf_path = "/apps/avant-window-navigator/applets/mountapplet"

    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.gconf_client = gconf.client_get_default()
        self.gconf_client.notify_add(self.gconf_path, self.config_event)
        self.get_config()

        self.height = height
        self.theme = gtk.IconTheme ()
        icon = gdk.pixbuf_new_from_file(os.path.dirname (__file__) + '/icons/mount-applet.png')
        if height != icon.get_height():
            icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_temp_icon (icon)
        self.title = awn.awn_title_get_default ()

        self.dialog = awn.AppletDialog (self)

        self.showing_dialog = False

        self.connect ("button-press-event", self.button_press)
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)
        self.dialog.connect ("focus-out-event", self.dialog_focus_out)

        # Setup popup menu
        self.popup_menu = self.create_default_menu()
        pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        self.popup_menu.append(pref_item)
        pref_item.connect_object("activate", self.pref_callback, self)
        pref_item.show()


    def get_config(self):
        self.hidden_mounts = self.gconf_client.get_list(self.gconf_path + "/hidden_mounts", gconf.VALUE_STRING)
        if self.hidden_mounts == None or self.hidden_mounts == []:
            self.gconf_client.set_list(self.gconf_path + "/hidden_mounts", gconf.VALUE_STRING, ['/', 'swap'])
            self.hidden_mounts = ['/', 'swap']

        self.execute_command = self.gconf_client.get_string(self.gconf_path + "/execute_command")
        if self.execute_command == None:
            self.gconf_client.set_string(self.gconf_path + "/execute_command", '')
            self.execute_command = ''


    def config_event(self, gconf_client, *args, **kwargs):
        self.dialog.hide()
        self.title.hide (self)
        self.get_config()


    def pref_callback(self, widget):
        window = PreferenceDialog(self)
        window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        window.set_destroy_with_parent(True)
        window.show_all()


    def button_press (self, widget, event):
        if event.button == 3:
            # right click
            self.title.hide(self)
            self.dialog.hide()
            self.popup_menu.popup(None, None, None, event.button, event.time)
        else:
            self.initialize_dialog()
            if self.showing_dialog:
                self.dialog.hide()
            else:
                self.dialog.show_all ()
            self.title.hide (self)

            self.showing_dialog = not self.showing_dialog


    def initialize_dialog(self):
        self.remove_buttons()

        fstab = self.readFile('/etc/fstab')
        mounts = self.readFile('/proc/mounts')

        for mountpoint in fstab:
            if self.hidden_mounts.count(mountpoint) > 0:
                continue

            button = gtk.Button(mountpoint)
            image = gtk.Image()

            if self.isMounted(mountpoint, mounts):
                button.connect("clicked", self.umount, mountpoint)
                image.set_from_stock(gtk.STOCK_APPLY, gtk.ICON_SIZE_BUTTON)
            else:
                button.connect("clicked", self.mount, mountpoint)
                image.set_from_stock(gtk.STOCK_CANCEL, gtk.ICON_SIZE_BUTTON)
            button.set_image(image)

            button.show()
            self.dialog.add (button)
            button.show_all ()


    def remove_buttons(self):
        for child in self.dialog.get_children():
            for vbox in child.get_children():
                for button in vbox.get_children():
                    vbox.remove(button)


    def dialog_focus_out (self, widget, event):
        self.dialog.hide ()


    def enter_notify (self, widget, event):
        self.title.show (self, "Mount Applet")


    def leave_notify (self, widget, event):
        self.title.hide (self)


    def readFile(self, filename):
        fstab = []
        f = open(filename, 'r')
        for line in f:
            if (not line.isspace() and not line.startswith('#') and not line.startswith('none')):
                fstabline = line.split()
                fstab.append(fstabline[1])

        fstab.sort()
        return fstab


    def isMounted(self, mountpoint, mounts):
        return mounts.count(mountpoint) > 0


    def mount(self, widget, mountpoint):
        self.execute_mount("mount " + mountpoint)

        mounts = self.readFile('/proc/mounts')
        if self.isMounted(mountpoint, mounts) and self.execute_command != '':
            command = self.execute_command.replace('%D', mountpoint)
            print command
            os.system(command)


    def execute_mount(self, command):
        output = os.system(command)
        self.initialize_dialog()
        self.dialog.show_all ()
        self.title.hide (self)


    def umount(self, widget, mountpoint):
        self.execute_mount("umount " + mountpoint)


class PreferenceDialog(gtk.Window):
    def __init__(self,applet):
        super(PreferenceDialog, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.applet = applet

        self.set_title("Preferences")
        vbox = gtk.VBox(True, 0)
        self.add(vbox)

        vbox1 = gtk.VBox(True, 0)
        label1 = gtk.Label("Space separated list of mount points not to show:")
        self.hidden_list = gtk.Entry(max=0)
        hidden_mounts_value = ''
        for mountpoint in applet.hidden_mounts:
            hidden_mounts_value += mountpoint
            hidden_mounts_value += ' '
        self.hidden_list.set_text(hidden_mounts_value)
        vbox1.pack_start(label1)
        vbox1.pack_end(self.hidden_list)
        vbox.pack_start(vbox1,True,False,2)

        vbox2 = gtk.VBox(True, 0)
        label2 = gtk.Label("Command to execute after successful mount")
        label3 = gtk.Label("(use %D for mounted directory):")
        self.execute_command = gtk.Entry(max=0)
        value = self.applet.execute_command
        self.execute_command.set_text(value)
        vbox2.pack_start(label2)
        vbox2.pack_start(label3)
        vbox2.pack_end(self.execute_command)
        vbox.pack_start(vbox2,True,False,2)

        hbox4 = gtk.HBox(True, 0)
        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", self.ok_button, "ok")
        hbox4.add(ok)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.cancel_button, "cancel")
        hbox4.add(cancel)
        vbox.pack_end(hbox4,True,False,2)


    def ok_button(self, widget, event):
        self.applet.gconf_client.set_list(self.applet.gconf_path + "/hidden_mounts", gconf.VALUE_STRING, self.hidden_list.get_text().rstrip().split(' '))
        self.applet.gconf_client.set_string(self.applet.gconf_path + "/execute_command", self.execute_command.get_text().strip())
        self.destroy()


    def cancel_button(self, widget, event):
        self.destroy()

if __name__ == "__main__":
    awn.init (sys.argv[1:])
    applet = MountApplet(awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()

