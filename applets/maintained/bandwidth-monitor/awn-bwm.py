#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
bandwidth-monitor - Network bandwidth monitor.
Copyright (c) 2006-2009 Kyle L. Huff (kyle.huff@curetheitch.com)
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
"""

from datetime import datetime
import os
import re
import string
import sys
import time

import gtk
import awn

from awn.extras import awnlib
import gobject
import gc
import cairo
from StringIO import StringIO
import bwmprefs

APPLET_NAME = "Bandwidth Monitor"
APPLET_VERSION = "0.3.9.2"
APPLET_COPYRIGHT = "© 2006-2009 CURE|THE|ITCH"
APPLET_AUTHORS = ["Kyle L. Huff <kyle.huff@curetheitch.com>"]
APPLET_DESCRIPTION = "Network Bandwidth monitor"
APPLET_WEBSITE = "http://www.curetheitch.com/projects/awn-bwm/"
APPLET_PATH = os.path.dirname(sys.argv[0])
APPLET_ICON = APPLET_PATH + "/images/icon.png"
UI_FILE = os.path.join(os.path.dirname(__file__), "bandwidth-monitor.ui")

class DeviceUsage:

    def __init__(self, parent, unit):
        self.parent = parent
        self.statistics_cmd = "netstat -ia"
        self.interfaces = {}
        self.interfaces["Sum Interface"] = {"collection_time": 0, "status": "V", "prbytes": 0, "ptbytes": 0, "index": 1, "rx_history": [0, 0], "tx_history": [0, 0], "ip_address": '', "netmask": '', "rx_bytes": 0, "tx_bytes": 0, "rx_sum": 0, "tx_sum": 0, "rxtx_sum": 0, "rabytes": 0, "tabytes": 0, 'include_in_sum': False, 'include_in_multi': False, 'upload_color': "#f00", 'download_color': "#ff0"}
        self.interfaces["Multi Interface"] = {"collection_time": 0, "status": "V", "prbytes": 0, "ptbytes": 0, "index": 1, "rx_history": [0, 0], "tx_history": [0, 0], "ip_address": '', "netmask": '', "rx_bytes": 0, "tx_bytes": 0, "rx_sum": 0, "tx_sum": 0, "rxtx_sum": 0, "rabytes": 0, "tabytes": 0, 'include_in_sum': False, 'include_in_multi': False}
        self.devices_cmd = "netstat -eia"
        self.regenerate = False
        self.update_net_stats()
        gobject.timeout_add(1000, self.update_net_stats)

    def update_net_stats(self):
        delta = time.time()
        ifcfg_str = os.popen(self.devices_cmd).read()
        stat_str = os.popen(self.statistics_cmd).readlines()
        device_list = os.popen(self.devices_cmd).readlines()
        device_list = device_list[2:]
        devices = []
        ''' Reset the Sum Interface records to zero '''
        self.interfaces["Sum Interface"]["rx_sum"], self.interfaces["Sum Interface"]["tx_sum"], self.interfaces["Sum Interface"]["rx_bytes"], self.interfaces["Sum Interface"]["tx_bytes"] = 0, 0, 0, 0
        sum_rx_history = 0.0
        sum_tx_history = 0.0
        ''' Reset the Multi Interface records to zero '''
        self.interfaces["Multi Interface"]["rx_sum"], self.interfaces["Multi Interface"]["tx_sum"], self.interfaces["Multi Interface"]["rx_bytes"], self.interfaces["Multi Interface"]["tx_bytes"] = 0, 0, 0, 0
        multi_rx_history = 0.0
        multi_tx_history = 0.0
        if ifcfg_str and stat_str:
            for device_group in ifcfg_str.split("\n\n"):
                device_lines = device_group.split("\n")
                if "Kernel" in device_lines[0]:
                    device_lines = device_lines[1:]
                dev_name = re.split('[\W]+', device_lines[0].strip().replace( ":", "_" ))[0]
                if len(device_lines) > 2 and not dev_name == "loaa" and not dev_name == "wmaster0aa":
                    try:
                        rx_bytes = int(re.search(r'RX bytes:(\d+)\D', device_group).group(1))
                        tx_bytes = int(re.search(r'TX bytes:(\d+)\D', device_group).group(1))
                    except:
                        rx_bytes = 0
                        tx_bytes = 0
                    if not dev_name in self.interfaces:
                        prefs = self.parent.applet.settings["device_display_parameters"]
                        include_in_sum = True
                        include_in_multi = True
                        for device_pref in prefs:
                            device_pref_values = device_pref.split("|")
                            if device_pref_values[0] == dev_name:
                                include_in_sum = device_pref_values[1].__str__()[0].upper()=='T'
                                include_in_multi = device_pref_values[2].__str__()[0].upper()=='T'
                        self.interfaces[dev_name] = {"collection_time": time.time(), "status": None, "prbytes": float(rx_bytes), "ptbytes": float(tx_bytes), "index": 1, "rx_history": [0, 0], "tx_history": [0, 0], "ip_address": '', "netmask": '', "include_in_sum": include_in_sum, 'include_in_multi': include_in_multi, 'upload_color': self.parent.preferences.get_color(dev_name, "upload"), 'download_color': self.parent.preferences.get_color(dev_name, "download")}
                    address = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)\b', device_group)
                    if address:
                        address = address.group(1)
                        netmask = re.search(r'Mask:(\d+\.\d+\.\d+\.\d+)\b', device_group).group(1)
                    else:
                        address = ''
                        netmask = ''
                    self.interfaces[dev_name]["ip_address"], self.interfaces[dev_name]["netmask"] = address, netmask
                    collection = (time.time() - self.interfaces[dev_name]["collection_time"])
                    rbytes = ((float(rx_bytes) - self.interfaces[dev_name]["prbytes"]) * self.parent.unit) / collection
                    tbytes = ((float(tx_bytes) - self.interfaces[dev_name]["ptbytes"]) * self.parent.unit) / collection
                    rabytes = (float(rx_bytes) - self.interfaces[dev_name]["prbytes"]) / collection
                    tabytes = (float(tx_bytes) - self.interfaces[dev_name]["ptbytes"]) / collection
                    self.interfaces[dev_name]["rabytes"] = rabytes
                    self.interfaces[dev_name]["tabytes"] = tabytes
                    rxtx_sum = float(rx_bytes) + float(tx_bytes)
                    if self.interfaces[dev_name]['include_in_sum'] == True:
                        self.interfaces["Sum Interface"]["rx_sum"] += float(rx_bytes)
                        self.interfaces["Sum Interface"]["tx_sum"] += float(tx_bytes)
                        self.interfaces["Sum Interface"]["rx_bytes"] += rbytes
                        self.interfaces["Sum Interface"]["tx_bytes"] += tbytes
                        sum_rx_history += rabytes
                        sum_tx_history += tabytes
                    if self.interfaces[dev_name]['include_in_multi'] == True:
                        self.interfaces["Multi Interface"]["rx_sum"] += float(rx_bytes)
                        self.interfaces["Multi Interface"]["tx_sum"] += float(tx_bytes)
                        self.interfaces["Multi Interface"]["rx_bytes"] += rbytes
                        self.interfaces["Multi Interface"]["tx_bytes"] += tbytes
                        multi_rx_history += rabytes
                        multi_tx_history += tabytes
                    for dev_line in stat_str:
                        if dev_name in dev_line and not ":" in dev_line:
                            ifstatus = re.split('[\W]+', dev_line.strip())[11]
                        elif ":" in dev_line:
                            ifstatus = re.split('[\W]+', dev_line.strip())[7]
                    self.interfaces[dev_name]["rx_bytes"], self.interfaces[dev_name]["tx_bytes"], self.interfaces[dev_name]["prbytes"], self.interfaces[dev_name]["ptbytes"], self.interfaces[dev_name]["rx_sum"], self.interfaces[dev_name]["tx_sum"], self.interfaces[dev_name]["rxtx_sum"], self.interfaces[dev_name]["status"], self.interfaces[dev_name]["collection_time"] = float(rbytes), float(tbytes), float(rx_bytes), float(tx_bytes), float(rx_bytes), float(tx_bytes), float(rxtx_sum), ifstatus, time.time()
                    if len(self.interfaces[dev_name]["rx_history"]) == 20:
                        self.interfaces[dev_name]["rx_history"].pop(0)
                    self.interfaces[dev_name]["rx_history"].append(self.interfaces[dev_name]["rabytes"])
                    if len(self.interfaces[dev_name]["tx_history"]) == 20:
                        self.interfaces[dev_name]["tx_history"].pop(0)
                    self.interfaces[dev_name]["tx_history"].append(self.interfaces[dev_name]["tabytes"])
        if len(self.interfaces["Sum Interface"]["rx_history"]) == 20:
            self.interfaces["Sum Interface"]["rx_history"].pop(0)
        self.interfaces["Sum Interface"]["rx_history"].append(sum_rx_history)
        if len(self.interfaces["Sum Interface"]["tx_history"]) == 20:
            self.interfaces["Sum Interface"]["tx_history"].pop(0)
        self.interfaces["Sum Interface"]["tx_history"].append(sum_tx_history)
        for device_group in ifcfg_str.split("\n\n"):
            device_lines = device_group.split("\n")
            if "Kernel" in device_lines[0]:
                device_lines = device_lines[1:]
            dev_name = re.split('[\W]+', device_lines[0].strip().replace( ":", "_" ))[0]
            if len(device_lines) > 2 and not dev_name == "loaa" and not dev_name == "wmaster0aa":
                devices.append(dev_name)
        for device in self.interfaces.keys():
            if not device in devices and not "Sum Interface" in device and not "Multi Interface" in device:
                ''' The device does not exist, remove it. '''
                self.interfaces.pop(device)
                self.regenerate = True
        return True


class AppletBandwidthMonitor:
    curY = 0
    curX = 0
    shadow_offset = 2
    locale_lang = "en"
    counter = 0
    show_title = False
    text_shadow = (0.0, 0.0, 0.0, 0.8)
    text_forground = (1.0, 1.0, 1.0, 1.0)

    def __init__(self, applet):
        self.applet = applet
        self.UI_FILE = UI_FILE
        applet.tooltip.set("Bandwidth Monitor")
        icon = gtk.gdk.pixbuf_new_from_file(APPLET_PATH + '/images/blank.png')
        self.width = int(self.applet.get_size() * 1.5)
        self.height = int(self.applet.get_size() * 1.5)
        if self.height != icon.get_height():
            icon = icon.scale_simple(self.height, self.height, gtk.gdk.INTERP_BILINEAR)
            self.applet.set_icon_pixbuf(icon)
        self.dialog = applet.dialog.new("main")
        self.vbox = gtk.VBox()
        self.dialog.add(self.vbox)
        button = gtk.Button("Change Unit")
        button.connect("clicked", self.change_unit)
        self.dialog.add(button)
        defaults = {'unit': 8, 'interface': 'wlan0', 'draw_threshold': 0.0, 'device_display_parameters': []}
        self.applet.settings.load(defaults)
        self.interface = self.applet.settings['interface']
        self.unit = self.applet.settings['unit']
        if not self.unit:
            self.change_unit(defaults['unit'])
        if self.applet.settings['draw_threshold'] == 0.0:
            self.ratio = 1
        else:
            ratio = self.applet.settings['draw_threshold']
            self.ratio = int(ratio*1024) if self.unit == 1 else int(ratio*1024/8)
        self.preferences = bwmprefs.preferences(self.applet, self)
        self.device_usage = DeviceUsage(self, self.unit)
        applet.tooltip.connect_becomes_visible(self.enter_notify)
        self.table = self.generate_table()
        self.vbox.add(self.table)
        self.__upload_overlay = awn.OverlayText()
        self.__download_overlay = awn.OverlayText()
        self.__upload_overlay.props.gravity = gtk.gdk.GRAVITY_NORTH
        self.__download_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH
        applet.add_overlay(self.__upload_overlay)
        applet.add_overlay(self.__download_overlay)
        self.__upload_overlay.props.y_override = 4
        self.__download_overlay.props.y_override = 18
        self.__upload_overlay.props.apply_effects = True
        self.__download_overlay.props.apply_effects = True
        self.__upload_overlay.props.text = "Scanning"
        self.__download_overlay.props.text = "Devices"
        self.preferences.setup()
        gobject.timeout_add(100, self.first_paint)
        self.timer = gobject.timeout_add(800, self.subsequent_paint)

    def setup_context_menu(self):
        prefs_ui = gtk.Builder()
        prefs_ui.add_from_file(UI_FILE)
        preferences_vbox = self.applet.dialog.new("preferences").vbox
        cell_box = self.preferences.setup()
        store = cell_box.liststore
        scaleThresholdSpinbutton = prefs_ui.get_object("scaleThresholdSpinbutton")
        thresholdLabel = prefs_ui.get_object("label-scaleThreshold")
        scaleThresholdSpinbutton.set_value(float(self.applet.settings["draw_threshold"]))
        scaleThresholdSpinbutton.connect('value-changed', self.change_draw_ratio)
        uomCheckbutton = prefs_ui.get_object('uomCheckbutton')
        if self.unit == 1:
            uomCheckbutton.set_property('active', True)
            thresholdLabel.set_text("KBps")
        else:
            thresholdLabel.set_text("Kbps")
        uomCheckbutton.connect('toggled', self.change_unit, scaleThresholdSpinbutton, thresholdLabel)
        for device in sorted(self.device_usage.interfaces):
            if not "Multi Interface" in device and not "Sum Interface" in device:
                if self.device_usage.interfaces[device]['include_in_sum'] == True:
                    include_in_sum = 1
                else:
                    include_in_sum = 0
                if self.device_usage.interfaces[device]['include_in_multi'] == True:
                    include_in_multi = 1
                else:
                    include_in_multi = 0
                current_iter = store.append([device, include_in_sum, include_in_multi, '', '', '#f00', '#ff0'])
        prefs_ui.get_object("scrolledwindow1").add_with_viewport(cell_box)
        prefs_ui.get_object("dialog-notebook").reparent(preferences_vbox)

    def change_draw_ratio(self, widget):
        ratio = widget.get_value()
        if self.unit == 1:
            self.ratio = int(ratio*1024)
        else:
            self.ratio = int(ratio*1024/8)
        self.applet.settings["draw_threshold"] = ratio

    def change_unit(self, widget=None, scaleThresholdSpinbutton=None, label=None):
        self.unit = 8 if self.unit == 1 else 1
        if label:
            if self.unit == 1:
                label.set_text("KBps")
                scaleThresholdSpinbutton.set_value(self.applet.settings["draw_threshold"]/8)
            else:
                label.set_text("Kbps")
                scaleThresholdSpinbutton.set_value(self.applet.settings["draw_threshold"]*8)
        self.applet.settings["unit"] = self.unit

    def change_interface(self, widget, interface):
        if widget.get_active():
            ''' Changed to interface %s" % interface '''
            self.interface = interface
            self.applet.settings["interface"] = interface

    def generate_table(self):
        table = gtk.Table(100, 100, False)
        col_iter = 0
        row_iter = 2
        for i in range(0, 7):
            table.set_col_spacing(i, 20)
        table.attach(gtk.Label(""), 0, 1, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Interface"), 1, 2, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Status"), 2, 3, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Sent"), 3, 4, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Received"), 4, 5, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Sending"), 5, 6, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Receiving"), 6, 7, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        radio = None
        for interface_name in sorted(self.device_usage.interfaces):
            widget = gtk.Label()
            widget.toggle = gtk.RadioButton(group=radio)
            radio = widget.toggle
            if interface_name == self.interface:
                widget.toggle.set_active(True)
            widget.toggle.connect("clicked", self.change_interface, interface_name)
            widget.name_label = gtk.Label(str(interface_name))
            widget.status_label = gtk.Label(str(status(self.device_usage.interfaces[interface_name]["status"])))
            if self.device_usage.interfaces[interface_name]["ip_address"] != "":
                widget.status_label.set_tooltip_text("IP Address: %s\nNetmask: %s" % (self.device_usage.interfaces[interface_name]["ip_address"], self.device_usage.interfaces[interface_name]["netmask"]))
            else:
                widget.status_label.set_tooltip_text("")
            widget.sent_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_sum"], self.unit, False).strip()))
            widget.received_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_sum"], self.unit, False).strip()))
            widget.tx_speed_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_bytes"] * self.unit, self.unit).strip()))
            widget.rx_speed_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_bytes"] * self.unit, self.unit).strip()))
            self.device_usage.interfaces[interface_name]["widget"] = widget
            for widget_object in [widget.toggle, widget.name_label, widget.status_label, widget.sent_label, widget.received_label, widget.tx_speed_label, widget.rx_speed_label]:
                table.attach(widget_object, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
                col_iter += 1
            row_iter += 1
            col_iter = 0
        return table

    def enter_notify(self):
        if not self.applet.dialog.is_visible("main"):
            if not self.interface in self.device_usage.interfaces:
                self.applet.set_tooltip_text("Please sleect a valid Network Device")
            else:
                self.applet.set_tooltip_text("Total Sent: %s - Total Received: %s (All Interfaces)" % (readable_speed(self.device_usage.interfaces[self.interface]["tx_sum"] * self.unit, self.unit, False), readable_speed(self.device_usage.interfaces[self.interface]["rx_sum"] * self.unit, self.unit, False)))

    def first_paint(self):
        self.repaint()
        return False

    def subsequent_paint(self):
        self.repaint()
        ''' force garbage collect. I think Python's GC doesn't take the size of the
            unreferenced objects into consideration when deciding what/when to release
            to the OS, and the Pixbufs can get pretty large. Hopefully this doesn't
            kill the CPU. '''
        self.counter = self.counter + 1
        if self.counter % 20 == 0:
            gc.collect()
        return True

    def draw_background(self, ct, x0, y0, x1, y1, radius):
        ct.set_source_rgba(0.1, 0.1, 0.1, 0.5)
        ct.move_to(x0, y0 + radius)
        ct.curve_to(x0, y0, x0, y0, x0 + radius, y0)
        ct.line_to(x1 - radius, y0)
        ct.curve_to(x1, y0, x1, y0, x1, y0 + radius)
        ct.line_to(x1, y1 - radius)
        ct.curve_to(x1, y1, x1, y1, x1 - radius, y1)
        ct.line_to(x0 + radius, y1)
        ct.curve_to(x0, y1, x0, y1, x0, y1 - radius)
        ct.close_path()

    def draw_meter(self, ct, height, interface, multi=False):
        ratio = self.ratio
        ct.set_line_width(2)
        ''' Create temporary lists to store the values of the transmit and receive history, which will be
            then placed into the tmp_total_history and sorted by size to set the proper scale/ratio for the line heights '''
        tmp_rx_history = [1]
        tmp_tx_history = [1]
        tmp_total_history = [1]
        if not multi:
            if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["rx_history"]) > 0:
                tmp_rx_history = list(self.device_usage.interfaces[interface]["rx_history"])
            if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["tx_history"]) > 0:
                tmp_tx_history = list(self.device_usage.interfaces[interface]["tx_history"])
            tmp_total_history.extend(tmp_rx_history)
            tmp_total_history.extend(tmp_tx_history)
        else:
            for iface in self.device_usage.interfaces:
                if self.device_usage.interfaces[iface]['include_in_multi'] == True and len(self.device_usage.interfaces[iface]["rx_history"]) > 0:
                    tmp_total_history.extend(list(self.device_usage.interfaces[iface]["rx_history"]))
                if self.device_usage.interfaces[iface]['include_in_multi'] == True and len(self.device_usage.interfaces[iface]["tx_history"]) > 0:
                    tmp_total_history.extend(list(self.device_usage.interfaces[iface]["tx_history"]))
        tmp_total_history.sort()
        ''' ratio variable controls the minimum threshold for data - i.e. 32000 would not draw graphs
            for data transfers below 3200 bytes - the initial value of ratio if set to the link speed will
            prevent the graph from scaling. If using the Multi Interface, the ratio will adjust based on the 
            highest throughput metric. '''
        highest_value = tmp_total_history[len(tmp_total_history) - 1]
        ratio = int(highest_value) / 28 if highest_value > self.ratio else self.ratio
        ''' Change the color of the line to red for upload '''
        color = gtk.gdk.Color(self.device_usage.interfaces[interface]['upload_color'])
        ct.set_source_rgba(color.red_float, color.green_float, color.blue_float, 1.0)
        ''' reset the position and iter to 0 '''
        x_pos = 0
        cnt = 0
        ''' If a transmit history exists, draw it '''
        if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["tx_history"]) > 0:
            for value in self.device_usage.interfaces[interface]["tx_history"]:
                ct.line_to(x_pos, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += self.width / 16
                if cnt == 18:
                    x_pos += 4
                cnt += 1
            ct.close_path()
            ct.stroke()
        ''' Set the color to yellow for download and set the width of the line '''
        color = gtk.gdk.Color(self.device_usage.interfaces[interface]['download_color'])
        ct.set_source_rgba(color.red_float, color.green_float, color.blue_float, 1.0)
        ''' Set the initial position and iter to 0 '''
        x_pos = 0
        cnt = 0
        ''' If a receive history exists, draw it '''
        if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["rx_history"]) > 0:
            for value in self.device_usage.interfaces[interface]["rx_history"]:
                ct.line_to(x_pos, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += self.width / 16
                if cnt == 18:
                    x_pos += 4
                cnt += 1
            ct.close_path()
            ct.stroke()

    def chart_coords(self, value, ratio=0):
        ''' Speed varable will eventually become link speed if specified/detected for non-scaling graphs '''
        speed = 64
        pos = (speed - 20) / float(self.applet.get_size())
        return (self.applet.get_size() - pos * (value / ratio)) + 1

    def repaint(self):
        self.curY = 0
        self.width = int(self.applet.get_size() * 1.5)
        now = datetime.now()
        cs = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.applet.get_size())
        ct = cairo.Context(cs)
        ct.set_source_surface(cs)
        ct.set_line_width(1)
        ct.set_source_rgba(0.1, 0.1, 0.1, 0.5)
        self.draw_background(ct, 2, 2, self.width - 2, self.applet.get_size(), 12)
        ct.fill()
        if self.interface == "Multi Interface":
            tmp_history = [1]
            for interface in self.device_usage.interfaces:
                if self.device_usage.interfaces[interface]['include_in_multi'] == True:
                    tmp_history.extend( list(self.device_usage.interfaces[interface]["rx_history"]) )
                    tmp_history.extend( list(self.device_usage.interfaces[interface]["tx_history"]) )
            tmp_history.sort()
            highest_value = tmp_history[len(tmp_history) - 1]
            ratio = int(highest_value) / 28 if highest_value > self.ratio else 1
            for interface in self.device_usage.interfaces:
                if self.device_usage.interfaces[interface]['include_in_multi'] == True:
                    self.draw_meter(ct, self.applet.get_size(), interface, True)
        else:
            self.draw_meter(ct, self.applet.get_size(), self.interface)
        if not self.interface in self.device_usage.interfaces:
            self.__upload_overlay.props.text = "No"
            self.__download_overlay.props.text = "Device"
            self.title_text = "Please select a valid device"
        else:
            self.__download_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["rx_bytes"], self.unit).strip()
            self.__upload_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit).strip()
            self.title_text = readable_speed(self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit)
        self.applet.set_icon_context(ct)
        if self.applet.dialog.is_visible("main"):
            for interface_name in self.device_usage.interfaces:
                if not "widget" in self.device_usage.interfaces[interface_name] or self.device_usage.regenerate == True:
                    self.device_usage.regenerate = False
                    self.vbox.remove(self.table)
                    self.table = self.generate_table()
                    self.vbox.add(self.table)
                    self.vbox.show_all()
                self.device_usage.interfaces[interface_name]["widget"].rx_speed_label.set_text(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_bytes"], self.unit).strip()))
                self.device_usage.interfaces[interface_name]["widget"].tx_speed_label.set_text(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_bytes"], self.unit).strip()))
                self.device_usage.interfaces[interface_name]["widget"].sent_label.set_text(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_sum"] * self.unit, self.unit, False).strip()))
                self.device_usage.interfaces[interface_name]["widget"].received_label.set_text(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_sum"] * self.unit, self.unit, False).strip()))
                self.device_usage.interfaces[interface_name]["widget"].status_label.set_text(str(status(self.device_usage.interfaces[interface_name]["status"])))
                if self.device_usage.interfaces[interface_name]["ip_address"] != "":
                    self.device_usage.interfaces[interface_name]["widget"].status_label.set_tooltip_text("IP Address: %s\nNetmask: %s" % (self.device_usage.interfaces[interface_name]["ip_address"], self.device_usage.interfaces[interface_name]["netmask"]))
                else:
                    self.device_usage.interfaces[interface_name]["widget"].status_label.set_tooltip_text("")
        return True


def readable_speed(speed, unit, seconds=True):
    ''' readable_speed(speed) -> string
        speed is in bytes per second
        returns a readable version of the speed given '''
    speed = 0 if speed is None or speed < 0 else speed
    units = ["B ", "KB", "MB", "GB", "TB"] if unit == 1 else ["b ", "Kb", "Mb", "Gb", "Tb"]
    if seconds:
        temp_units = []
        for u in units:
            temp_units.append("%sps" % u.strip())
        units = temp_units
    step = 1L
    for u in units:
        if step > 1:
            s = "%4.2f " % (float(speed) / step)
            if len(s) <= 5:
                return s + u
            s = "%4.2f " % (float(speed) / step)
            if len(s) <= 5:
                return s + u
        if speed / step < 1024:
            return "%4.1d " % (speed / step) + u
        step = step * 1024L
    return "%4.1d " % (speed / (step / 1024)) + units[-1]


def status(flags):
    if "V" in flags:
        status = "Virtual"
    elif "R" in flags and "U" in flags:
        status = "Connected"
    elif "R" in flags:
        status = "Down"
    else:
        status = "Disconnected"
    return status


def sort_dictionary_keys(dict):
    keys = dict.keys()
    keys.sort()
    return map(dict.get, keys)

if __name__ == "__main__":
    awnlib.init_start(AppletBandwidthMonitor, {"name": APPLET_NAME,
        "short": "bwm",
        "version": APPLET_VERSION,
        "description": APPLET_DESCRIPTION,
        "logo": APPLET_ICON,
        "author": "Kyle L. Huff",
        "copyright-year": "2009",
        "authors": APPLET_AUTHORS})
