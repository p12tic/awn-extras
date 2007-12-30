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

#include "aff-search-engine-beagle.h"

#include <libgnome/gnome-i18n.h>
#include <beagle/beagle.h>
#include <libgnomevfs/gnome-vfs-utils.h>
#include <string.h>

struct AffSearchEngineBeagleDetails {
	BeagleClient 	*client;
	gboolean 	query_pending;
	
	GdkPixbuf *email;
	GdkPixbuf *contact;
	
	BeagleQuery *current_query;
	GtkWidget *results;
	AffQueryType type;
	gulong id;	
};

static void  aff_search_engine_beagle_class_init       (AffSearchEngineBeagleClass *class);
static void  aff_search_engine_beagle_init             (AffSearchEngineBeagle      *engine);

G_DEFINE_TYPE (AffSearchEngineBeagle,
	       aff_search_engine_beagle,
	       AFF_TYPE_SEARCH_ENGINE);

static AffSearchEngineClass *parent_class = NULL;

static void
finalize (GObject *object)
{
	AffSearchEngineBeagle *beagle;

	beagle = AFF_SEARCH_ENGINE_BEAGLE (object);
	
	
	g_free (beagle->details);

	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(object);
}

static void
_hits_added (BeagleQuery *query, 
		   BeagleHitsAddedResponse *response, 
		   AffSearchEngineBeagle *engine)
{
	GSList *hits, *list;
	const char *uri = NULL;

	if (engine->details->current_query != query)
		return;
	
	hits = beagle_hits_added_response_get_hits (response);
	
	for (list = hits; list != NULL; list = list->next) {
		BeagleHit *hit = BEAGLE_HIT (list->data);
		
		const gchar *name;
		const gchar *desc;
		
		uri = beagle_hit_get_uri (hit);
		
		beagle_hit_get_one_property (hit, "beagle:Filename", &name);
		beagle_hit_get_one_property (hit, "beagle:MimeType", &desc);
			
		aff_results_add_uri (AFF_RESULTS (engine->details->results), engine->details->id,
		                     NULL, name, desc, uri);
		
		
		
	}
}

static void
_bookmarks_added (BeagleQuery *query, 
		   BeagleHitsAddedResponse *response, 
		   AffSearchEngineBeagle *engine)
{
	GSList *hits, *list;
	const char *uri = NULL;

	if (engine->details->current_query != query)
		return;
	
	hits = beagle_hits_added_response_get_hits (response);
	
	for (list = hits; list != NULL; list = list->next) {
		BeagleHit *hit = BEAGLE_HIT (list->data);
	
		uri = beagle_hit_get_uri (hit);
		
		GSList *p, *props;
		props = beagle_hit_get_all_properties (hit);
		g_print ("%s = \n", uri);
		for (p = props; p != NULL; p = p->next) {
			const char *key = beagle_property_get_key ((BeagleProperty *)p->data);
			const char *value = beagle_property_get_value ((BeagleProperty *)p->data);
			g_print ("%s : %s\n", key, value);
		}
		g_print ("\n\n");
		//beagle_hit_get_one_property (hit, "beagle:Filename", &name);
		//beagle_hit_get_one_property (hit, "beagle:MimeType", &desc);
			
		//aff_results_add_uri (AFF_RESULTS (engine->details->results), engine->details->id,
		//                     NULL, name, desc, uri);
		
		
		
	}
}

static void
_contacts_added (BeagleQuery *query, 
		   BeagleHitsAddedResponse *response, 
		   AffSearchEngineBeagle *engine)
{
	GSList *hits, *list;
	const char *uri = NULL;

	if (engine->details->current_query != query)
		return;
	
	hits = beagle_hits_added_response_get_hits (response);
	
	for (list = hits; list != NULL; list = list->next) {
		BeagleHit *hit = BEAGLE_HIT (list->data);
		gchar *name = NULL;
		const gchar *fullname;
		const gchar *email;
		gchar *exec = NULL;
		
		uri = beagle_hit_get_uri (hit);
		
		GSList *p, *props;
		props = beagle_hit_get_all_properties (hit);
		g_print ("%s = \n", uri);
		for (p = props; p != NULL; p = p->next) {
			char *key = beagle_property_get_key ((BeagleProperty *)p->data);
			char *value = beagle_property_get_value ((BeagleProperty *)p->data);
			g_print ("%s : %s\n", key, value);
		}
		g_print ("\n\n");		
		//continue;
				
		beagle_hit_get_one_property (hit, "fixme:FullName", &fullname);
		beagle_hit_get_one_property (hit, "fixme:Email", &email);
		
		if (fullname == NULL)
			continue;
		
		exec = g_strdup_printf ("evolution \"%s\"", uri);
		
		name = g_markup_escape_text (fullname, -1);
		aff_results_add_command (AFF_RESULTS (engine->details->results), 
						  engine->details->id,
		                     		  engine->details->contact, 
		                     		  name, email, exec);
		g_free (exec);
		g_free (name);
	}		
}

