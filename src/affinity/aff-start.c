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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <stdio.h>
#include <string.h>

#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <libawn/awn-desktop-item.h>
#include <libawn/awn-vfs.h>

#include "aff-start.h"

#include "aff-button.h"
#include "aff-settings.h"
#include "aff-utils.h"

#define AFF_START_GET_PRIVATE(obj) (G_TYPE_INSTANCE_GET_PRIVATE ((obj), AFF_TYPE_START, AffStartPrivate))

G_DEFINE_TYPE (AffStart, aff_start, GTK_TYPE_VBOX);

/* STRUCTS & ENUMS */
struct _AffStartPrivate
{
	AffinityApp *app;

        GtkWidget *fav;
        GtkWidget *fav_box;
        GtkWidget *fav_table;
        
        GtkWidget *recent;
        GtkWidget *recent_box;
        GtkWidget *recent_table;
        
        GList *favourites;
};

/* FORWARDS */

static void aff_start_class_init(AffStartClass *klass);
static void aff_start_init(AffStart *start);
static void aff_start_finalize(GObject *obj);

static GtkVBoxClass *parent_class;

static gint col = 0;
static gint row = 0;

/* CALLBACKS */

static void
refresh_favs (AffStart *start)
{
	AffStartPrivate *priv;	
	priv = AFF_START_GET_PRIVATE (start);
	
	GList *l = NULL;
	int i = 0;
	
	for (l = priv->favourites; l != NULL; l = l->next) {
		if ( i > 5)
			continue;
		const char *uri = (char*)l->data;
		
		AwnDesktopItem *item = awn_desktop_item_new ((gchar*)uri);
		if (item == NULL)
			continue;
		
		const char *name = awn_desktop_item_get_name (item);
		const char *icon_name = awn_desktop_item_get_icon (item, gtk_icon_theme_get_default ());
		GdkPixbuf *icon = aff_utils_get_app_icon_sized (icon_name, 48, 48);
		
		GtkWidget *image = gtk_image_new_from_pixbuf (icon);
		GtkWidget *button = aff_button_new (priv->app, 
				 		    GTK_IMAGE(image),  
				                    name,
				                    uri);
		gtk_widget_set_size_request (button, 200, -1);	
		gtk_widget_show_all (button);	                    
						                    
		gtk_table_attach_defaults  (GTK_TABLE (priv->fav_table),
                                    	button,
                                    	col, 
                                    	col+1,
                                    	row,
                                    	row+1);
		
		if (col == 1)
			col = 0;
		else
			col++;
	
		if (col == 0)
			row++;						                    	
		
		i++;
		if (item) {
			awn_desktop_item_free (item);
        }
	}					
}

static void
_sync_config (AffStart *start)
{
	AffStartPrivate *priv;	
	priv = AFF_START_GET_PRIVATE (start);
	AwnConfigClient *client = aff_settings_get_client ();
	
	GList *l = NULL;
	int i = 0;
	char *string = NULL;
	
	for (l = priv->favourites; l != NULL; l = l->next) {
		if ( i > 5)
			continue;
		const char *uri = (char*)l->data;
		char *temp = string;
		
		if (i)
			string = g_strdup_printf ("%s;%s", temp, uri);
		else
			string = g_strdup (uri);
		g_free (temp);
		i++;
	}
	awn_config_client_set_string (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, "favourites", string, NULL);		
	
	g_free (string);
	
}

void
aff_start_app_launched (AffStart *start, const char *uri)
{
	AffStartPrivate *priv;	
	priv = AFF_START_GET_PRIVATE (start);
	GtkWidget *table;
	
	GList *l = NULL;
	int i = 0;
	for (l = priv->favourites; l != NULL; l = l->next) {
		if ( i > 5)
			continue;
		const char *u = (char*)l->data;
		if (strcmp (u, uri) == 0)
			return;
		i++;
	}	
	
	if (priv->fav_table)
		gtk_widget_destroy (priv->fav_table);
	
	table = gtk_table_new (3, 2, TRUE);
	priv->fav_table = table;
	gtk_container_add (GTK_CONTAINER (priv->fav_box), priv->fav_table);	
	
	priv->favourites = g_list_prepend (priv->favourites, (gchar*)uri);
	
	_sync_config (start);

	col = row = 0;
	refresh_favs (start);
	
	gtk_widget_show_all (table);		
}

