#!/usr/bin/python
"""
PyNot v0.15 - Awn Notificaion/system tray.
Copyright (c) 2008 Nathan Howard (triggerhapp@googlemail.com)
         2003-2005 Jon Gelo      (ziljian@users.sourceforge.net)

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

# Would especially like to thank the guys at #awn, without whom
# I would still be trying to add this widget to the panel :)


from awn.extras import AWNLib # Interact with awn
import gtk # For GUI building
from gtk import gdk
from distutils import sysconfig
from Xlib import X, display, error, Xatom, Xutil
import Xlib.protocol.event
import locale, os, pwd, select, sys, time
import pdb
import gobject
import awn
import cairo
import math
import subprocess
import atexit
#Default Values
global D_BG_COLOR,D_CUSTOM_Y, D_HIGH,D_ALLOW_COL,D_REFRESH,D_DIVIDEBYZERO,D_BORDER,D_ZEROPID,D_IMPATH,D_USEIM,D_ICONSIZE
D_BG_COLOR="0x0070E0"
D_CUSTOM_Y=50
D_HIGH=2
D_ALLOW_COL=50
D_REFRESH=10
D_DIVIDEBYZERO=False
D_BORDER=True
D_ZEROPID=True
D_IMPATH="Your image here"
D_USEIM = False
D_ICONSIZE=32

# And thier current!
global BG_COLOR,SHADE,FONT,TRAY_I_WIDTH,CUSTOM_Y, HIGH,ALLOW_COL,REFRESH,DIVIDEBYZERO,BORDER,ZEROPID,IMPATH,USEIM,ICONSIZE
TRAY_I_WIDTH=24
FONT="bitstrem vera sans-8"
BG_COLOR="0x0070E0"
SHADE=255
CUSTOM_Y=50
HIGH=2
ALLOW_COL=50
REFRESH=1000
DIVIDEBYZERO=False
BORDER=True
ZEROPID=True
IMPATH=""
USEIM=False
ICONSIZE=TRAY_I_WIDTH

global awn_options


class Obj(object):
#----------------------------------------------------------------------------
    """ Multi-purpose class """
    #----------------------------
    def __init__(self, **kwargs):
    #----------------------------
        self.__dict__.update(kwargs)

class mywidget(gtk.Widget):
    def __init__(self, display,error,parent_window,gtkwin):
        gtk.Widget.__init__(self)
        self.curr_x=10
        self.curr_y=48
        self.OLDrpm = None
        self.parent_window=parent_window
        self.dsp = display.Display()
        self.scr = self.dsp.screen()
        self.root    = self.scr.root
        self.error   = error.CatchError()
        self.gtkwin=gtkwin
        self.realized= 0
        self.lastw=0
        self.DBGCOUNT=0
        self.lastdraw=0
        self.savebmp = None
        self.needredraw=False
        self.wind = self.root.create_window(600, 300, 80, 48,
                0, self.scr.root_depth, window_class=X.InputOutput,
                visual=X.CopyFromParent, colormap=X.CopyFromParent,
                event_mask=(X.ExposureMask|X.ButtonPressMask|X.ButtonReleaseMask|X.EnterWindowMask))
#        ppinit(self.wind.id,FONT)
        self.tray = Obj(id="tray", tasks={}, order=[], first=0, last=0, window=self.wind)
    
        self._OPCODE = self.dsp.intern_atom("_NET_SYSTEM_TRAY_OPCODE")
        self.manager = self.dsp.intern_atom("MANAGER")
        self.selection = self.dsp.intern_atom("_NET_SYSTEM_TRAY_S%d" % self.dsp.get_default_screen())
        self.selowin = self.scr.root.create_window(-1, -1, 1, 1, 0, self.scr.root_depth)
        self.selowin.set_selection_owner(self.selection, X.CurrentTime)
        self.tr__sendEvent(self.root, self.manager,[X.CurrentTime, self.selection,self.selowin.id], (X.StructureNotifyMask))
        self.tr__setProps(self.dsp, self.wind)
        self.tr__setStruts(self.wind)
        self.wind.map()
        self.dsp.flush()
        appchoice=gtk.MenuItem("PyNot Setup")
        self.dockmenu=self.gtkwin.create_default_menu()
        appchoice.connect("activate",self.OpenConf)
        self.dockmenu.append(appchoice)
        appchoice.show()


#        self.tr__updatePanel(self.root,self.wind)

    def do_realize(self):
        self.set_flags(gtk.REALIZED)
        #rgba = self.scr.get_rgba_colormap()
        #gwin.set_colormap(rgba)
        self.gwin=gdk.window_foreign_new(self.wind.id)
        self.gwin.reparent(self.parent_window.window,0,0)

        self.gwin.set_user_data(self)
        self.style.attach(self.gwin)
#        self.style.set_background(self.gwin, gdk.Color(255,0,0))
        self.tr__updatePanel(self.root,self.wind)
#        self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#FF0000"))
        self.style.set_background(self.gwin, gtk.STATE_NORMAL)
        self.gwin.move_resize(*self.allocation)
#        self.gwin.connect("expose-event", self.do_expose_event)

        self.tr__updatePanel(self.root,self.wind)
        gobject.timeout_add(REFRESH,self.tr__testTiming)
        if(REFRESH>80):
            gobject.timeout_add(REFRESH,self.tr__updateAlpha)
#        self.gwin.set_composite(True)
        self.realized= 1



    
    def do_unrealize(self):
        # The do_unrealized method is responsible for freeing the GDK resources
        return 1;

    def do_size_request(self,requisition):
        requisition.width=self.curr_x
        requisition.height=self.curr_y

    def do_size_allocate(self, allocation):
        # The do_size_allocate is called by when the actual size is known
        # and the widget is told how much space could actually be allocated

        self.allocation = allocation

        # If we're realized, move and resize the window to the
        # requested coordinates/positions
        if self.flags() & gtk.REALIZED:
            self.gwin.move_resize(*allocation)
 
    def do_expose_event(self, event):
        self.tr__updateAlpha()

        return True




    def tr__taskDelete(self,tid):
    #--------------------------------
        """ Delete the given task ID if it's in the tray/task list """
        if tid in self.tray.tasks:
            del self.tray.tasks[tid]
            self.tray.order.remove(tid)
            return 1
        return 0

    def tr__updatePanel(self,root,win):
        rr= self.gwin.get_geometry()
        offsety=rr[3]-((HIGH*ICONSIZE)+CUSTOM_Y)
        self.lastdraw = self.DBGCOUNT
        space=2
        if(BORDER==True):
            space+=5
        tempy=0
        for t in self.tray.tasks.values():
            if TRAY_I_WIDTH:
                t.width = TRAY_I_WIDTH
                #space += t.width
                if(tempy==0):
                    space+=t.width
                if(tempy < HIGH-1):
                    tempy+=1
                else:
                    tempy=0
        if(BORDER==True):
            space+=5
        self.set_size_request(space,CUSTOM_Y+HIGH*ICONSIZE)

        self.tr__updateBackground(self.root, win)
        self.tr__clearPanel(0, 0, 0, 0)
        self.curr_x=0
        if(BORDER==True):
            self.curr_x+=5
        self.curr_y=0
        for tid in self.tray.order:
            t = self.tray.tasks[tid]
            t.x = self.curr_x
            t.y = offsety+self.curr_y*ICONSIZE
            t.obj.configure(onerror=self.error, x=t.x, y=t.y, width=t.width, height=t.height)
            t.obj.map(onerror=self.error)
            if(self.curr_y < HIGH-1):
                self.curr_y+=1
            else:
                self.curr_x+=t.width
                self.curr_y=0
        if(self.curr_y == 0):
            self.curr_x+=1
        else:
            self.curr_x+=25
        self.curr_y=offsety+(HIGH)*ICONSIZE
        self.tr__updateAlpha()

    def tr__updateAlpha(self):
        rr= self.gwin.get_geometry()
        offsety=rr[3]-((HIGH*ICONSIZE)+CUSTOM_Y)
        if(self.realized == 1):
            w= self.curr_x
            h= offsety+ (HIGH*ICONSIZE)
            if(BORDER==True):
                w+=10
                h+=10
