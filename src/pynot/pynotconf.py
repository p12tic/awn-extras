#!/usr/bin/python
"""
PyNotConfig v0.20 - Awn Notification/system tray config manager.
Copyright (c) 2008 Nathan Howard (triggerhapp@googlemail.com)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

# Forgive me, comments are completely lacking and source is obfuscated.
# For now, make do that it just works ;)

import awn
import gtk
import gtk.glade
import os

global D_BG_COLOR, D_CUSTOM_Y, D_HIGH, D_BORDER, D_TRANS, D_USEIM, D_IMPATH, D_USEGTK
D_BG_COLOR="0x0070E0"
D_CUSTOM_Y=10
D_HIGH=2
D_BORDER=True
D_TRANS=False
D_ZEROPID=True
D_USEIM=False
D_USEGTK=True
D_ICONSIZE=24
D_IMPATH="/".join(__file__.split("/")[:-1])+"/pattern.png"


def activate_entry(self):

    impath.set_sensitive(useim.get_active())
 
def close_window(self):

    window.destroy()

def endstuff(self):

    gtk.main_quit()

def savestuff(self):

    nbg=bg_color.get_color()
    ntbg=nbg.to_string()
    r=int("0x"+ntbg[1:3], 0)
    g=int("0x"+ntbg[5:7], 0)
    b=int("0x"+ntbg[9:11], 0)
    final = "0x%02X%02X%02X" % (r, g, b)
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP, "BG_COLOR", final)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "CUSTOM_Y", int(custom_y.get_value()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "HIGH", int(high.get_value()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "BORDER", int(border.get_active()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "ZEROPID", int(pid.get_active()))
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,
        "IMPATH", impath.get_text())
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "USEIM", int(useim.get_active()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "ICONSIZE", int(iconsize.get_value()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,
        "USEGTK", int(usegtk.get_active()))
    window.destroy()


awn_options=awn.Config('pynot', None)
BG_COLOR = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP, "BG_COLOR")
CUSTOM_Y = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y")
HIGH = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "HIGH")
BORDER = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "BORDER")
TRANS = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "TRANS")
ZEROPID = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "ZEROPID")
USEIM = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "USEIM")
IMPATH = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP, "IMPATH")
ICONSIZE = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE")
USEGTK = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "USEGTK")
if(HIGH==0):
    HIGH = D_HIGH
    BORDER = D_BORDER
    CUSTOM_Y = D_CUSTOM_Y
    BG_COLOR = D_BG_COLOR
    TRANS = D_TRANS
    ZEROPID = D_ZEROPID
    USEIM = D_USEIM
    IMPATH = D_IMPATH
    ICONSIZE = D_ICONSIZE
    USEGTK = D_USEGTK
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP, "BG_COLOR", BG_COLOR)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "BORDER", BORDER)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y", CUSTOM_Y)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "HIGH", HIGH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "TRANS", TRANS)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "ZEROPID", ZEROPID)
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP, "IMPATH", IMPATH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "USEIM", USEIM)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE", ICONSIZE)

if(IMPATH==""):
    IMPATH=D_IMPATH
#print ICONSIZE

if(ICONSIZE==0):
    ICONSIZE=D_ICONSIZE

r = int("0x"+BG_COLOR[2:4], 0)*256
g = int("0x"+BG_COLOR[4:6], 0)*256
b = int("0x"+BG_COLOR[6:8], 0)*256
cbg=gtk.gdk.Color(r, g, b, 0)

glade_path = os.path.join(os.path.dirname(__file__),
                          "pynot-prefs.glade")
wTree = gtk.glade.XML(glade_path)

window = wTree.get_widget("dialog1")
window.set_icon(gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(__file__), "pynot.svg")))

ok_button = wTree.get_widget("okButton")
cancel_button = wTree.get_widget("cancelButton")

high = wTree.get_widget("iconRowsSpinbutton")
custom_y = wTree.get_widget("offsetSpinbutton")
bg_color = wTree.get_widget("bgColorbutton")
border = wTree.get_widget("roundedCheckbutton")
pid = wTree.get_widget("pidCheckbutton")
useim = wTree.get_widget("useImgRadiobutton")
usegtk = wTree.get_widget("useGtkRadiobutton")
usecolor =  wTree.get_widget("useCustomColorRadiobutton")
iconsize = wTree.get_widget("iconSizeSpinbutton")
impath = wTree.get_widget("imagePathEntry")

bg_color.set_color(cbg)
high.set_value(HIGH)
custom_y.set_value(CUSTOM_Y)
border.set_active(BORDER)
pid.set_active(ZEROPID)
usegtk.set_active(USEGTK)
useim.set_active(USEIM)
usecolor.set_active(not USEGTK and not USEIM)
impath.set_sensitive(USEIM)
impath.set_text(IMPATH)
iconsize.set_value(ICONSIZE)

useim.connect("toggled", activate_entry)
window.connect("destroy", endstuff)
ok_button.connect("clicked", savestuff)
cancel_button.connect("clicked", close_window)

window.show_all()
gtk.main()
