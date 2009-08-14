#!/usr/bin/python
"""
PyNot v0.20 - Awn Notificaion/system tray.
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

# Especially qball whos deconstructive criticsm has kept me up many nights

# I will start by saying this, This is a rather confusing applet
# The logic behind it is the fact that an X window and GDK window are
# the same. GDK windows are used to draw everything in GTK.
# Also, AWN can embed GTK widgets as applets

# Going up from there, I use GTK to find the RGBA visual/colormap
# Because I always got X errors when trying to do it with Xlib

# Also, attempting to embed an RGB icon into an RGBA window will spew
# X errors, and the workaround to that would be to make it look ugly again...
# So pynot just turns down RGB icons when they attempt to embed


import sys
import os

import gtk 
from gtk import gdk
import gobject      #Gtk/Gdk/GObj for interfacing with the applet
 
import awn
import cairo        # Awn and cairo drawing

awn.check_dependencies(globals(),"Xlib", "pynotify")
from Xlib import X, display, error, Xatom, Xutil
import Xlib.protocol.event
                    # Xlib and bits that are needed.
                    # These are used to create the custom GTK widget
                    # and to interface with system tray icons

import subprocess
                    # used to launch the config

import atexit
                    # Used in an attempt at clean closing

import math
                    # Used only for pi -.-


# And thier current value!
global BG_COLOR,CUSTOM_Y, HIGH,ALLOW_COL,ALPHA,BORDER,ZEROPID,IMPATH,USEIM,ICONSIZE,ALPHA2,FG_COLOR,EDGING,LINEWIDTH

ICONSIZE=24   # Icon size, 24 is optimal, Application has to support the
              # icon size as well as tray.

BG_COLOR=""   # Set it or it'll complain when trying to compare in the first
              # config read :)


global awn_options

class Obj(object):
#----------------------------------------------------------------------------
    """ Multi-purpose class """
    #----------------------------
    def __init__(self, **kwargs):
    #----------------------------
        self.__dict__.update(kwargs)

class mywidget(gtk.Widget):
    def __init__(self, display,error,gtkwin):
        gtk.Widget.__init__(self)
        
        # Define widget value and set to default
        self.curr_x=1 #Starting width and height
        self.curr_y=1
 
        self.dsp = display.Display()      # references to Xlib
        self.scr = self.dsp.screen()
        self.root    = self.scr.root
        self.error   = error.CatchError()



        
        self.gtkwin=gtkwin               # Applet's reference

        self.realized= 0                 # Is the Xwindow realized yet?
                                         # if not, can cause problems with
                                         # certain functions
        self.needredraw=False
                                         # Set to True when BG colour is 
                                         # changed in config
        self.warnrgba=False
                                         # To make pynot only warn once

        #for m in self.scr.allowed_depths:
        #    if m.depth == 32 :
        #        self.rgbavisid= m.visuals[0].visual_id
        ## A tad hackish, Maybe do some checks that its actually rgba?
    
        # I have chosen to keep the above code commented for
        # future reference, it works fine to find an RGBA X visual ID

        self.visatom = self.dsp.intern_atom("_NET_SYSTEM_TRAY_VISUAL")

        self.dudwindow = gtk.Window()
        self.dudwindow.set_title("PyNoT")
        self.dudwindow.set_decorated(False)
        self.dudwindow.add_events(gdk.BUTTON_RELEASE_MASK)
        self.dudwindow.add_events(gdk.EXPOSURE_MASK)
        self.dudwindow.add_events(gdk.BUTTON_PRESS_MASK)
        self.dudwindow.set_app_paintable(True)
        self.dudwindow.connect("expose-event", self.expose_event)
        self.dudwindow.connect("button-press-event", self.button_event)

        screen = self.get_screen()
        colormap = screen.get_rgba_colormap()
        self.dudwindow.set_colormap(colormap)
        # Sets a RGBA visual/colormap

        self.dudwindow.set_property("skip-taskbar-hint", True)
        self.dudwindow.show()
        self.wind_id= self.dudwindow.window.xid
        self.wind=self.dsp.create_resource_object("window",self.wind_id)
        self.dudwindow.connect('screen-changed', self.chbg)

        self.rgbavisid = self.wind.get_attributes().visual
        # This grabs the X visual from the GTK window         

                                      
        # System Tray window

        
        self.tray = Obj(id="tray", tasks={}, order=[], first=0, last=0, window=self.wind)
        # Create an empty Object, this will contain all the data on icons
        # to be added, and all currently managed
    

        # Create a non-visible window to be the selection owner
        self._OPCODE = self.dsp.intern_atom("_NET_SYSTEM_TRAY_OPCODE")
        self.manager = self.dsp.intern_atom("MANAGER")
        self.selection = self.dsp.intern_atom("_NET_SYSTEM_TRAY_S%d" % self.dsp.get_default_screen())
        self.selowin = self.scr.root.create_window(-1, -1, 1, 1, 0, self.scr.root_depth)
        owner = self.dsp.get_selection_owner(self.selection)
        if(owner!=X.NONE):
            # If someone already has the system tray... BAIL!

            pynotify.init('PyNot')
            notification = pynotify.Notification("PyNot Error",
                                                 "Another System Tray is already running",
                                                 "%s%s" % (path, "pynot.svg"))
            notification.set_timeout(10000)
            notification.show()
            pynotify.uninit()

            gtkwin.trayExists(self)
            self.dudwindow.hide()
            self.dudwindow.destroy()
            self.wind.destroy()
            return None
        else:
            self.selowin.set_selection_owner(self.selection, X.CurrentTime)
            self.tr__sendEvent(self.root, self.manager,
       [X.CurrentTime, self.selection,self.selowin.id], (X.StructureNotifyMask))

            self.selowin.change_property(self.visatom,Xatom.VISUALID,
                                             32,[self.rgbavisid])
            self.wind.change_property(self.visatom,Xatom.VISUALID,
                                             32,[self.rgbavisid])

 
            self.dsp.flush()
            # Show the window and flush the display

            appchoice = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
            aboutchoice = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
            sep = gtk.SeparatorMenuItem()
            self.dockmenu = self.gtkwin.create_default_menu()
            appchoice.connect("activate", self.OpenConf)
            aboutchoice.connect("activate", self.About)
            self.dockmenu.append(appchoice)
            self.dockmenu.append(sep)
            self.dockmenu.append(aboutchoice)
            aboutchoice.show()
            sep.show()
            appchoice.show()
            gtkwin.trayWorks(self)


            # Create a Menu from Awn's default, and add our config script to it

    def expose_event(self,widget,event):
       self.chbg()

    def button_event(self,widget,event):
       if(event.button == 3):
           # Again, Right click.
           # Thanks to moving the main window to GTK, this had to be moved
           # to here.
           self.dockmenu.show_all()
           self.dockmenu.popup(None, None, None, 3, event.time)

           

    def do_realize(self):
        self.set_flags(gtk.REALIZED)

        self.window = self.dudwindow.window
        self.window.reparent(self.gtkwin.window,0,0)
        # Reparent self into the applet

        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        # Tell it to use the background colour as background colour...
        # Im sure theres a reason i need to tell it that ;)

        self.tr__updatePanel(self.root,self.wind)
        # First render. Grab all the icons we know about, tell them where to
        # draw, and call a resize if necessary (likely, the first time around)

        #gobject.timeout_add(100,self.tr__testTiming)
        gobject.io_add_watch(self.dsp.fileno(), gobject.IO_IN | gobject.IO_PRI,
                             self.tr__testTiming)
        # Check for new X signals every 100 miliseconds (1/10th second) 

        gobject.timeout_add(100,self.chbg)
        self.chbg()

        self.realized= 1
    
    def do_unrealize(self):
        # The do_unrealized method is responsible for freeing the GDK resources



        # Lol.
        return 1;

    def do_size_request(self,requisition):
        # Widget is bieng asked what size it would like to be.
        requisition.width=self.curr_x
        requisition.height=self.curr_y

    def do_size_allocate(self, allocation):
        # The do_size_allocate is called by when the actual size is known
        # and the widget is told how much space could actually be allocated

        self.allocation = allocation

        # If we're realized, move and resize the window to the
        # requested coordinates/positions
        if self.flags() & gtk.REALIZED:
            self.window.move_resize(*allocation)
 
    def tr__taskDelete(self,tid):
    #--------------------------------
        """ Delete the given task ID if it's in the tray/task list """
        if tid in self.tray.tasks:
            del self.tray.tasks[tid]
            self.tray.order.remove(tid)
            return 1
        return 0

    def tr__updatePanel(self,root,win):
        # Requested re-draw/re-position
        rr= self.window.get_geometry()
        # find the gdk windows geometry (for the size of y)

        offsety=rr[3]-((HIGH*ICONSIZE)+CUSTOM_Y)
        if(offsety<0):
            offsety=0
        # find the Y position to start drawing icons at


        # First - a pre-render loop to find how much space we need.
        space=2 # Border of 1 pixel either side
        if(BORDER==True):
            space+=5 # For rounder corners, more border space is needed
        tempy=0
        for t in self.tray.tasks.values():
            iwant=0
            ifail=0
            try:
                iwant=t.obj.get_wm_normal_hints().min_width
            except:
                ifail=1
                pass
            if ifail==0:
                t.width = ICONSIZE
                #space += t.width
                if(tempy==0):
                    space+=t.width
                if(tempy < HIGH-1):
                    tempy+=1
                else:
                    tempy=0

        if(BORDER==True):
            space+=5
        self.set_size_request(space,250)
        self.gtkwin.set_size_request(space,250)
        # Request resize to the new size we need :)

        #Second pass, telling each icon where it is to go now.
        self.curr_x=0
        if(BORDER==True):
            self.curr_x+=5
        self.curr_y=0
        for tid in self.tray.order:
            t = self.tray.tasks[tid]
            t.x = self.curr_x
            t.y = offsety+self.curr_y*ICONSIZE
            t.obj.configure(onerror=self.error, x=t.x, y=t.y, width=ICONSIZE, height=ICONSIZE)
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
        self.chbg()
        # And then update the alpha again, just to make sure

    def tr__updateAlpha(self,returnvar):
        rr= self.window.get_geometry()
        offsety=rr[3]-((HIGH*ICONSIZE)+CUSTOM_Y)
 
        self.chbg()

        return returnvar


    def tr__sendEvent(self,win, ctype, data, mask=None):
    #------------------------------------------------
        """ Send a ClientMessage event to the root """
        data = (data+[0]*(5-len(data)))[:5]
        ev = Xlib.protocol.event.ClientMessage(window=win, client_type=ctype, data=(32,(data)))

        if not mask:
            mask = (X.SubstructureRedirectMask|X.SubstructureNotifyMask)
        self.root.send_event(ev, event_mask=mask)

    def tr__testTiming(self,var,var2):
        # Event "loop"
        # called every 1/10th second, does all events and quits
        # quickest hack towards multi-threading i had ;)
        while self.dsp.pending_events()>0:
            e = self.dsp.next_event()
            #print e
            if e.type == X.ButtonRelease:
                if(e.detail == 3):
                    # Button 3 is right click.
                    # I probably shouldnt have hard coded "3" into it...
                    # chances are I will regret this later :D
                    self.dockmenu.show_all()
                    self.dockmenu.popup(None, None, None, 3, e.time)
            if e.type == X.DestroyNotify:
                if self.tr__taskDelete(e.window.id):
                    self.tr__updatePanel(self.root, self.wind)
            if e.type == X.ConfigureNotify:
                task = self.tray.tasks[e.window.id]
                task.obj.configure(onerror=self.error,width=ICONSIZE, height=ICONSIZE)
                self.tr__updatePanel(self.root, self.wind)
            if e.type == X.Expose and e.count==0:
                if(e.window.id==self.wind.id):
                    self.chbg()
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
                    # we either get its Process ID, or an X-error
                    # Yay :D
                
                    # Next check : RGBA colormap
                    # If its not the visual we asked it to use...
                    # Tough luck. For now I cant be bothered helping it :)

                    itsok = 1
                    if(obj.get_attributes().visual != self.rgbavisid):
                        print "RGB icon, Error"
                        itsok=0
                        if(self.warnrgba == False):
                            self.warnrgba = True
                            pynotify.init('PyNot')
                            notification = pynotify.Notification("PyNot Error",
                                                                 "An RGB icon has attempted to dock, Pynot only allows RGBA",
                                                                 "%s%s" % (path, "pynot.svg"))
                            notification.set_timeout(10000)
                            notification.show()
                            pynotify.uninit()

                            
                    
                    if(itsok ==1 and (ZEROPID==False or (ZEROPID==True and pid>0))):

                        obj.reparent(self.tray.window.id,0,0)
                        obj.change_attributes(event_mask=(X.ExposureMask|X.StructureNotifyMask))
                        self.tray.tasks[task] = Obj(obj=obj, x=0, y=0, width=0, height=ICONSIZE,pid=pid)
                        self.tray.order.append(task)
                        self.tr__updatePanel(self.root,self.wind)
        if(self.needredraw == True):
            self.tr__updatePanel(self.root,self.wind)
            self.needredraw = False
        return True

    def OpenConf(self,thing):
        program = "%s%s"%(path,"pynotconf.py")
        self.config=subprocess.Popen("python "+program,shell=True)
        return 1

    def cleanup(self):
        # This is my attempt to cleanly close, in such a way that the icons do
        # not get an X window error

        for tid in self.tray.order:
            t = self.tray.tasks[tid]
            g= t.obj.query_tree()
            t.obj.unmap()
            t.obj.unmap_sub_windows()
            t.obj.reparent(g.root.id,0,0)
            # After trawling through a fair bit of Xembed/Systray Specs
            # I realised the trick was to reparent it to ITS root
            # not the generic one, not sure what difference it makes
            # but in practice it only works this way

        self.dsp.flush()
        return None

    def chbg(self):
        rr= self.window.get_geometry()
        offsety=rr[3]-((HIGH*ICONSIZE)+CUSTOM_Y)

        # offsety is the top of the first row of icons
        # the height can be gained by calculating HIGH * ICONSIZE
        # and the width from the same get_geometry function

        if(BORDER==True):
            y=offsety
            h=(HIGH*ICONSIZE)
            x=0
            w=rr[2]
            linewidth = LINEWIDTH
            edging = EDGING
            cr = self.window.cairo_create()
            cr.set_source_rgba(0.0,0.0,0.0,0.0)
            cr.set_line_width(linewidth)

            col= gtk.gdk.color_parse("#"+BG_COLOR[2:8])
            col2= gtk.gdk.color_parse("#"+FG_COLOR[2:8])

            cr.set_operator(cairo.OPERATOR_SOURCE)
            cr.paint()
            # Ok. First problem, if this wont fit in, dont draw a BG.
            if(rr[2]<(edging*2)):
                return 1
            if(rr[3]<(edging*2)):
                return 1
            cr.set_source_rgba(float(col.red)/float(65535),
                               float(col.green)/float(65535),
                               float(col.blue)/float(65535),
                               float(ALPHA)/float(65535))
            cr.arc(x+edging, y+edging,edging,1.0*math.pi, 1.5*math.pi)
            cr.line_to(x+edging,y+edging)
            cr.fill()
            cr.arc(x+w-edging, y+edging,edging,1.5*math.pi, 2*math.pi)
            cr.line_to(x+w-edging, y+edging)
            cr.fill()
            cr.arc(x+edging, y+h-edging,edging,0.5*math.pi, 1.0*math.pi)
            cr.line_to(x+edging, y+h-edging)
            cr.fill()
            cr.arc(x+w-edging, y+h-edging,edging,0., 0.5*math.pi)
            cr.line_to(x+w-edging, y+h-edging)
            cr.fill()

            cr.set_source_rgba(float(col2.red)/float(65535),
                               float(col2.green)/float(65535),
                               float(col2.blue)/float(65535),
                               float(ALPHA2)/float(65535))
            cr.arc(x+edging, y+edging,edging,1.0*math.pi, 1.5*math.pi)
            cr.stroke()
            cr.arc(x+w-edging, y+edging,edging,1.5*math.pi, 2*math.pi)
            cr.stroke()
            cr.arc(x+edging, y+h-edging,edging,0.5*math.pi, 1*math.pi)
            cr.stroke()
            cr.arc(x+w-edging, y+h-edging,edging,0., 0.5*math.pi)
            cr.stroke()

            cr.set_source_rgba(float(col.red)/float(65535),
                               float(col.green)/float(65535),
                               float(col.blue)/float(65535),
                               float(ALPHA)/float(65535))
            cr.rectangle(x+edging,y,w-(2*edging),h)
            cr.fill()
            cr.set_source_rgba(float(col2.red)/float(65535),
                               float(col2.green)/float(65535),
                               float(col2.blue)/float(65535),
                               float(ALPHA2)/float(65535))
            cr.move_to(x+edging,y)
            cr.line_to(x+w-edging,y)
            cr.stroke()
            cr.move_to(x+edging,y+h)
            cr.line_to(x+w-edging,y+h)
            cr.stroke()

            cr.set_source_rgba(float(col.red)/float(65535),
                               float(col.green)/float(65535),
                               float(col.blue)/float(65535),
                               float(ALPHA)/float(65535))
            cr.rectangle(x,y+edging,w,h-(2*edging))
            cr.fill()
            cr.set_source_rgba(float(col2.red)/float(65535),
                               float(col2.green)/float(65535),
                               float(col2.blue)/float(65535),
                               float(ALPHA2)/float(65535))
            cr.move_to(x,y+edging)
            cr.line_to(x,y+h-edging)
            cr.stroke()
            cr.move_to(x+w,y+edging)
            cr.line_to(x+w,y+h-edging)
            cr.stroke()

        else:
            if(USEIM==True):
                cr = self.window.cairo_create()
                cr.set_source_rgba(0.0,0.0,0.0,0.0)
                cr.set_operator(cairo.OPERATOR_SOURCE)
                cr.paint()
                image=None
            
                if IMPATH in [None,'']:
                    image=cairo.ImageSurface.create_from_png (D_IMPATH);
                else:
                    image=cairo.ImageSurface.create_from_png (IMPATH);
                pattern =cairo.SurfacePattern(image)
                cr.set_source(pattern)
                cr.paint()
 
            else:        
                col= gtk.gdk.color_parse("#"+BG_COLOR[2:8])
                cr = self.window.cairo_create()
                cr.set_source_rgba(0.0,0.0,0.0,0.0)
                cr.set_operator(cairo.OPERATOR_SOURCE)
                cr.paint()
                cr.set_source_rgba(float(col.red)/float(65535),
                                   float(col.green)/float(65535),
                                   float(col.blue)/float(65535),
                               float(ALPHA)/float(65535)) # Transparent`
                cr.set_operator(cairo.OPERATOR_SOURCE)
                w= self.curr_x
                h= (HIGH*ICONSIZE)

                cr.rectangle(0,offsety,w,h)
                cr.fill()

        return True

    def About(self, var):
        this = gtk.AboutDialog()
        this.set_name("PyNot")
        this.set_copyright("Copyright 2008 triggerhapp, Nathan Howard")
        this.set_comments("A Configurable System tray applet")
        this.set_logo(gtk.gdk.pixbuf_new_from_file_at_size(path+"PyNot.png", 48, 48))
        this.connect("response",self.endAbout)
        this.show()

    def endAbout(self, var1, var2):
        var1.destroy()

