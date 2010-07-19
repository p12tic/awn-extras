#!/usr/bin/python
# Copyright (c) 2007  Randal Barlow <im.tehk at gmail.com>
#               2008 - 2010  onox <denkpadje@gmail.com>
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
import subprocess
import sys
from threading import Thread

import pygtk
pygtk.require("2.0")
import gtk

import awn
from awn.extras import awnlib, __version__

import dbus
import pango

applet_name = "Quit-Log Out"
applet_description = "An applet to lock your screen, log out of your session, or shut down the system"

# Themed logo of the applet, shown in the GTK About dialog
applet_logo = "application-exit"

left_click_actions = ["Show Docklet", "Lock Screen", "Log Out", "Shut Down"]

user_name = commands.getoutput("/usr/bin/whoami")
log_out_label = "Log Out %s..." % user_name

docklet_actions_label_icon = {
"Lock Screen": ("Lock Screen", "system-lock-screen"),
"Log Out":     (log_out_label, "system-log-out"),
"Shut Down":   ("Shut Down...", "system-shutdown")
}

actions_label_icon = {
"Show Docklet": ("Show Docklet", "application-exit")
}
actions_label_icon.update(docklet_actions_label_icon)

action_args = {
"--lockscreen": "Lock Screen",
"--logout": "Log Out",
"--shutdown": "Shut Down"
}

action = sys.argv[1] if sys.argv[1] in action_args.keys() else None
if action is not None:
    del sys.argv[1]
    applet_logo = docklet_actions_label_icon[action_args[action]][1]


