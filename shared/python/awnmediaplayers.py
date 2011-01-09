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


import sys
import os
import subprocess
import atexit

import gobject
import pygtk
import gtk
from gtk import gdk

import awn
import dbus
from dbus.mainloop.glib import DBusGMainLoop
import string

try:
    import mutagen.mp3
    import mutagen.mp4
    from mutagen.id3 import ID3
    import tempfile
    album_art_file = "%s/awnmediaplayer_%s.png" % (tempfile.gettempdir(), os.getenv('USERNAME'))
    art_icon_from_tag = True
except ImportError:
    art_icon_from_tag = False

DBusGMainLoop(set_as_default=True)



def cleanup():
    if art_icon_from_tag:
        try:
            os.remove(album_art_file)
        except OSError:
            pass

atexit.register(cleanup)


def get_app_name():
    player_name = None
    bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
    if bus_obj.NameHasOwner('org.gnome.Rhythmbox') == True:
        player_name = "Rhythmbox"
    elif bus_obj.NameHasOwner('org.exaile.DBusInterface') == True:
        player_name = "Exaile"
    elif bus_obj.NameHasOwner('org.gnome.Banshee') == True:
        player_name = "Banshee"
    elif bus_obj.NameHasOwner('org.bansheeproject.Banshee') == True:
        player_name = "BansheeOne"
    elif bus_obj.NameHasOwner('org.gnome.Listen') == True:
        player_name = "Listen"
    elif bus_obj.NameHasOwner('net.sacredchao.QuodLibet') == True:
        player_name = "QuodLibet"
    elif bus_obj.NameHasOwner('org.mpris.songbird') == True:
        player_name = "Songbird"
    elif bus_obj.NameHasOwner('org.mpris.vlc') == True:
        player_name = "VLC"
    elif bus_obj.NameHasOwner('org.mpris.audacious') == True:
        player_name = "Audacious"
    elif bus_obj.NameHasOwner('org.mpris.bmp') == True:
        player_name = "BMP"
    elif bus_obj.NameHasOwner('org.mpris.xmms2') == True:
        player_name = "XMMS2"
    elif bus_obj.NameHasOwner('org.mpris.amarok') == True:
        player_name = "Amarok"
    elif bus_obj.NameHasOwner('org.mpris.aeon') == True:
        player_name = "Aeon"
    elif bus_obj.NameHasOwner('org.mpris.dragonplayer') == True:
        player_name = "DragonPlayer"
    elif bus_obj.NameHasOwner('org.freedesktop.MediaPlayer') == True:
        player_name = "mpDris"
    elif bus_obj.NameHasOwner('org.mpris.clementine') == True:
        player_name = "Clementine"
    elif bus_obj.NameHasOwner('org.mpris.guayadeque') == True:
        player_name = "Guayadeque"
    return player_name


def player_available(executable):
    """Check if player is installed if it's not in 'Activatable Services' on DBus"""

    for path in os.getenv('PATH').split(':'):
        if path == '':
            continue
        if os.path.isfile(os.path.join(path, executable)):
            return True
    return False


def launch_player(args):
    """Launch player if this can't be done via DBus"""

    try:
        subprocess.Popen(args)
    except OSError, e:
        print "awnmediaplayer: error launching %s: %s" % (args, e)
        return False
    return True


class GenericPlayer(object):
    """Insert the level of support here"""

    def __init__(self, dbus_name=None):
        # set signalling_supported to True in your subclass's constructor if you use signal(s) which are received when currently played song changes (e.g. playingUriChanged signal)
        self.signalling_supported = False
        # set to DBus service name string in your subclass
        self.dbus_base_name = dbus_name
        self.song_change_cb = None
        self.playing_changed_cb = None
        self.dbus_driver()

    def set_song_change_callback(self, cb):
        self.song_change_cb = cb

    def set_playing_changed_callback(self, cb):
        self.playing_changed_cb = cb

    def song_changed_emitter(self, *args, **kwargs):
        if (self.song_change_cb):
            self.song_change_cb()

    def playing_changed_emitter(self, playing):
        if (self.playing_changed_cb):
            self.playing_changed_cb(playing)

    def is_async(self):
        """
        Returns True if this player class supports song change signalling.
        """
        return self.signalling_supported

    def is_available(self):
        """
        Returns true if this player is present on the system.
        Override if necessary.
        """
        if (self.dbus_base_name != None):
            bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
            ACTIVATABLE_SERVICES = bus_obj.ListActivatableNames()
            return self.dbus_base_name in ACTIVATABLE_SERVICES
        return False

    def start(self):
        """
        Starts given player.
        Override if necessary.
        """
        if (self.dbus_base_name != None):
            object_path = '/' + self.dbus_base_name.replace('.', '/')
            bus = dbus.SessionBus()
            obj = bus.get_object(self.dbus_base_name, object_path)
            return True
        else:
            return False

    def get_dbus_name(self):
        """
        Returns player's dbus name.
        """
        return self.dbus_base_name

    def dbus_driver(self):
        """
        Defining the dbus location for GenericPlayer

        Provides self.player and any other interfaces needed by get_media_info
        and the button methods
        """
        pass

    def get_media_info(self):
        """
        This method tries to get information about currently playing media

        Returns
        * dict result = dictionary of various information about media
            (should always have at least the 'title' key)
        """
        return {}

    def is_playing(self):
        """
        This method determines if the player is currently in 'playing' state
        as opossed to 'paused' / 'stopped'
        """
        return False

    def previous(self):
        pass

    def play_pause(self):
        pass

    def next(self):
        pass

    def play_uri(self, uri):
        """
        Immediately starts playing the specified URI.
        """
        return False

    def enqueue_uris(self, uris):
        """
        Adds uris to current playlist.
        """
        return False


