#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2009 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
# File Browser Launcher
# Main Applet File

import sys
import os
import pygtk
pygtk.require('2.0')
import gtk
import subprocess
import pango
import urllib

try:
  import gio

except:
  gio = False

import awn
from awn.extras import _

group = awn.CONFIG_DEFAULT_GROUP

class App (awn.AppletSimple):
  icons = {}
  def __init__(self, uid, panel_id):
    self.uid = uid

    #AWN Applet Configuration
    awn.AppletSimple.__init__(self, 'file-browser-launcher', uid, panel_id)
    self.set_tooltip_text(_("File Browser Launcher"))
    self.dialog = awn.Dialog(self)

    #AwnConfigClient instance
    self.client = awn.Config('file-browser-launcher', None)

    #Get the default icon theme
    self.theme = gtk.icon_theme_get_default()
    self.icons['stock_folder'] = self.theme.load_icon('stock_folder', 24, 24)

    #Set the icon
    self.set_icon_name('stock_folder')
    self.icon = self.get_icon().get_icon_at_size(48, None)

    if not gio:
      #Read fstab for mounting info
      #(It it assumed that fstab won't change after the applet is started)
      self.fstab2 = open('/etc/fstab', 'r')
      self.fstab = self.fstab2.read().split('\n')
      self.fstab2.close()

    #Check if nautilus-connect-server is installed
    if os.path.exists('/usr/bin/nautilus-connect-server') or os.path.exists\
      ('/usr/local/bin/nautilus-connect-server'):
      self.nautilus_connect_server = True
    else:
      self.nautilus_connect_server = False

    #Make the dialog, will only be shown when approiate
    #Make all the things needed for a treeview for the homefolder, root dir, bookmarks, and mounted drives
    self.liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, gtk.gdk.Pixbuf, str, int)

    #Renderers
    renderer0 = gtk.CellRendererPixbuf()
    renderer1 = gtk.CellRendererText()
    self.eject_render = gtk.CellRendererPixbuf()
    self.eject_render.set_property("mode", gtk.CELL_RENDERER_MODE_ACTIVATABLE)

    #Add renderers to column
    column = gtk.TreeViewColumn('0')
    column.pack_start(renderer0, False)
    column.add_attribute(renderer0, 'pixbuf', 0)
    column.pack_start(renderer1, True)
    column.add_attribute(renderer1, 'markup', 1)
    column.pack_start(self.eject_render, False)
    column.add_attribute(self.eject_render, 'pixbuf', 2)

    #TreeView
    self.treeview = gtk.TreeView(self.liststore)
    self.treeview.set_hover_selection(True)
    self.treeview.set_headers_visible(False)
    self.treeview.append_column(column)
    self.treeview.connect('button-press-event', self.treeview_clicked)

    self.vbox = gtk.VBox()
    self.vbox.pack_start(self.treeview)

    if gio:
      self.monitor = gio.volume_monitor_get()
      self.monitor.connect('volume-added', self.do_gio_places)
      self.monitor.connect('volume-changed', self.do_gio_places)
      self.monitor.connect('volume-removed', self.do_gio_places)
      self.monitor.connect('mount-added', self.do_gio_places)
      self.monitor.connect('mount-changed', self.do_gio_places)
      self.monitor.connect('mount-removed', self.do_gio_places)

      self.client.notify_add(group, 'show_home', self.do_gio_places)
      self.client.notify_add(group, 'show_local', self.do_gio_places)
      self.client.notify_add(group, 'show_network', self.do_gio_places)
      self.client.notify_add(group, 'show_connect', self.do_gio_places)
      self.client.notify_add(group, 'show_bookmarks', self.do_gio_places)
      self.client.notify_add(group, 'show_filesystem', self.do_gio_places)

      self.do_gio_places()

      #(From YAMA by Onox)
      #Monitor bookmarks file for changes
      bookmarks_file = os.path.expanduser("~/.gtk-bookmarks")

      #keep a reference to avoid getting it garbage collected
      self.__bookmarks_monitor = gio.File(bookmarks_file).monitor_file()

      def bookmarks_changed_cb(monitor, file, other_file, event):
        if event == gio.FILE_MONITOR_EVENT_CHANGES_DONE_HINT:
          #Refresh menu to re-initialize the widget
          self.do_gio_places()

      self.__bookmarks_monitor.connect("changed", bookmarks_changed_cb)

    #Entry widget for displaying the path to open
    self.entry = gtk.Entry()
    self.entry.set_text(os.environ['HOME'])
    self.entry.connect('key-release-event', self.detect_enter)
    #Open button to run the file browser
    self.enter = gtk.Button(stock=gtk.STOCK_OPEN)
    self.enter.connect('clicked', self.launch_fb)
    #HBox to put the two together
    self.hbox = gtk.HBox()
    self.hbox.pack_start(self.entry)
    self.hbox.pack_start(self.enter, False)
    #And add the HBox to the vbox and add the vbox to the dialog
    self.vbox.pack_end(self.hbox)
    self.dialog.add(self.vbox)

    #Connect to signals
    self.connect('button-press-event', self.button_press)
    self.dialog.connect('focus-out-event', lambda a,b: self.dialog.hide())
    self.theme.connect('changed', self.icon_theme_changed)

  #Certain places, regardless of GIO/not GIO
  def do_places(self):
    self.liststore.clear()
    self.places_paths = []

    #Get the needed config values
    self.show_home = self.client.get_int(group, 'show_home')
    self.show_local = self.client.get_int(group, 'show_local')
    self.show_network = self.client.get_int(group, 'show_network')
    self.show_connect = self.client.get_int(group, 'show_connect')
    self.show_bookmarks = self.client.get_int(group, 'show_bookmarks')
    self.show_filesystem = self.client.get_int(group, 'show_filesystem')

    #Home folder
    if self.show_home == 2:
      self.place('user-home', _("Home Folder"), os.environ['HOME'])

    #Filesystem
    if self.show_filesystem == 2:
      self.place('drive-harddisk', _("Filesystem"), '/')

  def do_gio_places(self, *args):
    i = 0

    self.do_places()

    if self.show_local == 2:
      for vol in self.monitor.get_volumes():
        #Get the icon
        icon = vol.get_icon()
        eject = None

        if type(icon) == gio.ThemedIcon:
          icons = icon.get_names()

        else:
          icons = ('drive-harddisk', 'drive')

        #Get the human-readable name
        name = vol.get_name()

        #Get the path
        if vol.get_mount():
          path = vol.get_mount().get_root().get_uri()
          icons = vol.get_mount().get_icon().get_names()

          #Get the eject icon if this volume can be unmounted
          if vol.get_mount().can_unmount():
            eject = self.load_pixbuf(('media-eject', ))

        else:
          path = 'mount://%s' % i

        icon = self.load_pixbuf(icons)

        self.liststore.append((icon, name, eject, path, i))

        i += 1

    if self.show_network == 2:
      for mount in self.monitor.get_mounts():
        if mount.get_volume() is None:
          #Get the icon
          icon = mount.get_icon()

          if type(icon) == gio.ThemedIcon:
            icons = icon.get_names()

          else:
            icons = ('applications-internet', )

          #Human-readable name
          name = mount.get_name()

          #Path
          path = mount.get_root().get_uri()

          #Load the icon
          icon = self.load_pixbuf(icons)

          #Eject icon
          eject = None
          if mount.can_unmount():
            eject = self.load_pixbuf(('media-eject', ))

          self.liststore.append((icon, name, path, i))

          i += 1

    self.do_ncs()
    self.do_bookmarks()

  #A volume was mounted through file-browser-launcher; open the file manager to the path
  def gio_mounted(self, vol, blah):
    self.launch_fb(None, vol.get_mount().get_root().get_uri())

  #If nautilus-connect-server is installed, offer to start it "Connect to server..."
  def do_ncs(self):
    if self.nautilus_connect_server and self.show_connect == 2:
      self.place('applications-internet', _("Connect to Server..."),
        'exec://nautilus-connect-server')

  #Go through the list of bookmarks and add them to the list IF it's not in the mount list
  def do_bookmarks(self):
    if self.show_bookmarks == 2:
      #Get list of bookmarks
      self.bmarks2 = open(os.path.expanduser('~/.gtk-bookmarks'))
      self.bmarks = self.bmarks2.readlines()
      self.bmarks2.close()

      if gio:
        self.paths = []

      for path in self.bmarks:
        path = path.replace('file://', '').replace('\n', '')
        path = urllib.unquote(path)

        #Get the human-readable name
        try:
          name = ' '.join(path.split(' ')[1:])
          assert name.replace(' ', '') != ''
        except:
          name = None

        path = path.split(' ')[0]
        type = path.split(':')[0]

        #Check if this path hasn't been used already
        if path not in self.paths and path != os.environ['HOME']:

          #Check if this is a path on the filesystem
          if path[0] == '/':
            if os.path.isdir(path):

              #If the user did not rename the bookmark - get the name from
              #the folder name (/media/Lexar -> Lexar)
              if name is None:
                try: name = path.split('/')[-1]
                except: name = path

              #Check if this is the Desktop directory
              if (path == os.path.expanduser(_("~/Desktop"))):
                self.place('desktop', name, path)

              #It's not
              else:
                self.place('folder', name, path)

          #computer://, trash://, network fs, etc.
          else:
            if type == 'computer':
              self.place('computer', name, path, _("Computer"))

            elif type in ['network', 'smb', 'nfs', 'ftp', 'sftp', 'ssh']:
              self.place('network-folder', name, path, _("Network"))

            elif type == 'trash':
              #Get whether the trash is empty or not - but first find out if the Trash is in
              #~/.Trash or ~/.local/share/Trash
              try:
                #Get trash dir
                if os.path.isdir(os.path.expanduser('~/.local/share/Trash/files')):
                  self.trash_path = os.path.expanduser('~/.local/share/Trash/files')
                else:
                  self.trash_path = os.path.expanduser('~/.Trash')
                
                #Get number of items in trash
                if len(os.listdir(self.trash_path)) > 0:
                  self.trash_full = True
                else:
                  self.trash_full = False
              
              except:
                #Maybe the trash is in a different location? Just put false
                self.trash_full = False

              if self.trash_full:
                self.place('user-trash-full', name, path, _("Trash"))

              else:
                self.place('user-trash', name, path, _("Trash"))

            elif type == 'x-nautilus-search':
              self.place('search', name, path, _("Search"))

            elif type == 'burn':
              self.place('drive-optical', name, path, _("CD/DVD Burner"))

            elif type == 'fonts':
              self.place('font', name, path, _("Fonts"))

            #Default to folder
            else:
              self.place('stock_folder', name, path, _("Folder"))

  #Function to show the home folder, mounted drives/partitions, and bookmarks according to awncc
  #This also refreshes in case a CD was inserted, MP3 player unplugged, bookmark added, etc.
  #Note: this function is not called if Python bindings for GIO are installed
  def add_places(self):
    #This function adds items to the liststore. The TreeView was already made in __init__()
    
    self.do_places()

    #Check to see if we should check /etc/fstab and $mount
    self.do_mounted = False
    if 2 in [self.show_local, self.show_network]:
      self.do_mounted = True

    #Define some variables
    self.paths = []
    self.paths_fstab = []
    self.network_paths = []
    self.network_corr_hnames = []
    self.cd_paths = []
    self.dvd_paths = []

    #Get list of mounted drives from $mount and /etc/fstab
    if self.do_mounted:
      self.mount2 = os.popen('mount')
      self.mount = self.mount2.readlines()
      self.mount2.close()

    #Set list of paths, regardless of location
    hnames = {}

    #Get the mounted drives/partitions that are suitable to list (from fstab)
    if self.do_mounted:
      for line in self.fstab:
        try:
          if line.replace(' ','').replace('\t','') != '' and line[0] != "#":

            words = line.split(' ')
            for word in words[1:]:
              if word != '':
                if word[0] == '/':
                  if word != '/proc':
                    self.paths_fstab.append(word)

            words = line.replace('  ',' ').split(' ')

            #From this point on I'm not exactly sure what's going on
            z2 = []
            for z3 in z:
              z2.extend(z3.split('\t'))

            if z2[2] == 'smbfs':
              self.network_paths.append('smb:'+z2[0])
              self.network_corr_hnames.append(z2[0].split(':')[-1].split('/')[-1]+\
                ' on '+z2[0].split('/')[2])

            elif z2[2] in ['cifs','nfs','ftpfs','sshfs']:
              self.network_paths.append(z2[1])
              self.network_corr_hnames.append(z2[0].split(':')[-1].split('/')[-1]+\
                ' on '+z2[0].split('/')[2])

        except:
          #Maybe a syntax error or something in this line of fstab?
          #Just ignore it (better than not working at all (thanks Kinap/Felix)
          pass
      
      #Get the mounted drives/partitions that are suitable to list (from mount)
      for line in self.mount:
        words = line.split(' ')

        #Check if this line doesn't begin with '/'
        if words[0].find('/') != -1:
          #Make sure this is a device (hard drive, disk drive, etc.)
          if words[0].split('/')[1] == 'dev':
            #Get the filesystem location
            path = line.split(' on ')[1].split(' type ')[0]
            self.paths.append(path)

            #Try to get the human-readable name
            if line[-1] == ']':
              hnames[path] = line.split('[')[-1][:-1]
            else:
              hnames[path] = path.split('/')[-1]

            #Check for CD drive
            if line.split(' type ')[1].split(' ')[0] == 'iso9660':
              self.cd_paths.append(path)

            #Check for DVD drive
            elif line.split(' type ')[1].split(' ')[0] == 'udf':
              self.dvd_paths.append(path)

    #Go through the list and get the right icon and name for specific ones
    #ie/eg: / -> harddisk icon and "Filesystem"
    #/media/Lexar -> usb-disk icon and "Lexar"
    if self.show_local == 2:
      for path in self.paths:
        if path == '/':
          pass

        elif path.split('/')[1] == 'media':
          if path.split('/')[2] in ['cdrom0','cdrom1','cdrom2','cdrom3','cdrom4','cdrom5']:
            
            #Find out if it's a CD or DVD
            if path in self.dvd_paths:
              self.place('media-optical', _("DVD Drive"), path)

            #CD Drive
            else:
              self.place('media-optical', _("CD Drive"), path)

          #Flash drive, etc.
          elif path not in self.paths_fstab:
            self.place('gnome-dev-harddisk-usb', hnames[path], path)

          #Local mounted drive (separate disk/partition)
          else:
            self.place('drive-harddisk', hnames[path], path)

        #Partition not mounted in /media (such as /home)
        else:
          self.place('drive-harddisk', hnames[path], path)
    
    #Go through the list of network drives/etc. from /etc/fstab
    if self.show_network == 2:
      #GVFS stuff
      gvfs_dir = os.path.expanduser('~/.gvfs')
      if os.path.isdir(gvfs_dir):
        for path in os.listdir(gvfs_dir):
          self.place('network-folder', path, gvfs_dir + '/' + path)

      #Non-GVFS stuff
      y = 0
      for path in self.network_paths:
        self.place('network-folder', self.network_corr_hnames[y], path)
        y+=1

    #Get a single list of all the paths so far
    self.paths.extend(self.network_paths)
    self.paths.extend(self.places_paths)
    self.paths.extend(self.cd_paths)
    self.paths.extend(self.dvd_paths)

    self.do_ncs()

    self.do_bookmarks()

  def load_pixbuf(self, names):
    if type(names) == str:
      names = (names, )

    worked = False
    for name in names:
      #Load the icon if it hasn't been yet
      if not self.icons.has_key(name):
        try:
          icon = self.theme.load_icon(name, 24, 0)
          worked = True
          break

        except:
          pass

      #Icon has already been loaded
      else:
        worked = True
        icon = self.icons[name]
        break

    #If no icon does exists - load default folder icon
    if not worked:
      icon = self.icons['stock_folder']
      self.icons[name] = icon

    else:
      self.icons[name] = icon

    return icon

  def place(self, icon_names, human_name, path, alt_name=None):
    icon = self.load_pixbuf(icon_names)
    self.liststore.append([icon, [human_name, alt_name][human_name is None], None, path, -1])

  def ejected_or_unmounted(self, *a):
    pass

  #Function to do what should be done according to awncc when the treeview is clicked
  def treeview_clicked(self, widget, event):
    self.open_clicked = self.client.get_int(group, 'places_open')
    self.selection = self.treeview.get_selection()

    if gio:
      #Get some data
      path, column = widget.get_path_at_pos(int(event.x), int(event.y))[0:2]
      posx, posy = column.cell_get_position(self.eject_render)

      #Check if the eject column was clicked
      if posx + 24 > event.x and posx <= event.x:
        #Check if this is a volume or a mount
        num = self.liststore[path][4]
        if num != -1:
          li = self.monitor.get_volumes()
          li.extend(self.monitor.get_mounts())

          #If it's a volume
          if isinstance(li[num], gio.Volume):
            if li[num].get_mount():
              #If the volume can eject
              if li[num].get_mount().can_eject():
                li[num].get_mount().eject(self.ejected_or_unmounted)
                return False

              #If the volume can unmount
              if li[num].get_mount().can_unmount():
                li[num].get_mount().unmount(self.ejected_or_unmounted)
                return False

          #It's a mount
          else:
            #If the mount can eject
            if li[num].can_eject():
              li[num].eject(self.ejected_or_unmounted)
              return False

            #If the mount can unmount
            elif li[num].can_unmount():
              li[num].unmount(self.ejected_or_unmounted)
              return False

          #Otherwise, just open it

    if self.open_clicked == 2:
      self.dialog.hide()
      self.launch_fb(None, self.liststore[self.selection.get_selected()[1]][3])

    else:
      self.entry.set_text(self.liststore[self.selection.get_selected()[1]][3])
      self.entry.grab_focus()
  
  #Applet show/hide methods - copied from MiMenu (and edited)
  #When a button is pressed
  def button_press(self, widget, event):
    if event.button in (1, 2):
      if self.dialog.flags() & gtk.VISIBLE:
        self.dialog.hide()

      else:
        self.dialog_config(event.button)

    elif event.button == 3:
      self.dialog.hide()
      self.show_menu(event)

  #The user changed the icon theme
  def icon_theme_changed(self, icon_theme):
    for key in self.icons.keys():
      del self.icons[key]

    if gio:
      self.do_gio_places()

    #Reload the stock folder icon
    self.icons['stock_folder'] = self.theme.load_icon('stock_folder', 24, 24)

  #dialog_config: 
  def dialog_config(self, button):
    if button != 1 and button != 2:
      return False
    self.curr_button = button
    
    #Get whether to focus the entry when displaying the dialog or not
    self.awncc_focus = self.client.get_int(group, 'focus_entry')
    
    if button == 1: #Left mouse button
    #Get the value for the left mouse button to automatically open.
    #Create and default to 1 the entry if it doesn't exist
    #Also get the default directory or default to ~
      self.awncc_lmb = self.client.get_int(group, 'lmb')
      self.awncc_lmb_path = self.client.get_string(group, 'lmb_path')
      self.awncc_lmb_path = os.path.expanduser(self.awncc_lmb_path)
    
    elif button == 2: #Middle mouse button
    #Get the value for the middle mouse button to automatically open.
    #Create and default to 2 the entry if it doesn't exist
    #Also get the default directory or default to ~
      self.awncc_mmb = self.client.get_int(group, 'mmb')
      self.awncc_mmb_path = self.client.get_string(group, 'mmb_path')
      self.awncc_mmb_path = os.path.expanduser(self.awncc_mmb_path)
    
    #Left mouse button - either popup with correct path or launch correct path OR do nothing
    if button == 1:
      if self.awncc_lmb == 1:
        self.entry.set_text(self.awncc_lmb_path)

        if not gio:
          self.add_places()

        if self.awncc_focus == 2:
          self.entry.grab_focus()
          self.entry.set_position(-1)

        self.dialog.show_all()

      elif self.awncc_lmb == 2:
        self.launch_fb(None,self.awncc_lmb_path)
    
    #Right mouse button - either popup with correct path or launch correct path OR do nothing
    if button == 2:
      if self.awncc_mmb == 1:
        self.entry.set_text(self.awncc_mmb_path)

        if not gio:
          self.add_places()

        if self.awncc_focus == 2:
          self.entry.grab_focus()
          self.entry.set_position(-1)

        self.dialog.show_all()

      elif self.awncc_mmb == 2:
        self.launch_fb(None, self.awncc_mmb_path)
  
  #If the user hits the enter key on the main part OR the number pad
  def detect_enter(self, a, event):
    if event.keyval == 65293 or event.keyval == 65421:
      self.enter.clicked()
  
  #Launces file browser to open "path". If "path" is None: use value from the entry widget
  def launch_fb(self, widget, path=None):
    self.dialog.hide()
    if path == None:
      path = self.entry.get_text()

    #Get the file browser app, or set to xdg-open if it's not set
    self.awncc_fb = self.client.get_string(group, 'fb')

    #In case there is nothing but whitespace (or at all) in the entry widget
    if path.replace(' ','') == '':
      path = os.environ['HOME']

    #Check if we're supposed to open nautilus-connect-server
    if path.split(':')[0] == 'exec':
      os.system('%s &' % path.split('://')[-1])

    #Or mount a specified location
    elif path.split(':')[0] == 'mount':
      mo = gio.MountOperation()
      num = int(path.split('://')[-1])
      self.monitor.get_volumes()[num].mount(mo, self.gio_mounted)

    #Otherwise, open the file/directory
    else:
      os.system('%s %s &' % (self.awncc_fb, path.replace(' ', '\ ')))
  
  #Right click menu - Preferences or About
  def show_menu(self,event):
    #Hide the dialog if it's shown
    self.dialog.hide()

    #Create the items for Preferences and About
    self.prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
    self.about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)

    #Connect the two items to functions when clicked
    self.prefs.connect("activate", self.open_prefs)
    self.about.connect("activate", self.open_about)

    #Now create the menu to put the items in and show it
    self.menu = self.create_default_menu()
    self.menu.append(self.prefs)
    self.menu.append(self.about)
    self.menu.show_all()
    self.menu.popup(None, None, None, event.button, event.time)

  #Show the preferences window
  def open_prefs(self,widget):
    #Import the prefs file from the same directory
    import prefs
    
    #Show the prefs window - see prefs.py
    prefs.Prefs(self)
    gtk.main()

  #Show the about window
  def open_about(self,widget):
    #Import the about file from the same directory
    import about
    
    #Show the about window - see about.py
    about.About()

if __name__ == '__main__':
  awn.init(sys.argv[1:])
  applet = App(awn.uid, awn.panel_id)
  awn.embed_applet(applet)
  applet.show_all()
  gtk.main()