class QuitLogOutApplet:

    """An applet to lock your screen, log out of your session, or shut
    down the system.

    """

    def __init__(self, applet):
        self.applet = applet

        session_bus = dbus.SessionBus()
        services = session_bus.list_names()

        if "org.gnome.SessionManager" in services:
            sm_proxy = session_bus.get_object("org.gnome.SessionManager", "/org/gnome/SessionManager")
            self.sm_if = dbus.Interface(sm_proxy, "org.gnome.SessionManager")

            self.log_out_cb = self.gnome_log_out
        else:
            self.log_out_cb = self.other_log_out

            left_click_actions.remove("Shut Down")
            del docklet_actions_label_icon["Shut Down"]

        if "org.gnome.ScreenSaver" in services:
            ss_proxy = session_bus.get_object("org.gnome.ScreenSaver", "/")
            self.ss_if = dbus.Interface(ss_proxy, "org.gnome.ScreenSaver")

            self.lock_screen_cb = self.gnome_lock_screen
        else:
            self.lock_screen_cb = self.other_lock_screen

        self.load_settings()
        if action is None:
            self.setup_context_menu()
        else:
            left_click_actions.remove("Show Docklet")
            applet.settings["left-click-action"] = action_args[action]

        # Initialize tooltip and icon
        self.refresh_tooltip_icon_cb(self.applet.settings["left-click-action"])

        applet.connect("clicked", self.clicked_cb)

    def clicked_cb(self, widget):
        action = self.applet.settings["left-click-action"]
        if action == "Show Docklet":
            self.show_docklet()
        else:
            self.execute_action(action)

    def setup_context_menu(self):
        pref_dialog = self.applet.dialog.new("preferences")
        self.setup_dialog_settings(pref_dialog.vbox)

    def setup_docklet(self, window_id):

        def hover_cb(widget, event, effects):
            effects.start(awn.EFFECT_HOVER)

        def leave_cb(widget, event, effects):
            effects.stop(awn.EFFECT_HOVER)

        docklet = awn.Applet(self.applet.get_canonical_name(),
                             self.applet.props.uid,
                             self.applet.props.panel_id)
        docklet.props.quit_on_delete = False

        docklet_orientation = docklet.get_pos_type()
        top_bottom = docklet_orientation in (gtk.POS_TOP, gtk.POS_BOTTOM)

        align = awn.Alignment(docklet, 1 / 3.0)
        align.props.offset_multiplier = 0
        if top_bottom:
            box = gtk.HBox()
        else:
            box = gtk.VBox()
        box.set_spacing(10)
        align.props.scale = 0.3
        align.add(box)

        for i in docklet_actions_label_icon:
            label, icon = docklet_actions_label_icon[i]

            if docklet_orientation == gtk.POS_RIGHT:
                label_align = gtk.Alignment(xalign=1.0)
                label_align.set_padding(0, 0, 0, docklet.get_offset())
            elif docklet_orientation == gtk.POS_BOTTOM:
                label_align = gtk.Alignment(yalign=1.0)
                label_align.set_padding(0, docklet.get_offset(), 0, 0)
            elif docklet_orientation == gtk.POS_TOP:
                label_align = gtk.Alignment()
                label_align.set_padding(docklet.get_offset(), 0, 0, 0)
            else:
                label_align = gtk.Alignment()
                label_align.set_padding(0, 0, docklet.get_offset(), 0)

            # Event box
            event_box = gtk.EventBox()
            event_box.set_visible_window(False)
            box.pack_start(event_box, True, False)

            # HBox/VBox (container)
            if top_bottom:
                container = gtk.HBox()
            else:
                container = gtk.VBox()
            container.set_spacing(5)
            event_box.add(container)

            # Label
            label_label = awn.Label(label)
            label_align.add(label_label)
            if top_bottom:
                label_label.set_size_request(-1, docklet.get_size())
            else:
                label_label.set_size_request(docklet.get_size(), -1)

            # Label left/right
            if docklet_orientation == gtk.POS_LEFT:
                container.pack_start(label_align, False, False)
                label_label.props.angle = 90

            # Icon
            themed_icon = awn.ThemedIcon()
            themed_icon.set_info_simple(self.applet.meta["short"], docklet.props.uid, icon)
            pixbuf = themed_icon.get_icon_at_size((docklet.get_size() + docklet.props.max_size) / 2,
                                                  themed_icon.get_state())
            image = awn.Image()
            image.set_from_pixbuf(pixbuf)
            if top_bottom:
               image.set_padding(0, docklet.get_offset())
            else:
               image.set_padding(docklet.get_offset(), 0)
            container.pack_start(image, False, False)

            effects = image.get_effects()
            event_box.connect("enter-notify-event", hover_cb, effects)
            event_box.connect("leave-notify-event", leave_cb, effects)
            event_box.connect("button-release-event", self.apply_action_cb, i, docklet)

            # Label top/bottom
            if docklet_orientation != gtk.POS_LEFT:
                container.pack_start(label_align, False, False)
                if docklet_orientation == gtk.POS_RIGHT:
                    label_label.props.angle = 270

        docklet.add(align)
        gtk.Plug.__init__(docklet, long(window_id))
        docklet.show_all()

    def show_docklet(self):
        docklet_xid = self.applet.docklet_request(self.applet.get_size() * 3, True)
        if docklet_xid != 0:
            self.setup_docklet(docklet_xid)

    def refresh_tooltip_icon_cb(self, action):
        label, icon = actions_label_icon[action]
        self.applet.tooltip.set(label)
        self.applet.icon.theme(icon)

    def load_settings(self):
        if self.applet.settings["left-click-action"] not in left_click_actions:
            self.applet.settings["left-click-action"] = "Show Docklet"

        assert self.log_out_cb == self.gnome_log_out or "Shut Down" not in left_click_actions

    def setup_dialog_settings(self, vbox):
        hbox = gtk.HBox(spacing=12)
        # Use non-zero border width to align the entry with the close button
        hbox.set_border_width(5)
        vbox.add(hbox)

        combobox = gtk.combo_box_new_text()
        for i in left_click_actions:
            combobox.append_text(i)
        combobox.set_active(left_click_actions.index(self.applet.settings["left-click-action"]))
        combobox.connect("changed", self.action_changed_cb)

        label = gtk.Label("Left click _action:")
        label.set_use_underline(True)
        label.set_mnemonic_widget(combobox)

        hbox.add(label)
        hbox.add(combobox)

    def action_changed_cb(self, widget):
        self.applet.settings["left-click-action"] = left_click_actions[widget.get_active()]
        self.refresh_tooltip_icon_cb(self.applet.settings["left-click-action"])

    def apply_action_cb(self, widget, event, action, docklet):
        self.execute_action(action)
        docklet.destroy()

    def execute_action(self, action):
        assert action != "Show Docklet"

        if action == "Lock Screen":
            self.lock_screen_cb()
        elif action == "Log Out":
            self.log_out_cb()
        elif action == "Shut Down":
            assert self.log_out_cb == self.gnome_log_out

            self.gnome_shut_down()

    def gnome_lock_screen(self):

        def lock_screen():
            try:
                self.ss_if.Lock()
            except dbus.DBusException, e:
                # NoReply exception may occur even while the screensaver did lock the screen
                if e.get_dbus_name() != "org.freedesktop.DBus.Error.NoReply":
                    raise
        # Use a thread to avoid locking the GUI after unlocking the screensaver
        Thread(target=lock_screen).start()

    def gnome_log_out(self):
        self.sm_if.Logout(0)

    def gnome_shut_down(self):
        self.sm_if.Shutdown()

    def other_lock_screen(self):
        self.execute_command(self.applet.settings["lock-screen-command"])

    def other_log_out(self):
        self.execute_command(self.applet.settings["log-out-command"])

    def execute_command(self, command):
        try:
            subprocess.Popen(command)
        except OSError, e:
            if e.errno == 2:
                print "Couldn't execute command '%s'" % command
            else:
                raise


if __name__ == "__main__":
    awnlib.init_start(QuitLogOutApplet, {"name": applet_name, "short": "quit",
        "version": __version__,
        "description": applet_description,
        "theme": applet_logo,
        "author": "onox",
        "copyright-year": "2008 - 2010",
        "authors": ["Randal Barlow <im.tehk at gmail.com>", "onox <denkpadje@gmail.com>"]})
