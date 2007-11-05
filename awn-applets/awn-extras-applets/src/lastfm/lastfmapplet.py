#!/usr/bin/python

# Lastfm Applet for the Avant Window Navigator
# 2007 Jonathan Rauprich <joni@noplu.de>
# 2007 Tomas Kramar <kramar.tomas@gmail.com> - preferences dialog (gconf backend), stop/play toogle button, login verification
# This code is free.
# some code is from LastFMProxy, some from gstreamer tutorial and some from avatar-factory - rock on dudes


import sys, os
import gobject
import pygtk
import gtk
import gst
import awn
import os.path
import urllib
import shutil
from lastfm import lastfm
from gtk import gdk
import lastfmconfig
import gconf

class App (awn.AppletSimple):
    
  def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
        self.path = os.path.dirname(__file__)

        self.gconf_path = "/apps/avant-window-navigator/applets/lastfm"
        self.gconf_client = gconf.client_get_default()
       
        self.inactive_icon = gdk.pixbuf_new_from_file (self.path + "/icons/lastfm_icon.png")
        self.set_temp_icon (self.inactive_icon)
        self.title = awn.awn_title_get_default ()
        
        ## Player Dialog
        self.player_dialog = awn.AppletDialog (self)
                   
        player_label = gtk.Label("Last.fm Player")
        
        player_vbox = gtk.VBox(False, 0)
        player_hbox = gtk.HBox(False, 0)
        
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
        player_hbox.pack_start( ban_button, False, False, 0)    
        
        player_vbox.pack_start(player_label, False, False, 0) 
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
        self.station_type.append_text("Music for Tag")
        self.station_type.append_text("Music for User")
        self.station_type.set_active(0)
        self.station_type.set_property('has-frame', False)
        
        self.station_name = gtk.Entry()      
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
        self.get_config()
        self.lastfm = lastfm()
        self.retval = self.lastfm.connect(self.username, self.password)
        if self.retval == 1:
           window = self.get_preferences_window()
           window.show_all()
        
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

  def get_config(self):
      self.username = self.gconf_client.get_string(self.gconf_path + "/username")
      if self.username == None:
          self.username = ""
         # Empty name surely makes the login fail, which will bring up the preferences
      
      self.password = self.gconf_client.get_string(self.gconf_path + "/password")
      if self.password == None:
          self.password = ""
          # Empty password surely makes the login fail, which will bring up the preferences
  
  def preferences_callback(self, widget):
  		window = self.get_preferences_window()
		window.show_all()

  def get_preferences_window(self):
      window = lastfmconfig.LastFmConfiguration(self)
      window.set_size_request(350, 200)
      window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
      window.set_destroy_with_parent(True)
      # icon_name = self.icons.day_icons["0"]
      # icon = gdk.pixbuf_new_from_file(icon_name)
      # window.set_icon(icon)

      return window

  def on_message(self, bus, message):
      t = message.type
      if t == gst.MESSAGE_TAG:
          self.lastfm.getmetadata()
          #self.set_temp_icon (gdk.pixbuf_new_from_file (self.path + "/icons/play.png"))
          # fetch the cover, if ther is no cover, just take a standart
          imageurl = False
          if self.lastfm.metadata.has_key('albumcover_medium'):
              imageurl = self.lastfm.metadata['albumcover_medium']
          elif self.lastfm.metadata.has_key('albumcover_small'):
              imageurl = self.lastfm.metadata['albumcover_small']
          elif self.lastfm.metadata.has_key('albumcover_big'):
              imageurl = self.lastfm.metadata['albumcover_big']
          
          if imageurl:
              image = urllib.urlopen(self.lastfm.metadata['albumcover_small'])
              temp = image.read()
              image.close()
              f = open('/tmp/lfmapt',"wb")
              f.write(temp)
              f.close()
          else:
              shutil.copy(self.path + "/icons/cd.png", '/tmp/lfmapt')
        
          #resize it and make it eye candy
          os.system("convert /tmp/lfmapt  -thumbnail 98x98 /tmp/lfmapt")
          os.system("convert "+ self.path +"/icons/base.png -geometry  +0+0  -composite /tmp/lfmapt  -geometry  +19+5  -composite "+ self.path +"/icons/top.png  -geometry +0+0  -composite /tmp/lfmapt")
          os.system("convert /tmp/lfmapt -thumbnail x48 /tmp/lfmapt")
          
          
          self.set_temp_icon (gdk.pixbuf_new_from_file('/tmp/lfmapt'))
      elif t == gst.MESSAGE_EOS:
          self.set_temp_icon (self.inactive_icon)
      elif t == gst.MESSAGE_ERROR:
          self.set_temp_icon (self.inactive_icon)
      
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
         #self.set_temp_icon(self.inactive_icon)
         # Don't know why this code doesn't work..
         self.set_temp_icon(gdk.pixbuf_new_from_file (self.path + "/icons/lastfm_icon.png"))
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
      self.station_dialog.hide()
      self.gst_player.set_state(gst.STATE_NULL)
      act = self.station_type.get_active()
      if act == 0:
         station = "lastfm://artist/" + self.station_name.get_text() + "/similarartists"
      elif act == 1:
         station = "lastfm://globaltags/" + self.station_name.get_text()
      elif act == 2:
         station = "lasfm://user/" + self.station_name.get_text() + "/personal"
      print station
      self.lastfm.changestation(station)
      self.gst_player.set_property('uri', self.lastfm.info['stream_url'])
      self.gst_player.set_state(gst.STATE_PLAYING)
      self.playing = True
      self.play_button.set_image(self.stop_button_image)
      
  def enter_notify (self, widget, event):     
      if self.lastfm.metadata.has_key('station') and self.playing == True:
          self.title.show (self, self.lastfm.metadata['station'] + ": " + self.lastfm.metadata['artist'] + " - " + self.lastfm.metadata['track'])
      else:
          self.title.show (self, "LastFM Applet - Click to start listening!")

  def leave_notify (self, widget, event):
      self.title.hide (self)
    
if __name__ == "__main__":
      awn.init (sys.argv[1:])
      #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
      applet = App (awn.uid, awn.orient, awn.height)
      awn.init_applet (applet)
      applet.show_all ()
      gtk.main ()
