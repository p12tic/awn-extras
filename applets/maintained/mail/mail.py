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

import pygtk
pygtk.require("2.0")
import gtk

from awn import extras
from awn.extras import _, awnlib

icon_dir = os.path.join(os.path.dirname(__file__), "icons")
theme_dir = os.path.join(os.path.dirname(__file__), "themes")
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

        self.back = getattr(Backends(), self.settings["backend"])

        self.setup_themes()

        self.awn.theme.icon("login")
        self.awn.tooltip.set(_("Mail Applet (Click to Log In)"))

        self.__dialog = MainDialog(self)

        self.login()

    def login(self, force=False):
        """
        Login. Try to login from saved key, if this does not exist or
        force is True, show login dialog
        
        """
        self.awn.theme.icon("login")

        # If we're forcing initiation, just draw the dialog.
        # We wouldn't be forcing if we want to use the saved login token.
        if force:
            self.__dialog.login_form()
            self.awn.dialog.toggle("main", "show")
            return

        try:
            token = self.awn.settings["login-token"]
        except:  # You know what? too bad. No get_null, no exception handling
            token = 0

        # Force login if the token is 0, which we take to mean that there is no
        # login information. We'd delete the key, but that's not always
        # supported.
        if token == 0:
            return self.login(True)

        key = self.awn.keyring.from_token(token)

        self.perform_login(key)

    def logout(self):
        if hasattr(self, "timer"):
            self.timer.stop()
        self.awn.theme.icon("login")
        self.awn.settings["login-token"] = 0

    def perform_login(self, key):
        self.mail = self.back(key)  # Login

        try:
            self.mail.update()  # Update
        except RuntimeError:
            self.__dialog.login_form(True)

        else:
            self.awn.dialog.toggle("main", "hide")

            self.awn.notify.send(_("Mail Applet"),
                _("Logging in as %s") % key.attrs["username"],
                self.__getIconPath("login"))

            # Login successful
            self.awn.theme.icon("read")

            self.awn.settings["login-token"] = key.token

            self.timer = self.awn.timing.register(self.refresh,
                                                 self.settings["timeout"] * 60)
            self.refresh(show=False)

    def refresh(self, show=True):
        oldSubjects = self.mail.subjects

        try:
            self.mail.update()
        except RuntimeError, e:
            self.awn.theme.icon("error")

            if self.settings["show-network-errors"]:
                self.awn.errors.general(e)
            return

        diffSubjects = [i for i in self.mail.subjects if i not in oldSubjects]

        if len(diffSubjects) > 0:
            msg = strMailMessages(len(diffSubjects)) + ":\n" + \
                                                        "\n".join(diffSubjects)

            self.awn.notify.send(_("New Mail - Mail Applet"), msg,
                                 self.__getIconPath("unread"))

        self.awn.tooltip.set(strMessages(len(self.mail.subjects)))

        self.awn.theme.icon("unread" if len(self.mail.subjects) > 0 else "read")

        if self.settings["hide"] and len(self.mail.subjects) == 0:
            self.awn.icon.hide()
            self.awn.dialog.hide()
        elif show:
            self.awn.show()

        self.__dialog.update_email_list()

    def __getIconPath(self, name):
        path = os.path.join(theme_dir, self.settings["theme"], "scalable",
                            name + ".svg")
        if os.path.isfile(path):
            return path
        else:
            return os.path.join(icon_dir, name + ".svg")

    def __showWeb(self):
        if hasattr(self.mail, "showWeb"):
            self.mail.showWeb()
        elif hasattr(self.mail, "url"):
            subprocess.Popen(["xdg-open", self.mail.url()])

    def __showDesk(self):
        if hasattr(self.mail, "showDesk"):
            self.mail.showDesk()
        else:
            # Now if xdg-open had an option to just open the email client,
            # not start composing a message, that would be just wonderful.
            if " " in self.settings["email-client"]:
                subprocess.Popen(self.settings["email-client"], shell=True)
            else:
                subprocess.Popen(self.settings["email-client"])

    def setup_themes(self):
        """Loads themes and states"""
        states = {}
        for state in ["error", "login", "read", "unread"]:
            states[state] = state
        self.awn.theme.set_states(states)
        self.awn.theme.theme(self.settings["theme"])

    def setup_context_menu(self):
        prefs = gtk.Builder()
        prefs.add_from_file(ui_file)

        preferences_vbox = self.awn.dialog.new("preferences").vbox
        prefs.get_object("dialog-vbox").reparent(preferences_vbox)

        self.setup_preferences(prefs)

    def setup_preferences(self, prefs):
        def change_timeout(timeout):
            if hasattr(self, "timer"):
                self.timer.change_interval(timeout * 60)

        default_values = {
            "backend": "GMail",
            "theme": ("Tango", self.awn.theme.theme),
            "email-client": "evolution -c mail",
            "hide": (False, self.refresh_hide_applet,
                     prefs.get_object("checkbutton-hide-applet")),
            "show-network-errors": (True, None,
                                 prefs.get_object("checkbutton-alert-errors")),
            "timeout": (2, change_timeout,
                        prefs.get_object("spinbutton-timeout"))
        }
        self.settings = self.awn.settings.load_preferences(default_values)

        entry_client = prefs.get_object("entry-client")
        entry_client.set_text(self.settings["email-client"])
        entry_client.connect("changed", self.changed_client_cb)


        # Get a list of themes
        def is_dir(path):
            return os.path.isdir(os.path.join(theme_dir, path))
        themes = filter(is_dir, os.listdir(theme_dir))
        themes.append("Tango")
        themes.sort()

        combobox_theme = prefs.get_object("combobox-theme")
        awnlib.add_cell_renderer_text(combobox_theme)
        for theme in themes:
            combobox_theme.append_text(theme.replace('_', ' '))
        combobox_theme.set_active(themes.index(self.settings["theme"]))
        combobox_theme.connect("changed", self.changed_theme_cb)

    def changed_theme_cb(self, combobox):
        self.awn.settings["theme"] = \
                                   combobox.get_active_text().replace(' ', '_')

    def refresh_hide_applet(self, value):
        if hasattr(self, "mail") and self.settings["hide"] and \
                                                  len(self.mail.subjects) == 0:
            self.awn.icon.hide()
            self.awn.dialog.hide()
        else:
            self.awn.show()

    def changed_client_cb(self, entry):
        self.awn.settings["email-client"] = entry.get_text()


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

        self.__dialog.set_title(strMessages(len(self.__parent.mail.subjects)))

        vbox = gtk.VBox()
        self.__dialog.add(vbox)

        # Create table of new e-mails
        self.__email_list = gtk.Label()
        vbox.add(self.__email_list)

        # Fill the table
        self.update_email_list()

        # Buttons
        hbox_buttons = gtk.HBox()

        if hasattr(self.__parent.mail, "url") or \
                                        hasattr(self.__parent.mail, "showWeb"):
            # Don't show the button if it doesn't do anything

            # This'll be the "show web interface" button
            b = gtk.Button()
            b.set_relief(gtk.RELIEF_NONE) # Found it; that's a relief
            b.set_image(gtk.image_new_from_stock(gtk.STOCK_NETWORK,
                                                 gtk.ICON_SIZE_BUTTON))
            b.set_tooltip_text(_("Open Web Mail"))
            b.connect("clicked", lambda x: self.__parent.__showWeb())
            hbox_buttons.add(b)

        # This is the "show desktop client" button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT,
                                             gtk.ICON_SIZE_BUTTON))
        b.set_tooltip_text(_("Open Desktop Client"))
        b.connect("clicked", lambda x: self.__parent.__showDesk())
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
            self.__email_list = gtk.Table(len(self.__parent.mail.subjects), 2)
            self.__email_list.set_col_spacings(10)
            for i in xrange(len(mail.subjects)):
                label = gtk.Label("<b>" + str(i + 1) + "</b>")
                label.set_use_markup(True)
                self.__email_list.attach(label, 0, 1, i, i + 1)

                label = gtk.Label(mail.subjects[i])
                label.set_use_markup(True)
                self.__email_list.attach(label, 1, 2, i, i + 1)
