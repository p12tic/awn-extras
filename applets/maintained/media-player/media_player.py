#!/usr/bin/python
# Copyright (c)  2008 - 2009 Michal Hruby <michal.mhr at gmail.com>
# Thanks for inspiration from media-control appplet by im-tehk.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import pygst
pygst.require("0.10")
import gst
import gtk
import gobject

import awn
from desktopagnostic import config


class MediaPlayerApplet(awn.AppletSimple):
    """Displays a dialog with controls and track/album info and art"""

    audio_sink = gobject.property(type=str, nick='Audio Sink',
                                  blurb='Name of audio sink to use',
                                  default='autoaudiosink')
    video_sink = gobject.property(type=str, nick='Video Sink',
                                  blurb='Name of video sink to use',
                                  default='autovideosink')
    video_width = gobject.property(type=int, nick='Video Width',
                                   blurb='Width of the video window',
                                   default=240)
    video_height = gobject.property(type=int, nick='Video Height',
                                    blurb='Height of the video window',
                                    default=120)
    # PyGObject doesn't have BOXED support implemented
    # recent_items = gobject.property(type=gobject.TYPE_BOXED,
    #                                 nick='Recent Items')

    APPLET_NAME = "Media Player Applet"

    def __init__(self, uid, panel_id):
        """Creating the applets core"""
        awn.AppletSimple.__init__(self, "media-player", uid, panel_id)
        self.set_tooltip_text(MediaPlayerApplet.APPLET_NAME)
        self.set_icon_name('media-player')
        self.bind_keys()

        # some initialization stuff
        self.isVideo = False
        self.size = self.get_size()
        self.full_window = None
        self.dialog = awn.Dialog(self)
        self.play_icon = awn.OverlayThemedIcon(self.get_icon(),
                                               "media-playback-start", None)
        self.play_icon.props.scale = 0.4
        self.play_icon.props.active = False
        self.play_icon.props.gravity = gtk.gdk.GRAVITY_SOUTH_EAST
        self.add_overlay(self.play_icon)

        # Recent items menu
        self.recent_items_menu = gtk.Menu()
        for item in self.recentItems:
            menu_item = gtk.MenuItem(item)
            menu_item.connect("activate", self.playItem)
            self.recent_items_menu.append(menu_item)
        self.recent_items_menu.show_all()
        # Popup menu
        self.recent = gtk.MenuItem("Recent items")
        self.recent.set_submenu(self.recent_items_menu)
        self.prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.prefs.connect("activate", self.show_prefs)
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect("activate", self.show_about)

        self.popup_menu = self.create_default_menu()
        self.popup_menu.append(self.recent)
        self.popup_menu.append(self.prefs)

        item = gtk.SeparatorMenuItem()
        item.show()
        self.popup_menu.append(item)

        self.popup_menu.append(self.about)
        self.popup_menu.show_all()

        # gstreamer stuff
        self.viSink = gst.element_factory_make(self.video_sink, "viSink")
        self.auSink = gst.element_factory_make(self.audio_sink, "auSink")
        # Set up our playbin
        self.playbin = gst.element_factory_make("playbin", "pbin")
        self.playbin.set_property("video-sink", self.viSink)
        self.playbin.set_property("audio-sink", self.auSink)

        bus = self.playbin.get_bus()
        bus.enable_sync_message_emission()
        bus.add_watch(self.OnGstMessage)
        bus.connect("sync-message::element", self.OnGstSyncMessage)

        # Defining Widgets
        self.vbox = gtk.VBox(spacing=6)
        self.da = gtk.DrawingArea()
        self.da.set_size_request(self.video_width, self.video_height)
        self.da.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000"))
        self.da.set_events(gtk.gdk.ALL_EVENTS_MASK)
        self.mouse_handler_id = self.da.connect("button-press-event", self.video_clicked)
        self.vbox.pack_start(self.da)
        # Buttons
        self.button_play = gtk.Button(stock='gtk-media-play')
        self.button_stop = gtk.Button(stock='gtk-media-stop')
        self.button_play.connect("clicked", self.button_play_pause_cb)
        self.button_stop.connect("clicked", self.button_stop_cb)
        # Packing Widgets
        self.hbbox = gtk.HButtonBox()
        self.hbbox.set_spacing(2)
        self.hbbox.pack_start(self.button_play)
        self.hbbox.pack_start(self.button_stop)
        self.vbox.add(self.hbbox)
        self.dialog.add(self.vbox)
        # Video can't be played into RGBA widget
        rgbColormap = self.vbox.get_screen().get_rgb_colormap()
        self.da.set_colormap(rgbColormap)
        self.da.realize()

        # Standard AWN Connects
        self.connect("clicked", self.icon_clicked)
        self.connect("context-menu-popup", self.menu_popup)
        self.connect("button-press-event", self.button_press)
        self.dialog.props.hide_on_unfocus = True
        # Drag&drop support
        self.get_icon().drag_dest_set(
                               gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION,
                               [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                               gtk.gdk.ACTION_COPY)

        self.get_icon().connect("drag-data-received", self.applet_drop_cb)
        self.get_icon().connect("drag-motion", self.applet_drag_motion_cb)
        self.get_icon().connect("drag-leave", self.applet_drag_leave_cb)

    def playItem(self, widget):
        label = widget.get_child().get_label()
        self.stop()
        self.playbin.set_property("uri", label)
        self.play_pause()

    def updateRecent(self, uri):
        if self.recentItems.count(uri) > 0:
            return

        if len(self.recentItems) < 5:
            self.recentItems.insert(0, uri)
        else:
            self.recentItems.pop()
            self.recentItems.insert(0, uri)

        menu_items = self.recent_items_menu.get_children()
        for item in menu_items:
            self.recent_items_menu.remove(item)
        for item in self.recentItems:
            menu_item = gtk.MenuItem(item)
            menu_item.connect("activate", self.playItem)
            self.recent_items_menu.append(menu_item)
        self.recent_items_menu.show_all()
        self.recent.set_submenu(self.recent_items_menu)

        self.client.set_list(config.GROUP_DEFAULT, "recent_items", self.recentItems)

    def keyPressed(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            if self.full_window is not None:
                self.toggleFullscreen()
            return True
        elif event.keyval == gtk.keysyms.space:
            self.play_pause()
            return True

        return False

    def fullscreenHide(self, widget):
        if self.da.handler_is_connected(self.mouse_handler_id):
            self.da.handler_disconnect(self.mouse_handler_id)
        self.da.reparent(self.vbox)
        self.vbox.reorder_child(self.da, 0)
        self.mouse_handler_id = self.da.connect("button-press-event", self.video_clicked)

    def fullscreenDestroy(self, widget):
        self.full_window = None
        return False

    def toggleFullscreen(self):
        if self.full_window is None:
            self.full_window = gtk.Window()
            self.full_window.connect("destroy", self.fullscreenDestroy)
            self.full_window.connect("hide", self.fullscreenHide)
            self.full_window.connect("key-press-event", self.keyPressed)
            self.full_window.realize()
            if self.da.handler_is_connected(self.mouse_handler_id):
                self.da.handler_disconnect(self.mouse_handler_id)
            self.da.reparent(self.full_window)
            self.mouse_handler_id = self.da.connect("button-press-event", self.video_clicked)
            self.set_flags(gtk.CAN_FOCUS)
            self.full_window.show()
            self.full_window.fullscreen()
            self.full_window.present()
            self.hideApplet()
        else:
            self.full_window.destroy()
            self.showApplet()

    def video_clicked(self, widget, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            self.toggleFullscreen()

    def dialogVisible(self):
        return (self.dialog.flags() & gtk.VISIBLE) != 0

    def showApplet(self):
        self.dialog.stick()
        self.dialog.set_keep_above(True)
        self.dialog.show_all()
        self.da.set_property("visible", self.isVideo)

    def hideApplet(self):
        self.dialog.hide()

    def windowPrepared(self):
        self.isVideo = True
        self.dialog.props.hide_on_unfocus = False
        if not self.dialogVisible():
            self.showApplet()
        else:
            self.da.set_property("visible", self.isVideo)

    def OnGstMessage(self, bus, message, data = None):
        if message.type in [gst.MESSAGE_EOS, gst.MESSAGE_ERROR]:
            self.playbin.set_state(gst.STATE_NULL)
            self.button_play.set_label('gtk-media-play')
            self.play_icon.props.active = False
            if self.full_window:
                self.full_window.destroy()
            if self.dialogVisible():
                self.hideApplet()
        #elif message.type is gst.MESSAGE_NEW_CLOCK:
        #    pass
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
        if message.structure is None:
            return

        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            self.isVideo = True
            videosink = message.src
            videosink.set_property("force-aspect-ratio", True)
            videosink.set_xwindow_id(self.da.window.xid)
            gobject.timeout_add(150, self.windowPrepared)
        return True

    def icon_clicked(self, widget):
        if self.dialogVisible():
            self.hideApplet()
        else:
            self.showApplet()

    def menu_popup(self, widget, event):
        self.popup_menu.popup(None, None, None, event.button, event.time)

    def button_press(self, widget, event):
        if event.button == 2:
            self.button_play_pause_cb(widget)
            return True
        return False

    def resize_video_widget(self, *args):
        self.da.set_size_request(self.video_width, self.video_height)

    def bind_keys(self):
        """
        Loads all the config variables
        """
        self.client = awn.config_get_default_for_applet(self)

        config_map = {
            'audiosink': 'audio_sink',
            'videosink': 'video_sink',
            'video_width': 'video_width',
            'video_height': 'video_height',
        }

        for key, prop_name in config_map.iteritems():
            self.client.bind(config.GROUP_DEFAULT, key, self, prop_name, False,
                             config.BIND_METHOD_FALLBACK)

        self.recentItems = self.client.get_list(config.GROUP_DEFAULT, "recent_items")

        self.connect("notify::video-width", self.resize_video_widget)
        self.connect("notify::video-height", self.resize_video_widget)

    def play_pause(self):
        oldstate, currentstate, pending = self.playbin.get_state()
        if currentstate != gst.STATE_PLAYING:
            self.playbin.set_state(gst.STATE_PLAYING)
            self.play_icon.props.active = True
            self.button_play.set_label('gtk-media-pause')
        else:
            self.playbin.set_state(gst.STATE_PAUSED)
            self.play_icon.props.active = False
            self.button_play.set_label('gtk-media-play')

    def stop(self):
        self.playbin.set_state(gst.STATE_NULL)
        self.play_icon.props.active = False
        self.button_play.set_label('gtk-media-play')
        self.isVideo = False
        self.dialog.props.hide_on_unfocus = True
        if self.dialogVisible():
            self.hideApplet()

    def applet_drag_motion_cb(self, widget, context, x, y, time):
        self.get_effects().start(awn.EFFECT_LAUNCHING)
        return True

    def applet_drag_leave_cb(self, widget, context, time):
        self.get_effects().stop(awn.EFFECT_LAUNCHING)
        return True

    def applet_drop_cb(self, wdgt, context, x, y, selection, targetType, time):
        uri2play = selection.data
        if len(uri2play.split()) > 1:
            # just take the first one
            uri2play = uri2play.split()[0]
        # I wonder why there are zeroes sometimes?
        uri2play = uri2play.strip('\000').strip()

        if uri2play.startswith("udp://@"):
            uri2play = uri2play.replace("udp://@", "udp://")

        self.stop()
        self.playbin.set_property("uri", uri2play)
        self.updateRecent(uri2play)
        self.play_pause()

        context.finish(True, False, time)
        return True

    def button_play_pause_cb(self, widget):
        self.play_pause()

    def button_stop_cb(self, widget):
        self.stop()

    def show_prefs(self, widget):
        ui_path = os.path.join(os.path.dirname(__file__), "media-player-prefs.ui")
        wTree = gtk.Builder()
        wTree.add_from_file(ui_path)

        window = wTree.get_object("dialog1")
        window.set_icon(self.get_icon().get_icon_at_size(48))

        self.sinkChanged = False
        def sink_changed(widget):
            self.sinkChanged = True

        vidEntry = wTree.get_object("videoSinkEntry")
        vidEntry.set_text(self.video_sink)
        vidEntry.connect("changed", sink_changed)
        auEntry = wTree.get_object("audioSinkEntry")
        auEntry.set_text(self.audio_sink)
        auEntry.connect("changed", sink_changed)

        def size_changed(widget, isWidth):
            if isWidth:
                self.video_width = widget.get_value()
            else:
                self.video_height = widget.get_value()

        wSpin = wTree.get_object("widthSpin")
        wSpin.set_value(self.video_width)
        wSpin.connect("value-changed", size_changed, True)
        hSpin = wTree.get_object("heightSpin")
        hSpin.set_value(self.video_height)
        hSpin.connect("value-changed", size_changed, False)

        def prefs_closed(closeButton, tuple):
            win = tuple[0]
            if self.sinkChanged:
                dialog = gtk.MessageDialog(win, buttons=gtk.BUTTONS_OK, message_format="Please restart the applet to apply changes to sinks.")
                dialog.run()
                dialog.destroy()
                self.video_sink = tuple[1].get_text()
                self.audio_sink = tuple[2].get_text()
            win.destroy()

        close = wTree.get_object("closeButton")
        close.connect("clicked", prefs_closed, (window, vidEntry, auEntry))

        window.show()

    def show_about(self, widget):
        about = gtk.AboutDialog()
        awn_icon = self.get_icon()
        about.set_logo(awn_icon.get_icon_at_size(48))
        about.set_icon(awn_icon.get_icon_at_size(64))
        about.set_name("Media Player Applet")
        about.set_copyright("Copyright (c) 2008-2009 Michal Hruby <michal.mhr at gmail.com>")
        about.set_authors(["Michal Hruby <michal.mhr at gmail.com>"])
        about.set_comments("Plays any media files you drop on the applet.")
        about.set_license("This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.")
        about.set_wrap_license(True)
        about.set_documenters(["Michal Hruby <michal.mhr at gmail.com>"])
        about.set_artists(["Panana Pan"])
        about.run()
        about.destroy()


if __name__ == "__main__":
    awn.init(sys.argv[1:])
    applet = MediaPlayerApplet(awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