static void
_add_item (GtkRecentInfo *info, AffStart *start)
{
	AffStartPrivate *priv;
	GtkWidget *image, *button;
	gchar *mime = NULL;
	gchar *local_uri = NULL;
	gchar *markup = NULL;
	
	priv = AFF_START_GET_PRIVATE (start);
	
	mime = (gchar *)gtk_recent_info_get_mime_type (info);
#ifdef LIBAWN_USE_GNOME
	local_uri = gnome_vfs_local_path_from_uri (gtk_recent_info_get_uri (info));
#elif defined(LIBAWN_USE_XFCE)
	ThunarVfsPath *path = thunar_vfs_path_new (gtk_recent_info_get_uri (info));
	local_uri = thunar_vfs_path_dup_string (path);
	thunar_vfs_path_unref (path);
#else
	GFile *recent_file = g_file_new_for_uri (gtk_recent_info_get_uri (info));
	local_uri = g_file_get_path (recent_file);
	g_free (recent_file);
#endif
	
	gchar *res = strstr (mime, "image");
	if (res && local_uri) {
		GdkPixbuf *pixbuf;
		pixbuf = gdk_pixbuf_new_from_file_at_scale (local_uri,
                                                            48,
                                                            48,
                                                            TRUE,
                                                            NULL);
                image = gtk_image_new_from_pixbuf (pixbuf);
                g_free (local_uri);
        } else {
        	image = gtk_image_new_from_pixbuf (gtk_recent_info_get_icon (info, 48));
	}
	gchar *temp = NULL;
	temp = g_strdup_printf ("%s", gtk_recent_info_get_display_name (info));
	markup = g_markup_escape_text (temp, -1);
	g_free (temp);
	
	button = aff_button_new (priv->app, 
				 GTK_IMAGE(image),  
				 markup,
				 gtk_recent_info_get_uri (info));
	g_free (markup);				 
	gtk_widget_set_size_request (button, 200, -1);
	
	gtk_recent_info_unref(info) ;
	
	gtk_table_attach_defaults  (GTK_TABLE (priv->recent_table),
                                    button,
                                    col, 
                                    col+1,
                                    row,
                                    row+1);
	gtk_widget_show_all (button);
	if (col == 1)
		col = 0;
	else
		col++;
	
	if (col == 0)
		row++;
}

static void 
init_recent (AffStart *start, GtkRecentManager *recent)
{
	AffStartPrivate *priv;	
	
	GtkWidget *table;
	GList *items;
	
	priv = AFF_START_GET_PRIVATE (start);
	
	gtk_recent_manager_set_limit (recent, 6);
	
	if (priv->recent_table)
		gtk_container_remove (GTK_CONTAINER (priv->recent_box), priv->recent_table);
	
	table = gtk_table_new (3, 2, TRUE);
	priv->recent_table = table;
	gtk_container_add (GTK_CONTAINER (priv->recent_box), priv->recent_table);	
	
	items = gtk_recent_manager_get_items (recent);
	
	col = row = 0;
	g_list_foreach (items, (GFunc)_add_item, (gpointer)start);
	
	gtk_widget_show_all (table);
}

static void 
init_favs (AffStart *start)
{
	AffStartPrivate *priv;	
	
	GtkWidget *table;
	GList *items;
	
	priv = AFF_START_GET_PRIVATE (start);
		
	if (priv->fav_table)
		gtk_container_remove (GTK_CONTAINER (priv->fav_box), priv->fav_table);
	
	table = gtk_table_new (3, 2, TRUE);
	priv->fav_table = table;
	gtk_container_add (GTK_CONTAINER (priv->fav_box), priv->fav_table);	
	
	g_print ("%s\n", priv->app->settings->favourites);
	char **tokens = g_strsplit (priv->app->settings->favourites, ";", -1);
	char **uri;
	
	for (uri = tokens; *uri; uri++) {
		priv->favourites = g_list_append (priv->favourites, g_strdup (uri[0]));
	}
	
	col = row = 0;
	refresh_favs (start);
	g_strfreev (tokens);
	gtk_widget_show_all (table);
}


