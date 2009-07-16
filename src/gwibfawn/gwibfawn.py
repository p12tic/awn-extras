#!/usr/bin/python

# Copyright (c) 2009 Michal Hruby <michal.mhr at gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import awn
import gtk
import gobject
import cairo
import os, sys
import urllib2
import hashlib
import sexy
import re
import pynotify
from threading import Thread
from microblog import twitter

class AccountWrapper:
   def __init__ (self, accData, id):
      self.data = accData
      self.id = id

   def __getitem__ (self, key):
      return self.data[key]

IMG_CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "gwibber", "images")

def image_cache(url, cache_dir = IMG_CACHE_DIR):
  if not os.path.exists(cache_dir): os.makedirs(cache_dir)
  encoded_url = hashlib.sha1(url).hexdigest()
  if len(encoded_url) > 200: encoded_url = encoded_url[::-1][:200]
  fmt = url.split('.')[-1] # jpg/png etc.
  img_path = os.path.join(cache_dir, encoded_url + '.' + fmt).replace("\n", "")

  if not os.path.exists(img_path):
    try:
      loader = gtk.gdk.PixbufLoader()
      loader.write(urllib2.urlopen(url).read())
      loader.close()
      pixbuf = loader.get_pixbuf()
      (x, y) = pixbuf.get_width(), pixbuf.get_height()
      if x != 48 or y != 48:
        pixbuf = pixbuf.scale_simple(48, 48, gtk.gdk.INTERP_BILINEAR)
      pixbuf.save(img_path, fmt)
    except Exception, e:
      print "Error occurred during image fetching"
      img_path = ''

  return img_path

class Avatar (gtk.Image):
   def __init__ (self):
      gtk.Image.__init__ (self)
      self.connect ("expose-event", self.expose)
      self.connect ("size-request", self.on_size_request)

   def on_size_request (self, widget, requisition):
      if widget.get_storage_type() == gtk.IMAGE_PIXBUF:
        requisition.height = widget.get_pixbuf().get_height() * 3 / 2

   def expose (self, widget, event):
      if widget.get_storage_type() != gtk.IMAGE_PIXBUF: return False
      pixbuf = widget.get_pixbuf()

      cr = widget.window.cairo_create ()

      cr.rectangle (widget.allocation.x, widget.allocation.y,
                    widget.allocation.width, widget.allocation.height)
      cr.clip ()

      cr.translate (event.area.x, event.area.y)
      cr.set_source_pixbuf (pixbuf, 0, 0)
      cr.paint ()

      #reflection
      cr.translate (0, pixbuf.get_height())

      pat = cairo.LinearGradient (0, 0, 0, widget.allocation.height - pixbuf.get_height())
      pat.add_color_stop_rgba (0.0, 0.0, 0.0, 0.0, 0.5)
      pat.add_color_stop_rgba (1.0, 0.0, 0.0, 0.0, 0.0)

      """
      # debug
      cr.set_source (pat)
      cr.rectangle (0, 0, pixbuf.get_width(), pixbuf.get_height())
      cr.fill ()
      """
      flipped = pixbuf.flip(False)
      cr.set_source_pixbuf (flipped, 0, 0)
      cr.mask (pat)

      del flipped
      del pat
      del cr

      return True

