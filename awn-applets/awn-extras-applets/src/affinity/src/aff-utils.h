/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*- */
/*
 * Copyright (C) 2007 Neil J. Patel <njpatel@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * Authors: Neil J. Patel <njpatel@gmail.com>
 *
 */

#ifndef _AFF_UTILS_H_
#define _AFF_UTILS_H_

#include <gtk/gtk.h>

GdkPixbuf *aff_utils_get_icon (const char *uri);

GdkPixbuf *aff_utils_get_icon_sized (const char *uri, gint width, gint height);

GdkPixbuf *aff_utils_get_app_icon (const char *name);

GdkPixbuf *aff_utils_get_app_icon_sized (const char *name, gint width, gint height);

#endif
 
