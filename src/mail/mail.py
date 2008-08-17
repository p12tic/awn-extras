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
import locale
import os
import re
import time
import subprocess

import pygtk
pygtk.require("2.0")
import gtk
from awn.extras import AWNLib

APP = "awn-mail-applet"
DIR=os.path.dirname(__file__) + '/locale'
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

applet_name = _("Mail Applet")
applet_version = "0.2.8"
applet_description = _("An applet to check one's email")

# Logo of the applet, shown in the GTK About dialog
applet_logo = os.path.join(os.path.dirname(__file__), "Themes/Tango/read.svg")

themes_dir = os.path.join(os.path.dirname(__file__), "Themes")


def strMailMessages(num):
    return gettext.ngettext("You have %d new message", "You have %d new messages", num) % num


def strMessages(num):
    return gettext.ngettext("%d unread message", "%d unread messages", num) % num


class MailApplet:
    def __init__(self, applet):
        self.awn = applet
        
        self.awn.keyring.require()
        
        default_values = {
            "backend": "GMail",
            "theme": "Tango",
            "email-client": "evolution -c mail",
            "hide": False,
            "show-network-errors": True
        }
        applet.settings.load(default_values)
        
        self.back = getattr(Backends(), self.awn.settings["backend"])
        self.theme = self.awn.settings["theme"]
        self.emailclient = self.awn.settings["email-client"]
        self.hide = self.awn.settings["hide"]
        self.showerror = self.awn.settings["show-network-errors"]
        
        self.__setIcon("login")
        self.awn.title.set(_("Mail Applet (Click to Log In)"))
        
        self.setup_context_menu()
        
        self.awn.errors.module(globals(), "feedparser")
        
        self.login()
    
    def login(self, force=False):
        self.__setIcon("login")
        if force:
            return self.setup_login_dialog()
        # If we're forcing initiation, just draw the dialog
        # We wouldn't be forcing if we want to use the saved login token

        try:
            token = self.awn.settings["login-token"]
        except: # You know what? too bad. No get_null, no exception handling
            token = 0

        if token == 0:
           return self.login(True)
        # Force login if the token is 0, which we take to mean that there
        # is no login information. We'd delete the key, but that's not
        # always supported.

        key = self.awn.keyring.fromToken(token)

        self.submitPWD(key)

    def logout(self):
        if hasattr(self, "timer"):
            self.timer.stop()
        self.__setIcon("login")
        self.awn.settings["login-token"] = 0
        self.login(True)

    def submitPWD(self, key):
        self.mail = self.back(key) # Login

        try:
            self.mail.update() # Update
        except RuntimeError:
            self.setup_login_dialog(True)

        else:
            self.awn.notify.send(_("Mail Applet"), \
                _("Logging in as %s") % key.attrs["username"], \
                self.__getIconPath("login", full=True))

            # Login successful
            self.__setIcon("read")

            self.awn.settings["login-token"] = key.token

            self.timer = self.awn.timing.register(self.refresh, 300)
            self.refresh()

    def refresh(self, x=None):
        oldSubjects = self.mail.subjects

        try:
            self.mail.update()
        except RuntimeError, (err):
            self.__setIcon("error")

            if self.showerror:
                self.awn.errors.general(err, lambda: ())
            return

        diffSubjects = [i for i in self.mail.subjects if i not in oldSubjects]
        
        if len(diffSubjects) > 0:
            msg = strMailMessages(len(diffSubjects)) + "\n" + "\n".join(diffSubjects)
            self.awn.notify.send(_("New Mail - Mail Applet"), msg, self.__getIconPath("unread", full=True))

        self.awn.title.set(strMessages(len(self.mail.subjects)))
        
        self.__setIcon(len(self.mail.subjects) > 0 and "unread" or "read")
        
        if self.hide and len(self.mail.subjects) == 0:
            self.awn.icon.hide()

        self.awn.dialog.hide()
        self.drawMainDlog()

    def __setIcon(self, name):
        self.awn.icon.file(self.__getIconPath(name))
    
    def __getIconPath(self, name, full=False):
        if full:
            return os.path.join(themes_dir, self.theme, name + ".svg")
        else:
            return os.path.join("Themes", self.theme, name + ".svg")

    def __showWeb(self):
        if hasattr(self.mail, "showWeb"):
            self.mail.showWeb()
        elif hasattr(self.mail, "url"):
            subprocess.Popen(["xdg-open", self.mail.url()])

    def __showDesk(self):
        if hasattr(self.mail, "showDesk"):
            self.mail.showDesk()
        else:
            subprocess.Popen(self.emailclient, shell=True)
            # Now if xdg-open had an option to just open the email client,
            # not start composing a message, that would be just wonderful.

    def drawMainDlog(self):
        dialog = self.awn.dialog.new("main", strMessages(len(self.mail.subjects)))

        vbox = gtk.VBox()
        dialog.add(vbox)

        if len(self.mail.subjects) > 0:
            tbl = gtk.Table(len(self.mail.subjects), 2)
            tbl.set_col_spacings(10)
            for i in xrange(len(self.mail.subjects)):
                
                label = gtk.Label("<b>"+str(i+1)+"</b>")
                label.set_use_markup(True)
                tbl.attach(label, 0, 1, i, i+1)
                
                label = gtk.Label(self.mail.subjects[i])
                label.set_use_markup(True)
                tbl.attach(label, 1, 2, i, i+1)
                #print "%d: %s" % (i+1, self.mail.subjects[i])
            vbox.add(tbl)
        else:
            label = gtk.Label("<i>" + _("Hmmm, nothing here") + "</i>")
            label.set_use_markup(True)
            vbox.add(label)

        buttons = []

        if hasattr(self.mail, "url") or hasattr(self.mail, "showWeb"):
            # Don't show the button if it doesn't do anything

            # This'll be the "show web interface" button
            b = gtk.Button()
            b.set_relief(gtk.RELIEF_NONE) # Found it; that's a relief
            b.set_image(gtk.image_new_from_stock(gtk.STOCK_NETWORK, gtk.ICON_SIZE_BUTTON))
            b.connect("clicked", lambda x: self.__showWeb())
            buttons.append(b)

        # This is the "show desktop client" button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT, gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", lambda x: self.__showDesk())
        buttons.append(b)

        # Refresh button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH, gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", lambda x: self.refresh())
        buttons.append(b)

        # Log out
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_STOP, gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", lambda x: self.logout())

        buttons.append(b)
        hbox_buttons = gtk.HBox()
        for i in buttons:
            hbox_buttons.add(i)
        vbox.add(hbox_buttons)

    def setup_login_dialog(self, error=False):
        dialog = self.awn.dialog.new("main", _("Log In"))
        vbox = gtk.VBox(spacing=12)
        vbox.set_border_width(6)
        dialog.add(vbox)
        
        if error:
            label = gtk.Label("<i>" + _("Wrong Username or Password") + "</i>")
            label.set_use_markup(True)
            vbox.add(label)

        if hasattr(self.back, "drawLoginWindow"):
            t = self.back.drawLoginWindow()
            vbox.add(t["layout"])
        else:
            hbox_username = gtk.HBox(spacing=13)
            vbox.add(hbox_username)
            
            hbox_username.add(gtk.Label(_("Username:") + "\t"))
            usrE = gtk.Entry()
            hbox_username.add(usrE)
            
            hbox_password = gtk.HBox(spacing=13)
            vbox.add(hbox_password)
            
            hbox_password.add(gtk.Label(_("Password:") + "\t"))
            pwdE = gtk.Entry()
            pwdE.set_visibility(False)
            hbox_password.add(pwdE)
            
            t = {}

            t["callback"] = \
                lambda widgets, awn: awn.keyring.new("Mail Applet - %s(%s)" \
                % (widgets[0].get_text(), self.awn.settings["backend"]), \
                widgets[1].get_text(), \
                {"username": widgets[0].get_text()}, "network")

            t["widgets"] = [usrE, pwdE]
        
        submit_button = gtk.Button(label=_("Log In"), use_underline=False)
        def onsubmit(x=None, y=None):
            self.awn.dialog.toggle("main", "hide")
            self.submitPWD(t["callback"](t["widgets"], self.awn))
        submit_button.connect("clicked", onsubmit)
        vbox.add(submit_button)

        self.awn.dialog.toggle("main", "show")
    
    def setup_context_menu(self):
        prefs_vbox = self.awn.dialog.new("preferences").vbox
        vbox = gtk.VBox(spacing=18)
        prefs_vbox.add(vbox)
        vbox.set_border_width(5)
        
        vbox_mail = AWNLib.create_frame(vbox, "Mail")
        
        hbox_backend = gtk.HBox(spacing=13)
        vbox_mail.add(hbox_backend)
        hbox_backend.pack_start(gtk.Label(_("Backend: ")), expand=False)
        
        backend = gtk.combo_box_new_text()
        backend.set_title(_("Backend"))
        backends = [i for i in dir(Backends) if i[:2] != "__"]
        for i in backends:
            backend.append_text(i)
        backend.set_active(backends.index(self.awn.settings["backend"]))
        backend.connect("changed", self.changed_backend_cb)
        hbox_backend.add(backend)
        
        hbox_client = gtk.HBox(spacing=13)
        vbox_mail.add(hbox_client)
        hbox_client.add(gtk.Label(_("Email Client: ")))
        
        email = gtk.Entry()
        email.set_text(self.emailclient)
        email.connect("changed", self.changed_client_cb)
        hbox_client.add(email)
        
        vbox_display = AWNLib.create_frame(vbox, "Display")
        
        hbox_theme = gtk.HBox(spacing=13)
        vbox_display.add(hbox_theme)
        hbox_theme.pack_start(gtk.Label(_("Theme: ")), expand=False)
        
        theme = gtk.combo_box_new_text()
        theme.set_title(_("Theme"))
        themes = [i for i in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "Themes"))]
        for i in themes:
            theme.append_text(i)
        theme.connect("changed", self.changed_theme_cb)
        theme.set_active(themes.index(self.theme))
        hbox_theme.add(theme)
        
        hidden = gtk.CheckButton(label=_("Hide Unless New"))
        hidden.set_active(self.hide)
        hidden.connect("toggled", self.toggled_hide_cb)
        vbox_display.add(hidden)

        show_errors = gtk.CheckButton(label=_("Alert on Network Errors"))
        show_errors.set_active(self.showerror)
        show_errors.connect("toggled", self.toggled_show_errors_cb)
        vbox_display.add(show_errors)
    
    def toggled_hide_cb(self, button):
        self.awn.settings["hide"] = self.hide = button.get_active()
        
        if hasattr(self, "mail"):
            self.refresh()
    
    def toggled_show_errors_cb(self, button):
        self.awn.settings["show-network-errors"] = self.showerror = button.get_active()
    
    def changed_theme_cb(self, combobox):
        theme = combobox.get_active_text()
        if theme != -1:
            self.awn.settings["theme"] = self.theme = theme
            
            if hasattr(self, "mail"):
                self.refresh()
            else:
                self.__setIcon("login")
    
    def changed_backend_cb(self, combobox):
        backend = combobox.get_active_text()
        
        if backend != -1:
            self.awn.settings["backend"] = backend
            self.back = getattr(Backends(), backend)
            self.logout()
    
    def changed_client_cb(self, entry):
        self.awn.settings["email-client"] = self.emailclient = entry.get_text()