static void
_emails_added (BeagleQuery *query, 
		   BeagleHitsAddedResponse *response, 
		   AffSearchEngineBeagle *engine)
{
	GSList *hits, *list;
	const char *uri = NULL;

	if (engine->details->current_query != query)
		return;
	
	hits = beagle_hits_added_response_get_hits (response);
	
	for (list = hits; list != NULL; list = list->next) {
		BeagleHit *hit = BEAGLE_HIT (list->data);
		gchar *name = NULL;
		const gchar *title, *from, *to, *sent;
		gchar *desc = NULL;
		gchar *exec = NULL;
		
		uri = beagle_hit_get_uri (hit);
		/*
		GSList *p, *props;
		props = beagle_hit_get_all_properties (hit);
		g_print ("%s = \n", uri);
		for (p = props; p != NULL; p = p->next) {
			char *key = beagle_property_get_key ((BeagleProperty *)p->data);
			char *value = beagle_property_get_value ((BeagleProperty *)p->data);
			g_print ("%s : %s\n", key, value);
		}
		g_print ("\n\n");		
		continue;
		*/		
		beagle_hit_get_one_property (hit, "dc:title", &title);
		beagle_hit_get_one_property (hit, "fixme:from", &from);
		beagle_hit_get_one_property (hit, "fixme:to", &to);
		beagle_hit_get_one_property (hit, "isSent", &sent);
		
		if (title == NULL)
			continue;
		
		name = g_markup_escape_text (title, -1);
		if (sent)
			desc = g_markup_escape_text (to, -1);
		else	
			desc = g_markup_escape_text (from, -1);
		
		exec = g_strdup_printf ("evolution \"%s\"", uri);
					
		aff_results_add_command (AFF_RESULTS (engine->details->results), 
						  engine->details->id,
		                     		  engine->details->email, 
		                     		  name, desc, exec);
		g_free (exec);
		g_free (name);
		g_free (desc);
	}
}

static void
_filter_added (BeagleQuery *query, 
		   BeagleHitsAddedResponse *response, 
		   AffSearchEngineBeagle *engine)
{
	GSList *hits, *list;
	const char *uri = NULL;
	const gchar *mime;
		
	if (engine->details->current_query != query)
		return;
	
	hits = beagle_hits_added_response_get_hits (response);
	
	for (list = hits; list != NULL; list = list->next) {
		BeagleHit *hit = BEAGLE_HIT (list->data);
		
		gchar *name;
		gchar *desc;
		
		uri = beagle_hit_get_uri (hit);
		mime = beagle_hit_get_mime_type (hit);
		
		
		if (engine->details->type == AFF_QUERY_IMAGES) {
			const char *res = NULL;
			res = strstr (mime, "image");
			if (!res)
				continue;
			
			const char *filename;
			const char *height, *width;
			beagle_hit_get_one_property (hit, "beagle:ExactFilename", &filename);
			beagle_hit_get_one_property (hit, "fixme:height", &height);
			beagle_hit_get_one_property (hit, "fixme:width", &width);
			
			if (filename == NULL)
				continue;
		
			name = g_markup_escape_text (filename, -1);
			if (height && width) {
				char * temp = g_strdup_printf ("%s x %s", width, height);
				desc = g_markup_escape_text (temp, -1);
				g_free (temp);
			} else	
				desc = g_strdup (" "); 			
		
		} else if (engine->details->type == AFF_QUERY_MUSIC) {
			const char *res = NULL;
			res = strstr (mime, "audio");
			if (!res)
				continue;
			
			const char *filename, *title;
			const char *artist, *album;
			beagle_hit_get_one_property (hit, "beagle:ExactFilename", &filename);
			beagle_hit_get_one_property (hit, "fixme:title", &title);
			beagle_hit_get_one_property (hit, "fixme:artist", &artist);
			beagle_hit_get_one_property (hit, "fixme:album", &album);
			
			if (filename == NULL)
				continue;
			
			if (title)
				name = g_markup_escape_text (title, -1);
			else
				name = g_markup_escape_text (filename, -1);
				
			if (artist && album) {
				/* i18n: "by ARTIST from ALBUM */
				char * temp = g_strdup_printf (_("by %s from %s"), artist, album);
				desc = g_markup_escape_text (temp, -1);
				g_free (temp);
			
			} else if (artist) {
				desc = g_markup_escape_text (artist, -1);
			} else if (album) {
				desc = g_markup_escape_text (album, -1);
			} else	
				desc = g_strdup (" "); 			
		} else if (engine->details->type == AFF_QUERY_VIDEOS) {
			const char *res = NULL;
			res = strstr (mime, "video");
			if (!res)
				continue;
			
			const char *filename;
			const char *height, *width;
			beagle_hit_get_one_property (hit, "beagle:ExactFilename", &filename);
			beagle_hit_get_one_property (hit, "fixme:height", &height);
			beagle_hit_get_one_property (hit, "fixme:width", &width);
			
			if (filename == NULL)
				continue;
		
			name = g_markup_escape_text (filename, -1);
			if (height && width) {
				char * temp = g_strdup_printf ("%s x %s", width, height);
				desc = g_markup_escape_text (temp, -1);
				g_free (temp);
			} else	
				desc = g_strdup (" "); 	
		} else {
			
			const char *filename;
			beagle_hit_get_one_property (hit, "beagle:ExactFilename", &filename);
			
			if (filename == NULL)
				continue;
		
			name = g_markup_escape_text (filename, -1);
			char * temp = gnome_vfs_get_local_path_from_uri (uri);
			desc = g_markup_escape_text (temp, -1);
			g_free (temp);
			
		}
	
		aff_results_add_uri (AFF_RESULTS (engine->details->results), engine->details->id,
		                     NULL, name, desc, uri);
		
		g_free (name);
		g_free (desc);
		
	}
}

