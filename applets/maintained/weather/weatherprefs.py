#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007, 2008:
#   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#   Mike Rooney (launchpad.net/~michael) <mrooney@gmail.com>
#
# This is the configuration dialog for a weather applet for Avant Window Navigator.
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

import gtk, cairo
import gtk.glade
import os
from gtk import gdk
import xml.dom.minidom
import urllib
import weathericons
from helpers import debug

class WeatherCodeSearch(gtk.Window):
    def __init__(self, config_win):
        gtk.Window.__init__(self)

        self.config_win = config_win
        self.set_title(_("Search for Location Code"))        # needs i18n
        vbox = gtk.VBox(False, 2)
        self.add(vbox)
        # row 1
        hbox1 = gtk.HBox(True,0)
        label1 = gtk.Label(_("Location Name"))
        hbox1.pack_start(label1)
        self.location = gtk.Entry(20)
        self.location.connect("changed", self.text_entered, "text")
        self.location.connect("activate", self.go_clicked, "go")
        hbox1.pack_start(self.location)
        self.go = gtk.Button(_("Search"))
        self.go.connect("clicked", self.go_clicked, "go")
        self.go.set_sensitive(False)
        hbox1.pack_start(self.go)
        vbox.pack_start(hbox1,False,False,2)
        # row 1a
        hbox1a = gtk.HBox(True,0)
        label2 = gtk.Label(_("Enter the location you want to search for above.  For example: <i>Boston</i>; <i>Portland, ME</i>; <i>Paris</i>; or <i>Osaka, Japan</i>."))
        label2.set_line_wrap(True)
        label2.set_use_markup(True)
        hbox1a.pack_start(label2)
        vbox.pack_start(hbox1a,False,False,5)
        # row 2
        self.scrolled_win = gtk.ScrolledWindow()
        self.scrolled_win.set_border_width(10)
        self.scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.list = gtk.ListStore(str,str)
        self.list.append([_("No records found."),None])
        self.treeview = gtk.TreeView(self.list)
        tvcolumn = gtk.TreeViewColumn()
        self.treeview.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell,True)
        tvcolumn.add_attribute(cell, 'text', 0)
        self.treeview.set_sensitive(False)
        self.treeview.set_headers_visible(False)
        self.treeview.set_rules_hint(True)
        self.treeview.set_fixed_height_mode(True)
        self.treeview.connect("cursor-changed", self.selected, "selected")
        self.scrolled_win.add_with_viewport(self.treeview)
        vbox.pack_start(self.scrolled_win,True,True,5)
        # row 3
        hbox3 = gtk.HButtonBox()
        hbox3.set_layout(gtk.BUTTONBOX_END)
        self.ok = gtk.Button(stock=gtk.STOCK_OK)
        self.ok.set_sensitive(False)
        self.ok.connect("clicked", self.ok_button, "ok")
        hbox3.add(self.ok)
        self.cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.cancel.connect("clicked", self.cancel_button, "cancel")
        hbox3.add(self.cancel)
        vbox.pack_start(hbox3,False,False,2)

    def selected(self, widget, window):
        self.ok.set_sensitive(True)

    def text_entered(self, widget, window):
        if self.location.get_text() == "":
            self.go.set_sensitive(False)
        else:
            self.go.set_sensitive(True)
        
    def ok_button(self, widget, window):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        self.selected_location = model.get_value(iter,0)
        self.selected_code = model.get_value(iter, 1)
        self.config_win.location = self.selected_location
        self.config_win.location_code = self.selected_code
        self.config_win.loc_label.set_label("<b>" + self.selected_location + "</b>")
        self.destroy()

    def cancel_button(self, widget, window):
        self.destroy()

    def go_clicked(self, widget, window):
        if self.location.get_text() != "":
            self.list.clear()
            self.list.append([_("Searching..."),None])
            url = 'http://xoap.weather.com/search/search?where=' + urllib.quote(self.location.get_text())
            usock = urllib.urlopen(url)
            xmldoc = xml.dom.minidom.parse(usock)
            usock.close()
            locations = xmldoc.getElementsByTagName("loc")
            empty = True
            for loc in locations:
                if empty == True:
                    self.treeview.set_sensitive(True)
                    self.list.clear()
                    empty = False
                code = loc.getAttribute('id')
                city = loc.childNodes[0].data
                self.list.append([city,code])
            if empty == True:
                self.list.clear()
                self.list.append([_("No records found."),None])

