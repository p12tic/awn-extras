#!/usr/bin/python
# Copyright (c) 2009 Michal Hruby <michal.mhr at gmail.com>
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

import gtk
import gobject
import glib
import cairo

import awn
from desktopagnostic import config

class ActionItem(gtk.EventBox):
    __gtype_name__ = 'ActionItem'
    __gsignals__ = {
        'drag-finished':
            (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ()),
        'drag-data-received-simple':
            (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE,
                [gobject.TYPE_STRING])
    }

    def __init__(self, pixbuf, label):
        gtk.EventBox.__init__(self)

        self.hovering = False

        pad = gtk.Alignment()
        self.pad_size = pixbuf.get_width() / 10
        pad.set_padding(self.pad_size, self.pad_size,
                        self.pad_size, self.pad_size)
        vbox = gtk.VBox()
        vbox.set_spacing(12)

        self.img = awn.Image()
        self.img.set_from_pixbuf(pixbuf)
        self.text = awn.Label()
        self.text.set_markup('<span font-size="x-large" weight="bold">'+label+'</span>')

        vbox.add(self.img)
        vbox.add(self.text)
        pad.add(vbox)
        self.add(pad)

        # Init transparent colormap
        cm = self.get_screen().get_rgba_colormap()
        if cm != None:
            self.set_colormap(cm)

        awn.utils_ensure_transparent_bg(self)

        self.init_dnd()

    def do_expose_event(self, event):
        cr = self.window.cairo_create()

        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0, 0, 0, 0.5)
        cr.paint()

        if self.hovering:
            line_width = self.pad_size / 3
            awn.cairo_rounded_rect(cr, line_width, line_width,
                                   self.allocation.width - line_width*2,
                                   self.allocation.height - line_width*2,
                                   10, awn.ROUND_ALL)
            cr.set_source_rgba(0.2, 0.2, 0.2, 0.5)
            cr.fill_preserve()
            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.set_source_rgba(0.8, 0.8, 0.8, 0.75)
            cr.set_line_width(line_width)
            cr.stroke()

        del cr

        # propagate expose
        child = self.get_child()
        if child is not None:
            self.propagate_expose(child, event)
        return True

    # feel free to override this method, if you want special mime-types
    def init_dnd(self):
        self.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION,
                           [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                           gtk.gdk.ACTION_MOVE)

        self.connect("drag-data-received", self.do_data_received)
        self.connect("drag-data-received-simple", self.do_data_received_simple)
        self.connect("drag-motion", self.drag_motion_cb)
        self.connect("drag-leave", self.drag_leave_cb)

    def drag_motion_cb(self, widget, context, x, y, time):
        self.img.get_effects().start(awn.EFFECT_HOVER)
        if not self.hovering:
            self.hovering = True
            self.queue_draw()
        return True

    def drag_leave_cb(self, widget, context, time):
        self.img.get_effects().stop(awn.EFFECT_HOVER)
        self.hovering = False
        self.queue_draw()
        return True

    # this method can be overriden
    def do_data_received_simple(self, widget, data):
        print "received_simple was called, data:", data

    # this method can be also overriden if simple is not enough
    def do_data_received(self, wdgt, context, x, y, selection,
                         targetType, time):
        # stop the effect
        self.img.get_effects().stop(awn.EFFECT_HOVER)
        self.hovering = False

        self.emit('drag-data-received-simple', selection.data)

        context.finish(True, False, time)
        self.emit("drag-finished")
        return True


class OverlayWindow(gtk.Window):
    __gtype_name__ = 'OverlayWindow'
    __gsignals__ = {
        'drag-finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
    }

    def __init__(self, uid):
        gtk.Window.__init__(self, gtk.WINDOW_POPUP)

        # Init transparent colormap
        cm = self.get_screen().get_rgba_colormap()
        if cm != None:
            self.set_colormap(cm)

        screen = self.get_screen()
        mon_num = screen.get_monitor_at_point(0,0)
        rect = screen.get_monitor_geometry(mon_num)

        self.screen_w = rect.width
        self.screen_h = rect.height

        screen.connect("size-changed", self.screen_changed)

        awn.utils_ensure_transparent_bg(self)

        # Connect to signals we need
        self.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION,
                           [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                           gtk.gdk.ACTION_COPY)

        self.connect("drag-data-received", self.no_target_drop)
        
        # We will use this themed icon to get the hi-res pixbufs
        self.icon_cache = awn.ThemedIcon()
        self.icon_cache.set_applet_info("dropper", uid)
        self.icon_cache.set_info_append("icon-1", "stock_internet")
        self.icon_cache.set_info_append("icon-2", "stock_open")

        self.init_components()

    def do_size_request(self, requisition):
        # FIXME: don't use full screen if we're not composited
        child = self.get_child()
        if child is not None:
            child_req = child.size_request()

        requisition.width = self.screen_w
        requisition.height = self.screen_h

    def do_expose_event(self, event):
        cr = self.window.cairo_create()

        cr.set_operator(cairo.OPERATOR_OVER)
        cr.set_source_rgba(0, 0, 0, 0.5)
        cr.paint()

        del cr
        return True

    def screen_changed(self, screen):
        mon_num = screen.get_monitor_at_point(0,0)
        rect = screen.get_monitor_geometry(mon_num)

        self.screen_w = rect.width
        self.screen_h = rect.height

        self.queue_resize()

    def init_components(self):
        align = gtk.Alignment(0.5, 0.5)

        hbox = gtk.HBox()
        hbox.set_spacing(12)

        def widget_drag_finished(widget):
            # proxy the signal
            self.emit("drag-finished")

        for widget in self.get_action_widgets():
            widget.connect("drag-finished", widget_drag_finished)
            hbox.add(widget)

        align.add(hbox)
        self.add(align)

    def get_action_widgets(self):
        widgets = []

        pixbuf_size = 96

        pixbuf = self.icon_cache.get_icon_at_size(pixbuf_size, "icon-2")
        widgets.append(ActionItem(pixbuf, 'Open'))

        pixbuf = self.icon_cache.get_icon_at_size(pixbuf_size, "icon-1")
        widgets.append(ActionItem(pixbuf, 'Send to Pastebin'))

        return widgets

    def no_target_drop(self, wdgt, context, x, y, selection, targetType, time):
        context.finish(True, False, time)
        self.emit("drag-finished")
        return True

