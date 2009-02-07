#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
#
# Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
#
# This is a calendar applet for Avant Window Navigator.
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
import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import gconf
import pango
import awn, awn.extras
import cairo
from StringIO import StringIO
import datetime
import gc
import time
import sevensegled
import subprocess
import gnomevfs
import calendarprefs
import calendarlogin
import random
import googlecal
import owacal
import evocal
import calthread

# locale stuff
APP="awn-calendar"
DIR="locale"
import locale
import gettext
#locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext

class App(awn.AppletSimple):

	# default title/tooltip to show on startup.
	title_text = _("Calendar")

	# "Private" stuff
	dialog_visible = False
	gconf_path = "/apps/avant-window-navigator/applets/calendar"
	locale_lang = "en"
	counter = 0
	twelve_hour_clock = True
	blinky_colon = False
	integration = None
	integ_text = "None"
	graphic = "calendar.png"
	surface = None
	bkg_img = None
	plainClock = False
	show_title = False
	clock_background = (0.4,0.5,0.4,1.0)
	clock_text = (0.0,0.0,0.0,0.0)	
	clock_border = (0.0,0.0,0.0,0.0)
	clock_plain = False
	username = ""
	password = None
	url = ""
	login_open = False
	previous_minute = -1
	previous_day = -1
	ct = None
	thread = None
	days = []

	def __init__(self, uid, orient, height):
		awn.AppletSimple.__init__ (self, uid, orient, height)
		self.height = height
		def on_height_changed(applet, height):
			self.height = height
			self.surface = None
			self.repaint()
		self.connect("height-changed", on_height_changed)
		icon = gdk.pixbuf_new_from_file(os.path.dirname (__file__) + '/images/calendar.png')
		scaled = icon.scale_simple(height,height,gtk.gdk.INTERP_BILINEAR)
		self.set_temp_icon(scaled)
		self.title = awn.awn_title_get_default()
		self.dialog = awn.AppletDialog (self)
		self.connect ("button-press-event", self.button_press_callback)
		self.connect ("enter-notify-event", self.enter_notify_callback)
		self.connect ("leave-notify-event", self.leave_notify_callback)
		self.dialog.connect ("focus-out-event", self.dialog_focus_out_callback)
		gobject.timeout_add(100,self.first_paint)		
		self.timer = gobject.timeout_add(1000,self.timer_callback)
		#self.timer = gobject.timeout_add(1000,self.subsequent_paint)
		self.popup_menu = self.create_default_menu()
		pref_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_PREFERENCES)
		forget_item = gtk.MenuItem("Forget Password")
		about_item = gtk.ImageMenuItem(stock_id=gtk.STOCK_ABOUT)
		self.popup_menu.append(pref_item)
		self.popup_menu.append(forget_item)
		self.popup_menu.append(about_item)
		pref_item.connect_object("activate",self.pref_callback,self)
		forget_item.connect_object("activate",self.forget_callback,self)
		about_item.connect_object("activate",self.about_callback,self)
		pref_item.show()
		forget_item.show()
		about_item.show()
		# Build a login window.
		self.login_window = calendarlogin.CalendarLogin(self)
		self.login_window.set_size_request(350, 150)
		self.login_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		self.login_window.set_modal(True)
		self.login_window.set_destroy_with_parent(True)
		# Get config params
		self.gconf_client = gconf.client_get_default()
		self.gconf_client.notify_add(self.gconf_path, self.config_event_callback)
		self.get_config()
		if self.password == None and self.integration != None and self.integration.requires_login == True:
			self.login()
		try:
			self.locale_lang = locale.getdefaultlocale()[0][0:2]
		except:
                        pass
			#print "locale not set"
		self.connect("destroy",self.quit_callback)
		gtk.gdk.threads_init()


	############################################################################
	# Configuration.
	############################################################################

	def get_boolean_config(self,key,default):
		result = self.gconf_client.get_bool(self.gconf_path + "/" + key)
		if result == None:
			self.gconf_client.set_bool(self.gconf_path + "/" + key, default)
			result = default
		return result
	
	def get_string_config(self,key,default):
		result = self.gconf_client.get_string(self.gconf_path + "/" + key)
		if result == None:
			self.gconf_client.set_string(self.gconf_path + "/" + key, default)
			result = default
		return result

	def get_config(self, key_change=None):
		self.previous_minute = -1 # forces a full repaint
		self.twelve_hour_clock = self.get_boolean_config("twelve_hour_clock",True)
		self.blinky_colon = self.get_boolean_config("blinking_colon",False)
		self.clock_plain = self.get_boolean_config("clock_plain",False)
		self.integ_text = self.get_string_config("integration","None")
		if self.integ_text == "Evolution":
			self.integration = evocal.EvoCal(self)
		elif self.integ_text == "Google Calendar":
			self.integration = googlecal.GoogleCal(self)
		elif self.integ_text == "Outlook Web Access":
			self.integration = owacal.OwaCal(self)
		else:
			self.integration = None
		self.username = self.get_string_config("username","")		
		tmp_password = self.get_string_config("password","")
		if tmp_password != "":
			self.password = tmp_password
		else:
			self.password = None
		self.url = self.get_string_config("url","")		
		self.graphic = self.get_string_config("graphic","calendar-red.png")
		self.bkg_img = cairo.ImageSurface.create_from_png(os.path.dirname (__file__) + '/images/' + self.graphic)
		background = self.get_string_config("clock_background","667F66FF")		
		self.clock_background = self.hex_string_to_color(background)
		foreground = self.get_string_config("clock_foreground","000000FF")		
		self.clock_text = self.hex_string_to_color(foreground)
		border = self.get_string_config("clock_border","000000FF")		
		self.clock_border = self.hex_string_to_color(border)
		self.login_window.update_integ_text(self.integ_text)
		self.login_window.user.set_text(self.username)
		if key_change == "/apps/avant-window-navigator/applets/calendar/integration":
			self.login()
		if self.thread != None:
			self.thread.kill()
			self.thread = None
		self.thread = calthread.CalThread(self)
		self.thread.start()

	############################################################################
	# Callbacks..
	############################################################################

	def forget_callback(self, widget):
		text = _("Do you want to erase your calendar password from the calendar applet?  If you choose to clear your password, you will be prompted again for your calendar login credentials.")
		dialog = gtk.MessageDialog(parent=None, flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_YES_NO, type=gtk.MESSAGE_INFO, message_format=text)
		response = dialog.run()
		if response == gtk.RESPONSE_YES:
			# If the password is already clear, they probably are trying to re-login.  Setting the password to the same thing
			# that it already is set to won't trigger a config event, so they'll be out of luck.  So force a re-login if this
			# is the case.
			current = self.get_string_config("password","")
			if self.password != None and current != "":
				self.password = None
				self.gconf_client.set_string(self.gconf_path + "/password", "")
			self.login_window.password.set_text("")
			self.login()
		dialog.destroy()

	def pref_callback(self, widget):
		window = calendarprefs.CalendarPrefs(self)
		window.set_size_request(400, 250)
		window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
		window.set_destroy_with_parent(True)
		window.show_all()
				
	def about_callback(self, widget):
		about_dialog = gtk.AboutDialog()
		about_dialog.set_name("Avant Calendar Applet")
		about_dialog.set_copyright("Copyright 2007 Mike Desjardins")
		about_dialog.set_comments("A Calendar Applet for the Avant Window Navigator.  Images by Deleket (http://deleket.deviantart.com)")
		about_dialog.set_authors(["Mike Desjardins"])		
		about_dialog.set_artists(["Deleket", "Mike Desjardins"])		
		about_dialog.connect("response", lambda d, r: d.destroy())
		about_dialog.show()

	def goto_today_callback(self, widget, event):
		year,month,day,hour,minute,sec,msec,whocares,whocares2 = time.localtime()
		self.cal.select_month(month-1,year)
		self.cal.select_day(day)

	def config_event_callback(self, gconf_client, *args, **kwargs):
		key = args[1].get_key()
		self.get_config(key)

	def dialog_focus_out_callback(self, widget, event):
		self.show_title = False   
                self.dialog.hide()
                self.dialog_visible = False

	def enter_notify_callback(self, widget, event):
		self.show_title = True
		self.title.show(self, self.title_text)

	def leave_notify_callback(self, widget, event):
		self.show_title = False

	def button_press_callback(self,widget,event):
		self.show_title = False
		if self.dialog_visible:
			self.dialog.hide()
			self.dialog_visible = False
		else:
			if event.button == 3: # right click
				self.popup_menu.popup(None, None, None, event.button, event.time)
			else:
				self.build_calendar_dialog()
				self.dialog.show_all()
				self.dialog_visible = True
				
	def timer_callback(self):
		result = None
		current_minute = time.localtime()[4]
		current_day = time.localtime()[2]
		if current_day != self.previous_day:
			self.surface = None
		self.init_context()			
		if current_minute != self.previous_minute:
			result=self.repaint()
		else:		
			if self.blinky_colon == True:
				self.draw_colon(self.ct,123,202,30)
				self.set_icon_context(self.ct)
			result=True
		now = datetime.datetime.now()
		self.title_text = now.strftime("%x %X")
		if self.show_title == True:
			self.title.show(self, self.title_text)
		else:
			self.title.hide(self)
		self.previous_minute = current_minute
		self.previous_day = current_day
		return result

	def quit_callback(self):
		self.thread.kill()

	def month_changed_callback(self,widget):
		self.cal.clear_marks()
		cal_sel_date = self.cal.get_date()
		cal_date = (cal_sel_date[0], cal_sel_date[1]+1, cal_sel_date[2])
		if self.thread.check_cache(cal_date) == True:
			year,month,day = cal_date
			busy = self.thread.get_days(year,month)
			for day in busy:
				self.cal.mark_day(day)


	############################################################################
	# Drawing.
	############################################################################

	def init_context(self):
		if self.bkg_img == None:
			self.bkg_img = cairo.ImageSurface.create_from_png(os.path.dirname (__file__) + '/images/' + self.graphic)

		if self.surface == None:
                	height = self.get_height()
			self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, height, height)
			self.ct = cairo.Context(self.surface)
			self.ct.scale(float(height) / self.bkg_img.get_width(),
                                      float(height) / self.bkg_img.get_height())

	def first_paint(self):
		self.repaint()
		return False

	def get_text_width(self, context, text, maxwidth):
		potential_text = text
		text_width = context.text_extents(potential_text.encode('ascii','replace'))[2]
		end = -1
		while text_width > maxwidth:
			end -= 1
			potential_text = text.encode('ascii','replace')[:end] + '...'
			text_width = context.text_extents(potential_text.encode('ascii','replace'))[2]
		return potential_text, text_width

	def repaint(self):
		self.init_context()
		now = datetime.datetime.now()

                self.ct.set_operator(cairo.OPERATOR_SOURCE)
		self.ct.set_source_surface(self.bkg_img)
		self.ct.paint()
                self.ct.set_operator(cairo.OPERATOR_OVER)
		if self.clock_plain == False:		
			red, green, blue, alpha = self.clock_background
			self.ct.set_source_rgba(red,green,blue,alpha)		
			self.draw_rounded_rect(self.ct,35,191,182,51,20)
			self.ct.fill()
			red, green, blue, alpha = self.clock_border
			self.ct.set_source_rgba(red,green,blue,alpha)
			self.draw_rounded_rect(self.ct,35,191,182,51,20)
			self.ct.stroke()
			red, green, blue, alpha = self.clock_text
			self.ct.set_source_rgba(red,green,blue,alpha)
			led = sevensegled.SevenSegLed(self.ct) 
			self.draw_time_led(self.ct, led, 58, 202, 20, 30)
		else:
			# Shadow first
			red, green, blue, alpha = self.clock_background
			self.ct.set_source_rgba(red,green,blue,alpha)
			hour = now.strftime("%H")
			minute = now.strftime("%M")
			shorten = False		
			if hour[0] == "0":
				shorten = True
				hour = hour[1]
				if hour == "0": #is this 12AM?
					hour = "12"
				else:
					shorten = True
			elif self.twelve_hour_clock and int(hour) > 12:
				if int(hour) < 22:
					shorten = True
				hour = str(int(hour)-12)
			#	
			#
			#self.ct.move_to(37,240)
			self.ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
			self.ct.set_font_size(60.0)
			t = now.strftime("%H:%M")			
			if self.twelve_hour_clock == True:
				t = hour + ":" + minute
			text, width = self.get_text_width(self.ct, t, 250)
			x = (256 - width)/2
			self.ct.move_to(x,240)
			self.ct.show_text(t)	
			#
			#
			# Now foreground
			red, green, blue, alpha = self.clock_text
			self.ct.set_source_rgba(red,green,blue,alpha)
			self.ct.move_to(x-7,232)
			#if self.twelve_hour_clock == True:
			#	# The leading zero looks stupid on twelve hour clocks
			#	if shorten == True:
			#		self.ct.move_to(52,232)
			#	#seconds = time.localtime()[5]				
			#	#if self.blinky_colon == False or seconds % 2 == 0:
			#	self.ct.show_text(hour + ":" + minute)
			#	#else:
			#	#	ct.show_text(hour + " " + minute)
			#else:
			#	self.ct.show_text(now.strftime("%H:%M"))
			self.ct.show_text(t)
		self.ct.set_source_rgba(0.0,0.0,0.0,1.0)
		self.ct.select_font_face("Deja Vu",cairo.FONT_SLANT_NORMAL,cairo.FONT_WEIGHT_BOLD)
		self.ct.set_font_size(64.0)
		daytext = now.strftime("%d")
		if daytext[0] == "0":
			daytext = daytext[-1]
		text, width = self.get_text_width(self.ct, daytext, 999)
		x = (250 - width)/2
		self.ct.move_to(x,122)
		self.ct.show_text(text)
		self.ct.set_source_rgba(0.0,0.0,0.0,1.0)
		self.ct.set_font_size(36.0)
		text, width = self.get_text_width(self.ct, now.strftime("%a"), 999)
		x = (250 - width)/2
		self.ct.move_to(x,155)
		self.ct.show_text(text)
		text, width = self.get_text_width(self.ct, now.strftime("%b"), 999)
		x = (250 - width)/2
		self.ct.set_source_rgba(1.0,1.0,1.0,1.0)
		self.ct.move_to(x,60)
		self.ct.show_text(now.strftime("%b"))
		self.set_icon_context(self.ct)
		return True

	def draw_time_led(self, context, led, x0, y0, width, height):
		xpos = x0
		ypos = y0
		hours = time.localtime()[3]
		minutes = time.localtime()[4]
		seconds = time.localtime()[5]
		if self.twelve_hour_clock == True and hours > 12:
			hours = hours - 12
		# For twelve-hour clocks, don't draw the leading zeros.
		if self.twelve_hour_clock == False or hours > 9:
			led.draw(hours/10, context, xpos, ypos, xpos+width, ypos+height)
		xpos = xpos + 30
		led.draw(hours%10, context, xpos, ypos, xpos+width, ypos+height)
		# draw the separator (hard-code to a colon for now)
		xpos = xpos + 35		
		if self.blinky_colon == False or seconds % 2 == 0:
			self.draw_colon(context,xpos,ypos,height)
			#print "xpos %d ypos %d height %d" % (xpos, ypos, height)
			#context.move_to(xpos, ypos+(height/2)-2)
			#context.rel_line_to(0, 4)
			#context.move_to(xpos, ypos+height)
			#context.rel_line_to(0, -4)
		xpos = xpos + 15			
		led.draw(minutes/10, context, xpos, ypos, xpos+width, ypos+height)
		xpos = xpos + 30
		led.draw(minutes%10, context, xpos, ypos, xpos+width, ypos+height)

	def draw_colon(self, context, xpos, ypos, height):
		seconds = time.localtime()[5]
		if self.blinky_colon == True:
			if seconds % 2 == 0:
				red, green, blue, alpha = self.clock_text
			else:
				red, green, blue, alpha = self.clock_background
		else:
			red, green, blue, alpha = self.clock_text
		context.set_source_rgba(red,green,blue,alpha)
		(xpos, ypos, height) = (123, 202, 30)
		context.save()
		context.move_to(xpos, ypos+(height/2)-2)
		context.rel_line_to(0, 4)
		context.move_to(xpos, ypos+height)
		context.rel_line_to(0, -4)
		context.stroke()
		context.restore()

	############################################################################
	# Calendar Dialog.
	############################################################################

	def build_calendar_dialog(self):
		self.cal = gtk.Calendar()
		self.cal.connect("day-selected", self.update_tree_view)
		self.dialog = awn.AppletDialog (self)
		self.dialog.connect ("focus-out-event", self.dialog_focus_out_callback)
		self.dialog.set_title(_("Calendar"))
		self.vbox = gtk.VBox()
		self.hbox = gtk.HBox()
		self.vbox.pack_start(self.cal)
		hbox2 = gtk.HBox()
		if self.integration != None:
			self.opencal = gtk.Button(_("Open in ") + self.integ_text)
			self.opencal.connect("button-press-event", self.open_integrated_calendar)
			hbox2.pack_start(self.opencal)
		self.goto_today = gtk.Button(_("Today"))
		self.goto_today.connect("button-press-event", self.goto_today_callback)
		self.cal.connect("month-changed",self.month_changed_callback)
		hbox2.pack_start(self.goto_today)
		self.vbox.pack_start(hbox2)
		self.hbox.pack_start(self.vbox,False)
		if self.integration != None:
			self.dialog.set_size_request(600,300)		
			self.scrolled_win = gtk.ScrolledWindow()
			self.scrolled_win.set_border_width(10)
			self.scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
			self.list = gtk.ListStore(str,str)
			self.treeview = gtk.TreeView(self.list)
			self.tvcolumn = gtk.TreeViewColumn()
			self.treeview.append_column(self.tvcolumn)
			self.cell = gtk.CellRendererText()
			self.tvcolumn.pack_start(self.cell,True)
			self.tvcolumn.add_attribute(self.cell, 'text', 0)
			self.treeview.set_headers_visible(False)
			self.treeview.set_rules_hint(True)
			self.scrolled_win.add_with_viewport(self.treeview)
			self.hbox.pack_start(self.scrolled_win,True,True,5)
			self.update_tree_view(self.window)
		self.dialog.add(self.hbox)
		self.dialog.show_all()
		year,month,day,hour,minute,sec,msec,who,cares = time.localtime()
		self.cal.clear_marks()
		if self.thread.check_cache((year,month,day)) == True:
			busy = self.thread.get_days(year,month)
			for day in busy:
				self.cal.mark_day(day)
	
	def update_tree_view(self,widget):
		if self.integration != None:
			self.list.clear()
			cal_sel_date = self.cal.get_date()
			cal_date = (cal_sel_date[0], cal_sel_date[1]+1, cal_sel_date[2])
			try:
				if self.thread.check_cache(cal_date):
					events = self.thread.get_appointments(cal_date)
				else:
					events = self.integration.get_appointments(cal_date,self.url)
				for i, event in enumerate(events):	
					self.list.append([event[1],i])
			except:
				#print "Login error: ", sys.exc_info()[0], sys.exc_info()[1] 
				dialog = gtk.MessageDialog(parent=None, flags=gtk.DIALOG_MODAL, buttons=gtk.BUTTONS_OK, type=gtk.MESSAGE_WARNING, message_format=_("Unable to read calendar data from external source."))
				dialog.run()
				dialog.destroy()			

	def open_integrated_calendar(self,widget,event):
		if self.integration != None:
			when = self.cal.get_date()		
			self.integration.open_integrated_calendar(when,self.url)

	def login(self):
		# Try to avoid any potential weird race-conditions where we end up with two of these open.
		if self.integration != None:
			if self.login_open == False:
				if self.integration.requires_login == True:
					self.login_open = True
					self.login_window.show_all()
					self.login_open = False
				else:
                                        pass
					#print "Already have password, or this calendar doesn't require a login."
			else:
                                pass
				#print "Login window already opened?"
	
	############################################################################
	# Utilities.
	############################################################################

	def crypt(self,sequence, key):
		sign = (key > 0) * 2 - 1
		random.seed (abs (key * sign))
		s = ''
		for i in xrange (len (sequence)):
			r = random.randint(0, 255)
			s += chr ((ord (sequence [i]) + r * sign) % 128)
		return s

	def draw_rounded_rect(self,context,x,y,w,h,r = 10):
		#   A****BQ
		#  H      C
		#  *      *
		#  G      D
		#   F****E
		context.move_to(x+r,y)                      # Move to A
		context.line_to(x+w-r,y)                    # Straight line to B
		context.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
		context.line_to(x+w,y+h-r)                  # Move to D
		context.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
		context.line_to(x+r,y+h)                    # Line to F
		context.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
		context.line_to(x,y+r)                      # Line to H
		context.curve_to(x,y,x,y,x+r,y)             # Curve to A
		return

	def hex_string_to_color(self,hex):
		red = int(hex[0:2],16)
		green = int(hex[2:4],16)
		blue = int(hex[4:6],16)
		alpha = int(hex[6:8],16)
		return (red/255.0, green/255.0, blue/255.0, alpha/255.0)

############################################################################
# Applet Initialization.
############################################################################

if __name__ == "__main__":
	awn.init (sys.argv[1:])
	os.nice(19)
	#print "main %s %d %d" % (awn.uid, awn.orient, awn.height)
	applet = App(awn.uid, awn.orient, awn.height)
	awn.init_applet(applet)
	applet.show_all()
	gtk.main()
	applet.quit_callback()


