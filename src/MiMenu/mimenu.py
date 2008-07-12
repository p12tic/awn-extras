# !/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>
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

import sys, os
import subprocess
import string

import pygtk
import gtk
from gtk import gdk

import awn
import menus
import pathfinder
import keyboard

class App (awn.AppletSimple):
    """
    """
    def __init__ (self, uid, orient, height):
        """
        Creating the applets core
        """
        self.visible = False
        screen_hieght = gtk.gdk.screen_height()
        if screen_hieght >= 901:
            self.screen_hieght = int(screen_hieght * 0.4)
        if screen_hieght <= 900:
            self.screen_hieght = int(screen_hieght * 0.5)
        if screen_hieght <= 700:
            self.screen_hieght = int(screen_hieght * 0.55)
        theme = gtk.IconTheme()
        location =  __file__
        self.location = location.replace('mimenu.py','')
        self.location_icon = self.location + '/icons/icon.svg'
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.height = height
        self.theme = gtk.icon_theme_get_default()
        if hasattr(self, 'set_awn_icon'):
            self.set_awn_icon('MiMenu', uid, 'gnome-main-menu')
        else:
          try:icon = self.theme.load_icon ("gnome-main-menu", height, 0)
          except:
              icon = gdk.pixbuf_new_from_file (self.location_icon)
              print 'noicon'
          if height != icon.get_height():
              icon = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
          self.set_icon (icon)
        self.title = awn.awn_title_get_default ()
        self.resultToolTip = "Main Menu Applet"
        self.dialog = awn.AppletDialog (self)
        self.theme = gtk.icon_theme_get_default()
        self.popup_menu = self.create_default_menu()
        render = gtk.CellRendererPixbuf()
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererText()
        cell2.set_property('xalign', 1.0)
        column1 = gtk.TreeViewColumn("==1==", render)
        column1.add_attribute(render, 'pixbuf', 0)
        column2 = gtk.TreeViewColumn("==2==", cell1,text=1)
        tree1 = gtk.TreeView()
        tree1.set_size_request(200, -1)
        tree1.set_headers_visible (0)
        tree1.append_column(column1)
        tree1.append_column(column2)
        lst1,self.objlist1 = menus.get_menus(menus.data.MENUROOT,
                                             root2=menus.data.SYSTEMMENUROOT)
        model = menus.set_model(tree1,lst1,self.theme,self.location_icon)
        tree1.connect('cursor_changed', self.treeclick,
                      tree1,self.objlist1,False)
        tree1.set_model(model)

        render = gtk.CellRendererPixbuf()
        cell1 = gtk.CellRendererText()
        cell2 = gtk.CellRendererText()
        cell2.set_property('xalign', 1.0)
        column1 = gtk.TreeViewColumn("==1==", render)
        column1.add_attribute(render, 'pixbuf', 0)
        column2 = gtk.TreeViewColumn("==2==", cell1,text=1)
        tree2 = gtk.TreeView()
        tree2.set_size_request(200, -1)
        tree2.set_headers_visible (0)
        tree2.append_column(column1)
        tree2.append_column(column2)
        lst2,self.objlist2 = menus.get_menus(menus.data.MENUROOT)
        model,self.objlist3 = menus.get_places(self.theme)
        tree2.set_model(model)
        tree2.connect("button-press-event", keyboard.tree2faux,
                      self.treeclick,tree2,self.objlist2)
        entry = gtk.Entry()
        entry.set_size_request(-1,28)
        search_button = gtk.Button(stock="gtk-find")
        hbox = gtk.HBox()
        hbox2 = gtk.HBox()
        vbox = gtk.VBox()
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        swindow.set_size_request(-1, self.screen_hieght)
        hbox2.pack_start(entry,expand=False, fill=False, padding=0)
        hbox2.pack_end(search_button,expand=False, fill=False, padding=0)
        vbox.pack_start(tree1)
        vbox.pack_end(hbox2,expand=False, fill=False, padding=0)
        swindow.add(tree2)
        hbox.pack_start(vbox)
        hbox.add(swindow)
        hbox.show_all()
        self.dialog.add(hbox)
        self.connect("button-press-event", self.button_press)
        self.connect("enter-notify-event", self.enter_notify)
        self.connect("leave-notify-event", self.leave_notify)
        self.dialog.connect("focus-out-event", self.dialog_focus_out)
        entry.connect("activate",self.search)
        search_button.connect("clicked",self.search)
        tree1.connect("key-press-event",keyboard.navigate,tree2,1)
        tree2.connect("key-press-event",keyboard.navigate,tree1,2)
        tree2.connect("row-activated",keyboard.tree2activated,
                      self.treeclick,tree2,self.objlist2)
        tree2.set_hover_selection(True)
        self.entry = entry
        self.tree1 = tree1
        self.tree2 = tree2

    def search(self,widget):
        test = pathfinder.exists(self.entry.get_text())
        if test[0] == True and test[1] != None:
            subprocess.Popen([test[1]], shell=False)
        else:
            subprocess.Popen(["tracker-search-tool", self.entry.get_text()],
                             shell=False)

    def button_press(self, widget, event):
        if event.button == 1:
            if self.dialog.flags() & gtk.VISIBLE:
                self.dialog.hide()
                self.title.hide(self)
            else:
                self.tree1.set_cursor((self.objlist1.__len__()-1,0),None,False)
                self.dialog.show_all()
                self.title.hide(self)
                if "placesmodel" in self.__dict__:pass
                else:self.placesmodel,self.objlist3 = menus.get_places(self.theme)
                self.tree2.set_model(self.placesmodel)
                self.tree1.grab_focus()
        elif event.button == 3:
            self.popup_menu.popup(None, None, None, event.button, event.time)

    def dialog_focus_out(self, widget, event):
        self.dialog.hide()

    def enter_notify(self, widget, event):
        self.title.show(self, self.resultToolTip)

    def leave_notify(self, widget, event):
        self.title.hide(self)

    def treeclick(self,widget,tree,obj,toggle,t2act=False):
        """
        this method is activated when tree1 is clicked.
        It fills tree2 with a model from the selected tree1 row
        """
        selection = tree.get_selection()
        selection.set_mode('single')
        if t2act == True:
            selection.select_path(1)
            selection.select_path(0)
        model, iter = selection.get_selected()
        try:name = model.get_value(iter,1)
        except:name=None
        if name != None:
            try:
                if toggle == True:
                    obj = self.objlist2
                if obj[name][0] == 1:
                    command = obj[name][1]
                    if '%' in command:command = command[:command.index('%')]
                    subprocess.Popen([command], shell=True)
                    self.dialog.hide()
                if obj[name][0] == 2:
                    lst,self.objlist2 = menus.get_menus(obj[name][1])
                    model = menus.set_model(self.tree1,lst,self.theme,
                                            self.location_icon)
                    self.tree2.set_cursor_on_cell((0,0), focus_column=None,
                                                  focus_cell=None,
                                                  start_editing=False)
                    self.tree2.set_model(model)
                    self.tree2.set_cursor_on_cell((0,0), focus_column=None,
                                                  focus_cell=None,
                                                  start_editing=False)
            except KeyError:
                if self.objlist3[name][0] == 0:
                    print self.objlist3[name][1].replace('file://','')
                    subprocess.Popen(["xdg-open",
                                      self.objlist3[name][1].replace('file://','')],
                                     shell=False)
                    self.dialog.hide()
            try:
                if obj[name][0] == 4:
                    if "placesmodel" in self.__dict__:pass
                    else:self.placesmodel,self.objlist3 = \
                                                    menus.get_places(self.theme)
                    self.tree2.set_model(self.placesmodel)
            except:pass

if __name__ == "__main__":
    awn.init                      (sys.argv[1:])
    applet = App                  (awn.uid, awn.orient,awn.height)
    awn.init_applet               (applet)
    applet.show_all               ()
    gtk.main                      ()
