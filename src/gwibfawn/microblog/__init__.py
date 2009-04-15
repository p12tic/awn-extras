
import operator, traceback 
from . import can
from . import twitter, jaiku, identica, laconica, pownce
from . import digg, flickr, brightkite, rss, pingfm, facebook
from . import greader

# i18n magic
import gettext

_ = gettext.lgettext

PROTOCOLS = {
  "jaiku": jaiku,
  "digg": digg,
  "twitter": twitter,
  "facebook": facebook,
  "flickr": flickr,
  #"pownce": pownce,
  "identica": identica,
  "laconica": laconica,
  "rss": rss,
  "pingfm": pingfm,
  "greader": greader,
  #"brightkite": brightkite,
}

def supports(a, feature):
  return feature in PROTOCOLS[a["protocol"]].PROTOCOL_INFO["features"]

class Client:
  def __init__(self, accounts):
    self.accounts = accounts

  def handle_error(self, acct, err, msg = None):
    pass

  def post_process_message(self, message):
    return message

  def get_data(self, test, method, name, filter=list(PROTOCOLS.keys()), return_value=True, first_only=False):
    for acct in self.accounts:
      if acct["protocol"] in list(PROTOCOLS.keys()) and \
         acct["protocol"] in filter:
        try:
          client = PROTOCOLS[acct["protocol"]].Client(acct)
          if test(acct):
            if return_value:
              for message in method(client):
                yield self.post_process_message(message)
            else:
              yield method(client)
              if first_only: break
        except: self.handle_error(acct, traceback.format_exc(), name)

  def perform_operation(self, test, method, name, filter=list(PROTOCOLS.keys())):
    data = list(self.get_data(test, method, name, filter))
    data.sort(key=operator.attrgetter("time"), reverse=True)
    return data

  def send(self, message, filter=list(PROTOCOLS.keys())):
    return list(self.get_data(
      lambda a: a["send_enabled"] and supports(a, can.SEND),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened 
      lambda c: c.send(message), _("send message"), filter, False))

  def send_thread(self, message, target, filter=list(PROTOCOLS.keys())):
    return list(self.get_data(
      lambda a: a["send_enabled"] and supports(a, can.THREAD_REPLY),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened 
      lambda c: c.send_thread(message, target), _("send message"), filter, False))

  def reply(self, message, filter=list(PROTOCOLS.keys())):
    return list(self.get_data(
      lambda a: supports(a, can.SEND),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened       
      lambda c: c.send(message), _("send message"), filter, False, True))

  def thread(self, query, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.THREAD) and \
        a.id == query.account.id,
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened 
      lambda c: c.get_thread(query), _("retrieve thread"), filter)
  
  def responses(self, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.RESPONSES),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened 
      lambda c: c.responses(), _("retrieve responses"), filter)

  def receive(self, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.RECEIVE),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened 
      lambda c: c.receive(), _("retrieve messages"), filter)

  def friend_positions(self, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.GEO_FRIEND_POSITIONS),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened 
      lambda c: c.friend_positions(), _("retrieve positions"), filter)

  def search(self, query, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["search_enabled"] and supports(a, can.SEARCH),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened       
      lambda c: c.search(query), _("perform search query"), filter)

  def search_url(self, query, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["search_enabled"] and supports(a, can.SEARCH_URL),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened       
      lambda c: c.search_url(query), _("perform search query"), filter)

  def tag(self, query, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.TAG),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened       
      lambda c: c.tag(query.lower().replace("#", "")), _("perform tag query"), filter)

  def user_messages(self, screen_name, account_id, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.USER_MESSAGES) and \
        a.id == account_id,
      lambda c: c.user_messages(screen_name), "perform user_messages query", filter)

  def group(self, query, filter=list(PROTOCOLS.keys())):
    return self.perform_operation(
      lambda a: a["receive_enabled"] and supports(a, can.GROUP),
      # Translators: this message appears in the Errors dialog
      # Indicates with wich action the error happened       
      lambda c: c.group(query.lower().replace("!", "")), _("perform group query"), filter)
