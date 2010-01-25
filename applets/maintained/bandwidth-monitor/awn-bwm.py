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

from time import time
import os
import re
import sys


import gtk
import awn

from awn.extras import _, awnlib, __version__
import gobject
import cairo
import bwmprefs

APPLET_NAME = _('Bandwidth Monitor')
APPLET_VERSION = '0.3.9.3'
APPLET_COPYRIGHT = '© 2006-2009 CURE|THE|ITCH'
APPLET_AUTHORS = ['Kyle L. Huff <awn-bwm@curetheitch.com>']
APPLET_DESCRIPTION = _('Network Bandwidth monitor')
APPLET_WEBSITE = 'http://www.curetheitch.com/projects/awn-bwm/'
APPLET_PATH = os.path.dirname(sys.argv[0])
APPLET_ICON = APPLET_PATH + '/images/icon.png'
UI_FILE = os.path.join(os.path.dirname(__file__), 'bandwidth-monitor.ui')


class Netstat:

    def __init__(self, parent, unit):
        self.parent = parent
        self.ifaces = {}
        self.ifaces['Sum Interface'] = {'collection_time': 0,
            'status': 'V',
            'prbytes': 0,
            'ptbytes': 0,
            'index': 1,
            'rx_history': [0, 0],
            'tx_history': [0, 0],
            'rx_bytes': 0,
            'tx_bytes': 0,
            'rx_sum': 0,
            'tx_sum': 0,
            'rxtx_sum': 0,
            'rabytes': 0,
            'tabytes': 0,
            'sum_include': False,
            'multi_include': False,
            'upload_color': '#ff0000',
            'download_color': '#ffff00'}
        self.ifaces['Multi Interface'] = {'collection_time': 0,
            'status': 'V',
            'prbytes': 0,
            'ptbytes': 0,
            'index': 1,
            'rx_history': [0, 0],
            'tx_history': [0, 0],
            'rx_bytes': 0,
            'tx_bytes': 0,
            'rx_sum': 0,
            'tx_sum': 0,
            'rxtx_sum': 0,
            'rabytes': 0,
            'tabytes': 0,
            'sum_include': False,
            'multi_include': False}
        self.regenerate = False
        self.update_net_stats()
        gobject.timeout_add(800, self.update_net_stats)

    def timeout_add_seconds(self, seconds, callback):
        if hasattr(gobject, 'timeout_add_seconds'):
            return gobject.timeout_add_seconds(seconds, callback)
        else:
            return gobject.timeout_add(seconds * 1000, callback)

    def update_net_stats(self):
        ifcfg_str = os.popen('netstat -eia').read()
        if ifcfg_str:
            ifcfg_str = ifcfg_str.split('\n\n')
        stat_str = 'n'
        devices = []
        # Reset the Sum Interface records to zero
        self.ifaces['Sum Interface']['rx_sum'] = 0
        self.ifaces['Sum Interface']['tx_sum'] = 0
        self.ifaces['Sum Interface']['rx_bytes'] = 0
        self.ifaces['Sum Interface']['tx_bytes'] = 0
        sum_rx_history = 0.0
        sum_tx_history = 0.0
        # Reset the Multi Interface records to zero
        self.ifaces['Multi Interface']['rx_sum'] = 0
        self.ifaces['Multi Interface']['tx_sum'] = 0
        self.ifaces['Multi Interface']['rx_bytes'] = 0
        self.ifaces['Multi Interface']['tx_bytes'] = 0
        multi_rx_history = 0.0
        multi_tx_history = 0.0
        if ifcfg_str and stat_str:
            for device_group in ifcfg_str:
                device_lines = device_group.split('\n')
                if 'Kernel' in device_lines[0]:
                    device_lines = device_lines[1:]
                iface = re.split('[\W]+',
                    device_lines[0].strip().replace(':', '_'))[0]
                if len(device_lines) > 2:
                    try:
                        rx_bytes = float(re.search(r'RX bytes:(\d+)\D',
                            device_group).group(1))
                        tx_bytes = float(re.search(r'TX bytes:(\d+)\D',
                            device_group).group(1))
                    except:
                        rx_bytes = 0
                        tx_bytes = 0
                    if not iface in self.ifaces:
                        ddps = 'device_display_parameters'
                        prefs = self.parent.applet.settings[ddps]
                        sum_include = True
                        multi_include = True
                        for device_pref in prefs:
                            dpv = device_pref.split('|')
                            if dpv[0] == iface:
                                sum_include = str(dpv[1])[0].upper() == 'T'
                                multi_include = str(dpv[2])[0].upper() == 'T'
                        self.ifaces[iface] = {'collection_time': time(),
                            'status': None,
                            'prbytes': rx_bytes,
                            'ptbytes': tx_bytes,
                            'index': 1,
                            'rx_history': [0, 0],
                            'tx_history': [0, 0],
                            'sum_include': sum_include,
                            'multi_include': multi_include,
                            'upload_color': \
                                self.parent.prefs.get_color(iface, 'upload'),
                            'download_color': \
                                self.parent.prefs.get_color(iface, 'download')}
                    collection = (
                        time() - self.ifaces[iface]['collection_time'])
                    rbytes = ((rx_bytes - self.ifaces[iface]['prbytes'])
                        * self.parent.unit) / collection
                    tbytes = ((tx_bytes - self.ifaces[iface]['ptbytes'])
                        * self.parent.unit) / collection
                    rabytes = (rx_bytes - self.ifaces[iface]['prbytes']) \
                        / collection
                    tabytes = (tx_bytes - self.ifaces[iface]['ptbytes']) \
                        / collection
                    self.ifaces[iface]['rabytes'] = rabytes
                    self.ifaces[iface]['tabytes'] = tabytes
                    rxtx_sum = rx_bytes + tx_bytes
                    if self.ifaces[iface]['sum_include']:
                        self.ifaces['Sum Interface']['rx_sum'] += rx_bytes
                        self.ifaces['Sum Interface']['tx_sum'] += tx_bytes
                        self.ifaces['Sum Interface']['rx_bytes'] += rbytes
                        self.ifaces['Sum Interface']['tx_bytes'] += tbytes
                        sum_rx_history += rabytes
                        sum_tx_history += tabytes
                    if self.ifaces[iface]['multi_include']:
                        self.ifaces['Multi Interface']['rx_sum'] += rx_bytes
                        self.ifaces['Multi Interface']['tx_sum'] += tx_bytes
                        self.ifaces['Multi Interface']['rx_bytes'] += rbytes
                        self.ifaces['Multi Interface']['tx_bytes'] += tbytes
                        multi_rx_history += rabytes
                        multi_tx_history += tabytes
                    ifstatus = 'BRMU'
                    self.ifaces[iface]['rx_bytes'] = rbytes
                    self.ifaces[iface]['tx_bytes'] = tbytes
                    self.ifaces[iface]['prbytes'] = rx_bytes
                    self.ifaces[iface]['ptbytes'] = tx_bytes
                    self.ifaces[iface]['rx_sum'] = rx_bytes
                    self.ifaces[iface]['tx_sum'] = tx_bytes
                    self.ifaces[iface]['rxtx_sum'] = rxtx_sum
                    self.ifaces[iface]['status'] = ifstatus
                    self.ifaces[iface]['collection_time'] = time()
                    offset = self.parent.meter_scale - 1 \
                    if self.parent.border else self.parent.meter_scale
                    self.ifaces[iface]['rx_history'] = \
                        self.ifaces[iface]['rx_history'][0 - offset:]
                    self.ifaces[iface]['rx_history'].append(
                        self.ifaces[iface]['rabytes'])
                    self.ifaces[iface]['tx_history'] = \
                        self.ifaces[iface]['tx_history'][0 - offset:]
                    self.ifaces[iface]['tx_history'].append(
                        self.ifaces[iface]['tabytes'])
                    devices.append(iface)
        self.ifaces['Sum Interface']['rx_history'] = \
            self.ifaces['Sum Interface']['rx_history'][0 - offset:]
        self.ifaces['Sum Interface']['rx_history'].append(sum_rx_history)
        self.ifaces['Sum Interface']['tx_history'] = \
            self.ifaces['Sum Interface']['tx_history'][0 - offset:]
        self.ifaces['Sum Interface']['tx_history'].append(sum_tx_history)
        for dev in self.ifaces.keys():
            if not dev in devices and not 'Sum Interface' in dev \
            and not 'Multi Interface' in dev:
                ''' The device does not exist, remove it.
                    del dictionary[key] is faster than dictionary.pop(key) '''
                del self.ifaces[dev]
                self.regenerate = True
        return True


