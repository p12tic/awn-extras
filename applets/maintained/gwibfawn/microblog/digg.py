
"""

Digg interface for Gwibber
SegPhault (Ryan Paul) - 01/06/2008

"""

from . import can
import urllib2, support, re
import time, simplejson

PROTOCOL_INFO = {
  "name": "Digg",
  "version": 0.1,
  
  "config": [
    "username",
    "digg_color",
    "comment_color",
    "receive_enabled",
  ],

  "features": [
    can.RECEIVE,
  ],
}

LINK_PARSE =  re.compile("<a[^>]+href=\"(https?://[^\"]+)\">[^<]+</a>")

def sanitize_text(t):
  return LINK_PARSE.sub("\\1", t.strip())

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.title = data["title"]
    sender = data["friends"]["users"][0]
    self.sender = "fullname" in sender and sender["fullname"] or sender["name"]
    self.sender_nick = sender["name"]
    self.sender_id = sender["name"]
    
    try:
      self.time = support.parse_time(sender["date"])
    except:
      self.time = support.parse_time(time.asctime(time.gmtime(sender["date"])))
    
    self.text = sanitize_text(data["description"])
    self.image = sender["icon"]
    self.bgcolor = "comment_color"
    self.url = data["link"]
    self.profile_url = "http://digg.com/users/%s" % self.sender_nick
    self.diggs = data["diggs"]

class Digg(Message):
  def __init__(self, client, data):
    Message.__init__(self, client, data)
    self.title = "%s <small>dugg %s</small>" % (self.sender_nick, self.title)
    self.bgcolor = "digg_color"

class Client:
  def __init__(self, acct):
    self.account = acct

  def receive_enabled(self):
    return self.account["receive_enabled"] and \
      self.account["username"] != None

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(url, data))

  def get_comments(self):
    return simplejson.load(self.connect(
      "http://services.digg.com/user/%s/friends/commented?appkey=http://launchpad.net/gwibber&type=json" %
        self.account["username"]))["stories"]

  def get_diggs(self):
    return simplejson.load(self.connect(
      "http://services.digg.com/user/%s/friends/dugg?appkey=http://launchpad.net/gwibber&type=json" %
        (self.account["username"])))["stories"]

  def receive(self):
    #for data in self.get_comments()[0:10]:
    #  yield Message(self, data)

    for data in self.get_diggs():
      yield Digg(self, data)


