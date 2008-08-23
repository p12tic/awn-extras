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
        vbox = gtk.VBox(False, 0)
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
        hbox3 = gtk.HBox(True, 0)
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
        self.config_win.loc_label.set_label(_("Current Location:") + "  <b>" + self.selected_location + "</b>")
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

class WeatherConfig(gtk.Window):
    def __init__(self, applet):
        gtk.Window.__init__(self)

        self.applet = applet
        self.location = applet.settingsDict['location']
        self.location_code = applet.settingsDict['location_code']
        self.set_title(_("Preferences"))  # needs i18n
        vbox = gtk.VBox(True, 0)
        self.add(vbox)
        self.units_checkbox = gtk.CheckButton(_("Use metric units"))  # needs i18n
        if applet.settingsDict['metric']:
            self.units_checkbox.set_active(True)
        else:
            self.units_checkbox.set_active(False)
        hbox0 = gtk.HBox(False,0)
        hbox0.pack_start(self.units_checkbox,True,False,0)
        vbox.pack_start(hbox0,False,False,0)

        hbox025 = gtk.HBox(True, 0)
        self.click_checkbox = gtk.CheckButton(_("Close dialogs on mouse-out"))  # needs i18n
        if applet.settingsDict['open_til_clicked']:
            self.click_checkbox.set_active(False)
        else: 
            self.click_checkbox.set_active(True)
        hbox025.pack_start(self.click_checkbox,True,False,0)
        vbox.pack_start(hbox025,False,False,0)

        hbox05 = gtk.HBox(True, 0)
        self.click_checkbox2 = gtk.CheckButton(_("Use transparent/curved forecast dialog"))  # needs i18n
        if applet.settingsDict['curved_dialog']:
            self.click_checkbox2.set_active(True)
        else: 
            self.click_checkbox2.set_active(False)
        hbox05.pack_start(self.click_checkbox2,True,False,0)
        vbox.pack_start(hbox05,False,False,0)
        
        hbox075 = gtk.HBox(True, 0)
        self.temp_pos = gtk.combo_box_new_text()  # needs i18n
        self.temp_pos.append_text(_("Lower Center"))
        self.temp_pos.append_text(_("Lower Left"))
        self.temp_pos.append_text(_("Lower Right"))
        self.temp_pos.append_text(_("Upper Center"))
        self.temp_pos.append_text(_("Upper Left"))
        self.temp_pos.append_text(_("Upper Right"))
        self.temp_pos.append_text(_("Never"))

        self.temp_pos.set_active(applet.settingsDict['temp_position'])
        pos_label = gtk.Label(_("Show Temperature"))
        hbox075.pack_start(pos_label,True,False,0)
        hbox075.pack_start(self.temp_pos,True,False,0)
        vbox.pack_start(hbox075,False,False,0)
        
        # TEMP_FONTSIZE
        hbox6 = gtk.HBox(True, 0)
        label6 = gtk.Label(_("Temp Font Size"))  # needs i18n
        adj = gtk.Adjustment(32, 8, 100, 1, 1, 0)
        self.tempspin = gtk.SpinButton(adj, 0.5, 0)
        font_size = applet.settingsDict['temp_fontsize']
        self.tempspin.set_value(font_size)
        hbox6.pack_start(label6)
        hbox6.pack_end(self.tempspin)
        vbox.pack_start(hbox6,True,False,2)
        
        # MAP_MAXWIDTH
        hbox5 = gtk.HBox(True, 0)
        label5 = gtk.Label(_("Maximum Map Width"))  # needs i18n
        adj = gtk.Adjustment(450, 100, 800, 10, 100, 0)
        self.spin2 = gtk.SpinButton(adj, 0.5, 0)
        current_size = applet.settingsDict['map_maxwidth']
        self.spin2.set_value(current_size)
        hbox5.pack_start(label5)
        hbox5.pack_end(self.spin2)
        vbox.pack_start(hbox5,True,False,2)

        # FREQUENCY (ICON)
        hbox1 = gtk.HBox(True, 0)
        label1 = gtk.Label(_("Icon Poll Frequency (Mins)"))  # needs i18n
        adj = gtk.Adjustment(30, 30, 120, 5, 15, 0)
        self.spin = gtk.SpinButton(adj, 0.5, 0)
        current_freq = applet.settingsDict['frequency']
        self.spin.set_value(current_freq)
        hbox1.pack_start(label1)
        hbox1.pack_end(self.spin)
        vbox.pack_start(hbox1,True,False,2)

        # FREQUENCY (5DAY)
        hbox7 = gtk.HBox(True, 0)
        label7 = gtk.Label(_("Forecast Poll Frequency (Mins)"))  # needs i18n
        adj = gtk.Adjustment(30, 30, 120, 5, 15, 0)
        self.spin3 = gtk.SpinButton(adj, 0.5, 0)
        current_freq = applet.settingsDict['frequency_5day']
        self.spin3.set_value(current_freq)
        hbox7.pack_start(label7)
        hbox7.pack_end(self.spin3)
        vbox.pack_start(hbox7,True,False,2)

        # FREQUENCY (MAP)
        hbox8 = gtk.HBox(True, 0)
        label8 = gtk.Label(_("Map Poll Frequency (Mins)"))  # needs i18n
        adj = gtk.Adjustment(30, 30, 120, 5, 15, 0)
        self.spin4 = gtk.SpinButton(adj, 0.5, 0)
        current_freq = applet.settingsDict['frequency_map']
        self.spin4.set_value(current_freq)
        hbox8.pack_start(label8)
        hbox8.pack_end(self.spin4)
        vbox.pack_start(hbox8,True,False,2)

        # LOCATION
        hbox2 = gtk.HBox(True, 0)
        self.loc_label = gtk.Label(_("Current Location:") + " <b>" + self.location + "</b>")  # needs i18n
        self.loc_label.set_use_markup(True)
        hbox2.add(self.loc_label)
        #vbox.pack_start(hbox2,True,False,2)
        
        # change location button
        search = gtk.Button(_("Change Location"))
        hbox2.add(search)
        search.connect("clicked", self.search_button, "search")
        vbox.pack_start(hbox2,True,False,2)

        hbox4 = gtk.HBox(True, 0)
        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", self.ok_button, applet)
        hbox4.pack_start(ok,True,True,75)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.cancel_button, applet)
        hbox4.pack_start(cancel,True,True,75)
        vbox.pack_end(hbox4,True,False,2)
        
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
        self.destroy()

    def cancel_button(self, widget, event):
        self.destroy()
