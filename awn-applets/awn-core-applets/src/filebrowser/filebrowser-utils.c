/*
 * Copyright (c) 2007 Timon David Ter Braak
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <math.h>
#include <gtk/gtk.h>
#include <libawn/awn-cairo-utils.h>
#include <libgnomeui/gnome-thumbnail.h>
#include <libgnomeui/libgnomeui.h>
#include <libgnomevfs/gnome-vfs-ops.h>

#include "filebrowser-utils.h"
#include "filebrowser-applet.h"
#include "filebrowser-gconf.h"
#include "filebrowser-defines.h"

static GnomeThumbnailFactory* THUMBNAIL_FACTORY = NULL;

/**
 * Checks if uri is a directory
 * -returns FALSE if uri == NULL
 * -follow symlinks
 */
gboolean is_directory(
    GnomeVFSURI * uri ) {
    if ( !uri ) {
        return FALSE;
    }

    GnomeVFSFileInfo *info;
    GnomeVFSResult result;
    gboolean is_dir = FALSE;

    info = gnome_vfs_file_info_new(  );
    result =
        gnome_vfs_get_file_info_uri( uri, info,
                                     GNOME_VFS_FILE_INFO_DEFAULT | GNOME_VFS_FILE_INFO_FOLLOW_LINKS );

    if ( result == GNOME_VFS_OK && info->valid_fields & GNOME_VFS_FILE_INFO_FIELDS_TYPE ) {
        is_dir = ( info->type == GNOME_VFS_FILE_TYPE_DIRECTORY );
    }

    gnome_vfs_file_info_unref( info );

    return is_dir;
}

/**
 * Computes scaling properties with respect to @max_width and @max_height
 */
gboolean scale_keepping_ratio(
    guint * width,
    guint * height,
    guint max_width,
    guint max_height ) {

    gdouble         w = *width,
                    h = *height,
                    factor;
    gint            new_width,
                    new_height;
    gboolean        modified;

    if ( ( *width < max_width ) && ( *height < max_height ) ) {
        return FALSE;
    }

    factor = MIN( max_width / w, max_height / h );
    new_width = MAX( ( gint ) floor( w * factor + 0.50 ), 1 );
    new_height = MAX( ( gint ) floor( h * factor + 0.50 ), 1 );

    modified = ( new_width != *width ) || ( new_height != *height );

    *width = new_width;
    *height = new_height;

    return modified;
}

void resize_icon(
    GdkPixbuf ** pixbuf,
    gint icon_size ) {

    guint           width = gdk_pixbuf_get_width( *pixbuf );
    guint           height = gdk_pixbuf_get_height( *pixbuf );

    if ( scale_keepping_ratio( &width, &height, icon_size, icon_size ) ) {
	GdkPixbuf *old = *pixbuf;
	*pixbuf = gnome_thumbnail_scale_down_pixbuf(*pixbuf, width, height);
        //*pixbuf = gdk_pixbuf_scale_simple( *pixbuf, width, height, GDK_INTERP_BILINEAR );
	g_object_unref( G_OBJECT( old ) );
    }
}

/**
 * Get icon from a filename
 * -create thumbnails for image/video content
 * -scale icon to our prefered size
 */
