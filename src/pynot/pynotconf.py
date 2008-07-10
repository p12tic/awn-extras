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
from distutils import sysconfig
import locale, os, pwd, select, sys, time
import gtk
import gtk.glade

global D_BG_COLOR,D_CUSTOM_Y, D_HIGH,D_BORDER,D_TRANS,D_USEIM,D_IMPATH
D_BG_COLOR="0x0070E0"
D_CUSTOM_Y=10
D_HIGH=2
D_BORDER=True
D_TRANS=False
D_ZEROPID=True
D_USEIM=False
D_IMPATH="path/to/image"



def endstuff(self):
    gtk.main_quit()

def savestuff(self):
    nbg=bg_color.get_color()
    ntbg=nbg.to_string()
    r=int("0x"+ntbg[1:3],0)
    g=int("0x"+ntbg[5:7],0)
    b=int("0x"+ntbg[9:11],0)
    final = "0x%02X%02X%02X" % (r,g,b)
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,"BG_COLOR",final)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"CUSTOM_Y",int(custom_y.get_value()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"HIGH",int(high.get_value()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"BORDER",int(border.get_active()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"TRANS",int(trans.get_active()))
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"ZEROPID",int(pid.get_active()))
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,"IMPATH",impath.get_text())
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"USEIM",int(useim.get_active()))
 


awn_options=awn.Config('pysystemtray',None)
BG_COLOR = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"BG_COLOR")
CUSTOM_Y = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"CUSTOM_Y")
HIGH     = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"HIGH"    )
BORDER   = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"BORDER"  )
TRANS    = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"TRANS"   )
ZEROPID  = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"ZEROPID" )
USEIM    = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"USEIM"   )
IMPATH   = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"IMPATH"  )
if(HIGH==0):
    HIGH     = D_HIGH
    BORDER   = D_BORDER
    CUSTOM_Y = D_CUSTOM_Y
    BG_COLOR = D_BG_COLOR
    TRANS    = D_TRANS
    ZEROPID  = D_ZEROPID
    USEIM    = D_USEIM
    IMPATH   = D_IMPATH
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,"BG_COLOR",BG_COLOR)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"BORDER",BORDER)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"CUSTOM_Y",CUSTOM_Y)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"HIGH",HIGH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"TRANS",TRANS)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"ZEROPID",ZEROPID)
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,"IMPATH",IMPATH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"USEIM",USEIM)

if(IMPATH==None):
    IMPATH="Image here"



r = int("0x"+BG_COLOR[2:4],0)*256
g = int("0x"+BG_COLOR[4:6],0)*256
b = int("0x"+BG_COLOR[6:8],0)*256
cbg=gtk.gdk.Color(r,g,b,0)

window= gtk.Window(gtk.WINDOW_TOPLEVEL)
vbox=gtk.VBox()
window.add(vbox)
hbox=gtk.HBox()
alldone=gtk.Button("Save")
t1=gtk.Label("PyTray Config")
t2=gtk.Label("Number of Icons High")
t3=gtk.Label("Offset from Bottom")
t4=gtk.Label("Background Colour")
adj=gtk.Adjustment(1,1,5,1,1,0)
high=gtk.SpinButton(adj,1,0)
adj2=gtk.Adjustment(45,0,100,1,1,0)
custom_y=gtk.SpinButton(adj2,1,0)
bg_color=gtk.ColorButton()
border=gtk.CheckButton("Use a Rounded Border",False)
trans=gtk.CheckButton("Use Transparent Background (BUGGY)",False)
pid=gtk.CheckButton("Do Not Show Icons for PID=0.",False)
useim=gtk.CheckButton("Use Image",False)
impath=gtk.Entry()

bg_color.set_color(cbg)
high.set_value(HIGH)
custom_y.set_value(CUSTOM_Y)
border.set_active(BORDER)
trans.set_active(TRANS)
pid.set_active(ZEROPID)
useim.set_active(USEIM)
impath.set_text(IMPATH)

hbox1=gtk.HBox()
hbox2=gtk.HBox()
hbox3=gtk.HBox()
hbox4=gtk.HBox()
hbox5=gtk.HBox()
hbox6=gtk.HBox()
hbox7=gtk.HBox()


vbox.add(t1)
hbox1.add(high)
hbox1.add(t2)
vbox.add(hbox1)
hbox2.add(custom_y)
hbox2.add(t3)
vbox.add(hbox2)
vbox.add(t4)
vbox.add(bg_color)
hbox3.add(border)
vbox.add(hbox3)
hbox4.add(trans)
hbox5.add(pid)
hbox6.add(useim)
vbox.add(hbox4)
vbox.add(hbox5)
vbox.add(hbox6)
hbox7.add(impath)
vbox.add(hbox7)

hbox.add(alldone)
vbox.add(hbox)
window.show_all()
window.connect("destroy",endstuff)
alldone.connect("clicked",savestuff)
gtk.main()


