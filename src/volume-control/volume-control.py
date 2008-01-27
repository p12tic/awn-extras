"""
--------------------------------------------------------------------------------
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License version 2 as
 published by the Free Software Foundation

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
--------------------------------------------------------------------------------

 The icons of the "Black"-icon-theme are licensed unter a
 Creative Commons Attribution-Share Alike 3.0 License.
--------------------------------------------------------------------------------

Name:        volume-control.py
Version:     0.5.
Date:        September/October 2007
Description: A python Applet for the avant-windows-navigator to control the volume.

Authors:     Richard "nazrat" Beyer
             Jeff "Jawbreaker" Hubbard
"""

#!/usr/bin/python
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn

# Import python module to control the alsamixer and to get gconf keys.
try:
  import alsaaudio
  import gconf
except:
  print "You need to install the alsaaudio-python module and the python-gconf !"
  sys.exit(1)


# Set the mute level at startup.
__tmp_mute_level = 0



class VolumeApp (awn.AppletSimple):

  # Set the main audio device through a gconf-key or the soundcard channels.
  try:
    key = '/desktop/gnome/sound/default_mixer_tracks'
    client = gconf.client_get_default()
    channels = client.get_list(key, gconf.VALUE_STRING)
    control_channel = channels[0]
  except:
    try:
      print "The gconf key is empty."
      control_channel = alsaaudio.mixers()[0]
    except:
      control_channel = 'Master'


  # Set the path to the folder with the icon-theme.
  theme = "Black"
  themepath = os.path.abspath(os.path.dirname(__file__)) + "/Themes/" + theme + "/"


  def __init__ (self, uid, orient, height):
    awn.AppletSimple.__init__ (self, uid, orient, height)
    self.height = height
    self.theme = gtk.icon_theme_get_default()
    self.set_applet_icon ()
    self.title = awn.awn_title_get_default ()

  #
  # Create the left-click pop-up dialog and the buttons/sliders within.
  #  
    self.dialog = awn.AppletDialog (self)
    controls_container = gtk.HBox()
    controls_container.set_spacing(4)
    volume_container = gtk.VBox ()
    volume_container.set_spacing(4)
    
    global volume_slider
    volume_slider = gtk.VScale()
    volume_slider.set_range(0, 100)
    volume_slider.set_digits(0)
    volume_slider.set_inverted(True)
    volume_slider.set_value(alsaaudio.Mixer(self.control_channel).getvolume()[0])
  
    button_volume_up = gtk.Button ()
    button_volume_up.set_relief(gtk.RELIEF_NONE)
    button_volume_up_image = gtk.Image()
    button_volume_up_image.set_from_stock('gtk-go-up', gtk.ICON_SIZE_LARGE_TOOLBAR)
    button_volume_up.set_image(button_volume_up_image)

    button_volume_down = gtk.Button ()
    button_volume_down.set_relief(gtk.RELIEF_NONE)
    button_volume_down_image = gtk.Image()
    button_volume_down_image.set_from_stock('gtk-go-down', gtk.ICON_SIZE_LARGE_TOOLBAR)
    button_volume_down.set_image(button_volume_down_image)
    
    button_volume_mute = gtk.ToggleButton()
    button_volume_mute.set_relief(gtk.RELIEF_NONE)
    button_volume_mute_image = gtk.Image()
    button_volume_mute_image.set_from_stock('gtk-no', gtk.ICON_SIZE_SMALL_TOOLBAR)
    button_volume_mute.set_image(button_volume_mute_image)
    
    button_set = gtk.Button("Config")
    button_set.set_relief(gtk.RELIEF_NONE)
    
    label = gtk.Label("Volume:")

    volume_container.add (label)
    volume_container.add (button_volume_up)
    volume_container.add (button_volume_down)
    volume_container.add (button_volume_mute)
    volume_container.add (button_set)
    controls_container.add (volume_container)
    controls_container.add (volume_slider)
    
    self.dialog.add (controls_container)

  #
  # Create the Settings dialog: 
  #  
    self.settings_dialog = awn.AppletDialog (self)
    settings_container = gtk.VBox ()
    settings_container.set_spacing(4)
    
    # Device-Combo-Box:
    device_label = gtk.Label("Mixer Channel:")
    
    device_liststore = gtk.ListStore(str)
    device_cell = gtk.CellRendererText()
    global device_list
    device_list = gtk.ComboBox (device_liststore)
    device_list.pack_start(device_cell, True)
    device_list.add_attribute(device_cell, 'text', 0)
    for m in alsaaudio.mixers():
      device_liststore.append([m])

    
    # Theme-Combo-Box:
    theme_label = gtk.Label("Theme:")

    theme_liststore = gtk.ListStore(str)
    theme_cell = gtk.CellRendererText()
    global theme_list
    theme_list = gtk.ComboBox (theme_liststore)
    theme_list.pack_start(theme_cell, True)
    theme_list.add_attribute(theme_cell, 'text', 0)
    theme_liststore.append(["Black"])
    theme_liststore.append(["Tango"])
    
    settings_container.add (device_label)
    settings_container.add (device_list)
    settings_container.add (theme_label)
    settings_container.add (theme_list)

    self.settings_dialog.add (settings_container)

  #
  # Connect the events to the buttons, sliders and combo-boxes.
  #  
    self.connect ("button-press-event", self.button_press)
    self.connect ("scroll-event", self.wheel_turn)
    self.connect ("enter-notify-event", self.enter_notify)
    self.connect ("leave-notify-event", self.leave_notify)
    self.dialog.connect ("focus-out-event", self.dialog_focus_out)
    self.settings_dialog.connect ("focus-out-event", self.settings_dialog_focus_out)

    button_volume_up.connect ("button-press-event", self.button_volume_up_press)
    button_volume_down.connect ("button-press-event", self.button_volume_down_press)
    button_volume_mute.connect ("button-press-event", self.button_volume_mute_toggled)
    button_set.connect ("button-press-event", self.button_volume_set_press)
    volume_slider.connect ("value-changed", self.volume_slider_changed)
    volume_slider.connect ("scroll-event", self.wheel_turn)

    device_list.connect ("changed", self.device_list_changed)
    theme_list.connect ("changed", self.theme_list_changed)

