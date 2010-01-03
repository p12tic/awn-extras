#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
bandwidth-monitor - Network bandwidth monitor.
Copyright (c) 2006-2009 Kyle L. Huff (awn-bwm@curetheitch.com)
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

from awn.extras import awnlib, __version__
import gobject
import gc
import cairo
from StringIO import StringIO
import bwmprefs

APPLET_NAME = "Bandwidth Monitor"
APPLET_VERSION = "0.3.9.2"
APPLET_COPYRIGHT = "© 2006-2009 CURE|THE|ITCH"
APPLET_AUTHORS = ["Kyle L. Huff <awn-bwm@curetheitch.com>"]
APPLET_DESCRIPTION = "Network Bandwidth monitor"
APPLET_WEBSITE = "http://www.curetheitch.com/projects/awn-bwm/"
APPLET_PATH = os.path.dirname(sys.argv[0])
APPLET_ICON = APPLET_PATH + "/images/icon.png"
UI_FILE = os.path.join(os.path.dirname(__file__), "bandwidth-monitor.ui")


class DeviceUsage:

    def __init__(self, parent, unit):
        self.parent = parent
        self.interfaces = {}
        self.interfaces["Sum Interface"] = {"collection_time": 0,
            "status": "V",
            "prbytes": 0,
            "ptbytes": 0,
            "index": 1,
            "rx_history": [0, 0],
            "tx_history": [0, 0],
            "rx_bytes": 0,
            "tx_bytes": 0,
            "rx_sum": 0,
            "tx_sum": 0,
            "rxtx_sum": 0,
            "rabytes": 0,
            "tabytes": 0,
            'include_in_sum': False,
            'include_in_multi': False,
            'upload_color': "#ff0000",
            'download_color': "#ffff00"}
        self.interfaces["Multi Interface"] = {"collection_time": 0,
            "status": "V",
            "prbytes": 0,
            "ptbytes": 0,
            "index": 1,
            "rx_history": [0, 0],
            "tx_history": [0, 0],
            "rx_bytes": 0,
            "tx_bytes": 0,
            "rx_sum": 0,
            "tx_sum": 0,
            "rxtx_sum": 0,
            "rabytes": 0,
            "tabytes": 0,
            'include_in_sum': False,
            'include_in_multi': False}
        self.regenerate = False
        self.update_net_stats()
        self.timeout_add_seconds(1, self.update_net_stats)

    def timeout_add_seconds(self, seconds, callback):
        if hasattr(gobject, 'timeout_add_seconds'):
            return gobject.timeout_add_seconds(seconds, callback)
        else:
            return gobject.timeout_add(seconds * 1000, callback)

    def update_net_stats(self):
        ifcfg_str = os.popen("netstat -eia").read()
        if ifcfg_str:
            ifcfg_str = ifcfg_str.split("\n\n")
        stat_str = "n"
        devices = []
        ''' Reset the Sum Interface records to zero '''
        self.interfaces["Sum Interface"]["rx_sum"] = 0
        self.interfaces["Sum Interface"]["tx_sum"] = 0
        self.interfaces["Sum Interface"]["rx_bytes"] = 0
        self.interfaces["Sum Interface"]["tx_bytes"] = 0
        sum_rx_history = 0.0
        sum_tx_history = 0.0
        ''' Reset the Multi Interface records to zero '''
        self.interfaces["Multi Interface"]["rx_sum"] = 0
        self.interfaces["Multi Interface"]["tx_sum"] = 0
        self.interfaces["Multi Interface"]["rx_bytes"] = 0
        self.interfaces["Multi Interface"]["tx_bytes"] = 0
        multi_rx_history = 0.0
        multi_tx_history = 0.0
        if ifcfg_str and stat_str:
            for device_group in ifcfg_str:
                device_lines = device_group.split("\n")
                if "Kernel" in device_lines[0]:
                    device_lines = device_lines[1:]
                dev_name = re.split('[\W]+',
                    device_lines[0].strip().replace(":", "_"))[0]
                if len(device_lines) > 2:
                    try:
                        rx_bytes = float(re.search(r'RX bytes:(\d+)\D',
                            device_group).group(1))
                        tx_bytes = float(re.search(r'TX bytes:(\d+)\D',
                            device_group).group(1))
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
                                include_in_sum = device_pref_values[1].__str__()[0].upper() == 'T'
                                include_in_multi = device_pref_values[2].__str__()[0].upper() == 'T'
                        self.interfaces[dev_name] = {"collection_time": time.time(),
                            "status": None,
                            "prbytes": rx_bytes,
                            "ptbytes": tx_bytes,
                            "index": 1,
                            "rx_history": [0, 0],
                            "tx_history": [0, 0],
                            "include_in_sum": include_in_sum,
                            'include_in_multi': include_in_multi,
                            'upload_color': self.parent.preferences.get_color(dev_name, "upload"),
                            'download_color': self.parent.preferences.get_color(dev_name, "download")}
                    collection = (time.time() - self.interfaces[dev_name]["collection_time"])
                    rbytes = ((rx_bytes - self.interfaces[dev_name]["prbytes"]) * self.parent.unit) / collection
                    tbytes = ((tx_bytes - self.interfaces[dev_name]["ptbytes"]) * self.parent.unit) / collection
                    rabytes = (rx_bytes - self.interfaces[dev_name]["prbytes"]) / collection
                    tabytes = (tx_bytes - self.interfaces[dev_name]["ptbytes"]) / collection
                    self.interfaces[dev_name]["rabytes"] = rabytes
                    self.interfaces[dev_name]["tabytes"] = tabytes
                    rxtx_sum = rx_bytes + tx_bytes
                    if self.interfaces[dev_name]['include_in_sum']:
                        self.interfaces["Sum Interface"]["rx_sum"] += rx_bytes
                        self.interfaces["Sum Interface"]["tx_sum"] += tx_bytes
                        self.interfaces["Sum Interface"]["rx_bytes"] += rbytes
                        self.interfaces["Sum Interface"]["tx_bytes"] += tbytes
                        sum_rx_history += rabytes
                        sum_tx_history += tabytes
                    if self.interfaces[dev_name]['include_in_multi']:
                        self.interfaces["Multi Interface"]["rx_sum"] += rx_bytes
                        self.interfaces["Multi Interface"]["tx_sum"] += tx_bytes
                        self.interfaces["Multi Interface"]["rx_bytes"] += rbytes
                        self.interfaces["Multi Interface"]["tx_bytes"] += tbytes
                        multi_rx_history += rabytes
                        multi_tx_history += tabytes
                    ifstatus = "BRMU"
                    self.interfaces[dev_name]["rx_bytes"] = rbytes
                    self.interfaces[dev_name]["tx_bytes"] = tbytes
                    self.interfaces[dev_name]["prbytes"] = rx_bytes
                    self.interfaces[dev_name]["ptbytes"] = tx_bytes
                    self.interfaces[dev_name]["rx_sum"] = rx_bytes
                    self.interfaces[dev_name]["tx_sum"] = tx_bytes
                    self.interfaces[dev_name]["rxtx_sum"] = rxtx_sum
                    self.interfaces[dev_name]["status"] = ifstatus
                    self.interfaces[dev_name]["collection_time"] = time.time()
                    offset = self.parent.meter_scale - 1 if self.parent.border else self.parent.meter_scale
                    self.interfaces[dev_name]["rx_history"] = self.interfaces[dev_name]["rx_history"][- offset:]
                    self.interfaces[dev_name]["rx_history"].append(self.interfaces[dev_name]["rabytes"])
                    self.interfaces[dev_name]["tx_history"] = self.interfaces[dev_name]["tx_history"][- offset:]
                    self.interfaces[dev_name]["tx_history"].append(self.interfaces[dev_name]["tabytes"])
                    devices.append(dev_name)
        self.interfaces["Sum Interface"]["rx_history"] = self.interfaces["Sum Interface"]["rx_history"][- offset:]
        self.interfaces["Sum Interface"]["rx_history"].append(sum_rx_history)
        self.interfaces["Sum Interface"]["tx_history"] = self.interfaces["Sum Interface"]["tx_history"][- offset:]
        self.interfaces["Sum Interface"]["tx_history"].append(sum_tx_history)
        for device in self.interfaces.keys():
            if not device in devices and not "Sum Interface" in device and not "Multi Interface" in device:
                ''' The device does not exist, remove it. (del dictionary[key] is faster than dictionary.pop(key) '''
                del self.interfaces[device]
                self.regenerate = True
        return True