class MPRISPlayer(GenericPlayer):
    """ a default implementation of MPRIS """

    def __init__(self, interface):
        GenericPlayer.__init__(self, interface)
        self.signalling_supported = True

    def playing_changed_emitter(self, playing):
        print "Status Change: ", playing
        if (self.playing_changed_cb):
            self.playing_changed_cb(playing[0] == 0)

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner(self.dbus_base_name) == True:
            self.session_bus = dbus.SessionBus()
            self.player = self.session_bus.get_object(self.dbus_base_name, '/Player')
            self.player.connect_to_signal('TrackChange', self.song_changed_emitter, member_keyword='member')
            self.player.connect_to_signal('StatusChange', self.playing_changed_emitter)

    def get_media_info(self):
        self.dbus_driver()

        # Get information about song
        info = self.player.GetMetadata()

        result = {}
        if 'title' in info.keys():
            result['title'] = str(info['title'])
        elif 'location' in info.keys():
            pos = info['location'].rfind("/")
            if pos is not -1:
                result['title'] = str(info['location'][pos + 1:])
            else:
                result['title'] = ''
        else:
            result['title'] = ''

        if 'artist' in info.keys():
            result['artist'] = str(info['artist'])

        if 'album' in info.keys():
            result['album'] = str(info['album'])

        if 'arturl' in info:
            if info['arturl'][0:7] == "file://":
                result['album-art'] = str(info['arturl'][7:])
                if gtk.gtk_version >= (2, 18):
                    from urllib import unquote
                    result['album-art'] = unquote(result['album-art'])
            else:
                print "Don't understand the album art location: %s" % info['arturl']

        return result

    def is_playing(self):
        self.dbus_driver()

        stat = self.player.GetStatus()
        return stat[0] == 0

    def previous(self):
        self.player.Prev()

    def play_pause(self):
        stat = self.player.GetStatus()
        if stat[0] != 2:
            self.player.Pause()
        else:
            self.player.Play()

    def next(self):
        self.player.Next()


