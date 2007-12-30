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

#include "aff-search-engine-actions.h"

#include "aff-utils.h"

#include <libgnome/gnome-i18n.h>
#include <libgnomevfs/gnome-vfs-utils.h>
#include <libgnome/gnome-desktop-item.h>
#include <libgnomevfs/gnome-vfs.h>
#include <string.h>

struct AffSearchEngineActionsDetails {
	GList *dirs;
	GHashTable *actions;
};

typedef enum {
	AFF_ACTION_MATCH,
	AFF_ACTION_SCAN

} AffActionType;

typedef struct {
	GdkPixbuf *icon;
	gchar *name;
	gchar *desc;
	gchar *pattern;
	gchar *exec;
	AffActionType type;

} AffApplication;

typedef struct {
	AffSearchEngineActions *engine;
	GtkWidget *results;
	AffQueryType type;
	gulong id;
	gchar *query;

} AffActionsSearchTerm;

static void  aff_search_engine_actions_class_init       (AffSearchEngineActionsClass *class);
static void  aff_search_engine_actions_init             (AffSearchEngineActions      *engine);
static void finalize (GObject *object); 

G_DEFINE_TYPE (AffSearchEngineActions,
	       aff_search_engine_actions,
	       AFF_TYPE_SEARCH_ENGINE);

static AffSearchEngineClass *parent_class = NULL;

static void
_free_app (AffApplication *app)
{
	g_object_unref (G_OBJECT (app->icon));
	g_free (app->name);
	g_free (app->desc);
	g_free (app->pattern);
	g_free (app->exec);
	g_free (app);
}	

static void
_search_actions (const char *n, AffApplication *app, AffActionsSearchTerm *term)
{
	char *name = NULL;
	char *desc = NULL;
	char *temp = NULL;
	char *exec = NULL;
	
	if (app->type == AFF_ACTION_MATCH) {
		char *res = NULL;
		size_t len = strlen(app->pattern);
        	res = g_strstr_len (term->query, len+1, app->pattern);
		if (res == NULL) {
			return;
		}
		name = g_markup_escape_text (app->name, -1);
		temp = g_strdup_printf (app->desc, term->query+len);
		desc = g_markup_escape_text (temp, -1);
		exec = g_strdup_printf (app->exec, term->query+len);
				
		aff_results_add_command (AFF_RESULTS (term->results), term->id,
				         app->icon, name, desc, exec);
	
	} else {
		char *res = NULL;
		res = g_strstr_len (term->query,strlen (term->query), app->pattern);
		if (res == NULL) {
			return;
		}
		name = g_markup_escape_text (app->name, -1);
		temp = g_strdup_printf (app->desc, term->query);
		desc = g_markup_escape_text (temp, -1);
		exec = g_strdup_printf (app->exec, term->query);
				
		aff_results_add_command (AFF_RESULTS (term->results), term->id,
				         app->icon, name, desc, exec);		
	}	
	g_free (temp);
	g_free (name);
	g_free (desc);
	g_free (exec);
	
}

