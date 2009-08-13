
"""

Google Reader interface for Gwibber
Grillo (Diego Herrera) - 7/02/2009

bassed on RSS interface:
SegPhault (Ryan Paul) - 11/08/2008

"""

from . import can, support
import urlparse, logging, feedparser
import urllib, urllib2, re
import webbrowser

PROTOCOL_INFO = {
  "name": "Google Reader",
  "version": 0.1,

  "config": [
    "private:password",
    "username",
    "message_color",
    "receive_enabled",
  ],

  "features": [
    can.RECEIVE,
    can.READ,
  ],
}

feedparser._HTMLSanitizer.acceptable_elements = []

class Message:
  def __init__(self, client, data):
    self.client = client
    self.account = client.account
    self.protocol = client.account["protocol"]

    self.source = ""
    self.sender = data.get("author", "")

    if hasattr(data, "source"):
        self.source = data.source.get("title", "")
        self.sender = data.source.get("title", "")
        self.profile_url = data.source.link

    self.gr_id = data.get("id", "")

    self.image = "http://www.google.com/reader/ui/2296270177-logo-graphic.gif";
    self.sender_nick = data.get("author", "")
    self.sender_id = self.sender

    self.time = support.parse_time(data.updated)
    self.bgcolor = "message_color"
    self.url = data.get("link", "")

    if(self.source == ""):
        self.title = self.sender
    else:
        self.title = "%s <small>By %s</small>" % (self.source, self.sender)

    self.is_unread = True
    self.categories = []

    for category in data.tags:
      if( (category.term.find("user/")>=0) and (category.term.find("/state/")>=0) and (category.label=='read') ):
        self.is_unread = False
      elif((category.term.find("user/")>=0) and (category.term.find("/label/")>=0)):
        self.categories.append(category.label)

    self.summary = data.get("summary", "")
    self.html_string = data.title

    if(len(self.summary) > 0):
      self.text = self.summary
    else:
      self.text = data.source.get("title", "")

class Client:
    def __init__(self, acct):
        self.account = acct
        if(self.account["session"]!= None):
            self.sid = self.account["session"]
        else:
            self.get_auth()


    def get_auth(self):
        header = {'User-agent' : 'Gwibber'}
        post_data = urllib.urlencode({ 'Email': self.account["username"],
                                       'Passwd': self.account["private:password"],
                                       'service': 'reader',
                                       'source': 'Gwibber',
                                       'continue': 'http://www.google.com', })

        request = urllib2.Request('https://www.google.com/accounts/ClientLogin',
                                  post_data,
                                  header)
        try :
            f = urllib2.urlopen( request )
            res = f.read()
        except:
            raise
        self.sid = re.search('SID=(\S*)', res).group(1)
        self.account["session"] = self.sid

    def get_results(self,url, data = None,  count = 0):
        header ={'User-agent' : 'Gwibber',
                 'Cookie': 'Name=SID;SID=%s;Domain=.google.com;Path=/;Expires=160000000000' % self.sid}
        request = urllib2.Request(url, data, header)
        try :
            f = urllib2.urlopen( request )
            if(f.url != url):
                self.get_auth()
                if(count < 3):
                    res = self.get_results(url, data, count+1)
                else:
                    res = None
            else:
                res = f.read()
        except:
            res = None
        return res

    def read_message(self, message):
        webbrowser.open (message.url)
        if message.is_unread:
            token = self.get_results('http://www.google.com/reader/api/0/token')
            post_data = urllib.urlencode ({ 'i' : message.gr_id,
                                            'T' : token,
                                            'ac' : 'edit-tags' ,
                                            'a' : 'user/-/state/com.google/read' })

            url = 'http://www.google.com/reader/api/0/edit-tag'
            self.get_results(url, post_data)
            message.is_unread = False
            return True
        return False

    def get_messages(self):
        return feedparser.parse(
            self.get_results(
            'http://www.google.com/reader/atom/user/-/state/com.google/reading-list?n=%s' % '20' if (self.account["receive_count"] == None) else self.account["receive_count"])).entries

    def receive(self):
        for data in self.get_messages():
            yield Message(self, data)
