#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#     Please do not email the above person for support. The
#     email address is only there for license/copyright purposes.
#
# This is the login dialog for a calendar applet for Avant Window Navigator.
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


class CalendarLogin(gtk.Window):

    def crypt(self, sequence, key):
        sign = (key > 0) * 2 - 1
        random.seed(abs(key * sign))
        s = ''
        for i in xrange(len(sequence)):
            r = random.randint(0, 255)
            s += chr((ord(sequence[i]) + r * sign) % 128)
        return s

    def update_integ_text(self, integ_text):
        self.integ_text = integ_text
        self.set_title(_("Login to ") + self.integ_text)

    def __init__(self, applet):
        super(CalendarLogin, self).__init__()
        self.applet = applet
        self.update_integ_text(_("Online Calendar"))
        vbox = gtk.VBox(True, 0)
        self.add(vbox)

        hbox1 = gtk.HBox(True, 0)
        self.user_label = gtk.Label(_("Calendar Username"))
        hbox1.pack_start(self.user_label)
        self.user = gtk.Entry(40)
        self.user.set_text(self.applet.username)
        hbox1.pack_start(self.user)
        vbox.pack_start(hbox1, False, False, 2)

        hbox2 = gtk.HBox(True, 0)
        self.password_label = gtk.Label(_("Calendar Password"))
        hbox2.pack_start(self.password_label)
        self.password = gtk.Entry(20)
        self.password.set_visibility(False)
        self.password.grab_focus()
        #self.password.set_text(self.applet.password)
        hbox2.pack_start(self.password)
        vbox.pack_start(hbox2, False, False, 2)

        hbox3 = gtk.HBox(False, 0)
        self.save_password_checkbox = gtk.CheckButton(_("Save Password"))
        hbox3.pack_start(self.save_password_checkbox, True, False, 0)
        vbox.pack_start(hbox3, False, False, 0)

        hbox4 = gtk.HBox(True, 0)
        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", self.ok_button, "ok")
        hbox4.add(ok)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.cancel_button, "cancel")
        hbox4.add(cancel)
        vbox.pack_end(hbox4, True, False, 2)

    def ok_button(self, widget, event):
        self.applet.username = self.user.get_text()
        self.applet.password = self.crypt(self.password.get_text(), 17760704)
        saved_password = ""
        if self.save_password_checkbox.get_active() == True:
            warning = _("You have chosen to save your password.  Although the password will be stored in an encrypted format, there is always a remote possibility that your password can be stolen and decrypted if your computer's security is breached.  Are you still sure you want to save your password?")
            dialog = gtk.MessageDialog(parent=None, flags=gtk.DIALOG_MODAL,
                                       buttons=gtk.BUTTONS_YES_NO,
                                       type=gtk.MESSAGE_WARNING,
                                       message_format=warning)
            response = dialog.run()
            if response == gtk.RESPONSE_YES:
                saved_password = self.crypt(self.password.get_text(), 17760704)
            dialog.destroy()
        self.applet.set_string_config('username', self.user.get_text())
        self.applet.set_string_config('password', saved_password)
        self.hide()

    def cancel_button(self, widget, event):
        self.hide()
