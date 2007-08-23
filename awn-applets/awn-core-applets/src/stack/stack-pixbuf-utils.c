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
#include <libgnomeui/gnome-thumbnail.h>
#include <libgnomeui/libgnomeui.h>
#include <libgnomevfs/gnome-vfs-mime-utils.h>

#include "stack-pixbuf-utils.h"
#include "stack-gconf.h"

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
                            max_w = max_width,
                                    max_h = max_height,
                                            factor;
    gint            new_width,
    new_height;
    gboolean        modified;

    if ( ( *width < max_width ) && ( *height < max_height ) ) {
        return FALSE;
    }

    factor = MIN( max_w / w, max_h / h );
    new_width = MAX( ( gint ) floor( w * factor + 0.50 ), 1 );
    new_height = MAX( ( gint ) floor( h * factor + 0.50 ), 1 );

    modified = ( new_width != *width ) || ( new_height != *height );

    *width = new_width;
    *height = new_height;

    return modified;
}

GdkPixbuf *resize_icon(
    GdkPixbuf * pixbuf,
    gint icon_size ) {
    guint           width = gdk_pixbuf_get_width( pixbuf );
    guint           height = gdk_pixbuf_get_height( pixbuf );

    if ( scale_keepping_ratio( &width, &height, icon_size, icon_size ) ) {
        pixbuf = gdk_pixbuf_scale_simple( pixbuf, width, height, GDK_INTERP_BILINEAR );
    }
    return pixbuf;
}

/**
 * Get icon from a filename
 * -create thumbnails for image/video content
 * -scale icon to our prefered size
 */
GdkPixbuf *get_icon(
    const gchar * filename,
    gint icon_size ) {
    GdkPixbuf      *pixbuf = NULL;
    gchar          *mime_type = gnome_vfs_get_mime_type( filename );

    if ( mime_type ) {
        GnomeThumbnailFactory *thumbnail_factory = gnome_thumbnail_factory_new( icon_size );

        pixbuf =
            gnome_thumbnail_factory_generate_thumbnail( thumbnail_factory, filename, mime_type );

        if ( pixbuf ) {
            pixbuf = resize_icon( pixbuf, icon_size );
        }
        g_free( mime_type );
    }

    if ( !pixbuf ) {
        GtkIconTheme   *theme = gtk_icon_theme_get_default(  );

        pixbuf = gtk_icon_theme_load_icon( theme, filename, icon_size, 0, NULL );

        if ( !pixbuf ) {
            gchar          *icon_path = gnome_icon_lookup_sync( theme, NULL, filename, NULL,
                                        GNOME_ICON_LOOKUP_FLAGS_NONE,
                                        GNOME_ICON_LOOKUP_RESULT_FLAGS_NONE );

            pixbuf = gtk_icon_theme_load_icon( theme, icon_path, icon_size, 0, NULL );
            g_free( icon_path );
        }
    }

    return pixbuf;
}

GdkPixbuf *compose_applet_icon( GdkPixbuf * icon1, GdkPixbuf * icon2, GdkPixbuf * icon3, gint size ){

    g_return_val_if_fail( icon1, NULL );

    guint           mini = ( 3 * size / 4 );

    GdkPixbuf      *target = gdk_pixbuf_new( GDK_COLORSPACE_RGB, TRUE, 8, size, size );

    gdk_pixbuf_fill( target, 0x00000000 );	// transparent

    GdkPixbuf      *scaled = resize_icon( gdk_pixbuf_copy( icon1 ), mini );
    gint            w = gdk_pixbuf_get_width( scaled );
    gint            h = gdk_pixbuf_get_height( scaled );

    gdk_pixbuf_composite( scaled, target, 0, 0, w, h, 0.0, 0.0, 1.0, 1.0,
                          GDK_INTERP_BILINEAR, 255 );
    g_object_unref( G_OBJECT( scaled ) );

    if ( icon2 && !icon3 ) {
        scaled = resize_icon( gdk_pixbuf_copy( icon2 ), mini );
        w = gdk_pixbuf_get_width( scaled );
        h = gdk_pixbuf_get_height( scaled );
        gdk_pixbuf_composite( scaled, target, size - w, size - h, w, h,
                              size - w, size - h, 1.0, 1.0, GDK_INTERP_BILINEAR, 224 );
        g_object_unref( G_OBJECT( scaled ) );
    } else if ( icon2 && icon3 ) {
        scaled = resize_icon( gdk_pixbuf_copy( icon2 ), mini );
        w = gdk_pixbuf_get_width( scaled );
        h = gdk_pixbuf_get_height( scaled );
        gdk_pixbuf_composite( scaled, target, ( ( size - w ) / 2 ),
                              ( ( size - h ) / 2 ), w, h, ( ( size - w ) / 2 ),
                              ( ( size - h ) / 2 ), 1.0, 1.0, GDK_INTERP_BILINEAR, 224 );
        g_object_unref( G_OBJECT( scaled ) );

        scaled = resize_icon( gdk_pixbuf_copy( icon3 ), mini );
        w = gdk_pixbuf_get_width( scaled );
        h = gdk_pixbuf_get_height( scaled );
        gdk_pixbuf_composite( scaled, target, size - w, size - h, w, h,
                              size - w, size - h, 1.0, 1.0, GDK_INTERP_BILINEAR, 224 );
        g_object_unref( G_OBJECT( scaled ) );
    }

    return target;
}
