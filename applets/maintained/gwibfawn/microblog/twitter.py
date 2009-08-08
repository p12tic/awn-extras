
"""

Twitter interface for Gwibber
SegPhault (Ryan Paul) - 12/22/2007

"""

from . import can, support
import urllib2, urllib, base64, re, simplejson
import gettext
_ = gettext.lgettext


PROTOCOL_INFO = {
  "name": "Twitter",
  "version": 0.1,
  
  "config": [
    "private:password",
    "username",
    "message_color",
    "receive_enabled",
    "send_enabled",
    "search_enabled",
    "receive_count",
  ],

  "features": [
    can.SEND,
    can.RECEIVE,
    can.SEARCH,
    can.TAG,
    can.REPLY,
    can.RESPONSES,
    can.DELETE,
    #can.THREAD,
    can.THREAD_REPLY,
    can.SEARCH_URL,
    can.USER_MESSAGES,
  ],
}

NICK_PARSE = re.compile("\B@([A-Za-z0-9_]+|@[A-Za-z0-9_]$)")
HASH_PARSE = re.compile("\B#([A-Za-z0-9_\-]+|@[A-Za-z0-9_\-]$)")

class Message:
  def __init__(self, client, data):
   try:
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.bgcolor = "message_color"
    self.id = data["id"] or ''
    self.time = support.parse_time(data["created_at"])
    self.is_private  = False

    if "user" in data:
      user = data["user"]
      self.reply_nick = data["in_reply_to_screen_name"]
      self.reply_url = "https://twitter.com/%s/statuses/%s" % (data["in_reply_to_screen_name"], data["in_reply_to_status_id"])
    elif "sender" in data:
      user = data["sender"]
      self.reply_nick = None
      self.reply_url = None
    elif "name" in data:
      user = data

    self.sender = user["name"]
    self.sender_nick = user["screen_name"]
    self.sender_id = user["id"]
    self.sender_location = user["location"]
    self.sender_followers_count = user["followers_count"]
    self.image = user["profile_image_url"]
    self.url = "https://twitter.com/%s/statuses/%s" % (user["screen_name"], data["id"])
    self.profile_url = "gwibber:user/%s/%s" % (self.account.id, user["screen_name"])
    self.external_profile_url = "https://twitter.com/%s" % user["screen_name"]

    if "text" in data:
      self.text = data["text"]
      self.html_string = '<span class="text">%s</span>' % \
          HASH_PARSE.sub('#<a class="inlinehash" href="gwibber:tag/\\1">\\1</a>',
          NICK_PARSE.sub('@<a class="inlinenick" href="gwibber:user/'+self.account.id+'/\\1">\\1</a>',
          support.linkify(self.text)))
      self.is_reply = re.compile("@%s[\W]+|@%s$" % (self.username, self.username)).search(self.text)
      self.reply_nick = ''
      self.reply_url = ''
    else:
      # if reached a protected gwibber:user tab then do some things differently
      if "name" in data:
        self.url = self.profile_url = self.external_profile_url = "https://twitter.com/%s" % data["screen_name"]
        self.is_reply = False
        if data["protected"] == True:
          self.text = _("This user has protected their updates.") + ' ' + _("You need to send a request before you can view this person's timeline.") + ' ' + _("Send request...")
          self.html_string = '<p><b>' + _("This user has protected their updates.") + '</b><p>' + _("You need to send a request before you can view this person's timeline.") + '<p><a href="' + self.url + '">' + _("Send request...") + '</a>'
        else:
          self.text = self.html_string = ''

    if "in_reply_to_screen_name" in data and "in_reply_to_status_id" in data and data["in_reply_to_status_id"]:
      self.reply_nick = data["in_reply_to_screen_name"]
      self.reply_url = "https://twitter.com/%s/statuses/%s" % (self.reply_nick, data["in_reply_to_status_id"])
   except Exception:
    from traceback import format_exc
    print(format_exc())

