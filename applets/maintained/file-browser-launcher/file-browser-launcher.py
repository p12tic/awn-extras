#! /usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, 2010 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
import gobject
import subprocess
import pango
import urllib
import gettext

from desktopagnostic.config import GROUP_DEFAULT as group
from desktopagnostic import vfs
import awn
from awn.extras import _
gettext.bindtextdomain('xdg-user-dirs', '/usr/share/locale')

try:
  import gio
except:
  gio = False


class App(awn.Applet):
  icons = {}
  timer = None
  num_times = 0
  drag_done = True
  droppable_places = []
  places_data = []
  docklet_visible = False

  def __init__(self, uid, panel_id):
    #AWN Applet Configuration
    awn.Applet.__init__(self, 'file-browser-launcher', uid, panel_id)

    self.icon_box = awn.IconBox(self)
    self.add(self.icon_box)
    self.icon = awn.ThemedIcon()
    self.icon.set_tooltip_text(_("File Browser Launcher"))
    self.icon.set_size(self.get_size())
    self.dialog = awn.Dialog(self.icon, self)

    #AwnConfigClient instance
    self.client = awn.config_get_default_for_applet(self)

    #Get the default icon theme
    self.theme = gtk.icon_theme_get_default()
    self.icons[24] = {}
    self.icons[24]['folder'] = self.theme.load_icon('folder', 24, 0)

    #Docklet...
    self.mode = self.client.get_int(group, 'mode')
    self.client.notify_add(group, 'mode', self.update_mode)

    if self.mode == 2:
      self.docklet_visible = True
      self.update_docklet(False)

    else:
      self.icon_box.add(self.icon)

    #Set the icon
    self.icon.set_info_simple('file-browser-launcher', uid, 'folder')

    if gio:
      #This part (and other progress overlay code) adapted from
      #mhr3's 'Dropper' applet
      #Set the progress overlay
      self.timer_overlay = awn.OverlayProgressCircle()
      self.timer_overlay.props.active = False
      self.timer_overlay.props.apply_effects = False
      self.icon.add_overlay(self.timer_overlay)
    else:
      #Read fstab for mounting info
      #(It it assumed that fstab won't change after the applet is started)
      self.fstab2 = open('/etc/fstab', 'r')
      self.fstab = self.fstab2.read().split('\n')
      self.fstab2.close()

    #Check if nautilus-connect-server is installed
    if os.path.exists('/usr/bin/nautilus-connect-server') or os.path.exists \
      ('/usr/local/bin/nautilus-connect-server'):
      self.nautilus_connect_server = True
    else:
      self.nautilus_connect_server = False

    if os.path.exists('/usr/share/applications/nautilus-computer.desktop') or \
      os.path.exists('/usr/local/share/applications/nautilus-computer.desktop'):
      self.nautilus_computer = True
    else:
      self.nautilus_computer = False

    def trash_count_cb(*args):
      if self.show_trash:
        if gio:
          self.do_gio_places()
        else:
          self.add_places()

    self.trash = vfs.Trash.get_default()
    self.trash.connect('file-count-changed', trash_count_cb)

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
    self.treeview.set_no_show_all(True)
    self.treeview.connect('button-press-event', self.treeview_clicked)

    self.vbox = gtk.VBox()
    self.vbox.pack_start(self.treeview)

    if gio:
      self.monitor = gio.volume_monitor_get()
      for signal in ('volume-added', 'volume-changed', 'volume-removed', 'mount-added',
        'mount-changed', 'mount-removed'):
        self.monitor.connect(signal, self.do_gio_places)

      for key in ('show_computer', 'show_home', 'show_filesystem', 'show_local', 'show_network',
        'show_connect', 'show_trash', 'show_bookmarks'):
        self.client.notify_add(group, key, self.do_gio_places)

      self.do_gio_places()

      #(From YAMA by Onox)
      #Monitor bookmarks file for changes
      bookmarks_file = os.path.expanduser("~/.gtk-bookmarks")

      #keep a reference to avoid getting it garbage collected
      self.__bookmarks_monitor = gio.File(bookmarks_file).monitor_file()

      def bookmarks_changed_cb(monitor, file, other_file, event):
        if event in (gio.FILE_MONITOR_EVENT_CHANGES_DONE_HINT, gio.FILE_MONITOR_EVENT_CREATED,
          gio.FILE_MONITOR_EVENT_DELETED):
          #Refresh menu to re-initialize the widget
          self.do_gio_places()

      self.__bookmarks_monitor.connect("changed", bookmarks_changed_cb)

    #Entry widget for displaying the path to open
    self.entry = gtk.Entry()
    self.entry.set_text(os.environ['HOME'])
    self.entry.connect('key-release-event', self.detect_enter)
    self.entry.show()

    #Open button to run the file browser
    self.enter = gtk.Button(stock=gtk.STOCK_OPEN)
    self.enter.connect('clicked', self.launch_fb)
    self.enter.show()

    #HBox to put the two together
    entry_hbox = gtk.HBox()
    entry_hbox.pack_start(self.entry)
    entry_hbox.pack_start(self.enter, False)

    #And add the HBox to the vbox and add the vbox to the dialog
    self.vbox.pack_end(entry_hbox)
    self.dialog.add(self.vbox)

    #Connect to signals
    self.icon.connect('clicked', self.icon_clicked)
    self.icon.connect('middle-clicked', self.icon_clicked)
    self.icon.connect('context-menu-popup', self.show_context_menu)
    self.connect('size-changed', self.size_changed)
    self.dialog.connect('focus-out-event', self.dialog_focus_out)
    self.theme.connect('changed', self.icon_theme_changed)

    if gio:
      #Allow the user to drag&drop a file/folder onto the applet. After
      #a short delay, show the dialog, and allow the file/folder to be dropped
      #on any place in the TreeView (other than root, Connect to Server..., and
      #maybe unmounted places). The move the file/folder and (if successful)
      #open the place in the file browser
      #The Applet icon - just open the dialog after a short delay
      self.icon.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
        [("text/uri-list", 0, 0)], \
        gtk.gdk.ACTION_COPY)
      self.icon.connect('drag-data-received', self.applet_drag_data_received)
      self.icon.connect('drag-motion', self.applet_drag_motion)
      self.icon.connect('drag-leave', self.applet_drag_leave)

      #The TreeView - drop the file to move it to the folder
      self.treeview.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
        [("text/uri-list", 0, 0)], \
        gtk.gdk.ACTION_MOVE)
      self.treeview.connect('drag-data-received', self.treeview_drag_data_received)
      self.treeview.connect('drag-motion', self.treeview_drag_motion)
      self.treeview.connect('drag-leave', self.treeview_drag_leave)

    elif self.mode == 2:
      self.add_places()

  def size_changed(self, *args):
    if self.docklet_visible:
      self.update_docklet()

    self.icon.set_size(self.get_size())

  #Applet drag and drop
  def applet_drag_data_received(self, w, context, x, y, data, info, time):
    context.finish(True, False, time)

    self.drag_done = True
    self.num_times = 0
    self.timer = None
    self.dialog.hide()

    return True

  def applet_drag_motion(self, widget, context, x, y, time):
    if not self.timer and not self.dialog.flags() & gtk.VISIBLE:
      self.timer_overlay.props.active = True

      self.timer = gobject.timeout_add(30, self.update_timer)

    if self.client.get_int(group, 'mode') == 0:
      if not self.dialog.flags() & gtk.VISIBLE:
        self.icon.get_effects().start(awn.EFFECT_LAUNCHING)

  def applet_drag_leave(self, widget, context, time):
    self.icon.get_effects().stop(awn.EFFECT_LAUNCHING)

    if self.timer:
      gobject.source_remove(self.timer)

    self.timer = None
    self.drag_done = True
    self.num_times = 0

    self.timer_overlay.props.active = False
    self.timer_overlay.props.percent_complete = 0

  def update_timer(self):
    self.num_times += 1

    if self.num_times <= 20:
      self.timer_overlay.props.percent_complete = self.num_times * 100 / 20

      self.timer = gobject.timeout_add(30, self.update_timer)

    else:
      self.timer = None
      self.num_times = 0
      self.timer_overlay.props.active = False
      self.timer_overlay.props.percent_complete = 0

      self.icon.get_effects().stop(awn.EFFECT_LAUNCHING)

      self.dialog_config(1)

    return False

  #TreeView drag and drop
  def treeview_drag_data_received(self, treeview, context, x, y, data, info, time):
    self.drag_done = True
    context.finish(True, False, time)

    treepath, column = treeview.get_path_at_pos(x, y)[0:2]
    selection = self.treeview.get_selection()

    path = self.liststore[treepath][3]

    if path in self.droppable_places:
      dropped_paths = data.data.split('\n')
      num_success = 0

      if path == 'trash:///':
        for dropped_path in dropped_paths:
          from_file = vfs.File.for_uri(urllib.unquote(dropped_path).strip())
          try:
            self.trash.send_to_trash(from_file)
          except:
            pass

      else:
        for dropped_path in dropped_paths:
          if len(dropped_path) >= 8:
            if dropped_path[:8] == 'file:///':
              dropped_path = dropped_path.strip()

              dropped_path = urllib.unquote(dropped_path)

              from_file = gio.File(dropped_path)

              to_file = gio.File(path + '/' + from_file.get_basename())

              #Make sure we're not just moving the file to the same directory
              if not from_file.equal(to_file):
                if from_file.move(to_file):
                  num_success += 1

        if num_success > 0:
          config_fb = self.client.get_string(group, 'fb')
          open_dir = path.replace(' ', '\ ')
          os.system('%s %s &' % (config_fb, open_dir))
          self.dialog.hide()

    return True

  def treeview_drag_motion(self, treeview, context, x, y, time):
    treepath, column = treeview.get_path_at_pos(x, y)[0:2]
    selection = self.treeview.get_selection()

    path = self.liststore[treepath][3]

    if path in self.droppable_places:
      selection.select_path(treepath)

    else:
      selection.unselect_all()

  def treeview_drag_leave(self, treeview, context, time):
    self.treeview.get_selection().unselect_all()
    self.drag_done = True

  def dialog_focus_out(self, dialog, event):
    if self.drag_done:
      self.dialog.hide()

  #Certain places, regardless of GIO/not GIO
  def do_places(self, *args):
    self.liststore.clear()
    self.places_paths = []
    self.places_data = []

    #Get the needed config values
    self.show_computer = self.client.get_bool(group, 'show_computer')
    self.show_home = self.client.get_int(group, 'show_home')
    self.show_filesystem = self.client.get_int(group, 'show_filesystem')
    self.show_local = self.client.get_int(group, 'show_local')
    self.show_network = self.client.get_int(group, 'show_network')
    self.show_connect = self.client.get_int(group, 'show_connect')
    self.show_bookmarks = self.client.get_int(group, 'show_bookmarks')
    self.show_trash = self.client.get_bool(group, 'show_trash')

    if self.show_computer and self.nautilus_computer:
      self.place('computer', _("Computer"), 'exec://nautilus computer:')

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

        icons = None

        try:
          if isinstance(icon, gio.ThemedIcon):
            icons = icon.get_names()

          elif isinstance(icon, gio.FileIcon):
            icons = (icon.get_file().get_path(), )
        except:
          pass

        if icons is None:
          icons = ('drive-harddisk', 'drive')

        #Get the human-readable name
        name = vol.get_name()

        #Get the path
        if vol.get_mount():
          path = vol.get_mount().get_root().get_uri()
          icon = vol.get_mount().get_icon()

          icons = None
          try:
            if isinstance(icon, gio.ThemedIcon):
              icons = icon.get_names()

            elif isinstance(icon, gio.FileIcon):
              icons = (icon.get_file().get_path(), )
          except:
            pass

          if icons is None:
            icons = ('drive-harddisk', 'drive')

          #Get the eject icon if this volume can be unmounted
          if vol.get_mount().can_unmount():
            eject = self.load_pixbuf(('media-eject', ))

            #This also means that the volume is mounted, and probably can be written to
            if gio:
              if path not in self.droppable_places:
                self.droppable_places.append(path)

        else:
          path = 'mount://%s' % i

        icon = self.load_pixbuf(icons)

        self.liststore.append((icon, name, eject, path, i))
        self.places_data.append([icons, name, bool(eject), path, i])

        i += 1

    if self.show_network == 2:
      for mount in self.monitor.get_mounts():
        if mount.get_volume() is None:
          #Get the icon
          icon = mount.get_icon()

          icons = None
          try:
            if isinstance(icon, gio.ThemedIcon):
              icons = icon.get_names()

            elif isinstance(icon, gio.FileIcon):
              icons = (icon.get_file().get_path(), )
          except:
            pass

          if icons is None:
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

            #This means that the volume is mounted, and probably can be written to
            if gio:
              if path not in self.droppable_places:
                self.droppable_places.append(path)

          self.liststore.append((icon, name, eject, path, i))
          self.places_data.append([icons, name, bool(eject), path, i])

          i += 1

    self.do_ncs()
    self.do_bookmarks()
    self.do_trash()

    if self.docklet_visible:
      self.update_docklet()

  #A volume was mounted through file-browser-launcher; open the file manager to the path
  def gio_mounted(self, vol, blah):
    try:
      uri = vol.get_mount().get_root().get_uri()
    except:
      return

    self.launch_fb(None, uri)

  #If nautilus-connect-server is installed, offer to start it "Connect to server..."
  def do_ncs(self):
    if self.nautilus_connect_server and self.show_connect == 2:
      self.place('applications-internet', _("Connect to Server..."),
        'exec://nautilus-connect-server')

  def try_to_get_custom_icon_for_path(self, path):
    if not gio:
        return "folder"

    gfile = gio.File(path)
    ginfo = gfile.query_info(",".join(["metadata::custom-icon", gio.FILE_ATTRIBUTE_STANDARD_ICON]), gio.FILE_QUERY_INFO_NONE)

    std_icon_uri = ginfo.get_attribute_object(gio.FILE_ATTRIBUTE_STANDARD_ICON)
    custom_icon_uri = ginfo.get_attribute_string("metadata::custom-icon")

    if custom_icon_uri is not None:
        cu_ico = gio.File(custom_icon_uri).get_path()
        if cu_ico is not "":
            return cu_ico
    return std_icon_uri.get_names()

  #Go through the list of bookmarks and add them to the list IF it's not in the mount list
  def do_bookmarks(self):
    if self.show_bookmarks == 2:
      #Get list of bookmarks
      try:
        self.bmarks2 = open(os.path.expanduser('~/.gtk-bookmarks'))
        self.bmarks = self.bmarks2.readlines()
        self.bmarks2.close()
      except:
        self.bmarks = []

      if gio:
        self.paths = []

      for path in self.bmarks:
        path = path.replace('file://', '').replace('\n', '')

        #Get the human-readable name
        try:
          name = ' '.join(path.split(' ')[1:])
          assert name.strip() != ''
        except:
          name = None

        path = urllib.unquote(path.split(' ')[0])
        type = path.split(':')[0]

        #Check if this path hasn't been used already
        if path not in self.paths and path.rstrip('/') != os.environ['HOME'].rstrip('/'):
          #Check if this is a path on the filesystem
          if path[0] == '/':
            if os.path.isdir(path):
              #If the user did not rename the bookmark - get the name from
              #the folder name (/media/Lexar -> Lexar)
              if name is None:
                try: name = path.split('/')[-1]
                except: name = path

              if path.replace('/', '') != '/':
                path2 = path
                while path2[-1] == '/':
                  path2 = path2[:-1]

                self.place(self.try_to_get_custom_icon_for_path(path), name, path)

          # computer://, trash://, network fs, etc.
          else:
            if type == 'computer':
              self.place('computer', name, path, _("Computer"))

            elif type in ['network', 'smb', 'nfs', 'ftp', 'sftp', 'ssh']:
              self.place('network-folder', name, path, _("Network"))

            elif type == 'x-nautilus-search':
              self.place('search', name, path, _("Search"))

            elif type == 'burn':
              self.place('drive-optical', name, path, _("CD/DVD Burner"))

            elif type == 'fonts':
              self.place('font', name, path, _("Fonts"))

            #Default to folder
            else:
              self.place('folder', name, path, _("Folder"))

  def do_trash(self):
    if self.show_trash:
      count = self.trash.props.file_count
      if count > 0:
        self.place('user-trash-full', _("Trash (%d)" % count), 'trash:///')

      else:
        self.place('user-trash', _("Trash"), 'trash:///')

      if gio:
        self.droppable_places.append('trash:///')

  #Function to show the home folder, mounted drives/partitions, and bookmarks according to config
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
          if path.split('/')[2] in ['cdrom0', 'cdrom1', 'cdrom2', 'cdrom3', 'cdrom4', 'cdrom5']:

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
    self.do_trash()

    if self.docklet_visible:
      self.update_docklet()

  def load_pixbuf(self, names, size=24):
    if type(names) == str:
      names = (names, )

    if size not in self.icons:
      self.icons[size] = {}

    worked = False
    for name in names:
      #Load the icon if it hasn't been yet
      if not self.icons[size].has_key(name):
        if name[0] == '/':
          try:
            icon = gtk.gdk.pixbuf_new_from_file_at_size(name, size, size)
            worked = True
            break
          except:
            pass

        else:
          try:
            icon = self.theme.load_icon(name, size, 0)
            worked = True
            break

          except:
            pass

      #Icon has already been loaded
      else:
        worked = True
        icon = self.icons[size][name]
        break

    #If no icon does exists - load default folder icon
    if not worked:
      if 'folder' not in self.icons[size]:
        self.icons[size]['folder'] = self.theme.load_icon('folder', size, 0)

      icon = self.icons[size]['folder']
      self.icons[size][name] = icon

    else:
      self.icons[size][name] = icon

    return icon

  def place(self, icon_names, human_name, path, alt_name=None):
    icon = self.load_pixbuf(icon_names)
    self.liststore.append([icon, [human_name, alt_name][human_name is None], None, path, -1])
    self.places_data.append([icon_names, [human_name, alt_name][human_name is None], False, path, -1])

    if gio:
      if path not in self.droppable_places:
        if os.path.isdir(path) and path != '/':
          self.droppable_places.append(path)

  def ejected_or_unmounted(self, *a):
    pass

  #Function to do what should be done according to config when the treeview is clicked
  def treeview_clicked(self, widget, event):
    self.open_clicked = self.client.get_int(group, 'places_open')
    selection = self.treeview.get_selection()

    if gio:
      #Get some data
      path, column = widget.get_path_at_pos(int(event.x), int(event.y))[0:2]
      posx, posy = column.cell_get_position(self.eject_render)

      #Check if the eject column was clicked
      if posx + 24 > event.x and posx <= event.x:
        #Check if this is a volume or a mount
        num = self.liststore[path][4]
        if num != -1:
          if self.unmount(num):
            return False
          #Otherwise, just open it

    if self.open_clicked == 2:
      self.dialog.hide()
      self.launch_fb(None, self.liststore[selection.get_selected()[1]][3])

    else:
      self.entry.set_text(self.liststore[selection.get_selected()[1]][3])
      self.entry.grab_focus()

  def unmount(self, num):
    li = self.monitor.get_volumes()
    li.extend(self.monitor.get_mounts())

    #If it's a volume
    if isinstance(li[num], gio.Volume):
      if li[num].get_mount():
        #If the volume can eject
        if li[num].get_mount().can_eject():
          li[num].get_mount().eject(self.ejected_or_unmounted)
          return True

        #If the volume can unmount
        if li[num].get_mount().can_unmount():
          li[num].get_mount().unmount(self.ejected_or_unmounted)
          return True

    #It's a mount
    else:
      #If the mount can eject
      if li[num].can_eject():
        li[num].eject(self.ejected_or_unmounted)
        return True

      #If the mount can unmount
      elif li[num].can_unmount():
        li[num].unmount(self.ejected_or_unmounted)
        return True

    return False

  def icon_clicked(self, widget):
    event = gtk.get_current_event()

    #Dialog mode
    if self.client.get_int(group, 'mode') == 0:
      if self.dialog.flags() & gtk.VISIBLE:
        self.dialog.hide()

      else:
        self.dialog_config(event.button)

    #Docklet mode
    else:
      self.dialog_config(event.button)

  def show_context_menu(self, widget, event):
    self.dialog.hide()
    self.show_menu(event)

  def show_docklet(self, window_id):
    self.docklet_visible = True
    docklet = awn.Applet(self.get_canonical_name(), self.props.uid, self.props.panel_id)
    docklet.props.quit_on_delete = False
    self.docklet = docklet

    def invalidate_docklet(widget, applet):
      applet.docklet_visible = False
      applet.docklet = None
    docklet.connect("destroy", invalidate_docklet, self)

    docklet_position = docklet.get_pos_type()
    top_box = awn.Box()
    top_box.set_orientation_from_pos_type(docklet_position)

    align = awn.Alignment(docklet)
    box = awn.Box()
    box.set_orientation_from_pos_type(docklet_position)
    align.add(box)

    align.set(0.5, 0.5, 1.0, 1.0)
    top_box.pack_start(align)

    self.docklet_box = awn.IconBox(docklet)

    self.update_docklet(False)

    top_box.pack_start(self.docklet_box, True, True)
    docklet.add(top_box)

    gtk.Plug.__init__(docklet, long(window_id))

    self.update_docklet()

  def update_docklet(self, show_all=True):
    if self.mode == 1:
      box = self.docklet_box

    elif self.mode == 2:
      box = self.icon_box

    for icon in box.get_children():
      if icon == self.icon:
        box.remove(icon)
      else:
        icon.destroy()

    for place in self.places_data:
      icon = awn.Icon()
      icon.set_from_pixbuf(self.load_pixbuf(place[0], self.get_size()))
      icon.set_tooltip_text(place[1])
      icon.connect('clicked', self.docklet_icon_clicked, place[3])
      icon.connect('middle-clicked', self.docklet_icon_middle_clicked, place[3])
      icon.connect('context-menu-popup', self.docklet_icon_menu, place)
      box.add(icon)
      box.set_child_packing(icon, False, True, 0, gtk.PACK_START)

      if gio and place[3] in self.droppable_places:
        icon.drag_dest_set(gtk.DEST_DEFAULT_DROP | gtk.DEST_DEFAULT_MOTION, \
          [("text/uri-list", 0, 0)], gtk.gdk.ACTION_MOVE)
        icon.connect('drag-data-received', self.docklet_drag_data_received, place[3])
        icon.connect('drag-motion', self.docklet_drag_motion)
        icon.connect('drag-leave', self.docklet_drag_leave)

    if show_all and self.mode == 1:
      self.docklet.show_all()

    elif show_all and self.mode == 2:
      self.icon_box.show_all()

  def docklet_drag_data_received(self, w, context, x, y, data, info, time, path):
    if data and data.format == 8:
      context.finish(True, False, time)

      if path in self.droppable_places:
        dropped_paths = data.data.split('\n')
        num_success = 0

        if path == 'trash:///':
          for dropped_path in dropped_paths:
            from_file = vfs.File.for_uri(urllib.unquote(dropped_path).strip())
            try:
              self.trash.send_to_trash(from_file)
            except:
              pass

        else:
          for dropped_path in dropped_paths:
            if len(dropped_path) >= 8:
              if dropped_path[:8] == 'file:///':
                dropped_path = dropped_path.strip()

                dropped_path = urllib.unquote(dropped_path)

                from_file = gio.File(dropped_path)

                to_file = gio.File(path + '/' + from_file.get_basename())

                #Make sure we're not just moving the file to the same directory
                if not from_file.equal(to_file):
                  if from_file.move(to_file):
                    num_success += 1

          if num_success > 0:
            config_fb = self.client.get_string(group, 'fb')
            open_dir = path.replace(' ', '\ ')
            os.system('%s %s &' % (config_fb, open_dir))
            self.dialog.hide()

      return True

  def docklet_drag_motion(self, icon, context, x, y, time):
    icon.get_effects().start(awn.EFFECT_LAUNCHING)
    icon.get_tooltip().update_position()
    icon.get_tooltip().show()

    return True

  def docklet_drag_leave(self, icon, context, time):
    icon.get_effects().stop(awn.EFFECT_LAUNCHING)
    icon.get_tooltip().hide()

    return True

  def docklet_icon_clicked(self, icon, uri):
    self.launch_fb(None, uri)

    if self.mode == 1:
      self.docklet.destroy()

  def docklet_icon_middle_clicked(self, icon, uri):
    if not os.path.isdir(uri.replace('file:///', '/')):
      return False

    self.icon_dialog = awn.Dialog(icon, self)
    self.icon_dialog.connect('focus-out-event', self.icon_dialog_focusout)

    self.icon_entry = gtk.Entry()
    self.icon_entry.connect('key-release-event', self.detect_enter)
    self.icon_entry.set_text(uri.replace('file:///', '/') + ['/', ''][uri[-1] == '/'])

    self.icon_enter = gtk.Button(stock=gtk.STOCK_OPEN)
    self.icon_enter.connect('clicked', self.launch_fb, self.icon_entry)

    hbox = gtk.HBox()
    hbox.pack_start(self.icon_entry)
    hbox.pack_start(self.icon_enter, False)

    self.icon_dialog.add(hbox)
    self.icon_dialog.show_all()

    self.icon_entry.grab_focus()
    self.icon_entry.set_position(-1)

  def icon_dialog_focusout(self, widget, event):
    widget.hide()

    gobject.timeout_add_seconds(1, widget.destroy)

  def docklet_icon_menu(self, icon, event, place):
    menu = self.create_default_menu()

    if place is not None:
      #If the place is ejectable
      if place[2]:
        eject = awn.image_menu_item_new_with_label(_("Eject"))
        image = gtk.image_new_from_icon_name('media-eject', gtk.ICON_SIZE_MENU)
        eject.set_image(image)
        menu.append(eject)

        eject.connect('activate', self.docklet_menu_eject, place[4])

      elif place[3] == 'trash:///':
        empty = gtk.MenuItem(_("Empty Trash"))
        menu.append(empty)

        if self.trash.props.file_count == 0:
          empty.set_sensitive(False)

        empty.connect('activate', self.docklet_empty_trash)

    prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
    prefs.connect('activate', self.open_prefs)
    menu.append(prefs)

    about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
    about.connect("activate", self.open_about)
    menu.append(about)

    menu.show_all()
    icon.popup_gtk_menu (menu, event.button, event.time)

  def docklet_menu_eject(self, menu, num):
    self.unmount(num)

  def docklet_empty_trash(self, menu):
    dialog = gtk.Dialog(_("Confirm deletion"), self, gtk.DIALOG_MODAL,
      (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.set_icon_name('user-trash-full')

    vbox = gtk.VBox(False, 6)
    vbox.set_border_width(12)

    label1 = gtk.Label()
    label1.set_markup(_("<big><b>Are you sure you want to delete\nevery item from the trash?</b></big>"))

    label2 = gtk.Label(_("This action cannot be undone."))
    label2.set_alignment(0.0, 0.0)

    vbox.pack_start(label1, False)
    vbox.pack_start(label2, False)

    dialog.vbox.pack_start(vbox)
    dialog.show_all()
    response = dialog.run()
    dialog.destroy()

    if response == gtk.RESPONSE_ACCEPT:
      try:
        self.trash.empty()
      except:
        pass

  #The user changed the icon theme
  def icon_theme_changed(self, icon_theme):
    for d in self.icons.values():
      for key in d.keys():
        del d[key]

    if gio:
      self.do_gio_places()

    #Reload the stock folder icon
    self.icons[24]['folder'] = self.theme.load_icon('folder', 24, 0)

  def dialog_config(self, button):
    #Left click data
    if button == 1:
      action = self.client.get_int(group, 'lmb')
      path = os.path.expanduser(self.client.get_string(group, 'lmb_path'))

    #Middle click data
    elif button == 2:
      action = self.client.get_int(group, 'mmb')
      path = os.path.expanduser(self.client.get_string(group, 'mmb_path'))

    if action == 3:
      return

    if path.strip() == '':
        path = os.environ['HOME']

    if path[-1] != '/':
        path += '/'

    if not gio:
      self.add_places()

    mode = self.client.get_int(group, 'mode')

    #Get whether to focus the entry when displaying the dialog or not
    config_focus = self.client.get_int(group, 'focus_entry')

    #Show dialog/docklet
    if action == 1:
      #Docklet
      if mode == 1:
        #Occasionally this happens; don't do two docklets at once
        if not self.docklet_visible:
          win = self.docklet_request(0, True, True)
          if win != 0:
            self.show_docklet(win)

      #Dialog
      else:
        self.entry.set_text(path)

        self.treeview.show()
        self.dialog.set_property('anchor', self.icon)
        self.dialog.show_all()

        self.entry.grab_focus()
        self.entry.set_position(-1)

    #Launch path
    elif action == 2:
      self.launch_fb(None, path)

  def update_mode(self, *args):
    self.mode = self.client.get_int(group, 'mode')

    self.dialog.hide()

    if 'docklet' in dir(self) and self.docklet is not None:
      self.docklet.destroy()

    if self.mode != 2:
      self.docklet_visible = False

      for icon in self.icon_box.get_children():
        if icon == self.icon:
          self.icon_box.remove(icon)
        else:
          icon.destroy()

      self.icon_box.add(self.icon)
      self.show_all()

    else:
      self.docklet_visible = True
      self.update_docklet()

  #If the user hits the enter key on the main part OR the number pad
  def detect_enter(self, widget, event):
    if event.keyval == 65293 or event.keyval == 65421:
      if widget == self.entry:
        self.enter.clicked()
      else:
        self.icon_enter.clicked()

  #Launces file browser to open "path". If "path" is None: use value from the entry widget
  def launch_fb(self, widget, path=None):
    self.dialog.hide()
    if isinstance(path, gtk.Widget):
      path = path.get_text()
      self.icon_dialog.hide()
      if self.mode == 1:
        self.docklet.destroy()
    elif path is None:
      path = self.entry.get_text()

    #Get the file browser app
    config_fb = self.client.get_string(group, 'fb')

    #In case there is nothing but whitespace (or at all) in the entry widget
    if path.replace(' ', '') == '':
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
      os.system('%s %s &' % (config_fb, path.replace(' ', '\ ')))

  #Right click menu - Preferences or About
  def show_menu(self, event):
    #Hide the dialog if it's shown
    self.dialog.hide()

    #Create the items for Preferences and About
    prefs = gtk.ImageMenuItem(gtk.STOCK_PREFERENCES)
    about = gtk.ImageMenuItem(gtk.STOCK_ABOUT)

    #Connect the two items to functions when clicked
    prefs.connect("activate", self.open_prefs)
    about.connect("activate", self.open_about)

    #Now create the menu to put the items in and show it
    self.menu = self.create_default_menu()
    self.menu.append(prefs)
    self.menu.append(about)
    self.menu.show_all()
    self.popup_gtk_menu (self.menu, event.button, event.time)

  #Show the preferences window
  def open_prefs(self, widget):
    #Import the prefs file from the same directory
    import prefs

    #Show the prefs window - see prefs.py
    prefs.Prefs(self)
    gtk.main()

  #Show the about window
  def open_about(self, widget):
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
