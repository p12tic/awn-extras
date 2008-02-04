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

#include "aff-search-engine-apps.h"

#include "aff-utils.h"

#include <libawn/awn-desktop-item.h>
#include <libawn/awn-vfs.h>
#include <string.h>

struct AffSearchEngineAppsDetails {
	GList *dirs;
	GHashTable *apps;
};

typedef struct {
	GdkPixbuf *icon;
	gchar *icon_name;
	gchar *name;
	gchar *comment;
	gchar *generic_name;
	gint new;
	gchar *uri;

} AffApplication;

typedef struct {
	AffSearchEngineApps *engine;
	GtkWidget *results;
	AffQueryType type;
	gulong id;
	gchar *query;

} AffAppsSearchTerm;

static const char* strstri(const char *haystack, const char *needle);
static void  aff_search_engine_apps_class_init       (AffSearchEngineAppsClass *class);
static void  aff_search_engine_apps_init             (AffSearchEngineApps      *engine);
static void finalize (GObject *object); 

G_DEFINE_TYPE (AffSearchEngineApps,
	       aff_search_engine_apps,
	       AFF_TYPE_SEARCH_ENGINE);

static AffSearchEngineClass *parent_class = NULL;

static void
_free_app (AffApplication *app)
{
	g_object_unref (G_OBJECT (app->icon));
	g_free (app->name);
	g_free (app->comment);
	g_free (app->generic_name);
	g_free (app->uri);
	g_free (app);
}	

static void
_search_apps (const char *n, AffApplication *app, AffAppsSearchTerm *term)
{
	const char *res = NULL;
	char *name = NULL;
	char *desc = NULL;
	res = strstri (app->name, term->query);
	
	if (!res && app->comment) 
		res = strstri (app->comment, term->query);

	if (res) {
		name = g_markup_escape_text (app->name, -1);
		if (app->comment)
			desc = g_markup_escape_text (app->comment, -1);
		else
			desc = g_markup_escape_text (app->generic_name, -1);
			
		if (app->icon == NULL) {
			app->icon = aff_utils_get_app_icon (app->icon_name);
			if (app->icon)
				g_object_ref (G_OBJECT (app->icon));
		} else
			g_object_ref (G_OBJECT (app->icon));
		
		aff_results_add_uri (AFF_RESULTS (term->results), term->id,
				         app->icon, name, desc, app->uri);
		g_free (name);
		g_free (desc);
	}
	
}

static void
aff_search_engine_apps_set_query (AffSearchEngine *engine,
				     AffResults *results,
				     gulong id, 
				     const gchar* query, 
				     AffQueryType type)
{
	AffSearchEngineApps *apps;
	AffAppsSearchTerm *term;
	apps = AFF_SEARCH_ENGINE_APPS (engine);
	
	if (type == AFF_QUERY_ALL || type == AFF_QUERY_APPLICATIONS) {
		
		if (strlen (query) < 2)
			return;	
	} else
		return;
	
	term = g_new0 (AffAppsSearchTerm, 1);
	term->engine = apps;
	term->id = id;
	term->results = GTK_WIDGET (results);
	term->type = type;
	term->query = g_strdup (query);
	
	g_hash_table_foreach (apps->details->apps, (GHFunc)_search_apps, (gpointer)term);
	
	g_free (term->query);
	g_free (term);
}

static gchar *
_normalize (const gchar *string)
{
	gchar *temp = NULL;
	gchar *ret = NULL;
	
	temp = g_utf8_normalize (string, -1, G_NORMALIZE_ALL);
	ret = g_utf8_casefold (string, -1);
	
	g_free (temp);
	return ret;
}

static const char *
strstri(const char *haystack, const char *needle)
{
	const char *res;	
	
	gchar *n_hay = NULL;
	gchar *n_nee = NULL;
	
	n_hay = _normalize (haystack);
	n_nee = _normalize (needle);	
	
	res = strstr (n_hay, n_nee);

	g_free (n_hay);
	g_free (n_nee);	
	return res;
}

static void
aff_search_engine_apps_class_init (AffSearchEngineAppsClass *class)
{
	GObjectClass *gobject_class;
	AffSearchEngineClass *engine_class;

	parent_class = g_type_class_peek_parent (class);

	gobject_class = G_OBJECT_CLASS (class);
	gobject_class->finalize = finalize;

	engine_class = AFF_SEARCH_ENGINE_CLASS (class);
	engine_class->set_query = aff_search_engine_apps_set_query;
}

