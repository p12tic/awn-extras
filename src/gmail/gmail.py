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
import os
import AWN
import gobject
import gtk
from gtk import gdk
import re

AppletTheme = "Tango"
feedparser = None

class MailError(Exception):
	def __init__(self, type):
		self.type = type

	def __str__(self):
		return "The GMail applet had an error while trying to %s" % self.type

def setIcon(icon, name):
	files = {
			"error": icon.getFile("Themes/%s/error.svg" % AppletTheme),
			"login": icon.getFile("Themes/%s/login.svg" % AppletTheme),
			"read": icon.getFile("Themes/%s/read.svg" % AppletTheme),
			"unread": icon.getFile("Themes/%s/unread.svg" % AppletTheme),
			}
	icon.set(files[name])

class Applet:
	def __init__(self):
		self.awn = AWN.initiate()
		self.awn.title.set("GMail Applet (Click to Log In)")
		setIcon(self.awn.icon, "login")
		self.awn.module.visual("feedparser", {"Ubuntu": "python-feedparser"}, self.init2)

	def init2(self, module):
		global feedparser
		feedparser = module
		self.drawPWDlog()

	def drawPWDlog(self, error=False):
		dlog = self.awn.dialog.new("main")

		# Table based layout
		# Because we all yearn for web designing c. 1995
		table = gtk.Table()
		dlog.add(table)

		if error:
			table.resize(5, 1)
		else:
			table.resize(4, 1)
		table.show_all()

		# Title of Window
		title = gtk.Label("<b>Name and Password:</b>")
		title.set_use_markup(True)
		table.attach(title, 0, 1, 0, 1)
		title.show_all()

		# Username input box
		usrE = gtk.Entry()
		usrE.set_activates_default(True)
		table.attach(usrE, 0, 1, 1, 2)
		usrE.show_all()

		# Password input box
		pwdE = gtk.Entry()
		pwdE.set_visibility(False)
		table.attach(pwdE, 0, 1, 2, 3)
		pwdE.show_all()

		# Submit button
		submit = gtk.Button(label = "Log In", use_underline = False)
		table.attach(submit, 0, 1, 3, 4)
		submit.show_all()

		if error:
			errmsg = gtk.Label("<i>Wrong Username or Password</i>")
			errmsg.set_use_markup(True)
			table.attach(errmsg, 0, 2, 4, 5)
			errmsg.show_all()

		submit.connect("clicked", lambda x:
			self.submitPWD(usrE.get_text(), pwdE.get_text(), dlog))
		dlog.show_all()
		AWN.start(self.awn)

	def submitPWD (self, usr, pwd, dlog=None):
		try:
			self.gmail = GMail(usr, pwd)
			self.gmail.update()
		except MailError:
			#print "GMail Applet: Login unsuccessful"
			self.drawPWDlog(True)
		else:
			#print "GMail Applet: Login successful"
			if dlog:
				dlog.hide()
				del dlog

			setIcon(self.awn.icon, "read")

			self.timer = gobject.timeout_add(15000, self.refresh)
			self.refresh()

	def drawErrorDlog(self, msg=""):
		dlog = self.awn.dialog.new("main")

		table = gtk.Table()
		dlog.add(table)

		table.resize(3, 1)
		table.show_all()

		# Title of Window
		title = gtk.Label("<b>Error in GMail Applet:</b>")
		title.set_use_markup(True)
		table.attach(title, 0, 1, 0, 1)
		title.show_all()

		# Error Message
		text = gtk.Label("There seem to be problems with our connection to \
			your account. Your best bet is probably to log out and try again. \
			\n\nHere is the error given:\n\n<i>%s</i>" % msg)
		text.set_line_wrap(True)
		table.attach(text, 0, 1, 1, 2)
		text.set_use_markup(True)
		text.set_justify(gtk.JUSTIFY_FILL)
		text.show_all()

		# Submit button
		ok = gtk.Button(label = "Fine, log me out.")
		table.attach(ok, 0, 1, 2, 3)
		ok.show_all()

		def qu(x):
			dlog.hide()
			self.logout()

		ok.connect("clicked", qu)

		dlog.show_all()

	def refresh(self, widget=None):
		#print "Applet Refreshed"
		try:
			self.gmail.update()
		except MailError, (err):
			setIcon(self.awn.icon, "error")
			self.drawErrorDlog(err)
			return False

		self.awn.title.set(self.gmail.title())
		setIcon(self.awn.icon, self.gmail.status())
		self.redrawDlog()
		return True

	def redrawDlog(self):
		dlog = self.awn.dialog.new("main")

		layout = gtk.Table()
		layout.resize(3, 3)
		dlog.add(layout)
		layout.show_all()

		label = gtk.Label("<b>%s</b>" % self.gmail.title())
		label.set_use_markup(True)
		layout.attach(label, 0, 4, 0, 1)
		label.show_all()

		if self.gmail.len() > 0:
			innerlyt = gtk.Table()
			innerlyt.resize(self.gmail.len(), 2)
			#innerlyt.set_row_spacings(20)
			#innerlyt.set_col_spacing(0, 10)

			for i in xrange(self.gmail.len()):
				label = gtk.Label("%d:" % (i+1))
				innerlyt.attach(label, 0, 1, i, i+1)
				label.show_all()

				label = gtk.Label(self.gmail.subjects[i])
				innerlyt.attach(label, 1, 2, i, i+1)
				label.show_all()
				#print "%d: %s" % (i+1, self.gmail.subjects[i])

			layout.attach(innerlyt, 0, 4, 1, 2)
		else:
			label = gtk.Label("<i>Hmmm, nothing here</i>")
			label.set_use_markup(True)
			layout.attach(label, 0, 4, 1, 2)

		button = gtk.Button(label = "Gmail")
		button.connect("clicked", self.showGmail)
		button.set_size_request(125, 27)
		layout.attach(button, 0, 1, 2, 3)
		button.show_all()

		button = gtk.Button(label = "Refresh")
		button.connect("clicked", self.refresh)
		button.set_size_request(125, 27)
		layout.attach(button, 3, 4, 2, 3)
		button.show_all()

	def showGmail (self, widget):
		os.system('gnome-open http://mail.google.com/mail/')

	def logout(self):
		setIcon(self.awn.icon, "login")
		self.drawPWDlog()

