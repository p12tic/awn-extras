import os
import gtk
import gtk.glade
from gtk import gdk
import time
import subprocess
import awn

class dgClockPref:

  #glade path
  glade_path = os.path.join((os.path.dirname(__file__)), "pref.glade")

  pref_map = {
    'dbt': ('bool', 'dateBeforeTime'),
    'hour12': ('bool', 'hour12'),
    'font_face': ('string', 'fontFace'),
    'font_color': ('color', 'fontColor'),
    'font_shadow_color': ('color', 'fontShadowColor')
    }
  prefs = {}

  def __init__(self, config):
    self.config = config
    for key, details in self.pref_map.iteritems():
      self.config.notify_add(awn.CONFIG_DEFAULT_GROUP, key, self.config_notify, details)
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

  def update_pref(self, key, ptype, pkey):
      if ptype == 'bool':
        value = self.config.get_bool(awn.CONFIG_DEFAULT_GROUP, key)
      else:
        value = self.config.get_string(awn.CONFIG_DEFAULT_GROUP, key)
        if ptype == 'color':
          value = self.parseColors(value)
      self.prefs[pkey] = value

  def config_notify(self, entry, pref):
    self.update_pref(entry['key'], pref[0], pref[1])

  def get_prefs(self):
    for key, details in self.pref_map.iteritems():
      self.update_pref(key, details[0], details[1])

  def show_prefs(self, widget):
    if not hasattr(self, 'wTree'):
      self.wTree = gtk.glade.XML(self.glade_path)
      self.window = self.wTree.get_widget("main_window")

      close = self.wTree.get_widget("close_button")
      close.connect("clicked", self.close_prefs)

      font_btn = self.wTree.get_widget("fontface")
      font_btn.set_font_name(self.prefs['fontFace'])
      font_btn.connect("font-set", self.font_changed, 'font_face')

      color_btn = self.wTree.get_widget("fontcolor")
      color_btn.set_color(self.prefs['fontColor'])
      color_btn.connect("color-set", self.color_changed, 'font_color', self.prefs['fontColor'])

      scolor_btn = self.wTree.get_widget("shadowcolor")
      scolor_btn.set_color(self.prefs['fontShadowColor'])
      scolor_btn.set_use_alpha(False) #Not used yet
      scolor_btn.connect("color-set", self.color_changed, 'font_shadow_color', self.prefs['fontShadowColor'])

      h12 = self.wTree.get_widget("hour12")
      h12.set_active(self.prefs['hour12'])
      h12.connect("toggled", self.set_bool, 'hour12')

      tbd = self.wTree.get_widget("timebesidedate")
      tbd.set_active(self.prefs['dateBeforeTime'])
      tbd.connect("toggled", self.set_bool, 'dbt')

    self.window.show_all()

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

  def close_prefs(self, btn):
    self.window.hide_all()

  def set_bool(self, check, key):
    self.config.set_bool(awn.CONFIG_DEFAULT_GROUP, key, check.get_active())

  def font_changed(self, font_btn, key):
    self.clean_font_name(font_btn.get_font_name())
    self.config.set_string(awn.CONFIG_DEFAULT_GROUP, key, self.prefs['fontFace'])

  def color_changed(self, color_btn, key, var):
    var = color_btn.get_color()
    if color_btn.get_use_alpha():
      alpha = color_btn.get_alpha() #Not used yet
    self.config.set_string(awn.CONFIG_DEFAULT_GROUP, key, '%s,%s,%s' % (var.red, var.green, var.blue))

  def clean_font_name(self, fontface):
    rem = ["Condensed", "Book", "Oblique", "Bold", "Italic", "Regular", "Medium", "Light"]
    for r in rem:
      fontface = fontface.replace(r, '')
      fontface = fontface.rstrip('0123456789 ')
    self.prefs['fontFace'] = fontface

  def parseColors(self, color):
    colors = [int(p) for p in color.split(',')]
    return gtk.gdk.Color(*colors[:3])