GdkPixbuf *get_icon(
    const gchar * filename,
    GnomeVFSURI * uri,
    gint icon_size ) {

    GdkPixbuf *pixbuf = NULL;

    if (!THUMBNAIL_FACTORY)
        THUMBNAIL_FACTORY = gnome_thumbnail_factory_new( GNOME_THUMBNAIL_SIZE_NORMAL );
    GnomeThumbnailFactory *thumbnail_factory = THUMBNAIL_FACTORY;

    GnomeVFSFileInfo *info = gnome_vfs_file_info_new();
    gnome_vfs_get_file_info_uri(uri, info, GNOME_VFS_FILE_INFO_DEFAULT | GNOME_VFS_FILE_INFO_GET_MIME_TYPE);
    gchar *uri_path = gnome_vfs_uri_to_string(uri, GNOME_VFS_URI_HIDE_NONE);

    char* thumbnail_file = gnome_thumbnail_factory_lookup(thumbnail_factory, uri_path, info->mtime);

    if (thumbnail_file) {
        // thumbnail was already created, just load it
        GError *error = NULL;
        pixbuf = gdk_pixbuf_new_from_file(thumbnail_file, &error);
    } else {
        // should we create thumbnail?
        if (gnome_thumbnail_factory_can_thumbnail(thumbnail_factory, uri_path, info->mime_type, info->mtime)) {
            pixbuf = gnome_thumbnail_factory_generate_thumbnail(thumbnail_factory, uri_path, info->mime_type);
            // save new thumbnail?
            if (pixbuf && gnome_thumbnail_has_uri (pixbuf, uri_path))
                gnome_thumbnail_factory_save_thumbnail(thumbnail_factory, pixbuf, uri, info->mtime);
        }
    }

    gnome_vfs_file_info_unref(info);
    //g_object_unref(uri_path);

    if ( pixbuf ) {
        resize_icon( &pixbuf, icon_size );
    } else {
        GtkIconTheme *theme = gtk_icon_theme_get_default(  );
        pixbuf = gtk_icon_theme_load_icon( theme, filename, icon_size, 0, NULL );

        if ( !pixbuf ) {
            gchar          *icon_path = gnome_icon_lookup_sync( theme, NULL, uri_path, NULL,
                                        GNOME_ICON_LOOKUP_FLAGS_NONE,
                                        GNOME_ICON_LOOKUP_RESULT_FLAGS_NONE );

            pixbuf = gtk_icon_theme_load_icon( theme, icon_path, icon_size, 0, NULL );
            g_free( icon_path );
        }
    }

    g_free(uri_path);
    return pixbuf;
}

GdkPixbuf *compose_applet_icon( 
    const GdkPixbuf * icon1, 
    const GdkPixbuf * icon2, 
    const GdkPixbuf * icon3, 
    gint size ){

    g_return_val_if_fail( icon1, NULL );

    guint           mini = ( 3 * size / 4 );

    GdkPixbuf      *target = gdk_pixbuf_new( GDK_COLORSPACE_RGB, TRUE, 8, size, size );

    gdk_pixbuf_fill( target, 0x00000000 );	// transparent

    GdkPixbuf      *scaled = gdk_pixbuf_copy( icon1 );
    resize_icon( &scaled, mini );

    gint            w = gdk_pixbuf_get_width( scaled );
    gint            h = gdk_pixbuf_get_height( scaled );

    gdk_pixbuf_composite( scaled, target, 0, 0, w, h, 0.0, 0.0, 1.0, 1.0,
                          GDK_INTERP_BILINEAR, 255 );
    g_object_unref( G_OBJECT( scaled ) );

    if ( icon2 && !icon3 ) {
        scaled = gdk_pixbuf_copy( icon2 );
	resize_icon( &scaled, mini );
        w = gdk_pixbuf_get_width( scaled );
        h = gdk_pixbuf_get_height( scaled );
        gdk_pixbuf_composite( scaled, target, size - w, size - h, w, h,
                              size - w, size - h, 1.0, 1.0, GDK_INTERP_BILINEAR, 224 );
        g_object_unref( G_OBJECT( scaled ) );
    } else if ( icon2 && icon3 ) {
        scaled = gdk_pixbuf_copy( icon2 );
	resize_icon( &scaled, mini );
        w = gdk_pixbuf_get_width( scaled );
        h = gdk_pixbuf_get_height( scaled );
        gdk_pixbuf_composite( scaled, target, ( ( size - w ) / 2 ),
                              ( ( size - h ) / 2 ), w, h, ( ( size - w ) / 2 ),
                              ( ( size - h ) / 2 ), 1.0, 1.0, GDK_INTERP_BILINEAR, 224 );
        g_object_unref( G_OBJECT( scaled ) );

        scaled = gdk_pixbuf_copy( icon3 );
	resize_icon( &scaled, mini );
        w = gdk_pixbuf_get_width( scaled );
        h = gdk_pixbuf_get_height( scaled );
        gdk_pixbuf_composite( scaled, target, size - w, size - h, w, h,
                              size - w, size - h, 1.0, 1.0, GDK_INTERP_BILINEAR, 224 );
        g_object_unref( G_OBJECT( scaled ) );
    }

    return target;
}

/**
 * Paint the icon name
 * @cr the cairo surface
 * @icon_name the textual name
 * @x the (relative) x coordinate
 * @y the (relative) y coordinate
 */
