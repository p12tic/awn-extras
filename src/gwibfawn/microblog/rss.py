
"""

RSS interface for Gwibber
SegPhault (Ryan Paul) - 11/08/2008

"""

from . import can, support
import urlparse, feedparser

PROTOCOL_INFO = {
  "name": "RSS/Atom",
  "version": 0.1,
  
  "config": [
    "feed_url",
    "message_color",
    "receive_enabled",
  ],

  "features": [
    can.RECEIVE,
  ],
}

feedparser._HTMLSanitizer.acceptable_elements = []

def account_name(acct):
  if acct["feed_url"]:
    return urlparse.urlparse(acct["feed_url"])[1]

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.sender = data.get("author", "")
    self.sender_nick = self.sender
    self.sender_id = self.sender

    if hasattr(data, "summary"):
      self.text = data.summary
    elif hasattr(data, "content"):
      if hasattr(data.content, "value"):
        self.text = data.content.value
      else: self.text = ""
    else: self.text = ""

    self.time = support.parse_time(data.updated)
    self.bgcolor = "message_color"
    if hasattr(data, "link"):
      self.url = data.link
    self.profile_url = "" # feed.author_detail.href
    self.title = "%s <br /> <small>By %s</small>" % (data.title, self.sender)

    if len(self.text) > 300:
      self.html_string = "%s..." % self.text[:300]
    else: self.html_string = self.text

class Client:
  def __init__(self, acct):
    self.account = acct

  def receive(self):
    f = feedparser.parse(self.account["feed_url"])
    
    for data in f.entries:
      yield Message(self, data)
