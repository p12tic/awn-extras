
"""
Facebook interface for Gwibber
SegPhault (Ryan Paul) - 12/22/2007
"""

from . import can, support
import urllib2, urllib, re, mx.DateTime

PROTOCOL_INFO = {
  "name": "Facebook",
  "version": 0.1,
  
  "config": [
    "message_color",
    "receive_enabled",
    "send_enabled"
  ],

  "features": [
    can.SEND,
    can.RECEIVE,
  ],
}

APP_KEY = "71b85c6d8cb5bbb9f1a3f8bbdcdd4b05"
SECRET_KEY = "41e43c90f429a21e55c7ff67aa0dc201"
LINK_PARSE =  re.compile("<a[^>]+href=\"(https?://[^\"]+)\">[^<]+</a>")

def sanitize_text(t):
  return LINK_PARSE.sub("\\1", t.strip()) #.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")

class Message:
  def __init__(self, client, data):
   try:
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.data = data
    self.sender = data['name']
    self.sender_nick = self.sender
    self.sender_id = self.sender.replace(" ", "_")
    self.profile_url = data['profile_url']
    self.url = data['profile_url']
    if data['status']:
      self.id = data['status']['status_id']
      self.url += '&story_fbid=' + str(self.id)
      self.time = mx.DateTime.DateTimeFrom(data['status']['time']).gmtime()

      self.text = sanitize_text(data['status']['message'])

      if self.text.startswith(self.sender):
        self.text = self.text[len(self.sender)+1:]
    self.bgcolor = "message_color"
    
    if data['pic_square']:
      self.image = data['pic_square']
    else:
      self.image = "http://digg.com/img/udl.png"
   except Exception:
    from traceback import format_exc
    print(format_exc())

class Client:
  def __init__(self, acct):
    self.account = acct
    
    self.facebook = support.facelib.Facebook(APP_KEY, SECRET_KEY)
    self.facebook.session_key = self.account["session_key"]
    self.facebook.uid = self.account["session_key"].split('-')[1]
    self.facebook.secret = self.account["private:secret_key"]

  def send_enabled(self):
    return self.account["send_enabled"] and \
      self.account["session_key"] != None and \
      self.account["private:secret_key"] != None

  def receive_enabled(self):
    return self.account["receive_enabled"] and \
      self.account["session_key"] != None and \
      self.account["secret_key"] != None

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(url, data))

  def get_messages(self):
    query = "SELECT name, profile_url, status, pic_square FROM user WHERE uid in (SELECT uid2 FROM friend WHERE uid1 = "+str(self.facebook.uid)+") AND status.message != '' AND status.time > 0 ORDER BY status.time DESC" # LIMIT 1,30"
    return self.facebook.fql.query([query])

  def receive(self):
    for data in self.get_messages():
      yield Message(self, data)

  def send(self, message):
    self.facebook.users.setStatus(message, False)

