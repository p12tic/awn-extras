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

#ifndef __STACK_PIXBUF_UTILS_H__
#define __STACK_PIXBUF_UTILS_H__

#include <gtk/gtk.h>

#define STACK_ICON_SIZE 48

gboolean scale_keepping_ratio(
    guint * width,
    guint * height,
    guint max_width,
    guint max_height );

GdkPixbuf *resize_icon(
    GdkPixbuf * pixbuf,
    gint icon_size );

GdkPixbuf *get_icon(
    const gchar * filename,
    gint size );

GdkPixbuf *compose_applet_icon( GdkPixbuf * icon1, GdkPixbuf * icon2, GdkPixbuf * icon3, gint size );

#endif /* __STACK_PIXBUF_UTILS_H__ */
