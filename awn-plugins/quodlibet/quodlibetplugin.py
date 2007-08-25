import wnck
import gobject
import gtk
import time
import dbus
import os

class QuodLibet():
	def __init__(self):
		self.home = os.environ["HOME"]
		bus = dbus.SessionBus()
		obj = bus.get_object("com.google.code.Awn", "/com/google/code/Awn")
		self.awn = dbus.Interface(obj, "com.google.code.Awn")
		
		gobject.idle_add(self.run)
		gtk.main()

	
	def run(self):
		while 1:		
			
			if os.path.exists(self.home + "/.quodlibet/control"): 
				screen = wnck.screen_get_default()
				while gtk.events_pending(): gtk.main_iteration()
				windowlist = screen.get_windows()
				names = []		
				for window in windowlist:
					names.append(window.get_name())
			
				for name in names:				
					found = 0				
					if "Quod Libet" in name:
						self.awn.SetTaskIconByName (name, self.home + "/.quodlibet/cover.png")
						found = 1
				if not found:
					self.awn.SetTaskIconByName ("Quod Libet", self.home + "/.quodlibet/cover.png")	
			
			else:
				self.awn.UnsetTaskIconByName("Quod Libet")
			time.sleep(1)
				
run = QuodLibet()

	
