#!/usr/bin/python
#
#       gmail.py Version 2.0
#
#       Copyright 2008 Pavel Panchekha <pavpanchekha@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

# AWN API
from awn.extras import AWNLib

#GUI
import gtk, gobject

# Decrufting subject lines
import re

# Path stuff
import os

# Launching the browser and email client
import subprocess

# Yes! Someone else wrote the header-parsing algorithm!
import email

# For later AWNLib-mediated import
feedparser = None

import gettext
APP = "Mail Applet"
DIR = "locale"
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

import locale


def Label(str):
    """
    Create a button, add the markup
    """

    q = gtk.Label(str)
    q.set_use_markup(True)
    return q

def HBox(list, homog=True):
    """
    Create a new HBox and add all the widgets from list to it
    """

    q = gtk.HBox(homog)

    for i in list:
        q.add(i)

    return q

def VBox(list, homog=True):
    """
    Create a new HBox and add all the widgets from list to it
    """

    q = gtk.VBox(homog)

    for i in list:
        q.add(i)

    return q

class MailError(Exception):
    """
    Because networks never crash or anything, right?
    """

    def __init__(self, type):
        self.type = type

    def __str__(self):
        return _("The Mail Applet had an error: %s") % self.type

def strMailMessages(num):
    return gettext.ngettext("You have %d new message", \
        "You have %d new messages", num) % num

def strMessages(num):
    return gettext.ngettext("%d unread message", \
        "%d unread messages", num) % num

