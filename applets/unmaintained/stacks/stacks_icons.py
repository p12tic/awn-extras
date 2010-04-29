#!/usr/bin/env python

# Copyright (c) 2007 Timon ter Braak
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

import os
import gnome.ui
import gio
import gtk
import urllib

# Borrowed Thumbnailer from "gimmie"
class Thumbnailer:

    def __init__(self, uri, mimetype):
        self.uri = uri or ""
        self.mimetype = mimetype or ""
        self.cached_icon = None
        self.cached_timestamp = None
        self.cached_size = None


    def get_icon(self, icon_size, timestamp = 0):
        if not self.cached_icon or \
                icon_size != self.cached_size or \
                timestamp != self.cached_timestamp:
            self.cached_icon = self._lookup_or_make_thumb(icon_size, timestamp)
            self.cached_icon = self.cached_icon.add_alpha (True, '\0', '\0', '\0')
            self.cached_size = icon_size
            self.cached_timestamp = timestamp
        return self.cached_icon


    def _lookup_or_make_thumb(self, icon_size, timestamp):
        icon_theme = gtk.icon_theme_get_default()
        thumb_factory = gnome.ui.ThumbnailFactory("normal")
        icon_name, icon_type = \
                gnome.ui.icon_lookup(icon_theme, thumb_factory, self.uri, self.mimetype, 0)
        try:
            if icon_type == gnome.ui.ICON_LOOKUP_RESULT_FLAGS_THUMBNAIL or \
                    thumb_factory.has_valid_failed_thumbnail(self.uri, timestamp):
                # Use existing thumbnail
                thumb = IconFactory().load_icon(icon_name, icon_size)
            elif self._is_local_uri(self.uri):
                # Generate a thumbnail for local files only
                thumb = thumb_factory.generate_thumbnail(self.uri, self.mimetype)
                thumb_factory.save_thumbnail(thumb, self.uri, timestamp)
                thumb = IconFactory().scale_to_bounded(thumb, icon_size)
            if thumb:
                # Fixup the thumbnail a bit
                thumb = self._nicer_dimensions(thumb)
                
                return thumb
        except:
            pass

        # Fallback to mime-type icon on failure
        thumb = IconFactory().load_icon(icon_name, icon_size)
        
        return thumb


    def _is_local_uri(self, uri):
        # NOTE: gnomevfs.URI.is_local seems to hang for some URIs (e.g. ssh
        #       or http).  So look in a list of local schemes which comes
        #       directly from gnome_vfs_uri_is_local_scheme.
        try:
            scheme = uri.split("://")[0]
            return not scheme or scheme in ("file", "help", "ghelp", "gnome-help", 
                "trash", "man", "info", "hardware", "search", "pipe","gnome-trash")
        except:
            return False


    def _nicer_dimensions(self, icon):
        ### Constrain thumb dimensions to 1:1.2
        if float(icon.get_height()) / float(icon.get_width()) > 1.2:
            return icon.subpixbuf(0, 0, icon.get_width(), int(icon.get_width() * 1.2))
        return icon


# Borrowed IconFactory from "gimmie"
class IconFactory:

    def load_icon_from_path(self, icon_path, icon_size = None):
        if os.path.isfile(icon_path):
            try:
                if icon_size:
                    # constrain height, not width
                    thumb = gtk.gdk.pixbuf_new_from_file_at_size(icon_path, -1, int(icon_size))
                    return thumb
                else:
                    thumb = gtk.gdk.pixbuf_new_from_file(icon_path)
                    return thumb
            except:
                pass
        return None


    def load_icon_from_data_dirs(self, icon_value, icon_size = None):
        data_dirs = None
        if os.environ.has_key("XDG_DATA_DIRS"):
            data_dirs = os.environ["XDG_DATA_DIRS"]
        if not data_dirs:
            data_dirs = "/usr/local/share/:/usr/share/"

        for data_dir in data_dirs.split(":"):
            retval = self.load_icon_from_path(os.path.join(data_dir, "pixmaps", icon_value),
                                              icon_size)
            if retval:
                return retval

            retval = self.load_icon_from_path(os.path.join(data_dir, "icons", icon_value),
                                              icon_size)
            if retval:
                return retval

        return None


    def scale_to_bounded(self, icon, size):
        if icon:
            if icon.get_height() > size:
                _icon = icon.scale_simple(
                        int(round(size * icon.get_width() / icon.get_height())),
                        int(round(size)),
                        gtk.gdk.INTERP_BILINEAR)
                if _icon is not None:
                    icon = _icon
            if icon.get_width() > size:
                _icon = icon.scale_simple(
                        size,
                        size * icon.get_height() / icon.get_width(),
                        gtk.gdk.INTERP_BILINEAR)
                if _icon is not None:
                    icon = _icon
        return icon


    def load_icon(self, icon_value, icon_size, force_size = True):
        assert icon_value, "No icon to load!"

        if isinstance(icon_size, gtk.IconSize):
            icon_size = gtk.icon_size_lookup(icon_size)[0]
            force_size = True

        if isinstance(icon_value, gtk.gdk.Pixbuf):
            if force_size:
                return self.scale_to_bounded(icon_value, icon_size)
            return icon_value

        if os.path.isabs(icon_value):
            icon = self.load_icon_from_path(icon_value, icon_size)

            if icon:
                if force_size:
                    return self.scale_to_bounded(icon, icon_size)
                return icon
            icon_name = os.path.basename(icon_value)
        else:
            icon_name = icon_value

        if icon_name.endswith(".png"):
            icon_name = icon_name[:-len(".png")]
        elif icon_name.endswith(".xpm"):
            icon_name = icon_name[:-len(".xpm")]
        elif icon_name.endswith(".svg"):
            icon_name = icon_name[:-len(".svg")]

        icon = None
        icon_theme = gtk.icon_theme_get_default()
        info = icon_theme.lookup_icon(icon_name, icon_size, gtk.ICON_LOOKUP_USE_BUILTIN)
        
        if info:
            if icon_name.startswith("gtk-"):
                # NOTE: IconInfo/IconTheme.load_icon leaks a ref to the icon, so
                #       load it manually.
                # NOTE: The bindings are also broken for Gtk's builtin pixbufs:
                #       IconInfo.get_builtin_pixbuf always returns None.
                icon = info.load_icon()
            elif info.get_filename():
                icon = self.load_icon_from_path(info.get_filename())
        else:
            icon = self.load_icon_from_data_dirs(icon_value, icon_size) # Fallback

        if icon and force_size:
            return self.scale_to_bounded(icon, icon_size)
        return icon


    def load_image(self, icon_value, icon_size, force_size = True):
    	
        pixbuf = self.load_icon(icon_value, icon_size, force_size)
        img = gtk.Image()
        img.set_from_pixbuf(pixbuf)
        img.show()
        return img