class Rhythmbox(GenericPlayer):
    """Full Support with signals"""

    def __init__(self):
        GenericPlayer.__init__(self, 'org.gnome.Rhythmbox')
        self.signalling_supported = True
        self._is_playing = False

    def dbus_driver(self):
        """
        Defining the dbus location for Rhythmbox
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        self._is_playing = False
        if bus_obj.NameHasOwner(self.dbus_base_name) == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object(self.dbus_base_name, '/org/gnome/Rhythmbox/Player')
            self.player = dbus.Interface(self.proxy_obj, 'org.gnome.Rhythmbox.Player')
            self.player.connect_to_signal('playingUriChanged', self.song_changed_emitter, member_keyword='member')
            self.player.connect_to_signal('playingSongPropertyChanged', self.song_changed_emitter, member_keyword='member')
            self.player.connect_to_signal('playingChanged', self.playing_changed_emitter)
            self.rbShell = self.session_bus.get_object(self.dbus_base_name, '/org/gnome/Rhythmbox/Shell')

            self._is_playing = self.player.getPlaying()

    def get_media_info(self):
        self.dbus_driver()
        ret_dict = {}
        playinguri = self.player.getPlayingUri()
        result = self.rbShell.getSongProperties(playinguri)

        # Currently Playing Title
        if result['artist'] != '':
            ret_dict['artist'] = result['artist']
            ret_dict['title'] = result['title']
            if 'album' in result:
                ret_dict['album'] = result['album']
        elif 'rb:stream-song-title' in result:
            if result['title'] != '':
                ret_dict['title'] = result['rb:stream-song-title'] + ' (' + result['title'] + ')'
            else:
                ret_dict['title'] = result['rb:stream-song-title']
        elif 'title' in result:
            ret_dict['title'] = result['title']

        # cover-art
        if 'rb:coverArt-uri' in result:
            albumart_exact = result['rb:coverArt-uri']
            # bug in rhythmbox 0.11.6 - returns uri, but not properly encoded,
            # but it's enough to remove the file:// prefix
            albumart_exact = albumart_exact.encode('utf8').replace('file://', '', 1)
            if gtk.gtk_version >= (2, 18):
                from urllib import unquote
                albumart_exact = unquote(albumart_exact)
            ret_dict['album-art'] = albumart_exact
            return ret_dict

        # perhaps it's in the cache folder
        if 'album' in result and 'artist' in result:
            cache_dir = os.path.expanduser("~/.cache/rhythmbox/covers")
            cache_file = '%s/%s - %s.jpg' % (cache_dir, result['artist'], result['album'])
            if os.path.isfile(cache_file):
                ret_dict['album-art'] = cache_file
                return ret_dict

        # The following is taken and adapted from Dockmanager, including todo
        # Copyright (C) 2009-2010 Jason Smith, Rico Tzschichholz, Robert Dyer

        # Look in song folder
        # TODO need to replace some things, this is very weird
        filename = playinguri.encode('utf8').replace('file://', '', 1)
        if gtk.gtk_version >= (2, 18):
            from urllib import unquote
            filename = unquote(filename)
        coverdir = os.path.dirname(filename)
        covernames = ["cover.jpg", "cover.png", "Cover.jpg", "Cover.png",
                      "album.jpg", "album.png", "Album.jpg", "Album.png",
                      "albumart.jpg", "albumart.png", "Albumart.jpg",
                      "Albumart.png", "AlbumArt.jpg", "AlbumArt.png",
                      ".folder.jpg", ".folder.png", ".Folder.jpg",
                      ".Folder.png", "folder.jpg", "folder.png",
                      "Folder.jpg", "Folder.png"]
        for covername in covernames:
            coverfile = os.path.join(coverdir, covername)
            if os.path.isfile(coverfile):
                ret_dict['album-art'] = coverfile
                return ret_dict

        # Look for image in tags
        if art_icon_from_tag and 'mimetype' in result:
            image_data = None
            if result['mimetype'] == "application/x-id3":
                try:
                    f = ID3(filename)
                    apicframes = f.getall("APIC")
                    if len(apicframes) >= 1:
                        frame = apicframes[0]
                        image_data = frame.data
                except:
                    pass
            elif result['mimetype'] == "audio/x-aac":
                try:
                    f = mutagen.mp4.MP4(filename)
                    if "covr" in f.tags:
                        covertag = f.tags["covr"][0]
                        image_data = covertag
                except:
                    pass
            if image_data:
                try:
                    loader = gtk.gdk.PixbufLoader()
                    loader.write(image_data)
                    loader.close()
                    loader.get_pixbuf().save(album_art_file, "png", {})
                    ret_dict['album-art'] = album_art_file
                except:
                    pass

        return ret_dict

    def is_playing(self):
        self.dbus_driver()
        return self._is_playing

    def previous(self):
        self.player.previous()

    def play_pause(self):
        self.player.playPause(1)

    def next(self):
        self.player.next()

    def play_uri(self, uri):
        # unfortunatelly this only works for items present in media library
        self.rbShell.loadURI(uri, True)
        return True

    def enqueue_uris(self, uris):
        # unfortunatelly this only works for items present in media library
        for uri in uris:
            self.rbShell.addToQueue(uri)
        return True


class Exaile(GenericPlayer):
    """Full Support for the Exaile media player
    No signals as of Exaile 0.2.11

    Issues exist with play. It stops the player when pushed. Need further dbus info.
    """

    def __init__(self):
        GenericPlayer.__init__(self, 'org.exaile.DBusInterface')

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.exaile.DBusInterface') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.exaile.DBusInterface', '/DBusInterfaceObject')
            self.player = dbus.Interface(self.proxy_obj, "org.exaile.DBusInterface")

    def get_media_info(self):
        self.dbus_driver()

        # Currently Playing Title
        result = {}
        result['title'] = self.player.get_title()
        result['artist'] = self.player.get_artist()
        result['album'] = self.player.get_album()
        result['album-art'] = self.player.get_cover_path()

        return result

    def previous(self):
        self.player.prev_track()

    def play_pause(self):
        self.player.play_pause()

    def next(self):
        self.player.next_track()

    def play_uri(self, uri):
        self.player.play_file(uri)
        return True

    def enqueue_uris(self, uris):
        for uri in uris:
            self.player.play_file(uri)
        return True


class Banshee(GenericPlayer):
    """Full Support for the banshee media player
    No signals as of Banshee 0.13.2
    """

    def __init__(self):
        GenericPlayer.__init__(self, 'org.gnome.Banshee')

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.gnome.Banshee') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.gnome.Banshee', "/org/gnome/Banshee/Player")
            self.player = dbus.Interface(self.proxy_obj, "org.gnome.Banshee.Core")

    def get_media_info(self):
        self.dbus_driver()

        # Currently Playing Title
        result = {}
        result['title'] = self.player.GetPlayingTitle()
        result['artist'] = self.player.GetPlayingArtist()
        #result['album'] = self.player.GetPlayingAlbum() #FIXME: does it exist?
        result['album-art'] = self.player.GetPlayingCoverUri()

        return result

    def previous(self):
        self.player.Previous()

    def play_pause(self):
        self.player.TogglePlaying()

    def next(self):
        self.player.Next()

    def play_uri(self, uri):
        self.player.EnqueueFiles([uri])
        return True

    def enqueue_uris(self, uris):
        self.player.EnqueueFiles(uris)
        return True


class BansheeOne(GenericPlayer):
    """Partial support for the banshee media player"""

    def __init__(self):
        GenericPlayer.__init__(self, 'org.bansheeproject.Banshee')
        self.signalling_supported = True
        self._is_playing = False

    def dbus_driver(self):
        """
        Defining the dbus location for Banshee
        """
        self._is_playing = False
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.bansheeproject.Banshee') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.bansheeproject.Banshee', "/org/bansheeproject/Banshee/PlayerEngine")
            self.proxy_obj1 = self.session_bus.get_object('org.bansheeproject.Banshee', "/org/bansheeproject/Banshee/PlaybackController")
            self.player = dbus.Interface(self.proxy_obj, "org.bansheeproject.Banshee.PlayerEngine")
            self.player1 = dbus.Interface(self.proxy_obj1, "org.bansheeproject.Banshee.PlaybackController")
            self.player.connect_to_signal('EventChanged', self.event_changed, member_keyword='member')

            self._is_playing = self.player.GetCurrentState() == 'playing'

    def event_changed(self, *args, **kwargs):
        self.song_changed_emitter()

        playing = False
        try:
            # careful for dbus exceptions
            playing = self.player.GetCurrentState() == 'playing'
        except:
            pass

        if (playing != self._is_playing):
            self.playing_changed_emitter(playing)
            self._is_playing = playing

    def get_media_info(self):
        self.dbus_driver()
        result = {}

        self.albumart_general = os.environ['HOME'] + "/.cache/media-art/"
        self.albumart_general2 = os.environ['HOME'] + "/.cache/album-art/"

        # Currently Playing Title
        info = self.player.GetCurrentTrack()

        if 'name' in info.keys():
            result['title'] = str(info['name'])
        else:
            result['title'] = ''

        if 'artist' in info.keys():
            result['artist'] = str(info['artist'])

        if 'album' in info.keys():
            result['album'] = str(info['album'])

        if 'artwork-id' in info:
            result['album-art'] = '%s.jpg' % (self.albumart_general + info['artwork-id'])
            if not os.path.isfile(result['album-art']):
                result['album-art'] = '%s.jpg' % (self.albumart_general2 + info['artwork-id'])
        elif 'album' in info and 'artist' in result:
            albumart_exact = '%s-%s.jpg' % (self.albumart_general + result['artist'], info['album'])
            result['album-art'] = albumart_exact.replace(' ', '').lower()

        return result

    def is_playing(self):
        self.dbus_driver()
        return self._is_playing

    def previous(self):
        self.player1.Previous(False)

    def play_pause(self):
        self.player.TogglePlaying()

    def next(self):
        self.player1.Next(False)


class Listen(GenericPlayer):
    """Partial Support"""

    def __init__(self):
        GenericPlayer.__init__(self, 'org.gnome.Listen')

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('org.gnome.Listen') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('org.gnome.Listen', "/org/gnome/listen")
            self.player = dbus.Interface(self.proxy_obj, "org.gnome.Listen")

    def get_media_info(self):
        self.dbus_driver()
        result = {}

        # Currently Playing Title
        try:
            # Version => 0.6
            result['title'] = self.player.get_title()
            if result['title'] == None:  # if paused
                result['title'] = ''
            result['artist'] = self.player.get_artist()
            result['album'] = self.player.get_album()
            result['album-art'] = self.player.get_cover_path()
        except:
            # Version == 0.5
            # A single string of this pattern: Title - (Album - Artist)
            # Streaming media can have less fields
            result['title'] = self.player.current_playing().split(" - ", 3)[0]
            try:
                result['album'] = self.player.current_playing().split(" - ", 3)[1][1:]
                result['artist'] = self.player.current_playing().split(" - ", 3)[2][:-1]
                result['album-art'] = os.environ['HOME'] + "/.listen/cover/" + result['artist'].lower() + "+" + result['album'].lower() + ".jpg"
            except IndexError:
                pass

        return result

    def previous(self):
        self.player.previous()

    def play_pause(self):
        self.player.play_pause()

    def next(self):
        self.player.next()

    def play_uri(self, uri):
        self.player.play([uri])
        return True

    def enqueue_uris(self, uris):
        self.player.enqueue(uris)
        return True


class QuodLibet(GenericPlayer):
    """Full Support with signals"""  # (but not implemented yet)

    def __init__(self):
        GenericPlayer.__init__(self, 'net.sacredchao.QuodLibet')

    def dbus_driver(self):
        """
        Defining the dbus location for
        """
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner('net.sacredchao.QuodLibet') == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object('net.sacredchao.QuodLibet', '/net/sacredchao/QuodLibet')
            self.player = dbus.Interface(self.proxy_obj, 'net.sacredchao.QuodLibet')

    def get_media_info(self):
        # You need to activate the "Picture Saver" plugin in QuodLibet
        albumart_exact = os.environ["HOME"] + "/.quodlibet/current.cover"
        self.dbus_driver()

        # Currently Playing Title
        result = self.player.CurrentSong()

        result['album-art'] = albumart_exact

        return albumart_exact, markup, tooltip

    def previous(self):
        self.player.Previous()

    def play_pause(self):
        self.player.PlayPause()

    def next(self):
        self.player.Next()


class Songbird(MPRISPlayer):
    """Discontinued in 2010"""

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.songbird')


class VLC(MPRISPlayer):

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.vlc')

    def is_available(self):
        return player_available('vlc')

    def start(self):
        return launch_player(['vlc', '--control', 'dbus'])


class Audacious(MPRISPlayer):

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.audacious')

    def is_available(self):
        return player_available('audacious')

    def start(self):
        return launch_player('audacious')


class BMP(MPRISPlayer):
    """Beep Media Player, discontinued"""

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.bmp')


class XMMS2(MPRISPlayer):

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.xmms2')


class Amarok(MPRISPlayer):
    """Amarok 2.0 +"""

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.amarok')

    def is_available(self):
        return player_available('amarok')

    def start(self):
        return launch_player('amarok')


class Aeon(MPRISPlayer):
    """Discontinued"""

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.aeon')


class DragonPlayer(MPRISPlayer):
    """ FIXME: Doesn't work: bus path is org.mpris.dragonplayer-XXXXX """

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.dragonplayer')