class SearchResult:
  def __init__(self, client, data, query = None):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]
    self.username = client.account["username"]
    self.sender = data["from_user"]
    self.sender_nick = data["from_user"]
    self.sender_id = data["from_user_id"]
    self.time = support.parse_time(data["created_at"])
    self.text = data["text"]
    self.image = data["profile_image_url"]
    self.bgcolor = "message_color"
    self.url = "https://twitter.com/%s/statuses/%s" % (data["from_user"], data["id"])
    self.profile_url = "gwibber:user/%s/%s" % (self.account.id, data["from_user"])
    self.external_profile_url = "https://twitter.com/%s" % data["from_user"]

    if query: html = support.highlight_search_results(self.text, query)
    else: html = self.text
    
    self.html_string = '<span class="text">%s</span>' % \
      HASH_PARSE.sub('#<a class="inlinehash" href="gwibber:tag/\\1">\\1</a>',
      NICK_PARSE.sub('@<a class="inlinenick" href="gwibber:user/'+self.account.id+'/\\1">\\1</a>',
        support.linkify(self.text)))

    self.is_reply = re.compile("@%s[\W]+|@%s$" % (self.username, self.username)).search(self.text) 

class Client:
  def __init__(self, acct):
    self.account = acct

  def send_enabled(self):
    return self.account["send_enabled"] and \
      self.account["username"] != None and \
      self.account["private:password"] != None

  def receive_enabled(self):
    return self.account["receive_enabled"] and \
      self.account["username"] != None and \
      self.account["private:password"] != None

  def get_auth(self):
    return "Basic %s" % base64.encodestring(
      ("%s:%s" % (self.account["username"], self.account["private:password"]))).strip()

  def connect(self, url, data = None):
    return urllib2.urlopen(urllib2.Request(
      url, data, headers = {"Authorization": self.get_auth()})).read()

  def get_messages(self):
    return simplejson.loads(self.connect(
      "https://twitter.com/statuses/friends_timeline.json" +'?'+
      urllib.urlencode({"count": self.account["receive_count"] or "20"})))

  def get_user_messages(self, screen_name):
    try:
      return simplejson.loads(self.connect(
        "https://twitter.com/statuses/user_timeline/"+ screen_name + ".json" +'?'+
          urllib.urlencode({"count": self.account["receive_count"] or "20"})))
    except Exception:
      profile = [simplejson.loads(self.connect(
        "https://twitter.com/users/show/"+ screen_name +".json"))]
      return profile

  def get_replies(self):
    return simplejson.loads(self.connect(
      "https://twitter.com/statuses/replies.json" +'?'+
        urllib.urlencode({"count": self.account["receive_count"] or "20"})))

  def get_direct_messages(self):
    return simplejson.loads(self.connect(
      "https://twitter.com/direct_messages.json"))

  def get_search_data(self, query):
    return simplejson.loads(urllib2.urlopen(
      urllib2.Request("http://search.twitter.com/search.json",
        urllib.urlencode({"q": query}))).read())

  def search(self, query):
    for data in self.get_search_data(query)["results"]:
      yield SearchResult(self, data, query)

  def search_url(self, query):
    urls = support.unshorten_url(query)
    for data in self.get_search_data(" OR ".join(urls))["results"]:
      if any(item in data["text"] for item in urls):
        yield SearchResult(self, data, query)

  def tag(self, query):
    for data in self.get_search_data("#%s" % query)["results"]:
      yield SearchResult(self, data, "#%s" % query)

  def responses(self):
    for data in self.get_replies():
      yield Message(self, data)

    for data in self.get_direct_messages():
      m = Message(self, data)
      m.is_private = True
      yield m

  def receive(self):
    for data in self.get_messages():
      yield Message(self, data)

  def user_messages(self, screen_name):
    for data in self.get_user_messages(screen_name):
      yield Message(self, data)

  def send(self, message):
    data = simplejson.loads(self.connect(
      "https://twitter.com/statuses/update.json",
        urllib.urlencode({"status":message, "source": "gwibbernet"})))
    return Message(self, data)

  def send_thread(self, message, target):
    data = simplejson.loads(self.connect(
      "https://twitter.com/statuses/update.json",
        urllib.urlencode({"status":message,
          "in_reply_to_status_id":target.id, "source": "gwibbernet"})))
    return Message(self, data)

