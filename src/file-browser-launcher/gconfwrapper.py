#! /usr/bin/env python
# -*- coding:utf-8 -*-
#
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
#File Browser Launcher
#AwnConfigClient wrapper file

import awn
class AwnCCWrapper:
  
  def __init__(self,uid):
    self.instance_client = awn.Config('file-browser-launcher', str(uid))
    self.default_client = awn.Config('file-browser-launcher', None)
  
  #Get an AwnConfigClient string
  def get_string(self,key,default):
    if self.instance_client.exists(awn.CONFIG_DEFAULT_GROUP, key):
      val = self.instance_client.get_string(awn.CONFIG_DEFAULT_GROUP,key)
      if val==None:
        return default
      return val
    else:
      val = self.default_client.get_string(awn.CONFIG_DEFAULT_GROUP,key)
      if val==None:
        return default
      return val

  #Set an AwnConfigClient string
  def set_string(self,key,val):
    val = self.default_client.set_string(awn.CONFIG_DEFAULT_GROUP,key,val)
    return val

  #Get an AwnConfigClient integer
  def get_int(self,key,default):
    if self.instance_client.exists(awn.CONFIG_DEFAULT_GROUP, key):
      val = self.instance_client.get_int(awn.CONFIG_DEFAULT_GROUP,key)
      if val==0:
        return default
      return val
    else:
      val = self.default_client.get_int(awn.CONFIG_DEFAULT_GROUP,key)
      if val==0:
        return default
      return val

  #Set an AwnConfigClient integer  
  def set_int(self,key,val):
    val = self.default_client.set_int(awn.CONFIG_DEFAULT_GROUP,key,val)
    return val
