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
        #   <alignment>
        label = gtk.Label(_("Backend"))
        page1 = gtk.Alignment(0, 0, 0, 0)
        page1.set_padding(10,10,20,20)
        self.notebook.append_page(page1, label)
        #       <vbox>
        vbox1 = gtk.VBox(False, 2)
        page1.add(vbox1)
        #           <label>
        info_label = gtk.Label(_("If you select a <b>file</b> as backend, the stack will just contain a group of links to files (symlinks).\n\nIf you select a <b>folder</b> as backend, the stack will support real file operations, so that you can copy, move and link files to that folder."))
        info_label.set_use_markup(True)
        info_label.set_line_wrap(True)
        vbox1.pack_start(info_label, True, True, 0)
        #           </label>
        #           <hbox>
        type_hbox = gtk.HBox(False, 0)
        vbox1.pack_start(type_hbox, True, True, 0)
        #               <label>
        select_label = gtk.Label(_("Select backend for this stack:"))
        type_hbox.pack_start(select_label, True, True, 0)
        #               </label>
        #               <button>
        fbutton = gtk.Button(gtk.STOCK_OPEN)
        fbutton.set_use_stock(True)
        fbutton.connect("button-release-event", self.activate_filechooser)
        type_hbox.pack_end(fbutton, True, True, 0)
        #           </hbox>
        #       </vbox>
        #   </alignment>

        # page 2: the layout
        #   <alignment>
        label2 = gtk.Label(_("Layout"))
        page2 = gtk.Alignment(0, 0, 0, 0)
        page2.set_padding(10,10,20,20)
        self.notebook.append_page(page2, label2)
        #       <vbox>
        vbox2 = gtk.VBox(False, 2)
        page2.add(vbox2)
        #           <hbox>
        hbox21 = gtk.HBox(False, 2)
        vbox2.pack_start(hbox21, True, True, 0)
        #               <label>
        label_dim = gtk.Label(_("Maximum dimension (cols X rows):"))
        hbox21.pack_start(label_dim, True, True, 0)
        #               </label>
        #               <entry>
        self.cols = gtk.Entry()
        self.cols.set_width_chars(3)
        self.cols.set_alignment(0.5)
        gconf_cols = self.applet.gconf_client.get_int(self.applet.gconf_path + "/cols")
        if not gconf_cols > 0:
            gconf_cols = 5
        self.cols.set_text(str(gconf_cols))       
        hbox21.pack_start(self.cols, True, True, 0)
        #               </entry>
        #               <label>
        label_times = gtk.Label("X")
        hbox21.pack_start(label_times, True, True, 0)
        #               </label>
        #               <entry>
        self.rows = gtk.Entry()
        self.rows.set_width_chars(3)
        self.rows.set_alignment(0.5)
        gconf_rows = self.applet.gconf_client.get_int(self.applet.gconf_path + "/rows")
        if not gconf_rows > 0:
            gconf_rows = 4
        self.rows.set_text(str(gconf_rows))
        hbox21.pack_start(self.rows, True, True, 0)
        #               <entry />
        #           </hbox>
        #           <hbox>
        hbox22 = gtk.HBox(False, 2)
        vbox2.pack_start(hbox22, True, True, 0)
        #               <label>
        label22 = gtk.Label(_("Icon size (inside stacks):"))
        hbox22.pack_start(label22, True, True, 0)
        #               </label>
        #               <spinbutton>
        gconf_icon_size = self.applet.gconf_client.get_int(self.applet.gconf_path + "/icon_size")
        if not gconf_icon_size > 0:
            gconf_icon_size = 48
        spin21_adj = gtk.Adjustment(gconf_icon_size, 24, 96, 2, 2, 0)
        self.spin21 = gtk.SpinButton(spin21_adj, 0.5, 0)
        hbox22.pack_start(self.spin21, True, True, 0)
        #               </spinbutton>
        #           </hbox>
        #       </vbox>
        #   </alignment>

        # page 3: the behavior
        #   <alignment>
        label3 = gtk.Label(_("Behavior"))
        page3 = gtk.Alignment(0, 0, 0, 0)
        page3.set_padding(10, 10, 20, 20)
        self.notebook.append_page(page3, label3)
        #       <vbox>
        vbox3 = gtk.VBox(False, 2)
        page3.add(vbox3)
        #           <label>
        lbl_actions = gtk.Label(_("In most OS configurations, the <b>CTRL</b>, <b>ALT</b> and <b>SHIFT</b> are the modifiers that determine what drag operation is used."))
        lbl_actions.set_use_markup(True)
        lbl_actions.set_line_wrap(True)
        vbox3.pack_start(lbl_actions, True, False, 0)
        #           </label>
        #           <hbox>
        hbox_ops = gtk.HBox(False, 0)
        vbox3.pack_start(hbox_ops, False, False, 0)
        #               <label>
        lbl_fileops = gtk.Label(_("Enable file-operations:"))
        hbox_ops.pack_start(lbl_fileops, False, False, 0)
        #               </label>
        #               <checkbutton>
        self.chk_copy = gtk.CheckButton(_("Copy")) 
        self.chk_copy.set_active(True)
        hbox_ops.pack_start(self.chk_copy, False, False, 2)
        #               </checkbutton>
        #               <checkbutton>
        self.chk_move = gtk.CheckButton(_("Move"))
        self.chk_move.set_active(True)
        hbox_ops.pack_start(self.chk_move, False, False, 2)
        #               </checkbutton>
        #               <checkbutton>
        self.chk_link = gtk.CheckButton(_("Link"))
        self.chk_link.set_active(True)
        hbox_ops.pack_start(self.chk_link, False, False, 2)
        #               </checkbutton>
        actions = self.applet.gconf_client.get_int(self.applet.gconf_path + "/file_operations")
        if actions > 0:
            if (actions & gtk.gdk.ACTION_COPY) == 0:
                self.chk_copy.set_active(False)
            if (actions & gtk.gdk.ACTION_MOVE) == 0:
                self.chk_move.set_active(False)
            if (actions & gtk.gdk.ACTION_LINK) == 0:
                self.chk_link.set_active(False)
        #           </hbox>
        #       </vbox>
        #   </alignment>

        # page 4: about
        #   <alignment>
        label4 = gtk.Label(_("About"))
        page4 = gtk.Alignment(0, 0, 0, 0)
        page4.set_padding(10, 10, 20, 20)
        self.notebook.append_page(page4, label4)
        #       <vbox> 
        vbox4 = gtk.VBox(False, 2)
        page4.add(vbox4)
        #           <label>
        about_label = gtk.Label(_("<big><b>Stacks: applet for Avant Window Navigator</b></big>\n\nTODO: description\n\nauthor: Timon ter Braak"))
        about_label.set_line_wrap(True)                                 
        about_label.set_use_markup(True)
        vbox4.pack_start(about_label, True, True, 0)
        #           </label>
        #       </vbox>
        #   </alignment>
       
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
        if int(self.spin21.get_value()) > 0:
            self.applet.gconf_client.set_int(self.applet.gconf_path + "/icon_size",
                                                int(self.spin21.get_value()) )

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

