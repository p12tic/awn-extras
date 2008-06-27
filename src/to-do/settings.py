# -*- coding: utf-8 -*-
# Copyright (c) 2008 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.
#
#A class to sort of act like a daemon for the GConf settings  
class Settings:
  def __init__(self,prefix=''):
    
    #Parse the prefix
    if prefix!='':
      if prefix[-1]!='/':
        self.prefix = prefix+'/'
      else:
        self.prefix = prefix
    else:
      self.prefix = prefix
    
    import gconf
    self._client = gconf.client_get_default()
    self._values = {} #{key:value,key:value,etc:etc}
    self._registered = {} #{key:type,key:type,etc:etc}
    self._connects = {} #{key:[[func,arg],[func,arg]],key:[[func,arg],[func,arg]]}
  
  #A function to add another value to the registered dictionary -- includes the type
  def register(self,dictionary):
    for string,valtype in dictionary.items():
      try:#String has been registered -- no action necessary
        self._registered[string]
      except:#String has not been registered -- register it
        self._registered[string] = valtype
        self.get(string)
  
  #A function to get the value of a key -- assumes that <string> has already been registered
  def get(self,string):
    import gconf
    try:#Has been fetched from GConf -- return the value
      self._values[string]
      return self._values[string]
    except:#Has not been fetched from GConf -- fetch it and return the value
      if self._registered[string] in ['string','str',str]:
        self._values[string] = self._client.get_string(self.prefix+string)
      elif self._registered[string] in ['integer','int',int]:
        self._values[string] = self._client.get_int(self.prefix+string)
      elif self._registered[string] in ['float',float]:
        self._values[string] = self._client.get_float(self.prefix+string)
      elif self._registered[string] in ['boolean','bool',bool]:
        self._values[string] = self._client.get_bool(self.prefix+string)
      elif self._registered[string] in ['list-string','list-str',['string'],['str'],[str]]:
        self._values[string] = self._client.get_list(self.prefix+string,gconf.VALUE_STRING)
      elif self._registered[string] in ['list-integer','list-int',['integer'],['int'],[int]]:
        self._values[string] = self._client.get_list(self.prefix+string,gconf.VALUE_INT)
      elif self._registered[string] in ['list-boolean','list-bool',['boolean'],['bool'],[bool]]:
        self._values[string] = self._client.get_list(self.prefix+string,gconf.VALUE_BOOL)
      else:#Error when registering the key (setting the type)
        print "KEY TYPE ERROR for %s" % string
        return "KEY TYPE ERROR for %s" % string
      
      #Set the functions to call for when <string> is changed as an empty list
      self._connects[string] = []
      
      #Return the value
      return self._values[string]
  
  #A function to call self.get -- in case someone messes up
  def get_value(self,string):
    self.get(string)
  
  #A function to set the value of a key -- assumes that <string> has already been registered and the <value> is the
  #same type as when registered
  def set(self,string,value):
    import gconf
    #Set the GConf value first
    if self._registered[string] in ['string','str',str]:
      self._client.set_string(self.prefix+string,value)
    elif self._registered[string] in ['integer','int',int]:
      self._client.set_int(self.prefix+string,value)
    elif self._registered[string] in ['float',float]:
      self._client.set_float(self.prefix+string,value)
    elif self._registered[string] in ['boolean','bool',bool]:
      self._client.set_bool(self.prefix+string,value)
    elif self._registered[string] in ['list-string','list-str',['string'],['str'],[str]]:
      self._client.set_list(self.prefix+string,gconf.VALUE_STRING,value)
    elif self._registered[string] in ['list-integer','list-int',['integer'],['int'],[int]]:
      self._client.set_list(self.prefix+string,gconf.VALUE_INT,value)
    elif self._registered[string] in ['list-boolean','list-bool',['boolean'],['bool'],[bool]]:
      self._client.set_list(self.prefix+string,gconf.VALUE_BOOL,value)
    else:
      print "KEY TYPE ERROR for %s" % self._registered[string]
      return "KEY TYPE ERROR for %s" % self._registered[string]
    
    #Set the value (internally)
    self._values[string] = value
    
    #Last, go through any functions set to call for when <string> is changed
    for x in self._connects[string]:
      x[0](string,value,*x[1],**x[2])
  
  #A function to call set.set -- in case someone messes up
  def set_value(self,string,value):
    self.set(string,value)
  
  #A function to set a function to be called when one of <strings> is changed
  #<arg> is an optional parameter which will be passed to the function, if called
  #This assumes that each of <strings> has been registered
  def connect(self,strings,function,*args1,**args2):
    if type(strings)==type(''):#<strings> is a single string
      self._connects[strings].append([function,args1,args2])
    else:#Assume that <strings> is a list of strings
      for x in strings:
        self._connects[x].append([function,args1,args2])
  
  #In case the user wants to get a value via <settingsinstance>[<key>]
  def __getitem__(self,key):
    return self.get(key)
  
  #In case the user wants to set a value via <settingsinstance>[<key>] = ...
  def __setitem__(self,key,value):
    return self.set(key,value)