static void
aff_search_engine_beagle_set_query (AffSearchEngine *engine,
				     AffResults *results,
				     gulong id, 
				     const gchar* text, 
				     AffQueryType type)
{
	AffSearchEngineBeagle *beagle;
	GError *error = NULL;
	
	beagle = AFF_SEARCH_ENGINE_BEAGLE (engine);

	beagle->details->id = id;
	beagle->details->results = GTK_WIDGET (results);
	beagle->details->type = type;
	
	beagle->details->current_query = beagle_query_new ();

	switch (type) {
		case AFF_QUERY_ALL:
			beagle_query_add_hit_type (beagle->details->current_query, "File");
			g_signal_connect (beagle->details->current_query, "hits-added", 
					  G_CALLBACK (_hits_added), engine);
			break;
		case AFF_QUERY_APPLICATIONS:
			return;		
		case AFF_QUERY_BOOKMARKS:
			beagle_query_add_hit_type (beagle->details->current_query, "Bookmark");
			g_signal_connect (beagle->details->current_query, "hits-added", 
					  G_CALLBACK (_bookmarks_added), engine);		
			break;
		case AFF_QUERY_CONTACTS:
			beagle_query_add_hit_type (beagle->details->current_query, "Contact");
			g_signal_connect (beagle->details->current_query, "hits-added", 
					  G_CALLBACK (_contacts_added), engine);		
			break;
		case AFF_QUERY_EMAILS:
			beagle_query_add_hit_type (beagle->details->current_query, "MailMessage");
			g_signal_connect (beagle->details->current_query, "hits-added", 
					  G_CALLBACK (_emails_added), engine);		
			break;
		case AFF_QUERY_DOCUMENTS:
		case AFF_QUERY_IMAGES:
		case AFF_QUERY_MUSIC:
		case AFF_QUERY_VIDEOS:
			beagle_query_add_hit_type (beagle->details->current_query, "File");
			g_signal_connect (beagle->details->current_query, "hits-added", 
					  G_CALLBACK (_filter_added), engine);		
			break;		
		default:
			beagle_query_add_hit_type (beagle->details->current_query, "File");
			g_signal_connect (beagle->details->current_query, "hits-added", 
					  G_CALLBACK (_hits_added), engine);
			break;
	}
		
	beagle_query_set_max_hits (beagle->details->current_query, 20);
	
	beagle_query_add_text (beagle->details->current_query, text);
	
	if (!beagle_client_send_request_async (beagle->details->client,
					       BEAGLE_REQUEST (beagle->details->current_query), &error)) {
		g_print ("%s\n", error->message);
		g_error_free (error);
	}
					    
}
static void
aff_search_engine_beagle_class_init (AffSearchEngineBeagleClass *class)
{
	GObjectClass *gobject_class;
	AffSearchEngineClass *engine_class;

	parent_class = g_type_class_peek_parent (class);

	gobject_class = G_OBJECT_CLASS (class);
	gobject_class->finalize = finalize;

	engine_class = AFF_SEARCH_ENGINE_CLASS (class);
	engine_class->set_query = aff_search_engine_beagle_set_query;
}

static void
aff_search_engine_beagle_init (AffSearchEngineBeagle *engine)
{
	engine->details = g_new0 (AffSearchEngineBeagleDetails, 1);
}


AffSearchEngine *
aff_search_engine_beagle_new (void)
{
	AffSearchEngineBeagle *engine;
	BeagleClient *beagle_client;
	
	if (!beagle_util_daemon_is_running ()) {
		/* check whether daemon is running as beagle_client_new
		 * doesn't fail when a stale socket file exists */
		return NULL;
	}

	beagle_client = beagle_client_new (NULL);

	if (beagle_client == NULL) {
		return NULL;
	}

	engine = g_object_new (AFF_TYPE_SEARCH_ENGINE_BEAGLE, NULL);
	engine->details->client = beagle_client;

	engine->details->email = gtk_icon_theme_load_icon (gtk_icon_theme_get_default(),
                                                           "email",
                                                           48,
                                                           0,
                                                           NULL);
	g_object_ref (G_OBJECT (engine->details->email));

	engine->details->contact = gtk_icon_theme_load_icon (gtk_icon_theme_get_default(),
                                                           "contact-new",
                                                           48,
                                                           0,
                                                           NULL);
	g_object_ref (G_OBJECT (engine->details->contact));	
	return AFF_SEARCH_ENGINE (engine);
}
