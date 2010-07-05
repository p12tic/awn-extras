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
import gtop
import interfaces_dialog


APPLET_NAME = _('Bandwidth Monitor')
APPLET_VERSION = '0.3.9.4'
APPLET_COPYRIGHT = '© 2006-2009 CURE|THE|ITCH'
APPLET_AUTHORS = ['Kyle L. Huff <awn-bwm@curetheitch.com>']
APPLET_DESCRIPTION = _('Network Bandwidth monitor')
APPLET_WEBSITE = 'http://www.curetheitch.com/projects/awn-bwm/'
ICON_DIR = os.path.join(os.path.dirname(__file__), 'images')
APPLET_ICON = os.path.join(ICON_DIR, 'icon.png')
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
            'address': 'n/a',
            'subnet': 'n/a',
            'rx_history': range(0,25),
            'tx_history': range(0,25),
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
            'address': 'n/a',
            'subnet': 'n/a',
            'rx_history': range(0,25),
            'tx_history': range(0,25),
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

    def get_wireless_devices(self):
        if os.access('/proc/net/wireless', os.R_OK):
            wireless_devices = {}
            wireless = open('/proc/net/wireless', 'r').read()
            match = re.findall(r'(\w+): (\d+)\s+(\d+).*?([^\w]\d+).*?([^\w]\d+)', wireless, re.DOTALL)
            for wcard in match:
                wireless_devices[wcard[0]] = \
                    {'status': wcard[1],
                    'quality': wcard[2],
                    'strength': wcard[3],
                    'noise': wcard[4] }
            return wireless_devices
        else:
            return None


    def update_net_stats(self):
        netlist = gtop.netlist()        
        devices = {}
        
        wireless_devices = self.get_wireless_devices()

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
        if netlist:
            for device in netlist:
                device_lines = gtop.netload(device).dict()
                iface = device
                rx_bytes = device_lines['bytes_in']
                tx_bytes = device_lines['bytes_out']
                address = device_lines['address']
                subnet = device_lines['subnet']
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
                        'status': device_lines['if_flags'],
                        'prbytes': rx_bytes,
                        'ptbytes': tx_bytes,
                        'index': 1,
                        'address': address,
                        'subnet': subnet,
                        'rx_history': range(0,25),
                        'tx_history': range(0,25),
                        'ss_history': [],
                        'sq_history': [],
                        'sum_include': sum_include,
                        'multi_include': multi_include,
                        'upload_color': \
                            self.parent.prefs.get_color(iface, 'upload'),
                        'download_color': \
                            self.parent.prefs.get_color(iface, 'download'),
                        'graph_type': 'fan'}
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
                self.ifaces[iface]['address'] = address
                self.ifaces[iface]['subnet'] = subnet
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
                self.ifaces[iface]['rx_bytes'] = rbytes
                self.ifaces[iface]['tx_bytes'] = tbytes
                self.ifaces[iface]['prbytes'] = rx_bytes
                self.ifaces[iface]['ptbytes'] = tx_bytes
                self.ifaces[iface]['rx_sum'] = rx_bytes
                self.ifaces[iface]['tx_sum'] = tx_bytes
                self.ifaces[iface]['rxtx_sum'] = rxtx_sum
                self.ifaces[iface]['status'] = device_lines['if_flags']
                self.ifaces[iface]['collection_time'] = time()
                offset = self.parent.meter_scale
                if iface in wireless_devices:
                    ''' this is a wireless card '''
                    self.ifaces[iface]['signal'] = \
                        { 'strength': wireless_devices[iface]['strength'],
                        'quality': wireless_devices[iface]['quality'],
                        'noise': wireless_devices[iface]['noise'] }
                    self.ifaces[iface]['ss_history'] = \
                        self.ifaces[iface]['ss_history'][0 - offset:]
                    self.ifaces[iface]['ss_history'].append(
                        self.ifaces[iface]['signal']['strength'])
                    self.ifaces[iface]['sq_history'] = \
                        self.ifaces[iface]['sq_history'][0 - offset:]
                    self.ifaces[iface]['sq_history'].append(
                        self.ifaces[iface]['signal']['quality'])
                self.ifaces[iface]['rx_history'] = \
                    self.ifaces[iface]['rx_history'][0 - offset:]
                self.ifaces[iface]['rx_history'].append(
                    self.ifaces[iface]['rabytes'])
                self.ifaces[iface]['tx_history'] = \
                    self.ifaces[iface]['tx_history'][0 - offset:]
                self.ifaces[iface]['tx_history'].append(
                    self.ifaces[iface]['tabytes'])
                devices[iface] = 1
        self.ifaces['Sum Interface']['rx_history'] = \
            self.ifaces['Sum Interface']['rx_history'][0 - offset:]
        self.ifaces['Sum Interface']['rx_history'].append(sum_rx_history)
        self.ifaces['Sum Interface']['tx_history'] = \
            self.ifaces['Sum Interface']['tx_history'][0 - offset:]
        self.ifaces['Sum Interface']['tx_history'].append(sum_tx_history)
        for dev in self.ifaces.keys():
            if not dev in devices.keys() and not 'Sum Interface' in dev \
            and not 'Multi Interface' in dev:
                ''' The device does not exist, remove it.
                    del dictionary[key] is faster than dictionary.pop(key) '''
                del self.ifaces[dev]
                self.regenerate = True
        return True


