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

#ifndef _AFF_SIDEBAR_H_
#define _AFF_SIDEBAR_H_

#include <gtk/gtk.h>

#include "affinity.h"

typedef struct _AffSidebar      AffSidebar;
typedef struct _AffSidebarClass AffSidebarClass;
typedef struct _AffSidebarPrivate  AffSidebarPrivate;

#define AFF_TYPE_SIDEBAR            (aff_sidebar_get_type())
#define AFF_SIDEBAR(obj)            (G_TYPE_CHECK_INSTANCE_CAST((obj), AFF_TYPE_SIDEBAR, AffSidebar))
#define AFF_SIDEBAR_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST((klass), AFF_TYPE_SIDEBAR, AffSidebarClass))
#define AFF_IS_SIDEBAR(obj)         (G_TYPE_CHECK_INSTANCE_TYPE((obj), AFF_TYPE_SIDEBAR))
#define AFF_IS_SIDEBAR_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), AFF_TYPE_SIDEBAR))
#define AFF_SIDEBAR_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS((obj), AFF_TYPE_SIDEBAR, AffSidebarClass))

struct _AffSidebar
{
	GtkVBox parent;
};

struct _AffSidebarClass
{
	GtkVBoxClass parent_class;
	
	AffSidebarPrivate *priv;
};

G_BEGIN_DECLS

GType      aff_sidebar_get_type(void);
GtkWidget *aff_sidebar_new(AffinityApp *app);

G_END_DECLS

#endif