#            pfft=gdk.Image(gdk.IMAGE_FASTEST, gdk.visual_get_system(),w,h)
#            pfft=self.gwin.copy_to_image(pfft,0,0,0,0,w,h)
#            trayimage=pfft
            bitmap = gtk.gdk.Pixmap(None, w, h, 1)
            cr = bitmap.cairo_create()

            # Clear the bitmap
            cr.set_source_rgb(0, 0, 0)
            cr.set_operator(cairo.OPERATOR_DEST_OUT)
            cr.paint()

            # Draw our shape into the bitmap using cairo
            cr.set_operator(cairo.OPERATOR_OVER)


            if(DIVIDEBYZERO == False):
                # Lets not do the impossible. Just draw a box around it.
                if(BORDER == True):
                    newh= (HIGH*ICONSIZE)
                    cr.set_line_width(1)

                    cr.rectangle(0,offsety+1,w,newh-2)
                    cr.fill()
                    cr.rectangle(6,offsety-5,w-16,newh+10)
                    cr.fill()
                    cr.rectangle(1,offsety-1,w-6,newh+2)
                    cr.fill()
                    cr.rectangle(2,offsety-2,w-8,newh+4)
                    cr.fill()
                    cr.rectangle(3,offsety-3,w-10,newh+6)
                    cr.fill()
                    cr.rectangle(4,offsety-4,w-12,newh+8)
                    cr.fill()




                else:
                    cr.rectangle(0,CUSTOM_Y,w,h)
                    cr.fill()

                self.gwin.shape_combine_mask(bitmap, 0, 0)
            else:
                # THIS BIT deals with Transparency for all of the BG colour
                cr.rectangle(0,CUSTOM_Y,w,h)
                cr.fill()
                self.gwin.shape_combine_mask(bitmap, 0, 0)
                # And ^THIS^ is the bit that causes flicker...
                # If you take this away, any updates to the image will not get
                # seen by the "trayimage" comming up. Thus animated icons or
                # new icons are not seen until a resize

                trayimage=gdk.Image(gdk.IMAGE_FASTEST, gdk.visual_get_system(),w,h)
                trayimage=self.gwin.copy_to_image(trayimage,0,0,0,0,w,h)