gobject.type_register(mywidget)
# Register it as a widget
# If this is missed, it does not realise that this class is infact
# a widget at all

class App(awn.Applet):
    def __init__(self,uid,orient,height):
        awn.Applet.__init__(self,uid,orient,height)
        self.height=height
        self.widg=None
        self.loadconf(1, 2)
        self.reloada = gtk.Alignment(0.0,0.85,1.0,0.15)
        self.reload = gtk.Button(stock=gtk.STOCK_REFRESH)
        self.reloada.add(self.reload)
        self.reload.connect("clicked",self.retry)
        #self.set_size_request(50,30)
        self.widg = mywidget(display, error, self)
                              # create a new custom widget.
                              # This is the system tray
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "BG_COLOR", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "FG_COLOR", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "CUSTOM_Y", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "HIGH", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "BORDER", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "TRANS", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "TRANS2", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "ZEROPID", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "IMPATH", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "USEIM", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "ICONSIZE", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "EDGING", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP, 
                                "LINEWIDTH", self.loadconf)
        
    def trayExists(self,widget):
        self.add(self.reloada)
        widget.destroy()
        self.widg = None

    def trayWorks(self,widget):
        self.add(widget)

    def retry(self, var):
        self.remove(self.reloada)
        self.widg = mywidget(display, error, self)
                              # create a new custom widget.
                              # This is the system tray

    def loadconf(self, t, t2):
        # Load the config
        global BG_COLOR, CUSTOM_Y, HIGH, BORDER, ALPHA,ZEROPID,IMPATH,USEIM,ICONSIZE,ALPHA2,FG_COLOR,EDGING,LINEWIDTH
        oldBG=BG_COLOR
        BG_COLOR     = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"BG_COLOR")
        FG_COLOR     = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"FG_COLOR")
        CUSTOM_Y     = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"CUSTOM_Y")
        HIGH         = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"HIGH"    )
        BORDER       = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"BORDER"  )
        ALPHA = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"TRANS"   )
        ALPHA2= awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"TRANS2"   )

        ZEROPID      = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"ZEROPID" )
        IMPATH       = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP,"IMPATH"  )
        USEIM        = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"USEIM"   )
        ICONSIZE     = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"ICONSIZE")
        EDGING       = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"EDGING")
        LINEWIDTH    = awn_options.get_int(   awn.CONFIG_DEFAULT_GROUP,"LINEWIDTH")

        if(self.widg != None):
            self.widg.needredraw=True
        return True

global path
path= sys.argv[0] 
path = path[0:-8]
# path takes the directory that pynot is in

awn.init(sys.argv[1:])
awn_options=awn.Config('pynot-rgba',None)

a = App(awn.uid, awn.orient, awn.height)
awn.embed_applet(a)
a.show_all()
atexit.register(a.widg.cleanup)
try:
    gtk.main()
except:
    a.widg.cleanup() 