class AppletBandwidthMonitor:
    text_shadow = (0.0, 0.0, 0.0, 0.8)
    text_forground = (1.0, 1.0, 1.0, 1.0)

    def __init__(self, applet):
        ''' Test if user has access to /proc/net/dev '''
        if not os.access('/proc/net/dev', os.R_OK):
            applet.errors.general('Cannot read from /proc/net/dev', 'Unable to retrieve statistics. Bandwith-Monitor will not function without read access to /proc/net/dev')
            applet.errors.set_error_icon_and_click_to_restart()
            return None
        self.applet = applet
        self.UI_FILE = UI_FILE
        applet.tooltip.set("Bandwidth Monitor")
        self.meter_scale = 20
        icon = gtk.gdk.pixbuf_new_from_file(APPLET_PATH + '/images/blank.png')
        width = self.applet.get_size() * 1.5
        height = self.applet.get_size() * 1.5
        if height != icon.get_height():
            icon = icon.scale_simple(int(height), int(height/1.5), gtk.gdk.INTERP_BILINEAR)
            self.applet.set_icon_pixbuf(icon)
        self.dialog = applet.dialog.new("main")
        self.vbox = gtk.VBox()
        self.dialog.add(self.vbox)
        button = gtk.Button("Change Unit")
        self.dialog.add(button)
        defaults = {'unit': 8, 'interface': '', 'draw_threshold': 0.0, 'device_display_parameters': [], 'background': True, 'background_color': "#000000|0.5", 'border': False, 'border_color': "#000000|1.0", 'label_control': 2, 'graph_zero': 0}
        self.applet.settings.load_preferences(defaults)
        self.interface = self.applet.settings['interface']
        self.unit = self.applet.settings['unit']
        self.label_control = self.applet.settings["label_control"]
        self.background = self.applet.settings['background']
        self.background_color = self.applet.settings['background_color']
        self.border = self.applet.settings['border']
        self.border_color = self.applet.settings['border_color']
        self.graph_zero = self.applet.settings['graph_zero']
        if not self.unit:
            self.change_unit(defaults['unit'])
        if self.applet.settings['draw_threshold'] == 0.0:
            self.ratio = 1
        else:
            ratio = self.applet.settings['draw_threshold']
            self.ratio = ratio*1024 if self.unit == 1 else ratio*1024/8
        self.preferences = bwmprefs.preferences(self.applet, self)
        self.device_usage = DeviceUsage(self, self.unit)
        applet.tooltip.connect_becomes_visible(self.enter_notify)
        self.table = self.generate_table()
        self.vbox.add(self.table)
        self.__upload_overlay = awn.OverlayText()
        self.__download_overlay = awn.OverlayText()
        self.__sum_overlay = awn.OverlayText()
        self.__upload_overlay.props.gravity = gtk.gdk.GRAVITY_NORTH
        self.__download_overlay.props.gravity = gtk.gdk.GRAVITY_SOUTH
        self.__sum_overlay.props.gravity = gtk.gdk.GRAVITY_NORTH
        applet.add_overlay(self.__upload_overlay)
        applet.add_overlay(self.__download_overlay)
        applet.add_overlay(self.__sum_overlay)
        self.__upload_overlay.props.y_override = 4
        self.__download_overlay.props.y_override = 18
        self.__sum_overlay.props.y_override = 11
        self.__upload_overlay.props.apply_effects = True
        self.__download_overlay.props.apply_effects = True
        self.__sum_overlay.props.apply_effects = True
        self.__upload_overlay.props.text = "Scanning"
        self.__download_overlay.props.text = "Devices"
        self.preferences.setup()
        ''' connect the left-click dialog button "Change Unit" to the call_change_unit function,
            which does not call self.change_unit directly, instead it toggles the "active" property of
            the checkbutton so everything that needs to happen, happens. '''
        button.connect("clicked", self.call_change_unit)
        gobject.timeout_add(100, self.first_paint)
        self.timer = gobject.timeout_add(800, self.subsequent_paint)

    def change_draw_ratio(self, widget):
        ratio = widget.get_value()
        self.ratio = ratio*1024 if self.unit == 1 else ratio*1024/8
        self.applet.settings["draw_threshold"] = ratio

    def call_change_unit(self, *args):
        if self.unit == 8:
            self.preferences.uomCheckbutton.set_property('active', True)
        else:
            self.preferences.uomCheckbutton.set_property('active', False)

    def change_unit(self, widget=None, scaleThresholdSpinbutton=None, label=None):
        self.unit = 8 if self.unit == 1 else 1
        ''' normalize and update the label, and normalize the spinbutton '''
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
        for i in [0, 1, 2, 3, 4, 5, 6]:
            table.set_col_spacing(i, 20)
        table.attach(gtk.Label(""), 0, 1, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Interface"), 1, 2, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Sent"), 2, 3, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Received"), 3, 4, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Sending"), 4, 5, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        table.attach(gtk.Label("Receiving"), 5, 6, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
        radio = None
        for interface_name in sorted(self.device_usage.interfaces):
            widget = gtk.Label()
            widget.toggle = gtk.RadioButton(group=radio)
            radio = widget.toggle
            if interface_name == self.interface:
                widget.toggle.set_active(True)
            widget.toggle.connect("clicked", self.change_interface, interface_name)
            widget.name_label = gtk.Label(str(interface_name))
            widget.sent_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_sum"], self.unit, False).strip()))
            widget.received_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_sum"], self.unit, False).strip()))
            widget.tx_speed_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_bytes"] * self.unit, self.unit).strip()))
            widget.rx_speed_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_bytes"] * self.unit, self.unit).strip()))
            self.device_usage.interfaces[interface_name]["widget"] = widget
            for widget_object in [widget.toggle, widget.name_label, widget.sent_label, widget.received_label, widget.tx_speed_label, widget.rx_speed_label]:
                table.attach(widget_object, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
                col_iter += 1
            row_iter += 1
            col_iter = 0
        return table

    def enter_notify(self):
        if not self.applet.dialog.is_visible("main"):
            if not self.interface in self.device_usage.interfaces:
                self.applet.set_tooltip_text("Please select a valid Network Device")
            else:
                self.applet.set_tooltip_text("Total Sent: %s - Total Received: %s (All Interfaces)" % (readable_speed(self.device_usage.interfaces[self.interface]["tx_sum"] * self.unit, self.unit, False), readable_speed(self.device_usage.interfaces[self.interface]["rx_sum"] * self.unit, self.unit, False)))

    def first_paint(self):
        self.repaint()
        return False

    def subsequent_paint(self):
        self.repaint()
        return True

    def draw_background(self, ct, x0, y0, x1, y1, radius):
        ct.move_to(x0, y0 + radius)
        ct.curve_to(x0, y0, x0, y0, x0 + radius, y0)
        ct.line_to(x1 - radius, y0)
        ct.curve_to(x1, y0, x1, y0, x1, y0 + radius)
        ct.line_to(x1, y1 - radius)
        ct.curve_to(x1, y1, x1, y1, x1 - radius, y1)
        ct.line_to(x0 + radius, y1)
        ct.curve_to(x0, y1, x0, y1, x0, y1 - radius)
        ct.close_path()

    def draw_meter(self, ct, width, height, interface, multi=False):
        ratio = self.ratio
        ct.set_line_width(2)
        ''' Create temporary lists to store the values of the transmit and receive history, which will be
            then placed into the tmp_total_history and sorted by size to set the proper scale/ratio for the line heights '''
        tmp_rx_history = [1]
        tmp_tx_history = [1]
        tmp_total_history = [1]
        if not multi:
            if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["rx_history"]):
                tmp_rx_history = self.device_usage.interfaces[interface]["rx_history"]
            if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["tx_history"]):
                tmp_tx_history = self.device_usage.interfaces[interface]["tx_history"]
            tmp_total_history.extend(tmp_rx_history)
            tmp_total_history.extend(tmp_tx_history)
        else:
            for iface in self.device_usage.interfaces:
                if self.device_usage.interfaces[iface]['include_in_multi'] and len(self.device_usage.interfaces[iface]["rx_history"]):
                    tmp_total_history.extend(self.device_usage.interfaces[iface]["rx_history"])
                if self.device_usage.interfaces[iface]['include_in_multi'] and len(self.device_usage.interfaces[iface]["tx_history"]):
                    tmp_total_history.extend(self.device_usage.interfaces[iface]["tx_history"])
        tmp_total_history.sort()
        ''' ratio variable controls the minimum threshold for data - i.e. 32000 would not draw graphs
            for data transfers below 3200 bytes - the initial value of ratio if set to the link speed will
            prevent the graph from scaling. If using the Multi Interface, the ratio will adjust based on the
            highest throughput metric. '''
        highest_value = tmp_total_history[-1]
        ratio = highest_value / 28 if highest_value > self.ratio else self.ratio
        ''' Change the color of the upload line to the configured or default '''
        if interface:
            color = gtk.gdk.Color(self.device_usage.interfaces[interface]['upload_color'])
            ct.set_source_rgba(color.red_float, color.green_float, color.blue_float, 1.0)
        else:
            ct.set_source_rgba(0.1, 0.1, 0.1, 0.5)
        ''' Set the initial position and iter to 0 '''
        x_pos = 2 if self.border else 0
        cnt = 0
        ''' If a transmit history exists, draw it '''
        if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["tx_history"]):
            for value in self.device_usage.interfaces[interface]["tx_history"]:
                x_pos_end = (x_pos - width) + 2 if self.border and x_pos > width else 0
                ct.line_to(x_pos - x_pos_end, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += width / self.meter_scale
                cnt += 1
            ct.close_path()
            ct.stroke()
        ''' Change the color of the download line to the configured or default '''
        if interface:
            color = gtk.gdk.Color(self.device_usage.interfaces[interface]['download_color'])
            ct.set_source_rgba(color.red_float, color.green_float, color.blue_float, 1.0)
        else:
            ct.set_source_rgba(0.1, 0.1, 0.1, 0.5)
        ''' Reset the position and iter to 0 '''
        x_pos = 2 if self.border else 0
        cnt = 0
        ''' If a receive history exists, draw it '''
        if interface in self.device_usage.interfaces and len(self.device_usage.interfaces[interface]["rx_history"]):
            for value in self.device_usage.interfaces[interface]["rx_history"]:
                x_pos_end = (x_pos - width) + 2 if self.border and x_pos > width else 0
                ct.line_to(x_pos - x_pos_end, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += width / self.meter_scale
                cnt += 1
            ct.close_path()
            ct.stroke()

    def chart_coords(self, value, ratio=1):
        ratio = 1 if ratio < 1 else ratio
        pos = float(self.applet.get_size()) / 58
        bottom = 2.0 if self.border else 0
        return (self.applet.get_size() - pos * (value / int(ratio))) + self.graph_zero - bottom

    def repaint(self):
        orientation = self.applet.get_pos_type()
        if orientation in (gtk.POS_LEFT, gtk.POS_RIGHT):
            width = self.applet.get_size()
            self.__upload_overlay.props.font_sizing = 9
            self.__download_overlay.props.font_sizing = 9
            self.__sum_overlay.props.font_sizing = 9
        else:
            width = self.applet.get_size() * 1.5
        cs = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width), self.applet.get_size())
        ct = cairo.Context(cs)
        ct.set_source_surface(cs)
        ct.set_line_width(2)
        if self.background:
            bgColor, alpha = self.applet.settings["background_color"].split("|")
            bgColor = gtk.gdk.Color(bgColor)
            ct.set_source_rgba(bgColor.red_float, bgColor.green_float, bgColor.blue_float, float(alpha))
            self.draw_background(ct, 0, 0, width, self.applet.get_size(), 10)
            ct.fill()
        if self.interface == "Multi Interface":
            tmp_history = [1]
            for interface in self.device_usage.interfaces:
                if self.device_usage.interfaces[interface]['include_in_multi']:
                    tmp_history.extend(self.device_usage.interfaces[interface]["rx_history"])
                    tmp_history.extend(self.device_usage.interfaces[interface]["tx_history"])
            tmp_history.sort()
            highest_value = tmp_history[-1]
            ratio = highest_value / 28 if highest_value > self.ratio else 1
            for interface in self.device_usage.interfaces:
                if self.device_usage.interfaces[interface]['include_in_multi']:
                    self.draw_meter(ct, width, self.applet.get_size(), interface, True)
        else:
            self.draw_meter(ct, width, self.applet.get_size(), self.interface)
        if self.interface in self.device_usage.interfaces:
            if self.label_control:
                if self.label_control == 2:
                    self.__sum_overlay.props.text = ""
                    self.__download_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["rx_bytes"], self.unit).strip()
                    self.__upload_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit).strip()
                else:
                    self.__upload_overlay.props.text = ""
                    self.__download_overlay.props.text = ""
                    self.__sum_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["rx_bytes"]+self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit).strip()
            else:
                    self.__upload_overlay.props.text = ""
                    self.__download_overlay.props.text = ""
                    self.__sum_overlay.props.text = ""
            self.title_text = readable_speed(self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit)
        else:
            self.__upload_overlay.props.text = "No"
            self.__download_overlay.props.text = "Device"
            self.title_text = "Please select a valid device"
        if self.border:
            line_width = 2
            ct.set_line_width(line_width)
            borderColor, alpha = self.applet.settings["border_color"].split("|")
            borderColor = gtk.gdk.Color(borderColor)
            ct.set_source_rgba(borderColor.red_float, borderColor.green_float, borderColor.blue_float, float(alpha))
            self.draw_background(ct, line_width/2, line_width/2, width - line_width/2, self.applet.get_size() - line_width/2, 4)
            ct.stroke()
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
        "short": "bandwidth-monitor",
        "version": __version__,
        "description": APPLET_DESCRIPTION,
        "logo": APPLET_ICON,
        "author": "Kyle L. Huff",
        "copyright-year": "2009",
        "authors": APPLET_AUTHORS})
