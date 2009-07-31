#!/usr/bin/python

# Copyright (c) 2009 Michal Hruby <michal.mhr AT gmail.com>
#
# This is the configuration dialog for shiny-switcher applet for AWN.
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

import awn
import gtk
import gtk.glade
import os

class Preferences:
  def __init__(self):
    self.client = awn.Config("shinyswitcher", None)
    glade_path = os.path.join(os.path.dirname(__file__),
                              "shiny-prefs.glade")
    wTree = gtk.glade.XML(glade_path)

    self.init_controls(wTree)

    wTree.signal_autoconnect(self)

    self.window = wTree.get_widget("dialog1")
    self.window.set_icon_name("gnome-panel-workspace-switcher")
    self.window.connect("destroy", gtk.main_quit)
    self.window.show_all()

  def init_controls(self, wTree):
    # "Look" widgets
    self.appletSizeScale = wTree.get_widget("appletSizeScale")
    self.appletSizeScale.set_value(int(self.client.get_float(
      awn.CONFIG_DEFAULT_GROUP, "applet_scale")*100))

    self.grabWallpaperRadio = wTree.get_widget("grabWallpaperRadio")
    self.nograbWallPaperRadio = wTree.get_widget("customBackgroundRadio")
    if (self.client.get_bool(awn.CONFIG_DEFAULT_GROUP, "grab_wallpaper")):
      self.grabWallpaperRadio.set_active(True)
    else:
      self.nograbWallPaperRadio.set_active(True)

    self.borderSizeSpin = wTree.get_widget("borderSizeSpin")
    self.borderSizeSpin.set_value(self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "applet_border_width"))

    self.backgroundColor = wTree.get_widget("backgroundColor")
    self.stringToColorButton(self.backgroundColor, self.client.get_string(
      awn.CONFIG_DEFAULT_GROUP, "desktop_colour"))

    self.borderColor = wTree.get_widget("borderColor")
    self.stringToColorButton(self.borderColor, self.client.get_string(
      awn.CONFIG_DEFAULT_GROUP, "applet_border_colour"))

    self.activeIconAlphaScale = wTree.get_widget("activeIconAlphaScale")
    self.activeIconAlphaScale.set_value(int(self.client.get_float(
      awn.CONFIG_DEFAULT_GROUP, "win_active_icon_alpha")*100))
    
    self.inactiveIconAlphaScale = wTree.get_widget("inactiveIconAlphaScale")
    self.inactiveIconAlphaScale.set_value(int(self.client.get_float(
      awn.CONFIG_DEFAULT_GROUP, "win_inactive_icon_alpha")*100))

    self.activeWsAlphaScale = wTree.get_widget("activeWsAlphaScale")
    self.activeWsAlphaScale.set_value(int(self.client.get_float(
      awn.CONFIG_DEFAULT_GROUP, "background_alpha_active")*100))

    self.inactiveWsAlphaScale = wTree.get_widget("inactiveWsAlphaScale")
    self.inactiveWsAlphaScale.set_value(int(self.client.get_float(
      awn.CONFIG_DEFAULT_GROUP, "background_alpha_inactive")*100))

    # "Behavior" widgets
    
    self.rowsSpin = wTree.get_widget("rowsSpin")
    self.rowsSpin.set_value(self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "rows"))

    self.columnsSpin = wTree.get_widget("columnsSpin")
    self.columnsSpin.set_value(self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "columns"))

    self.winThumb = []
    self.winThumb.append(wTree.get_widget("thumbRadio0"))
    self.winThumb.append(wTree.get_widget("thumbRadio1"))
    self.winThumb.append(wTree.get_widget("thumbRadio2"))
    self.winThumb.append(wTree.get_widget("thumbRadio3"))
    self.winThumb[self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "win_grab_mode")].set_active(True)

    i = 0
    for widget in self.winThumb:
      widget.connect("toggled", self.update_int, ("win_grab_mode", i))
      i = i+1

    self.iconDisplay = []
    self.iconDisplay.append(wTree.get_widget("showRadio0"))
    self.iconDisplay.append(wTree.get_widget("showRadio1"))
    self.iconDisplay.append(wTree.get_widget("showRadio2"))
    self.iconDisplay.append(wTree.get_widget("showRadio3"))
    self.iconDisplay[self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "show_icon_mode")].set_active(True)

    i = 0
    for widget in self.iconDisplay:
      widget.connect("toggled", self.update_int, ("show_icon_mode", i))
      i = i+1

    self.iconScale = []
    self.iconScale.append(wTree.get_widget("scaleRadio0"))
    self.iconScale.append(wTree.get_widget("scaleRadio1"))
    self.iconScale.append(wTree.get_widget("scaleRadio2"))
    self.iconScale.append(wTree.get_widget("scaleRadio3"))
    self.iconScale[self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "scale_icon_mode")].set_active(True)

    i = 0
    for widget in self.iconScale:
      widget.connect("toggled", self.update_int, ("scale_icon_mode", i))
      i = i+1

    self.iconScaleScale = wTree.get_widget("iconScaleScale")
    self.iconScaleScale.set_value(int(self.client.get_float(
      awn.CONFIG_DEFAULT_GROUP, "scale_icon_factor")*100))

    self.iconPosCombobox = wTree.get_widget("iconPosCombobox")
    self.iconPosCombobox.set_active(self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "scale_icon_position"))

    self.cacheSpin = wTree.get_widget("cacheSpin")
    self.cacheSpin.set_value(self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "cache_expiry"))

    self.renderSpin = wTree.get_widget("renderSpin")
    self.renderSpin.set_value(self.client.get_int(
      awn.CONFIG_DEFAULT_GROUP, "queued_render_timer") / 1000)

  def update_int(self, widget, tuple):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, tuple[0], tuple[1])

  def stringToColorButton(self, widget, string):
    if string == None or len(string) != 9: return
    color = string[:7]
    widget.set_color(gtk.gdk.color_parse(color))
    widget.set_alpha(int(string[7:], 16) * 256)

  def colorButtonToString(self, widget):
    c = widget.get_color()
    return '#' +  ''.join(['%02X' % int(x / 256)
                           for x in [c.red, c.green, c.blue, widget.get_alpha()]])

  # callbacks from the glade file
  def appletSizeScale_value_changed_cb(self, widget):
    self.client.set_float(awn.CONFIG_DEFAULT_GROUP, "applet_scale",
      widget.get_value() / 100.0)

  def grabWallpaperRadio_toggled_cb(self, widget):
    self.client.set_bool(awn.CONFIG_DEFAULT_GROUP, "grab_wallpaper", True)

  def customBackgroundRadio_toggled_cb(self, widget):
    self.client.set_bool(awn.CONFIG_DEFAULT_GROUP, "grab_wallpaper", False)

  def backgroundColor_color_set_cb(self, widget):
    self.client.set_string(awn.CONFIG_DEFAULT_GROUP, "desktop_colour",
      self.colorButtonToString(widget))

  def borderColor_color_set_cb(self, widget):
    self.client.set_string(awn.CONFIG_DEFAULT_GROUP, "applet_border_colour",
       self.colorButtonToString(widget))

  def borderSizeSpin_value_changed_cb(self, widget):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, "applet_border_width",
      widget.get_value())

  def activeIconAlphaScale_value_changed_cb(self, widget):
    self.client.set_float(awn.CONFIG_DEFAULT_GROUP, "win_active_icon_alpha",
      widget.get_value() / 100.0)

  def inactiveIconAlphaScale_value_changed_cb(self, widget):
    self.client.set_float(awn.CONFIG_DEFAULT_GROUP, "win_inactive_icon_alpha",
      widget.get_value() / 100.0)

  def activeWsAlphaScale_value_changed_cb(self, widget):
    self.client.set_float(awn.CONFIG_DEFAULT_GROUP, "background_alpha_active",
      widget.get_value() / 100.0)

  def inactiveWsAlphaScale_value_changed_cb(self, widget):
    self.client.set_float(awn.CONFIG_DEFAULT_GROUP, "background_alpha_inactive",
      widget.get_value() / 100.0)

  def rowsSpin_value_changed_cb(self, widget):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, "rows", widget.get_value())

  def columnsSpin_value_changed_cb(self, widget):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, "columns", widget.get_value())

  def iconScaleScale_value_changed_cb(self, widget):
    self.client.set_float(awn.CONFIG_DEFAULT_GROUP, "scale_icon_factor",
      widget.get_value() / 100.0)

  def iconPosCombobox_changed_cb(self, widget):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, "scale_icon_position",
      widget.get_active())

  def cacheSpin_value_changed_cb(self, widget):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, "cache_expiry",
      widget.get_value())

  def renderSpin_value_changed_cb(self, widget):
    self.client.set_int(awn.CONFIG_DEFAULT_GROUP, "queued_render_timer",
      widget.get_value()*1000)


  def closeButton_clicked_cb(self, widget):
    gtk.main_quit()

if __name__ == "__main__":
  pref_dialog = Preferences()
  gtk.main()