class AppletBandwidthMonitor:

    def __init__(self, applet):
        # Test if user has access to /proc/net/dev
        if not os.access('/proc/net/dev', os.R_OK):
            applet.errors.general((_('Unable to caclulate statistics'), _('''\
Statistics calculation requires read access to /proc/net/dev''')))
            applet.errors.set_error_icon_and_click_to_restart()
            return None
        self.applet = applet
        self.UI_FILE = UI_FILE
        applet.tooltip.set(_('Bandwidth Monitor'))
        self.meter_scale = 25
        icon = gtk.gdk.pixbuf_new_from_xpm_data(['1 1 1 1',
            '       c #000',
            ' '])
        height = self.applet.get_size() * 1.5
        if height != icon.get_height():
            icon = icon.scale_simple(int(height), \
                int(height / 1.5), gtk.gdk.INTERP_BILINEAR)
            self.applet.set_icon_pixbuf(icon)
        self.dialog = applet.dialog.new('main')
        self.vbox = gtk.VBox()
        self.dialog.add(self.vbox)
        button = gtk.Button(_('Change Unit'))
        self.dialog.add(button)
        defaults = {'unit': 8,
            'interface': '',
            'draw_threshold': 0.0,
            'device_display_parameters': [],
            'background': True,
            'background_color': '#000000|0.5',
            'border': False,
            'border_color': '#000000|1.0',
            'label_control': 2,
            'graph_zero': 0}
        for key, value in defaults.items():
            if not key in self.applet.settings:
                self.applet.settings[key] = value
        self.iface = self.applet.settings['interface']
        self.unit = self.applet.settings['unit']
        self.label_control = self.applet.settings['label_control']
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
            self.ratio = ratio * 1024 if self.unit == 1 else ratio * 1024 / 8
        self.prefs = bwmprefs.Preferences(self.applet, self)
        self.netstats = Netstat(self, self.unit)
        applet.tooltip.connect_becomes_visible(self.enter_notify)
        self.table = self.generate_table()
        self.vbox.add(self.table)
        self.upload_ot = awn.OverlayText()
        self.download_ot = awn.OverlayText()
        self.sum_ot = awn.OverlayText()
        self.upload_ot.props.gravity = gtk.gdk.GRAVITY_NORTH
        self.download_ot.props.gravity = gtk.gdk.GRAVITY_SOUTH
        self.sum_ot.props.gravity = gtk.gdk.GRAVITY_NORTH
        applet.add_overlay(self.upload_ot)
        applet.add_overlay(self.download_ot)
        applet.add_overlay(self.sum_ot)
        self.default_font_size = self.upload_ot.props.font_sizing
        self.upload_ot.props.y_override = 4
        self.download_ot.props.y_override = 18
        self.sum_ot.props.y_override = 11
        self.upload_ot.props.apply_effects = True
        self.download_ot.props.apply_effects = True
        self.sum_ot.props.apply_effects = True
        self.upload_ot.props.text = _('Scanning')
        self.download_ot.props.text = _('Devices')
        self.prefs.setup()
        ''' connect the left-click dialog button 'Change Unit' to
            the call_change_unit function, which does not call
            self.change_unit directly, instead it toggles the 'active'
            property of the checkbutton so everything that needs to
            happen, happens. '''
        button.connect('clicked', self.call_change_unit)
        gobject.timeout_add(100, self.first_paint)
        gobject.timeout_add(800, self.subsequent_paint)

    def change_draw_ratio(self, widget):
        ratio = widget.get_value()
        self.ratio = ratio * 1024 if self.unit == 1 else ratio * 1024 / 8
        self.applet.settings['draw_threshold'] = ratio

    def call_change_unit(self, *args):
        if self.unit == 8:
            self.prefs.uomCheckbutton.set_property('active', True)
        else:
            self.prefs.uomCheckbutton.set_property('active', False)

    def change_unit(self, widget=None, scaleThresholdSBtn=None, label=None):
        self.unit = 8 if self.unit == 1 else 1
        # normalize and update the label, and normalize the spinbutton
        if label:
            if self.unit == 1:
                label.set_text(_('KBps'))
                scaleThresholdSBtn.set_value(
                    self.applet.settings['draw_threshold'] / 8)
            else:
                label.set_text(_('Kbps'))
                scaleThresholdSBtn.set_value(
                    self.applet.settings['draw_threshold'] * 8)
        self.applet.settings['unit'] = self.unit

    def change_iface(self, widget, iface):
        if widget.get_active():
            # Changed to interface %s' % iface
            self.iface = iface
            self.applet.settings['interface'] = iface

    def generate_table(self):
        table = gtk.Table(100, 100, False)
        col_iter = 0
        row_iter = 2
        for i in [0, 1, 2, 3, 4, 5, 6]:
            table.set_col_spacing(i, 20)
        table.attach(gtk.Label(''),
            0, 1, 0, 1,
            xoptions=gtk.EXPAND | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.FILL,
            xpadding=0, ypadding=0)
        table.attach(gtk.Label(_('Interface')),
            1, 2, 0, 1,
            xoptions=gtk.EXPAND | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.FILL,
            xpadding=0, ypadding=0)
        table.attach(gtk.Label(_('Sent')),
            2, 3, 0, 1,
            xoptions=gtk.EXPAND | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.FILL,
            xpadding=0, ypadding=0)
        table.attach(gtk.Label(_('Received')),
            3, 4, 0, 1,
            xoptions=gtk.EXPAND | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.FILL,
            xpadding=0, ypadding=0)
        table.attach(gtk.Label(_('Sending')),
            4, 5, 0, 1,
            xoptions=gtk.EXPAND | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.FILL,
            xpadding=0, ypadding=0)
        table.attach(gtk.Label(_('Receiving')),
            5, 6, 0, 1,
            xoptions=gtk.EXPAND | gtk.FILL,
            yoptions=gtk.EXPAND | gtk.FILL,
            xpadding=0, ypadding=0)
        radio = None
        for iface in sorted(self.netstats.ifaces):
            widget = gtk.Label()
            widget.toggle = gtk.RadioButton(group=radio)
            radio = widget.toggle
            if iface == self.iface:
                widget.toggle.set_active(True)
            widget.toggle.connect('clicked', self.change_iface, iface)
            widget.name_label = gtk.Label(str(iface))
            widget.sent_label = gtk.Label(str(
                readable_speed(self.netstats.ifaces[iface]['tx_sum'],
                    self.unit, False).strip()))
            widget.received_label = gtk.Label(str(
                readable_speed(self.netstats.ifaces[iface]['rx_sum'],
                    self.unit, False).strip()))
            widget.tx_speed_label = gtk.Label(str(
                readable_speed(self.netstats.ifaces[iface]['tx_bytes']
                    * self.unit, self.unit).strip()))
            widget.rx_speed_label = gtk.Label(str(
                readable_speed(self.netstats.ifaces[iface]['rx_bytes']
                    * self.unit, self.unit).strip()))
            self.netstats.ifaces[iface]['widget'] = widget
            for widget_object in [widget.toggle,
                widget.name_label,
                widget.sent_label,
                widget.received_label,
                widget.tx_speed_label,
                widget.rx_speed_label]:
                table.attach(widget_object,
                    col_iter, col_iter + 1,
                    row_iter, row_iter + 1,
                    xoptions=gtk.EXPAND | gtk.FILL,
                    yoptions=gtk.EXPAND | gtk.FILL,
                    xpadding=0, ypadding=0)
                col_iter += 1
            row_iter += 1
            col_iter = 0
        return table

    def enter_notify(self):
        if not self.applet.dialog.is_visible('main'):
            if not self.iface in self.netstats.ifaces:
                self.applet.set_tooltip_text(
                    _('Please select a valid Network Device'))
            else:
                self.applet.set_tooltip_text(_('''\
Total Sent: %s - Total Received: %s (All Interfaces)''') % (
                        readable_speed(
                            self.netstats.ifaces[self.iface]['tx_sum']
                            * self.unit, self.unit, False),
                        readable_speed(
                            self.netstats.ifaces[self.iface]['rx_sum']
                            * self.unit, self.unit, False)))

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

    def draw_meter(self, ct, width, height, iface, multi=False):
        ratio = self.ratio
        ct.set_line_width(2)
        ''' Create temporary lists to store the values of the transmit
            and receive history, which will be then placed into the
            _total_hist and sorted by size to set the proper
            scale/ratio for the line heights '''
        _rx_hist = [1]
        _tx_hist = [1]
        _total_hist = [1]
        if not multi:
            if iface in self.netstats.ifaces \
            and len(self.netstats.ifaces[iface]['rx_history']):
                _rx_hist = self.netstats.ifaces[iface]['rx_history']
            if iface in self.netstats.ifaces \
            and len(self.netstats.ifaces[iface]['tx_history']):
                _tx_hist = self.netstats.ifaces[iface]['tx_history']
            _total_hist.extend(_rx_hist)
            _total_hist.extend(_tx_hist)
        else:
            for device in self.netstats.ifaces:
                if self.netstats.ifaces[device]['multi_include']:
                    _total_hist.extend(
                        self.netstats.ifaces[device]['rx_history'])
                if self.netstats.ifaces[iface]['multi_include']:
                    _total_hist.extend(
                        self.netstats.ifaces[device]['tx_history'])
        _total_hist.sort()
        ''' ratio variable controls the minimum threshold for data -
            i.e. 32000 would not draw graphs for data transfers below
            3200 bytes - the initial value of ratio if set to the link
            speed will prevent the graph from scaling. If using the
            Multi Interface, the ratio will adjust based on the
            highest throughput metric. '''
        max_val = _total_hist[-1]
        ratio = max_val / 28 if max_val > self.ratio else self.ratio
        # Change the color of the upload line to configured/default
        if iface:
            color = gtk.gdk.color_parse(
                self.netstats.ifaces[iface]['upload_color'])
            ct.set_source_rgba(color.red / 65535.0,
                color.green / 65535.0,
                color.blue / 65535.0, 1.0)
        else:
            ct.set_source_rgba(0.1, 0.1, 0.1, 0.5)
        # Set the initial position and iter to 0
        x_pos = 2 if self.border else 0
        cnt = 0
        # If a transmit history exists, draw it
        if iface in self.netstats.ifaces \
        and len(self.netstats.ifaces[iface]['tx_history']):
            for value in self.netstats.ifaces[iface]['tx_history']:
                x_pos_end = (x_pos - width) + 2 if self.border \
                and x_pos > width else 0
                ct.line_to(x_pos - x_pos_end, self.chart_coords(value, ratio))
                ct.move_to(x_pos, self.chart_coords(value, ratio))
                x_pos += width / self.meter_scale
                cnt += 1
            ct.close_path()
            ct.stroke()
        # Change the color of the download line to configured/default
        if iface:
            color = gtk.gdk.color_parse(
                self.netstats.ifaces[iface]['download_color'])
            ct.set_source_rgba(color.red / 65535.0,
                color.green / 65535.0,
                color.blue / 65535.0, 1.0)
        else:
            ct.set_source_rgba(0.1, 0.1, 0.1, 0.5)
        # Reset the position and iter to 0
        x_pos = 2 if self.border else 0
        cnt = 0
        # If a receive history exists, draw it
        if iface in self.netstats.ifaces \
        and len(self.netstats.ifaces[iface]['rx_history']):
            for value in self.netstats.ifaces[iface]['rx_history']:
                x_pos_end = (x_pos - width) + 2 if self.border \
                and x_pos > width else 0
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
        return (self.applet.get_size() - pos \
            * (value / int(ratio))) + self.graph_zero - bottom

    def repaint(self):
        orientation = self.applet.get_pos_type()
        if orientation in (gtk.POS_LEFT, gtk.POS_RIGHT):
            width = self.applet.get_size()
            self.upload_ot.props.font_sizing = 9
            self.download_ot.props.font_sizing = 9
            self.sum_ot.props.font_sizing = 9
        else:
            width = self.applet.get_size() * 1.5
            self.upload_ot.props.font_sizing = self.default_font_size
            self.download_ot.props.font_sizing = self.default_font_size
            self.sum_ot.props.font_sizing = self.default_font_size
        cs = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width),
            self.applet.get_size())
        ct = cairo.Context(cs)
        ct.set_source_surface(cs)
        ct.set_line_width(2)
        if self.background:
            bgColor, alpha = \
                self.applet.settings['background_color'].split('|')
            bgColor = gtk.gdk.color_parse(bgColor)
            ct.set_source_rgba(bgColor.red / 65535.0,
                bgColor.green / 65535.0,
                bgColor.blue / 65535.0,
                float(alpha))
            self.draw_background(ct, 0, 0, width, self.applet.get_size(), 10)
            ct.fill()
        if self.iface == 'Multi Interface':
            tmp_history = [1]
            for iface in self.netstats.ifaces:
                if self.netstats.ifaces[iface]['multi_include']:
                    tmp_history.extend(
                        self.netstats.ifaces[iface]['rx_history'])
                    tmp_history.extend(
                        self.netstats.ifaces[iface]['tx_history'])
            tmp_history.sort()
            max_val = tmp_history[-1]
            self.ratio = max_val / 28 if max_val > self.ratio else 1
            for iface in self.netstats.ifaces:
                if self.netstats.ifaces[iface]['multi_include']:
                    self.draw_meter(ct, width, self.applet.get_size(),
                        iface, True)
        else:
            self.draw_meter(ct, width, self.applet.get_size(), self.iface)
        if self.iface in self.netstats.ifaces:
            if self.label_control:
                if self.label_control == 2:
                    self.sum_ot.props.text = ''
                    self.download_ot.props.text = \
                        readable_speed(
                            self.netstats.ifaces[self.iface]['rx_bytes'],
                            self.unit).strip()
                    self.upload_ot.props.text = \
                        readable_speed(
                            self.netstats.ifaces[self.iface]['tx_bytes'],
                            self.unit).strip()
                else:
                    self.upload_ot.props.text = ''
                    self.download_ot.props.text = ''
                    self.sum_ot.props.text = \
                        readable_speed(
                            self.netstats.ifaces[self.iface]['rx_bytes'] \
                            + self.netstats.ifaces[self.iface]['tx_bytes'],
                            self.unit).strip()
            else:
                    self.upload_ot.props.text = ''
                    self.download_ot.props.text = ''
                    self.sum_ot.props.text = ''
            self.title_text = readable_speed(
                self.netstats.ifaces[self.iface]['tx_bytes'], self.unit)
        else:
            self.upload_ot.props.text = _('No')
            self.download_ot.props.text = _('Device')
            self.title_text = _('Please select a valid device')
        if self.border:
            line_width = 2
            ct.set_line_width(line_width)
            borderColor, alpha = \
                self.applet.settings['border_color'].split('|')
            borderColor = gtk.gdk.color_parse(borderColor)
            ct.set_source_rgba(borderColor.red / 65535.0,
                borderColor.green / 65535.0,
                borderColor.blue / 65535.0,
                float(alpha))
            self.draw_background(ct,
                line_width / 2,
                line_width / 2,
                width - line_width / 2,
                self.applet.get_size() - line_width / 2, 4)
            ct.stroke()
        self.applet.set_icon_context(ct)
        if self.applet.dialog.is_visible('main'):
            for iface in self.netstats.ifaces:
                if not 'widget' in self.netstats.ifaces[iface] \
                or self.netstats.regenerate == True:
                    self.netstats.regenerate = False
                    self.vbox.remove(self.table)
                    self.table = self.generate_table()
                    self.vbox.add(self.table)
                    self.vbox.show_all()
                self.netstats.ifaces[iface]['widget'].rx_speed_label.set_text(
                    str(readable_speed(self.netstats.ifaces[iface]['rx_bytes'],
                    self.unit).strip()))
                self.netstats.ifaces[iface]['widget'].tx_speed_label.set_text(
                    str(readable_speed(self.netstats.ifaces[iface]['tx_bytes'],
                    self.unit).strip()))
                self.netstats.ifaces[iface]['widget'].sent_label.set_text(
                    str(readable_speed(self.netstats.ifaces[iface]['tx_sum'] \
                    * self.unit, self.unit, False).strip()))
                self.netstats.ifaces[iface]['widget'].received_label.set_text(
                    str(readable_speed(self.netstats.ifaces[iface]['rx_sum'] \
                    * self.unit, self.unit, False).strip()))
        return True


