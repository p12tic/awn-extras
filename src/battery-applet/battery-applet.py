#!/usr/bin/env python

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

import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk

import awn
import time
import dbus


class App (awn.AppletSimple):
    """An applet which displays battery information"""

    def __init__ (self, uid, orient, height):
        try:
            from dbus.mainloop.glib import DBusGMainLoop
            DBusGMainLoop(set_as_default=True)
            self.dService = "org.freedesktop.PowerManagement"
            self.dObjectPath = "/org/freedesktop/PowerManagement"
            self.dInterface = "org.freedesktop.PowerManagement"
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object(self.dService, self.dObjectPath)
            self.dbus_int = dbus.Interface(self.proxy_obj, self.dInterface)
            self.dbuson = True
        except:
            self.dbuson = False
            pass
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
        self.title = awn.awn_title_get_default ()
        self.set_temp_icon
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)
        if self.dbuson == True:
            self.dbus_int.connect_to_signal("OnBatteryChanged", self.checker, False)
        self.checker(True)

    def enter_notify (self, widget, event):
        self.title.show (self, self.percent + ' || '+ self.remaining)

    def leave_notify (self, widget, event):
        self.title.hide (self)

    def checker(self, x):
        """Parses the text returned from 'acpi -v' to get battery info"""
        height = self.height
        pipe = os.popen(r"acpi -V")
        raw_report = pipe.read()
        if "remaining" in raw_report:
            try:
                self.remaining = raw_report[raw_report.index('%,') + 3:raw_report.index('remaining') + 9]
            except:self.remaining = "Unknown"
        elif "until charged" in raw_report:
            try:
                self.remaining = raw_report[raw_report.index('%,') + 3:raw_report.index('until charged')+13]
            except:self.remaining = "Unknown"
        else: self.remaining = "Unknown"
        try:
            if "on-line" in raw_report:self.onac = True
            elif "off-line" in raw_report:self.onac = False
            else: self.onac = None
        except:pass
        pipe.close()
        try:
            var1 = raw_report[raw_report.index("%")-3:raw_report.index("%")]
            var1 = var1.replace(',','')
        except:var1 = "100"
        var1 = eval(var1)
        if self.onac == True: actoggle = "charging"
        elif self.onac == False: actoggle = "discharging"
        else: actoggle = "charging"
        self.percent = str(var1) + "%"
        var = var1
        location = __file__.replace('battery-applet.py','')
        icon0 = location + "icons/battery-" + actoggle + "-000" + ".svg"
        icon1 = location + "icons/battery-" + actoggle + "-020" + ".svg"
        icon2 = location + "icons/battery-" + actoggle + "-040" + ".svg"
        icon3 = location + "icons/battery-" + actoggle + "-060" + ".svg"
        icon4 = location + "icons/battery-" + actoggle + "-080" + ".svg"
        icon5 = location + "icons/battery-" + actoggle + "-100" + ".svg"
        icon = gdk.pixbuf_new_from_file (icon5)
        if var > 0 and var < 6.5:
            icon = gdk.pixbuf_new_from_file (icon0)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        if var > 6.6   and var < 20.5:
            icon = gdk.pixbuf_new_from_file (icon1)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        if var > 20.6 and var < 40.5:
            icon = gdk.pixbuf_new_from_file (icon2)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        if var > 40.6 and var < 60.5:
            icon = gdk.pixbuf_new_from_file (icon3)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        if var > 60.6 and var < 80.5:
            icon = gdk.pixbuf_new_from_file (icon4)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        if var > 80.6 and var < 101:
            icon = gdk.pixbuf_new_from_file (icon5)
            if height != icon.get_height():
                icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
        self.set_temp_icon(icon)
        if x == True:
            gobject.timeout_add (60000, self.checker, (True))


if __name__ == "__main__":
    awn.init (sys.argv[1:])
    applet = App (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
