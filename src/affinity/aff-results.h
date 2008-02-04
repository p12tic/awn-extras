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

#ifndef _AFF_RESULTS_H
#define _AFF_RESULTS_H

#include <glib.h>
#include <gtk/gtk.h>

#include "affinity.h"

G_BEGIN_DECLS

#define AFF_TYPE_RESULTS      (aff_results_get_type())
#define AFF_RESULTS(o)        (G_TYPE_CHECK_INSTANCE_CAST((o), AFF_TYPE_RESULTS, AffResults))
#define AFF_RESULTS_CLASS(c)  (G_TYPE_CHECK_CLASS_CAST((c), AFF_TYPE_RESULTS, AffResultsClass))
#define IS_AFF_RESULTS(o)     (G_TYPE_CHECK_INSTANCE_TYPE((o), AFF_TYPE_RESULTS))
#define IS_AFF_RESULTS_CLASS  (G_TYPE_INSTANCE_GET_CLASS((o), AFF_TYPE_RESULTS, AffResultsClass))

#define BORDER_WIDTH 6

typedef struct _AffResults AffResults;
typedef struct _AffResultsClass AffResultsClass;
typedef struct _AffResultsPrivate  AffResultsPrivate;

struct _AffResults {
        GtkTreeView viewport;
};

struct _AffResultsClass {
        GtkTreeViewClass parent_class;
        
	AffResultsPrivate *priv;
};

enum {
	COLUMN_IMAGE,
	COLUMN_STRING,
	COLUMN_URI,
	COLUMN_COMMAND,
	N_COLUMNS	
};

GType aff_results_get_type( void );

GtkWidget *aff_results_new(AffinityApp *app);

void aff_results_set_search_string (AffResults *results, const gchar *text);

void aff_results_add_uri (AffResults *this, gulong id,  
					    GdkPixbuf *pixbuf,
					    const gchar *name,
					    const gchar *desc,
					    const gchar *uri);

void aff_results_add_command (AffResults *this, gulong id,  
					    GdkPixbuf *pixbuf,
					    const gchar *name,
					    const gchar *desc,
					    const gchar *command);

G_END_DECLS

#endif
