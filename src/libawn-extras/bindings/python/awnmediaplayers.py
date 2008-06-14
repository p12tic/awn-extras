# !/usr/bin/python

# Copyright (c) 2007 Randal Barlow <im.tehk at gmail.com>
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


import sys, os
import gobject
import pygtk
import gtk
from gtk import gdk
import awn
import dbus
import gconf
import string

try:import pydcop
except: ImportError


def what_app():
    player_name = None
    bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    if bus_obj.NameHasOwner('org.gnome.Rhythmbox') == True:
        player_name = "Rhythmbox"
    if bus_obj.NameHasOwner('org.exaile.DBusInterface') == True:
        player_name = "Exaile"
    if bus_obj.NameHasOwner('org.gnome.Banshee') == True:
        player_name = "Banshee"
    if bus_obj.NameHasOwner('org.bansheeproject.Banshee') == True:
        player_name = "BansheeOne"
    if bus_obj.NameHasOwner('org.gnome.Listen') == True:
        player_name = "Listen"
    if bus_obj.NameHasOwner('net.sacredchao.QuodLibet') == True:
        player_name = "QuodLibet"
    try:
        if pydcop.anyAppCalled("amarok") == None:pass
        else:player_name = "Amarok"
    except: SyntaxError
    return player_name


class GenericPlayer(object):
    """Insert the level of support here"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for GenericPlayer

        Provides self.player and any other interfaces needed by labeler and
        the button methods
        """
        #bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        #if bus_obj.NameHasOwner('org.gnome.Rhythmbox') == True:
        #    self.session_bus = dbus.SessionBus()
        #    self.proxy_obj = self.session_bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Player')
        #    self.player = dbus.Interface(self.proxy_obj, 'org.gnome.Rhythmbox.Player')
        #    self.player1 = self.session_bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Shell')
        pass

    def labeler(self, artOnOff, titleOrder, titleLen, titleBoldFont):
        """
        This method changes the application titles and album art

        Arguments
        * bool artOnOff = should the labeler return art locations? True or False
        * str titleOrder = 'artist - title' or 'title - artist'
        * int titleLen = length of the title
        * bool titleBoldFont = should the labeler use bold fonts via pango?

        Returns
        * str albumart_exact = the location of album art on the file system
        * str result = the title/album string
        * str result_tooltip = a result with no bolding and less len
        """
        #return albumart_exact, result, result_tooltip
        pass

    def button_previous_press (self):
        pass

    def button_pp_press (self):
        pass

    def button_next_press (self):
        pass


class Rhythmbox(GenericPlayer):
    """Full Support"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.gnome.Rhythmbox') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Player')
            self.player = dbus.Interface(self.proxy_obj, 'org.gnome.Rhythmbox.Player')
            self.player1 = self.session_bus.get_object('org.gnome.Rhythmbox', '/org/gnome/Rhythmbox/Shell')

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        self.albumart_general = ".gnome2/rhythmbox/covers/"
        self.dbus_driver()
        result = self.player.getPlayingUri()
        result = self.player1.getSongProperties(result)

        if self.artOnOff == 'on':
            albumart_exact = self.albumart_general + result['artist'] + ' - ' + result['album'] + ".jpg"

        # Currently Playing Title
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')

        return albumart_exact,result,result_tooltip

    def button_previous_press (self):
        self.player.previous ()

    def button_pp_press (self):
        self.player.playPause (1)

    def button_next_press (self):
        self.player.next ()



class Exaile(GenericPlayer):
    """Full Support for the Exaile media player

    Issues exist with play. It stops the player when pushed. Need further dbus info.
    """

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.exaile.DBusInterface') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.exaile.DBusInterface', '/DBusInterfaceObject')
            self.player = dbus.Interface(self.proxy_obj, "org.exaile.DBusInterface")

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        self.dbus_driver()

        # Currently Playing Title
        result = {}
        result['title'] = self.player.get_title()
        result['artist'] = self.player.get_artist()
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')

        return self.player.get_cover_path(),result,result_tooltip

    def button_previous_press (self):
        self.player.prev_track()

    def button_pp_press (self):
        self.player.play_pause()

    def button_next_press (self):
        self.player.next_track()


class Banshee(GenericPlayer):
    """Full Support for the banshee media player"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.gnome.Banshee') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.gnome.Banshee',"/org/gnome/Banshee/Player")
            self.player = dbus.Interface(self.proxy_obj, "org.gnome.Banshee.Core")

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        self.dbus_driver()

        # Currently Playing Title
        result = {}
        result['title'] = self.player.GetPlayingTitle()
        result['artist'] = self.player.GetPlayingArtist()
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')

        return self.player.GetPlayingCoverUri(),result,result_tooltip

    def button_previous_press (self):
        self.player.Previous()

    def button_pp_press (self):
        self.player.TogglePlaying ()

    def button_next_press (self):
        self.player.Next()


