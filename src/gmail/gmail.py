#!/usr/bin/python
import sys, os
import gobject
import pygtk
import cairo
import gtk
from gtk import gdk
import awn
import time
import rsvg
from StringIO import StringIO
import libgmail
from os import system
import re

usr = "google"
pwd = "pwd"
theme = "Default" #Change it here if you want!

def timer1 (applet, mail):
  return mail.ThreadFunction(applet)

def cleanGmailSubject(n):
    n = re.sub(r"^[^>]*\\>", "", n)
    n = re.sub(r"\\[^>]*\\>$", "", n)
    n = n.replace("&quot;", "\"")
    n = n.replace("&amp;", "&")
    if len(n) > 37:
        n = n[:37] + "..."
    return n

def cleanGmailMsg(n):
    n = re.sub("\n\s*\n", "\n",
        re.sub("&[#x(0x)]?\w*;", " ",
        re.sub("(\<[^\<\>]*\>)", "",
        msg.source)))
        # Wow, huh?

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

class App (awn.AppletSimple):
    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)

        self.drawPWDlog()

        theme = gtk.icon_theme_get_default()
        icon = theme.load_icon ("stock_mail-reply", height, 0)
        #icon = gdk.pixbuf_new_from_file ("/home/njp/Projects/test.png")
        self.set_icon (icon)
        
        self.title = awn.awn_title_get_default ()
        self.dialog = awn.AppletDialog (self)
        self.connect ("button-press-event", self.button_press)
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)
        self.pwDialog.connect ("focus-out-event", self.pw_dialog_focus_out)
        self.dialog.connect ("focus-out-event", self.dialog_focus_out)

        # Show PWD/Mail dlog
        self.showDlog = lambda: self.pwDialog.show_all()
        # Redefine that once logged in

    def drawPWDlog (self):
        self.pwDialog = awn.AppletDialog (self)

        # Table based layout
        # Because we all yearn for web designing c. 1995
        pwdLayout = gtk.Table()
        self.pwDialog.add(pwdLayout)
        pwdLayout.resize(4, 1)
        pwdLayout.set_row_spacing(0, 17)
        pwdLayout.set_row_spacing(1, 26)
        pwdLayout.set_row_spacing(2, 24)
        pwdLayout.set_row_spacing(3, 1)
        pwdLayout.show_all()

        # Title of Window
        titleLabel = gtk.Label("Name and Password:")
        pwdLayout.attach(titleLabel, 0, 2, 0, 2)
        titleLabel.show_all()

        # Username input box
        entryUsr = gtk.Entry()
        entryUsr.set_activates_default(True)
        pwdLayout.attach(entryUsr, 0, 2, 1, 3)
        entryUsr.show_all()
        self.pwDialog.usrEntry = entryUsr # For later use

        # Password input box
        entryPwd = gtk.Entry()
        entryPwd.set_visibility(False)
        entryPwd.set_activates_default(True)
        pwdLayout.attach(entryPwd, 0, 2, 2, 4)
        entryPwd.show_all()
        self.pwDialog.pwdEntry = entryPwd # For later use

        # Submit button
        submitPwd = gtk.Button(label = "Log In", use_underline = False)
        submitPwd.set_flags(gtk.CAN_DEFAULT)
        submitPwd.grab_default()
        pwdLayout.attach(submitPwd, 0, 2, 4, 5)
        submitPwd.show_all()
        submitPwd.connect("clicked", self.submit_pwd)

    def refresh(self, widget):
        global msgs
        self.dialog.hide()
        self.mail = GMail("Default")
        self.mail.check()
        self.mail.LoadTheme()
        self.mail.DrawTheme(self)
        self.redrawDlog(msgs)
        self.dialog.show_all()

    def redrawDlog(self, msgs):
        del self.dialog
        self.dialog = awn.AppletDialog (self)

        layout = gtk.Table()
        layout.resize(3, 3)
        #layout.set_row_spacing(0, 20)
        #layout.set_row_spacing(1, len(msgs)*20)
        layout.set_row_spacing(2, 20)
        layout.set_col_spacing(0, 50)
        layout.set_col_spacing(1, 10)
        layout.set_col_spacing(2, 50)
        self.dialog.add(layout)
        layout.show_all()

        label = gtk.Label("%d Mails in %s" % (len(msgs), usr))
        layout.attach(label, 0, 4, 0, 1)
        label.show_all()

        innerlyt = gtk.Table()
        innerlyt.resize(len(msgs), 2)
        innerlyt.set_row_spacings(20)
        innerlyt.set_col_spacing(0, 10)
        innerlyt.set_col_spacing(1, 80)

        for i in range(len(msgs)):
            label = gtk.Label(str(i+1) + ":")
            innerlyt.attach(label, 0, 1, i, i+2)
            label.show_all()

            label = gtk.Label(msgs[i])
            innerlyt.attach(label, 1, 2, i, i+2)
            label.show_all()
            print str(i+1) + ": " + msgs[i]

        layout.attach(innerlyt, 0, 4, 1, 2)

        button = gtk.Button(label = "Gmail")
        button.connect("clicked", self.showGmail)
        button.set_size_request(125, 27)
        layout.attach(button, 0, 2, 2, 3)
        button.show_all()

        button = gtk.Button(label = "Refresh")
        button.connect("clicked", self.refresh)
        button.set_size_request(125, 27)
        layout.attach(button, 3, 4, 2, 3)
        button.show_all()

        self.dialog.connect ("focus-out-event", self.dialog_focus_out)
    
    def submit_pwd (self, widget):
        global usr, pwd, theme

        usr = self.pwDialog.usrEntry.get_text()
        pwd = self.pwDialog.pwdEntry.get_text()

        # print "Submitted:", usr, pwd
        
        self.mail = GMail(theme)
        try:
            self.mail.check()
        except libgmail.GmailError:
            self.pwDialog.usrEntry.set_text("")
            self.pwDialog.pwdEntry.set_text("")
        else:
            self.mail.LoadTheme()
            self.mail.DrawTheme(self)

            self.timer = gobject.timeout_add (60000, timer1, self, self.mail)

            # redefine button click
            self.showDlog = lambda: self.dialog.show_all()

            self.pwDialog.hide ()
            self.redrawDlog(msgs)
            self.dialog.show_all()

    def button_press (self, widget, event):
        print "Showing"
        self.showDlog()
        self.title.hide (self)
        # Show dialog

    def showGmail (self, widget):
        system('gnome-open http://mail.google.com/mail/')

    def dialog_focus_out (self, widget, event):
        self.dialog.hide ()
        print "hide dialog"

    def pw_dialog_focus_out (self, widget, event):
        self.pwDialog.hide ()
        # Hide dialog

    def enter_notify (self, widget, event):
        global msgs
        self.title.show (self, "%d New Messages in %s" % (len(msgs), usr))
        self.redrawDlog(msgs)
        # Show title

    def leave_notify (self, widget, event):
        self.title.hide (self)
        # Hide title

