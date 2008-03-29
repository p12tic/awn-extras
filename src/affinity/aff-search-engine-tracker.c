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

#include "aff-search-engine-tracker.h"

#include <glib/gi18n.h>
#include <tracker.h>
#ifdef LIBAWN_USE_GNOME
#include <libgnomevfs/gnome-vfs-utils.h>
#elif defined(LIBAWN_USE_XFCE)
#include <thunar-vfs/thunar-vfs.h>
#else
#include <gio/gio.h>
#endif
#include <string.h>

struct AffSearchEngineTrackerDetails {
	TrackerClient 	*client;
	gboolean 	query_pending;
	
	GdkPixbuf *email;
};

typedef struct {
	AffSearchEngineTracker *tracker;
	GtkWidget *results;
	AffQueryType type;
	gulong id;

} AffTrackerSearchTerm;


static void  aff_search_engine_tracker_class_init       (AffSearchEngineTrackerClass *class);
static void  aff_search_engine_tracker_init             (AffSearchEngineTracker      *engine);

G_DEFINE_TYPE (AffSearchEngineTracker,
	       aff_search_engine_tracker,
	       AFF_TYPE_SEARCH_ENGINE);

static AffSearchEngineClass *parent_class = NULL;

static void
finalize (GObject *object)
{
	AffSearchEngineTracker *tracker;

	tracker = AFF_SEARCH_ENGINE_TRACKER (object);
	
	tracker_disconnect (tracker->details->client);

	g_free (tracker->details);

	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(object);
}

static void
_add_emails (gchar **data, AffTrackerSearchTerm *term)
{
	gchar *name = g_markup_escape_text (_("Unknown Email Subject"), -1);
	gchar *desc = g_markup_escape_text (_("Unknown Email Sender"), -1);
	gchar *command = NULL;
	
	if (data[3]) {
		g_free (name);
		name = g_markup_escape_text (data[3], -1);
		if (data[4]) {
			g_free (desc);
			desc = g_markup_escape_text (data[4], -1);
		}
	}
	
	command = g_strdup_printf ("evolution \"%s\"", data[0]);
	
	aff_results_add_command (AFF_RESULTS (term->results), term->id,
					  term->tracker->details->email, 
					  name, desc, command);	
	
	g_free (name);
	g_free (desc);	
	g_free (command);				  
}

static void
_add_results (gchar **data, AffTrackerSearchTerm *term)
{
	gchar *uri = NULL;
	gchar *name = NULL;
	gchar *temp = NULL; 
	
	char *res = NULL;
	res = strstr (data[0], "email:");
	if (res) {
		_add_emails (data, term);
		g_strfreev (data);
		return;
	}

#ifdef LIBAWN_USE_GNOME
	uri = gnome_vfs_get_uri_from_local_path (data[0]);
#elif defined(LIBAWN_USE_XFCE)
    ThunarVfsPath *path = thunar_vfs_path_new (data[0]);
    uri = thunar_vfs_path_dup_uri (path);
    thunar_vfs_path_unref (path);
#else
    GFile *path = g_file_new_for_path (data[0]);
    uri = g_file_get_uri (path);
    g_free (path);
#endif
	temp = g_filename_display_name (data[0]);
	name = g_markup_escape_text (temp, -1);
	g_free (temp);
	
	temp = NULL;
	if (name) {
		size_t len = strlen (name);
		int i = 0;
		int pos = 0;
		for (i=0; i<len;i++) {
			if (name[i] == G_DIR_SEPARATOR)
				pos = i;;
		}
		GString *file = NULL;
		file = g_string_new (name);
		file = g_string_erase (file,0, pos+1);
		g_free (name);
		name = g_strdup (file->str);
		g_string_free (file, TRUE);
	}
	aff_results_add_uri (AFF_RESULTS (term->results), term->id,
					  NULL, name, data[1], uri);
	
	g_free (uri);
	g_free (name);
	
	g_strfreev (data);					  
}

static void
search_callback (GPtrArray *result, GError *error, AffTrackerSearchTerm *term)
{
	AffSearchEngineTracker *tracker;
	tracker = AFF_SEARCH_ENGINE_TRACKER (term->tracker);
	
	if (error) {
		g_print("%s\n",error->message);
		g_error_free (error);
		return;
	}

	if (result == NULL) {
		return;
	}
	g_ptr_array_foreach (result, (GFunc)_add_results, (gpointer)term);
	
	g_ptr_array_free  (result, TRUE);
	g_free (term);
}

static void
aff_search_engine_tracker_set_query (AffSearchEngine *engine,
				     AffResults *results,
				     gulong id, 
				     const gchar* query, 
				     AffQueryType type)
{
	AffSearchEngineTracker *tracker;
	AffTrackerSearchTerm *term;
	ServiceType service = SERVICE_FILES;
	tracker = AFF_SEARCH_ENGINE_TRACKER (engine);

	switch (type) {
		case AFF_QUERY_ALL:
			service = SERVICE_FILES;
			break;
		case AFF_QUERY_APPLICATIONS:
		case AFF_QUERY_BOOKMARKS:
			return;
		case AFF_QUERY_CONTACTS:
			service = SERVICE_CONTACTS;
			break;
		case AFF_QUERY_DOCUMENTS:
			service = SERVICE_DOCUMENTS;
			break;
		case AFF_QUERY_EMAILS:
			service = SERVICE_EMAILS;
			break;
		case AFF_QUERY_IMAGES:
			service = SERVICE_IMAGES;
			break;
		case AFF_QUERY_MUSIC:
			service = SERVICE_MUSIC;
			break;
		case AFF_QUERY_VIDEOS:
			service = SERVICE_VIDEOS;
			break;
		default:
			service = SERVICE_FILES;
			break;
	}
		
	term = g_new0 (AffTrackerSearchTerm, 1);
	term->tracker = tracker;
	term->id = id;
	term->results = GTK_WIDGET (results);
	term->type = type;
	

	tracker_search_text_detailed_async (tracker->details->client, 
					    -1, 
					    service, 
					    query, 
					    0, 20, 
					    (TrackerGPtrArrayReply) search_callback, 
					    (gpointer) term);					    
}
static void
aff_search_engine_tracker_class_init (AffSearchEngineTrackerClass *class)
{
	GObjectClass *gobject_class;
	AffSearchEngineClass *engine_class;

	parent_class = g_type_class_peek_parent (class);

	gobject_class = G_OBJECT_CLASS (class);
	gobject_class->finalize = finalize;

	engine_class = AFF_SEARCH_ENGINE_CLASS (class);
	engine_class->set_query = aff_search_engine_tracker_set_query;
}

static void
aff_search_engine_tracker_init (AffSearchEngineTracker *engine)
{
	engine->details = g_new0 (AffSearchEngineTrackerDetails, 1);
}


AffSearchEngine *
aff_search_engine_tracker_new (void)
{
	AffSearchEngineTracker *engine;
	TrackerClient *tracker_client;

	tracker_client =  tracker_connect (FALSE);

	if (!tracker_client) {
		return NULL;
	}

	engine = g_object_new (AFF_TYPE_SEARCH_ENGINE_TRACKER, NULL);

	engine->details->client = tracker_client;

	engine->details->query_pending = FALSE;
	
	engine->details->email = gtk_icon_theme_load_icon (gtk_icon_theme_get_default(),
                                                           "email",
                                                           48,
                                                           0,
                                                           NULL);

	return AFF_SEARCH_ENGINE (engine);
}