#                trayimage=pfft



                if(self.savebmp != None):
                    self.gwin.shape_combine_mask(self.savebmp,0,0)
                # Attempt to minimise the time that the background is all shown
                # By borrowing the last mask used. Nasty but shorter flicker

                bitmap = gtk.gdk.Pixmap(None, w, h, 1)
                cr = bitmap.cairo_create()
                # Create a B/W mask. Drawing on a pixel means it is shown.
                # Pixels that arent shown are transparent

                cr.set_source_rgb(0, 0, 0)
                cr.set_operator(cairo.OPERATOR_DEST_OUT)
                cr.paint()
                # Clear the Bitmap
                
                cr.set_operator(cairo.OPERATOR_OVER)
                cr.set_line_width(1)

                bg_r    =int("0x"+BG_COLOR[2:4],0)
                bg_g    =int("0x"+BG_COLOR[4:6],0)
                bg_b    =int("0x"+BG_COLOR[6:8],0)
                # Store the Background colour



                for y in range(CUSTOM_Y,h):
                    for x in range(0,w):
                        # Pixel by pixel checking within the tray area.
                        # This isnt as slow as some might assume! :P
                        col = trayimage.get_pixel(x,y)
                        if(self.tr__isBackground(col,bg_r,bg_g,bg_b)==False):
                            # If its an icon pixel...
                            cr.move_to(x,y)
                            cr.line_to(x,y+1)
                            cr.stroke()
                            # Draw a dodgy line that somehow seems to work :D
                self.gwin.shape_combine_mask(bitmap, 0, 0)
                self.savebmp = bitmap
                # Attach mask and save for next render
        return True

    def tr__isBackground(self,col,bg_r,bg_g,bg_b):
        col_s   = "0x%06X" % col
        if(col_s==BG_COLOR):
            return True
        col_r   =int("0x"+col_s[2:4],0)
        col_g   =int("0x"+col_s[4:6],0)
        col_b   =int("0x"+col_s[6:8],0)

        # Just smile and nod. 

        if(bg_r-ALLOW_COL<col_r and bg_r+ALLOW_COL>col_r):
            if(bg_g-ALLOW_COL<col_g and bg_g+ALLOW_COL>col_g):
                if(bg_b-ALLOW_COL<col_b and bg_b+ALLOW_COL>col_b):
                    return True
        
        return False
  

    def tr__updateBackground(self,root, win):
    #-------------------------------------
        """ Check and update the panel background if necessary """
        self._RPM             = self.dsp.intern_atom("_XROOTPMAP_ID")
        rpm = root.get_full_property(self._RPM, Xatom.PIXMAP)

        if hasattr(rpm, "value"):
            rpm = rpm.value[0]
        else:
            rpm = root.id

