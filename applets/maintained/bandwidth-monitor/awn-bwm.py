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

APPLET_NAME = "Bandwidth Monitor"
APPLET_VERSION = "0.3.9.2"
APPLET_COPYRIGHT = "© 2006-2009 CURE|THE|ITCH"
APPLET_AUTHORS = ["Kyle L. Huff <kyle.huff@curetheitch.com>"]
APPLET_DESCRIPTION = "Network Bandwidth monitor"
APPLET_WEBSITE = "http://www.curetheitch.com/projects/awn-bwm/"
APPLET_PATH = os.path.dirname(sys.argv[0])
APPLET_ICON = APPLET_PATH + "/images/icon.png"


class DeviceUsage:

    def __init__(self, parent, unit):
        self.parent = parent
        self.statistics_cmd = "netstat -ia"
        self.interfaces = {}
        self.devices_cmd = "netstat -ei"
        self.regenerate = False
        self.update_net_stats()
        gobject.timeout_add(1000, self.update_net_stats)

    def update_net_stats(self):
        delta = time.time()
        ifcfg_str = os.popen(self.devices_cmd).read()
        stat_str = os.popen(self.statistics_cmd).readlines()
        device_list = os.popen('netstat -i').readlines()
        device_list = device_list[2:]
        devices = []
        if ifcfg_str and stat_str:
            for device_group in ifcfg_str.split("\n\n"):
                device_lines = device_group.split("\n")
                if "Kernel" in device_lines[0]:
                    device_lines = device_lines[1:]
                dev_name = re.split('[\W]+', device_lines[0].strip())[0]
                if len(device_lines) > 4 and not dev_name == "lo" and not dev_name == "wmaster0":
                    rx_bytes = int(re.search(r'RX bytes:(\d+)\D', device_group).group(1))
                    tx_bytes = int(re.search(r'TX bytes:(\d+)\D', device_group).group(1))
                    if not dev_name in self.interfaces:
                        self.interfaces[dev_name] = {"collection_time": time.time(), "status": None, "prbytes": float(rx_bytes), "ptbytes": float(tx_bytes), "index": 1, "rx_history": [0,0], "tx_history": [0,0], "ip_address": '', "netmask": ''}
                    address = re.search(r'inet addr: (\d+\.\d+\.\d+\.\d+)\b', device_group)
                    if address:
                        address = address.group(1)
                        netmask = re.search(r'Mask: (\d+\.\d+\.\d+\.\d+)\b', device_group).group(1)
                        self.interfaces[dev_name]["ip_address"], self.interfaces[dev_name]["netmask"] = address, netmask
                    collection = (time.time() - self.interfaces[dev_name]["collection_time"])
                    rbytes = ((float(rx_bytes) - self.interfaces[dev_name]["prbytes"]) * self.parent.unit) / collection
                    tbytes = ((float(tx_bytes) - self.interfaces[dev_name]["ptbytes"]) * self.parent.unit) / collection
                    rabytes = (float(rx_bytes) - self.interfaces[dev_name]["prbytes"]) / collection
                    tabytes = (float(tx_bytes) - self.interfaces[dev_name]["ptbytes"]) / collection
                    self.interfaces[dev_name]["rabytes"] = rabytes
                    self.interfaces[dev_name]["tabytes"] = tabytes
                    index = ((((float(rx_bytes) - self.interfaces[dev_name]["prbytes"]) * self.parent.unit) / collection) + (((float(tx_bytes) - self.interfaces[dev_name]["ptbytes"]) * self.parent.unit) / collection)) + self.interfaces[dev_name]["index"]
                    rxtx_sum = float(rx_bytes) + float(tx_bytes)
                    ''' The whole index thing is to not collect statistics on ever single read, because on some systems, /proc/net/dev is only updated every 2 seconds '''
                    if index > -2:
                        if index == 0:
                            self.interfaces[dev_name]["index"] = -1
                            continue
                        elif index == -1:
                            self.interfaces[dev_name]["index"] = -2
                        else:
                            self.interfaces[dev_name]["index"] = 0
                    for dev_line in stat_str:
                        if dev_name in dev_line and not ":" in dev_line:
                            ifstatus = re.split('[\W]+', dev_line.strip())[11]
                    self.interfaces[dev_name]["rx_bytes"], self.interfaces[dev_name]["tx_bytes"], self.interfaces[dev_name]["prbytes"], self.interfaces[dev_name]["ptbytes"], self.interfaces[dev_name]["rx_sum"], self.interfaces[dev_name]["tx_sum"], self.interfaces[dev_name]["rxtx_sum"], self.interfaces[dev_name]["status"], self.interfaces[dev_name]["collection_time"] = float(rbytes), float(tbytes), float(rx_bytes), float(tx_bytes), float(rx_bytes), float(tx_bytes), float(rxtx_sum), ifstatus, time.time()
                    if len(self.interfaces[dev_name]["rx_history"]) == 20:
                        self.interfaces[dev_name]["rx_history"].pop(0)
                    self.interfaces[dev_name]["rx_history"].append(self.interfaces[dev_name]["rabytes"])
                    if len(self.interfaces[dev_name]["tx_history"]) == 20:
                        self.interfaces[dev_name]["tx_history"].pop(0)
                    self.interfaces[dev_name]["tx_history"].append(self.interfaces[dev_name]["tabytes"])
        for device_group in ifcfg_str.split("\n\n"):
            device_lines = device_group.split("\n")
            if "Kernel" in device_lines[0]:
                device_lines = device_lines[1:]
            dev_name = re.split('[\W]+', device_lines[0].strip())[0]
            if len(device_lines) > 4 and not dev_name == "lo" and not dev_name == "wmaster0":
                devices.append(dev_name)
        for device in self.interfaces.keys():
            if not device in devices:
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
        defaults = { "unit": 0, "interface": '', }
        self.applet.settings.load(defaults)
        self.interface = self.applet.settings["interface"]
        self.unit = self.applet.settings["unit"]
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
        gobject.timeout_add(100, self.first_paint)
        self.timer = gobject.timeout_add(1500, self.subsequent_paint)

    def close(self, dialog, res):
        if res == gtk.RESPONSE_CANCEL:
            dialog.destroy()

    def change_interface(self, widget, interface):
        if widget.get_active():
            ''' Changed to interface %s" % interface '''
            self.interface = interface
            self.applet.settings["interface"] = interface

    def generate_table(self):
        table = gtk.Table(100, 100, False)
        col_iter = 0
        row_iter = 2
        table.set_col_spacing(0, 20)
        table.set_col_spacing(1, 20)
        table.set_col_spacing(2, 20)
        table.set_col_spacing(3, 20)
        table.set_col_spacing(4, 20)
        table.set_col_spacing(5, 20)
        table.set_col_spacing(6, 20)
        table.attach(gtk.Label("Sum"), 0, 1, 0, 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
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
            widget.sent_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_sum"], self.unit, False).strip()))
            widget.received_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_sum"], self.unit, False).strip()))
            widget.tx_speed_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["tx_bytes"] * self.unit, self.unit).strip()))
            widget.rx_speed_label = gtk.Label(str(readable_speed(self.device_usage.interfaces[interface_name]["rx_bytes"] * self.unit, self.unit).strip()))
            self.device_usage.interfaces[interface_name]["widget"] = widget
            table.attach(widget.toggle, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            col_iter += 1
            table.attach(widget.name_label, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            col_iter += 1
            table.attach(widget.status_label, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            col_iter += 1
            table.attach(widget.sent_label, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            col_iter += 1
            table.attach(widget.received_label, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            col_iter += 1
            table.attach(widget.tx_speed_label, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            col_iter += 1
            table.attach(widget.rx_speed_label, col_iter, col_iter + 1, row_iter, row_iter + 1, xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.EXPAND | gtk.FILL, xpadding=0, ypadding=0)
            row_iter += 1
            col_iter = 0
        return table

    def change_unit(self, widget):
        self.unit = 8 if self.unit == 1 else 1
        self.applet.settings["unit"] = self.unit

    def enter_notify(self):
        if not self.applet.dialog.is_visible("main"):
            if not self.interface in self.device_usage.interfaces:
                self.applet.set_tooltip_text("Please sleect a valid Network Device") 
            else:
                self.applet.set_tooltip_text("Total Sent: %s - Total Received: %s" % (readable_speed(self.device_usage.interfaces[self.interface]["tx_sum"] * self.unit, self.unit, False), readable_speed(self.device_usage.interfaces[self.interface]["rx_sum"] * self.unit, self.unit, False)))

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

    def draw_meter(self, ct, height):
        ct.set_line_width(2)
        ''' Create temporary lists to store the values of the transmit and receive history, which will be
            then placed into the tmp_total_history and sorted by size to set the proper scale/ratio for the line heights '''
        tmp_rx_history = []
        tmp_tx_history = []
        tmp_total_history = []
        if self.interface in self.device_usage.interfaces and len(self.device_usage.interfaces[self.interface]["rx_history"]) > 0:
            tmp_rx_history = list(self.device_usage.interfaces[self.interface]["rx_history"])
        if self.interface in self.device_usage.interfaces and len(self.device_usage.interfaces[self.interface]["tx_history"]) > 0:
            tmp_tx_history = list(self.device_usage.interfaces[self.interface]["tx_history"])
        tmp_total_history.extend(tmp_rx_history)
        tmp_total_history.extend(tmp_tx_history)
        tmp_total_history.sort()
        ratio = 1
        if tmp_total_history:
            highest_value = tmp_total_history[len(tmp_total_history) - 1]
            if highest_value > ratio:
                ratio = int(highest_value) / 28
        ''' Change the color of the line to red for upload '''
        ct.set_source_rgba(1.0, 0.0, 0.0, 1.0)
        ''' reset the position and iter to 0 '''
        x_pos = 0
        cnt = 0
        ''' If a transmit history exists, draw it '''
        if self.interface in self.device_usage.interfaces and len(self.device_usage.interfaces[self.interface]["tx_history"]) > 0:
            for value in self.device_usage.interfaces[self.interface]["tx_history"]:
                ct.line_to(x_pos, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += self.width / 16
                if cnt == 18:
                    x_pos += 4
                cnt += 1
            ct.close_path()
            ct.stroke()
        ''' Set the color to yellow for download and set the width of the line '''
        ct.set_source_rgba(1.0, 0.8, 0.0, 1.0)
        ''' Set the initial position and iter to 0 '''
        x_pos = 0
        cnt = 0
        ''' If a receive history exists, draw it '''
        if self.interface in self.device_usage.interfaces and len(self.device_usage.interfaces[self.interface]["rx_history"]) > 0:
            for value in self.device_usage.interfaces[self.interface]["rx_history"]:
                ct.line_to(x_pos, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += self.width / 16
                if cnt == 18:
                    x_pos += 4
                cnt += 1
            ct.close_path()
            ct.stroke()

    def chart_coords(self, value, ratio=0):
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
        self.draw_meter(ct, self.applet.get_size())
        if not self.interface in self.device_usage.interfaces:
            self.__upload_overlay.props.text = "No"
            self.__download_overlay.props.text = "Device"
            self.title_text = "Please select a valid device"
        else:
            self.__download_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["rx_bytes"], self.unit).strip()
            self.__upload_overlay.props.text = readable_speed(self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit).strip()
            self.title_text = readable_speed(self.device_usage.interfaces[self.interface]["tx_bytes"], self.unit)
        self.applet.set_icon_context(ct)
        if hasattr(self.dialog.window, 'is_visible') and self.dialog.window.is_visible():
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
        return True


def readable_speed(speed, unit, seconds=True):
    ''' readable_speed(speed) -> string
        speed is in bytes per second
        returns a readable version of the speed given '''
    if speed is None or speed < 0:
        speed = 0
    if unit == 1:
        units = "B ", "KB", "MB", "GB", "TB"
    else:
        units = "b ", "Kb", "Mb", "Gb", "Tb"
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
    if "R" in flags and "U" in flags:
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
        "authors": APPLET_AUTHORS })