class GMail:
	def __init__(self, usr, pwd):
		self.usr = usr;
		self.pwd = pwd.encode("rot13")
		# Not at all secure. But, protection from random snoop across RAM

	def url(self):
		return "https://%s:%s@mail.google.com/gmail/feed/atom" % \
			(self.usr, self.pwd.encode("rot13"))
		# rot13 * rot13 = orig

	def update(self):
		f = feedparser.parse(self.url())

		if "bozo_exception" in f.keys():
			raise MailError("login")

		class MailItem:
			def __init__(self, subject, author):
				self.subject = subject
				self.author = author

		t = []
		self.subjects = []
		for i in f.entries:
			i.title = self.cleanGmailSubject(i.title)
			t.append(MailItem(i.title, i.author))
			self.subjects.append(i.title)

	def title(self):
		return "%d Unread Message%s" % \
			(len(self.subjects), len(self.subjects) != 1 and "s" or "")

	def status(self):
		if len(self.subjects) > 0:
			return "unread"
		else:
			return "read"

	def len(self):
		return len(self.subjects)

	def cleanGmailSubject(self, n):
		n = re.sub(r"^[^>]*\\>", "", n) # "sadf\>fdas" -> "fdas"
		n = re.sub(r"\\[^>]*\\>$", "", n) # "asdf\afdsasdf\>" -> "asdf"
		n = n.replace("&quot;", "\"")
		n = n.replace("&amp;", "&")
		n = n.replace("&nbsp;", "")

		if len(n) > 37:
			n = n[:37] + "..."
		return n

	def cleanGmailMsg(self, n):
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


if __name__ == "__main__":
	applet = Applet()