class Backends:
    class GMail:
        def __init__(self, key):
            self.key = key

        def url(self):
            return "http://mail.google.com/mail/"

        def update(self):
            f = feedparser.parse( \
                "https://%s:%s@mail.google.com/gmail/feed/atom" \
                 % (self.key.attrs["username"], self.key.password))

            if "bozo_exception" in f.keys():
                raise RuntimeError, _("There seem to be problems with our \
                    connection to your account. Your best bet is probably \
                    to log out and try again.")
            # Hehe, Google is funny. Bozo exception

            class MailItem:
                def __init__(self, subject, author):
                    self.subject = subject
                    self.author = author

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
        def __init__(self, key):
            self.key = key

        def url(self):
            return "http://mail.google.com/a/%s" % self.key.attrs["username"]

        def update(self):
            f = feedparser.parse( \
                "https://%s%%40%s:%s@mail.google.com/a/%s/feed/atom" \
                 % (self.key.attrs["username"], self.key.attrs["domain"], \
                 self.key.password, self.key.attrs["domain"]))

            if "bozo_exception" in f.keys():
                raise RuntimeError, _("There seem to be problems with our \
                    connection to your account. Your best bet is probably \
                    to log out and try again.")
            # Hehe, Google is funny. Bozo exception

            class MailItem:
                def __init__(self, subject, author):
                    self.subject = subject
                    self.author = author

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
        def drawLoginWindow(cls):
            vbox = gtk.VBox(spacing=12)
            vbox.set_border_width(6)
            
            hbox_username = gtk.HBox(spacing=13)
            vbox.add(hbox_username)
            
            hbox_username.add(gtk.Label(_("Username:") + "\t"))
            usrE = gtk.Entry()
            hbox_username.add(usrE)
            
            hbox_password = gtk.HBox(spacing=13)
            vbox.add(hbox_password)
            
            hbox_password.add(gtk.Label(_("Password:") + "\t"))
            pwdE = gtk.Entry()
            pwdE.set_visibility(False)
            hbox_password.add(pwdE)
            
            hbox_domain = gtk.HBox(spacing=13)
            vbox.add(hbox_domain)
            
            hbox_domain.add(gtk.Label(_("Domain:") + "\t"))
            domE = gtk.Entry()
            hbox_domain.add(domE)
            
            return {"layout": vbox, "callback": cls.__submitLoginWindow,
                "widgets": [usrE, pwdE, domE]}

        @staticmethod
        def __submitLoginWindow(widgets, awn):
            return awn.keyring.new("Mail Applet - %s(%s)" \
                % (widgets[0].get_text(), "GApps"), \
                widgets[1].get_text(), \
                {"username": widgets[0].get_text(),
                "domain": widgets[2].get_text()}, "network")

    class Empty:
        def __init__(self, key):
            self.subjects = [_("Dummy Message")]

        def update(self):
            pass

    try:
        global poplib
        import poplib
    except:
        pass
    else:
        class POP:
            def __init__(self, key):
                if key.attrs["usessl"]:
                    self.server = poplib.POP3_SSL(key.attrs["url"])
                else:
                    self.server = poplib.POP3(key.attrs["url"])

                self.server.user(key.attrs["username"])
                try:
                    self.server.pass_(key.password)
                except poplib.error_proto:
                    raise RuntimeError, _("Could not log in")

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

                class MailItem:
                    def __init__(self, subject, author):
                        self.subject = subject
                        self.author = author

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
            def drawLoginWindow(cls):
                vbox = gtk.VBox(spacing=12)
                vbox.set_border_width(6)
                
                hbox_username = gtk.HBox(spacing=13)
                vbox.add(hbox_username)
                
                hbox_username.add(gtk.Label(_("Username:") + "\t"))
                usrE = gtk.Entry()
                hbox_username.add(usrE)
                
                hbox_password = gtk.HBox(spacing=13)
                vbox.add(hbox_password)
                
                hbox_password.add(gtk.Label(_("Password:") + "\t"))
                pwdE = gtk.Entry()
                pwdE.set_visibility(False)
                hbox_password.add(pwdE)
                
                hbox_server = gtk.HBox(spacing=13)
                vbox.add(hbox_server)
                
                hbox_server.add(gtk.Label(_("Server:") + "\t"))
                srvE = gtk.Entry()
                hbox_server.add(srvE)
                sslE = gtk.CheckButton(label=_("Use SSL encryption"))
                hbox_server.add(sslE)
                
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

if __name__ == "__main__":
    applet = AWNLib.initiate({"name": applet_name, "short": "mail",
	    "version": applet_version,
        "description": applet_description,
        "logo": applet_logo,
        "author": "Pavel Panchekha",
        "copyright-year": 2008,
        "email": "pavpanchekha@gmail.com",
        "type": ["Network", "Email"],
        "settings-per-instance": True})
    applet = MailApplet(applet)
    AWNLib.start(applet.awn)
