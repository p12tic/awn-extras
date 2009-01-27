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

import sys

import gtk
from gtk import gdk
import gobject      #Gtk/Gdk/GObj for interfacing with the applet
import awn
from awn import extras
import cairo        # Awn and cairo drawing
awn.check_dependencies(globals(), "Xlib")
from Xlib import X, display, error, Xatom, Xutil
import Xlib.protocol.event
                    # Xlib and bits that are needed.
                    # These are used to create the custom GTK widget
                    # and to interface with system tray icons

import subprocess
                    # used to launch the config

import atexit
                    # Used in an attempt at clean closing


#Default Values
# Used if no config is found.
global D_BG_COLOR, D_CUSTOM_Y, D_HIGH, D_ALLOW_COL
global D_REFRESH, D_DIVIDEBYZERO, D_BORDER, D_ZEROPID
global D_IMPATH, D_USEIM, D_ICONSIZE
D_BG_COLOR="0x0070E0"
D_CUSTOM_Y=10
D_HIGH=2
D_ALLOW_COL=50
D_REFRESH=10
D_DIVIDEBYZERO=False
D_BORDER=True
D_ZEROPID=True
D_IMPATH="/".join(__file__.split("/")[:-1])+"/pattern.png"
D_USEIM = False
D_ICONSIZE=24

# And thier current value!
global BG_COLOR, CUSTOM_Y, HIGH, ALLOW_COL, REFRESH, DIVIDEBYZERO
global BORDER, ZEROPID, IMPATH, USEIM, ICONSIZE, USEGTK