class WeatherConfig:
    def __init__(self, applet):
        glade_path = os.path.join(os.path.dirname(__file__),
                                  "weather-prefs.glade")
        self.wTree = gtk.glade.XML(glade_path)

        self.toplevel = self.wTree.get_widget("weatherDialog")

        self.applet = applet
        self.location = applet.settingsDict['location']
        self.location_code = applet.settingsDict['location_code']
        self.units_checkbox = self.wTree.get_widget("metricCheckbutton")
        if applet.settingsDict['metric']:
            self.units_checkbox.set_active(True)
        else:
            self.units_checkbox.set_active(False)

        self.click_checkbox = self.wTree.get_widget("clickCheckbutton")
        if applet.settingsDict['open_til_clicked']:
            self.click_checkbox.set_active(False)
        else: 
            self.click_checkbox.set_active(True)

        self.click_checkbox2 = self.wTree.get_widget("curvedCheckbutton")
        if applet.settingsDict['curved_dialog']:
            self.click_checkbox2.set_active(True)
        else: 
            self.click_checkbox2.set_active(False)
        
        self.temp_pos = self.wTree.get_widget("posCombobox")

        self.temp_pos.set_active(applet.settingsDict['temp_position'])
        
        # TEMP_FONTSIZE
        self.tempspin = self.wTree.get_widget("fontSpinbutton")
        font_size = applet.settingsDict['temp_fontsize']
        self.tempspin.set_value(font_size)
        
        # MAP_MAXWIDTH
        self.spin2 = self.wTree.get_widget("mapWidthSpinbutton")
        current_size = applet.settingsDict['map_maxwidth']
        self.spin2.set_value(current_size)

        # FREQUENCY (ICON)
        self.spin = self.wTree.get_widget("iconSpinbutton")
        current_freq = applet.settingsDict['frequency']
        self.spin.set_value(current_freq)

        # FREQUENCY (5DAY)
        adj = gtk.Adjustment(30, 30, 120, 5, 15, 0)
        self.spin3 = self.wTree.get_widget("freqSpinbutton")
        current_freq = applet.settingsDict['frequency_5day']
        self.spin3.set_value(current_freq)

        # FREQUENCY (MAP)
        self.spin4 = self.wTree.get_widget("mapSpinbutton")
        current_freq = applet.settingsDict['frequency_map']
        self.spin4.set_value(current_freq)

        # LOCATION
        hbox2 = gtk.HBox(True, 0)
        self.loc_label = self.wTree.get_widget("locationLabel")
        self.loc_label.set_markup("<b>" + self.location + "</b>")
        
        # change location button
        search = self.wTree.get_widget("locationButton")
        search.connect("clicked", self.search_button, "search")

        ok = self.wTree.get_widget("okButton")
        ok.connect("clicked", self.ok_button, applet)
        cancel = self.wTree.get_widget("cancelButton")
        cancel.connect("clicked", self.cancel_button, applet)
      
    def get_toplevel(self):
        return self.toplevel

    def search_button(self, widget, event):
        self.code_window = WeatherCodeSearch(self)
        self.code_window.set_size_request(400, 400)
        self.code_window.set_modal(True)
        self.code_window.set_destroy_with_parent(True)
        icon_name = weathericons.GetIcon("0")
        icon = gtk.gdk.pixbuf_new_from_file(icon_name)
        self.code_window.set_icon(icon)

        self.code_window.show_all()
        
    def ok_button(self, widget, parent):
        mapping = {
            'location' : self.location,
            'location_code' : self.location_code,
            'metric' : self.units_checkbox.get_active(),
            'temp_position' : self.temp_pos.get_active(),
            'temp_fontsize' : self.tempspin.get_value_as_int(),
            'open_til_clicked' : not self.click_checkbox.get_active(),
            'curved_dialog' : self.click_checkbox2.get_active(),
            'map_maxwidth' : self.spin2.get_value_as_int(),
            'frequency' : self.spin.get_value_as_int(),
            'frequency_5day' : self.spin3.get_value_as_int(),
            'frequency_map' : self.spin4.get_value_as_int(),
        }
        
        for name, value in mapping.items():
            self.applet.applet.settings[name] = value

        parent.onSettingsChanged() #TODO: remove this once we have listening properly working, maybe?
        self.toplevel.destroy()

    def cancel_button(self, widget, event):
        self.toplevel.destroy()