class AppletBandwidthMonitor:

    def __init__(self, applet):
        self.applet = applet
        self.UI_FILE = UI_FILE
        applet.tooltip.set(_('Bandwidth Monitor'))
        self.meter_scale = 24
        icon = gtk.gdk.pixbuf_new_from_xpm_data(['1 1 1 1',
            '       c #000',
            ' '])
        self.max_tx_lbl_x = 0
        self.max_rx_lbl_x = 0

        height = self.applet.get_size() * 1.5
        if height != icon.get_height():
            icon = icon.scale_simple(int(height), \
                int(height / 1.5), gtk.gdk.INTERP_BILINEAR)
            self.applet.set_icon_pixbuf(icon)
        self.interface_dialog = interfaces_dialog.InterfaceDeatil(self)
        defaults = {'unit': 8,
            'interface': '',
            'draw_threshold': 0.0,
            'device_display_parameters': [],
            'background': True,
            'background_color': '#000000|0.5',
            'border': False,
            'border_color': '#000000|1.0',
            'label_control': 2,
            'graph_zero': 0,
            'wireless_signal_graph_type': []}
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
        self.setup_context_menu()
        self.prefs.setup()
        self.interface_dialog.setup_interface_dialogs()
        ''' connect the left-click dialog button 'Change Unit' to
            the call_change_unit function, which does not call
            self.change_unit directly, instead it toggles the 'active'
            property of the checkbutton so everything that needs to
            happen, happens. '''
        gobject.timeout_add(100, self.first_paint)
        gobject.timeout_add(800, self.subsequent_paint)

    def change_draw_ratio(self, widget):
        ratio = widget.get_value()
        self.ratio = ratio * 1024 if self.unit == 1 else ratio * 1024 / 8
        self.applet.settings['draw_threshold'] = ratio

    def call_change_unit(self, *args):
        active = True if self.unit == 8 else False
        self.prefs.uomCheckbutton.set_property('active', active)

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
        active = True if self.unit == 1 else False

    def generate_iface_submenu(self):
        if hasattr(self, 'iface_submenu'):
            self.iface_submenu.foreach(lambda x: self.iface_submenu.remove(x))
            iface_submenu = self.iface_submenu
        else:
            iface_submenu = gtk.Menu()
        iface_item1 = None
        devices = self.netstats.ifaces.keys()
        devices.sort()
        for device in devices:
            if not iface_item1:
                iface_item1 = gtk.RadioMenuItem(label=device)
                iface_item = iface_item1
            else:
                iface_item = gtk.RadioMenuItem(iface_item1, label=device)
            iface_item.connect('toggled', self.change_iface, device)
            if device == self.iface:
                iface_item.set_active(True)
            iface_submenu.add(iface_item)
        iface_submenu.show_all()
        return iface_submenu
        
    def setup_context_menu(self):
        """Add options to the context menu.

        """
        menu = self.applet.dialog.menu
        menu_index = len(menu) - 1

        self.context_menu_unit = gtk.CheckMenuItem(label='Use KBps instead of Kbps')
        if self.unit == 1:
            self.context_menu_unit.set_active(True)
        def menu_opened(widget):
            self.context_menu_unit.disconnect(self.context_menu_unit_handler)
            if self.unit == 1:
                self.context_menu_unit.set_active(True)
            else:
                self.context_menu_unit.set_active(False)
            self.context_menu_unit_handler = self.context_menu_unit.connect('toggled', self.call_change_unit)
        menu.connect("show", menu_opened)
        self.context_menu_unit_handler = self.context_menu_unit.connect('toggled', self.call_change_unit)
        menu.insert(self.context_menu_unit, menu_index)

        iface_submenu = self.generate_iface_submenu()
        self.iface_submenu = iface_submenu
        map_item = gtk.MenuItem(_("Devices"))
        map_item.set_submenu(iface_submenu)
        menu.insert(map_item, menu_index + 1)
        menu.insert(gtk.SeparatorMenuItem(), menu_index + 2)

    def change_iface(self, widget, iface):
        self.iface = iface
        self.applet.settings['interface'] = iface

    def enter_notify(self):
        if not self.applet.dialog.is_visible('main'):
            if not self.iface in self.netstats.ifaces:
                self.applet.set_tooltip_text(
                    _('Please select a valid Network Device'))
            else:
                self.applet.set_tooltip_text(_('''\
Total Sent: %s - Total Received: %s (All Interfaces)''') % (
                        self.readable_size(
                            self.netstats.ifaces[self.iface]['tx_sum']
                            * self.unit, self.unit, False),
                        self.readable_size(
                            self.netstats.ifaces[self.iface]['rx_sum']
                            * self.unit, self.unit, False)))

    def first_paint(self):
        self.repaint()
        return False

    def subsequent_paint(self):
        self.repaint()
        return True

    def draw_background(self, ct, x, y, w, h, radius):
        awn.cairo_rounded_rect(ct, x, y, w, h, radius, awn.ROUND_ALL)

    def draw_wireless(self, ct, width, height, iface):
        graph_type = "bar"
        prefs = self.applet.settings['wireless_signal_graph_type']
        for wdev in prefs:
            wdev_name, wdev_graph = wdev.split("|")
            if wdev_name == iface:
                graph_type = wdev_graph
                break
        self.netstats.ifaces[iface]['graph_type'] = graph_type
        x_pos = 0
        _ss_hist = [1]
        _total_hist = [1]
        if iface in self.netstats.ifaces \
        and 'ss_history' in self.netstats.ifaces[iface] \
        and len(self.netstats.ifaces[iface]['ss_history']):
            _ss_hist = self.netstats.ifaces[iface]['ss_history']
            _total_hist.extend(_ss_hist)
            _total_hist.sort()
            max_ss = _total_hist[-1]
            for value in self.netstats.ifaces[iface]['ss_history']:
                if int(value) == 0:
                    value = 200
                else:
                    value = abs(int(value))*80/100
                x_pos_end = (x_pos - width) + 2 if self.border \
                and x_pos > width else 0
                if height > 150:
                    placement = value + 30
                    opacity = 0.10
                else:
                    placement = value - height/3 - 10
                    opacity = 0.50 if self.background else 0.18
                    graph_type = 'area_bar'
                if value <= 40:
                    ct.set_source_rgba(0, 1, 0, opacity)
                elif value <= 60:
                    ct.set_source_rgba(1, 1, 0, opacity)
                elif value <= 90:
                    ct.set_source_rgba(1, 0.647058823529, 0, opacity)
                else:
                    ct.set_source_rgba(1, 0, 0, opacity)
                if graph_type == 'bar':
                    ct.line_to((x_pos - 1) - x_pos_end, placement)
                    ct.line_to((x_pos - 1) - x_pos_end, height)
                else:
                    ct.line_to(x_pos - x_pos_end, placement)
                    ct.line_to(x_pos - x_pos_end, height)
                
                if graph_type == 'area_bar':
                    # The bar chart is really an area graph, but with colored bars
                    ct.line_to(x_pos - width / (self.meter_scale - 1), height)
                    ct.move_to(x_pos, placement)
                    ct.close_path()
                    ct.fill()
                    later = True
                if graph_type == 'bar':
                    ct.line_to((x_pos - width / (self.meter_scale - 1)) + 1, height)
                    ct.move_to(x_pos, placement)
                    ct.close_path()
                    ct.fill()
                    later = False
                    ct.move_to(x_pos + 1, placement)
                    x_pos += (width / (self.meter_scale - 1))
                elif graph_type == 'fan':
                    # The fan chart is like a fan
                    ct.line_to(0, height)   
                    ct.move_to(x_pos, placement)
                    ct.close_path()
                    ct.fill()
                    x_pos += width / (self.meter_scale - 1)
                    ct.move_to(x_pos, placement)
                    later = False
                elif graph_type == 'fan_bar':
                    # The fan_bar chart is like fan, but with connected bars
                    ct.line_to(0, height)
                    ct.move_to(x_pos, placement)
                    ct.close_path()
                    ct.fill()
                    later = True
                else:
                    # otherwise draw AREA Chart 
                    ct.line_to(0, height)
                    later = True
                if later:
                    ct.move_to(x_pos, placement)
                    x_pos += width / (self.meter_scale - 1)
            ct.close_path()
            ct.fill()

    def draw_meter(self, ct, width, height, iface, multi=False, line_width=2,
        ratio=None, scale=1, border=None):
        border = self.border if not border else border
        ratio = self.ratio if not ratio else ratio
        ct.set_line_width(line_width)
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
        # Set the initial position to 0
        x_pos = 2 if border else 0
        # If a transmit history exists, draw it
        if iface in self.netstats.ifaces \
        and len(self.netstats.ifaces[iface]['tx_history']):
            _temp_hist = []
            _temp_hist.extend(self.netstats.ifaces[iface]['tx_history'])
            _temp_hist.sort()
            max_tx = _temp_hist[-1]
            for value in self.netstats.ifaces[iface]['tx_history']:
                x_pos_end = (x_pos - width) + 2 if border \
                and x_pos > width else 0
                placement = self.chart_coords(value, ratio, height, border)
                ct.line_to(x_pos - x_pos_end, placement)
                x_offset, y_offset = 0, 0
                if width > 200:
                    old_x, old_y = ct.get_current_point()
                    if value == max_tx and max_tx > 1 and not old_x == 0:
                        old_rgba = ct.get_source().get_rgba()
                        ct.close_path()
                        ct.stroke()
                        ct.set_line_width(1)
                        ct.set_source_rgba(1, 1, 1)
                        max_placement = self.chart_coords(max_tx, ratio, height, border)
                        self.max_tx_lbl_x = x_pos - x_pos_end - 60
                        if x_pos - x_pos_end - 60 < 1:
                            x_offset = 0 - (x_pos - x_pos_end - 60) + 5
                        ct.move_to(x_pos - x_pos_end - 60 + x_offset, max_placement - 7)
                        ct.show_text(self.readable_speed_ps(max_tx * self.unit, self.unit))
                        ct.fill()
                        ct.set_source_rgba(old_rgba[0], old_rgba[1], old_rgba[2])
                        ct.move_to(x_pos - x_pos_end - 60 + x_offset, max_placement - 4)
                        ct.line_to(x_pos - x_pos_end - 10 + x_offset, max_placement - 4)
                        ct.move_to(x_pos - x_pos_end - 10 + x_offset, max_placement - 4)
                        ct.line_to(x_pos - x_pos_end, max_placement)
                        ct.close_path()
                        ct.stroke()
                        ct.set_line_width(line_width)
                        ct.move_to(old_x, old_y)
                    x_offset = 1
                ct.move_to(x_pos, placement)
                x_pos += width / (self.meter_scale - x_offset)
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
        # Reset the position to 0
        x_pos = 2 if border else 0
        # If a receive history exists, draw it
        if iface in self.netstats.ifaces \
        and len(self.netstats.ifaces[iface]['rx_history']):
            _temp_hist = []
            _temp_hist.extend(self.netstats.ifaces[iface]['rx_history'])
            _temp_hist.sort()
            max_rx = _temp_hist[-1]
            for value in self.netstats.ifaces[iface]['rx_history']:
                x_pos_end = (x_pos - width) + 2 if border \
                and x_pos > width else 0
                placement = self.chart_coords(value, ratio, height, border)
                ct.line_to(x_pos - x_pos_end, placement)
                x_offset, y_offset = 0, 0
                if width > 200:
                    old_x, old_y = ct.get_current_point()
                    if value == max_rx and max_rx > 1 and not old_x == 0:
                        old_rgba = ct.get_source().get_rgba()
                        ct.close_path()
                        ct.stroke()
                        ct.set_line_width(1)
                        ct.set_source_rgba(1, 1, 1)
                        max_placement = self.chart_coords(max_rx, ratio, height, border)
                        rx_lbl_x, rx_lbl_y = x_pos - x_pos_end - 60, max_placement - 22
                        if rx_lbl_x - self.max_tx_lbl_x < 15 and rx_lbl_x - \
                            self.max_tx_lbl_x > -15:
                            if rx_lbl_y - self.chart_coords(max_tx, ratio, 
                                height, border) < 20 and rx_lbl_y - \
                                self.chart_coords(max_tx, ratio, height, border) > -20:
                                y_offset = 25
                        if x_pos - x_pos_end - 60 < 1:
                            x_offset = 0 - (x_pos - x_pos_end - 60) + 5
                        ct.move_to(x_pos - x_pos_end - 60 + x_offset, max_placement - 22 - y_offset)
                        ct.show_text(self.readable_speed_ps(max_rx * self.unit, self.unit))
                        ct.fill()
                        ct.set_source_rgba(old_rgba[0], old_rgba[1], old_rgba[2])
                        ct.move_to(x_pos - x_pos_end - 60 + x_offset, max_placement - 19 - y_offset)
                        ct.line_to(x_pos - x_pos_end - 5 + x_offset, max_placement - 19 - y_offset)
                        ct.move_to(x_pos - x_pos_end - 5 + x_offset, max_placement - 19 - y_offset)
                        ct.line_to(x_pos - x_pos_end, max_placement)
                        ct.close_path()
                        ct.stroke()
                        ct.set_line_width(line_width)
                        ct.move_to(old_x, old_y)
                    x_offset = 1
                ct.move_to(x_pos, placement)
                x_pos += width / (self.meter_scale - x_offset)
            ct.close_path()
            ct.stroke()




    def chart_coords(self, value, ratio=1, height=None, border=None):
        height = self.applet.get_size() if not height else height
        ratio = 1 if ratio < 1 else int(ratio)
        pos = height / 58.0
        bottom = 2.0 if border else 0
        return (height - pos \
            * (value / ratio)) + self.graph_zero - bottom

    def repaint(self):
        orientation = self.applet.get_pos_type()
        applet_size = self.applet.get_size()
        if orientation in (gtk.POS_LEFT, gtk.POS_RIGHT):
            width = applet_size
            self.meter_scale = 20
            self.upload_ot.props.font_sizing = 9
            self.download_ot.props.font_sizing = 9
            self.sum_ot.props.font_sizing = 9
        else:
            width = applet_size * 1.5
            self.upload_ot.props.font_sizing = self.default_font_size
            self.download_ot.props.font_sizing = self.default_font_size
            self.sum_ot.props.font_sizing = self.default_font_size
        cs = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width),
            applet_size)
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
            self.draw_background(ct, 0, 0, width, applet_size, 4)
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
                    self.draw_meter(ct, width, applet_size,
                        iface, True)
        else:
            if self.iface and self.iface in self.netstats.ifaces:
                if 'signal' in self.netstats.ifaces[self.iface]:
                    if self.background:
                        self.draw_wireless(ct, width, applet_size, self.iface)
                self.draw_meter(ct, width, applet_size, self.iface)
        if self.iface in self.netstats.ifaces:
            if self.label_control:
                if self.label_control == 2:
                    self.sum_ot.props.text = ''
                    self.download_ot.props.text = \
                        self.readable_speed_ps(
                            self.netstats.ifaces[self.iface]['rx_bytes'],
                            self.unit)
                    self.upload_ot.props.text = \
                        self.readable_speed_ps(
                            self.netstats.ifaces[self.iface]['tx_bytes'],
                            self.unit)
                else:
                    self.upload_ot.props.text = ''
                    self.download_ot.props.text = ''
                    self.sum_ot.props.text = \
                        self.readable_speed_ps(
                            self.netstats.ifaces[self.iface]['rx_bytes'] \
                            + self.netstats.ifaces[self.iface]['tx_bytes'],
                            self.unit)
            else:
                    self.upload_ot.props.text = ''
                    self.download_ot.props.text = ''
                    self.sum_ot.props.text = ''
            self.title_text = self.readable_speed_ps(
                self.netstats.ifaces[self.iface]['tx_bytes'], self.unit)
        else:
            self.upload_ot.props.text = _('No')
            self.download_ot.props.text = _('Device')
            self.sum_ot.props.text = ''
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
               applet_size - line_width / 2, 4)
            ct.stroke()
        self.applet.set_icon_context(ct)
        if self.applet.dialog.is_visible('main'):
            self.interface_dialog.do_current()
        if self.applet.dialog.is_visible('main') or hasattr(self.applet.dialog.menu.window, 'is_visible') and self.applet.dialog.menu.window.is_visible():
            for iface in self.netstats.ifaces:
                if not 'in_list' in self.netstats.ifaces[iface] \
                or self.netstats.regenerate == True:
                    self.netstats.regenerate = False
                    if hasattr(self.applet.dialog.menu.window, 'is_visible') and self.applet.dialog.menu.window.is_visible():
                        self.generate_iface_submenu()
                    self.interface_dialog.interfaceListArea.rebuild()
                    self.interface_dialog.interfaceListArea.refresh()
                    self.interface_dialog.interfaceOptionsArea.refresh()
                    return True
        return True

    #TODO: combine the following 2 methods
    def readable_speed_ps(self, speed=0, unit=1):
        ''' readable_speed_ps(speed) -> string
            speed is in bytes per second
            returns a readable version of the speed given '''
        units = ['Bps', 'KBps', 'MBps', 'GBps', 'TBps'] if unit == 1 \
        else ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']
        step = 1.0
        for u in units:
            if step > 1:
                s = '%4.2f ' % (speed / step)
                if len(s) <= 5:
                    return s + u
            if speed / step < 1024:
                return '%4.1d ' % (speed / step) + u
            step = step * 1024.0
        return '%4.1d ' % (speed / (step / 1024)) + units[-1]


    def readable_size(self, speed=0, unit=1, seconds=False):
        ''' readable_size(speed) -> string
            speed is in bytes per second
            returns a readable version of the speed given '''
        units = ['B ', 'KB', 'MB', 'GB', 'TB'] if unit == 1 \
        else ['b ', 'Kb', 'Mb', 'Gb', 'Tb']
        step = 1.0
        for u in units:
            if step > 1:
                s = '%4.2f ' % (speed / step)
                if len(s) <= 5:
                    return s + u
            if speed / step < 1024:
                return '%4.1d ' % (speed / step) + u
            step = step * 1024.0
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
