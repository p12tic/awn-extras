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

#ifndef _AFF_BUTTON_H_
#define _AFF_BUTTON_H_

#include <gtk/gtk.h>

#include "affinity.h"

typedef struct _AffButton      AffButton;
typedef struct _AffButtonClass AffButtonClass;
typedef struct _AffButtonPrivate  AffButtonPrivate;

#define AFF_TYPE_BUTTON            (aff_button_get_type())
#define AFF_BUTTON(obj)            (G_TYPE_CHECK_INSTANCE_CAST((obj), AFF_TYPE_BUTTON, AffButton))
#define AFF_BUTTON_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST((klass), AFF_TYPE_BUTTON, AffButtonClass))
#define AFF_IS_BUTTON(obj)         (G_TYPE_CHECK_INSTANCE_TYPE((obj), AFF_TYPE_BUTTON))
#define AFF_IS_BUTTON_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), AFF_TYPE_BUTTON))
#define AFF_BUTTON_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS((obj), AFF_TYPE_BUTTON, AffButtonClass))

struct _AffButton
{
	GtkButton parent;
};

struct _AffButtonClass
{
	GtkButtonClass parent_class;
	
	AffButtonPrivate *priv;
};

G_BEGIN_DECLS

GType      aff_button_get_type(void);
GtkWidget *aff_button_new(AffinityApp *app, GtkImage *image, const char *text, const char *uri);
GtkWidget *aff_button_new_with_command(AffinityApp *app, GtkImage *image, const char *text, const char *command);

G_END_DECLS

#endif