static void
aff_search_engine_actions_set_query (AffSearchEngine *engine,
				     AffResults *results,
				     gulong id, 
				     const gchar* query, 
				     AffQueryType type)
{
	AffSearchEngineActions *actions;
	AffActionsSearchTerm *term;
	actions = AFF_SEARCH_ENGINE_ACTIONS (engine);
	
	term = g_new0 (AffActionsSearchTerm, 1);
	term->engine = actions;
	term->id = id;
	term->results = GTK_WIDGET (results);
	term->type = type;
	term->query = g_strdup (query);
	
	g_hash_table_foreach (actions->details->actions, (GHFunc)_search_actions, (gpointer)term);
	
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

static void
aff_search_engine_actions_class_init (AffSearchEngineActionsClass *class)
{
	GObjectClass *gobject_class;
	AffSearchEngineClass *engine_class;

	parent_class = g_type_class_peek_parent (class);

	gobject_class = G_OBJECT_CLASS (class);
	gobject_class->finalize = finalize;

	engine_class = AFF_SEARCH_ENGINE_CLASS (class);
	engine_class->set_query = aff_search_engine_actions_set_query;
}

static void
aff_search_engine_actions_init (AffSearchEngineActions *engine)
{
	engine->details = g_new0 (AffSearchEngineActionsDetails, 1);
	engine->details->dirs = NULL;
	engine->details->actions = NULL;
}

static void 
strrep( char *str, char find, char replace )
{
        int len = strlen (str );
        int i = 0;
        for (i=0; i<len; i++ ) {
                if ( str[i] == find )
                        str[i] = replace;
        }
        
}

static void
_add_app (AffSearchEngineActions *engine, const char *uri)
{
	if (uri == NULL)
		return;
	AffApplication *app;
	app = g_new0 (AffApplication, 1);
	const gchar *type;
	GnomeDesktopItem *item= NULL;
	
	item = gnome_desktop_item_new_from_file (uri, GNOME_DESKTOP_ITEM_LOAD_ONLY_IF_EXISTS, NULL);
        
        if (item == NULL) {
        	g_free (app);
        	return;
        }
        app->icon = aff_utils_get_app_icon (gnome_desktop_item_get_string (item, GNOME_DESKTOP_ITEM_ICON));
	app->name = g_strdup (gnome_desktop_item_get_localestring (item, GNOME_DESKTOP_ITEM_NAME));
	app->desc = g_strdup (gnome_desktop_item_get_localestring (item, GNOME_DESKTOP_ITEM_COMMENT));
	app->pattern = g_strdup (gnome_desktop_item_get_localestring (item, GNOME_DESKTOP_ITEM_CATEGORIES));;
	strrep(app->pattern, '_', ' ');
	app->exec = g_strdup (gnome_desktop_item_get_string (item, GNOME_DESKTOP_ITEM_EXEC));
	
	type = gnome_desktop_item_get_localestring (item, GNOME_DESKTOP_ITEM_TYPE);
	if (strcmp (type, "match") == 0)
		app->type = AFF_ACTION_MATCH;
	else
		app->type = AFF_ACTION_SCAN;
	
	if (item)
		gnome_desktop_item_unref (item);
	/* app application to the hash */
	g_hash_table_insert (engine->details->actions, app->name, app);
}

static void 
watch_callback (GnomeVFSMonitorHandle *handle,const gchar *dir,
					      const gchar *file,
					      GnomeVFSMonitorEventType type,
					      AffSearchEngineActions *engine)
{
        if (strstr(file, ".desktop") == NULL)
                return;
        GString *uri;
        uri = g_string_new(file);
        g_string_erase(uri, 0, 7);
        
        if ( type == GNOME_VFS_MONITOR_EVENT_CREATED) {
                g_print("Created : %s\n", uri->str);
                _add_app(engine, uri->str);        
        }
        else if ( type == GNOME_VFS_MONITOR_EVENT_DELETED)
                g_print("Deleted : %s\n", uri->str);
        else
                ;
                
        g_string_free(uri, TRUE);
}

static void
_load_actions (const gchar *directory, AffSearchEngineActions *engine)
{
	GDir *dir;
	const gchar *name = NULL;
	
	g_print ("Action Engine : Scanning %s\n", directory);
	
	dir = g_dir_open(directory, 0, NULL);
	while ( name = g_dir_read_name(dir)) {
		gchar *path = g_build_filename (directory, name, NULL);
		
		if (g_file_test (path, G_FILE_TEST_IS_DIR)) {
			
			_load_actions (path, engine);
		} else {
			const char *res = strstr(name, ".desktop");
			if (  res != NULL ) {
				_add_app (engine, path);
			}
		}
		g_free (path);
	}
	g_dir_close(dir);

        GnomeVFSMonitorHandle *handle;
        GnomeVFSResult result;
        
        result = gnome_vfs_monitor_add (&handle, directory, GNOME_VFS_MONITOR_DIRECTORY, 
        				(GnomeVFSMonitorCallback)watch_callback, 
        				(gpointer)engine);
        if(! result == GNOME_VFS_OK)
                g_print("VFS ERROR : %s", gnome_vfs_result_to_string (result));	
}

AffSearchEngine *
aff_search_engine_actions_new (void)
{
	AffSearchEngineActions *engine;
	
	engine = g_object_new (AFF_TYPE_SEARCH_ENGINE_ACTIONS, NULL);

	/* Load application directories */
        gchar *dir = NULL;

        char *home;
        home = getenv("HOME");
        if (home != NULL) {
		dir = g_strdup_printf("%s/.gnome2/affinity/actions", home);
	}
	
              
        /* Add user defined applications path to service directory list */
        if (dir != NULL) {
	        engine->details->dirs = g_list_append (engine->details->dirs, dir);
        }
                      
        /* Add system defined applications path to service directory list */
        dir = g_strdup (ACTIONDIR);
	engine->details->dirs = g_list_append (engine->details->dirs, dir);
	
	engine->details->actions = g_hash_table_new (g_str_hash, g_str_equal);
        
	g_list_foreach (engine->details->dirs, (GFunc)_load_actions, (gpointer)engine);
	
	return AFF_SEARCH_ENGINE (engine);
}

static void
finalize (GObject *object)
{
	AffSearchEngineActions *actions;

	actions = AFF_SEARCH_ENGINE_ACTIONS (object);
	
	g_free (actions->details);

	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(object);
}