#
# Functions for the main applet:
#

  # Set the applet-icon based on the actual volume.
  def set_applet_icon (self):
    currentvolume = alsaaudio.Mixer(self.control_channel).getvolume()[0]
    if currentvolume > 60 :
      icon = gdk.pixbuf_new_from_file (self.themepath + "audio-volume-high.svg")
    elif currentvolume > 25 :
      icon = gdk.pixbuf_new_from_file (self.themepath + "audio-volume-medium.svg")
    elif currentvolume > 0 :
      icon = gdk.pixbuf_new_from_file (self.themepath + "audio-volume-low.svg")
    else:
      icon = gdk.pixbuf_new_from_file (self.themepath + "audio-volume-muted.svg")  
    if self.height != icon.get_height():
      icon = icon.scale_simple(self.height,self.height,gtk.gdk.INTERP_BILINEAR)
    #self.set_temp_icon(icon)
    self.set_icon(icon)
   

  # When the applet is left-clicked the pop-up dialog appears, when middle-clicked 
  # the volume is muted, and when right-clicked the mixer-control appears.
  def button_press (self, widget, event):
    if event.button == 1:
        #print "leftmouse clicked -> open controls"
        self.dialog.show_all ()
    if event.button == 2:
        #print "middlemouse clicked -> mute/unmute"
        self.volume_mute_toggle()
    if event.button == 3:
        #print "rightmouse clicked -> run gnome-volume-control"
        os.popen("gnome-volume-control &")
        #self.player_dialog()
    self.title.hide (self)


  # Turning the mouse wheel up/down should increase/decrease the volume.
  def wheel_turn (self, widget, event):
    if event.direction == gtk.gdk.SCROLL_UP:
      self.volume_up()
    elif event.direction == gtk.gdk.SCROLL_DOWN:
      self.volume_down()
    volumestring = "Volume: " + str(alsaaudio.Mixer(self.control_channel).getvolume()[0]) + "%"
    self.title.show (self, volumestring)


  # When "mouse over applet" the current volume is shown.
  def enter_notify (self, widget, event):
    volumestring = "Volume: " + str(alsaaudio.Mixer(self.control_channel).getvolume()[0]) + "%"
    self.title.show (self, volumestring)
    self.set_applet_icon ()
    
  # When the mouse leaves the applet the title disappears.
  def leave_notify (self, widget, event):
    self.title.hide (self)
  
  # When the mouse leaves the dialogs they disappear.
  def dialog_focus_out (self, widget, event):
    self.dialog.hide ()
  def settings_dialog_focus_out (self, widget, event): 
    self.settings_dialog.hide ()

