#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
# Detach Applet from Awn file


import pygtk
pygtk.require('2.0')
import gtk
import gobject
import cairo
import os

class Detach:
  def __init__(self):
    #These are the default settings
    self._settings = { \
      #Things to remember
      'awn-drag-drop-ready':False, \
      'detached':False, \
      'displayed':False, \
      
      #Icon
      'icon-mode':'pixbuf', \
      'icon':None, \
      'icon-width':48, \
      'icon-height':48, \
      
      #Button clicks, etc. on actual applet
      'applet-left-press':None, \
      'applet-left-release':None, \
      'applet-left-click':'applet-toggle-dialog', \
      'applet-middle-press':None, \
      'applet-middle-release':None, \
      'applet-middle-click':'applet-toggle-dialog', \
      'applet-right-press':None, \
      'applet-right-release':None, \
      #Most will change this to None or 'signal' so they can display a
      #right-click context menu
      'applet-right-click':'applet-toggle-dialog', \
      
      #Button clicks, etc. on detached window
      'left-press':None, \
      'left-release':None, \
      'left-click':'show-dialog', \
      'middle-press':None, \
      'middle-release':None, \
      'middle-click':'show-dialog', \
      'right-press':None, \
      'right-release':None, \
      #Same as applet right click
      'right-click':'show-dialog', \
      
      #Other events to the detached window
      'escape-key':'hide-dialog', \
      'focus-lost':'hide-dialog', \
      'draw-background':True, \
      
      #Buttons to use for dragging the window around the screen
      'drag-around-screen':[1,2,3]}
    
    #These are the allowed values, which
    #will eventually be used for documentation
    #TODO: finish this
    self._allowed_values = { \
      'awn-drag-drop-ready':[False,True], \
      'detached':[False,True], \
      'displayed':[False,True], \
      'icon-mode':['pixbuf','cairo'], \
      'icon':[None,gtk.gdk.Pixbuf], \
      'icon-width':[int], \
      'icon-height':[int]}
      
    #These are the signals that can be connected to
    #Many (such as middle-press), will not be used
    self._connects = { \
      'event':[], \
      'attach':[], \
      'detach':[], \
      'hide-awn-icon':[], \
      'hide-dialog':[], \
      'draw-icon':[], \
      'applet-toggle-dialog':[], \
      'show-dialog':[], \
      'awn-dragged':[], \
      'applet-left-press':[], \
      'applet-left-release':[], \
      'applet-left-click':[], \
      'applet-middle-press':[], \
      'applet-middle-release':[], \
      'applet-middle-click':[], \
      'applet-right-press':[], \
      'applet-right-release':[], \
      'applet-right-click':[], \
      'left-press':[], \
      'left-release':[], \
      'left-click':[], \
      'middle-press':[], \
      'middle-release':[], \
      'middle-click':[], \
      'right-press':[], \
      'right-release':[], \
      'right-click':[], \
      'escape-key':[], \
      'focus-lost':[], \
      'scroll-up':[], \
      'scroll-right':[], \
      'scroll-down':[], \
      'scroll-left':[]}
  
  #Detach the applet, duh!
  def detach(self,position=None):
    if self['detached'] == False:
      self['detached'] = True
      self['displayed'] = False
      self.exposed = False
      self.button_pressed = False
      self.configure_after_move = False
      self.ready_for_configure = False
      
      #Make the window
      self.win = gtk.Window()
      self.win.align = gtk.Alignment(0.5,0.5,1,1)
      self.win.vbox = gtk.VBox(False)
      self.win.add(self.win.align)
      self.win.align.add(self.win.vbox)
      self.win.align.show_all()
      self.win.add = self.win.vbox.pack_start
      self.win.remove = self.win.vbox.remove
      
      #Give it the correct size, etc.
      self.win.set_default_size(self['icon-width']+8,self['icon-height']+8)
      self.win.set_border_width(8)
      
      #Give it the needed properties
      self.win.set_property('skip-pager-hint',True)
      self.win.set_property('skip-taskbar-hint',True)
      self.win.set_decorated(False)
      self.win.set_app_paintable(True)
      self.win.stick()
      
      #Give it an accelerator group
      self.accel = gtk.AccelGroup()
      self.win.add_accel_group(self.accel)
      
      #Connect to the right events
      self.win.add_events(gtk.gdk.ALL_EVENTS_MASK)
      self.win.connect('configure-event',self.configure)
      self.win.connect('button-press-event',self.button_press)
      self.win.connect('button-release-event',self.button_release)
      self.win.connect('expose-event', self.expose)
      self.win.connect('screen-changed', self.screen_changed)
      self.win.connect('destroy',self.attach)
      self.win.connect('key-press-event',self.key_press)
      self.win.connect('focus-out-event',self.focus_lost)
      self.win.connect('scroll-event',self.scroll)
      self.win.connect('motion-notify-event',self.motion_notify)
      
      #Get the RGBA colormap of the window
      #Also, get the window's screen
      self.screen_changed()
      
      #This causes the window to be exposed,
      #and the drawing will start at the right time
      self.win.show()
      
      #The applet can now be considered detached
      self.emit('detach')
      
      #Correctly position the window
      #No position specified
      if type(position)!=tuple:
        
        #Position the window at about the middle of the screen
        self.win.move(int(self.screen.get_width()/2-self['icon-width']/2),\
          int(self.screen.get_height()/2-self['icon-height']/2))
      
      #A specific position was specified
      else:
        self.win.move(int(position[0]),int(position[1]))
      
      #Tell the applet to hide its icon
      self.emit('hide-awn-icon')
      
      #Get the exact coordinates of the window
      self.posx,self.posy = self.win.get_position()
      
      #Yes, this connects to itself
      self.connect('hide-dialog',self._hide_dialog)
  
  #When the window has allocated space and position
  def configure(self,win,event):
    #print "CONFIGURE (pos size pressed after)", self.win.get_position(),\
    #self.win.get_size(), self.button_pressed, self.configure_after_move
    
    #Make sure that the window is detached
    if self['detached'] == True and self.ready_for_configure == True and\
      self.configure_after_move == True:
      
      self.button_pressed = False
      
      #Check that it should be dropped on Awn
      #print "CONFIGURE: checking for should attach"
      if self.should_drop_on_awn(\
        self.win.get_position()[1],self.win.get_size()[1])==True:
        
        #It should; do so
        gobject.idle_add(self.attach)
      
      #The button is not pressed; check that the window
      #is not off screen - sometimes Compiz Fusion does that,
      #and since this is not on the pager/alt-tab/etc, it
      #should be dealt with
      else:
        #TODO: Clean this up
        tmp_pos = win.get_position()
        if tmp_pos[0]<0 or\
          tmp_pos[1]<0 or\
          tmp_pos[0]>self.screen.get_width() or\
          tmp_pos[1]>self.screen.get_height():
          #Re-center the window
          self.win.move(int(self.screen.get_width()/2-self['icon-width']/2),\
            int(self.screen.get_height()/2-self['icon-height']/2))
    self.configure_after_move = True
  
  #When the window is exposed (sometimes aka ready for drawing),
  #draw on it appropriately
  def expose(self,*args):
    #print "EXPOSE", self['displayed'], self.exposed
    #If this is the first time this function has been called
    if self.exposed == False:
