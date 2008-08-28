#!/usr/bin/python
#
#       configdialog.py Version 0.5
#
#       Copyright 2008 Allan Wirth <allanlw@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
import gtk

class ConfigDialog(gtk.Dialog) :
	def __init__(self, parent, config) :
		self.config = config
		self.browsing = False
		self.switcher = parent
		gtk.Dialog.__init__(self,"Preferences", None, 0, (gtk.STOCK_ABOUT,gtk.RESPONSE_HELP,gtk.STOCK_OK,gtk.RESPONSE_OK,gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL))
	        self.theme = gtk.icon_theme_get_default()
		pixbuf = self.theme.load_icon("desktop", 64, 0)
		self.set_icon(pixbuf)
		#table = gtk.Table(9, 2)
		table = gtk.Table(10,2)
		label = gtk.Label("Base Folder:")
		table.attach(label, 0,1,0,1)
		self.filedialog = gtk.FileChooserDialog("Choose a Folder",self, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK), None)
		self.filedialog.connect("response", self.fileResponse)
		self.filedialog.set_icon(pixbuf)
		self.folderentry = gtk.Button()
		self.folderentry.connect("clicked", self.browse)
		table.attach(self.folderentry, 1,2,0,1)

		label1 = gtk.Label("Method of choosing the wallpaper:")
		table.attach(label1,0,1,1,2)
		self.combo0 = gtk.combo_box_new_text()
		self.types0 = ["Random", "Manual"]
		i = 0
		for type in self.types0 :
			self.combo0.append_text(type)
		self.combo0.connect("changed", self.combo0changed)
		table.attach(self.combo0,1,2,1,2)

		hbox2 = gtk.HBox()
		label2 = gtk.Label("How often to change\nthe wallpaper (in random mode):")
		table.attach(label2,0,1,2,3)
		adjustment = gtk.Adjustment(1, .1, 1440, .1, 1,0)
		self.secsentry = gtk.SpinButton(adjustment, 0, 1)
		hbox2.pack_start(self.secsentry,True,True)
		label2b = gtk.Label("Minutes")
		hbox2.pack_end(label2b, False, False,10)
		table.attach(hbox2,1,2,2,3)

		label3 = gtk.Label("How to render the wallpaper:")
		table.attach(label3,0,1,3,4)
		self.combo = gtk.combo_box_new_text()
		self.types = ["centered", "scaled", "stretched", "zoom"]
		i = 0
		for type in self.types :
			self.combo.append_text(type)
		self.combo.connect("changed", self.combochanged)
		table.attach(self.combo,1,2,3,4)
		label4 = gtk.Label("What mode to use:")
		table.attach(label4,0,1,4,5)
		self.combo2 = gtk.combo_box_new_text()
		self.types2 = ["GNOME", "Xfce"]
		i = 0
		for type in self.types2 :
			self.combo2.append_text(type)
		self.combo2.connect("changed", self.combo2changed)
		table.attach(self.combo2,1,2,4,5)
		label5 = gtk.Label("Play attention effect on change")
		table.attach(label5,0,1,5,6)
		self.check = gtk.CheckButton()
		table.attach(self.check,1,2,5,6,0)

		label6 = gtk.Label("Applet action on left click:")
		table.attach(label6,0,1,6,7)
		self.combo3 = gtk.combo_box_new_text()
		self.types3 = ["Switch Desktop Image", "Show Desktop", "None"]
		i = 0
		for type in self.types3 :
			self.combo3.append_text(type)
		table.attach(self.combo3,1,2,6,7)

		label7 = gtk.Label("Applet action on middle click:")
		table.attach(label7,0,1,7,8)
		self.combo4 = gtk.combo_box_new_text()
		i = 0
		for type in self.types3 :
			self.combo4.append_text(type)
		table.attach(self.combo4,1,2,7,8)

		label8 = gtk.Label("What to do when showing the desktop:")
		table.attach(label8,0,1,8,9)
		self.combo5 = gtk.combo_box_new_text()
		i = 0
		self.types5 = ["Toggle showing the desktop", "Just show the desktop"]
		for type in self.types5 :
			self.combo5.append_text(type)
		table.attach(self.combo5,1,2,8,9)
		hbox10 = gtk.HBox()
		label10 = gtk.Label("How much to scale the icon:")
		table.attach(label10,0,1,9,10)
		adjustment10 = gtk.Adjustment(1, 1, 100, 1, 10,0)
		self.secsentry10 = gtk.SpinButton(adjustment10)
		hbox10.pack_start(self.secsentry10,True,True)
		label10b = gtk.Label("Percent")
		hbox10.pack_end(label10b, False, False,10)
		table.attach(hbox10,1,2,9,10)
		self.vbox.add(table)
		self.connect("response", self.response)
	def combo2changed(self, widget) :
		if (widget.get_active_text() == "Xfce") :
			self.combo.set_sensitive(False)
			self.combo.set_active(self.types.index(self.config.get_render()))
		else :
			self.combo.set_sensitive(True)
	def combo0changed(self, widget) :
		if (widget.get_active_text() == "Manual") :
			self.secsentry.set_sensitive(False)
		else :
			self.secsentry.set_sensitive(True)
	def combochanged(self,widget) :
		self.config.set_render(widget.get_active_text())
	def response(self,widget,response) :
		if (response == gtk.RESPONSE_OK) :
			self.okButton(None)
		elif (response == gtk.RESPONSE_CANCEL) :
			self.close()
		elif (response == gtk.RESPONSE_HELP) :
			self.switcher.aboutDialog(None)
	def show(self) :
		self.folder = self.config.get_folder()
		self.folder2 = self.folder
		secs = self.config.get_secs()
		scale = self.config.get_scale()
		render = self.config.get_render()
		environment = self.config.get_environment()
		button1_action = self.config.get_button_action(1)
		button2_action = self.config.get_button_action(2)
		show_desktop = self.config.get_show_desktop()
		method = self.config.get_method()
		self.setFolder(self.folder)
		self.secsentry.set_value(float(secs)/float(60000))
		self.secsentry10.set_value(scale)
		self.combo0.set_active(self.types0.index(method))
		self.combo.set_active(self.types.index(render))
		self.combo2.set_active(self.types2.index(environment))
		self.combo3.set_active(self.types3.index(button1_action))
		self.combo4.set_active(self.types3.index(button2_action))
		self.combo5.set_active(self.types5.index(show_desktop))
		self.check.set_active(self.config.get_attention())
		self.show_all()
	def okButton(self, widget) :
		secs = int(float(self.secsentry.get_value()*60000))
		scale = self.secsentry10.get_value()
		render = self.combo.get_active_text()
		environment = self.combo2.get_active_text()
		button1_action = self.combo3.get_active_text()
		button2_action = self.combo4.get_active_text()
		show_desktop = self.combo5.get_active_text()
		attention = self.check.get_active()
		method = self.combo0.get_active_text()
		self.config.set_folder(self.folder)
		self.config.set_secs(secs)
		if (self.folder != self.folder2) :
			self.config.set_sub_folder("")
		self.config.set_render(render)
		self.config.set_attention(attention)
		self.config.set_button_action(1,button1_action)
		self.config.set_button_action(2,button2_action)
		self.config.set_show_desktop(show_desktop)
		self.config.set_method(method)
		self.config.set_scale(scale)
		if (environment == "Xfce") :
			message = gtk.MessageDialog(self,type=gtk.MESSAGE_WARNING,buttons=gtk.BUTTONS_OK,message_format="In order for DesktopManager to function properly in Xfce mode, you must right click on your desktop, select \"Desktop Settings\" and then click \"New List...\" in the Preferences dialog. After that click \"Save\" on the list creation dialog. You can then close the desktop preferences dialog and click \"OK\" in this window.\n\nIf you do not do this, your current desktop wallpaper will be overwritten!")
			pixbuf = self.theme.load_icon("desktop", 64, 0)
			message.set_icon(pixbuf)
			result = message.run()
			message.hide()
		self.config.set_environment(environment)
		self.switcher.updateConfig()
		self.destroy()
	def browse(self, widget) :
		self.browsing = True
		self.filedialog.show()
		self.filedialog.set_filename(self.folder)
	def errorResponse(self, widget, response) :
		widget.destroy()
	def setFolder(self, folder) :
		if (len(folder) <= 25) :
			self.folderentry.set_label(folder)
		else :
			length = len(folder)
			firstpart = folder[0:11]
			lastpart = folder[-11:len(folder)]
			total = firstpart+"..."+lastpart
			self.folderentry.set_label(total)
	def fileResponse(self, widget, response = None) :
		self.setFolder(self.filedialog.get_filename())
		self.folder = self.filedialog.get_filename()
		widget.hide()
		self.browsing = False
	def close(self, widget=None) :
		self.destroy()
