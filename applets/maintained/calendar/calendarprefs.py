#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#     Please do not email the above person for support. The
#     email address is only there for license/copyright purposes.
#
# This is the preferences dialog for a calendar applet for Avant Window
# Navigator.
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
#
import gtk
import random
from awn.extras import _


class CalendarPrefs(gtk.Window):

    # There *must* be a more "Pythonic" way to do this:
    int_opt = {
        "None": 0,
        "Evolution": 1,
        "Google Calendar": 2,
        "Outlook Web Access": 3}
    int_opt_inv = {
        0: "None",
        1: "Evolution",
        2: "Google Calendar",
        3: "Outlook Web Access"}

    clock_appearance = {
        _("Classic LCD"): ("667F66FF", "000000FF", "000000FF", False),
        _("Indy Glow LCD"): ("22B7B7FF", "000000FF", "000000FF", False),
        _("Backlit Amber LCD"): ("AA4A3AFF", "000000FF", "000000FF", False),
        _("Backlit Green LCD"): ("337A33FF", "000000FF", "000000FF", False),
        _("Green LED"): ("000000FF", "00FF66FF", "000000FF", False),
        _("Red LED"): ("000000FF", "FF2211FF", "000000FF", False),
        _("Blue LED"): ("000000FF", "00AAFFFF", "000000FF", False),
        _("Plain White"): ("0000008F", "FFFFFFFF", "000000FF", True),
        _("Plain Black"): ("0000003F", "000000FF", "000000FF", True)}

    calendar_appearance = {
        _("Red"): "calendar-red.png",
        _("Green"): "calendar-green.png",
        _("Blue"): "calendar-blue.png",
        _("Gray"): "calendar-gray.png",
        _("Black"): "calendar-black.png"}

    def crypt(self, sequence, key):
        sign = (key > 0) * 2 - 1
        random.seed(abs(key * sign))
        s = ''
        for i in xrange(len(sequence)):
            r = random.randint(0, 255)
            s += chr((ord(sequence[i]) + r * sign) % 128)
        return s

    def __init__(self, applet):
        super(CalendarPrefs, self).__init__()
        self.applet = applet
        self.set_title(_("Preferences"))
        vbox = gtk.VBox(True, 0)
        self.add(vbox)

        cal_appearance_index = \
            self.applet.get_int_config('cal_appearance_index')
        clock_appearance_index = \
            self.applet.get_int_config('clock_appearance_index')

        self.twelve_hour_checkbox = gtk.CheckButton(_("Twelve Hour Clock"))
        self.twelve_hour_checkbox.set_active(applet.twelve_hour_clock)
        hbox0 = gtk.HBox(False, 0)
        hbox0.pack_start(self.twelve_hour_checkbox, True, False, 0)
        vbox.pack_start(hbox0, False, False, 0)

