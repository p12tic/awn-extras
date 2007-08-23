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

#include "stack-cairo.h"
#include "stack-applet.h"
#include "stack-gconf.h"
//#include "stack-defines.h"

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
    int y ) {

    AwnColor                              color;
    cairo_text_extents_t extents;
    guint           icon_size = stack_gconf_get_icon_size(  ) + MARGIN_X/2;
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
                len -= ( STACK_ICON_TEXT_CUTOFF - remains );
                remains = STACK_ICON_TEXT_CUTOFF;
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
        tx = x + ( icon_size / 2 ) - ( ( extents.width / 2 ) + extents.x_bearing ) - MARGIN_X/4;
        ty = y + ( 3 * STACK_ICON_TEXT_INNERLINE_PADDING ) +
             ( num * ( extents.height + STACK_ICON_TEXT_INNERLINE_PADDING ) );

        cairo_move_to( cr, tx, ty );
        cairo_text_path( cr, subname );

        g_free( subname );

        name = name + len;
        num++;
    } while ( g_utf8_strlen( name, -1 ) > 0 && num < 2 );

    stack_gconf_get_icontext_color (&color);
    cairo_set_source_rgba (cr, color.red, color.green, color.blue, color.alpha);
    //cairo_set_source_rgba( cr, 1.0, 1.0, 1.0, 1.0 );
    cairo_fill_preserve( cr );

    //stack_gconf_get_border_color (&color);
    //cairo_set_source_rgba (cr, color.red, color.green, color.blue, color.alpha);
    //cairo_set_source_rgba( cr, 0.0, 0.0, 0.0, 0.6 );
    //cairo_set_line_width( cr, 0.05 );
    //cairo_stroke( cr );
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
