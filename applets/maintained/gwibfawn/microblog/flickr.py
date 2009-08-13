
"""
Flickr interface for Gwibber
SegPhault (Ryan Paul) - 03/01/2008
"""
from . import can, support
import urllib2, urllib, mx.DateTime, simplejson

PROTOCOL_INFO = {
  "name": "Flickr",
  "version": 0.1,
  
  "config": [
    "username",
    "message_color",
    "receive_enabled",
  ],

  "features": [
    can.RECEIVE,
  ],
}

API_KEY = "36f660117e6555a9cbda4309cfaf72d0"
REST_SERVER = "http://api.flickr.com/services/rest"
BUDDY_ICON_URL = "http://farm%s.static.flickr.com/%s/buddyicons/%s.jpg"
IMAGE_URL = "http://farm%s.static.flickr.com/%s/%s_%s_%s.jpg"
IMAGE_PAGE_URL = "http://www.flickr.com/photos/%s/%s"

def parse_time(t):
  return mx.DateTime.DateTimeFrom(int(t)).gmtime()

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.sender = data["username"]
    self.sender_nick = data["ownername"]
    self.sender_id = data["owner"]
    self.time = parse_time(data["dateupload"])
    self.text = data["title"]
    self.image =  BUDDY_ICON_URL % (data["iconfarm"], data["iconserver"], data["owner"])
    self.bgcolor = "message_color"
    self.url = IMAGE_PAGE_URL % (data["owner"], data["id"])
    self.profile_url = "http://www.flickr.com/people/%s" % (data["owner"])
    self.thumbnail = IMAGE_URL % (data["farm"], data["server"], data["id"], data["secret"], "t")
    self.html_string = """<a href="%s"><img src="%s" /></a>""" % (self.url, self.thumbnail)

class Client:
  def __init__(self, acct):
    self.account = acct

  def receive_enabled(self):
    return self.account["receive_enabled"] and \
      self.account["username"] != None

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(url, data)).read()

  def restcall(self, method, args):
    return simplejson.loads(self.connect(
      "%s/?api_key=%s&format=json&nojsoncallback=1&method=%s&%s" % (
        REST_SERVER, API_KEY, method, urllib.urlencode(args))))

  def getNSID(self):
    return self.restcall("flickr.people.findByUsername",
      {"username": self.account["username"]})["user"]["nsid"]

  def get_images(self):
    return self.restcall("flickr.photos.getContactsPublicPhotos",
      {"user_id": self.getNSID(), "extras": "date_upload,owner_name,icon_server"})

  def receive(self):
    for data in self.get_images()["photos"]["photo"]:
      yield Message(self, data)