void paint_icon_name(
    cairo_t * cr,
    const gchar * icon_name,
    int x,
    int y,
    GdkColor tc ) {
   
    cairo_text_extents_t extents;
    guint           icon_size = filebrowser_gconf_get_icon_size(  ) + ICON_MARGIN_X*2/3;
    guint           num = 0;
    gchar          *name = g_strdup( icon_name );

    cairo_select_font_face( cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD );
    cairo_set_font_size( cr, 10 );

    do {
        guint           len = g_utf8_strlen( name, -1 ),
                              remains = 0,
                                        tx,
                                        ty;

        cairo_text_extents( cr, name, &extents );

        if ( extents.width > icon_size ) {
            guint           nlen = floor( ( icon_size / extents.width ) * len );

            remains = len - nlen;
            len = nlen;
        }

        if ( remains > 0 && remains < len ) {
            gboolean        fixed = FALSE;
            gchar          *delims = G_STR_DELIMITERS;
            gint            i;

            for ( i = len; ( len - i + remains ) < len; i-- ) {
                gint            j;

                for ( j = 0; j < 7; j++ ) {
                    if ( delims[j] == name[i] ) {
                        fixed = TRUE;
                        break;
                    }
                }

                if ( fixed ) {
                    remains += ( len - ( i + 1 ) );
                    len -= ( len - ( i + 1 ) );
                    break;
                }
            }

            if ( !fixed ) {
                len -= ( FILEBROWSER_ICON_TEXT_CUTOFF - remains );
                remains = FILEBROWSER_ICON_TEXT_CUTOFF;
            }
        }

        gchar          *subname = g_strdup( name );

        if ( remains > 0 && num == 1 ) {
            subname[len - 3] = 0x0;
            gchar          *cutoff = g_strconcat( subname, "...", NULL );

            g_free( subname );
            subname = cutoff;
        } else {
            subname[len] = 0x0;
        }

        cairo_text_extents( cr, subname, &extents );
        tx = x + ( icon_size / 2 ) - ( ( extents.width / 2 ) + extents.x_bearing ) - ICON_MARGIN_X/3;
        ty = y + ( 3 * FILEBROWSER_ICON_TEXT_INNERLINE_PADDING ) +
             ( num * ( extents.height + FILEBROWSER_ICON_TEXT_INNERLINE_PADDING ) );

        cairo_move_to( cr, tx, ty );
        cairo_text_path( cr, subname );

        g_free( subname );

        name = name + len;
        num++;
    } while ( g_utf8_strlen( name, -1 ) > 0 && num < 2 );

//    filebrowser_gconf_get_icontext_color (&color);
//    cairo_set_source_rgba (cr, color.red, color.green, color.blue, color.alpha);

    //cairo_set_source_rgba( cr, 1.0, 1.0, 1.0, 1.0 );
//    cairo_fill_preserve( cr );

    //filebrowser_gconf_get_border_color (&color);
    //cairo_set_source_rgba (cr, color.red, color.green, color.blue, color.alpha);
    //cairo_set_source_rgba( cr, 0.0, 0.0, 0.0, 0.6 );
    //cairo_set_line_width( cr, 0.05 );
    //cairo_stroke( cr );
    
    cairo_set_source_rgba( cr, tc.red/65335.0,
                               tc.green/65335.0,
                               tc.blue/65335.0,
                               1.0 );
    cairo_fill( cr );   
    cairo_destroy( cr );

    return;
}

/**
 * Clear the background to transparent
 */
void clear_background(
    cairo_t * cr ) {

    cairo_set_source_rgba( cr, 1.0f, 1.0f, 1.0f, 0.0f );
    cairo_set_operator( cr, CAIRO_OPERATOR_CLEAR );
    cairo_paint( cr );
}

/**
 * Paint an icon on the cairo surface
 * @cr cairo surface
 * @icon the pixbuf to paint
 * @x the (relative) x coordinate
 * @y the (relative) y coordinate
 * @a alpha value to use
 */
void paint_icon(
    cairo_t * cr,
    GdkPixbuf * icon,
    int x,
    int y,
    double a ) {

    cairo_set_operator( cr, CAIRO_OPERATOR_OVER );
    gdk_cairo_set_source_pixbuf( cr, icon, x, y );
    cairo_paint_with_alpha( cr, a );
}
