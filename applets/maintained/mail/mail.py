#!/usr/bin/env python
# Copyright (C) 2008  Pavel Panchekha <pavpanchekha@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import email
import gettext
import os
import re
import subprocess
import socket

import pygtk
pygtk.require("2.0")
import gtk

from awn.extras import _, awnlib, __version__

system_theme_name = "System theme"

theme_dir = "/usr/share/icons"
icon_dir = os.path.join(os.path.dirname(__file__), "icons")
mail_theme_dir = os.path.join(os.path.dirname(__file__), "themes")
ui_file = os.path.join(os.path.dirname(__file__), "mail.ui")


def strMailMessages(num):
    return gettext.ngettext("You have %d new message", "You have %d new messages", num) % num


def strMessages(num):
    return gettext.ngettext("%d unread message", "%d unread messages", num) % num


def get_label_entry(text, label_group=None):
    hbox = gtk.HBox(False, 12)

    label = gtk.Label(text)
    label.set_alignment(0.0, 0.5)
    hbox.pack_start(label, expand=False)

    entry = gtk.Entry()
    hbox.pack_start(entry)

    if label_group is not None:
        label_group.add_widget(label)

    return (entry, hbox)


class MailApplet:

    def __init__(self, applet):
        self.awn = applet

        self.awn.errors.module(globals(), "feedparser")

        self.setup_context_menu()

        self.back = getattr(Backends(), self.awn.settings["backend"])

        self.setup_themes()

        self.awn.theme.icon("login")
        self.awn.tooltip.set(_("Mail Applet (Click to Log In)"))

        self.__dialog = MainDialog(self)
        
        # Login from key or dialog
        self.init_keyring()
        login_data = self.get_data_from_key(self.get_key())
        if login_data:
            self.login(login_data, startup=True)
        else:
            self.__dialog.login_form()
            #self.awn.dialog.toggle("main", "show")

    def init_keyring(self):
        self.keyring = None
        try:
            self.keyring = awnlib.Keyring()
        except awnlib.KeyRingError:
            pass

    def get_key(self):
        '''Get key for backend from Gnome Keyring'''

        if not self.keyring:
            return None

        if self.back.__name__ == "UnixSpool":
            return None
        
        identify = "Awn Extras/Mail/" + self.back.__name__
        try:
            keys = self.keyring.from_attributes({'id': identify}, 'generic')
            if len(keys) > 1:
                print "Warning from Mail Applet: You have more than one key " + \
                      "with id '%s'. Using the first one." % identify
            return keys[0]
        except awnlib.KeyRingError:
            return None

    def get_data_from_key(self, key):
        if not self.keyring or not key:
            return None
        
        try:
            data = key.attrs
            data['password'] = key.password
        except awnlib.KeyRingError:
            return None

        return data

    def save_key(self, data):
        '''Save login data for backend in Gnome Keyring'''

        if not self.keyring or not data:
            return

        if self.back.__name__ == "UnixSpool":
            return

        identify = "Awn Extras/Mail/" + self.back.__name__
        password = data['password']
        attrs = data.copy()
        del attrs['password']
        attrs['id'] = identify

        # Overwrite existing key, do not double it or we run into problems
        key = self.get_key()
        if key:
            try:
                key.password = password
                key.attrs = attrs
            except awnlib.KeyRingError:
                pass  # not successfull, propably cancelled by user,
                      # so we don't have to send a message
        else:
           try:
               self.keyring.new(
                   keyring=None,
                   name=identify,
                   pwd=password,
                   attrs=attrs,
                   type='generic')
           except awnlib.KeyRingError:
                pass  # not successfull, propably cancelled by user,
                      # so we don't have to send a message

    def check_login_data(self, data):
        if self.back.__name__ == "GMail":
            fields = ['username', 'password']
        elif self.back.__name__ == "GApps":
            fields = ['username', 'domain', 'password']
        elif self.back.__name__ == "POP":
            fields = ['username', 'url', 'usessl', 'password']
        elif self.back.__name__ == "IMAP":
            fields = ['username', 'url', 'usessl', 'folder', 'password']
        else:
            # UnixSpool has no password
            return
        
        for field in fields:
            if field not in data:
                raise RuntimeError("Wrong or corrupt key")
            if data[field] is None or data[field] == '':
                raise RuntimeError("Please fill in every field")

    def logout(self):
        if hasattr(self, "timer"):
            self.timer.stop()
        self.awn.theme.icon("login")
        self.awn.tooltip.set(_("Mail Applet (Click to Log In)"))

    def login(self, data, startup=False):
        try:
            self.mail = self.back(data)  # Initialize backend, check login data
                                         # IMAP backend connects to server
        except RuntimeError, error:
            self.__dialog.login_form(True, str(error))
        else:
            try:
                self.mail.update()  # Connect to server
            except RuntimeError, error:
                self.__dialog.login_form(True, str(error))

            else:
                # Login successful
                self.awn.notification.send(_("Mail Applet"),
                    _("Logging in as %s") % data["username"],
                    self.__getIconPath("login"))

                self.awn.theme.icon("read")

                self.save_key(data)  # TODO key is actually saved every
                                     # login again, even if it didn't change

                self.timer = self.awn.timing.register(self.refresh,
                                                     self.awn.settings["timeout"] * 60)
                if startup and self.awn.settings["hide"]:
                    self.awn.timing.delay(self.refresh, 0.1)  # init must finish first
                else:
                    self.refresh(show=False)

    def refresh(self, show=True):
        oldSubjects = self.mail.subjects

        try:
            self.mail.update()
        except RuntimeError, e:
            self.awn.theme.icon("error")

            if self.awn.settings["show-network-errors"]:
                self.awn.notification.send(_("Network error - Mail Applet"), str(e), "")
            return

        diffSubjects = [i for i in self.mail.subjects if i not in oldSubjects]

        if len(diffSubjects) > 0:
            msg = strMailMessages(len(diffSubjects)) + ":\n" + \
                                                        "\n".join(diffSubjects)

            self.awn.notification.send(_("New Mail - Mail Applet"), msg,
                                 self.__getIconPath("mail-unread"))

        self.awn.tooltip.set(strMessages(len(self.mail.subjects)))

        self.awn.theme.icon("unread" if len(self.mail.subjects) > 0 else "read")

        if self.awn.settings["hide"] and len(self.mail.subjects) == 0:
            self.awn.icon.hide()
            self.awn.dialog.hide()
        elif show:
            self.awn.show()

        self.__dialog.update_email_list()

    def __getIconPath(self, name):
        path = os.path.join(mail_theme_dir, self.awn.settings["theme"], "scalable", name + ".svg")
        if os.path.isfile(path):
            return path
        else:
            path = os.path.join(theme_dir, self.awn.settings["theme"], "scalable/status", name + ".svg")
            if os.path.isfile(path):
                return path
            else:
                return os.path.join(icon_dir, name + ".svg")

    def showWeb(self):
        if hasattr(self.mail, "showWeb"):
            self.mail.showWeb()
        elif hasattr(self.mail, "url"):
            subprocess.Popen(["xdg-open", self.mail.url()])

    def showDesk(self):
        if hasattr(self.mail, "showDesk"):
            self.mail.showDesk()
        else:
            # Now if xdg-open had an option to just open the email client,
            # not start composing a message, that would be just wonderful.
            use_shell = " " in self.awn.settings["email-client"]
            subprocess.Popen(self.awn.settings["email-client"], shell=use_shell)

    def setup_themes(self):
        """Loads themes and states.

        """
        states = {
            "error": "error",
            "login": "login",
            "read": "mail-read",
            "unread": "mail-unread"}

        self.awn.theme.set_states(states)
        theme = self.awn.settings["theme"] if self.awn.settings["theme"] != system_theme_name else None
        self.awn.theme.theme(theme)

    def setup_context_menu(self):
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        preferences_vbox = self.awn.dialog.new("preferences").vbox
        prefs.get_object("dialog-vbox").reparent(preferences_vbox)

        self.setup_preferences(prefs)

    def setup_preferences(self, prefs):
        def change_timeout(value):
            if hasattr(self, "timer"):
                self.timer.change_interval(value * 60)

        # Only use themes that are likely to provide all the files
        def filter_theme(theme):
            return os.path.isfile(os.path.join(theme_dir, theme, "scalable/status/mail-read.svg")) \
                or os.path.isfile(os.path.join(theme_dir, theme, "48x48/status/mail-read.png"))
        themes = filter(filter_theme, os.listdir(theme_dir))
        themes = [system_theme_name] + sorted(themes) + sorted(os.listdir(mail_theme_dir))

        combobox_theme = prefs.get_object("combobox-theme")
        awnlib.add_cell_renderer_text(combobox_theme)
        for theme in themes:
            combobox_theme.append_text(theme)
        if self.awn.settings["theme"] not in themes:
            self.awn.settings["theme"] = system_theme_name

        binder = self.awn.settings.get_binder(prefs)
        binder.bind("theme", "combobox-theme", key_callback=self.awn.theme.theme)
        binder.bind("email-client", "entry-client")
        binder.bind("hide", "checkbutton-hide-applet", key_callback=self.refresh_hide_applet)
        binder.bind("show-network-errors", "checkbutton-alert-errors")
        binder.bind("timeout", "spinbutton-timeout", key_callback=change_timeout)
        self.awn.settings.load_bindings(binder)

    def refresh_hide_applet(self, value):
        if hasattr(self, "mail") and value and len(self.mail.subjects) == 0:
            self.awn.icon.hide()
            self.awn.dialog.hide()
        else:
            self.awn.show()


