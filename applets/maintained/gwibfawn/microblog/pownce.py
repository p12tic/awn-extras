
"""

Pownce interface for Gwibber
SegPhault (Ryan Paul) - 03/01/2008

"""

from . import can, support
import urllib2, urllib, base64, mx.DateTime, simplejson

PROTOCOL_INFO = {
  "name": "Pownce",
  "version": 0.1,
  
  "config": [
    "private:password",
    "username",
    "message_color",
    "comment_color",
    "receive_enabled",
    "send_enabled"
  ],

  "features": [
    can.SEND,
    can.RECEIVE,
  ],
}

API_KEY = "w5t07ju7t1072o1wfx8l9012a51fdabq"

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.sender = data["sender"]["first_name"]
    self.sender_nick = data["sender"]["username"]
    self.sender_id = data["sender"]["id"]
    self.time = mx.DateTime.DateTimeFrom(data["timestamp"]).gmtime()
    self.text = support.xml_escape(data["body"])
    self.image = data["sender"]["profile_photo_urls"]["medium_photo_url"]
    self.bgcolor = "message_color"
    if "permalink" in data:
      self.url = data["permalink"]
    self.profile_url = data["sender"]["permalink"]
    self.id = data["id"]

class Comment(Message):
  def __init__(self, client, data):
    Message.__init__(self, client, data)
    self.bgcolor = "comment_color"

class Client:
  def __init__(self, acct):
    self.account = acct

  def get_auth(self):
    return "Basic %s" % base64.encodestring(
      ("%s:%s" % (self.account["username"], self.account["private:password"]))).strip()

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(
      url, data, {"Authorization": self.get_auth()})).read()

  def get_thread_data(self, msg):
    return simplejson.loads(self.connect(
      "http://api.pownce.com/2.0/notes/%s.json?app_key=%s&show_replies=true" % (msg.id, API_KEY)))

  def get_thread(self, msg):
    yield msg
    messages = self.get_reply_data(msg)
    if "replies" in messages:
      for data in messages["replies"]:
        yield Comment(self, data)

  def reply(self, msg, message):
    return self.connect("http://api.pownce.com/2.0/send/reply.json",
        urllib.urlencode({"note_body": message, "app_key": API_KEY, "reply_to": msg.id}))
    
  def get_data(self):
    return simplejson.loads(self.connect(
      "http://api.pownce.com/2.0/note_lists/%s.json?app_key=%s" % (self.account["username"], API_KEY)))

  def receive(self):
    for data in self.get_data()["notes"]:
      if data["type"] == "message": yield Message(self, data)
      else: yield Comment(self, data)

  def send(self, message):
    return self.connect("http://api.pownce.com/2.0/send/message.json",
        urllib.urlencode({"note_body":message, "app_key": API_KEY, "note_to": "public"}))

  def send_link(self, message):
    return self.connect("http://api.pownce.com/2.0/send/message.json",
        urllib.urlencode({"note_body":message, "app_key": API_KEY, "note_to": "public"}))