REFRESH=10    # Not in config yet. Wont be needed until Transparency works
                # if <90 milliseconds then its ignored.
                # otherwise, its the milliseconds between alpha-redraws

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

    def __init__(self, display, error, gtkwin):
        gtk.Widget.__init__(self)

        # Define widget value and set to default
        self.curr_x=1 #Starting width and height
        self.curr_y=1

        self.dsp = display.Display()      # references to Xlib
        self.scr = self.dsp.screen()
        self.root = self.scr.root
        self.error = error.CatchError()

        self.gtkwin=gtkwin               # Applet's reference

        self.realized= 0                 # Is the Xwindow realized yet?
                                         # if not, can cause problems with
                                         # certain functions
        self.needredraw=False
                                         # Set to True when BG colour is
                                         # changed in config
        ourmask = (X.ButtonPressMask|X.ButtonReleaseMask|X.ExposureMask)

        self.wind = self.root.create_window(0, 0, 1, 10,
                0, self.scr.root_depth, window_class=X.InputOutput,
                visual=X.CopyFromParent, colormap=X.CopyFromParent,
                event_mask=ourmask)

        # System Tray window


        self.tray = Obj(id="tray", tasks={}, order=[],
                    first=0, last=0, window=self.wind)
        # Create an empty Object, this will contain all the data on icons
        # to be added, and all currently managed


        # Create a non-visible window to be the selection owner
        self._OPCODE = self.dsp.intern_atom("_NET_SYSTEM_TRAY_OPCODE")
        self.manager = self.dsp.intern_atom("MANAGER")
        self.selection = self.dsp.intern_atom(
            "_NET_SYSTEM_TRAY_S%d" % self.dsp.get_default_screen())
        self.selowin = self.scr.root.create_window(-1,
                                  -1, 1, 1, 0, self.scr.root_depth)
        owner = self.dsp.get_selection_owner(self.selection)
        if(owner==X.NONE):
            print "K."
        else:
            # If someone already has the system tray... BAIL!
            extras.notify_message("PyNot Error",
                "Another System Tray is already running",
                "%s%s"%(path, "PyNot.png"), 10000, 0)

            sys.exit()

        self.selowin.set_selection_owner(self.selection, X.CurrentTime)
        self.tr__sendEvent(self.root, self.manager,
              [X.CurrentTime, self.selection, self.selowin.id],
              (X.StructureNotifyMask))

        self.tr__setProps(self.dsp, self.wind)
        # Set a list of Properties that we'll need

        self.wind.map()
        self.dsp.flush()
        # Show the window and flush the display

        appchoice=gtk.MenuItem("PyNot Setup")
        self.dockmenu=self.gtkwin.create_default_menu()
        appchoice.connect("activate", self.OpenConf)
        self.dockmenu.append(appchoice)
        appchoice.show()

        # Create a Menu from Awn's default, and add our config script to it

    def do_realize(self):
        self.set_flags(gtk.REALIZED)

        self.window=gdk.window_foreign_new(self.wind.id)
        self.window.reparent(self.gtkwin.window, 0, 0)
        # Take the system manager window (not selection owner!)
        # And make it the gdk.window of the custom widget.

        self.window.set_user_data(self)
        self.style.attach(self.window)
        # Set it up as a custom widget and tell it what style (theme) to use

        self.style.set_background(self.window, gtk.STATE_NORMAL)
        self.window.move_resize(*self.allocation)
        # Tell it to use the background colour as background colour...
        # Im sure theres a reason i need to tell it that ;)

        self.tr__updatePanel(self.root, self.wind)
        # First render. Grab all the icons we know about, tell them where to
        # draw, and call a resize if necessary (likely, the first time around)

        gobject.timeout_add(100, self.tr__testTiming)
        # Check for new X signals every 100 miliseconds (1/10th second)

        if(REFRESH>80):
            gobject.timeout_add(REFRESH, self.tr__updateAlpha, True)
        else:
            gobject.timeout_add(100, self.tr__updateAlpha, False)
        # Either do a single render of Alpha, or cause one every REFRESH
        # milliseconds
        self.chbg()
        if USEGTK == 0:
            self.modify_bg(gtk.STATE_NORMAL,
                           gtk.gdk.color_parse("#"+BG_COLOR[2:8]))
                              # Change the theme for this window
        gobject.timeout_add(1000, self.chbg)
                              # check for BG change every second,
                              # again, may be a good idea to do this less often


        self.realized= 1
        # and now we can safely render alpha :D

    def do_unrealize(self):
        # The do_unrealized method is responsible for freeing the GDK resources



        # Lol.
        return 1

    def do_size_request(self, requisition):
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

    def tr__taskDelete(self, tid):
    #--------------------------------
        """ Delete the given task ID if it's in the tray/task list """
        if tid in self.tray.tasks:
            del self.tray.tasks[tid]
            self.tray.order.remove(tid)
            return 1
        return 0

    def tr__updatePanel(self, root, win):
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
        self.set_size_request(space, CUSTOM_Y+HIGH*ICONSIZE)
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
            t.obj.configure(onerror=self.error, x=t.x, y=t.y,
                            width=ICONSIZE, height=ICONSIZE)
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
        self.tr__updateAlpha(False)
        # And then update the alpha again, just to make sure

    def tr__updateAlpha(self, returnvar):
        rr= self.window.get_geometry()
        offsety=rr[3]-((HIGH*ICONSIZE)+CUSTOM_Y)
        # Again : find location of icons on the widget

        if(self.realized == 1 and offsety>-1):
            w= self.curr_x
            h= offsety+ (HIGH*ICONSIZE)
            if(BORDER==True):
                w+=10
                h+=10

            # get the width and height again

            # Create a 1Bit-map, each pixel is either True of False
            # if i use a function to draw on certain pixels, those
            # that are set to True will be shown, all False will be
            # 100% transparent.
            if(DIVIDEBYZERO == False):
                bitmap = gtk.gdk.Pixmap(None, w, h, 1)
                cr = bitmap.cairo_create()

                # Clear the bitmap to False
                cr.set_source_rgb(0, 0, 0)
                cr.set_operator(cairo.OPERATOR_DEST_OUT)
                cr.paint()

                # Draw our shape into the bitmap using cairo
                cr.set_operator(cairo.OPERATOR_OVER)

                # Lets not do the impossible. Just draw a box around it.
                if(BORDER == True):
                    newh= (HIGH*ICONSIZE)
                    cr.set_line_width(1)

                    # For the rounded edges, I just hacked together some
                    # hardwired numbers that looked acceptable.
                    cr.rectangle(0, offsety+1, w, newh-2)
                    cr.fill()
                    cr.rectangle(6, offsety-5, w-16, newh+10)
                    cr.fill()
                    cr.rectangle(1, offsety-1, w-6, newh+2)
                    cr.fill()
                    cr.rectangle(2, offsety-2, w-8, newh+4)
                    cr.fill()
                    cr.rectangle(3, offsety-3, w-10, newh+6)
                    cr.fill()
                    cr.rectangle(4, offsety-4, w-12, newh+8)
                    cr.fill()
                else:
                    cr.rectangle(0, offsety, w, h)
                    cr.fill()

                self.window.shape_combine_mask(bitmap, 0, 0)
            else:
                newh= (HIGH*ICONSIZE)
                bitmap = gtk.gdk.Pixmap(None, w, h, 1)
                cr = bitmap.cairo_create()

                # Clear the bitmap to False
                cr.set_source_rgb(0, 0, 0)
                cr.set_operator(cairo.OPERATOR_DEST_OUT)
                cr.paint()

                # Draw our shape into the bitmap using cairo
                cr.set_operator(cairo.OPERATOR_OVER)
                cr.rectangle(0, offsety, w, newh)
                cr.fill()
                self.window.shape_combine_mask(bitmap, 0, 0)

                self.window.merge_child_shapes()

        return returnvar

    def tr__sendEvent(self, win, ctype, data, mask=None):
    #------------------------------------------------
        """ Send a ClientMessage event to the root """
        data = (data+[0]*(5-len(data)))[:5]
        ev = Xlib.protocol.event.ClientMessage(window=win,
                       client_type=ctype, data=(32, (data)))

        if not mask:
            mask = (X.SubstructureRedirectMask|X.SubstructureNotifyMask)
        self.root.send_event(ev, event_mask=mask)

    def tr__testTiming(self):
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
                task.obj.configure(onerror=self.error,
                     width=ICONSIZE, height=ICONSIZE)
                self.tr__updatePanel(self.root, self.wind)
            if e.type == X.Expose and e.count==0:
                if(e.window.id==self.wind.id):
                    self.wind.clear_area(0, 0, 0, 0)
