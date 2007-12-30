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
 
#ifndef AFFINITY_APP_H
#define AFFINITY_APP_H

#include <glib-object.h>
#include <gtk/gtk.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-dialog.h>

#include "aff-settings.h"

#define AFFINITY_TYPE_APP		(affinity_app_get_type ())
#define AFFINITY_APP(obj)		(G_TYPE_CHECK_INSTANCE_CAST ((obj), AFFINITY_TYPE_APP, AffinityApp))
#define AFFINITY_APP_CLASS(klass)	(G_TYPE_CHECK_CLASS_CAST ((klass), AFFINITY_TYPE_APP, AffinityAppClass))
#define AFFINITY_IS_APP(obj)		(G_TYPE_CHECK_INSTANCE_TYPE ((obj), AFFINITY_TYPE_APP))
#define AFFINITY_IS_APP_CLASS(klass)	(G_TYPE_CHECK_CLASS_TYPE ((klass), AFFINITY_TYPE_APP))
#define AFFINITY_APP_GET_CLASS(obj)     (G_TYPE_INSTANCE_GET_CLASS ((obj), AFFINITY_TYPE_APP, AffinityAppClass))

typedef struct AffinityApp {
	GObject parent;
	
	AffSettings *settings;
	
	gboolean visible;
	gboolean lock_focus;
	gboolean ptr_is_grabbed;
	gboolean kbd_is_grabbed;
	gboolean searching;
	
	GtkStatusIcon *status;
	GtkWidget *status_menu;
	GtkWidget *window;
	
	GtkWidget *icon;
	GtkWidget *entry;
	GtkWidget *spinner;
	
	GtkWidget *start_box;
	GtkWidget *start;
	GtkWidget *sidebar;
		
	GtkWidget *results_box;
	GtkWidget *scroll;
	GtkWidget *treeview;
	GtkWidget *metabar;	

    AwnApplet *applet;
} AffinityApp;

typedef struct {
	GObjectClass parent_class;
	
	void (*affinity_shown) (AffinityApp *app);
	void (*affinity_hidden) (AffinityApp *app);
} AffinityAppClass;

typedef enum {
	AFF_QUERY_ALL,
	AFF_QUERY_APPLICATIONS,
	AFF_QUERY_BOOKMARKS,
	AFF_QUERY_CONTACTS,
	AFF_QUERY_DOCUMENTS,
	AFF_QUERY_EMAILS,
	AFF_QUERY_IMAGES,
	AFF_QUERY_MUSIC,
	AFF_QUERY_VIDEOS,
	AFF_N_QUERIES

} AffQueryType;

GType          affinity_app_get_type  (void);

AffinityApp *affinity_app_new (gboolean menu_mode, AwnApplet *applet);

void affinity_app_show (AffinityApp *app);
void affinity_app_hide (AffinityApp *app);
void affinity_app_close (AffinityApp *app);

#endif /* AFFINITYINITY_APP_H */
