import os
import gtk
import gtk.glade
from gtk import gdk
import gconf
import time
import subprocess

def _to_full_path(path):
    head, tail = os.path.split(__file__)
    return os.path.join(head, path)

class dgClockPref:

  #glade path
  glade_path = _to_full_path("pref.glade")

  #gconf path
  gconf_path        = "/apps/avant-window-navigator/applets/digitalClock"
  font_face_path    = os.path.join(gconf_path, 'font_face')
  font_color_path   = os.path.join(gconf_path, 'font_color')
  shadow_color_path = os.path.join(gconf_path, 'font_shadow_color')
  hour12_path       = os.path.join(gconf_path, 'hour12')
  date_b4_time_path = os.path.join(gconf_path, 'dbt')
  prefs             = {}

  def __init__(self):
    self.gconf_client = gconf.client_get_default()
    #self.gconf_client.notify_add(self.gconf_path, self.gconf_event)
    self.menu = self.buildMenu()
    self.get_prefs()

  def buildMenu(self):
    popup_menu = gtk.Menu()
    hbox = gtk.HBox(False,2)
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_PREFERENCES, gtk.ICON_SIZE_MENU)
    hbox.pack_start(img, expand=False, fill=False, padding=0)
    lbl = gtk.Label("Preferences")
    hbox.pack_start(lbl, expand=False, fill=False, padding=0)
    pref = gtk.MenuItem()
    pref.add(hbox)

    hbox = gtk.HBox(False,2)
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_EDIT, gtk.ICON_SIZE_MENU)
    hbox.pack_start(img, expand=False, fill=False, padding=0)
    hbox.pack_start(gtk.Label("Adjust Date & Time"))
    timead = gtk.MenuItem()
    timead.add(hbox)

    hbox = gtk.HBox(False,2)
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)
    hbox.pack_start(img, expand=False, fill=False, padding=0)
    lbl = gtk.Label("Copy Time")
    hbox.pack_start(lbl, expand=False, fill=False, padding=0)
    ctime = gtk.MenuItem()
    ctime.add(hbox)

    hbox = gtk.HBox(False,2)
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_COPY, gtk.ICON_SIZE_MENU)
    hbox.pack_start(img, expand=False, fill=False, padding=0)
    lbl = gtk.Label("Copy Date")
    hbox.pack_start(lbl, expand=False, fill=False, padding=0)
    cdate = gtk.MenuItem()
    cdate.add(hbox)

    popup_menu.append(ctime)
    popup_menu.append(cdate)
    popup_menu.append(pref)
    popup_menu.append(timead)

    pref.connect_object("activate",self.show_prefs, self)
    timead.connect_object("activate",self.time_admin, self)
    ctime.connect_object("activate",self.copy_time, self)
    cdate.connect_object("activate",self.copy_date, self)
    popup_menu.show_all()
    return popup_menu

  def get_prefs(self):
    try:
      self.gconf_client.get_value(self.date_b4_time_path)
      self.prefs['dateBeforeTime'] = self.gconf_client.get_bool(self.date_b4_time_path)
    except ValueError:
      self.gconf_client.set_bool(self.date_b4_time_path, False)
      self.prefs['dateBeforeTime'] = True

    try:
      self.gconf_client.get_value(self.hour12_path)
      self.prefs['hour12'] = self.gconf_client.get_bool(self.hour12_path)
    except ValueError:
      self.gconf_client.set_bool(self.hour12_path, True)
      self.prefs['hour12'] = True

    self.prefs['fontFace'] = self.gconf_client.get_string(self.font_face_path)
    if(self.prefs['fontFace'] == None):
      self.gconf_client.set_string(self.font_face_path, "Sans 10")
      self.prefs['fontFace'] = "Sans 10"
      self.clean_font_name(self.prefs['fontFace'])

    self.prefs['fontColor'] = self.gconf_client.get_string(self.font_color_path)
    if(self.prefs['fontColor'] == None or self.prefs['fontColor'] == ""):
      self.gconf_client.set_string(self.font_color_path, "255,255,255")
      self.prefs['fontColor'] = self.parseColors("255,255,255")
    else:
      self.prefs['fontColor'] = self.parseColors(self.prefs['fontColor'])

    self.prefs['fontShadowColor'] = self.gconf_client.get_string(self.shadow_color_path)
    if(self.prefs['fontShadowColor'] == None or self.prefs['fontShadowColor'] == ""):
      self.gconf_client.set_string(self.shadow_color_path, "0,0,0")
      self.prefs['fontShadowColor'] = self.parseColors("0,0,0")
    else:
      self.prefs['fontShadowColor'] = self.parseColors(self.prefs['fontShadowColor'])

  def show_prefs(self, widget):
    self.wTree = gtk.glade.XML(self.glade_path)
    window = self.wTree.get_widget("main_window")

    close = self.wTree.get_widget("close_button")
    close.connect("clicked", self.close_prefs, window)

    font_btn = self.wTree.get_widget("fontface")
    font_btn.set_font_name(self.prefs['fontFace'])
    font_btn.connect("font-set", self.font_changed, self.font_face_path)

    color_btn = self.wTree.get_widget("fontcolor")
    c = self.parseColors(self.gconf_client.get_string(self.font_color_path))
    color_btn.set_color(c)
    color_btn.connect("color-set", self.color_changed, self.font_color_path, self.prefs['fontColor'])

    scolor_btn = self.wTree.get_widget("shadowcolor")
    c = self.parseColors(self.gconf_client.get_string(self.shadow_color_path))
    scolor_btn.set_color(c)
    scolor_btn.set_use_alpha(False) #Not used yet
    scolor_btn.connect("color-set", self.color_changed, self.shadow_color_path, self.prefs['fontShadowColor'])

    h12 = self.wTree.get_widget("hour12")
    h12.set_active(self.prefs['hour12'])
    h12.connect("toggled", self.set_bool, self.hour12_path)

    tbd = self.wTree.get_widget("timebesidedate")
    tbd.set_active(self.prefs['dateBeforeTime'])
    tbd.connect("toggled", self.set_bool, self.date_b4_time_path)

    window.show_all()

  def copy_date(self, widget):
    cb = gtk.Clipboard()
    txt = time.strftime("%A, %B %d, %Y")
    cb.set_text(txt)

  def copy_time(self, widget):
    cb = gtk.Clipboard()
    if self.prefs['hour12']:
      h = time.strftime("%I").lstrip('0')
      txt = h + time.strftime(":%M:%S %p")
    else:
      txt = time.strftime("%H:%M:%S")
    cb.set_text(txt)

  def time_admin(self, widget):
    subprocess.Popen('gksudo time-admin', shell=True)

  def close_prefs(self, btn, win):
    win.destroy()

  def set_bool(self, check, key):
    self.gconf_client.set_bool(key, check.get_active())

  def font_changed(self, font_btn, key):
    self.clean_font_name(font_btn.get_font_name())
    self.gconf_client.set_string(key, self.prefs['fontFace'])

  def color_changed(self, color_btn, key, var):
    var = color_btn.get_color()
    if color_btn.get_use_alpha():
      alpha = color_btn.get_alpha() #Not used yet
    self.gconf_client.set_string(key, "%s,%s,%s" % (var.red, var.green, var.blue))

  def clean_font_name(self, fontface):
    rem = ["Condensed", "Book", "Oblique", "Bold", "Italic", "Regular", "Medium", "Light"]
    for r in rem:
      fontface = fontface.replace(r, '')
      fontface = fontface.rstrip('0123456789 ')
    self.prefs['fontFace'] = fontface

  def parseColors(self,color):
    colors = color.split(',')
    c = gtk.gdk.Color(int(colors[0]), int(colors[1]), int(colors[2]))
    return c