#        if self.OLDrpm != rpm:
        self.OLDrpm = rpm
        r = int("0x"+BG_COLOR[2:4],0)
        g = int("0x"+BG_COLOR[4:6],0)
        b = int("0x"+BG_COLOR[6:8],0)
#        ppshade(win.id, rpm, 0, 0, 1, 1,
#            r, g, b, SHADE)

    def tr__clearPanel(self,x1, y1, x2, y2):
    #------------------------------------
        """ Clear panel at the given coordinates """
#        ppclear(self.wind.id, int(x1), int(y1), int(x2), int(y2))

    def tr__sendEvent(self,win, ctype, data, mask=None):
    #------------------------------------------------
        """ Send a ClientMessage event to the root """
        data = (data+[0]*(5-len(data)))[:5]
        ev = Xlib.protocol.event.ClientMessage(window=win, client_type=ctype, data=(32,(data)))

        if not mask:
            mask = (X.SubstructureRedirectMask|X.SubstructureNotifyMask)
        self.root.send_event(ev, event_mask=mask)

    def tr__testTiming(self):
#        self.modify_bg(gtk.STATE_NORMAL,gtk.gdk.color_parse("#FF0000"))
#        self.tr__updatePanel(self.root,self.wind);
        while self.dsp.pending_events()>0:
            e = self.dsp.next_event()
            if e.type == X.ButtonRelease:
                if(e.detail == 3):
                    self.dockmenu.show_all()
                    self.dockmenu.popup(None, None, None, 3, e.time)
                    # RIGHT CLEECK
            if e.type == X.DestroyNotify:
                if self.tr__taskDelete(e.window.id):
                    self.tr__updatePanel(self.root, self.wind)
            if e.type == X.ConfigureNotify:
                task = self.tray.tasks[e.window.id]
                task.obj.configure(onerror=self.error,width=ICONSIZE, height=ICONSIZE)
                self.tr__updatePanel(self.root, self.wind)
            if e.type == X.ClientMessage:
                data = e.data[1][1]
                task = e.data[1][2]
                if e.client_type == self._OPCODE and data == 0:
                    obj = self.dsp.create_resource_object("window",task)
                    pid=0
                    try:
                        pidob= obj.get_property(self._PIDTHING,X.AnyPropertyType,0,1024)
                        pid = pidob.value[0]
                    except:
                        pass
                    if(ZEROPID==False or (ZEROPID==True and pid>0)):

                        obj.reparent(self.tray.window.id,0,0)
                        obj.change_attributes(event_mask=(X.ExposureMask|X.StructureNotifyMask))
                        self.tray.tasks[task] = Obj(obj=obj, x=0, y=0, width=0, height=ICONSIZE,pid=pid)
                        self.tray.order.append(task)
                        self.tr__updatePanel(self.root,self.wind)