class MainDialog:

    def __init__(self, parent):

        self.__parent = parent
        self.__dialog = parent.awn.dialog.new("main", _("Mail"))
        self.__current_type = None

    def __remove_current(self):
        """Checks if dialog already has some content and removes it"""
        if (len(self.__dialog.child.child.get_children()) > 1):
            # Destroy current dialog vbox
            self.__dialog.child.child.get_children()[-1].destroy()

    def email_list(self):
        """
        Creates a dialog with mail subjects and 3-4 buttons

        """
        self.__remove_current()
        self.__current_type = "email_list"

        vbox = gtk.VBox()
        self.__dialog.add(vbox)

        # Create table of new e-mails
        self.__email_list = gtk.Label()
        vbox.add(self.__email_list)

        # Buttons
        hbox_buttons = gtk.HBox()

        if hasattr(self.__parent.mail, "url") or \
                                        hasattr(self.__parent.mail, "showWeb"):
            # Don't show the button if it doesn't do anything

            # This'll be the "show web interface" button
            b = gtk.Button()
            b.set_relief(gtk.RELIEF_NONE)  # Found it; that's a relief
            b.set_image(gtk.image_new_from_stock(gtk.STOCK_NETWORK,
                                                 gtk.ICON_SIZE_BUTTON))
            b.set_tooltip_text(_("Open Web Mail"))
            b.connect("clicked", lambda x: self.__parent.showWeb())
            hbox_buttons.add(b)

        # This is the "show desktop client" button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT,
                                             gtk.ICON_SIZE_BUTTON))
        b.set_tooltip_text(_("Open Desktop Client"))
        b.connect("clicked", lambda x: self.__parent.showDesk())
        hbox_buttons.add(b)

        # Refresh button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH,
                                             gtk.ICON_SIZE_BUTTON))
        b.set_tooltip_text(_("Refresh"))
        b.connect("clicked", lambda x: self.__parent.refresh())
        hbox_buttons.add(b)

        # Log out
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_STOP,
                                             gtk.ICON_SIZE_BUTTON))
        b.set_tooltip_text(_("Log Out"))
        b.connect("clicked", lambda x: self.__parent.logout())
        b.connect("clicked", lambda x: self.login_form())
        hbox_buttons.add(b)

        vbox.pack_end(hbox_buttons)
        vbox.show_all()

    def update_email_list(self):
        if self.__current_type is not "email_list":
            self.email_list()

        parent = self.__email_list.get_parent()
        parent.remove(self.__email_list)

        mail = self.__parent.mail
        if len(mail.subjects) > 0:
            self.__dialog.set_title(strMessages(len(self.__parent.mail.subjects)))

            self.__email_list = gtk.Table(len(self.__parent.mail.subjects), 2)
            self.__email_list.set_col_spacings(10)
            for i in xrange(len(mail.subjects)):
                label = gtk.Label("<b>" + str(i + 1) + "</b>")
                label.set_use_markup(True)
                self.__email_list.attach(label, 0, 1, i, i + 1)

                label = gtk.Label(mail.subjects[i])
                label.set_use_markup(True)
                self.__email_list.attach(label, 1, 2, i, i + 1)
        else:
            self.__dialog.set_title(_("No unread messages"))

            self.__email_list = gtk.Label("<i>%s</i>" % _("No new messages"))
            self.__email_list.set_use_markup(True)

        self.__email_list.show_all()
        parent.pack_start(self.__email_list)

    def __login_get_widgets(self, vbox, *groups):
        for widget in self.login_widgets:
            widget.destroy()

        t = self.__parent.back.drawLoginWindow(*groups)
        self.login_widgets.append(t["layout"])
        vbox.add(t["layout"])
        vbox.show_all()
        return t

    def login_form(self, error=False, message=_("Wrong username or password")):
        """
        Creates a dialog the login form

        """
        self.__remove_current()
        self.__current_type = "login_form"

        self.__dialog.set_title(_("Log In"))
        self.callback = None

        vbox = gtk.VBox(spacing=12)
        vbox.set_border_width(6)
        self.__dialog.add(vbox)

        # Make all the labels the same size
        label_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        # Display an error message if there is an error
        if error:
            image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR,
                                             gtk.ICON_SIZE_MENU)
            label = gtk.Label("<b>" + message + "</b>")
            label.set_use_markup(True)

            hbox = gtk.HBox(False, 6)
            hbox.pack_start(image, False)
            hbox.pack_start(label)

            # Align the image and label in the center, with the image
            # right next to the label
            hboxbox = gtk.HBox(False)
            hboxbox.pack_start(hbox, True, False)

            vbox.add(hboxbox)

        # Allow user to change the backend in the login dialog
        def changed_backend_cb(combobox, label_group):
            backend = combobox.get_active()

            if backend != -1:
                backends = [i for i in dir(Backends) if i[:2] != "__"]
                self.__parent.awn.settings["backend"] = backends[backend]
                self.__parent.back = getattr(Backends(), backends[backend])
                #self.__login_get_widgets(vbox, label_group)
                self.callback = self.__login_get_widgets(vbox, label_group)
                # TODO if there was an error message remove it
                login_data = self.__parent.get_data_from_key(self.__parent.get_key())
                if login_data:
                    try:
                        self.__parent.check_login_data(login_data)
                        self.callback['fill-in'](self.callback['widgets'], login_data)
                    except RuntimeError:
                        pass

        label_backend = gtk.Label(_("Type:"))
        label_backend.set_alignment(0.0, 0.5)
        label_group.add_widget(label_backend)

        combobox_backend = gtk.combo_box_new_text()
        combobox_backend.set_title(_("Backend"))
        backends = [i for i in dir(Backends) if i[:2] != "__"]
        for i in backends:
            combobox_backend.append_text(getattr(Backends(), i).title)
        combobox_backend.set_active(
                             backends.index(self.__parent.awn.settings["backend"]))
        combobox_backend.connect("changed", changed_backend_cb, label_group)

        hbox_backend = gtk.HBox(False, 12)
        hbox_backend.pack_start(label_backend, expand=False)
        hbox_backend.pack_start(combobox_backend)

        vbox.add(hbox_backend)

        self.login_widgets = []
        self.callback = self.__login_get_widgets(vbox, label_group)
        login_data = self.__parent.get_data_from_key(self.__parent.get_key())
        if login_data:
            try:
                self.__parent.check_login_data(login_data)
                self.callback['fill-in'](self.callback['widgets'], login_data)
            except RuntimeError:
                pass

        image_login = gtk.image_new_from_stock(gtk.STOCK_NETWORK,
                                               gtk.ICON_SIZE_BUTTON)
        submit_button = gtk.Button(label=_("Log In"), use_underline=False)
        submit_button.set_image(image_login)
        # TODO make button insensitive as long as required fields are not filled in
        # TODO make button default action for entries

        def onsubmit(widget):
            self.__parent.login(
                                self.callback["callback"](self.callback["widgets"]))
        submit_button.connect("clicked", onsubmit)

        hbox_login = gtk.HBox(False, 0)
        hbox_login.pack_start(submit_button, True, False)
        vbox.pack_end(hbox_login)

        vbox.show_all()