#                self.tr__updateAlpha(False)
                    self.tr__updatePanel(self.root, self.wind)
            if e.type == X.ClientMessage:
                data = e.data[1][1]
                task = e.data[1][2]
                if e.client_type == self._OPCODE and data == 0:
                    obj = self.dsp.create_resource_object("window", task)
                    pid=0
                    try:
                        pidob= obj.get_property(self._PIDTHING,
                            X.AnyPropertyType, 0, 1024)
                        pid = pidob.value[0]
                    except:
                        pass
                    # we either get its Process ID, or an X-error
                    # Yay :D

                    if(ZEROPID==False or (ZEROPID==True and pid>0)):

                        obj.reparent(self.tray.window.id, 0, 0)
                        ourmask = (X.ExposureMask|X.StructureNotifyMask)
                        obj.change_attributes(event_mask=ourmask)
                        self.tray.tasks[task] = Obj(obj=obj, x=0, y=0,
                            width=0, height=ICONSIZE, pid=pid)
                        self.tray.order.append(task)
                        self.tr__updatePanel(self.root, self.wind)
        if(self.needredraw == True):
            self.tr__updatePanel(self.root, self.wind)
        return True

    def OpenConf(self, thing):
        program = "%s%s"%(path, "pynotconf.py")
        self.config=subprocess.Popen("python "+program, shell=True)
        return 1

    def tr__setProps(self, dsp, win):
    #----------------------------
        """ Set necessary X atoms and panel window properties """
        self._ABOVE = dsp.intern_atom("_NET_WM_STATE_ABOVE")
        self._BELOW = dsp.intern_atom("_NET_WM_STATE_BELOW")
        self._BLACKBOX = dsp.intern_atom("_BLACKBOX_ATTRIBUTES")
        self._CHANGE_STATE = dsp.intern_atom("WM_CHANGE_STATE")
        self._CLIENT_LIST = dsp.intern_atom("_NET_CLIENT_LIST")
        self._CURRENT_DESKTOP = dsp.intern_atom("_NET_CURRENT_DESKTOP")
        self._DESKTOP = dsp.intern_atom("_NET_WM_DESKTOP")
        self._DESKTOP_COUNT = dsp.intern_atom("_NET_NUMBER_OF_DESKTOPS")
        self._DESKTOP_NAMES = dsp.intern_atom("_NET_DESKTOP_NAMES")
        self._HIDDEN = dsp.intern_atom("_NET_WM_STATE_HIDDEN")
        self._ICON = dsp.intern_atom("_NET_WM_ICON")
        self._NAME = dsp.intern_atom("_NET_WM_NAME")
        self._RPM = dsp.intern_atom("_XROOTPMAP_ID")
        self._SHADED = dsp.intern_atom("_NET_WM_STATE_SHADED")
        self._SHOWING_DESKTOP = dsp.intern_atom("_NET_SHOWING_DESKTOP")
        self._SKIP_PAGER = dsp.intern_atom("_NET_WM_STATE_SKIP_PAGER")
        self._SKIP_TASKBAR = dsp.intern_atom("_NET_WM_STATE_SKIP_TASKBAR")
        self._STATE = dsp.intern_atom("_NET_WM_STATE")
        self._STICKY = dsp.intern_atom("_NET_WM_STATE_STICKY")
        self._STRUT = dsp.intern_atom("_NET_WM_STRUT")
        self._STRUTP = dsp.intern_atom("_NET_WM_STRUT_PARTIAL")
        self._WMSTATE = dsp.intern_atom("WM_STATE")
        self._PIDTHING = dsp.intern_atom("_NET_WM_PID")

        win.set_wm_name("PyNot")
        win.set_wm_class("PyNot", "PyNot")
        win.set_wm_hints(flags=(Xutil.InputHint|Xutil.StateHint),
            input=0, initial_state=1)
        win.set_wm_normal_hints(flags=(
            Xutil.PPosition|Xutil.PMaxSize|Xutil.PMinSize),
            min_width=80, min_height=48,
            max_width=2000, max_height=48)
        win.change_property(dsp.intern_atom("_WIN_STATE"),
            Xatom.CARDINAL, 32, [1])
        win.change_property(dsp.intern_atom("_MOTIF_WM_HINTS"),
            dsp.intern_atom("_MOTIF_WM_HINTS"), 32, [0x2, 0x0, 0x0, 0x0, 0x0])
        win.change_property(self._DESKTOP, Xatom.CARDINAL, 32, [0xffffffffL])
        win.change_property(dsp.intern_atom("_NET_WM_WINDOW_TYPE"),
            Xatom.ATOM, 32, [dsp.intern_atom("_NET_WM_WINDOW_TYPE_UTILITY")])

    def cleanup(self):
        # This is my attempt to cleanly close, in such a way that the icons do
        # not get an X window error

        for tid in self.tray.order:
            t = self.tray.tasks[tid]
            g= t.obj.query_tree()
            t.obj.unmap()
            t.obj.unmap_sub_windows()
            t.obj.reparent(g.root.id, 0, 0)
        self.dsp.flush()
        return None

    def chbg(self):
         if(USEGTK == 0):
            if IMPATH in [None, '']:
                image=gdk.pixbuf_new_from_file(D_IMPATH)
            else:
                image=gdk.pixbuf_new_from_file(IMPATH)
                (pic, mask)=image.render_pixmap_and_mask()
                if(USEIM==True):
                    # If the user wants an image ...
                    self.window.set_back_pixmap(pic, False) #Change image
                    self.window.clear()
                    self.window.clear_area_e(0, 0, self.curr_x*2, self.curr_y)
                    #and cause an expose.
         return True