#
# Functions for the control dialog:
#
 
  # Moving the slider up and down changes the volume.
  def volume_slider_changed (self, widget):
    volume = int(volume_slider.get_value())
    alsaaudio.Mixer(self.control_channel).setvolume(volume)
    self.set_applet_icon ()

  # Clicking the volume-control-buttons should increase/decrease/mute the volume.
  def button_volume_up_press (self, widget, event):
    self.volume_up()

  def button_volume_down_press (self, widget, event):
    self.volume_down()

  def button_volume_mute_toggled (self, widget, event):
    self.volume_mute_toggle()
    
  def button_volume_set_press (self, widget, event):
    self.settings_dialog.show_all ()

#
# Functions for the settings dialog.    
#  

  # Changing the audio device. 
  def device_list_changed (self, widget):
    self.control_channel = alsaaudio.mixers()[device_list.get_active()]
    print "device changed to " + self.control_channel
  
  # Changing the icon theme.    
  def theme_list_changed (self, widget):
    if theme_list.get_active() == 1 :
      self.theme = "Tango"
    else :
      self.theme = "Black"
    self.themepath = os.path.abspath(os.path.dirname(__file__)) + "/Themes/" + self.theme + "/"
    print "theme changed to " + self.theme



#
# Functions to increase/decrease/mute the volume.
#

  def volume_up(self):
    volume = alsaaudio.Mixer(self.control_channel).getvolume()[0]
    # if the volume is under 97, increase the volume one step.
    if volume < 97:
      alsaaudio.Mixer(self.control_channel).setvolume(volume+4)
      volume_slider.set_value(volume+4)
    # if the volume is over 97, set it to 100.
    else:
      alsaaudio.Mixer(self.control_channel).setvolume(100)
      volume_slider.set_value(100)
    self.set_applet_icon()

  def volume_down(self):
    volume = alsaaudio.Mixer(self.control_channel).getvolume()[0]
    # if the volume is over 3, decrease it's value one step.
    if volume > 3:
      alsaaudio.Mixer(self.control_channel).setvolume(volume-4)
      volume_slider.set_value(volume-4)
    # if the volume is under 3, set it to 0.
    elif volume > 0:
      alsaaudio.Mixer(self.control_channel).setvolume(0)
      volume_slider.set_value(0)
    self.set_applet_icon()

  def volume_mute_toggle(self):
    volume = alsaaudio.Mixer(self.control_channel).getvolume()[0]
    if volume > 0:
      self.__tmp_mute_level = volume
      alsaaudio.Mixer(self.control_channel).setvolume(0)
      #alsa.Mixer(control_channel).setmute(1)
    else:
      alsaaudio.Mixer(self.control_channel).setvolume(self.__tmp_mute_level)
      #alsa.Mixer(control_channel).setmute(0)
    self.set_applet_icon()
    
  

#
# Main loop
#
if __name__ == "__main__":
  awn.init (sys.argv[1:])
  #print "%s %d %d" % (awn.uid, awn.orient, awn.height)
  applet = VolumeApp (awn.uid, awn.orient, awn.height)
  awn.init_applet (applet)
  applet.show_all ()
  gtk.main ()
  