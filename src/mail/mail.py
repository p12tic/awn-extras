#!/usr/bin/python
#
#       gmail.py Version 2.0
#
#       Copyright 2007 Pavel Panchekha <pavpanchekha@gmail.com>
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

from awn.extras import AWNLib
import gobject
import gtk
from gtk import gdk
import re
import os
import subprocess

feedparser = None

class MailError(Exception):
    def __init__(self, type):
        self.type = type

    def __str__(self):
        return "The Mail applet had an error while trying to %s" % self.type

class Applet:
    def __init__(self):
        self.awn = AWNLib.initiate({"name": "Mail Applet", "short": "mail"})
        self.awn.settings.require()
        self.awn.keyring.require()
        self.awn.notify.require()

        try:
            self.back = getattr(Backends(), self.awn.settings["backend"])
        except:
            self.back = Backends().GMail
            self.awn.settings["backend"] = "GMail"

        # The Joy of Python - Pavel Panchekha
        # A haiku
        #
        #       Python is real cool
        # First class classes are awesome
        #        Joy and happiness
        #

        try:
            self.theme = self.awn.settings["theme"]
        except:
            self.theme = "Tango"
            self.awn.settings["theme"] = "Tango"

        try:
            self.hide = self.awn.settings["hide"]
        except:
            self.hide = False
            self.awn.settings["hide"] = False

        self.awn.title.set("Mail Applet (Click to Log In)")
        self.awn.icon.set(self.getIcon("login"))
        self.awn.module.get("feedparser", { \
            "Debian/Ubuntu": "python-feedparser", \
            "Gentoo": "dev-python/feedparser", \
            "OpenSUSE": "python-feedparser"},
            self.init2)

    def init2(self, module=None, force=False):
        global feedparser
        if module:
            feedparser = module

        if force:
            return self.drawPWDDlog()

        self.drawPrefDlog()

        try:
            token = self.awn.settings["login-token"]
            if self.awn.settings["login-token"] == 0:
                raise Exception
        except:
            self.drawPWDDlog()
        else:
            key = self.awn.keyring.new()
            key.token = token
            self.awn.notify.send("Mail Applet", "Logging in as %s" % key.name, \
                self.getIconPath("login", full=True))
            self.submitPWD(key)

    def submitPWD(self, key, dlog=None):
        if dlog:
            dlog.hide()

        try:
            self.mail = self.back(key)
            self.mail.update()
        except MailError:
            #print "Mail Applet: Login unsuccessful"
            self.drawPWDDlog(True)
        else:
            #print "Mail Applet: Login successful"
            self.awn.icon.set(self.getIcon("read"))

            self.awn.settings["login-token"] = key.token

            self.timer = self.awn.timing.time(self.refresh, 300)
            self.refresh()

    def refresh(self, widget=None):
        olen = len(self.mail.subjects)
        try:
            self.mail.update()
        except MailError, (err):
            self.awn.icon.set(self.getIcon("error"))
            self.drawErrorDlog(err)
            return False

        if len(self.mail.subjects) > olen:
            self.awn.notify.send("New Mail - Mail Applet", \
                "You have %s new mail" % str(len(self.mail.subjects) - olen), \
                self.getIconPath("unread", full=True))
            self.awn.effects.notify()
        self.awn.title.set("%d Unread Message%s" % \
                (len(self.mail.subjects), len(self.mail.subjects) \
                != 1 and "s" or ""))
        self.awn.icon.set(self.getIcon(len(self.mail.subjects) > 0 and \
            "unread" or "read"()))

        if self.hide and len(self.mail.subjects) > 0:
            self.awn.icon.hide()

        if self.awn.dialog.main:
            self.awn.dialog.main.hide()
        self.drawMainDlog()

    def logout(self):
        self.awn.icon.set(self.getIcon("login"))
        self.awn.settings["login-token"] = 0
        self.drawPWDDlog()

    def getIcon(self, name):
        return self.awn.icon.getFile(self.getIconPath(name))

    def getIconPath(self, name, full=False):
        files = {
                "error": "Themes/%s/error.svg" % self.theme,
                "login": "Themes/%s/login.svg" % self.theme,
                "read": "Themes/%s/read.svg" % self.theme,
                "unread": "Themes/%s/unread.svg" % self.theme,
                }
        if not full:
            return files[name]
        else:
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), files[name])

    def showWeb(self):
        if hasattr(self.mail, "showWeb"):
            self.mail.showWeb()
        elif hasattr(self.mail, "url"):
            subprocess.Popen(["xdg-open", self.mail.url()])

    def showDesk(self):
        if hasattr(self.mail, "showDesk"):
            self.mail.showDesk()
        else:
            subprocess.Popen(['evolution', '-c', 'mail'])

    def drawMainDlog(self):
        dlog = self.awn.dialog.new("main")
        dlog.set_title(" %d Unread Message%s " % \
                (len(self.mail.subjects), len(self.mail.subjects) \
                != 1 and "s" or ""))

        layout = gtk.Table()
        layout.resize(2, 1)
        dlog.add(layout)

        if len(self.mail.subjects) > 0:
            innerlyt = gtk.Table()
            innerlyt.resize(len(self.mail.subjects), 2)
            #innerlyt.set_row_spacings(20)
            #innerlyt.set_col_spacing(0, 10)

            for i in xrange(len(self.mail.subjects)):
                label = gtk.Label("%d:" % (i+1))
                innerlyt.attach(label, 0, 1, i, i+1)

                label = gtk.Label(self.mail.subjects[i])
                innerlyt.attach(label, 1, 2, i, i+1)
                #print "%d: %s" % (i+1, self.mail.subjects[i])

            layout.attach(innerlyt, 0, 1, 1, 2)
        else:
            label = gtk.Label("<i>Hmmm, nothing here</i>")
            label.set_use_markup(True)
            layout.attach(label, 0, 1, 0, 1)

        btnlayout = gtk.Table()
        btnlayout.resize(1, 5)
        button1 = gtk.Button()
        button1.set_relief(gtk.RELIEF_NONE) # Found it; that's a relief
        button1.connect("clicked", lambda x: self.showWeb())
        button1.set_image(gtk.image_new_from_stock(gtk.STOCK_NETWORK, \
            gtk.ICON_SIZE_BUTTON))
        btnlayout.attach(button1, 0, 1, 0, 1)

        button2 = gtk.Button()
        button2.set_relief(gtk.RELIEF_NONE)
        button2.connect("clicked", lambda x: self.showDesk())
        button2.set_image(gtk.image_new_from_stock(gtk.STOCK_DISCONNECT, \
            gtk.ICON_SIZE_BUTTON))
        btnlayout.attach(button2, 1, 2, 0, 1)

        button3 = gtk.Button()
        button3.set_relief(gtk.RELIEF_NONE)
        button3.connect("clicked", lambda x: self.refresh())
        button3.set_image(gtk.image_new_from_stock(gtk.STOCK_REFRESH, \
            gtk.ICON_SIZE_BUTTON))
        btnlayout.attach(button3, 2, 3, 0, 1)

        button4 = gtk.Button()
        button4.set_relief(gtk.RELIEF_NONE)
        button4.connect("clicked", lambda x: self.awn.dialog.secondaryFocus())
        button4.set_image(gtk.image_new_from_stock(gtk.STOCK_PREFERENCES, \
            gtk.ICON_SIZE_BUTTON))
        btnlayout.attach(button4, 3, 4, 0, 1)

        button5 = gtk.Button()
        button5.set_relief(gtk.RELIEF_NONE)
        button5.connect("clicked", lambda x: self.logout())
        button5.set_image(gtk.image_new_from_stock(gtk.STOCK_STOP, \
            gtk.ICON_SIZE_BUTTON))
        btnlayout.attach(button5, 4, 5, 0, 1)

        layout.attach(btnlayout, 0, 1, 2, 3)

    def drawErrorDlog(self, msg=""):
        dlog = self.awn.dialog.new("main")
        dlog.set_title(" Error in Mail Applet ")

        table = gtk.Table()
        table.resize(3, 1)
        dlog.add(table)

        # Error Message
        text = gtk.Label("There seem to be problems with our connection to \
            your account. Your best bet is probably to log out and try again. \
            \n\nHere is the error given:\n\n<i>%s</i>" % msg)
        text.set_line_wrap(True)
        table.attach(text, 0, 1, 1, 2)
        text.set_use_markup(True)
        text.set_justify(gtk.JUSTIFY_FILL)

        # Submit button
        ok = gtk.Button(label = "Fine, log me out.")
        table.attach(ok, 0, 1, 2, 3)

        def qu(x):
            dlog.hide()
            self.logout()

        ok.connect("clicked", qu)

        dlog.show_all()
    def drawPWDDlog(self, error=False):
        dlog = self.awn.dialog.new("main")
        dlog.set_title(" Log In ")

        table = gtk.Table()
        dlog.add(table)

        if error:
            table.resize(6, 1)
        else:
            table.resize(5, 1)

        # Username input box
        usrE = gtk.Entry()
        usrE.set_activates_default(True)
        table.attach(usrE, 0, 1, 1, 2)

        # Password input box
        pwdE = gtk.Entry()
        pwdE.set_visibility(False)
        table.attach(pwdE, 0, 1, 2, 3)

        # Submit button
        submit = gtk.Button(label = "Log In", use_underline = False)
        table.attach(submit, 0, 1, 3, 4)

        if error:
            errmsg = gtk.Label("<i>Wrong Username or Password</i>")
            errmsg.set_use_markup(True)
            table.attach(errmsg, 0, 2, 4, 5)

        submit.connect("clicked", lambda x: \
            self.submitPWD(self.awn.keyring.new(usrE.get_text(), \
            pwdE.get_text(), {}, "network"), dlog))

        button4 = gtk.Button(label="Choose Backend")
        button4.connect("clicked", lambda x: self.awn.dialog.secondaryFocus())
        table.attach(button4, 0, 2, 5, 6)

        dlog.show_all()

    def drawPrefDlog(self):
        dlog = self.awn.dialog.new("secondary", focus=False)
        dlog.set_title(" Options ")

        table = gtk.Table()
        table.resize(4, 1)
        dlog.add(table)

        def showDlog(x=None, y=None):
            dlog.show_all()
            #print "Reshowing Dialog"

        theme = gtk.combo_box_new_text()
        theme.set_title("Theme")
        themes = [i for i in os.listdir(os.path.join(os.path.dirname( \
            os.path.abspath(__file__)), "Themes"))]
            # Ewww. Stupid AWN
        for i in themes:
            theme.append_text(i)
        table.attach(theme, 0, 1, 0, 1)
        theme.set_focus_on_click(True)

        backend = gtk.combo_box_new_text()
        backend.set_title("Backend")
        backends = [i for i in dir(Backends) if i[:2] != "__"]
        for i in backends:
            backend.append_text(i)
        table.attach(backend, 0, 1, 1, 2)
        backend.set_focus_on_click(True)

        hidden = gtk.CheckButton(label="Hide Unless New")
        hidden.set_active(self.hide)
        table.attach(hidden, 0, 1, 2, 3)

        save = gtk.Button(label = "Save", use_underline = False)
        table.attach(save, 0, 1, 3, 4)

        def saveit(self, t, b, h, dlog):
            if b != -1:
                self.awn.settings["backend"] = b
                b = getattr(Backends(), b)
            if t != self.theme and t != -1:
                self.theme = t
                self.awn.settings["theme"] = t
                self.refresh()
            if b != self.back and b != -1:
                self.back = b
                self.init2(force=True)
            if h != self.hide:
                self.awn.settings["hide"] = h
                self.hide = h
                self.refresh()
            dlog.hide()

        save.connect("clicked", lambda x: saveit(self, \
            theme.get_active_text(), backend.get_active_text(), \
            hidden.get_active(), dlog))

class Backends:
    class GMail:
        def __init__(self, key):
            self.key = key

        def url(self):
            return "http://mail.google.com/mail/"

        def update(self):
            f = feedparser.parse("https://%s:%s@mail.google.com/gmail/feed \
                /atom" % (self.key.name, self.key.password))

            if "bozo_exception" in f.keys():
                raise MailError("login")

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
                n = "[No Subject]"
            return n

        def __cleanGmailMsg(self, n):
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
            self.subjects = ["Dummy Message"]

        def update(self):
            pass

if __name__ == "__main__":
    applet = Applet()
    AWNLib.start(applet.awn)