class MailApplet:
    def __init__(self, awn):
        # Interface with AWN
        self.awn = awn

        self.awn.settings.require() # Settings like mail backend and login
        self.awn.keyring.require() # Secure login remembering
        self.awn.notify.require() # "You have # new messages"

        self.awn.settings.cd("mail-%s" % self.awn.uid)

        try:
            self.back = getattr(Backends(), self.awn.settings["backend"])
            # Backends has a number of classes as attributes
            # The setting has the name, as a string, of one of them
        except ValueError:
            self.back = Backends().GMail
            self.awn.settings["backend"] = "GMail"
            # If you can't find the setting, assign a default one.

        try:
            self.theme = self.awn.settings["theme"]
            self.__setIcon("login")
            # Set the theme...
        except ValueError, gobject.GError:
            self.theme = "Tango"
            self.awn.settings["theme"] = "Tango"
            # ... or at least a default

        try:
            self.emailclient = self.awn.settings["email-client"]
            # Email clients. Pft.
        except ValueError:
            self.emailclient = "evolution -c mail"
            self.awn.settings["email-client"] = "evolution"
            # Moonbeam, are you happy?

        try:
            self.hide = self.awn.settings["hide"]
            # Whether to autohide
        except ValueError:
            self.hide = False
            self.awn.settings["hide"] = False
            # No by default

        try:
            self.showerror = self.awn.settings["show-network-errors"]
            # Whether to show errors
        except ValueError:
            self.showerror = True
            self.awn.settings["show-network-errors"] = True
            # Yes by default

        self.awn.title.set(_("Mail Applet (Click to Log In)"))
        self.drawPrefDlog()

        self.awn.module.get("feedparser", { \
            "Debian/Ubuntu": "python-feedparser", \
            "Gentoo": "dev-python/feedparser", \
            "OpenSUSE": "python-feedparser"},
            self.__init2)

    def __init2(self, module):
        global feedparser
        if module:
            feedparser = module

        self.login()
        #print "Initing"

    def login(self, force=False):
        self.__setIcon("login")
        if force:
            return self.drawPWDDlog()
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
            # Either of the operations can go wrong.
        except MailError:
            # Login has failed
            self.drawPWDDlog(True)

        else:
            self.awn.notify.send(_("Mail Applet"), \
                _("Logging in as %s") % key.attrs["username"], \
                self.__getIconPath("login", full=True))

            # Login successful
            self.__setIcon("read")

            self.awn.settings["login-token"] = key.token

            self.timer = self.awn.timing.time(self.refresh, 300)
            self.refresh()

    def refresh(self, x=None):
        oldSubjects = self.mail.subjects

        try:
            self.mail.update()
        except MailError, (err):
            self.awn.icon.set(self.getIcon("error"))

            if self.showerror:
                self.drawErrorDlog(err)
            return

        diffSubjects = [i for i in self.mail.subjects if i not in \
            oldSubjects]
        if len(diffSubjects) > 0:

            msg = strNewMessages(len(diffSubjects))

            for i in diffSubjects:
                msg.append("\n" + i)

            self.awn.notify.send(_("New Mail - Mail Applet"), msg, \
                self.__getIconPath("unread", full=True))
            # Show the new mail dialog

            self.awn.effects.notify()
            # Do the "attention" effect

        self.awn.title.set(strMessages(len(self.mail.subjects)))

        self.__setIcon(len(self.mail.subjects) > 0 and "unread" or "read")

        if self.hide and len(self.mail.subjects) == 0:
            self.awn.icon.hide()

        self.awn.dialog.hide()
        self.drawMainDlog()

    def __setIcon(self, name):
        self.awn.icon.file(self.__getIconPath(name))

    def __getIconPath(self, name, full=False):
        files = {
                "error": "Themes/%s/error.svg" % self.theme,
                "login": "Themes/%s/login.svg" % self.theme,
                "read": "Themes/%s/read.svg" % self.theme,
                "unread": "Themes/%s/unread.svg" % self.theme,
                }
        if not full:
            return files[name]
        else:
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), \
                files[name])

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
        dlog=self.awn.dialog.new("main", strMessages(len(self.mail.subjects)))

        layout = gtk.VBox()
        dlog.add(layout)

        if len(self.mail.subjects) > 0:
            tbl = gtk.Table(len(self.mail.subjects), 2)
            tbl.set_col_spacings(10)
            for i in xrange(len(self.mail.subjects)):
                tbl.attach(Label("<b>"+str(i+1)+"</b>"), 0, 1, i, i+1)
                tbl.attach(Label(self.mail.subjects[i]), 1, 2, i, i+1)
                #print "%d: %s" % (i+1, self.mail.subjects[i])
            layout.add(tbl)
        else:
            layout.add(Label("<i>" + _("Hmmm, nothing here") + "</i>"))

        buttons = []

        if hasattr(self.mail, "url") or hasattr(self.mail, "showWeb"):
            # Don't show the button if it doesn't do anything

            # This'll be the "show web interface" button
            b = gtk.Button()
            b.set_relief(gtk.RELIEF_NONE) # Found it; that's a relief
            b.set_image(gtk.image_new_from_stock(gtk.STOCK_NETWORK, \
                gtk.ICON_SIZE_BUTTON))
            b.connect("clicked", lambda x: self.__showWeb())
            buttons.append(b)

        # This is the "show desktop client" button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT, \
            gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", lambda x: self.__showDesk())
        buttons.append(b)

        # Refresh button
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH, \
            gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", lambda x: self.refresh())
        buttons.append(b)

        # Show preferences
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_PREFERENCES, \
            gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", \
            lambda x: self.awn.dialog.toggle("secondary"))
        buttons.append(b)

        # Log out
        b = gtk.Button()
        b.set_relief(gtk.RELIEF_NONE)
        b.set_image(gtk.image_new_from_stock(gtk.STOCK_STOP, \
            gtk.ICON_SIZE_BUTTON))
        b.connect("clicked", lambda x: self.logout())

        buttons.append(b)
        layout.add(HBox(buttons))

    def drawErrorDlog(self, msg=""):
        dlog = self.awn.dialog.new("main", _("Error in Mail Applet"))

        layout = gtk.VBox()
        dlog.add(layout)

        # Error Message
        text = gtk.Label(_("There seem to be problems with our connection to \
            your account. Your best bet is probably to log out and try again. \
            \n\nHere is the error given:\n\n<i>%s</i>") % msg)
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)
        layout.add(text)

        # Submit button
        ok = gtk.Button(label = _("Fine, log me out"))
        layout.add(ok)

        def qu(x):
            dlog.hide()
            self.logout()

        ok.connect("clicked", qu)

        dlog.show_all() # We want the dialog to show itself right away

    def drawPWDDlog(self, error=False):
        dlog = self.awn.dialog.new("main", _("Log In"))
        layout = gtk.VBox()
        dlog.add(layout)

        if error:
            layout.add(Label("<i>" + _("Wrong Username or Password") + "</i>"))

        if hasattr(self.back, "drawLoginWindow"):
            t = self.back.drawLoginWindow()
            ilayout = t["layout"]
        else:
            # Username input box
            usrE = gtk.Entry()

            # Password input box
            pwdE = gtk.Entry()
            pwdE.set_visibility(False)

            ilayout = VBox([HBox([Label(_("Username:")), usrE]),
                HBox([Label(_("Password:")), pwdE])])

            t = {}

            t["callback"] = \
                lambda widgets, awn: awn.keyring.new("Mail Applet - %s(%s)" \
                % (widgets[0].get_text(), self.awn.settings["backend"]), \
                widgets[1].get_text(), \
                {"username": widgets[0].get_text()}, "network")

            t["widgets"] = [usrE, pwdE]

        layout.add(ilayout)

        # Submit button
        submit = gtk.Button(label = _("Log In"), use_underline = False)
        layout.add(submit)

        def onsubmit(x=None, y=None):
            dlog.hide()
            self.submitPWD(t["callback"](t["widgets"], self.awn))

        submit.connect("clicked", onsubmit)

        button = gtk.Button(label=_("Change Options"))
        button.connect("clicked", \
            lambda x: self.awn.dialog.toggle("secondary"))
        layout.add(button)

        dlog.show_all()

    def drawPrefDlog(self):
        dlog = self.awn.dialog.new("secondary", _("Options"), focus=False)

        layout = gtk.VBox()
        dlog.add(layout)

        theme = gtk.combo_box_new_text()
        theme.set_title(_("Theme"))
        themes = [i for i in os.listdir(os.path.join(os.path.dirname( \
            os.path.abspath(__file__)), "Themes"))]
            # Ewww. Stupid AWN
        for i in themes:
            theme.append_text(i)
        theme.set_focus_on_click(True)
        layout.add(HBox([Label(_("Theme: ")), theme]))

        backend = gtk.combo_box_new_text()
        backend.set_title(_("Backend"))
        backends = [i for i in dir(Backends) if i[:2] != "__"]
        for i in backends:
            backend.append_text(i)
        backend.set_focus_on_click(True)
        layout.add(HBox([Label(_("Backend: ")), backend]))

        email = gtk.Entry()
        email.set_text(self.emailclient)
        layout.add(HBox([Label(_("Email Client: ")), email]))

        hidden = gtk.CheckButton(label=_("Hide Unless New"))
        hidden.set_active(self.hide)
        layout.add(hidden)

        showerror = gtk.CheckButton(label=_("Alert on Network Errors"))
        showerror.set_active(self.showerror)
        layout.add(showerror)

        save = gtk.Button(label = _("Save"), use_underline = False)
        layout.add(save)

        def saveit(self, t, b, c, h, s, dlog):
            dlog.hide()

            #print t
            #print b
            #print c # Oh, how I wish for a debugger
            #print h
            #print s

            if t and t != self.theme and t != -1:
                self.theme = t
                self.awn.settings["theme"] = t
                if hasattr(self, "mail"):
                    self.refresh()

            if c and c != self.emailclient:
                self.awn.settings["email-client"] = c
                self.emailclient = c

            if h != self.hide:
                self.awn.settings["hide"] = h
                self.hide = h
                if hasattr(self, "mail"):
                    self.refresh()

            if s != self.showerror:
                self.awn.settings["show-network-errors"] = s
                self.showerror = s

            if b != -1 and b:
                self.awn.settings["backend"] = b
                b = getattr(Backends(), b)
            else:
                return

            if b != self.back and b != -1:
                self.back = b
                self.logout()

        save.connect("clicked", lambda x: saveit(self, \
            theme.get_active_text(), backend.get_active_text(), \
            email.get_text(), hidden.get_active(), \
            showerror.get_active(), dlog))

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
                raise MailError, _("Could not log in")
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
                    raise MailError, _("Could not log in")

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
                # Username input box
                usrE = gtk.Entry()

                # Password input box
                pwdE = gtk.Entry()
                pwdE.set_visibility(False)

                # Server input box
                srvE = gtk.Entry()

                sslE = gtk.CheckButton(label=_("Use SSL encryption"))

                layout = VBox([HBox([Label(_("Username:")), usrE]),
                    HBox([Label(_("Password:")), pwdE]),
                    HBox([Label(_("Server:")), srvE]),
                    sslE])

                return {"layout": layout, "callback": cls.__submitLoginWindow,
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
    applet = AWNLib.initiate({"name": _("Mail Applet"),
        "short": "mail",
        "author": "Pavel Panchekha",
        "email": "pavpanchekha@gmail.com",
        "description": _("An applet to check one's email"),
        "type": ["Network", "Email"]})
    applet = MailApplet(applet)
    AWNLib.start(applet.awn)