class GMail:

    #Svg Memory Space
    SVGH_Face = ""
    msgs = 0
    theme = "Default"
    p_layouta = None
    Hover = False

    def __init__ (self, theme):
        self.theme = theme

    def check(self):
        global usr, pwd, msgs
        self.ga = libgmail.GmailAccount(usr, pwd)

        self.ga.login()

        self.sources = [cleanGmailSubject(i.subject) for i in self.ga.getMessagesByQuery("is:unread in:inbox")]

        self.ms = self.ga.getunreadInfo()

        if self.ms != None :
            #self.msgs = str(self.ms)
            #self.msgs = self.msgs.replace('[' , '')
            #self.msgs = self.msgs.replace(']' , '')
            #self.msgs = self.msgs.replace('inbox' , '')
            #self.msgs = self.msgs.replace(' ' , '')
            #self.msgs = self.msgs.replace(',' , '')
            #self.msgs = self.msgs.replace("'" , '')
            self.msgs = re.sub(r"\[|\]|(inbox)|,|'| ", "", str(self.ms))
        else:
            self.msgs = "0"



        #if str(self.msgs) == "1":
        #    txt = " Unread Message"
        #else:
        #    txt = " Unread Messages"
        #
        #print str(self.msgs) + txt
        msgs = self.sources

    def SetTitle(self, applet):
        applet.title.show (applet, str(self.msgs) + ' Unread Messages')

    def SetHover(self, applet, status):
        if status == True:
            self.Hover = True
            self.SetTitle(applet)
        if status == False:
            self.Hover = False
            applet.title.hide(applet)

    def ThreadFunction(self, applet):
        self.check()
        self.LoadTheme()
        self.DrawTheme(applet)
        if self.Hover == True:
            self.SetTitle(applet)
        return True

    def GetPixbufFromSurface(self, surface):
        sio = StringIO()
        surface.write_to_png(sio)
        sio.seek(0)
        loader = gtk.gdk.PixbufLoader()
        loader.write(sio.getvalue())
        loader.close()
        return loader.get_pixbuf()

    def GetThemeFile(self, filen, theme):
        return os.path.abspath(os.path.dirname(__file__)) + "/Themes/" + theme + "/" + filen

    def LoadTheme(self):
        if str(self.msgs) == "0" :
            self.SVGH_Face = rsvg.Handle(self.GetThemeFile('gmailread.svg', self.theme))
        else :
            print str(self.msgs)
            self.SVGH_Face = rsvg.Handle(self.GetThemeFile('gmailunread.svg', self.theme))

    def SetIconFromSurface(self, applet, surface):
        icon = self.GetPixbufFromSurface(surface)
        applet.set_icon (icon)

    def DrawTheme(self, applet):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 50, 50)
        ctx = cairo.Context(surface)
        #ctx.scale(0.50,0.50)
        self.SVGH_Face.render_cairo(ctx)
        ctx.translate(50,50)
        ctx.save()
        
        self.SetIconFromSurface(applet, surface)

if __name__ == "__main__":
    awn.init (sys.argv[1:])
    #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
    applet = App (awn.uid, awn.orient, awn.height)
    awn.init_applet (applet)
    applet.show_all ()
    gtk.main ()