class mpDris(MPRISPlayer):
    """ mpDris is an implementation of the XMMS2 media player interface MPRIS as a client for MPD. """

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.freedesktop.MediaPlayer')


class Clementine(MPRISPlayer):

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.clementine')

    def is_available(self):
        return player_available('clementine')

    def start(self):
        return launch_player('clementine')

    def previous(self):
        self.player.Prev()
        # We have to emit song changed signal ourselves (Clementine 0.5)
        self.song_changed_emitter()

    def next(self):
        self.player.Next()
        # We have to emit song changed signal ourselves (Clementine 0.5)
        self.song_changed_emitter()


class Guayadeque(MPRISPlayer):

    def __init__(self):
        MPRISPlayer.__init__(self, 'org.mpris.guayadeque')

    def dbus_driver(self):
        bus_obj = dbus.SessionBus().get_object('org.freedesktop.DBus', '/org/freedesktop/DBus')
        if bus_obj.NameHasOwner(self.dbus_base_name) == True:
            self.session_bus = dbus.SessionBus()
            self.proxy_obj = self.session_bus.get_object(self.dbus_base_name, '/Player')
            self.player = dbus.Interface(self.proxy_obj, 'org.freedesktop.MediaPlayer')
            self.player.connect_to_signal('TrackChange', self.song_changed_emitter, member_keyword='member')
            self.player.connect_to_signal('StatusChange', self.playing_changed_emitter)

    def is_available(self):
        return player_available('guayadeque')

    def start(self):
        return launch_player('guayadeque')
