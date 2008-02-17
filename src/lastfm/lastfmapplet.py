#!/usr/bin/env python

# Copyright (c) 2007 Tomas Kramar (kramar.tomas@gmail.com), Jonathan Rauprich (joni@noplu.de)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import sys, os
import gobject
import pygtk
import gtk
import gst
import awn
import shutil
import os.path
import urllib
from lastfm import lastfm
from gtk import gdk
import lastfmpreferences
import lastfmconfig
import lastfmexception
import gconf
import imageproducer
      

class App (awn.AppletSimple):
    
  def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
                   
        self.path = os.path.dirname(__file__)
        
        self.config = lastfmconfig.LastFmConfiguration()

        self.scale_and_set_icon()
        self.title = awn.awn_title_get_default ()
        
        ## Player Dialog
        self.player_dialog = awn.AppletDialog (self)
                   
        player_label = gtk.Label("Last.fm Player")
        
        player_vbox = gtk.VBox(False, 0)
        player_hbox = gtk.HBox(False, 0)
        
        #title_hbox = gtk.HBox(False,0)
        #self.playing_title = gtk.LinkButton()
        #title_hbox.pack_start(self.playing_title, False, False, 0)
        
        self.play_button = self.create_button("play")      
        self.play_button.connect("clicked", self.player_dialog_play_button)
        self.playing = False
        skip_button = self.create_button("skip")
        skip_button.connect("clicked", self.player_dialog_skip_button)
        love_button = self.create_button("love")
        love_button.connect("clicked", self.player_dialog_love_button)
        ban_button  = self.create_button("ban")
        ban_button.connect("clicked", self.player_dialog_ban_button)
        
        player_hbox.pack_start(self.play_button, False, False, 0)
        player_hbox.pack_start(skip_button, False, False, 0)
        player_hbox.pack_start(love_button, False, False, 0)
        player_hbox.pack_start(ban_button, False, False, 0)    
                       
        player_vbox.pack_start(player_label, False, False, 0)
        #player_vbox.pack_start(title_hbox, False, False, 0)
        player_vbox.pack_start(player_hbox, False, False, 0)
            
        player_vbox.show_all
        
        self.player_dialog.add (player_vbox)
        
        self.player_dialog.connect ("focus-out-event", self.player_dialog_focus_out)
        
        ## Station Dialog
        self.station_dialog = awn.AppletDialog(self)
        
        station_label = gtk.Label("Select Station")
        
        station_vbox = gtk.VBox(False, 0)
        station_hbox = gtk.HBox(False, 0)
        
        self.station_type = gtk.combo_box_new_text()
        self.station_type.append_text("Similar Artists")
	self.station_type.append_text("Group")
        self.station_type.append_text("Music for Tag")
        self.station_type.append_text("Music for User")
        self.station_type.set_active(0)
        self.station_type.set_property('has-frame', False)
        
        self.station_name = gtk.Entry()
        self.station_name.connect('key-release-event', self.station_name_key_event)
        #station_name.set_property('has-frame', False)
        
        station_play = self.create_button("play")
        
        station_play.connect('clicked', self.station_dialog_play_button)

        station_hbox.pack_start(self.station_type, False, 0, 5)
        station_hbox.pack_start(self.station_name, False, 0, 5)
        station_hbox.pack_start(station_play, False, 0, 0)
        
        station_vbox.pack_start(station_label, False, False, 0)        
        station_vbox.pack_start(station_hbox, False, False, 0)
        
        self.station_dialog.add (station_vbox)      
        
        player_vbox.show_all()
                
        self.connect ("button-press-event", self.applet_button_press)
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)
        
        #lastfm stuff
        self.reload_config()
        self.lastfm = lastfm()
     
        
        #gstreamer stuff
        self.gst_player = gst.element_factory_make("playbin", "player")
        fakesink = gst.element_factory_make('fakesink', "my-fakesink")
        self.gst_player.set_property("video-sink", fakesink)
        bus = self.gst_player.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self.on_message)      
        
        #popup menu
        self.popup_menu = gtk.Menu()
        pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
        self.popup_menu.append(pref_item)
        pref_item.connect_object("activate", self.preferences_callback, self)
        pref_item.show()

        #stop/play button images setup
        self.play_button_image = gtk.Image()
        self.play_button_image.set_from_file(self.path + "/icons/play.png")
        self.stop_button_image = gtk.Image()
        self.stop_button_image.set_from_file(self.path + "/icons/stop.png")

        #connect as needed
        self.connected = False;
        
        self.station_desc = "";
        self.title_text = "LastFM Applet - Click to start listening!"

        self.imageproducer = imageproducer.ImageProducer(height)
        
  def scale_and_set_icon(self):
       self.inactive_icon = gdk.pixbuf_new_from_file (self.path + "/icons/" + self.config.get_icon())
       if self.height != self.inactive_icon.get_height():
           self.inactive_icon = self.inactive_icon.scale_simple(self.height,self.height,gtk.gdk.INTERP_BILINEAR)
            
       self.set_icon (self.inactive_icon)

  def connect_to_lastfm(self):
      try:
        retval = self.lastfm.connect(self.username, self.password)
        if retval == 1:
           window = self.get_preferences_window()
           window.show_all()
        else:
           self.connected = True
           # we are connected, set the title to default
           self.title_text = "Oops, we had a problem connecting."
           return True
      except lastfmexception.LastFmException:
          # set the title to notify the user
          self.title_text = "Oops, we had a problem connecting."
          return False

  def reload_config(self):
      self.username = self.config.get_username()
      self.password = self.config.get_password()
      # Empty name or passord will make the login fail, which will bring up the preferences
      self.scale_and_set_icon()
  
  def preferences_callback(self, widget):
  		window = self.get_preferences_window()
		window.show_all()

  def get_preferences_window(self):
      window = lastfmpreferences.LastFmPreferences(self)
      window.set_size_request(270, 300)
      window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
      window.set_destroy_with_parent(True)
      icon = gdk.pixbuf_new_from_file(self.path + "/icons/" + self.config.get_icon())
      window.set_icon(icon)

      return window

  def on_message(self, bus, message):
      t = message.type
      if t == gst.MESSAGE_TAG:
          self.lastfm.getmetadata()
          # fetch the cover, if ther is no cover, just take a standart
          imageurl = self.lastfm.get_cover_url()
          
          if imageurl:
              image = urllib.urlopen(imageurl)
              temp = image.read()
              image.close()
              f = open('/tmp/lfmapt',"wb")
              f.write(temp)
              f.close()
          else:
              shutil.copy(self.path + "/icons/cd.png", "/tmp/lfmapt")             
              #path_to_cover = self.path + "/icons/cd.png"              
         
          
          path_to_cover = self.imageproducer.generate_cover("/tmp/lfmapt")  
          self.set_icon (gdk.pixbuf_new_from_file(path_to_cover))
          
          #self.playing_title(self.lastfm.metadata['artist'] + " - " + self.lastfm.metadata['track']);
          
      elif t == gst.MESSAGE_EOS:
          self.set_icon (self.inactive_icon)
      elif t == gst.MESSAGE_ERROR:
          self.set_icon (self.inactive_icon)
      
  def create_button(self, name):
      image = gtk.Image()
      image.set_from_file(self.path + "/icons/" + name + ".png")
      button = gtk.Button(stock="gtk-apply")
      button.set_image(image)
      button.set_relief(gtk.RELIEF_NONE)
      button.set_label("")
      return button  
            
  def applet_button_press (self, widget, event):
      self.station_dialog.hide ()
      self.title.hide (self)

      if event.button == 3:
          self.popup_menu.popup(None,None,None,event.button,event.time)
      else:
          self.player_dialog.show_all()

  def player_dialog_focus_out (self, widget, event):
      self.player_dialog.hide ()
      
  def player_dialog_play_button (self, widget):
      if self.playing == False:
         self.player_dialog.hide ()
         self.station_dialog.show_all ()
      else:
         self.lastfm.command('nortp')
         self.gst_player.set_state(gst.STATE_NULL)
         self.player_dialog.hide()
         self.playing = False
         self.set_icon(self.inactive_icon)       
         self.play_button.set_image(self.play_button_image)         
      
  def player_dialog_skip_button (self, widget):
      self.player_dialog.hide ()
      self.lastfm.command('skip')
      self.gst_player.set_state(gst.STATE_NULL)
      self.gst_player.set_state(gst.STATE_PLAYING)     
      
  def player_dialog_love_button (self, widget):
      self.player_dialog.hide()
      self.lastfm.command('love')
      
  def player_dialog_ban_button (self, widget):
      self.player_dialog.hide()
      self.lastfm.command('ban')
      self.gst_player.set_state(gst.STATE_NULL)
      self.gst_player.set_state(gst.STATE_PLAYING)     

  def station_dialog_play_button (self, widget):
      self.do_play()

  def station_name_key_event(self, widget, event):
      if event.keyval == gtk.keysyms.Return:
         self.do_play()

  def do_play(self):
      if self.connected == False:
         if self.connect_to_lastfm() == False:
             return

      self.station_dialog.hide()
      self.gst_player.set_state(gst.STATE_NULL)
      act = self.station_type.get_active()
      # it looks like a bug in last.fm webservices - when playing the 'music for user' station
      # their service always returns the last station type name
      # anyway, we do not need to ask them what station are we listening to, we already know it
      if act == 0:
         station = "similarartists"
      elif act == 1:
         station = "group"
      elif act == 2:
         station = "tag"
      elif act == 3:
         station = "personal"
      
      self.lastfm.command("rtp")
      self.station_desc = self.lastfm.changestation(station, self.station_name.get_text())
      
      if  self.station_desc == False:
          print "bad thing happend, returning"
          return
      
      self.gst_player.set_property('uri', self.lastfm.info['stream_url'])
      self.gst_player.set_state(gst.STATE_PLAYING)
      self.playing = True
      self.play_button.set_image(self.stop_button_image)
      
  def enter_notify (self, widget, event):     
      if self.lastfm.metadata.has_key('station') and self.playing == True:
          self.title.show (self, self.station_desc + ": " + self.lastfm.metadata['artist'] + " - " + self.lastfm.metadata['track'])
      else:
          self.title.show (self, self.title_text)

  def leave_notify (self, widget, event):
      self.title.hide (self)
      

    
if __name__ == "__main__":
      awn.init (sys.argv[1:])
      #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
      applet = App (awn.uid, awn.orient, awn.height)
      awn.init_applet (applet)
      applet.show_all ()
      gtk.main ()