static void
aff_search_engine_apps_init (AffSearchEngineApps *engine)
{
	engine->details = g_new0 (AffSearchEngineAppsDetails, 1);
	engine->details->dirs = NULL;
	engine->details->apps = NULL;
}

static void
_add_app (AffSearchEngineApps *engine, const char *uri)
{
	AffApplication *app;
	app = g_new0 (AffApplication, 1);

	AwnDesktopItem *item = awn_desktop_item_new ((gchar*)uri);

	if (item == NULL) {
		g_free (app);
		return;
	}
	 if (awn_desktop_item_get_item_type (item) != "Application") {
		g_free (app);
		awn_desktop_item_free (item);
		return;
	}

	app->icon = NULL;
	app->icon_name = g_strdup (awn_desktop_item_get_icon (item, gtk_icon_theme_get_default ()));
	app->name = g_strdup (awn_desktop_item_get_name (item));
	app->comment = g_strdup (awn_desktop_item_get_localestring (item, "Comment"));
	app->generic_name = NULL;
	app->new = 0;
	app->uri = g_strdup (uri);

	if (item) {
		awn_desktop_item_free (item);
	}

	/* app application to the hash */
	g_hash_table_insert (engine->details->apps, app->name, app);
}

static void
watch_callback (AwnVfsMonitor *monitor, const gchar *dir,
                const gchar *file,
                AwnVfsMonitorEvent event,
                AffSearchEngineApps *engine)
{
	if (strstr(file, ".desktop") == NULL) {
		return;
	}
	GString *uri;
	uri = g_string_new(file);
	g_string_erase(uri, 0, 7);

	switch (event) {
		case AWN_VFS_MONITOR_EVENT_CREATED:
			g_print("Created : %s\n", uri->str);
			_add_app(engine, uri->str);
			break;
		case AWN_VFS_MONITOR_EVENT_DELETED:
			g_print("Deleted : %s\n", uri->str);
			break;
		default:
			break;
	}
		g_string_free(uri, TRUE);
}

static void
_load_apps (const gchar *directory, AffSearchEngineApps *engine)
{
	GDir *dir;
	const gchar *name = NULL;

	g_print ("Application Engine : Scanning %s\n", directory);

	dir = g_dir_open(directory, 0, NULL);
	while ((name = g_dir_read_name(dir))) {
		gchar *path = g_build_filename (directory, name, NULL);

		if (g_file_test (path, G_FILE_TEST_IS_DIR)) {
			_load_apps (path, engine);
		} else {
			const char *res = strstr(name, ".desktop");
			if (  res != NULL ) {
				_add_app (engine, path);
			}
		}
		g_free (path);
	}
	g_dir_close(dir);

	AwnVfsMonitor *monitor = awn_vfs_monitor_add ((gchar*)directory, AWN_VFS_MONITOR_DIRECTORY,
	                                              (AwnVfsMonitorFunc)watch_callback, 
	                                              (gpointer)engine);
	if (!monitor) {
		g_message ("VFS ERROR");
	}
}

AffSearchEngine *
aff_search_engine_apps_new (void)
{
	AffSearchEngineApps *engine;

	engine = g_object_new (AFF_TYPE_SEARCH_ENGINE_APPS, NULL);

	/* Load application directories */
	gchar *dir = g_strdup_printf ("%s/applications", g_get_user_data_dir ());

	/* Add user defined applications path to service directory list */
	engine->details->dirs = g_list_append (engine->details->dirs, dir);

	/* Add system defined applications path to service directory list */
	const gchar * const *dir_array = g_get_system_data_dirs ();
	gint i;
	for (i = 0; dir_array[i]; i++) {
		dir = g_strdup_printf ("%s/applications", dir_array[i]);
		engine->details->dirs = g_list_append (engine->details->dirs, dir);
	}
	engine->details->apps = g_hash_table_new (g_str_hash, g_str_equal);

	g_list_foreach (engine->details->dirs, (GFunc)_load_apps, (gpointer)engine);

	return AFF_SEARCH_ENGINE (engine);
}

static void
finalize (GObject *object)
{
	AffSearchEngineApps *apps;

	apps = AFF_SEARCH_ENGINE_APPS (object);

	g_free (apps->details);

	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(object);
}
