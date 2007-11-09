#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
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
#
import gtk
from gtk import gdk
import cairo
import wnck
import weathericons
import xml.dom.minidom
import urllib
APP="awn-weather-applet"
DIR="locale"
import locale
import gettext
#locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class WeatherCodeSearch(gtk.Window):
	def __init__(self,config_win):
		gtk.Window.__init__(self)
		#super(WeatherCodeSearch, self).__init__(gtk.WINDOW_TOPLEVEL)
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
	def __init__(self,applet):
		gtk.Window.__init__(self)
		#super(WeatherConfig, self).__init__(gtk.WINDOW_TOPLEVEL)
		self.applet = applet
		self.location=applet.location
		self.location_code=applet.location_code
		self.set_title(_("Preferences"))                     # needs i18n
		vbox = gtk.VBox(True, 0)
		self.add(vbox)
		self.units_checkbox = gtk.CheckButton(_("Metric Units"))        # needs i18n
		if applet.units == "Metric":
			self.units_checkbox.set_active(True)
		else:
			self.units_checkbox.set_active(False)
		hbox0 = gtk.HBox(False,0)
		hbox0.pack_start(self.units_checkbox,True,False,0)
		vbox.pack_start(hbox0,False,False,0)

		hbox025 = gtk.HBox(True, 0)
		self.click_checkbox = gtk.CheckButton(_("Keep Forecast window opened until clicked"))  # needs i18n
		if applet.open_til_clicked == True:
			self.click_checkbox.set_active(True)
		else: 
			self.click_checkbox.set_active(False)
		hbox025.pack_start(self.click_checkbox,True,False,0)
		vbox.pack_start(hbox025,False,False,0)

		hbox05 = gtk.HBox(True, 0)
		self.click_checkbox2 = gtk.CheckButton(_("Use Curved Dialog look"))  # needs i18n
		if applet.curved_dialog == True:
			self.click_checkbox2.set_active(True)
		else: 
			self.click_checkbox2.set_active(False)
		hbox05.pack_start(self.click_checkbox2,True,False,0)
		vbox.pack_start(hbox05,False,False,0)
		
		hbox075 = gtk.HBox(True, 0)
		self.temp_pos = gtk.combo_box_new_text()							# needs i18n
		self.temp_pos.append_text(_("Lower Center"))
		self.temp_pos.append_text(_("Lower Left"))
		self.temp_pos.append_text(_("Lower Right"))
		self.temp_pos.append_text(_("Upper Center"))		
		self.temp_pos.append_text(_("Upper Left"))
		self.temp_pos.append_text(_("Upper Right"))
		self.temp_pos.append_text(_("Never"))

		self.temp_pos.set_active(applet.temp_position)
		pos_label = gtk.Label(_("Show Temperature"))
		hbox075.pack_start(pos_label,True,False,0)
		hbox075.pack_start(self.temp_pos,True,False,0)		
		vbox.pack_start(hbox075,False,False,0)

		hbox1 = gtk.HBox(True, 0)
		label1 = gtk.Label(_("Poll Frequency (Mins)"))  			# needs i18n
		adj = gtk.Adjustment(30.0, 30.0, 120.0, 1.0, 1.0, 0.0)
		self.spin = gtk.SpinButton(adj, 0.5, 0)
		current_freq = applet.polling_frequency / 60 / 1000
		self.spin.set_value(current_freq)
		hbox1.pack_start(label1)
		hbox1.pack_end(self.spin)
		vbox.pack_start(hbox1,True,False,2)

		hbox2 = gtk.HBox(True, 0)
		self.loc_label = gtk.Label(_("Current Location:") + " <b>" + self.location + "</b>")          # needs i18n
		self.loc_label.set_use_markup(True)
		hbox2.add(self.loc_label)
		#vbox.pack_start(hbox2,True,False,2)		
		
		#hbox3 = gtk.HBox(True,0)
		search = gtk.Button(_("Change Location"))
		hbox2.add(search)
		search.connect("clicked", self.search_button, "search")
		vbox.pack_start(hbox2,True,False,2)

		hbox4 = gtk.HBox(True, 0)
		ok = gtk.Button(stock=gtk.STOCK_OK)
		ok.connect("clicked", self.ok_button, "ok")
		hbox4.pack_start(ok,True,True,75)
		cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
		cancel.connect("clicked", self.cancel_button, "cancel")
		hbox4.pack_start(cancel,True,True,75)
		vbox.pack_end(hbox4,True,False,2)

		self.icons = weathericons.WeatherIcons()
		
	def search_button(self, widget, event):
		self.code_window = WeatherCodeSearch(self)
		self.code_window.set_size_request(400, 400)
		self.code_window.set_modal(True)
		self.code_window.set_destroy_with_parent(True)
		icon_name = self.icons.day_icons["0"]
		icon = gtk.gdk.pixbuf_new_from_file(icon_name)
		self.code_window.set_icon(icon)

		self.code_window.show_all()
		
	def ok_button(self, widget, event):
		self.applet.gconf_client.set_string(self.applet.gconf_path + "/location", self.location)
		self.applet.gconf_client.set_string(self.applet.gconf_path + "/location_code", self.location_code)
		self.applet.gconf_client.set_bool(self.applet.gconf_path + "/metric", self.units_checkbox.get_active())
		self.applet.gconf_client.set_int(self.applet.gconf_path + "/frequency", self.spin.get_value_as_int())
		self.applet.gconf_client.set_int(self.applet.gconf_path + "/temp_position", self.temp_pos.get_active())
		self.applet.gconf_client.set_bool(self.applet.gconf_path + "/open_til_clicked", self.click_checkbox.get_active())
		self.applet.gconf_client.set_bool(self.applet.gconf_path + "/curved_dialog", self.click_checkbox2.get_active())
		self.destroy()

	def cancel_button(self, widget, event):		
		self.destroy()
