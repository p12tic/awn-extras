"""
A python Applet for the avant-windows-navigator
to control the volume and the audio player.

Version 0.1.

Richard Beyer September 2007
"""

#!/usr/bin/python
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
try:
    import alsaaudio as alsa
except:
    print "you need to install the alsaaudio-python module !"
    sys.exit(1)
try:
    import commands
except:
    print "you need to install the alsaaudio-python module !"
    sys.exit(1)    
    


class VolumeApp (awn.AppletSimple):
  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    self.height = height
    self.theme = gtk.IconTheme ()
    self.set_applet_icon ()
    self.title = awn.awn_title_get_default ()

    
    #Create the pop-up dialog and the buttons within.
    self.dialog = awn.AppletDialog (self)
    dialogcontainer = gtk.VBox()
    controls_container = gtk.HBox ()
    volume_container = gtk.HBox ()

    button_play = gtk.Button ()
    button_play.set_relief(gtk.RELIEF_NONE)
    button_play_image = gtk.Image()
    button_play_image.set_from_file("/usr/share/icons/Tango/24x24/actions/gtk-media-play-ltr.png")
    button_play.set_image(button_play_image)
    
    button_previous = gtk.Button ()
    button_previous.set_relief(gtk.RELIEF_NONE)
    button_previous_image = gtk.Image()
    button_previous_image.set_from_file("/usr/share/icons/Tango/24x24/actions/gtk-media-previous-ltr.png")
    button_previous.set_image(button_previous_image)

    button_next = gtk.Button ()
    button_next.set_relief(gtk.RELIEF_NONE)
    button_next_image = gtk.Image()
    button_next_image.set_from_file("/usr/share/icons/Tango/24x24/actions/gtk-media-next-ltr.png")
    button_next.set_image(button_next_image)

    button_volume_up = gtk.Button ()
    button_volume_up.set_relief(gtk.RELIEF_NONE)
    button_volume_up_image = gtk.Image()
    button_volume_up_image.set_from_file("/usr/share/icons/Tango/24x24/actions/add.png")
    button_volume_up.set_image(button_volume_up_image)

    button_volume_down = gtk.Button ()
    button_volume_down.set_relief(gtk.RELIEF_NONE)
    button_volume_down_image = gtk.Image()
    button_volume_down_image.set_from_file("/usr/share/icons/Tango/24x24/actions/remove.png")
    button_volume_down.set_image(button_volume_down_image)
    
    knob_image = gtk.Image()
    knob_image.set_from_file("/usr/share/icons/gnome/48x48/apps/gnome-settings-sound.png")

    #Arrange the buttons.
    volume_container.add (knob_image)
    volume_container.add (button_volume_up)
    volume_container.add (button_volume_down)
    controls_container.add (button_previous)
    controls_container.add (button_play)
    controls_container.add (button_next)
    dialogcontainer.add (volume_container)
    dialogcontainer.add (controls_container)

    self.dialog.add (dialogcontainer)
    #controls_container.show_all ()

    #Connect the events for the buttons.
    self.connect ("button-press-event", self.button_press)
    self.connect("scroll-event", self.wheel_turn)
    self.connect ("enter-notify-event", self.enter_notify)
    self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)
    button_previous.connect ("button-press-event", self.button_previous_press)
    button_play.connect ("button-press-event", self.button_play_press)
    button_next.connect ("button-press-event", self.button_next_press)
    button_volume_up.connect ("button-press-event", self.button_volume_up_press)
    button_volume_down.connect ("button-press-event", self.button_volume_down_press)


  #Set the applet-icon based on the actual volume.
  def set_applet_icon (self):
    currentvolume = alsa.Mixer('PCM').getvolume()[0]
    if currentvolume > 60 :
      icon = gdk.pixbuf_new_from_file ("/usr/share/icons/Tango/scalable/status/audio-volume-high.svg")
    elif currentvolume > 25 :
      icon = gdk.pixbuf_new_from_file ("/usr/share/icons/Tango/scalable/status/audio-volume-medium.svg")
    elif currentvolume > 0 :
      icon = gdk.pixbuf_new_from_file ("/usr/share/icons/Tango/scalable/status/audio-volume-low.svg")
    else:
      icon = gdk.pixbuf_new_from_file ("/usr/share/icons/Tango/scalable/status/audio-volume-muted.svg")  
    self.set_temp_icon (icon)
    
 
  #When the mouse leaves the dialog it disappears.
  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
    #print "hide pop-up dialog"


  #When applet is left-clicked the pop-up dialog appears, when middle-clicked the audio player 
  #should pause/continue play, and when right-clicked the mixer-control should appear.
  def button_press (self, widget, event):
    if event.button == 1:
        print "leftmouse clicked -> open controls"
    if event.button == 2:
        print "middlemouse clicked (not yet implemented!)"
    if event.button == 3:
        print "rightmouse clicked -> run gnome-volume-control"
        commands.getstatusoutput("gnome-volume-control")
    self.dialog.show_all ()
    self.title.hide (self)


  #Turning the mouse wheel up/down should increase/decrease the volume.
  def wheel_turn (self, widget, event):
    if event.direction == gtk.gdk.SCROLL_UP:
      #print "wheel up"
      self.volume_up()
    elif event.direction == gtk.gdk.SCROLL_DOWN:
      #print "wheel down" 
      self.volume_down()
    volumestring = "Volume: " + str(alsa.Mixer('PCM').getvolume()[0]) + "%"
    self.title.show (self, volumestring)


  #When "mouse over applet" the current volume should appear.
  def enter_notify (self, widget, event):
    volumestring = "Volume: " + str(alsa.Mixer('PCM').getvolume()[0]) + "%"
    self.title.show (self, volumestring)
    #self.set_temp_icon (icon)


  #When the mouse leaves the applet title disappears.
  def leave_notify (self, widget, event):
    self.title.hide (self)
    #print "hide title"

  #Clicking the audio-control-buttons should control the prefered music player application,
  #preferably through DBus.  
  def button_previous_press (self, widget, event):
    print "button_previous clicked!!! (not yet implemented!)"

  def button_play_press (self, widget, event):
    print "button_play clicked!!! (not yet implemented!)"

  def button_next_press (self, widget, event):
    print "button_next clicked!!! (not yet implemented!)"


  #Clicking the volume-control-buttons should increase/decrease the volume.
  def button_volume_up_press (self, widget, event):
    #print "button_volume_up clicked."
    self.volume_up()

  def button_volume_down_press (self, widget, event):
    #print "button_volume_down clicked."
    self.volume_down()


  #The methods to increase/decrease the volume.
  def volume_up(self):
    volume = alsa.Mixer('PCM').getvolume()[0]
    # if the volume is under 97, increase the volume for one step.
    if volume < 97:
      alsa.Mixer('PCM').setvolume(volume+4)
    # if the volume is over 97, set it to 100.
    else:
      alsa.Mixer('PCM').setvolume(100)
    self.set_applet_icon ()  

  def volume_down(self):
    volume = alsa.Mixer('PCM').getvolume()[0]
    # if the volume is over 3, decrease it's value for one step.
    if volume > 3:
      alsa.Mixer('PCM').setvolume(volume-4)
    # if the volume is under 3, set it to 0 and mute it.
    elif volume > 0:
      alsa.Mixer('PCM').setvolume(0)
    self.set_applet_icon ()  


#Main loop
if __name__ == "__main__":
  awn.init (sys.argv[1:])
  #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
  applet = VolumeApp (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