#        self.blink_checkbox = gtk.CheckButton(_("Blinking Colon"))
#        if applet.blinky_colon == True:
#            self.blink_checkbox.set_active(True)
#        else:
#            self.blink_checkbox.set_active(False)
#        hbox1 = gtk.HBox(False,0)
#        hbox1.pack_start(self.blink_checkbox,True,False,0)
#        vbox.pack_start(hbox1,False,False,0)

        hbox1a = gtk.HBox(True, 0)
        self.clock_appear_combo = gtk.combo_box_new_text()
        for item in self.clock_appearance.keys():
            self.clock_appear_combo.append_text(item)
        self.clock_appear_combo.set_active(clock_appearance_index)
        clock_appear_label = gtk.Label(_("Clock Appearance"))
        hbox1a.pack_start(clock_appear_label, True, False, 0)
        hbox1a.pack_start(self.clock_appear_combo, True, True, 0)
        vbox.pack_start(hbox1a, True, False, 0)

        hbox1b = gtk.HBox(True, 0)
        self.cal_appear_combo = gtk.combo_box_new_text()
        for item in self.calendar_appearance.keys():
            self.cal_appear_combo.append_text(item)
        self.cal_appear_combo.set_active(cal_appearance_index)
        cal_appear_label = gtk.Label(_("Calendar Appearance"))
        hbox1b.pack_start(cal_appear_label, True, False, 0)
        hbox1b.pack_start(self.cal_appear_combo, True, True, 0)
        vbox.pack_start(hbox1b, True, False, 0)

        hbox2 = gtk.HBox(True, 0)
        self.integ_combo = gtk.combo_box_new_text()
        self.integ_combo.append_text(_("None"))
        self.integ_combo.append_text(_("Evolution"))
        self.integ_combo.append_text(_("Google Calendar"))
        self.integ_combo.append_text(_("Outlook Web Access"))
        self.integ_combo.set_active(self.int_opt[applet.integ_text])
        self.integ_combo.connect("changed", self.combo_changed, "bla")
        int_label = gtk.Label(_("Calendar Integration"))
        hbox2.pack_start(int_label, True, False, 0)
        hbox2.pack_start(self.integ_combo, True, True, 0)
        vbox.pack_start(hbox2, True, False, 0)

        #hbox3 = gtk.HBox(True, 0)
        #self.user_label = gtk.Label(_("Calendar Username"))
        #hbox3.pack_start(self.user_label)
        #self.user = gtk.Entry(40)
        #self.user.set_text(self.applet.username)
        #hbox3.pack_start(self.user)
        #vbox.pack_start(hbox3,False,False,2)

        #hbox4 = gtk.HBox(True, 0)
        #self.password_label = gtk.Label(_("Calendar Password"))
        #hbox4.pack_start(self.password_label)
        #self.password = gtk.Entry(20)
        #self.password.set_visibility(False)
        #self.password.set_text(self.applet.password)
        #hbox4.pack_start(self.password)
        #vbox.pack_start(hbox4,False,False,2)

        hbox5 = gtk.HBox(True, 0)
        self.url_label = gtk.Label(_("Calendar URL"))
        hbox5.pack_start(self.url_label)
        self.url = gtk.Entry(50)
        self.url.set_text(self.applet.url)
        hbox5.pack_start(self.url)
        vbox.pack_start(hbox5, False, False, 2)

        hbox6 = gtk.HBox(True, 0)
        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", self.ok_button, "ok")
        hbox6.add(ok)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.cancel_button, "cancel")
        hbox6.add(cancel)
        vbox.pack_end(hbox6, True, False, 2)

        self.set_credential_sensitivity()

    def set_credential_sensitivity(self):
        option = self.int_opt_inv[self.integ_combo.get_active()]
        if option == "Google Calendar" or option == "Outlook Web Access":
            #self.user_label.set_sensitive(True)
            #self.user.set_sensitive(True)
            #self.password_label.set_sensitive(True)
            #self.password.set_sensitive(True)
            if option == "Google Calendar":
                self.url_label.set_sensitive(False)
                self.url.set_sensitive(False)
            else:
                self.url_label.set_sensitive(True)
                self.url.set_sensitive(True)
        else:
            #self.user_label.set_sensitive(False)
            #self.user.set_sensitive(False)
            #self.password_label.set_sensitive(False)
            #self.password.set_sensitive(False)
            self.url_label.set_sensitive(False)
            self.url.set_sensitive(False)

    def combo_changed(self, widget, bla):
        self.set_credential_sensitivity()

    def ok_button(self, widget, event):
        integration = self.int_opt_inv[self.integ_combo.get_active()]
        self.applet.set_string_config('integration', integration)
        #self.applet.set_string_config('username', self.user.get_text())
        #self.applet.set_string_config('password',
        #                              self.crypt(self.password.get_text(),
        #                                         17760704))
        self.applet.set_string_config('url', self.url.get_text())
        self.applet.set_boolean_config('twelve_hour_clock',
                                       self.twelve_hour_checkbox.get_active())
        #self.applet.set_boolean_config('blinking_colon',
        #                    self.blink_checkbox.get_active())
        background, text, border, plain = \
            self.clock_appearance[self.clock_appear_combo.get_active_text()]
        self.applet.set_string_config('clock_background', background)
        self.applet.set_string_config('clock_foreground', text)
        self.applet.set_string_config('clock_border', border)
        self.applet.set_boolean_config('clock_plain', plain)
        graphic = \
            self.calendar_appearance[self.cal_appear_combo.get_active_text()]
        self.applet.set_string_config('graphic', graphic)
        self.applet.set_int_config('clock_appearance_index',
                                   self.clock_appear_combo.get_active())
        self.applet.set_int_config('cal_appearance_index',
                           self.cal_appear_combo.get_active())
        self.destroy()

    def cancel_button(self, widget, event):
        self.destroy()