class MailItem:

    def __init__(self, subject, author):
        self.subject = subject
        self.author = author


class Backends:

    class GMail:

        title = "Gmail"

        def __init__(self, data):
            self.data = data
            check_login_data(self.data)

        def url(self):
            return "https://mail.google.com/mail/"

        def update(self):
            f = feedparser.parse(\
                "https://%s:%s@mail.google.com/gmail/feed/atom" \
                            % (self.data["username"], self.data['password']))

            if "bozo_exception" in f.keys():
                raise RuntimeError(_("There seem to be problems with our \
connection to your account. Your best bet is probably \
to log out and try again."))
            # Hehe, Google is funny. Bozo exception

            t = []
            self.subjects = []
            for i in f.entries:
                if "title" in i:
                    i.title = self.__cleanGmailSubject(i.title)
                else:
                    i.title = _("[No Subject]")
                if not "author" in i:
                    i.author = _("[Unknown]")
                t.append(MailItem(i.title, i.author))
                self.subjects.append(i.title)

        def __cleanGmailSubject(self, n):
            n = re.sub(r"^[^>]*\\>", "", n)  # "sadf\>fdas" -> "fdas"
            n = re.sub(r"\\[^>]*\\>$", "", n)  # "asdf\afdsasdf\>" -> "asdf"
            n = n.replace("&quot;", "\"")
            n = n.replace("&amp;", "&")
            n = n.replace("&nbsp;", "")

            if len(n) > 37:
                n = n[:37] + "..."
            elif n == "":
                n = _("[No Subject]")
            return n

        def __cleanMsg(self, n):
            n = re.sub("\n\s*\n", "\n", n)
            n = re.sub("&[#x(0x)]?\w*;", " ", n)
            n = re.sub("\<[^\<\>]*?\>", "", n)  # "<h>asdf<a></h>" -> "asdf"

            f = False
            h = []
            n = n.split("\n")
            for line in n:
                if f:
                    h.append(line)
                elif re.match("X-Spam-Score", line):
                    f = True
            n = "\n".join(h)
            # Get source of message
            return n

        @classmethod
        def drawLoginWindow(cls, *groups):
            vbox = gtk.VBox(spacing=12)

            usrE, box = get_label_entry(_("Username:"), *groups)
            vbox.add(box)

            pwdE, box = get_label_entry(_("Password:"), *groups)
            pwdE.set_visibility(False)
            vbox.add(box)

            return {"layout": vbox, "callback": cls.__submitLoginWindow,
                "widgets": [usrE, pwdE],
                "fill-in": cls.__fillinLoginWindow}

        @staticmethod
        def __submitLoginWindow(widgets):
            return {'username': widgets[0].get_text(), \
                    'password': widgets[1].get_text()}

        @staticmethod
        def __fillinLoginWindow(widgets, data):
            widgets[0].set_text(data['username'])
            widgets[1].set_text(data['password'])


    class GApps:

        title = _("Google Apps")

        def __init__(self, data):
            self.data = data
            check_login_data(self.data)

        def url(self):
            return "https://mail.google.com/a/%s" % self.data["domain"]

        def update(self):
            f = feedparser.parse(\
                "https://%s%%40%s:%s@mail.google.com/a/%s/feed/atom" \
                 % (self.data["username"], self.data["domain"], \
                    self.data['password'], self.data["domain"]))

            if "bozo_exception" in f.keys():
                raise RuntimeError(_("There seem to be problems with our \
connection to your account. Your best bet is probably \
to log out and try again."))
            # Hehe, Google is funny. Bozo exception

            t = []
            self.subjects = []
            for i in f.entries:
                if "title" in i:
                    i.title = self.__cleanGmailSubject(i.title)
                else:
                    i.title = _("[No Subject]")
                if not "author" in i:
                    i.author = _("[Unknown]")
                t.append(MailItem(i.title, i.author))
                self.subjects.append(i.title)

        def __cleanGmailSubject(self, n):
            n = re.sub(r"^[^>]*\\>", "", n)  # "sadf\>fdas" -> "fdas"
            n = re.sub(r"\\[^>]*\\>$", "", n)  # "asdf\afdsasdf\>" -> "asdf"
            n = n.replace("&quot;", "\"")
            n = n.replace("&amp;", "&")
            n = n.replace("&nbsp;", "")

            if len(n) > 37:
                n = n[:37] + "..."
            elif n == "":
                n = _("[No Subject]")
            return n

        def __cleanMsg(self, n):
            n = re.sub("\n\s*\n", "\n", n)
            n = re.sub("&[#x(0x)]?\w*;", " ", n)
            n = re.sub("\<[^\<\>]*?\>", "", n)  # "<h>asdf<a></h>" -> "asdf"

            f = False
            h = []
            n = n.split("\n")
            for line in n:
                if f:
                    h.append(line)
                elif re.match("X-Spam-Score", line):
                    f = True
            n = "\n".join(h)
            # Get source of message
            return n

        @classmethod
        def drawLoginWindow(cls, *groups):
            vbox = gtk.VBox(spacing=12)

            usrE, box = get_label_entry(_("Username:"), *groups)
            vbox.add(box)

            pwdE, box = get_label_entry(_("Password:"), *groups)
            pwdE.set_visibility(False)
            vbox.add(box)

            domE, box = get_label_entry(_("Domain:"), *groups)
            vbox.add(box)

            return {"layout": vbox, "callback": cls.__submitLoginWindow,
                "widgets": [usrE, pwdE, domE],
                "fill-in": cls.__fillinLoginWindow}

        @staticmethod
        def __submitLoginWindow(widgets):
            return {'username': widgets[0].get_text(), \
                    'password': widgets[1].get_text(), \
                    'domain': widgets[2].get_text()}

        @staticmethod
        def __fillinLoginWindow(widgets, data):
            widgets[0].set_text(data['username'])
            widgets[1].set_text(data['password'])
            widgets[2].set_text(data['domain'])

    try:
        global mailbox
        import mailbox
    except:
        pass
    else:

        class UnixSpool:

            title = _("Unix Spool")

            def __init__(self, data):
                check_login_data(data)
                self.path = data["path"]

            def update(self):
                try:
                    self.box = mailbox.mbox(self.path)
                except IOError, e:
                    raise RuntimeError(e)
                email = []

                self.subjects = []
                for i, msg in self.box.items():
                    if "subject" in msg:
                        subject = msg["subject"]
                    else:
                        subject = _("[No Subject]")

                    self.subjects.append(subject)

            @classmethod
            def drawLoginWindow(cls, *groups):
                vbox = gtk.VBox(spacing=12)

                path, box = get_label_entry(_("Spool Path:"), *groups)
                vbox.add(box)

                path.set_text("/var/spool/mail/" + os.path.split(os.path.expanduser("~"))[1])

                return {"layout": vbox, "callback": cls.__submitLoginWindow,
                    "widgets": [path]}

            @staticmethod
            def __submitLoginWindow(widgets):
                return {'path': widgets[0].get_text(), \
                        'username': os.path.split(widgets[0].get_text())[1]}

    try:
        global poplib
        import poplib
    except:
        pass
    else:

        class POP:

            title = "POP"

            def __init__(self, data):
                self.data = data
                check_login_data(self.data)

            def update(self):
                # POP is not designed for being logged in continously.
                # We log in, fetch mails and quit on every update.

                # Log in
                try:
                    if 'usessl' in self.data and self.data["usessl"]:
                        self.server = poplib.POP3_SSL(self.data["url"])
                    else:
                        self.server = poplib.POP3(self.data["url"])
                except socket.gaierror, message:
                    raise RuntimeError(_("Could not log in: ") + str(message))
                except socket.error, message:
                    raise RuntimeError(_("Could not log in: ") + str(message))

                else:
                    self.server.user(self.data["username"])
                    try:
                        self.server.pass_(self.data['password'])
                    except poplib.error_proto:
                        raise RuntimeError(_("Could not log in: Username or password incorrect"))

                # Fetch mails
                try:
                    messagesInfo = self.server.list()[1][-20:]
                except poplib.error_proto, err:
                    raise RuntimeError("POP protocol error: %s" % err)

                emails = []
                for msg in messagesInfo:
                    msgNum = int(msg.split(" ")[0])
                    msgSize = int(msg.split(" ")[1])
                    if msgSize < 10000:
                        try:
                            message = self.server.retr(msgNum)[1]
                        except poplib.error_proto, err:
                            # Probably not so serious errors
                            print("Mail Applet: POP protocol error: %s" % err)
                            continue
                        message = "\n".join(message)
                        emails.append(message)

                #t = []
                self.subjects = []
                for i in emails:
                    msg = email.message_from_string(i)

                    #t.append(MailItem(i.title, i.author))
                    # TODO: Actually do something with t
                    # TODO: Implement body previews

                    if "subject" in msg:
                        subject = msg["subject"]
                    else:
                        subject = _("[No Subject]")

                    self.subjects.append(subject)

                # Quit
                try:
                    self.server.quit()
                except poplib.error_proto, err:
                    # Probably not so serious errors
                    print("Mail Applet: POP protocol error: %s" % err)

            @classmethod
            def drawLoginWindow(cls, *groups):
                vbox = gtk.VBox(spacing=12)

                usrE, box = get_label_entry(_("Username:"), *groups)
                vbox.add(box)

                pwdE, box = get_label_entry(_("Password:"), *groups)
                pwdE.set_visibility(False)
                vbox.add(box)

                srvE, box = get_label_entry(_("Server:"), *groups)
                vbox.add(box)

                sslE = gtk.CheckButton(label=_("Use SSL encryption"))
                vbox.add(sslE)

                return {"layout": vbox, "callback": cls.__submitLoginWindow,
                    "widgets": [usrE, pwdE, srvE, sslE],
                    "fill-in": cls.__fillinLoginWindow}

            @staticmethod
            def __submitLoginWindow(widgets):
                return {'username': widgets[0].get_text(), \
                        'password': widgets[1].get_text(), \
                        'url': widgets[2].get_text(), \
                        "usessl": widgets[3].get_active()}

            @staticmethod
            def __fillinLoginWindow(widgets, data):
                widgets[0].set_text(data['username'])
                widgets[1].set_text(data['password'])
                widgets[2].set_text(data['url'])
                widgets[3].set_active(data['usessl'])

    try:
        global imaplib
        import imaplib
    except:
        pass
    else:

        class IMAP:

            title = "IMAP"

            def __init__(self, data):
                self.data = data
                check_login_data(self.data)
                args = self.data["url"].split(":")

                if self.data["usessl"]:
                    self.server = imaplib.IMAP4_SSL(*args)
                else:
                    self.server = imaplib.IMAP4(*args)

                try:
                    self.server.login(self.data["username"], self.data['password'])
                except poplib.error_proto:
                    raise RuntimeError(_("Could not log in"))

                mboxs = [i.split(")")[1].split(" ", 2)[2].strip('"') for i in self.server.list()[1]]
                self.box = self.data["folder"]

                if self.box not in mboxs and self.box != "":
                    raise RuntimeError(_("Folder does not exst"))

                if self.box != "":
                    self.server.select(self.box)

            def update(self):
                self.subjects = []

                if self.box != "":
                    emails = [i for i in self.server.search(None, "(UNSEEN)")[1][0].split(" ") if i != ""]

                    for i in emails:
                        s = self.server.fetch(i, '(BODY[HEADER.FIELDS (SUBJECT)])')[1][0]

                        if s is not None:
                            self.subjects.append(s[1][9:].replace("\r\n", "\n").replace("\n", ""))  # Don't ask
                else:
                    mboxs = [re.search("(\W*) (\W*) (.*)", i).groups()[2] for i in self.server.list()[1]]
                    mboxs = [i for i in mboxs if i not in ("Sent", "Trash") and i[:6] != "[Gmail]"]

                    emails = []
                    for b in mboxs:
                        r, d = self.server.select(b)

                        if r == "NO":
                            continue

                        p = self.server.search("UTF8", "(UNSEEN)")[1][0].split(" ")

                        emails.extend([i for i in p if i != ""])

                        for i in emails:
                            s = self.server.fetch(i, '(BODY[HEADER.FIELDS (SUBJECT)])')[1][0]

                            if s is not None:
                                self.subjects.append(s[1][9:].replace("\r\n", "\n").replace("\n", ""))  # Don't ask

            @classmethod
            def drawLoginWindow(cls, *groups):
                vbox = gtk.VBox(spacing=12)

                usrE, box = get_label_entry(_("Username:"), *groups)
                vbox.add(box)

                pwdE, box = get_label_entry(_("Password:"), *groups)
                pwdE.set_visibility(False)
                vbox.add(box)

                srvE, box = get_label_entry(_("Server:"), *groups)
                vbox.add(box)

                sslE = gtk.CheckButton(label=_("Use SSL encryption"))
                vbox.add(sslE)

                allE = gtk.CheckButton(label=_("Get messages from only one folder"))
                allE.set_active(True)
                vbox.add(allE)

                foldE, boxE = get_label_entry(_("Folder:"), *groups)
                foldE.set_text("INBOX")
                alignmentE = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
                alignmentE.props.left_padding = 12
                alignmentE.add(boxE)
                vbox.add(alignmentE)

                def on_toggle(widget, box):
                    box.set_sensitive(widget.get_active())

                allE.connect("toggled", on_toggle, boxE)
                return {"layout": vbox, "callback": cls.__submitLoginWindow,
                    "widgets": [usrE, pwdE, srvE, sslE, allE, foldE],
                    "fill-in": cls.__fillinLoginWindow}

            @staticmethod
            def __submitLoginWindow(widgets):
                if widgets[4].get_active():
                    folder = widgets[5].get_text()

                    if folder == "":
                        folder = "INBOX"
                else:
                    folder = ""
                return {'username': widgets[0].get_text(), \
                        'password': widgets[1].get_text(), \
                        'url': widgets[2].get_text(), \
                        'usessl': widgets[3].get_active(), \
                        'folder': folder}

            @staticmethod
            def __fillinLoginWindow(widgets, data):
                widgets[0].set_text(data['username'])
                widgets[1].set_text(data['password'])
                widgets[2].set_text(data['url'])
                widgets[3].set_active(data['usessl'])
                if data['folder'] != "":
                    widgets[4].set_active(False)
                else:
                    widgets[4].set_active(True)
                widgets[5].set_text(data['folder'])



if __name__ == "__main__":
    awnlib.init_start(MailApplet, {
        "name": _("Mail Applet"),
        "short": "mail",
        "version": __version__,
        "description": _("An applet to check one's email"),
        "logo": os.path.join(icon_dir, "mail-read.svg"),
        "author": "Pavel Panchekha",
        "copyright-year": "2008",
        "email": "pavpanchekha@gmail.com",
        "authors": ["onox <denkpadje@gmail.com>",
                    "sharkbaitbobby <sharkbaitbobby+awn@gmail.com>",
                    "Pavel Panchekha"]})
