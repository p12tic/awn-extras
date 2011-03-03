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


def check_login_data(backend, data):
    '''Sanity check for login data. Data from login dialog should always
    pass this test, this is mainly for wrong or manipulated keys.'''

    for field in backend.fields:
        if field not in data:
            raise LoginError("Wrong or corrupt key")
        if data[field] is None:
            raise LoginError("Key with field is None")
        if type(data[field]) == str and len(data[field]) == 0:
            raise LoginError("Key with empty field")

    # Optional fields must be in data but may be empty.
    if hasattr(backend, "optional"):
        for field in backend.optional:
            if field not in data:
                raise LoginError("Wrong or corrupt key")
            if data[field] is None:
                raise LoginError("Key with field is None")


def decode_header(message):
    ''' Decodes internationalized headers like these:
    =?UTF-8?B?dMOkc3Q=?= '''

    if message is None or len(message) == 0:
        return _("[No Subject]")

    decoded_message = ""
    for split in message.split(" "):
        text, charset = email.Header.decode_header(split)[0]
        if charset:
            split = text.decode(charset)
        else:
            split += " "
        decoded_message += split

    if decoded_message.endswith(" "):
        return decoded_message[:-1]
    return decoded_message


class LoginError(Exception):
    pass


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
            self.login(login_data)
        else:
            self.__dialog.login_form()
            #self.awn.dialog.toggle("main", "show")

    def init_keyring(self):
        try:
            self.keyring = awnlib.Keyring()
        except awnlib.KeyringError:
            self.keyring = None

    def get_key(self):
        '''Get key for backend from Gnome Keyring'''

        def set_login_settings_to_default():
            # Default setting means we have no key at all
            self.awn.settings["login-keyring-token"] = ["Backend", "Keyring", "Token"]

        if self.keyring is None:
            return None
        if self.back.__name__ == "UnixSpool":
            return None

        # Migration code from old "login-token" to new "login-keyring-token"
        # To be deleted in the version following version 0.6
        try:
            old_token = self.awn.settings["login-token"]
        except ValueError:
            # New installation, token does not exist
            old_token = 0
        if old_token != 0:
            import gnomekeyring
            self.awn.settings["login-keyring-token"] = \
                [self.back.__name__,
                 gnomekeyring.get_default_keyring_sync(),
                 str(old_token)]
            self.awn.settings["login-token"] = 0

        keydata = self.awn.settings["login-keyring-token"]
        if len(keydata) == 0 or len(keydata) > 3:
            set_login_settings_to_default()
            return None
        if keydata[0] != self.back.__name__:
            return None

        try:
            key = self.keyring.from_token(keydata[1], long(keydata[2]))
            return key
        except awnlib.KeyringNoMatchError:
            set_login_settings_to_default()
            return None

    def get_data_from_key(self, key):
        # Unix Spool has no password, get data from config
        if self.back.__name__ == "UnixSpool":
            path = self.awn.settings["unix-spool"]
            if path == "default":
                path = os.path.join("/var/spool/mail/",
                    os.path.split(os.path.expanduser("~"))[1])
            data = {}
            data['path'] = path
            data['username'] = os.path.split(path)[1]
            return data

        if self.keyring is None or key is None:
            return None

        try:
            data = key.attrs
            data['password'] = key.password
        except awnlib.KeyringError:
            # Reads data from keyring, probably only KeyringCancelledError,
            # but return None on any failure
            return None

        return data

    def save_key(self, data):
        '''Save login data for backend in Gnome Keyring'''

        if self.keyring is None or data is None:
            return

        # Spool has no password, just save path in config
        if self.back.__name__ == "UnixSpool":
            self.awn.settings["unix-spool"] = data["path"]
            return

        password = data['password']
        attrs = data.copy()
        del attrs['password']
        desc = "Awn Extras/Mail/" + self.back.__name__ + "/" + attrs['username']

        key = self.get_key()
        if key is None:
            try:
                key = self.keyring.new(
                          keyring=None,
                          name=desc,
                          pwd=password,
                          attrs=attrs,
                          type='generic')
                self.awn.settings["login-keyring-token"] = [self.back.__name__,
                                                            key.keyring,
                                                            str(key.token)]
            except awnlib.KeyringCancelledError:
                # User cancelled himself
                pass
        else:
            try:
                key.password = password
                key.attrs = attrs
                key.name = desc
            except awnlib.KeyringCancelledError:
                pass

    def logout(self):
        if hasattr(self, "timer"):
            self.timer.stop()
        self.awn.theme.icon("login")
        self.awn.tooltip.set(_("Mail Applet (Click to Log In)"))

    def login(self, data):
        # Initialize backend, check login data
        # IMAP backend already connects to server
        try:
            self.mail = self.back(data)
        except LoginError, error:
            self.__dialog.login_form(True, str(error))
            return

        # Connect to server
        try:
            self.mail.update()
        except LoginError, error:
            self.__dialog.login_form(True, str(error))
            return

        # Login successful
        self.__dialog.update_email_list()
        self.awn.notification.send(_("Mail Applet"),
                                   _("Logging in as %s") % data["username"],
                                   self.__getIconPath("login"))
        self.save_key(data)
        self.timer = self.awn.timing.register(self.refresh,
                                             self.awn.settings["timeout"] * 60)

    def refresh(self):
        oldSubjects = self.mail.subjects

        # Login
        try:
            self.mail.update()
        except LoginError, e:
            self.awn.theme.icon("error")
            if self.awn.settings["show-network-errors"]:
                self.awn.notification.send(_("Network error - Mail Applet"), str(e), "")
            return

        self.__dialog.update_email_list()

        # Notify on new subjects
        diffSubjects = [i for i in self.mail.subjects if i not in oldSubjects]
        if len(diffSubjects) > 0:
            msg = strMailMessages(len(diffSubjects)) + ":\n" + \
                                                        "\n".join(diffSubjects)
            self.awn.notification.send(_("New Mail - Mail Applet"), msg,
                                 self.__getIconPath("mail-unread"))

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
        binder.bind("show-network-errors", "checkbutton-alert-errors")
        binder.bind("timeout", "spinbutton-timeout", key_callback=change_timeout)
        self.awn.settings.load_bindings(binder)


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
        self.__parent.awn.tooltip.set(strMessages(len(mail.subjects)))
        self.__parent.awn.theme.icon("unread" if len(mail.subjects) > 0 else "read")
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
        errorbox = None
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
            errorbox = gtk.HBox(False)
            errorbox.pack_start(hbox, True, False)

            vbox.add(errorbox)

        # Allow user to change the backend in the login dialog
        def changed_backend_cb(combobox, label_group):
            backend = combobox.get_active()

            if backend != -1:
                backends = [i for i in dir(Backends) if i[:2] != "__"]
                self.__parent.awn.settings["backend"] = backends[backend]
                self.__parent.back = getattr(Backends(), backends[backend])
                self.callback = self.__login_get_widgets(vbox, label_group)

                # Remove previous error message, fill in data if available
                if errorbox:
                    errorbox.hide()
                fill_in()

                # Make submit button insensitive if required data is missing
                connect_entries()
                onchanged(None)

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

        def fill_in():
            login_data = self.__parent.get_data_from_key(self.__parent.get_key())
            if login_data:
                try:
                    check_login_data(self.__parent.back, login_data)
                    self.callback['fill-in'](self.callback['widgets'], login_data)
                except LoginError:
                    # Corrupt key, user won't know what to do, just skip it
                    pass

        fill_in()

        image_login = gtk.image_new_from_stock(gtk.STOCK_NETWORK,
                                               gtk.ICON_SIZE_BUTTON)
        submit_button = gtk.Button(label=_("Log In"), use_underline=False)
        submit_button.set_image(image_login)

        def onsubmit(widget):
            self.__parent.login(
                                self.callback["callback"](self.callback["widgets"]))
        submit_button.connect("clicked", onsubmit)

        # Make submit button insensitive if required data is missing
        def onchanged(entry):
            state = True
            for e in self.entries:
                if e.get_text() == "":
                    state = False
            submit_button.set_sensitive(state)

        def connect_entries():
            self.entries = []
            for w in self.callback['widgets']:
                if isinstance(w, gtk.Entry):
                    w.connect("activate", onsubmit)
                    if not hasattr(w, "optional"):
                        self.entries.append(w)
                        w.connect("changed", onchanged)

        connect_entries()
        onchanged(None)

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
        fields = ['username', 'password']

        def __init__(self, data):
            self.data = data
            check_login_data(self, self.data)

        def url(self):
            return "https://mail.google.com/mail/"

        def update(self):
            f = feedparser.parse(\
                "https://%s:%s@mail.google.com/gmail/feed/atom" \
                            % (self.data["username"], self.data['password']))

            if "bozo_exception" in f.keys():
                raise LoginError(_("There seem to be problems with our \
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
        fields = ['username', 'domain', 'password']

        def __init__(self, data):
            self.data = data
            check_login_data(self, self.data)

        def url(self):
            return "https://mail.google.com/a/%s" % self.data["domain"]

        def update(self):
            f = feedparser.parse(\
                "https://%s%%40%s:%s@mail.google.com/a/%s/feed/atom" \
                 % (self.data["username"], self.data["domain"], \
                    self.data['password'], self.data["domain"]))

            if "bozo_exception" in f.keys():
                raise LoginError(_("There seem to be problems with our \
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
            fields = ['username', 'path']

            def __init__(self, data):
                self.path = data['path']

            def update(self):
                try:
                    self.box = mailbox.mbox(self.path)
                except IOError, e:
                    raise LoginError(e)
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

                return {"layout": vbox, "callback": cls.__submitLoginWindow,
                    "fill-in": cls.__fillinLoginWindow,
                    "widgets": [path]}

            @staticmethod
            def __submitLoginWindow(widgets):
                return {'path': widgets[0].get_text(), \
                        'username': os.path.split(widgets[0].get_text())[1]}

            @staticmethod
            def __fillinLoginWindow(widgets, data):
                widgets[0].set_text(data['path'])

    try:
        global poplib
        import poplib
    except:
        pass
    else:

        class POP:

            title = "POP"
            fields = ['username', 'url', 'usessl', 'password']

            def __init__(self, data):
                self.data = data
                check_login_data(self, self.data)

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
                    raise LoginError(_("Could not log in: ") + str(message))
                except socket.error, message:
                    raise LoginError(_("Could not log in: ") + str(message))

                else:
                    self.server.user(self.data["username"])
                    try:
                        self.server.pass_(self.data['password'])
                    except poplib.error_proto:
                        raise LoginError(_("Could not log in: Username or password incorrect"))

                # Fetch mails
                try:
                    messagesInfo = self.server.list()[1][-20:]
                except poplib.error_proto, message:
                    raise LoginError(_("Could not log in: ") + str(message))

                emails = []
                for msg in messagesInfo:
                    msgNum = int(msg.split(" ")[0])
                    try:
                        message = self.server.top(msgNum, 0)[1]
                    except poplib.error_proto, err:
                        print("Mail Applet: POP protocol error: %s" % err)
                        continue
                    message = "\n".join(message)
                    emails.append(message)

                self.subjects = []
                for i in emails:
                    msg = email.message_from_string(i)
                    if "subject" in msg:
                        subject = decode_header(msg["subject"])
                    else:
                        subject = _("[No Subject]")
                    self.subjects.append(subject)

                # Quit
                try:
                    self.server.quit()
                except poplib.error_proto, err:
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
            fields = ['username', 'url', 'usessl', 'password']
            optional = ['folder']

            def __init__(self, data):
                self.data = data
                check_login_data(self, self.data)

            def update(self):
                # Login on each update
                # otherwise it won't work after suspend
                args = self.data["url"].split(":")

                try:
                    if self.data["usessl"]:
                        self.server = imaplib.IMAP4_SSL(*args)
                    else:
                        self.server = imaplib.IMAP4(*args)
                except imaplib.socket.error:
                    raise LoginError(_("Server did not respond"))

                try:
                    self.server.login(self.data["username"], self.data['password'])
                except imaplib.IMAP4.error:
                    raise LoginError(_("Could not log in"))

                # Select mailbox(es) and get subjects
                mboxs = [i.split(")")[1].split(" ", 2)[2].strip('"') for i in self.server.list()[1]]
                self.box = self.data["folder"]

                if self.box not in mboxs and self.box != "":
                    raise LoginError(_("Folder does not exst"))

                if self.box != "":
                    # select mailbox with "read only" flag
                    self.server.select(self.box, True)
                self.subjects = []

                def get_subject(emails):
                    for i in emails:
                        s = self.server.fetch(i, '(BODY[HEADER.FIELDS (SUBJECT)])')[1][0]
                        if s is not None:
                            subject = s[1][9:].replace("\r\n", "\n").replace("\n", "")  # Don't ask
                            self.subjects.append(decode_header(subject))
                    self.server.close()  # Close current mailbox

                if self.box != "":
                    emails = [i for i in self.server.search(None, "(UNSEEN)")[1][0].split(" ") if i != ""]
                    get_subject(emails)

                else:
                    mboxs = [re.search("(\W*) (\W*) (.*)", i).groups()[2] for i in self.server.list()[1]]
                    mboxs = [i for i in mboxs if i not in ("Sent", "Trash") and i[1:8] != "[Gmail]"]

                    for b in mboxs:
                        # select mailbox with "read only" flag
                        r, d = self.server.select(b, True)

                        if r == "NO":
                            continue

                        p = self.server.search("UTF8", "(UNSEEN)")[1][0].split(" ")

                        emails = []
                        emails.extend(i for i in p if i != "")
                        get_subject(emails)

                # Finally quit
                self.server.logout()

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
                foldE.optional = True
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
                if data['folder'] == "":
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
        "authors": ["Gabor Karsay <gabor.karsay@gmx.at>",
                    "onox <denkpadje@gmail.com>",
                    "sharkbaitbobby <sharkbaitbobby+awn@gmail.com>",
                    "Pavel Panchekha"]})