#        if(self.curr_x != self.lastw):
#            self.lastw = self.curr_x
#            self.tr__updatePanel(self.root,self.wind)
        if(self.needredraw == True):
            self.tr__updatePanel(self.root,self.wind)
        return True

    def OpenConf(self,thing):
        program = "%s%s"%(path,"pynotconf.py")
        self.config=subprocess.Popen(program)
        return 1

    def tr__setProps(self,dsp, win):
    #----------------------------
        """ Set necessary X atoms and panel window properties """
        self._ABOVE           = dsp.intern_atom("_NET_WM_STATE_ABOVE")
        self._BELOW           = dsp.intern_atom("_NET_WM_STATE_BELOW")
        self._BLACKBOX        = dsp.intern_atom("_BLACKBOX_ATTRIBUTES")
        self._CHANGE_STATE    = dsp.intern_atom("WM_CHANGE_STATE")
        self._CLIENT_LIST     = dsp.intern_atom("_NET_CLIENT_LIST")
        self._CURRENT_DESKTOP = dsp.intern_atom("_NET_CURRENT_DESKTOP")
        self._DESKTOP         = dsp.intern_atom("_NET_WM_DESKTOP")
        self._DESKTOP_COUNT   = dsp.intern_atom("_NET_NUMBER_OF_DESKTOPS")
        self._DESKTOP_NAMES   = dsp.intern_atom("_NET_DESKTOP_NAMES")
        self._HIDDEN          = dsp.intern_atom("_NET_WM_STATE_HIDDEN")
        self._ICON            = dsp.intern_atom("_NET_WM_ICON")
        self._NAME            = dsp.intern_atom("_NET_WM_NAME")
        self._RPM             = dsp.intern_atom("_XROOTPMAP_ID")
        self._SHADED          = dsp.intern_atom("_NET_WM_STATE_SHADED")
        self._SHOWING_DESKTOP = dsp.intern_atom("_NET_SHOWING_DESKTOP")
        self._SKIP_PAGER      = dsp.intern_atom("_NET_WM_STATE_SKIP_PAGER")
        self._SKIP_TASKBAR    = dsp.intern_atom("_NET_WM_STATE_SKIP_TASKBAR")
        self._STATE           = dsp.intern_atom("_NET_WM_STATE")
        self._STICKY          = dsp.intern_atom("_NET_WM_STATE_STICKY")
        self._STRUT           = dsp.intern_atom("_NET_WM_STRUT")
        self._STRUTP          = dsp.intern_atom("_NET_WM_STRUT_PARTIAL")
        self._WMSTATE         = dsp.intern_atom("WM_STATE")
        self._PIDTHING        = dsp.intern_atom("_NET_WM_PID")

        win.set_wm_name("PyPanel")
        win.set_wm_class("pypanel","PyPanel")
        win.set_wm_hints(flags=(Xutil.InputHint|Xutil.StateHint),
            input=0, initial_state=1)
        win.set_wm_normal_hints(flags=(
            Xutil.PPosition|Xutil.PMaxSize|Xutil.PMinSize),
            min_width=80, min_height=48,
            max_width=2000, max_height=48)
        win.change_property(dsp.intern_atom("_WIN_STATE"),Xatom.CARDINAL,32,[1])
        win.change_property(dsp.intern_atom("_MOTIF_WM_HINTS"),
            dsp.intern_atom("_MOTIF_WM_HINTS"), 32, [0x2, 0x0, 0x0, 0x0, 0x0])
        win.change_property(self._DESKTOP, Xatom.CARDINAL, 32, [0xffffffffL])
        win.change_property(dsp.intern_atom("_NET_WM_WINDOW_TYPE"),
            Xatom.ATOM, 32, [dsp.intern_atom("_NET_WM_WINDOW_TYPE_DOCK")])


    def tr__setStruts(self,win, hidden=0):
    #----------------------------------
        top = top_start = top_end = 0
        bottom = 48
        bottom_start = 0
        bottom_end   = 48
        self._STRUT           = self.dsp.intern_atom("_NET_WM_STRUT")
        self._STRUTP          = self.dsp.intern_atom("_NET_WM_STRUT_PARTIAL")


        win.change_property(self._STRUT, Xatom.CARDINAL, 32, [0, 0, top, bottom])
        win.change_property(self._STRUTP, Xatom.CARDINAL, 32, [0, 0, top, bottom,
            0, 0, 0, 0, top_start, top_end, bottom_start, bottom_end])

gobject.type_register(mywidget)

#if __name__ == "__main__":
#    def destwindow(widget,data=None):
#        gtk.main_quit()
#    dsp = display.Display()
#    scr = dsp.screen()
#
#    
#    def dohello(widget, info):
#        widget.set_label("boo")
#
#    window=gtk.Window(gtk.WINDOW_TOPLEVEL)
#    window.connect("destroy", destwindow)
#
#    box1 = gtk.VBox(False,0)
#    window.add(box1)
#    button = gtk.Button("Button")
#    button.connect("clicked", dohello,"Piano")
#    mywid = mywidget(display,error,box1)
#    gobject.timeout_add(100,mywid.tr__testTiming)
#    box1.pack_start(mywid,True,True,0)
#    box1.pack_end(button, True,True,0)
#
#
#    window.show_all()
#    gtk.main()

