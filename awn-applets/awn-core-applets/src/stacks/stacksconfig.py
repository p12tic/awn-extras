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
import gobject
from gtk import gdk
import os
APP="Stacks"
DIR="locale"
import locale
import gettext
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)

class StacksConfig:

    def __init__(self, applet):
        self.applet = applet
        self.window = gtk.Window()
        self.window.set_title(_("Preferences"))
        self.window.set_size_request(400, 225)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.window.set_destroy_with_parent(True)
       
        # possible options
        self.backend = None

        drop_icon = _to_full_path("icons/stacks-drop.svg")
        icon = gdk.pixbuf_new_from_file (drop_icon)
        self.window.set_icon(icon)

        vbox = gtk.VBox(False, 0)
        self.window.add(vbox)
        self.notebook = gtk.Notebook()
        self.notebook.popup_disable()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        vbox.add(self.notebook)

        hbox = gtk.HBox(True, 0)
        ok = gtk.Button(stock=gtk.STOCK_OK)
        ok.connect("clicked", self.ok_button, "ok")
        hbox.add(ok)
        cancel = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel.connect("clicked", self.cancel_button, "cancel")
        hbox.add(cancel)
        vbox.pack_end(hbox,False,False,2)

        # page 1: the backend
        label = gtk.Label("Backend")
        page1 = gtk.VBox(False, 0)
        info_label = gtk.Label("If you select a <b>file</b> as backend, the stack will just contain a group of links to files (symlinks).\n\nIf you select a <b>folder</b> as backend, the stack will support real file operations, so that you can copy, move and link files to that folder.")
        info_label.set_use_markup(True)
        info_label.set_line_wrap(True)
        page1.pack_start(info_label, True, False, 2)
        type_hbox = gtk.HBox(False, 0)
        page1.pack_start(type_hbox, False, False, 10)
        select_label = gtk.Label("Select backend for this stack:")
        type_hbox.pack_start(select_label, False, False, 30)
        fbutton = gtk.Button(gtk.STOCK_OPEN)
        fbutton.set_use_stock(True)
        fbutton.connect("button-release-event", self.activate_filechooser)
        type_hbox.pack_end(fbutton, True, True, 30)
        self.notebook.append_page(page1, label)

        # page 2: the layout
        label2 = gtk.Label("Layout")
        page2 = gtk.VBox(False, 0)
        hbox_dim = gtk.HBox(False, 0)
        page2.pack_start(hbox_dim, True, False, 10)
        label_dim = gtk.Label("Maximum dimension (cols X rows):")
        hbox_dim.pack_start(label_dim, False, False, 30)
        self.cols = gtk.Entry()
        self.cols.set_width_chars(3)
        self.cols.set_alignment(0.5)
        gconf_cols = self.applet.gconf_client.get_int(self.applet.gconf_path + "/cols")
        if not gconf_cols > 0:
            gconf_cols = 5
        self.cols.set_text(str(gconf_cols))       
        hbox_dim.pack_start(self.cols, False, False, 0)
        label_times = gtk.Label("X")
        hbox_dim.pack_start(label_times, False, False, 2)
        self.rows = gtk.Entry()
        self.rows.set_width_chars(3)
        self.rows.set_alignment(0.5)
        gconf_rows = self.applet.gconf_client.get_int(self.applet.gconf_path + "/rows")
        if not gconf_rows > 0:
            gconf_rows = 4
        self.rows.set_text(str(gconf_rows))
        hbox_dim.pack_start(self.rows, False, False, 2)
        self.notebook.append_page(page2, label2)

        # page 3: the behavior
        label3 = gtk.Label("Behavior")
        page3 = gtk.VBox(False, 0)
        hbox_ops = gtk.HBox(False, 0)
        lbl_actions = gtk.Label(_("In most OS configurations, the CTRL, ALT and SHIFT are the modifiers that determine what drag operation is used."))
        page3.pack_start(lbl_actions, False, False, 2)
        lbl_fileops = gtk.Label(_("Enable file-operations:"))
        actions = self.applet.gconf_client.get_int(self.applet.gconf_path + "/file_operations")
        self.chk_copy = gtk.CheckButton(_("Copy")) 
        self.chk_move = gtk.CheckButton(_("Move"))
        self.chk_link = gtk.CheckButton(_("Link"))
        if actions > 0:
            if (actions & gtk.gdk.ACTION_COPY) > 0:
                self.chk_copy.set_active(True)
            if (actions & gtk.gdk.ACTION_MOVE) > 0:
                self.chk_move.set_active(True)
            if (actions & gtk.gdk.ACTION_LINK) > 0:
                self.chk_link.set_active(True)
        hbox_ops.pack_start(lbl_fileops, False, False, 10)
        hbox_ops.pack_start(self.chk_copy, False, False, 2)
        hbox_ops.pack_start(self.chk_move, False, False, 2)
        hbox_ops.pack_start(self.chk_link, False, False, 2)
        page3.pack_start(hbox_ops, False, False, 0)
        self.notebook.append_page(page3, label3)

        # page 4: about
        label4 = gtk.Label("About")
        page4 = gtk.VBox(False, 0)
        about_label = gtk.Label("<big><b>Stacks: applet for Avant Window Navigator</b></big>\n\nTODO: description\n\nauthor: Timon ter Braak")
                                    
        about_label.set_use_markup(True)
        page4.pack_start(about_label, True, False, 2)
        self.notebook.append_page(page4, label4)

        self.window.show_all()


    def activate_filechooser(self, widget, event):
        filesel = gtk.FileChooserDialog("Select backend destination:", 
                                        None, 
                                        gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER, 
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                        gtk.STOCK_APPLY, gtk.RESPONSE_OK), 
                                        None)
        filesel.set_default_response(gtk.RESPONSE_OK)
        gconf_backend = self.applet.gconf_client.get_string(self.applet.gconf_path + "/backend")
        if gconf_backend != None and not filesel.set_filename(gconf_backend):
            filesel.set_current_folder(gconf_backend)

        selected = None
        if filesel.run() == gtk.RESPONSE_OK:
            self.backend = filesel.get_filename()
        filesel.destroy()

    def ok_button(self, widget, event):
        if self.backend != None:
            self.applet.gconf_client.set_string(self.applet.gconf_path + "/backend", 
                                                self.backend )
        if int(self.cols.get_text()) > 0:
            self.applet.gconf_client.set_int(self.applet.gconf_path + "/cols",
                                                int(self.cols.get_text()) )
        if int(self.rows.get_text()) > 0:
            self.applet.gconf_client.set_int(self.applet.gconf_path + "/rows",
                                                int(self.rows.get_text()) )
        actions = 0
        if self.chk_copy.get_active():
            actions |= gtk.gdk.ACTION_COPY
        if self.chk_move.get_active():
            actions |= gtk.gdk.ACTION_MOVE
        if self.chk_link.get_active():
            actions |= gtk.gdk.ACTION_LINK
        self.applet.gconf_client.set_int(self.applet.gconf_path + "/file_operations",
                                            actions)

        self.window.destroy()

    def cancel_button(self, widget, event):		
	    self.window.destroy()

