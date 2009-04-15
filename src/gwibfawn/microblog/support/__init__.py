
"""

Microblog support methods
SegPhault (Ryan Paul) - 07/25/2008

"""

from . import facelib
import re, os, locale, mx.DateTime, urllib2

import gettext

_ = gettext.lgettext

def parse_time(t):

  loc = locale.getlocale(locale.LC_TIME)
  locale.setlocale(locale.LC_TIME, 'C')
  result = mx.DateTime.Parser.DateTimeFromString(t)
  locale.setlocale(locale.LC_TIME, loc)
  return result 

SCHEMES = ('http', 'https', 'ftp', 'mailto', 'news', 'gopher',
                'nntp', 'telnet', 'wais', 'prospero', 'aim', 'webcal')
URL_FORMAT = (r'(?<!\w)((?:%s):' # protocol + :
    '/*(?!/)(?:' # get any starting /'s
    '[\w$\+\*@&=\-/]' # reserved | unreserved
    '|%%[a-fA-F0-9]{2}' # escape
    '|[\?\.:\(\),;!\'\~](?!(?:\s|$))' # punctuation
    '|(?:(?<=[^/:]{2})#)' # fragment id
    '){2,}' # at least two characters in the main url part
    ')') % ('|'.join(SCHEMES),)
LINK_PARSE = re.compile(URL_FORMAT)

def linkify(t):
  return LINK_PARSE.sub('<a href="\\1">\\1</a>', t)

def highlight_search_results(t, q):
  pattern = re.compile(re.escape(q), re.I)
  return re.sub(pattern, ' <span class="searchresult">&nbsp;%s </span> ' % q, t)

def xml_escape(t):
  return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def truncate(text, count=10):
  return len(text) > count and "%s..." % text[:count+1] or text

def unshorten_url(url):
  return urllib2.urlopen("http://tweetbacks.appspot.com/tb?url=%s" % url).read().split()

def generate_time_string(t):
  if isinstance(t, str): return t

  d = mx.DateTime.gmt() - t

  # Aliasing the function doesn't work here with intltool...
  if d.days >= 365:
    years = round(d.days / 365)
    return gettext.ngettext("%(year)d year ago", "%(year)d years ago", years) % {"year": years}
  elif d.days >= 1 and d.days < 365:
    days = round(d.days)
    return gettext.ngettext("%(day)d day ago", "%(day)d days ago", days) % {"day": days}
  elif d.seconds >= 3600 and d.days < 1:
    hours = round(d.seconds / 60 / 60)
    return gettext.ngettext("%(hour)d hour ago", "%(hour)d hours ago", hours) % {"hour": hours}
  elif d.seconds < 3600 and d.seconds >= 60:
    minutes = round(d.seconds / 60)
    return gettext.ngettext("%(minute)d minute ago", "%(minute)d minutes ago", minutes) % {"minute": minutes}
  elif round(d.seconds) < 60:
    seconds = round(d.seconds)
    return gettext.ngettext("%(sec)d second ago", "%(sec)d seconds ago", seconds) % {"sec": seconds}
  else:
    return _("BUG: %s") % str(d)
