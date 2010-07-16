#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
bandwidth-monitor - Network bandwidth monitor.
Copyright (c) 2006-2010 Kyle L. Huff (awn-bwm@curetheitch.com)
url: <http://www.curetheitch.com/projects/awn-bwm/>
Email: awn-bwm@curetheitch.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
'''

import os

import gtk
from gtk import gdk

import awn
from awn import Dialog, cairo_rounded_rect, ROUND_ALL, OverlayText
from awn.extras import _

import cairo
import dbus
awn.check_dependencies(globals(), "gtop")

ICON_DIR = os.path.join(os.path.dirname(__file__), 'images')


class NetworkManager:

    def __init__(self):
        self.bus = dbus.SystemBus()
        self.nm_path = 'org.freedesktop.NetworkManager'
        self.nm_object = self.bus.get_object(self.nm_path, '/org/freedesktop/NetworkManager')

    def get_device_by_name(self, dev_name):
        try:
            for dev_opath in self.nm_object.GetDevices(dbus_interface=self.nm_path):
                device = self.bus.get_object(self.nm_path, dev_opath)
                if self.get_device_name(device) == dev_name:
                    return device
            return None
        except dbus.exceptions.DBusException:
            return None

    def get_devices(self):
        devices = []
        for dev_opath in self.nm_object.GetDevices(dbus_interface=self.nm_path):
            device = self.bus.get_object(self.nm_path, dev_opath)
            devices.append(device)
        return devices

    def get_device_name(self, device):
        return device.Get(self.nm_path + '.Device', 'Interface',
            dbus_interface='org.freedesktop.DBus.Properties').decode() if device else None

    def get_device_type(self, device):
        return device.Get(self.nm_path + '.Device', 'DeviceType',
            dbus_interface='org.freedesktop.DBus.Properties') if device else None

    def get_device_status(self, device):
        return device.Get(self.nm_path + '.Device', 'State',
            dbus_interface='org.freedesktop.DBus.Properties') if device else None

    def get_current_ssid(self, device):
        ap_path = device.Get(self.nm_path + '.Device.Wireless', 'ActiveAccessPoint', dbus_interface='org.freedesktop.DBus.Properties')
        ap = self.bus.get_object(self.nm_path, ap_path)
        ssid_byteArray = ap.Get(self.nm_path + '.AccessPoint', 'Ssid', dbus_interface='org.freedesktop.DBus.Properties')
        if ssid_byteArray:
            ssid = ''.join(chr(b) for b in ssid_byteArray)
        else:
            ssid = None
        return ssid

    def get_bluetooth_endpoint_name(self, device):
        return device.Get(self.nm_path + '.Device.Bluetooth', 'Name',
            dbus_interface='org.freedesktop.DBus.Properties').decode() if device else None


class InterfaceGraph(gtk.DrawingArea):

    def __init__(self, parent, iface, width, height, show_text=False):
        gtk.DrawingArea.__init__(self)
        self.__parent = parent
        self.interface = iface
        self.width = width
        self.height = height
        self.translated_x = 0
        self.translated_y = 0
        self.show_text = show_text
        self.connect('expose_event', self.expose)
        self.button_click_time = 0
        self.highlight = False
        self.set_events(gtk.gdk.BUTTON_PRESS_MASK |
                        gtk.gdk.BUTTON_RELEASE_MASK |
                        gtk.gdk.ENTER_NOTIFY_MASK |
                        gtk.gdk.LEAVE_NOTIFY_MASK)
        try:
            self.network_manager = NetworkManager()
        except Exception, e:
            self.network_manager = None

    def expose(self, widget, event):
        if not self.show_text and \
            self.__parent.interface_dialog.current_dialog == 'graph':
            widget.window.hide()
        self.set_size_request(int(self.width), int(self.height))
        context = widget.window.cairo_create()
        context.set_operator(cairo.OPERATOR_CLEAR)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)
        self.draw_graph()
        return False

    def refresh(self, event=None):
        if not self.show_text and \
            self.__parent.interface_dialog.current_dialog == 'graph':
            return True
        self.draw_graph()

    def get_cairo_color(self, color):
        return color / 65535.0

    def draw_graph(self):
        if not self.window:
            return True
        self.set_size_request(int(self.width), int(self.height))
        context = self.window.cairo_create()
        context.translate(self.translated_x, self.translated_y)
        context.set_operator(cairo.OPERATOR_CLEAR)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)
        iface = self.interface
        context.set_source_rgba(0, 0, 0, 0.85)
        if self.show_text:
            context.rectangle(0, 0, self.width, self.height + 20)
            context.fill()
        else:
            cairo_rounded_rect(context, -1, -1, self.width + 2, self.height + 2, 4, ROUND_ALL)
            context.fill()
        if self.show_text and not self.interface == self.__parent.iface:
            self.interface = self.__parent.iface
        if self.interface in self.__parent.netstats.ifaces:
            if self.show_text:
                line_width = 3
                icon_size = 0
                pixbuf = None
                self.interface = self.__parent.iface
                ''' if wireless, draw it '''
                if iface in self.__parent.netstats.ifaces:
                    if 'signal' in self.__parent.netstats.ifaces[iface]:
                        signal = abs(int(self.__parent.netstats.ifaces[iface]['signal']['strength'])) * 80 / 100
                        quality = int(self.__parent.netstats.ifaces[iface]['signal']['quality'])
                        noise = int(self.__parent.netstats.ifaces[iface]['signal']['noise'])
                        icon_size = 24
                        if quality == 0 or noise == -256:
                            icon_name = 'wireless-disconnected.png'
                        elif signal <= 40:
                            icon_name = 'wireless-full.png'
                        elif signal <= 60:
                            icon_name = 'wireless-high.png'
                        elif signal <= 90:
                            icon_name = 'wireless-medium.png'
                        else:
                            icon_name = 'wireless-low.png'
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, icon_name), icon_size, icon_size)
                        signal = self.__parent.netstats.ifaces[iface]['signal']
                        ssid = None
                        self.__parent.draw_wireless(context, self.width, self.height, self.interface)
                        if self.network_manager:
                            nm_device = self.network_manager.get_device_by_name(iface)
                            nm_device_status = self.network_manager.get_device_status(nm_device)
                            if nm_device_status in [7, 8]:
                                ssid = self.network_manager.get_current_ssid(nm_device)
                                context.set_source_rgba(1, 1, 1)
                                context.set_font_size(18)
                                context.set_line_width(3)
                                context.move_to(6, 45)
                                context.set_source_rgba(0, 0, 0)
                                context.text_path('SSID: %s' % ssid)
                                context.stroke()
                                context.set_source_rgba(1, 1, 1)
                                context.move_to(6, 45)
                                context.show_text('SSID: %s' % ssid)
                                context.fill()
                    if not 'signal' in self.__parent.netstats.ifaces[iface] and \
                        not self.__parent.netstats.ifaces[iface]['status'] == 'V' and \
                        not gtop.NETLOAD_IF_FLAGS_LOOPBACK & self.__parent.netstats.ifaces[iface]['status']:
                        icon_size = 24
                        icon_name = 'ethernet.png'
                        try:
                            if os.access('/sys/class/net/%s/device/device/address' % iface, os.R_OK):
                                hw_addr = open('/sys/class/net/%s/device/address' % iface, 'r').read().strip()
                                ''' most likely a bluetooth connection, check with NM '''
                                if self.network_manager:
                                    nm_device = self.network_manager.get_device_by_name(hw_addr)
                                    nm_device_type = self.network_manager.get_device_type(nm_device)
                                    if nm_device_type == 5:
                                        ''' bluetooth '''
                                        icon_name = 'bluetooth.png'
                                        bt_endpoint = self.network_manager.get_bluetooth_endpoint_name(nm_device)
                                        context.set_source_rgba(1, 1, 1)
                                        context.set_font_size(18)
                                        context.set_line_width(3)
                                        context.move_to(6, 45)
                                        context.set_source_rgba(0, 0, 0)
                                        context.text_path(bt_endpoint)
                                        context.stroke()
                                        context.set_source_rgba(1, 1, 1)
                                        context.move_to(6, 45)
                                        context.show_text(bt_endpoint)
                                        context.fill()
                        except:
                            pass
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, icon_name), icon_size, icon_size)
                    if not self.__parent.netstats.ifaces[iface]['status'] == 'V' and \
                        gtop.NETLOAD_IF_FLAGS_LOOPBACK & self.__parent.netstats.ifaces[iface]['status']:
                        icon_size = 24
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'loopback.png'), icon_size, icon_size)
                    if iface == 'Multi Interface':
                        icon_size = 24
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'multi.png'), icon_size, icon_size + 5)
                    if iface == 'Sum Interface':
                        icon_size = 24
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'sum.png'), icon_size, icon_size)
                    if 'tun' in iface or 'tap' in iface:
                        icon_size = 24
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'tun-tap.png'), icon_size, icon_size)
                    if pixbuf:
                        context.set_source_pixbuf(pixbuf, 4, 0)
                        context.paint()
                context.set_source_rgba(0.0, 1.0, 0.0, 1.0)
                context.set_line_width(0.2)
                ''' draw horizontal lines on the meter '''
                i = 50
                while i < self.height + 50:
                    context.move_to(0, i)
                    context.line_to(self.width, i)
                    i += 20
                context.stroke()
                context.set_source_rgba(1, 1, 1)
                context.select_font_face('Helvetica',
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                context.set_font_size(24.0)
                context.set_line_width(3)
                context.move_to(8 + icon_size, 20)
                context.set_source_rgba(0, 0, 0)
                context.text_path(self.__parent.iface)
                context.stroke()
                context.set_source_rgba(1, 1, 1)
                context.move_to(8 + icon_size, 20)
                context.show_text(self.__parent.iface)
                context.set_font_size(14.0)
                tx_label = 'TX: %s' % self.__parent.readable_speed_ps(
                    self.__parent.netstats.ifaces[self.interface]['tx_bytes'],
                        self.__parent.unit)
                rx_label = 'RX: %s' % self.__parent.readable_speed_ps(
                    self.__parent.netstats.ifaces[self.interface]['rx_bytes'],
                        self.__parent.unit)
                context.move_to(self.width - 100, 15)
                context.set_source_rgba(0, 0, 0)
                context.text_path(tx_label)
                context.stroke()
                context.move_to(self.width - 100, 15)
                context.set_source_rgba(1, 1, 1)
                context.show_text(tx_label)
                context.fill()
                context.move_to(self.width - 100, 30)
                context.set_source_rgba(0, 0, 0)
                context.text_path(rx_label)
                context.stroke()
                context.move_to(self.width - 100, 30)
                context.set_source_rgba(1, 1, 1)
                context.show_text(rx_label)
                context.fill()
            else:
                line_width = 2
                context.set_line_width(line_width)
                x, y = 0, 0
                h = self.height
                cairo_rounded_rect(context, 1, 1, self.width - 2, self.height - 2, 4, ROUND_ALL)
                pat = cairo.LinearGradient(0, self.height / 2 + 15, 0, 0)
                if self.__parent.netstats.ifaces[iface]['status'] == 'V' or \
                    gtop.NETLOAD_IF_FLAGS_RUNNING & \
                    self.__parent.netstats.ifaces[iface]['status']:
                    c1, c2, c3 = 0, 0, 0
                    c4, c5, c6 = 0, 1, 0
                else:
                    c1, c2, c3 = 0, 0, 0
                    c4, c5, c6 = 1, 0, 0

                pat.add_color_stop_rgba(0.1, c1, c2, c3, 0.85)
                pat.add_color_stop_rgba(1.0, c4, c5, c6, 0.85)
                count = 1

                context.set_source(pat)
                context.fill()

                pixbuf = None
                icon_size = 24 if self.highlight else 16
                if 'Multi' in iface:
                    icon_size = 28 if self.highlight else 20
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'multi.png'), icon_size, icon_size)
                if 'Sum' in iface:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'sum.png'), icon_size, icon_size)
                if not self.__parent.netstats.ifaces[iface]['status'] == 'V' and \
                        gtop.NETLOAD_IF_FLAGS_LOOPBACK & self.__parent.netstats.ifaces[iface]['status']:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'loopback.png'), icon_size, icon_size)
                if 'signal' in self.__parent.netstats.ifaces[iface]:
                    signal = abs(int(self.__parent.netstats.ifaces[iface]['signal']['strength'])) * 80 / 100
                    quality = int(self.__parent.netstats.ifaces[iface]['signal']['quality'])
                    noise = int(self.__parent.netstats.ifaces[iface]['signal']['noise'])
                    if quality == 0 or noise == -256:
                        icon_name = 'wireless-disconnected.png'
                    elif signal <= 40:
                        icon_name = 'wireless-full.png'
                    elif signal <= 60:
                        icon_name = 'wireless-high.png'
                    elif signal <= 90:
                        icon_name = 'wireless-medium.png'
                    else:
                        icon_name = 'wireless-low.png'
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, icon_name), icon_size, icon_size)
                if not 'signal' in self.__parent.netstats.ifaces[iface] and \
                    not self.__parent.netstats.ifaces[iface]['status'] == 'V' and \
                    not gtop.NETLOAD_IF_FLAGS_LOOPBACK & self.__parent.netstats.ifaces[iface]['status']:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'ethernet.png'), icon_size, icon_size)
                    if self.network_manager:
                        try:
                            if os.access('/sys/class/net/%s/device/device/address' % iface, os.R_OK):
                                hw_addr = open('/sys/class/net/%s/device/address' % iface, 'r').read().strip()
                                ''' most likely a bluetooth connection, check with NM '''
                                nm_device = self.network_manager.get_device_by_name(hw_addr)
                                nm_device_type = self.network_manager.get_device_type(nm_device)
                                if nm_device_type == 5:
                                    ''' bluetooth '''
                                    icon_size = 32 if self.highlight else 20
                                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'bluetooth.png'), icon_size, icon_size)
                        except:
                            pass
                if 'tun' in iface or 'tap' in iface:
                    pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(ICON_DIR, 'tun-tap.png'), icon_size, icon_size)
                if pixbuf:
                    context.set_source_pixbuf(pixbuf, self.width - pixbuf.get_width() - 4, 4)
                    context.paint()
                context.select_font_face('Helvetica',
                        cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                if not self.highlight:
                    context.set_font_size(12.0)
                    text_xpos = 0
                else:
                    context.set_font_size(14.0)
                    text_xpos = -4
                context.set_source_rgba(1, 1, 1)

                iface_name = self.interface.split(' ')[0]
                text_xpos = self.width / 3 - 20
                context.move_to(text_xpos, self.height - self.height / 2)
                context.show_text(iface_name)
                context.fill()

                def click_event(widget, event):
                    if abs(event.time - self.button_click_time) > 500:
                        self.button_click_time = event.time
                        self.__parent.change_iface(widget, self.interface)
                        self.__parent.interface_dialog.buttonArea.change_dialog(widget, event, 'graph')
                self.connect('button_release_event', click_event)
            context.set_font_size(12.0)
            multi = True if self.interface == 'Multi Interface' else False
            if multi:
                tmp_history = [1]
                for iface in self.__parent.netstats.ifaces:
                    if self.__parent.netstats.ifaces[iface]['multi_include']:
                        tmp_history.extend(
                            self.__parent.netstats.ifaces[iface]['rx_history'])
                        tmp_history.extend(
                            self.__parent.netstats.ifaces[iface]['tx_history'])
                tmp_history.sort()
                max_val = tmp_history[-1]
                ratio = max_val / 28 if max_val > self.__parent.ratio else 1
                for iface in self.__parent.netstats.ifaces:
                    if self.__parent.netstats.ifaces[iface]['multi_include']:
                        self.__parent.draw_meter(context, self.width, self.height, iface, multi=multi, line_width=line_width, ratio=ratio, border=True)
            else:
                self.__parent.draw_meter(context, self.width, self.height, self.interface, multi=multi, line_width=line_width, ratio=1, border=True)
            if not self.show_text:
                if self.highlight:
                    context.set_source_rgba(1, 1, 1, 1)
                    context.set_line_width(3)
                    cairo_rounded_rect(context, 1, 1, self.width - 2, self.height - 2, 6, ROUND_ALL)
                    context.stroke()
                else:
                    context.set_source_rgba(1, 1, 1, 1)
                    cairo_rounded_rect(context, 0, 0, self.width, self.height, 4, ROUND_ALL)
                    context.stroke()
        else:
            context.set_source_rgba(1, 1, 1)
            context.select_font_face('Helvetica',
                    cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            context.set_font_size(18.0)
            device_error = _('No Device')
            device_error_message = _('Please select a valid device')
            context.move_to(self.width / 3.0, self.height / 2 - 7)
            context.show_text(device_error)
            context.move_to(self.width / 3.0, self.height / 2 + 10)
            context.show_text(device_error_message)
            context.fill()
        return True


class InterfaceDeatil:

    def __init__(self, parent):
        self.parent = parent
        self.applet = parent.applet

        self.interfaceDialog = None
        self.interfaceArea = None
        self.interfaceListArea = None
        self.interfaceOptionsArea = None
        self.buttonArea = None
        self.current_dialog = 'graph'

    def setup_interface_dialogs(self):
        if self.interfaceDialog is not None:
            del self.interfaceDialog
            self.applet.dialog.unregister('main')
        if self.interfaceArea is not None:
            del self.interfaceArea
        if self.interfaceListArea is not None:
            del self.interfaceListArea
        if self.buttonArea is not None:
            del self.buttonArea
        if self.interfaceOptionsArea:
            del self.interfaceOptionsArea

        self.interfaceDialog = self.InterfaceDialogWrapper(self.applet)
        self.applet.dialog.register('main', self.interfaceDialog)

        def leave_notify(widget, event, self):
            #return True
            if not hasattr(self.interfaceOptionsArea, 'graph_selection') or \
                not self.interfaceOptionsArea.graph_selection.get_property('popup-shown'):
                self.parent.interface_dialog.buttonArea.change_dialog(widget, event, 'graph')
        self.interfaceDialog.foe_id = self.interfaceDialog.connect('focus-out-event', leave_notify, self)
        self.interfaceArea = InterfaceGraph(self.parent, self.parent.iface, 450, 170, True)

        self.buttonArea = InterfaceControls(self.parent)
        self.interfaceListArea = InterfaceSelectionList(self.parent)
        self.interfaceListArea.draw_interface_list()

        self.interfaceOptionsArea = InterfaceOptionsDialog(self.parent)

        self.interfaceArea.set_size_request(450, 170)
        self.interfaceListArea.set_size_request(450, 190)
        self.buttonArea.set_size_request(450, 210)

        box = gtk.Fixed()
        box.put(self.buttonArea, 0, 0)
        box.put(self.interfaceListArea, 10, 15)
        box.put(self.interfaceArea, 10, 0)
        box.put(self.interfaceOptionsArea, 10, 0)

        box.show_all()
        self.interfaceDialog.add(box)

    def do_current(self):
        self.interfaceListArea.hide()
        self.interfaceArea.hide()
        self.interfaceOptionsArea.hide()
        if self.current_dialog == 'graph':
            self.interfaceArea.refresh()
            self.interfaceArea.show()
        if self.current_dialog == 'list':
            self.interfaceListArea.refresh()
            self.interfaceListArea.show_all()
        if self.current_dialog == 'options':
            self.interfaceOptionsArea.show_all()

    class InterfaceDialogWrapper(Dialog):

        def __init__(self, applet):
            Dialog.__init__(self, applet)
            self.__parent = self
            self.applet = applet
            self.connect('expose-event', self.expose_event_cb)

        def expose_event_cb(self, widget, event=None):
            context = widget.window.cairo_create()

            context.set_operator(cairo.OPERATOR_CLEAR)
            context.paint()
            context.set_operator(cairo.OPERATOR_OVER)

            for child in self.get_children():
                self.propagate_expose(child, event)

            return True


class InterfaceControls(gtk.Fixed):

    def __init__(self, parent_applet):
        gtk.Fixed.__init__(self)
        self.__parent = parent_applet
        self.width, self.height = 450, 200
        self.connect('expose_event', self.expose_event_cb)

    def change_dialog(self, widget, event, force=None):
        self.__parent.interface_dialog.interfaceArea.hide()
        self.__parent.interface_dialog.interfaceListArea.hide()
        self.__parent.interface_dialog.interfaceOptionsArea.hide()
        if self.__parent.interface_dialog.current_dialog == force:
            self.__parent.interface_dialog.current_dialog = 'graph'
        else:
            self.__parent.interface_dialog.current_dialog = force if \
                force else self.__parent.interface_dialog.current_dialog
        if self.__parent.interface_dialog.current_dialog == 'list':
            self.__parent.interface_dialog.current_dialog = 'list'
            self.__parent.interface_dialog.interfaceListArea.rebuild()
            self.__parent.interface_dialog.interfaceListArea.refresh()
            self.__parent.interface_dialog.interfaceListArea.show_all()
            self.iface_options_btn.set_label(_('Options/Info'))
            self.iface_options_btn.hide()
            self.iface_list_btn.set_label(_('Back to Graph'))
        elif self.__parent.interface_dialog.current_dialog == 'options':
            self.iface_options_btn.parent.move(self.iface_options_btn, self.width - 110, self.height - 25)
            self.iface_options_btn.set_label(_('Back to Graph'))
            self.iface_list_btn.set_label(_('Interfaces'))
            self.__parent.interface_dialog.interfaceOptionsArea.show_all()
        else:
            self.iface_list_btn.set_label(_('Interfaces'))
            self.iface_options_btn.set_label(_('Options/Info'))
            self.iface_options_btn.show()
            self.__parent.interface_dialog.interfaceArea.refresh()
            self.__parent.interface_dialog.interfaceArea.show_all()

    def expose_event_cb(self, widget, event=None):
        context = widget.window.cairo_create()
        context.translate(25, 10)
        context.set_operator(cairo.OPERATOR_CLEAR)
        context.paint()
        context.set_operator(cairo.OPERATOR_OVER)
        context.set_source_rgba(0, 0, 0, 0.85)
        cairo_rounded_rect(context, 0, 0, self.width, self.height + 12, 4, ROUND_ALL)
        context.fill()
        context.set_line_width(1)
        context.set_source_rgba(0, 0, 0, 0.55)
        cairo_rounded_rect(context, 0, 0, self.width, self.height + 12, 4, ROUND_ALL)
        context.stroke()

        if not hasattr(self, 'iface_list_btn'):
            self.iface_list_btn = gtk.Button(_('Interfaces'))
            self.iface_list_btn.connect('button_press_event', self.change_dialog, 'list')
            self.parent.put(self.iface_list_btn, 20, self.height - 25)

        if not hasattr(self, 'change_unit_btn'):
            self.change_unit_btn = gtk.Button(_('Change Unit'))
            self.change_unit_btn.connect('clicked', self.__parent.call_change_unit)
            self.parent.put(self.change_unit_btn, 180, self.height - 25)

        if not hasattr(self, 'iface_options_btn'):
            self.iface_options_btn = gtk.Button(_('Options/Info'))
            self.iface_options_btn.connect('button_press_event', self.change_dialog, 'options')
            self.parent.put(self.iface_options_btn, self.width - 98, self.height - 25)

        if not hasattr(self, 'initted'):
            self.iface_list_btn.show()
            self.change_unit_btn.show()
            self.iface_options_btn.show()
            self.initted = True

        return True


class InterfaceOptionsDialog(gtk.Fixed):

    def __init__(self, parent_applet):
        gtk.Fixed.__init__(self)
        self.__parent = parent_applet
        self.width, self.height = 450, 200
        self.connect('expose_event', self.expose_event_cb)
        self.iface = None

    def refresh(self):
        for child in self.get_children():
            self.remove(child)
            del child
        self.rebuild()

    def rebuild(self):
        self.iface = self.__parent.iface
        ifaces = self.__parent.netstats.ifaces
        iface = self.__parent.iface

        def keep_open(widget, event):
            if hasattr(self, 'graph_selection'):
                return True if self.graph_selection.get_property('popup-shown') else False
        self.__parent.interface_dialog.interfaceDialog.connect('focus_out_event', keep_open)

        if iface in ifaces:
            fields = [('status', _('Status')), ('address', _('IP Address')), ('subnet', _('Subnet Mask'))]
            y_pos = 10
            for field in fields:
                if field[0] == 'status':
                    lbl_text = '%s: ' % (field[1])
                    if ifaces[iface]['status'] == 'V' or \
                    gtop.NETLOAD_IF_FLAGS_UP & ifaces[iface]['status']:
                        lbl_text += 'UP'
                    if ifaces[iface]['status'] == 'V' or \
                    gtop.NETLOAD_IF_FLAGS_RUNNING & ifaces[iface]['status']:
                        lbl_text += ', RUNNING'
                else:
                    lbl_text = '%s: %s' % (field[1], ifaces[iface][field[0]])
                lbl = gtk.Label()
                lbl.set_markup("<span color='white'>%s</span>" % lbl_text)
                lbl.show()
                self.put(lbl, 12, y_pos)
                y_pos += 20
            if iface == 'Sum Interface':
                members = ''
                for interface in sorted(ifaces):
                    if ifaces[interface]['sum_include']:
                        if members == '':
                            members += ' %s' % (interface)
                        else:
                            members += ', %s' % (interface)
                if members == '':
                    members = ' None'
                members_lbl = gtk.Label()
                members_lbl.set_size_request(450, 50)
                members_lbl.set_line_wrap(True)
                members_lbl.set_markup("<span color='white'>Members:%s</span>" % members)
                self.put(members_lbl, 12, y_pos)
                members_lbl.show()
                y_pos += 20
            if iface == 'Multi Interface':
                members = ''
                for interface in sorted(ifaces):
                    if ifaces[interface]['multi_include']:
                        if members == '':
                            members += ' %s' % (interface)
                        else:
                            members += ', %s' % (interface)
                if members == '':
                    members = ' None'
                members_lbl = gtk.Label()
                members_lbl.set_size_request(450, 50)
                members_lbl.set_line_wrap(True)
                members_lbl.set_markup("<span color='white'>Members:%s</span>" % members)
                self.put(members_lbl, 12, y_pos)
                members_lbl.show()
                y_pos += 20
            if 'signal' in ifaces[iface]:
                self.graph_selection = gtk.combo_box_new_text()
                slist = ['Area', 'Area/Bar', 'Bar', 'Fan', 'Fan/Bar']
                for listitem in enumerate(slist):
                    self.graph_selection.append_text(listitem[1])
                    if listitem[1].lower().replace('/', '_') == \
                        ifaces[iface]['graph_type']:
                        selected_item = listitem[0]
                self.graph_selection.set_active(selected_item)

                def change_graph(widget):
                    model = widget.get_model()
                    index = widget.get_active()
                    graph_type = model[index][0].lower().replace('/', '_')
                    self.__parent.netstats.ifaces[iface]['graph_type'] = graph_type
                    prefs = self.__parent.applet.settings['wireless_signal_graph_type']
                    if not prefs:
                        prefs = ['%s|fan' % (iface)]
                    if not iface in prefs.__str__():
                        prefs.append('%s|fan' % (iface))
                    for i, device_pref in enumerate(prefs):
                        dpv = device_pref.split('|')
                        if dpv[0] == iface:
                            dpv[1] = graph_type
                            prefs[i] = '|'.join(dpv)
                    self.__parent.applet.settings['wireless_signal_graph_type'] = prefs
                self.graph_selection.connect('changed', change_graph)
                graph_lbl = gtk.Label()
                graph_lbl.set_markup("<span color='white'>%s</span>" % (_('Wireless graph type')))
                self.put(graph_lbl, 12, y_pos + 4)
                graph_lbl.show()
                self.put(self.graph_selection, 160, y_pos)
                self.graph_selection.show()

    def expose_event_cb(self, widget, event):
        if not len(self.get_children()) or not \
            self.iface == self.__parent.iface or \
            self.__parent.netstats.regenerate:
            for child in self.get_children():
                self.remove(child)
                del child
            self.rebuild()


class InterfaceSelectionList(gtk.Fixed):

    def __init__(self, parent_applet):
        gtk.Fixed.__init__(self)
        self.__parent = parent_applet
        self.width = 450
        self.height = 160
        self.setup_complete = False

    def refresh(self):
        for child in self.get_children():
            child.refresh()

    def rebuild(self):
        for child in self.get_children():
            self.remove(child)
            del child
        self.draw_interface_list()
        self.refresh()

    def draw_interface_list(self):
        if self.setup_complete and \
            not self.__parent.interface_dialog.current_dialog == 'list':
            return
        self.setup_complete = True
        ifaces = self.__parent.netstats.ifaces
        if len(self.__parent.netstats.ifaces) > 10:
            self.mct_height, mct_height = 24, 24

            n = int(len(ifaces) / 5.1)
            ypos_calculation = int(30 * n)
            ypos_spacing = int(30 / n) if n > 3 else 30
        else:
            self.mct_height, mct_height = 42, 42
            ypos_calculation = 58
            ypos_spacing = 10
        self.mct_width, mct_width = 72, 72

        spacing = (self.width - (48 * 2)) / (self.width / (48 * 2))
        xpos, ypos = 13, int(75 - ypos_calculation)

        if ypos < -60:
            ypos = -10
        elif ypos < 0:
            ypos = -5
        for iface in sorted(self.__parent.netstats.ifaces):
            self.__parent.netstats.ifaces[iface]['in_list'] = True
            graph = InterfaceGraph(self.__parent, iface, mct_width, mct_height)

            def hover_action(widget, event, xpos, ypos):
                widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))
                widget.highlight = True
                widget.height = 64
                widget.width = widget.height * 1.5
                widget.refresh()
                widget.window.raise_()
                self.move(widget, xpos - 12, ypos + 1 - widget.height / 3)
            graph.connect('enter_notify_event', hover_action, xpos, ypos)

            def leave_action(widget, event, xpos, ypos):
                widget.window.set_cursor(None)
                widget.highlight = False
                widget.height = self.mct_height
                widget.width = self.mct_width
                widget.refresh()
                self.move(widget, xpos, ypos)
            graph.connect('leave_notify_event', leave_action, xpos, ypos)

            self.put(graph, xpos, ypos)
            xpos += spacing
            if xpos > self.width:
                xpos = 13
                ypos += (mct_height * 2) - int(30 / ypos_spacing) * 4

    def expose_event_cb(self, widget, event=None):
        self.refresh()
        return True