gobject.type_register(mywidget)
# Register it as a widget


class App(awn.Applet):

    def __init__(self, uid, orient, height):

        awn.Applet.__init__(self, uid, orient, height)
        self.height = height
        self.widg = None
        self.loadconf(1,2)
        if(HIGH == 0):
            self.makeconf()
        self.widg = mywidget(display, error, self)
                              # create a new custom widget.
                              # This is the system tray
        #gobject.timeout_add(1000, self.loadconf)
        #                      # This causes a time out of 1 second,
        #                      # each second, checking if the config has changed
        #                      # May be a good idea to turn this down
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "BG_COLOR", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "CUSTOM_Y", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "HIGH", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "BORDER", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "TRANS", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "IMPATH", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "USEIM", self.loadconf)
        awn_options.notify_add(awn.CONFIG_DEFAULT_GROUP,
                                "ICONSIZE", self.loadconf)

        self.add(self.widg)

    def loadconf(self,dud1,dud2):
        # Load the config
        global BG_COLOR, CUSTOM_Y, HIGH, BORDER
        global DIVIDEBYZERO, ZEROPID, IMPATH, USEIM, ICONSIZE,USEGTK
        oldBG=BG_COLOR
        BG_COLOR = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP, "BG_COLOR")
        CUSTOM_Y = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y")
        HIGH = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "HIGH")
        BORDER = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "BORDER")
        DIVIDEBYZERO = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "TRANS")
        ZEROPID = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "ZEROPID")
        IMPATH = awn_options.get_string(awn.CONFIG_DEFAULT_GROUP, "IMPATH")
        USEIM = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "USEIM")
        ICONSIZE = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE")
        USEGTK = awn_options.get_int(awn.CONFIG_DEFAULT_GROUP, "USEGTK")
        print USEGTK
        # If BG has changed, reset it
        if(self.widg != None):
            self.widg.needredraw=True
        return True

    def makeconf(self):
        awn_options.set_string(awn.CONFIG_DEFAULT_GROUP,
            "BG_COLOR", D_BG_COLOR)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "BORDER", D_BORDER)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "CUSTOM_Y", D_CUSTOM_Y)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "HIGH", D_HIGH)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "TRANS", D_DIVIDEBYZERO)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "ZEROPID", D_ZEROPID)
        awn_options.set_string(awn.CONFIG_DEFAULT_GROUP, "IMPATH", D_IMPATH)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "USEIM", D_USEIM)
        awn_options.set_int(awn.CONFIG_DEFAULT_GROUP, "ICONSIZE", D_ICONSIZE)
        self.loadconf()

global path
path = sys.argv[0]
path = path[0:-8]
# path takes the directory that pynot is in

awn.init(sys.argv[1:])
awn_options = awn.Config('pynot', None)

a = App(awn.uid, awn.orient, awn.height)
awn.init_applet(a)
a.show_all()
atexit.register(a.widg.cleanup)
try:
    gtk.main()
except:
    a.widg.cleanup()