class DropperApplet(awn.AppletSimple):

    APPLET_NAME = "Dropper"

    def __init__(self, uid, panel_id):
        """Creating the applets core"""
        awn.AppletSimple.__init__(self, "dropper", uid, panel_id)
        self.set_tooltip_text(DropperApplet.APPLET_NAME)
        self.set_icon_name('dropper')

        # init stuff
        self.timer_id = 0
        self.dialog = OverlayWindow(uid)

        # Popup menu
        self.prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
        self.prefs.connect("activate", self.show_prefs)
        self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
        self.about.connect("activate", self.show_about)

        self.popup_menu = self.create_default_menu()
        self.popup_menu.append(self.prefs)

        item = gtk.SeparatorMenuItem()
        item.show()
        self.popup_menu.append(item)

        self.popup_menu.append(self.about)
        self.popup_menu.show_all()

        self.timer_overlay = awn.OverlayProgressCircle()
        self.timer_overlay.props.active = False
        self.timer_overlay.props.apply_effects = False
        self.get_icon().add_overlay(self.timer_overlay)

        # Standard AWN Connects
        self.connect("context-menu-popup", self.menu_popup)
        # Drag&drop support
        self.get_icon().drag_dest_set(
                               gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION,
                               [("text/uri-list", 0, 0), ("text/plain", 0, 1)],
                               gtk.gdk.ACTION_COPY)

        self.get_icon().connect("drag-data-received", self.applet_drop_cb)
        self.get_icon().connect("drag-motion", self.applet_drag_motion_cb)
        self.get_icon().connect("drag-leave", self.applet_drag_leave_cb)

        self.dialog.connect("drag-finished", self.applet_dropped)

    def dialogVisible(self):
        return (self.dialog.flags() & gtk.VISIBLE) != 0

    def showActions(self):
        self.timer_overlay.props.active = False
        # make sure the drag effect is stopped
        self.get_effects().stop(awn.EFFECT_LAUNCHING)

        self.dialog.set_keep_above(True)
        self.dialog.show_all()

        return False

    def hideApplet(self):
        self.dialog.hide()

    def showTimer(self, context):
        TIMER_MAX = 35
        self.timer_count += 1
        self.timer_overlay.props.percent_complete = self.timer_count * 100 / TIMER_MAX

        if self.timer_count == TIMER_MAX:
            self.showActions()
            self.timer_id = 0
            context.drag_status(gtk.gdk.ACTION_COPY, 0)
            return False

        return True

    def menu_popup(self, widget, event):
        self.popup_menu.popup(None, None, None, event.button, event.time)

    def applet_drag_motion_cb(self, widget, context, x, y, time):
        self.get_effects().start(awn.EFFECT_LAUNCHING)
        if self.timer_id == 0:
            self.timer_count = 0
            self.timer_overlay.props.percent_complete = 0
            self.timer_overlay.props.active = True
            self.timer_id = glib.timeout_add(40, self.showTimer, context)
        return True

    def applet_drag_leave_cb(self, widget, context, time):
        self.timer_overlay.props.active = False
        self.get_effects().stop(awn.EFFECT_LAUNCHING)
        if self.timer_id != 0:
            glib.source_remove(self.timer_id)
            self.timer_id = 0
        return True

    def applet_drop_cb(self, wdgt, context, x, y, selection, targetType, time):
        context.finish(True, False, time)
        return True

    def applet_dropped(self, widget):
        self.hideApplet()

    def show_prefs(self, widget):
        ui_path = os.path.join(os.path.dirname(__file__), "dropper-prefs.ui")
        wTree = gtk.Builder()
        wTree.add_from_file(ui_path)

        window = wTree.get_object("dialog1")
        window.set_icon(self.get_icon().get_icon_at_size(48))

        def prefs_closed(closeButton, win):
            win.destroy()

        close = wTree.get_object("closeButton")
        close.connect("clicked", prefs_closed, window)

        window.show()

    def show_about(self, widget):
        about = gtk.AboutDialog()
        awn_icon = self.get_icon()
        about.set_logo(awn_icon.get_icon_at_size(48))
        about.set_icon(awn_icon.get_icon_at_size(64))
        about.set_name("Dropper Applet")
        about.set_copyright("Copyright (c) 2009 Michal Hruby <michal.mhr at gmail.com>")
        about.set_authors(["Michal Hruby <michal.mhr at gmail.com>"])
        about.set_comments("Shows actions overlay when you drag something over the applet.")
        about.set_license("This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.")
        about.set_wrap_license(True)
        about.set_documenters(["Michal Hruby <michal.mhr at gmail.com>"])
        about.run()
        about.destroy()


if __name__ == "__main__":
    awn.init(sys.argv[1:])
    applet = DropperApplet(awn.uid, awn.panel_id)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