#                print "%d: %s" % (i+1, self.mail.subjects[i])
        else:
            self.__email_list = gtk.Label("<i>%s</i>" % _("No new messages"))
            self.__email_list.set_use_markup(True)

        self.__email_list.show_all()
        parent.pack_start(self.__email_list)

    def __login_get_widgets(self, vbox, *groups):
        for widget in self.login_widgets:
            widget.destroy()

        if hasattr(self.__parent.back, "drawLoginWindow"):
            t = self.__parent.back.drawLoginWindow(*groups)
            self.login_widgets.append(t["layout"])
            vbox.add(t["layout"])
        else:
            usrE, box = get_label_entry(_("Username:"), *groups)
            vbox.add(box)
            self.login_widgets.append(box)

            pwdE, box = get_label_entry(_("Password:"), *groups)
            pwdE.set_visibility(False)
            vbox.add(box)
            self.login_widgets.append(box)

            t = {}

            t["callback"] = \
                lambda widgets, awn: awn.keyring.new(
                    "Mail Applet - %s(%s)" % (widgets[0].get_text(),
                                        self.__parent.awn.settings["backend"]),
                    widgets[1].get_text(),
                    {"username": widgets[0].get_text()}, "network")

            t["widgets"] = [usrE, pwdE]

        vbox.show_all()

        return t

    def login_form(self, error=False):
        """
        Creates a dialog the login form
        
        """
        self.__remove_current()
        self.__current_type = "login_form"

        self.__dialog.set_title(_("Log In"))

        vbox = gtk.VBox(spacing=12)
        vbox.set_border_width(6)
        self.__dialog.add(vbox)

        # Make all the labels the same size
        label_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)

        # Display an error message if there is an error
        if error:
            image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR,
                                             gtk.ICON_SIZE_MENU)
            label = gtk.Label("<b>" + _("Wrong username or password") + "</b>")
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
                self.__login_get_widgets(vbox, label_group)

        label_backend = gtk.Label(_("Type:"))
        label_backend.set_alignment(0.0, 0.5)
        label_group.add_widget(label_backend)

        combobox_backend = gtk.combo_box_new_text()
        combobox_backend.set_title(_("Backend"))
        backends = [i for i in dir(Backends) if i[:2] != "__"]
        for i in backends:
            combobox_backend.append_text(getattr(Backends(), i).title)
        combobox_backend.set_active(
                             backends.index(self.__parent.settings["backend"]))
        combobox_backend.connect("changed", changed_backend_cb, label_group)

        hbox_backend = gtk.HBox(False, 12)
        hbox_backend.pack_start(label_backend, expand=False)
        hbox_backend.pack_start(combobox_backend)

        vbox.add(hbox_backend)

        self.login_widgets = []
        t = self.__login_get_widgets(vbox, label_group)

        image_login = gtk.image_new_from_stock(gtk.STOCK_NETWORK,
                                               gtk.ICON_SIZE_BUTTON)
        submit_button = gtk.Button(label=_("Log In"), use_underline=False)
        submit_button.set_image(image_login)
        def onsubmit(widget):
            self.__parent.perform_login(
                                t["callback"](t["widgets"], self.__parent.awn))
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

        def __init__(self, key):
            self.key = key

        def url(self):
            return "http://mail.google.com/mail/"

        def update(self):
            f = feedparser.parse(\
                "https://%s:%s@mail.google.com/gmail/feed/atom" \
                 % (self.key.attrs["username"], self.key.password))

            if "bozo_exception" in f.keys():
                raise RuntimeError(_("There seem to be problems with our \
                    connection to your account. Your best bet is probably \
                    to log out and try again."))
            # Hehe, Google is funny. Bozo exception

            t = []
            self.subjects = []
            for i in f.entries:
                i.title = self.__cleanGmailSubject(i.title)
                t.append(MailItem(i.title, i.author))
                self.subjects.append(i.title)

        def __cleanGmailSubject(self, n):
            n = re.sub(r"^[^>]*\\>", "", n) # "sadf\>fdas" -> "fdas"
            n = re.sub(r"\\[^>]*\\>$", "", n) # "asdf\afdsasdf\>" -> "asdf"
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
            n = re.sub("\<[^\<\>]*?\>", "", n) # "<h>asdf<a></h>" -> "asdf"

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

    class GApps:

        title = _("Google Apps")

        def __init__(self, key):
            self.key = key

        def url(self):
            return "http://mail.google.com/a/%s" % self.key.attrs["username"]

        def update(self):
            f = feedparser.parse(\
                "https://%s%%40%s:%s@mail.google.com/a/%s/feed/atom" \
                 % (self.key.attrs["username"], self.key.attrs["domain"], \
                 self.key.password, self.key.attrs["domain"]))

            if "bozo_exception" in f.keys():
                raise RuntimeError(_("There seem to be problems with our \
                    connection to your account. Your best bet is probably \
                    to log out and try again."))
            # Hehe, Google is funny. Bozo exception

            t = []
            self.subjects = []
            for i in f.entries:
                i.title = self.__cleanGmailSubject(i.title)
                t.append(MailItem(i.title, i.author))
                self.subjects.append(i.title)

        def __cleanGmailSubject(self, n):
            n = re.sub(r"^[^>]*\\>", "", n) # "sadf\>fdas" -> "fdas"
            n = re.sub(r"\\[^>]*\\>$", "", n) # "asdf\afdsasdf\>" -> "asdf"
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
            n = re.sub("\<[^\<\>]*?\>", "", n) # "<h>asdf<a></h>" -> "asdf"

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
                "widgets": [usrE, pwdE, domE]}

        @staticmethod
        def __submitLoginWindow(widgets, awn):
            return awn.keyring.new("Mail Applet - %s(%s)" \
                % (widgets[0].get_text(), "GApps"), \
                widgets[1].get_text(), \
                {"username": widgets[0].get_text(),
                "domain": widgets[2].get_text()}, "network")

    try:
        global mailbox
        import mailbox
    except:
        pass
    else:
        class UnixSpool:

            title = _("Unix Spool")

            def __init__(self, key):
                self.path = key.attrs["path"]

            def update(self):
                self.box = mailbox.mbox(self.path)
                email = []

                self.subjects = []
                for i, msg in self.box.items():
                    if "subject" in msg:
                        subject = msg["subject"]
                    else:
                        subject = "[No Subject]"

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
            def __submitLoginWindow(widgets, awn):
                return awn.keyring.new("Mail Applet - %s" \
                    % "UnixSpool", "-", \
                    {"path": widgets[0].get_text(),
                     "username": os.path.split(widgets[0].get_text())[1]},
                     "network")

    try:
        global poplib
        import poplib
    except:
        pass
    else:
        class POP:

            title = "POP"

            def __init__(self, key):
                if key.attrs["usessl"]:
                    self.server = poplib.POP3_SSL(key.attrs["url"])
                else:
                    self.server = poplib.POP3(key.attrs["url"])

                self.server.user(key.attrs["username"])
                try:
                    self.server.pass_(key.password)
                except poplib.error_proto:
                    raise RuntimeError(_("Could not log in"))

            def update(self):
                messagesInfo = self.server.list()[1][-20:]
                # Server messages? Too bad

                emails = []
                for msg in messagesInfo:
                    msgNum = int(msg.split(" ")[0])
                    msgSize = int(msg.split(" ")[1])
                    if msgSize < 10000:
                        message = self.server.retr(msgNum)[1]
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
                        subject = "[No Subject]"

                    self.subjects.append(subject)

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
                    "widgets": [usrE, pwdE, srvE, sslE]}

            @staticmethod
            def __submitLoginWindow(widgets, awn):
                return awn.keyring.new("Mail Applet - %s(%s)" \
                    % (widgets[0].get_text(), "POP"), \
                    widgets[1].get_text(), \
                    {"username": widgets[0].get_text(),
                    "url": widgets[2].get_text(),
                    "usessl": widgets[3].get_active()}, "network")

    try:
        global imaplib
        import imaplib
    except:
        pass
    else:
        class IMAP:

            title = "IMAP"

            def __init__(self, key):
                args = key.attrs["url"].split(":")

                if key.attrs["usessl"]:
                    self.server = imaplib.IMAP4_SSL(*args)
                else:
                    self.server = imaplib.IMAP(*args)

                try:
                    self.server.login(key.attrs["username"], key.password)
                except poplib.error_proto:
                    raise RuntimeError(_("Could not log in"))

                mboxs = [i.split(")")[1].split(" ", 2)[2].strip('"') for i in self.server.list()[1]]
                self.box = key.attrs["folder"]

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
                            self.subjects.append(s[1][9:].replace("\r\n", "\n").replace("\n", "")) # Don't ask
                else:
                    mboxs = [re.search("(\W*) (\W*) (.*)", i).groups()[2][1:-1] for i in self.server.list()[1]]
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
                                self.subjects.append(s[1][9:].replace("\r\n", "\n").replace("\n", "")) # Don't ask

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

                hbox_box = gtk.HBox(False, 12)
                vbox.add(hbox_box)

                foldE, boxE = get_label_entry(_("Password:"), *groups)
                foldE.set_text("INBOX")
                vbox.add(boxE)

                def on_toggle(w):
                    boxE.set_sensitive(allE.get_active())

                allE.connect("toggled", on_toggle)

                return {"layout": vbox, "callback": cls.__submitLoginWindow,
                    "widgets": [usrE, pwdE, srvE, sslE, allE, boxE]}

            @staticmethod
            def __submitLoginWindow(widgets, awn):
                if widgets[4].get_active():
                    folder = widgets[5].get_text()

                    if folder == "":
                        folder = "INBOX"
                else:
                    folder = ""

                return awn.keyring.new("Mail Applet - %s(%s)" \
                    % (widgets[0].get_text(), "IMAP"), \
                    widgets[1].get_text(), \
                    {"username": widgets[0].get_text(),
                    "url": widgets[2].get_text(),
                    "usessl": widgets[3].get_active(),
                    "folder": folder}, "network")

if __name__ == "__main__":
    awnlib.init_start(MailApplet, {
        "name": _("Mail Applet"),
        "short": "mail",
        "version": extras.__version__,
        "description": _("An applet to check one's email"),
        "logo": os.path.join(icon_dir, "read.svg"),
        "author": "Pavel Panchekha",
        "copyright-year": "2008",
        "email": "pavpanchekha@gmail.com",
        "type": ["Network", "Email"],
        "authors": ["onox <denkpadje@gmail.com>",
                    "sharkbaitbobby <sharkbaitbobby+awn@gmail.com>",
                    "Pavel Panchekha"]},
        ["settings-per-instance", "detach"])