/* AFF_START_NEW */
static void
aff_start_class_init(AffStartClass *klass)
{
	GObjectClass *gobject_class;
	
	parent_class = g_type_class_peek_parent(klass);

	gobject_class = G_OBJECT_CLASS(klass);
	g_type_class_add_private (gobject_class, sizeof (AffStartPrivate));
	gobject_class->finalize = aff_start_finalize;
}

static void
update_recent (GtkRecentManager *recent, AffStart *start)
{
	init_recent (start, recent);
}

static void
aff_start_init(AffStart *start)
{
    
}



static void
aff_start_finalize(GObject *obj)
{
	AffStart *start;
	
	g_return_if_fail(obj != NULL);
	g_return_if_fail(AFF_IS_START(obj));

	start = AFF_START(obj);
	
	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(obj);
}

GtkWidget *
aff_start_new(AffinityApp *app)
{
	AffStartPrivate *priv;
	GtkRecentManager *recent;
	GtkWidget *box, *frame, *alignment;
	GtkWidget *label;
	gchar *markup = NULL;
	
	GtkWidget *start = g_object_new(AFF_TYPE_START, 
					 "homogeneous", TRUE,
					 "spacing", 24,
					 NULL);
	priv = AFF_START_GET_PRIVATE (start);					 
	priv->app = app;
	
	
	/* Favourites */
        frame = gtk_frame_new(" ");
	priv->fav = frame;
	gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_NONE);
	
	label = gtk_label_new (" ");
	markup = g_strdup_printf ("<span foreground='%s' size='larger' weight='bold'>%s</span>", 
				  app->settings->text_color, 
				  _("Favourites"));
				  
	gtk_label_set_markup (GTK_LABEL (label), markup);
	g_free (markup);
	gtk_frame_set_label_widget (GTK_FRAME (frame), label);
	
        alignment = gtk_alignment_new (0.0, 0.0, 0.0, 0.0);
        gtk_alignment_set_padding(GTK_ALIGNMENT(alignment), 5, 0, 15, 0);
        gtk_container_add(GTK_CONTAINER(frame), alignment);	
       
        box = gtk_vbox_new(FALSE, 0 );
        priv->fav_box = box;
        gtk_container_add (GTK_CONTAINER(alignment), box); 
        init_favs (AFF_START (start));
        
        /* Recent Documents */
        frame = gtk_frame_new(" ");
        priv->recent = frame;
	gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_NONE);

	label = gtk_label_new (" ");
	markup = g_strdup_printf ("<span foreground='%s' size='larger' weight='bold'>%s</span>", 
				  app->settings->text_color, 
				  _("Recent Documents"));
				  
	gtk_label_set_markup (GTK_LABEL (label), markup);
	g_free (markup);
	gtk_frame_set_label_widget (GTK_FRAME (frame), label);	

        alignment = gtk_alignment_new (0.0, 0.0, 0.0, 0.0);
        priv->recent_box = alignment;
        gtk_alignment_set_padding(GTK_ALIGNMENT(alignment), 5, 0, 15, 0);
        gtk_container_add(GTK_CONTAINER(frame), alignment);	

	priv->recent_table = NULL;
        recent = gtk_recent_manager_get_default();
        init_recent(AFF_START (start), recent);
	g_signal_connect (G_OBJECT (recent), "changed", G_CALLBACK (update_recent), (gpointer)start);
	
	        
        gtk_box_pack_start(GTK_BOX(start), priv->fav, TRUE, TRUE, 0);
        gtk_box_pack_start(GTK_BOX(start), priv->recent, FALSE, TRUE, 0);   
		
	return GTK_WIDGET(start);
}