#      gtk.main_iteration()
      #The window is ready for drawing, so draw the icon
      gobject.idle_add(self.draw_icon)
      
      #So this is only done once
      self.exposed = True
    
    #This is called when the window must be re-exposed,
    #such as a button mouseover, etc.
    if self['displayed'] == True:
      #Clear the window
      self.clear()
      
      #Draw the background
      self.background()
  
  #A button was pressed on the window
  def button_press(self,widget,event):
    #print "BUTTON PRESS"
    #print 'button_press', self['displayed']
    if self.button_pressed == False:
      self.button_pressed = event.button
      
      #Emit the right signal
      
      #Left
      if event.button not in [2,3]:
        self.emit('left-press',event)
      
      #Middle
      elif event.button == 2:
        self.emit('middle-press',event)
      
      #Right
      elif event.button == 3:
        self.emit('right-press',event)
  
  #The mouse cursor was moved on the window
  def motion_notify(self,widget,event):
    #print "MOTION_NOTIFY",self.button_pressed,self['displayed']
    if self.button_pressed!=False:
      if self['displayed']==False:
        #Make sure that the applet wants the window
        #to be dragged around the screen
        if self.button_pressed in self['drag-around-screen']:
          self.ready_for_configure = True
          self.configure_after_move = False
          #Start the drag around the screen, don't display the dialog
          self.win_pos = self.win.get_position()
          self.win.begin_move_drag(self.button_pressed, int(event.x_root),\
            int(event.y_root), event.time)
          
          #Save the actual height of Awn to later determine
          #if the applet should be "dropped" on Awn
          for line in os.popen('xwininfo -name  "awn_elements"').readlines():
            if line.find("Height:") > 0:
              self.awn_height = int(line.split(' ')[-1])
  
  #A button was released on the window
  def button_release(self,widget,event):
    self.ready_for_configure = False
    
    #Emit the right signal
    #Left
    if event.button not in [2,3]:
      self.emit('left-release',event)
    
    #Middle
    elif event.button == 2:
      self.emit('middle-release',event)
    
    #Right
    elif event.button == 3:
      self.emit('right-release',event)
    
    #Do the right thing  based on the button that is released
    #Check that the dialog is NOT displayed
    if self['displayed'] == False:
      #Check that the button released is the originally pressed button
      if self.button_pressed==event.button:
        
        #The button is no longer pressed
        self.button_pressed = False
        
        #Check what the applet wants us to do based on the button
        if event.button not in [2,3]:
          self.emit('left-click',event)
          if self['left-click']=='show-dialog':
            self.win.resize(1,1)
            self.emit('show-dialog')
        elif event.button==2:
          self.emit('middle-click',event)
          if self['middle-click']=='show-dialog':
            self.win.resize(1,1)
            self.emit('show-dialog')
        elif event.button==3:
          self.emit('right-click',event)
          if self['right-click']=='show-dialog':
            self.win.resize(1,1)
            self.emit('show-dialog')
        
        #The dialog is now shown
        self['displayed'] = True
    self.button_pressed = False
  
  #Clear the window (draw transparency on it)
  #If the dialog is being displayed (Gtk widgets are shown)
  #Then this draws the transparency under the widgets
  def clear(self):
    #print "CLEAR"
    if self['detached']==True:
      self.cr = self.win.window.cairo_create()
      self.cr.set_source_rgba(1,1,1,0)
      self.cr.set_operator(cairo.OPERATOR_SOURCE)
      self.cr.paint()
  
  #Draw a background on the window - like Awn's default dialog,
  #but without the arrow
  def background(self):
    if self['draw-background'] == True:
      #print "BACKGROUND"
      #Update the colors in case the Gtk theme has changed
      self.get_colors()
      
      #Draw the background
      self.cr = self.win.window.cairo_create()
      self.cr.set_operator(cairo.OPERATOR_OVER)
      
      #Get the coordinates, etc.
      x0 = 4
      y0 = 4
      x1 = x0+self.win.get_size()[0]-8
      y1 = y0+self.win.get_size()[1]-8
      
      #Radius of the border
      radius = 5
      
      #Set the correct line width
      self.cr.set_line_width(3.0)
      
      #Draw the border
      #Copied from Avant Window Navigator and modified for this/ported to python
      #( /libawn/awn-cairo-utils.c )
      
      #Top left
      self.cr.move_to(x0,y0+radius)
      self.cr.curve_to(x0,y0,x0,y0,x0+radius,y0)
      
      #Top right
      self.cr.line_to(x1-radius,y0)
      self.cr.curve_to(x1,y0,x1,y0,x1,y0+radius)
      
      #Bottom right
      self.cr.line_to(x1,y1-radius)
      self.cr.curve_to(x1,y1,x1,y1,x1-radius,y1)
      
      #Bottom left
      self.cr.line_to(x0+radius,y1)
      self.cr.curve_to(x0,y1,x0,y1,x0,y1-radius)
      
      #Finish
      self.cr.line_to(x0,y0+radius)
      self.cr.close_path()
      
      #Fill the rectangle
      self.cr.set_source_rgba(self.bg_red,self.bg_green,self.bg_blue,0.9)
      self.cr.fill_preserve()
      
      #Actually draw the border
      self.cr.set_source_rgba(self.fg_red,self.fg_green,self.fg_blue,0.9)
      self.cr.stroke()
  
  #When the screen has changed - get the new RGBA colormap
  def screen_changed(self,*args):
    #print "SCREEN_CHANGED"
    #Get the window's screen
    self.screen = self.win.get_screen()
    
    #Get the window's screen's colormap
    self.colormap = self.screen.get_rgba_colormap()
    
    #Set up the window
    self.win.unrealize()
    self.win.set_colormap(self.colormap)
    
    return True
  
  #Emit the 'hide-dialog' signal
  #This looks better to the applet dev
  def hide_dialog(self):
    self.emit('hide-dialog')
  
  #Actually hide the dialog - clear, go back to icon, etc.
  def _hide_dialog(self):
    #print "HIDE_DIALOG"
    
    self['displayed'] = False
    
    #Clear the dialog
    self.clear()
    
    #Resize the window back to the icon plus padding
    self.win.resize(self['icon-width']+8,self['icon-height']+8)
    
    #Draw the icon
    #The expose event will be called.
    #It sees that self.exposed is False, so it clears the window and
    #draws the icon, just like when the window was first detached
    self.exposed = False
    
    #print "(HIDE_DIALOG END)"
  
  #When the focus has been lost
  def focus_lost(self,widget,event):
    #print "focus_lost", self.applet_button_pressed, self['displayed']
    
    #It does; check if the dialog is being displayed
    if self['displayed']==True:
      
      #It is; find out what the applet wants to do
      
      #Just hide the dialog
      if self['focus-lost']=='hide-dialog':
        self.hide_dialog()
      
      #Emit the signal
      elif self['focus-lost']=='signal':
        self.emit('focus-lost',event)
  
  #A key was pressed; check for Escape key
  #If so: hide the dialog
  def key_press(self,widget,event):
    
    #First: check if the applet wants the detached dialog to "hide"
    #when the escape key is pressed
    if self['escape-key']=='hide-dialog':
      
      #It does; check that the escape key was pressed
      if event.keyval == 65307:
        
        #It was; hide the dialog
        self.emit('hide-dialog')
    
    #Now, check if the applet instead just wants
    #a signal saying the escape was pressed emitted
    elif self['escape-key']=='signal':
      
      #It does; check that the escape key was pressed
      if event.keyval == 65307:
        
        #It was; emit the signal
        self.emit('escape-key',event)
  
  #Draw the icon, or tell the applet to draw the icon via cairo
  def draw_icon(self,expose=False):
    #print "DRAW_ICON"
    #A pixbuf is used
    if self['icon-mode']=='pixbuf':
      
      #Clear the window
      self.clear()
      
      #Get a new cairo context
      self.cr = self.win.window.cairo_create()
      self.cr.set_operator(cairo.OPERATOR_OVER)
      
      #Set the source pixbuf of the cairo context to the applet's icon
      self.cr.set_source_pixbuf(self['icon'],0,0)
      
      #Now paint the pixbuf
      self.cr.translate(8,8)
      self.cr.paint()
      
      if expose==True:
        gobject.timeout_add(50,self.draw_icon)
      
    #Cairo drawing is used; emit the 'draw-icon' signal
    elif self['icon-mode']=='cairo':
      
      #Clear the dialog - again, also gets the cairo context
      self.clear()
      
      #Hopyfully the applet is connected to this signal
      #If so, it should draw on the cairo context
      self.emit('draw-icon',self.cr)
    
    #Some surface drawing is used; draw the surface to, well, the surface
    elif self['icon-mode']=='surface':
      
      #Clear dialog
      self.clear()
      
      #Get a new cairo context
      self.cr = self.win.window.cairo_create()
      self.cr.set_operator(cairo.OPERATOR_OVER)
      
      #Set the source surface of the cairo context to the applet's icon
      self.cr.set_source_surface(self['icon'],0,0)
      
      #Now paint the surface
      self.cr.translate(8,8)
      self.cr.paint()
      
      if expose==True:
        gobject.timeout_add(50,self.draw_icon)
    
    #Explicitly no icon is used; clear the surcafe
    elif self['icon-mode'] is None:
      print 'icon-mode is None'
      #Clear the dialog
      self.clear()
      
  
  #Destroy the window, etc.
  #Tell the applet to attach to Awn
  #(such as reparent/destroy the widget,
  #hide the icon, etc.)
  def attach(self,*args):
    if self['detached'] == True:
      self['detached'] = False
      
      #Hopefully the applet is connected to this signal
      #If so, it should show its normal icon
      self.emit('attach')
      
      #Destroy the window
      self.win.destroy()
      
      #Save a little memory
      del self.screen, self.colormap, self.cr
  
  #Get the colors for drawing the background of the dialog
  def get_colors(self):
    #print "GET_COLORS"
    #Realize the window so we can get the correct colors
    self.win.realize()
    
    #Get the background color - will be used for the background of the window
    state1 = gtk.STATE_ACTIVE
    state2 = gtk.STATE_SELECTED
    style = self.win.get_style()
    self.bg_red =   float(style.bg[state1].red)/65535.0
    self.bg_green = float(style.bg[state1].green)/65535.0
    self.bg_blue =  float(style.bg[state1].blue)/65535.0
    
    #Get the foreground color - will be used for the border of the window
    self.fg_red = float(style.bg[state2].red)/65535.0
    self.fg_green = float(style.bg[state2].green)/65535.0
    self.fg_blue =  float(style.bg[state2].blue)/65535.0
  
  #Prepare the applet and detach for drag and drop to and from Awn
  def prepare_awn_drag_drop(self,applet):
    
    #These will be referenced later
    self.applet_button_pressed = True
    self.applet_button_press_event = None
    self.applet_size = applet.get_size()
    
    #Connect to the right signals/events
    applet.connect('button-press-event',self.applet_button_press)
    applet.connect('button-release-event',self.applet_button_release)
    applet.connect('motion-notify-event',self.applet_motion)
    applet.connect('size-changed',self.applet_size_changed)
    applet.connect('scroll-event',self.scroll)
    
    #Applet is ready to be dragged and dropped to and from Awn
    self['awn-drag-drop-ready'] = True
  
  #A button is pressed on the applet (not released)
  def applet_button_press(self,applet,event):
    #print "APPLET_BUTTON_PRESS"
    #Check which button was pressed
    #Left click: (or anything else not middle nor right)
    if event.button not in [2,3]:
      
      #Remember what button is pressed on the applet
      self.applet_button_pressed = event.button
      
      #Save the event for later reference
      self.applet_button_press_event = event.copy()
      
      #Emit this signal
      self.emit('applet-left-press',event)
    
    #Middle click:
    elif event.button == 2:
      
      #Remember what button is pressed on the applet
      self.applet_button_pressed = event.button
      
      #Emit this signal
      self.emit('applet-middle-press',event)
    
    #Right click:
    elif event.button == 3:
      
      #Remember what button is pressed on the applet
      self.applet_button_pressed = event.button
      
      #Emit this signal
      self.emit('applet-right-press',event)
  
  #A button is released on the applet
  def applet_button_release(self,applet,event):
    #print "APPLET_BUTTON_RELEASE"
    
    #Not middle or right click (probably left)
    if event.button not in [2,3]:
      self.emit('applet-left-release',event)
      
      #Check that this is the same button as pressed
      if self.applet_button_pressed == event.button:
        
        #Check that the applet is not detached
        if not self['detached']:
          
          #Find out what the applet wants us to do
          #Show the dialog
          if self['applet-left-click']=='applet-toggle-dialog':
            
            #Show the dialog
            self.emit('applet-toggle-dialog')
          
          #Emit the signal
          elif self['applet-left-click']=='signal':
            
            #Emit the signal
            self.emit('applet-left-click',event)
    
    #Middle
    elif event.button == 2:
      self.emit('applet-middle-release',event)
      
      #Check that this is the same button as pressed
      if self.applet_button_pressed == 2:
        
        #Check that the applet is not detached
        if not self['detached']:
          
          #Find out what the applet wants us to do
          #Show the dialog
          if self['applet-middle-click']=='applet-toggle-dialog':
            
            #Show the dialog
            self.emit('applet-toggle-dialog')
          
          #Emit the signal
          elif self['applet-middle-click']=='signal':
            
            #Emit the signal
            self.emit('applet-middle-click',event)
    
    #Right
    elif event.button == 3:
      self.emit('applet-right-release',event)
      
      #Check that this is the same button as pressed
      if self.applet_button_pressed == 3:
        
        #Check that the applet is not detached
        if not self['detached']:
          
          #Find out what the applet wants us to do
          #Show the dialog
          if self['applet-right-click']=='applet-toggle-dialog':
            
            #Show the dialog
            self.emit('applet-toggle-dialog')
          
          #Emit the signal
          elif self['applet-right-click']=='signal':
            
            #Emit the signal
            self.emit('applet-right-click',event)
    
    #The button is no longer pressed
    self.applet_button_pressed = False
  
  #The cursor was moved on the applet
  def applet_motion(self,applet,event):
    
    #Check if it was remembered that the button is pressed
    if self.applet_button_pressed != False:
      
      try:
        if int(self.applet_button_press_event.y_root-event.y_root) >= \
          int(self.applet_size/3.0):
          #print "APPLET DRAGGED FROM AWN"
          
          #It did; detach the applet!
          #Pass the position of the window as a dictionary
          self.detach((event.x_root,event.y_root))
          
          #So the applet hides the icon, knows that it's detached, etc.
          self.emit('awn-dragged')
          
          #The button is no longer pressed on the applet
          #(it's still REALLY pressed though)
          self.applet_button_pressed = False
          
          #Start the dragging of the window when ready
          gobject.idle_add(self.win.begin_move_drag,\
            self.applet_button_press_event.button,\
            int(event.x_root),\
            int(event.y_root),\
            event.time)
      except:
        #Occasionally this raises an AttributeError -
        #but it still works fine...
        pass
  
  #The size of the applet (/ Awn bar) has changed - remember it
  def applet_size_changed(self,applet,size):
    #Save the applet height
    self.applet_size = size
  
  #Find out if the applet should be "dropped" on Awn
  def should_drop_on_awn(self,posy,height):
    #print "should_drop_on_awn: posy,height,awn_height,scr.height"
    #print posy, height, self.awn_height, self.screen.get_height()
    #print self.screen.get_height() - self.awn_height, 'scr.h-awn.h'
    #print posy+height, 'y+h'
    scr_awn = self.screen.get_height()-self.awn_height
    y_h = posy+height
    #print
    #print posy,scr_awn,height
    return posy >= (scr_awn-height)
    #return scr_awn >= y_h
    #return self.screen.get_height() - self.awn_height >= posy + height
  
  #Helper function to set the icon to <pixbuf> and draw it if necessary
  def set_pixbuf(self,pixbuf):
    
    #Make sure we are using a GdkPixbuf for the icon
    if self['icon-mode'] == 'pixbuf':
      self['icon'] = pixbuf
      
      #If the icon is being shown and the dialog is not being displayed -
      #show the new icon
      if self['detached']==True and self['displayed']==False:
        self.exposed = False
        self.win.resize(self['icon-width']+8,self['icon-height']+8)
  
  #Helper function to set the icon to <surface> and draw it if necessary
  def set_surface(self,surface):
    #Make sure we are using a surface for the icon
    if self['icon-mode'] == 'surface':
      self['icon'] = surface
      
      #Draw it if the dialog is NOT displayed
      if self['displayed']==False and self['detached']==True:
        #Clear window
        self.clear()
        
        #Prepare Cairo
        self.cr.set_operator(cairo.OPERATOR_OVER)
        
        #Set the source surface of the cairo context to the applet's icon
        self.cr.set_source_surface(self['icon'],0,0)
        
        #Now paint the surface
        self.cr.translate(8,8)
        self.cr.paint()
  
  #Helper function to add the widget to the window
  #Equivalent to .win.add(...)
  def add(self,widget):
    self.win.vbox.pack_start(widget)
  
  #Helper function to remove the widget from the window
  #Equivalend to .win.vbox.remove(...)
  def remove(self,widget):
    self.win.vbox.remove(widget)
  
  #Helper function to emit the right signal when the mouse wheel is scrolled
  #Some applets may have their icon size increase if the icon is scrolled
  #Of course, this does no resizing, but if the applet is connected to the
  #scroll-* signals, it'll do the resizing or whatever it wants to do
  #(such as change workspace/viewport)
  def scroll(self,widget,event):
    if event.direction == gtk.gdk.SCROLL_UP:
      self.emit('scroll-up',event)
    elif event.direction == gtk.gdk.SCROLL_RIGHT:
      self.emit('scroll-right',event)
    elif event.direction == gtk.gdk.SCROLL_DOWN:
      self.emit('scroll-down',event)
    elif event.direction == gtk.gdk.SCROLL_LEFT:
      self.emit('scroll-left',event)
  
  #Helper function to make a 1x1 transparent pixbuf and return it
  #The applet can use this to hide the icon
  def empty_pixbuf(self):
    #Make a pixbuf with transparency
    empty_pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,True,8,1,1)
    
    #Fill it with black transparency
    empty_pixbuf.fill(0x00000000)#0xRRGGBBAA where RR is from 00 to FF
    
    #Return it
    return empty_pixbuf
  
  #Helper function to make a simple "Detach" menu item with an Up arrow
  def menu_item(self,detach_func=None,attach_func=None,\
    detach_text=None,attach_text=None):
    #Applet wants a Detach applet menu icon
    if self['detached']==False:
      menu = gtk.ImageMenuItem(gtk.STOCK_GO_UP)
      
      menu.get_children()[0].set_text(\
        [detach_text,'Detach'][detach_text is None])
      
      if detach_func is not None:
        menu.connect('activate',detach_func)
    
    #Applet wants an Attach applet menu icon
    else:
      menu = gtk.ImageMenuItem(gtk.STOCK_GO_DOWN)
      
      menu.get_children()[0].set_text(\
        [attach_text,'Attach'][attach_text is None])
      
      if attach_func is not None:
        menu.connect('activate',attach_func)
    
    return menu
  
  #"Emit" a signal, such as 'attach'
  #Any connected functions will be called
  def emit(self,strid,*args):
    
    #Emit the 'event' signal first
    if strid!='event':
      self.emit('event',strid,*args)
    
    #If is emitting something for detaching:
    if strid in self._connects.keys():
      
      #Go through each of the connected functions
      for x in self._connects[strid]:
        
        #Correctly call the function
        if len(x)==3:
          x[0](*args+x[1],**x[2])
    
    #Emit the same signal on the window
    else:
      self.win.emit(strid)
  
  #"Connect" to a signal, such as 'show-dialog'
  #When that signal is emitted, this function
  #will be called with all its arguments, including
  #the argument(s) passed when emit() is called
  def connect(self,strid,func,*args,**args2):
    #print "CONNECT:", strid
    if type(strid) in [list,tuple]:
      for x in strid:
        self.connect(x,func,*args,**args2)
    else:
      try:
        self._connects[strid].append([func,args,args2])
      except:
        try:
          return self.win.connect(strid,func,*args)
        except:
          #print "Signal", strid, "does not exist"
          raise AttributeError
  
  #When this instance is used like a dictionary, such as instance[key] = val
  #Getting values
  def __getitem__(self,key):
    return self._settings[key]
  
  #Setting values
  def __setitem__(self,key,val):
    #print '[\''+str(key)+'\']', "=", val
    self._settings[key] = val
  
  #Deleting values
  def __delitem__(self,key):
    #print "del", key
    self._settings[key] = None