class GwibberApplet (awn.AppletSimple):

   APPLET_NAME = "Gwibfawn"

   def __init__ (self, uid, panel_id):

      awn.AppletSimple.__init__ (self, "gwibfawn", uid, panel_id)
      self.set_tooltip_text(GwibberApplet.APPLET_NAME)
      self.set_icon_name('gwibber')

      pynotify.init(GwibberApplet.APPLET_NAME)

      self.dialog = awn.Dialog(self)

      self.msg_ids = []
      self.first_update = True

      self.timeline = gtk.VBox()
      self.timeline.set_spacing(6)
      self.dialog.add (self.timeline)

      # add credentials here, since the applet doesn't have prefs dialog yet
      data = {"protocol": "Twitter",
              "username": "",
              "private:password": "",
              "receive_enabled": True,
              "send_enabled": False,
              "search_enabled": False,
              "receive_count": 5}
      account = AccountWrapper (data, "123")

      self.client = twitter.Client(account)

      self.connect("button-press-event", self.button_press)

      self.unread_msgs = 0
      self.update_thread_running = False
      self.update_messages()

      gobject.timeout_add_seconds (60, self.update_messages)

   def button_press (self, widget, event):
       if event.button == 1:
          if self.dialog.flags() & gtk.VISIBLE != 0:
              self.dialog.hide()
          else:
              self.unread_msgs = 0
              self.get_icon().set_indicator_count(0)
              self.dialog.show_all()

   def update_messages (self):
      if self.update_thread_running: return True

      self.update_thread_running = True

      def worker():
         l = []
         try:
            for msg in self.client.receive():
               msg.image_path = image_cache(msg.image)
               l.append(msg)
         except Exception, e:
            print >> sys.stderr, "%s: Unable to retrieve messages!" % GwibberApplet.APPLET_NAME
         gobject.idle_add(self.messages_ready, l)

      Thread(target=worker).start()
      return True

   def create_message_widget (self, msg, do_notify = False):
      # TODO: wrap all in Event box and paint custom background?
      message = gtk.HBox()
      message.set_spacing (6)
      # get avatar
      image = Avatar()
      image_pixbuf = gtk.gdk.pixbuf_new_from_file (msg.image_path)
      image.set_from_pixbuf (image_pixbuf)
      message.add(image)
      # get author & text
      content = gtk.VBox()
      author_align = gtk.Alignment (0.0)
      author = gtk.Label()
      author.set_justify(gtk.JUSTIFY_LEFT)
      author.set_markup("<span size='large' weight='bold'>%s</span>" % msg.sender_nick)
      author_align.add (author)

      text_align = gtk.Alignment ()
      text_align.set_padding (0, 0, 6, 0)
      text = sexy.UrlLabel()
      string = re.sub(r'\bclass="[^"]*"\s*', '', msg.html_string)
      string = re.sub(r'&', '&amp;', string)
      text.set_markup(string)
      text.set_line_wrap(True)
      text.set_size_request(250, -1)
      text_align.add (text)

      content.add(author_align)
      content.add(text_align)

      message.add(content)

      if do_notify:
         n = pynotify.Notification (msg.sender_nick, msg.text)
         n.set_icon_from_pixbuf (image_pixbuf)
         n.show ()

      return message

   def messages_ready (self, msgs):
      gtk.gdk.threads_enter()

      self.update_thread_running = False

      msgs = filter (lambda x: x.id not in self.msg_ids, msgs)

      new_msgs = len(msgs)
      self.unread_msgs = self.unread_msgs + new_msgs

      if new_msgs > 0:
         fx = self.get_icon().get_effects()
         fx.start_ex(awn.EFFECT_ATTENTION, max_loops = 1)

      if self.dialog.flags() & gtk.VISIBLE == 0:
         self.get_icon().set_indicator_count(self.unread_msgs)

      # yea, i know this is a bit of black magic, but it basically makes sure
      # that when messages_ready is called the 2nd, 3rd, .... time, the latest
      # messages are still on top

      for i in msgs:
         ch = self.timeline.get_children()
         if len(ch) > 0:
           self.timeline.remove(ch[-1])
           self.msg_ids = self.msg_ids[:-1]

      msg_sorted = []

      for msg in msgs:
         msg.widget = self.create_message_widget (msg, not self.first_update)
         msg_sorted.append(msg)

      msg_sorted.reverse()
      for msg in msg_sorted:
         self.msg_ids.insert (0, msg.id)
         self.timeline.pack_end (msg.widget)
      self.timeline.show_all ()

      self.first_update = False

      gtk.gdk.threads_leave()

if __name__ == "__main__":
   gobject.threads_init   ()
   gtk.gdk.threads_init   ()
   gtk.gdk.threads_enter  ()
   awn.init               (sys.argv[1:])
   applet = GwibberApplet (awn.uid, awn.panel_id)
   awn.init_applet        (applet)
   applet.show_all        ()
   gtk.main               ()
   gtk.gdk.threads_leave  ()
