import os
import gnome.ui
import gnomevfs
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
            self.cached_size = icon_size
            self.cached_timestamp = timestamp
        return self.cached_icon

    def _lookup_or_make_thumb(self, icon_size, timestamp):
        icon_name, icon_type = \
                gnome.ui.icon_lookup(icon_theme, thumb_factory, self.uri, self.mimetype, 0)
        try:
            if icon_type == gnome.ui.ICON_LOOKUP_RESULT_FLAGS_THUMBNAIL or \
                    thumb_factory.has_valid_failed_thumbnail(self.uri, timestamp):
                # Use existing thumbnail
                thumb = icon_factory.load_icon(icon_name, icon_size)
            #elif self._is_local_uri(self.uri):
            else:
                # Generate a thumbnail for local files only
                print " *** Calling generate_thumbnail for", self.uri
                thumb = thumb_factory.generate_thumbnail(self.uri, self.mimetype)
                thumb_factory.save_thumbnail(thumb, self.uri, timestamp)
    
            if thumb:
                # Fixup the thumbnail a bit
                #thumb = self._nicer_dimensions(thumb)
                #thumb = icon_factory.make_icon_frame(thumb, icon_size)
                return thumb
        except:
            pass
    
        # Fallback to mime-type icon on failure
        return icon_factory.load_icon(icon_name, icon_size)

    def _is_local_uri(self, uri):
        # NOTE: gnomevfs.URI.is_local seems to hang for some URIs (e.g. ssh
        #       or http).  So look in a list of local schemes which comes
        #       directly from gnome_vfs_uri_is_local_scheme.
        scheme, path = urllib.splittype(self.get_uri() or "")
        return not scheme or scheme in ("file", "help", "ghelp", "gnome-help", "trash",
            "man", "info", "hardware", "search", "pipe","gnome-trash")
    
    def _nicer_dimensions(self, icon):
        ### Constrain thumb dimensions to 1:1.2
        if float(icon.get_height()) / float(icon.get_width()) > 1.2:
            return icon.subpixbuf(0, 0, icon.get_width(), int(icon.get_width() * 1.2))
        return icon

# Borrowed IconFactory from "gimmie"
class IconFactory:
    '''
    Icon lookup swiss-army knife (from menutreemodel.py)
    '''

    def load_icon_from_path(self, icon_path, icon_size = None):
        if os.path.isfile(icon_path):
            try:
                if icon_size:
                    # constrain height, not width
                    return gtk.gdk.pixbuf_new_from_file_at_size(icon_path, -1, int(icon_size))
                else:
                    return gtk.gdk.pixbuf_new_from_file(icon_path)
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
                return icon.scale_simple(size * icon.get_width() / icon.get_height(),
                                         size,
                                         gtk.gdk.INTERP_BILINEAR)
            elif icon.get_width() > size:
                return icon.scale_simple(size,
                                         size * icon.get_height() / icon.get_width(),
                                         gtk.gdk.INTERP_BILINEAR)
            else:
                return icon
        else:
            return None

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

    def make_icon_frame(self, thumb, icon_size = None, blend = False):
        border = 1

        mythumb = gtk.gdk.Pixbuf(thumb.get_colorspace(),
                                 True,
                                 thumb.get_bits_per_sample(),
                                 thumb.get_width(),
                                 thumb.get_height())
        mythumb.fill(0x00000080) # black, 50% transparent
        if blend:
            thumb.composite(mythumb, 0, 0,
                            thumb.get_width(), thumb.get_height(),
                            0, 0,
                            1.0, 1.0,
                            gtk.gdk.INTERP_NEAREST,
                            128)
        thumb.copy_area(border, border,
                        thumb.get_width() - (border * 2), thumb.get_height() - (border * 2),
                        mythumb,
                        border, border)
        return mythumb

    def transparentize(self, pixbuf, percent):
        pixbuf = pixbuf.add_alpha(False, '0', '0', '0')
        for row in pixbuf.get_pixels_array():
            for pix in row:
                pix[3] = min(int(pix[3]), 255 - (percent * 0.01 * 255))
        return pixbuf

    def colorshift(self, pixbuf, shift):
        pixbuf = pixbuf.copy()
        for row in pixbuf.get_pixels_array():
            for pix in row:
                pix[0] = min(255, int(pix[0]) + shift)
                pix[1] = min(255, int(pix[1]) + shift)
                pix[2] = min(255, int(pix[2]) + shift)
        return pixbuf

    def greyscale(self, pixbuf):
        pixbuf = pixbuf.copy()
        for row in pixbuf.get_pixels_array():
            for pix in row:
                pix[0] = pix[1] = pix[2] = (int(pix[0]) + int(pix[1]) + int(pix[2])) / 3
        return pixbuf

icon_theme = gtk.icon_theme_get_default()
thumb_factory = gnome.ui.ThumbnailFactory("normal")
icon_factory = IconFactory()