def readable_speed(speed, unit, seconds=True):
    ''' readable_speed(speed) -> string
        speed is in bytes per second
        returns a readable version of the speed given '''
    speed = 0 if speed is None or speed < 0 else speed
    units = ['B ', 'KB', 'MB', 'GB', 'TB'] if unit == 1 \
    else ['b ', 'Kb', 'Mb', 'Gb', 'Tb']
    if seconds:
        temp_units = []
        for u in units:
            temp_units.append('%sps' % u.strip())
        units = temp_units
    step = 1L
    for u in units:
        if step > 1:
            s = '%4.2f ' % (float(speed) / step)
            if len(s) <= 5:
                return s + u
            s = '%4.2f ' % (float(speed) / step)
            if len(s) <= 5:
                return s + u
        if speed / step < 1024:
            return '%4.1d ' % (speed / step) + u
        step = step * 1024L
    return '%4.1d ' % (speed / (step / 1024)) + units[-1]

if __name__ == '__main__':
    awnlib.init_start(AppletBandwidthMonitor, {'name': APPLET_NAME,
        'short': 'bandwidth-monitor',
        'version': __version__,
        'description': APPLET_DESCRIPTION,
        'logo': APPLET_ICON,
        'author': 'Kyle L. Huff',
        'copyright-year': '2010',
        'authors': APPLET_AUTHORS})
