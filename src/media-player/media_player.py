# !/usr/bin/python

# Copyright (c) 2007 Michal Hruby <michal.mhr at gmail.com>
# Thanks for inspiration from media-control appplet by im-tehk.
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

import pygst
pygst.require("0.10")
import gst
import pygtk
import gtk
import gconf
import sys

import awn

class App(awn.AppletSimple):
    """Displays a dialog with controls and track/album info and art"""

    APPLET_NAME = "Media Player Applet"
    def __init__(self, uid, orient, height):
        """Creating the applets core"""
        awn.AppletSimple.__init__(self, uid, orient, height)
        self.toolTip = App.APPLET_NAME
        self.keylocation = "/apps/avant-window-navigator/applets/media-player/"
        self.set_awn_icon('media-player', 'media-player')
        self.load_keys()

        # some initialization stuff
        self.isVideo = False
        self.height = height
        self.title = awn.awn_title_get_default()
        self.dialog = awn.AppletDialog(self)
        self.dialog_visible = False
        self.popup_menu = self.create_default_menu()

        # gstreamer stuff
        self.viSink = gst.element_factory_make(self.videosink, "viSink")
        self.auSink = gst.element_factory_make(self.audiosink, "auSink")
        # Set up our playbin
        self.playbin = gst.element_factory_make("playbin", "pbin")
        self.playbin.set_property("video-sink", self.viSink)
        self.playbin.set_property("audio-sink", self.auSink)

        bus = self.playbin.get_bus()
        bus.enable_sync_message_emission()
        bus.add_watch(self.OnGstMessage)
        bus.connect("sync-message::element", self.OnGstSyncMessage)

        # Defining Widgets
        self.vbox = gtk.VBox()
        self.da = gtk.DrawingArea()
        self.da.set_size_request(self.videoW, self.videoH)
        self.vbox.pack_start(self.da)
        # Buttons
        self.button_play = gtk.Button(stock='gtk-media-play')
        self.button_stop = gtk.Button(stock='gtk-media-stop')
        self.button_play.connect("clicked", self.button_play_pause_cb)
        self.button_stop.connect("clicked", self.button_stop_cb)
        # Packing Widgets
        hbox = gtk.HBox()
        hbox.pack_start(self.button_play)
        hbox.add(self.button_stop)
        self.vbox.add(hbox)
        self.dialog.add(self.vbox)
        # Video can't be played into RGBA widget
        rgbColormap = self.vbox.get_screen().get_rgb_colormap()
        self.da.set_colormap(rgbColormap)
        self.da.realize()

        # Standard AWN Connects
        self.connect("button-press-event", self.button_press)
        self.connect("enter-notify-event", self.enter_notify)
        self.connect("leave-notify-event", self.leave_notify)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)
        # Drag&drop support
        self.connect("drag-data-received", self.applet_drop_cb)
        self.connect("drag-motion", self.applet_drag_motion_cb)
        self.connect("drag-leave", self.applet_drag_leave_cb)

        self.drag_dest_set(gtk.DEST_DEFAULT_ALL,
                           [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                           gtk.gdk.ACTION_COPY)

    def showApplet(self):
        self.dialog.stick()
        self.dialog.set_keep_above(True)
        self.dialog_visible = True
        self.dialog.show_all()
        self.da.set_property("visible", self.isVideo)

    def hideApplet(self):
        self.dialog_visible = False
        self.dialog.hide()

    def OnGstMessage(self, bus, message, data = None):
        if message.type in [gst.MESSAGE_EOS, gst.MESSAGE_ERROR]:
            self.playbin.set_state(gst.STATE_NULL)
            self.button_play.set_label('gtk-media-play')
            if self.dialog_visible:
                self.hideApplet()
        elif message.type is gst.MESSAGE_NEW_CLOCK:
            if self.isVideo and self.dialog_visible == False:
                self.showApplet()
            elif self.isVideo:
                self.da.set_property("visible", self.isVideo)
        #elif message.type in [gst.MESSAGE_STATE_CHANGED]:
        #    oldstate, newstate, pending = message.parse_state_changed()
        #    print "state change %s -> %s" % (str(oldstate), str(newstate))
        #elif message.type in [gst.MESSAGE_TAG]:
        #    taglist = message.parse_tag()
        #    if not self.isVideo:
        #        self.isVideo = "video-codec" in taglist

        return True

    def OnGstSyncMessage(self, bus, message, data = None):
        # careful here it's different thread
        if message.structure is None: return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            self.isVideo = True
            videosink = message.src
            videosink.set_property("force-aspect-ratio", True)
            videosink.set_xwindow_id(self.da.window.xid)
        return True

    def button_press(self, widget, event):
        if event.button == 1:
            if self.dialog_visible:
                self.hideApplet()
            else:
                self.title.hide(self)
                self.showApplet()
        elif event.button == 2:
            self.button_play_pause_cb(widget)
        elif event.button == 3:
            self.popup_menu.popup(None, None, None, event.button, event.time)

    def enter_notify(self, widget, event):
        self.title.show(self, self.toolTip)

    def leave_notify(self, widget, event):
        self.title.hide(self)

    def dialog_focus_out(self, widget, event):
        if not self.isVideo:
            self.hideApplet()

    def key_control(self, keyname, default):
        """
        This Method takes the keyname and the defualt
        value and either loads an existing key -or-
        loads and saves the defualt key if no key is defined
        """
        keylocation_with_name = self.keylocation + keyname
        result = None
        try:
            if default.__class__ is int:
                val = self.client.get_without_default(keylocation_with_name)
                if val == None:
                    result = None
                else:
                    result = val.get_int()
            else:
                result = self.client.get_string(keylocation_with_name)

            if result == None and default != None:
                result = default
                if default.__class__ is int:
                    self.client.set_int(keylocation_with_name, result)
                else:
                    self.client.set_string(keylocation_with_name, result)
        except NameError:
            result = default
        return result

    def load_keys(self):
        """
        Loads all the gconf variables by calling the key_control method
        """
        self.client = gconf.client_get_default()
        self.audiosink = self.key_control("audiosink", "default")
        self.videosink = self.key_control("videosink", "default")
        self.videoW = self.key_control("videoWidth", 200)
        self.videoH = self.key_control("videoHeight", 150)

        if self.videosink == "default":
          self.videosink = self.client.get_string("/system/gstreamer/0.10/default/videosink")
        if self.audiosink == "default":
          self.audiosink = self.client.get_string("/system/gstreamer/0.10/default/audiosink")

    def play_pause(self):
        oldstate, currentstate, pending = self.playbin.get_state()
        if currentstate != gst.STATE_PLAYING:
            self.playbin.set_state(gst.STATE_PLAYING)
            self.button_play.set_label('gtk-media-pause')
        else:
            self.playbin.set_state(gst.STATE_PAUSED)
            self.button_play.set_label('gtk-media-play')

    def stop(self):
        self.playbin.set_state(gst.STATE_NULL)
        self.button_play.set_label('gtk-media-play')
        self.isVideo = False
        if self.dialog_visible:
            self.hideApplet()

    def applet_drag_motion_cb(self, widget, context, x, y, time):
        awn.awn_effect_start(self.get_effects(), "launching")
        return True

    def applet_drag_leave_cb(self, widget, context, time):
        awn.awn_effect_stop(self.get_effects(), "launching")
        return True

    def applet_drop_cb(self, wdgt, context, x, y, selection, targetType, time):
        uri2play = selection.data
        if len(uri2play.split()) > 1:
            # just take the first one
            uri2play = uri2play.split()[0]
        # I wonder why there are zeroes sometimes?
        uri2play = uri2play.strip('\000').strip()

        self.stop()
        self.playbin.set_property("uri", uri2play)
        self.play_pause()

        context.finish(True, False, time)
        return True

    def button_play_pause_cb(self, widget):
        self.play_pause()

    def button_stop_cb(self, widget):
        self.stop()


if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
