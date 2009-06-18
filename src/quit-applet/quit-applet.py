#!/usr/bin/python
# Copyright (c) 2007  Randal Barlow <im.tehk at gmail.com>
#               2008 - 2009  onox <denkpadje@gmail.com>
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
# License along with this library.  If not, see <http://www.gnu.org/licenses/>.

import commands

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import awnlib

import dbus

applet_name = "Quit-Log Out"
applet_version = "0.3.3"
applet_description = "An applet to lock your screen, log out of your session, or shut down the system"

# Themed logo of the applet, shown in the GTK About dialog
applet_logo = "application-exit"

left_click_actions = ("Lock Screen", "Log Out", "Shut Down")


class QuitLogOutApplet:

    """An applet to lock your screen, log out of your session, or shut
    down the system.

    """

    def __init__(self, applet):
        self.applet = applet

        self.setup_context_menu()

        # Initialize tooltip and icon
        self.refresh_tooltip_icon_cb(self.settings["left-click-action"])

        session_bus = dbus.SessionBus()

        sm_proxy = session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
        self.sm_if = dbus.Interface(sm_proxy, "org.gnome.SessionManager")

        ss_proxy = session_bus.get_object("org.gnome.ScreenSaver", "/")
        self.ss_if = dbus.Interface(ss_proxy, "org.gnome.ScreenSaver")

        applet.connect("button-press-event", self.button_press_event_cb)

    def button_press_event_cb(self, widget, event):
        if event.button == 1:
            self.left_click_cb()

    def setup_context_menu(self):
        pref_dialog = self.applet.dialog.new("preferences")
        self.setup_dialog_settings(pref_dialog.vbox)

    def refresh_tooltip_icon_cb(self, action_index):
        action = left_click_actions[action_index]

        if action == "Lock Screen":
            self.applet.tooltip.set("Lock Screen")
            self.applet.icon.theme("system-lock-screen")
        elif action == "Log Out":
            user_name = commands.getoutput("/usr/bin/whoami")
            self.applet.tooltip.set("Log Out %s..." % user_name)
            self.applet.icon.theme("system-log-out")
        elif action == "Shut Down":
            self.applet.tooltip.set("Shut Down...")
            self.applet.icon.theme("system-shutdown")

    def setup_dialog_settings(self, vbox):
        defaults = {
            "left-click-action": (left_click_actions.index("Log Out"), self.refresh_tooltip_icon_cb)
        }
        self.settings = self.applet.settings.load_preferences(defaults)

        hbox = gtk.HBox(spacing=12)
        # Use non-zero border width to align the entry with the close button
        hbox.set_border_width(5)
        vbox.add(hbox)

        combobox = gtk.combo_box_new_text()
        for i in left_click_actions:
            combobox.append_text(i)
        combobox.set_active(self.settings["left-click-action"])
        combobox.connect("changed", self.action_changed_cb) 

        label = gtk.Label("Left click _action:")
        label.set_use_underline(True)
        label.set_mnemonic_widget(combobox)

        hbox.add(label)
        hbox.add(combobox)

    def action_changed_cb(self, widget):
        self.applet.settings["left-click-action"] = widget.get_active()

    def left_click_cb(self):
        action = left_click_actions[self.settings["left-click-action"]]

        if action == "Lock Screen":
            try:
                self.ss_if.Lock()
            except dbus.DBusException, e:
                # NoReply exception may occur even while the screensaver did lock the screen
                if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
                    raise
        elif action == "Log Out":
            self.sm_if.Logout(0)
        elif action == "Shut Down":
            self.sm_if.Shutdown()


if __name__ == "__main__":
    awnlib.init_start(QuitLogOutApplet, {"name": applet_name, "short": "quit",
        "version": applet_version,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox",
        "copyright-year": "2008 - 2009",
        "authors": ["Randal Barlow <im.tehk at gmail.com>", "onox <denkpadje@gmail.com>"]},
        ["settings-per-instance"])