#    applet = AWNLib.initiate() # Create a new applet
#    applet.title.set("Test python applet") # This is the hover name
#    dlog = applet.dialog.new("main")
#    widg = mywidget(display, error, dlog)
#    time = applet.timing.time(lambda: widg.tr__testTiming(),1)
#    dlog.add(widg)
#    applet.icon.theme("gtk-apply")
#    applet.add(widg)

#    AWNLib.start(applet)

class App(awn.Applet):
    def __init__(self,uid,orient,height):
        awn.Applet.__init__(self,uid,orient,height)
        self.height=height
        self.box1= gtk.VBox()
        self.add(self.box1)
        self.box1.show()
#        self.box1.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("blue"))
        self.widg = mywidget(display, error, self.box1,self)
        gobject.timeout_add(1000,loadconf,self.widg)
        self.box1.add(self.widg)
        self.widg.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse("#"+BG_COLOR[2:8]))
#        self.widg.bg_pixmap[gtk.STATE_NORMAL] = pic
        # We have to wait for the window to be realized...
        gobject.timeout_add(1000,self.chbg,self.widg)

    def chbg(self,widg):
        image=gdk.pixbuf_new_from_file(IMPATH)
        (pic,mask)=image.render_pixmap_and_mask()
        if(USEIM):
            widg.gwin.set_back_pixmap(pic,False)
            widg.gwin.clear()
            widg.gwin.clear_area_e(0,0,1,1)
        return True


def cleanup(k):
    d = display.Display()
    scree=d.screen()
#    k.widg.selowin.destroy()

    for tid in k.widg.tray.order:
        t = k.widg.tray.tasks[tid]
        print t.obj.query_tree()
        
#        t.obj.reparent(scree.root,0,0)

    manager = d.intern_atom("MANAGER")
#    k.widg.selowin.set_selection_owner(d.intern_atom("NONE"), X.CurrentTime,onerror=error)
#    k.widg.tr__sendEvent(scree.root, manager,[X.CurrentTime, d.intern_atom("NONE"),k.widg.selowin.id], (X.StructureNotifyMask))

    d.sync()
    k.widg.wind.destroy(onerror=error)


global path
path= sys.argv[0] 
path = path[0:-8]
awn.init(sys.argv[1:])
awn_options=awn.Config('pysystemtray',None)
def loadconf(thingie):
    global BG_COLOR, CUSTOM_Y, HIGH, BORDER, DIVIDEBYZERO,ZEROPID,IMPATH,USEIM
    oldBG=BG_COLOR
    BG_COLOR     = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"BG_COLOR")
    CUSTOM_Y     = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"CUSTOM_Y")
    HIGH         = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"HIGH"    )
    BORDER       = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"BORDER"  )
    DIVIDEBYZERO = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"TRANS"   ) 
    ZEROPID      = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"ZEROPID" )
    IMPATH       = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"IMPATH"  )
    USEIM        = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"USEIM"   )
    if(oldBG != BG_COLOR):
        if(thingie != None):
            thingie.needredraw=True
    return True
loadconf(None)
if(HIGH==0):
    HIGH     = D_HIGH
    BORDER   = D_BORDER
    CUSTOM_Y = D_CUSTOM_Y
    BG_COLOR = D_BG_COLOR
    DIVIDEBYZERO = D_DIVIDEBYZERO
    ZEROPID  = D_ZEROPID
    IMPATH   = D_IMPATH
    USEIM    = D_USEIM
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,"BG_COLOR",BG_COLOR)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"BORDER",BORDER)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"CUSTOM_Y",CUSTOM_Y)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"HIGH",HIGH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"TRANS",DIVIDEBYZERO)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"ZEROPID",ZEROPID)
    awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,"IMPATH",IMPATH)
    awn_options.set_int(awn.CONFIG_DEFAULT_GROUP,"USEIM",USEIM)


a = App(awn.uid, awn.orient, awn.height)
awn.init_applet(a)
a.show_all()
atexit.register(cleanup,a)
#gobject.timeout_add(1000,loadconf)
gtk.main()

