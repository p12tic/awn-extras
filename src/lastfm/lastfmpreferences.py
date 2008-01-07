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
import os
import lastfmexception

class LastFmPreferences(gtk.Window):
   def __init__(self,applet):
      gtk.Window.__init__(self)
      self.path = os.path.dirname(__file__)
      #super(LastFmConfiguration, self).__init__(gtk.WINDOW_TOPLEVEL)
      self.applet = applet
      self.set_title("Last.Fm Configuration")
      self.vbox = gtk.VBox(False, 0)
      self.add(self.vbox)

      # row 1
      hbox1 = gtk.HBox(True,0)
      label1 = gtk.Label("Username")
      hbox1.pack_start(label1)
      self.username = gtk.Entry(20)
      self.username.set_text(self.applet.config.get_username())
      hbox1.pack_start(self.username)
      self.vbox.pack_start(hbox1,False,False,2)

      # row 2
      hbox2 = gtk.HBox(True,0)
      label2 = gtk.Label("Password")
      hbox2.pack_start(label2)
      self.password = gtk.Entry(20)
      self.password.set_visibility(False)
      hbox2.pack_start(self.password)
      self.vbox.pack_start(hbox2,False,False,5)

      # row3
      hboxw = gtk.HBox(True,0)
      self.labelw = gtk.Label("")
      self.labelw.set_line_wrap(True)
      hboxw.pack_start(self.labelw)
      self.vbox.pack_start(hboxw,False,False,5)
      
      # row 4
      hbox4 = gtk.HBox(True, 0)
      self.icon = gtk.Image()
      icon_name = self.applet.config.get_icon()
      icon_image = self.__create_and_scale_image(icon_name)
      self.icon.set_from_pixbuf(icon_image)
      
      hbox4.pack_start(self.icon)
      
      self.icon_list = gtk.combo_box_new_text()
      
      active_icon_num = 7 #default
      
      self.icon_list.append_text("black")
      if icon_name == "black.ico":
          active_icon_num = 0
      self.icon_list.append_text("blue")
      if icon_name == "blue.icon":
          active_icon_num = 1
      self.icon_list.append_text("cd")
      if icon_name == "cd.ico":
          active_icon_num = 2
      self.icon_list.append_text("green")
      if icon_name == "green.ico":
          active_icon_num = 3
      self.icon_list.append_text("grey")
      if icon_name == "grey.ico":
          active_icon_num = 4
      self.icon_list.append_text("orange")
      if icon_name == "orange.ico":
          active_icon_num = 5
      self.icon_list.append_text("purple")
      if icon_name == "purple.ico":
          active_icon_num = 6
      self.icon_list.append_text("red")
      if icon_name == "red.ico":
          active_icon_num = 7
      self.icon_list.append_text("white")
      if icon_image == "white.ico":
          active_icon_num = 8
          
      self.icon_list.set_active(active_icon_num)
      self.icon_list.set_property('has-frame', False)
      
      self.icon_list.connect('changed', self.icon_changed)
      
      hbox4.pack_start(self.icon_list)
      self.vbox.pack_start(hbox4,False,False,5)

      # Button
      hbox3 = gtk.HBox(True,0)
      self.go = gtk.Button(label="Save", stock="gtk-save")
      #self.go.set_size_request(50, 40)
      self.go.connect("clicked", self.go_clicked, "go")
      #self.go.set_sensitive(False)
      hbox3.pack_start(self.go)
      self.vbox.pack_start(hbox3,False,False,8)
      
   def __create_and_scale_image(self, name):
       icon_image = gdk.pixbuf_new_from_file(self.path + "/icons/" + name)
       icon_image.scale_simple(30,30,gtk.gdk.INTERP_BILINEAR)
       return icon_image

   def go_clicked(self, widget, window):
      
      self.applet.config.set_icon(self.icon_list.get_active_text() + ".ico")
      
      #if the password was left blank, do not change it and do not try to connect
      if self.password.get_text() == "":
          self.applet.reload_config()
          self.destroy()
          return
          
      self.applet.config.set_username(self.username.get_text())
      pwd_hash = self.applet.config.set_password(self.password.get_text())
      
      try:
          retval = self.applet.lastfm.connect(self.username.get_text(), pwd_hash)
          if retval == 0:
             # login succesfull
             self.destroy()        
          else:
             self.labelw.set_text("Invalid username/password. Try again.")
      except lastfmexception.LastFmException:
          self.labelw.set_text("Network Connection error: unable to contact Last.Fm")
          
      finally:
          #reload the config no matter if we are connected or not - it will at least change the icon 
          self.applet.reload_config()
         
   def icon_changed(self,event):
        icon_name = self.icon_list.get_active_text()
        icon_image = gdk.pixbuf_new_from_file(self.path + "/icons/" + icon_name + ".ico")
        self.icon.set_from_pixbuf(icon_image)
        
