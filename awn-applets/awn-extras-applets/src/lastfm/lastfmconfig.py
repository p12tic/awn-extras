#!/usr/bin/python

# Lastfm Applet Configuration for the Avant Window Navigator
# 2007 Tomas Kramar <kramar.tomas@gmail.com>
# This code is free.
# inspired by weather applet preferences window


import gtk
from gtk import gdk
import cairo
import wnck
import locale
import gettext
import md5

class LastFmConfiguration(gtk.Window):
   def __init__(self,applet):
      gtk.Window.__init__(self)
      super(LastFmConfiguration, self).__init__(gtk.WINDOW_TOPLEVEL)
      self.applet = applet
      self.set_title("Last.Fm Configuration")
      self.vbox = gtk.VBox(False, 0)
      self.add(self.vbox)

      # row 1
      hbox1 = gtk.HBox(True,0)
      label1 = gtk.Label("Username")
      hbox1.pack_start(label1)
      self.username = gtk.Entry(20)
      tmp_username = self.applet.gconf_client.get_string(self.applet.gconf_path + "/username")
      if tmp_username == None:
          tmp_username = ""
      self.username.set_text(tmp_username)
      hbox1.pack_start(self.username)
      self.vbox.pack_start(hbox1,False,False,2)

      # row 2
      hbox2 = gtk.HBox(True,0)
      label2 = gtk.Label("Password")
      hbox2.pack_start(label2)
      self.password = gtk.Entry(20)
      hbox2.pack_start(self.password)
      self.vbox.pack_start(hbox2,False,False,5)

      # row3
      hboxw = gtk.HBox(True,0)
      self.labelw = gtk.Label("")
      self.labelw.set_line_wrap(True)
      hboxw.pack_start(self.labelw)
      self.vbox.pack_start(hboxw,False,False,5)

      # Button
      hbox3 = gtk.HBox(True,0)
      self.go = gtk.Button(label="Save", stock="gtk-save")
      #self.go.set_size_request(50, 40)
      self.go.connect("clicked", self.go_clicked, "go")
      #self.go.set_sensitive(False)
      hbox3.pack_start(self.go)
      self.vbox.pack_start(hbox3,False,False,8)

   def go_clicked(self, widget, window):
      self.applet.gconf_client.set_string(self.applet.gconf_path + "/username", self.username.get_text())
      self.md5_password = md5.md5(self.password.get_text()).hexdigest()
      self.applet.gconf_client.set_string(self.applet.gconf_path + "/password", self.md5_password)
      
      retval = self.applet.lastfm.connect(self.username.get_text(), self.md5_password)

      if retval == 0:
         # login succesfull
         self.destroy()
      else:
         self.labelw.set_text("Invalid username/password. Try again.")
