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

#ifndef __FILEBROWSER_UTILS_H__
#define __FILEBROWSER_UTILS_H__

#include <gtk/gtk.h>
#include <libgnomevfs/gnome-vfs.h>

#define FILEBROWSER_ICON_TEXT_SIZE 24
#define FILEBROWSER_ICON_TEXT_CUTOFF 5
#define FILEBROWSER_ICON_TEXT_INNERLINE_PADDING 4
#define MARGIN_X 24
#define MARGIN_Y 24
#define PADDING_X 6
#define PADDING_Y 6

gboolean is_directory(
    GnomeVFSURI * uri );

gboolean scale_keepping_ratio(
    guint * width,
    guint * height,
    guint max_width,
    guint max_height );

void resize_icon(
    GdkPixbuf ** pixbuf,
    gint icon_size );

GdkPixbuf *get_icon(
    const gchar * filename,
    gint size );

GdkPixbuf *compose_applet_icon(
    const GdkPixbuf * icon1, 
    const GdkPixbuf * icon2, 
    const GdkPixbuf * icon3, 
    gint size );

void paint_icon_name(
    cairo_t * cr,
    const gchar * name,
    int x,
    int y,
    GdkColor tc );
    
void clear_background(
    cairo_t * cr );
    
void paint_icon(
    cairo_t * cr,
    GdkPixbuf * icon,
    int x,
    int y,
    double a );

#endif /* __FILEBROWSER_UTILS_H__ */
