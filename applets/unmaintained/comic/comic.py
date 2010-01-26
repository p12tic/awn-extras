#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Name:        comic.py
# Version:     .5.
# Date:        10-15-07
# Description: A python Applet for the avant-windows-navigator to display comic strips.
#
# Authors:     cj13
#             pavpanchekha

import sys, os
import gobject
import gtk
import awn
import comicdialog
#default comic
GETWHAT = 'getdilbert.py'
showhover = False

class App (awn.AppletSimple):
    titleText = "Daily Comic"
    visible = False

    def __init__ (self, uid, orient, height):
        awn.AppletSimple.__init__ (self, uid, orient, height)
        self.set_awn_icon('comic', 'comic-applet')

        self.title = awn.awn_title_get_default ()
        self.dialog = awn.AppletDialog (self)
        self.connect ("button-press-event", self.button_press)
        self.connect ("enter-notify-event", self.enter_notify)
        self.connect ("leave-notify-event", self.leave_notify)
        self.dialog.connect ("focus-out-event", self.dialog_focus_out)

        # Setup popup menu
        self.popup_menu = self.create_default_menu()
        dil_item = gtk.MenuItem("Dilbert")
        pnut_item = gtk.MenuItem("Peanuts")
        born_item = gtk.MenuItem("The Born Loser")
        ben_item = gtk.MenuItem("Ben")
        ferdnand_item = gtk.MenuItem("Ferdnand")
        nancy_item = gtk.MenuItem("Nancy")
        pickles_item = gtk.MenuItem("Pickles")
        garfield_item = gtk.MenuItem("Garfield")
        uf_item = gtk.MenuItem("User Friendly")
        wiz_item = gtk.MenuItem("Wizard of ID")
        xkcd_item = gtk.MenuItem("xkcd")
        showho_item = gtk.CheckMenuItem("Hide Strip on Hover")
        self.popup_menu.append(dil_item)
        self.popup_menu.append(pnut_item)
        self.popup_menu.append(born_item)
        self.popup_menu.append(ben_item)
        self.popup_menu.append(ferdnand_item)
        self.popup_menu.append(nancy_item)
        self.popup_menu.append(pickles_item)
        self.popup_menu.append(garfield_item)
        self.popup_menu.append(uf_item)
        self.popup_menu.append(wiz_item)
        self.popup_menu.append(xkcd_item)
        self.popup_menu.append(showho_item)
        dil_item.connect_object("activate",self.dil_callback,self)
        pnut_item.connect_object("activate",self.pnut_callback,self)
        born_item.connect_object("activate",self.born_callback,self)
        ben_item.connect_object("activate",self.ben_callback,self)
        ferdnand_item.connect_object("activate",self.ferdnand_callback,self)
        nancy_item.connect_object("activate",self.nancy_callback,self)
        pickles_item.connect_object("activate",self.pickles_callback,self)
        garfield_item.connect_object("activate",self.garfield_callback,self)
        uf_item.connect_object("activate",self.uf_callback,self)
        wiz_item.connect_object("activate",self.wiz_callback,self)
        xkcd_item.connect_object("activate",self.xkcd_callback,self)
        showho_item.connect_object("activate",self.showho_callback,self)
        dil_item.show()
        pnut_item.show()
        born_item.show()
        ben_item.show()
        ferdnand_item.show()
        nancy_item.show()
        pickles_item.show()
        garfield_item.show()
        uf_item.show()
        wiz_item.show()
        xkcd_item.show()
        showho_item.show()

        self.build_dialog()


    def build_dialog(self):
        #print "Getting Comic"

        getit = 'python ' + os.path.dirname (__file__) + '/' + GETWHAT
        os.system(getit)

        self.dialog = awn.AppletDialog (self)
        self.dialog.set_title("Comic")

        box = gtk.VBox()
        comic = comicdialog.ComicDialog()
        box.pack_start(comic,False,False,0)
        box.show_all()
        self.dialog.add(box)

        self.timer = gobject.timeout_add (3600000, self.build_dialog)


    def button_press (self, widget, event):
        if event.button == 3:
                # right click
                self.title.hide(self)
                self.visible = False
                self.dialog.hide()
                self.popup_menu.popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            if self.visible:
                self.dialog.hide()
                self.title.hide(self)
            else:
                self.title.hide(self)
                self.dialog.show_all()
            self.visible = not self.visible


    def dil_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getdilbert.py'
        self.build_dialog()


    def pnut_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getpeanuts.py'
        self.build_dialog()

    def born_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getborn.py'
        self.build_dialog()

    def ben_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getben.py'
        self.build_dialog()

    def ferdnand_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getferdnand.py'
        self.build_dialog()

    def nancy_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getnancy.py'
        self.build_dialog()

    def pickles_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getpickles.py'
        self.build_dialog()

    def garfield_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getgarfield.py'
        self.build_dialog()

    def uf_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getuf.py'
        self.build_dialog()

    def wiz_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getwiz.py'
        self.build_dialog()

    def xkcd_callback(self, widget):
        global GETWHAT
        GETWHAT = 'getxkcd.py'
        self.build_dialog()

    def showho_callback(self, widget):
        global showhover
        showhover = not showhover


    def dialog_focus_out (self, widget, event):
        self.visible = False
        self.dialog.hide()


    def enter_notify (self, widget, event):
        global showhover
        self.title.show (self, self.titleText)
        if showhover:
            self.title.hide(self)
            self.dialog.show_all()
            self.visible = False

    def leave_notify (self, widget, event):
        global showhover
        self.title.hide(self)
        if showhover:
            self.dialog.hide()
            self.visible = False


if __name__ == "__main__":
    awn.init (sys.argv[1:])
    #print "main %s %d %d" % (awn.uid, awn.orient, awn.height)
    applet = App(awn.uid, awn.orient, awn.height)
    awn.embed_applet(applet)
    applet.show_all()
    gtk.main()
