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

        self.applet_icon_empty = self.applet.gconf_client.get_string(self.applet.gconf_path + "/applet_icon_empty")
        if self.applet_icon_empty == None:
            self.applet_icon_empty = _to_full_path("icons/stacks-drop.svg")
        self.applet_icon_full = self.applet.gconf_client.get_string(self.applet.gconf_path + "/applet_icon_full")
        if self.applet_icon_full == None:
            self.applet_icon_full = _to_full_path("icons/stacks-full.svg")      

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
        vbox1 = gtk.VBox(False, 4)
        page1.add(vbox1)
        #           <label>
        info_label = gtk.Label(_("As default a <b>file</b> is used as backend, and the stack will just contain a group of links to files (symlinks).\n\nIf you select a <b>folder</b> as backend, the stack will support real file operations, so that you can copy, move and link files to that folder."))
        info_label.set_use_markup(True)
        info_label.set_line_wrap(True)
        vbox1.pack_start(info_label, True, True, 0)
        #           </label>
        #           <hbox>
        type_hbox = gtk.HBox(False, 0)
        vbox1.pack_start(type_hbox, True, True, 0)
        #               <label>
        select_label = gtk.Label(_("Select <b>folder backend</b> for this stack:"))
        select_label.set_use_markup(True)
        type_hbox.pack_start(select_label, True, True, 0)
        #               </label>
        #               <button>
        fbutton = gtk.Button(gtk.STOCK_OPEN)
        fbutton.set_use_stock(True)
        fbutton.connect("button-release-event", self.activate_filechooser)
        type_hbox.pack_end(fbutton, True, True, 2)
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
        vbox2 = gtk.VBox(False, 4)
        page2.add(vbox2)
        #           <hbox>
        hbox21 = gtk.HBox(False, 0)
        vbox2.pack_start(hbox21, True, True, 0)
        #               <label>
        label_dim = gtk.Label(_("Maximum dimension (cols x rows):"))
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
        hbox21.pack_start(self.cols, True, True, 2)
        #               </entry>
        #               <label>
        label_times = gtk.Label("X")
        hbox21.pack_start(label_times, True, True, 1)
        #               </label>
        #               <entry>
        self.rows = gtk.Entry()
        self.rows.set_width_chars(3)
        self.rows.set_alignment(0.5)
        gconf_rows = self.applet.gconf_client.get_int(self.applet.gconf_path + "/rows")
        if not gconf_rows > 0:
            gconf_rows = 4
        self.rows.set_text(str(gconf_rows))
        hbox21.pack_start(self.rows, True, True, 1)
        #               <entry />
        #           </hbox>
        #           <hbox>
        hbox22 = gtk.HBox(False, 0)
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
        self.spin21.set_numeric(True)
        self.spin21.set_snap_to_ticks(True)
        self.spin21.set_width_chars(3)
        self.spin21.set_alignment(0.5)
        hbox22.pack_start(self.spin21, True, True, 2)
        #               </spinbutton>
        #           </hbox>
        #           <separator>
        hseparator21 = gtk.HSeparator()
        vbox2.pack_start(hseparator21, True, True, 0)
        #           <hbox>
        hbox23 = gtk.HBox(False, 0)
        vbox2.pack_start(hbox23, True, True, 0)
        #               <label>
        label23 = gtk.Label(_("Applet icon:"))
        hbox23.pack_start(label23, True, True, 0)
        #               </label>
        #               <button>
        self.button21 = gtk.Button(_("Empty"))
        e_icon = gdk.pixbuf_new_from_file (self.applet_icon_empty)
        if e_icon:
            image21 = gtk.Image()
            image21.set_from_pixbuf(e_icon)
            self.button21.set_image(image21)
        self.button21.connect("button-release-event", self.icon_button, "empty")
        hbox23.pack_start(self.button21, True, True, 2)
        #               </button>
        #               <button>
        self.button22 = gtk.Button(_("Full"))
        f_icon = gdk.pixbuf_new_from_file (self.applet_icon_full)
        if f_icon:
            image22 = gtk.Image()
            image22.set_from_pixbuf(f_icon)
            self.button22.set_image(image22)
        self.button22.connect("button-release-event", self.icon_button, "full")
        hbox23.pack_start(self.button22, True, True, 2)
        #               </button>
        #           </hbox>
        #           <hbox>
        hbox24 = gtk.HBox(False, 2)
        vbox2.pack_start(hbox24, True, True, 0)
        #               <label>
        label24 = gtk.Label(_("Composite last stack icon onto \"full\" applet icon:"))
        label24.set_use_markup(True)
        hbox24.pack_start(label24, True, True, 0)
        #               </label>
        #               <checkbutton>
        self.checkbutton21 = gtk.CheckButton(_("Enable"))
        composite = self.applet.gconf_client.get_bool(self.applet.gconf_path + "/composite_icon")
        # TODO: howto "detect" True by default
        if composite:
            self.checkbutton21.set_active(True)
        else:
            self.checkbutton21.set_active(False)
        hbox24.pack_start(self.checkbutton21, True, True, 2)
        #               </checkbutton>
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
        vbox3 = gtk.VBox(False, 4)
        page3.add(vbox3)
        #           <label>
        label31 = gtk.Label(_("In most OS configurations, the <b>CTRL</b>, <b>ALT</b> and <b>SHIFT</b> are the modifiers that determine what drag operation is used on the <b>folder</b> backend.\nUsing a <b>file backend</b> (default) allows only for symlinks."))
        label31.set_use_markup(True)
        label31.set_line_wrap(True)
        vbox3.pack_start(label31, True, False, 0)
        #           </label>
        #           <hbox>
        hbox31 = gtk.HBox(False, 0)
        vbox3.pack_start(hbox31, False, False, 0)
        #               <label>
        label32 = gtk.Label(_("Restrict folder-operations to:"))
        hbox31.pack_start(label32, False, False, 0)
        #               </label>
        #               <checkbutton>
        self.chk_copy = gtk.CheckButton(_("Copy")) 
        self.chk_copy.set_active(True)
        hbox31.pack_start(self.chk_copy, False, False, 2)
        #               </checkbutton>
        #               <checkbutton>
        self.chk_move = gtk.CheckButton(_("Move"))
        self.chk_move.set_active(True)
        hbox31.pack_start(self.chk_move, False, False, 2)
        #               </checkbutton>
        #               <checkbutton>
        self.chk_link = gtk.CheckButton(_("Link"))
        self.chk_link.set_active(True)
        hbox31.pack_start(self.chk_link, False, False, 2)
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
        vbox4 = gtk.VBox(False, 4)
        page4.add(vbox4)
        #           <label>
        label41 = gtk.Label(_("<big><b>Stacks: applet for Avant Window Navigator</b></big>\n\nTODO: description\n\nauthor: Timon ter Braak"))
        label41.set_line_wrap(True)                                 
        label41.set_use_markup(True)
        vbox4.pack_start(label41, True, True, 0)
        #           </label>
        #       </vbox>
        #   </alignment>
       
        self.window.show_all()


    def activate_filechooser(self, widget, event):
        filesel = gtk.FileChooserDialog("Select backend destination:", 
                                        None, 
                                        gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER |
                                        gtk.FILE_CHOOSER_ACTION_SAVE, 
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                        gtk.STOCK_APPLY, gtk.RESPONSE_OK), 
                                        None)
        filesel.set_default_response(gtk.RESPONSE_OK)
        gconf_backend = self.applet.gconf_client.get_string(self.applet.gconf_path + "/backend")
        if gconf_backend != None:
            filesel.set_current_folder(gconf_backend)
        else:
            filesel.set_current_folder(os.path.expanduser("~"))

        selected = None
        if filesel.run() == gtk.RESPONSE_OK:
            self.backend = filesel.get_filename()
        filesel.destroy()
        

    def icon_button(self, widget, event, user_data):
        print "icon button pushed: ", user_data
        filesel = gtk.FileChooserDialog("Select applet icon:", 
                                        None, 
                                        gtk.FILE_CHOOSER_ACTION_OPEN, 
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                        gtk.STOCK_APPLY, gtk.RESPONSE_OK), 
                                        None)
        filesel.set_default_response(gtk.RESPONSE_OK)
        img_filter = gtk.FileFilter()
        img_filter.set_name(_("Supported image types"))
        # PyGTK 2.6 and above:
        img_filter.add_pixbuf_formats()
        # else:
        #for format in gtk.gdk.pixbuf_get_formats():
        #    for m in format['mime_types']:
        #        img_filter.add_mime_type(m)
        filesel.add_filter(img_filter)
        if user_data == "empty":
            filesel.set_filename(self.applet_icon_empty)
        else:
            filesel.set_filename(self.applet_icon_full)

        selected = None
        if filesel.run() == gtk.RESPONSE_OK:
            icon = gdk.pixbuf_new_from_file(filesel.get_filename())
            if icon != None:
                image = gtk.Image()
                image.set_from_pixbuf(icon)
                if user_data == "empty":
                    self.applet_icon_empty = filesel.get_filename()
                    self.button21.set_image(image)
                else:
                    self.applet_icon_full = filesel.get_filename()
                    self.button22.set_image(image)
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
        if self.checkbutton21.get_active():
            self.applet.gconf_client.set_bool(self.applet.gconf_path + "/composite_icon",
                                                True)
        else:
            self.applet.gconf_client.set_bool(self.applet.gconf_path + "/composite_icon",
                                                False)

        self.applet.gconf_client.set_string(self.applet.gconf_path + "/applet_icon_empty",
                                                self.applet_icon_empty)
        self.applet.gconf_client.set_string(self.applet.gconf_path + "/applet_icon_full",
                                                self.applet_icon_full)

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