class BansheeOne(GenericPlayer):
    """Partial support for the banshee media player"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.bansheeproject.Banshee') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.bansheeproject.Banshee',"/org/bansheeproject/Banshee/PlayerEngine")
            self.proxy_obj1 = self.session_bus.get_object('org.bansheeproject.Banshee',"/org/bansheeproject/Banshee/PlaybackController")
            self.player = dbus.Interface(self.proxy_obj, "org.bansheeproject.Banshee.PlayerEngine")
            self.player1 = dbus.Interface(self.proxy_obj1, "org.bansheeproject.Banshee.PlaybackController")

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        self.dbus_driver()
        self.albumart_general = ".cache/album-art/"
        # Currently Playing Title
        info = self.player.GetCurrentTrack()
        result = {}
        result['title'] = str(info['name'])
        result['artist'] = str(info['artist'])
        if self.artOnOff == 'on':
            albumart_exact = self.albumart_general + result['artist'] + '-' + info['album'] + ".jpg"
            albumart_exact = albumart_exact.replace(' ','').lower()
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')
        return albumart_exact, result, result_tooltip

    def button_previous_press (self):
        self.player1.Previous(False)

    def button_pp_press (self):
        self.player.TogglePlaying ()

    def button_next_press (self):
        self.player1.Next(False)


class Listen(GenericPlayer):
    """Partial Support"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.gnome.Listen') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.gnome.Listen',"/org/gnome/listen")
            self.player = dbus.Interface(self.proxy_obj, "org.gnome.Listen")

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        self.dbus_driver()

        # Currently Playing Title
        result = {}
        result['title'] = self.player.current_playing().split(" - ",3)[0]
        result['artist'] = self.player.current_playing().split(" - ",3)[2]
        result['album'] = self.player.current_playing().split(" - ",3)[1][1:]
        albumart = os.environ['HOME'] + "/.listen/cover/" + result['artist'].lower() + "+" + result['album'].lower() + ".jpg"
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')
        return albumart,result,result_tooltip

    def button_previous_press (self):
        self.player.previous()

    def button_pp_press (self):
        self.player.play_pause ()

    def button_next_press (self):
        self.player.next()


class Amarok(GenericPlayer):
    """Not Working"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for Amarok
        """
        if pydcop.anyAppCalled("amarok") == None:pass
        else:self.player = pydcop.anyAppCalled("amarok").player

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        self.dbus_driver()

        # Currently Playing Title
        result = {}
        result['title'] = self.player.title ()
        result['artist'] = self.player.artist ()
        result['album'] = self.player.album ()
        albumart = self.player.coverImage()
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')
        return albumart,result,result_tooltip

    def button_previous_press (self):
        self.player.prev()

    def button_pp_press (self):
        self.player.playPause()

    def button_next_press (self):
        self.player.next()


class QuodLibet(GenericPlayer):
    """Full Support"""

    def __init__(self):
        self.dbus_driver()

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('net.sacredchao.QuodLibet') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('net.sacredchao.QuodLibet', '/net/sacredchao/QuodLibet')
            self.player = dbus.Interface(self.proxy_obj, 'net.sacredchao.QuodLibet')

    def labeler(self,artOnOff,titleOrder,titleLen,titleBoldFont):
        """
        This method changes the application titles and album art
        """
        self.artOnOff = artOnOff
        self.titleOrder = titleOrder
        self.titleLen = titleLen
        self.titleBoldFont = titleBoldFont
        # You need to activate the "Picture Saver" plugin in QuodLibet
        albumart_exact = os.environ["HOME"] + "/.quodlibet/current.cover"
        self.dbus_driver()
        result = self.player.CurrentSong()

        # Currently Playing Title
        if self.titleOrder == 'artist - title':
            try:result = result['artist'] + ' - ' + result['title']
            except:SyntaxError
        elif self.titleOrder == 'title - artist':
            try:result = result['title'] + ' - ' + result['artist']
            except:SyntaxError
        if result.__len__() > self.titleLen:
            result = result[:self.titleLen]
            result = result + '..'
        if self.titleBoldFont == 'on':
            result = """<span weight="bold">""" + result + """</span>"""
        result_tooltip = result.replace("""</span>""",'')
        result_tooltip = result_tooltip.replace("""<span weight="bold">""",'')

        return albumart_exact,result,result_tooltip

    def button_previous_press (self):
        self.player.Previous ()

    def button_pp_press (self):
        self.player.PlayPause ()

    def button_next_press (self):
        self.player.Next ()
