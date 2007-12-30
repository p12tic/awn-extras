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

#include <string.h>


#include "aff-results.h"

#include <libgnome/gnome-i18n.h>
#include <libgnomevfs/gnome-vfs.h>
#include <libgnomevfs/gnome-vfs-mime-handlers.h>
#include <libgnome/gnome-desktop-item.h>

#include "aff-utils.h"
#include "aff-search-engine.h"
#include "aff-search-engine-actions.h"
#include "aff-search-engine-apps.h"
#include "aff-start.h"
#include "aff-window.h"

#ifdef HAVE_TRACKER
#include "aff-search-engine-tracker.h"
#endif

#ifdef HAVE_BEAGLE
#include "aff-search-engine-beagle.h"
#endif

#define AFF_RESULTS_GET_PRIVATE(obj) (G_TYPE_INSTANCE_GET_PRIVATE ((obj), AFF_TYPE_RESULTS, AffResultsPrivate))

G_DEFINE_TYPE (AffResults, aff_results, GTK_TYPE_TREE_VIEW)

/* STRUCTS & ENUMS */
struct _AffResultsPrivate
{
	AffinityApp *app;
	
	gulong id;
	
	AffSearchEngine *act_engine;
	AffSearchEngine *app_engine;
	AffSearchEngine *doc_engine;
	
	GdkPixbuf *pixbufs[AFF_N_QUERIES];
	
	GtkWidget *menu;
};

static void aff_results_row_activated(GtkTreeView       *tree_view,
                                         GtkTreePath       *path,
                                         GtkTreeViewColumn *column,
                                         AffResults     *this);
static void _make_new_model (AffResults *results);                                         

static GtkTreeViewClass *parent_class;

/*
static gchar* pixbuf_names[] = {"search",
			  "applications-system",
			  "bookmark-new",
			  "system-users",
			  "text-x-generic",
			  "email",
			  "image-x-generic",
			  "video-x-generic"};
*/
static gboolean
_find_filter (const char *filters, const char *term)
{
	gchar **tokens = NULL;
	gchar **filter = NULL;
	
	if (term == NULL)
		return FALSE;
	
	tokens = g_strsplit (filters, ",", -1);
	
	for (filter = tokens; *filter; filter++) {
		if (strcmp (filter[0], term) == 0) {
			g_strfreev (tokens);
			return TRUE;
		}
	}
	g_strfreev (tokens);	
	return FALSE;
}

static AffQueryType
aff_results_find_type_for_string (AffResults *results, GString *query)
{
	AffResultsPrivate *priv;
	AffSettings *s;
	AffQueryType type = AFF_QUERY_ALL;
	gchar **term = NULL;
	
	int i = 0;
	int res = 0;
	for (i=0; i<query->len; i++) {
		if (query->str[i] == ':')
			res++;
	}
	if (res == 0)
		return type;
	
	priv = AFF_RESULTS_GET_PRIVATE (results);
	s = priv->app->settings;
	
	term =  g_strsplit (query->str, ":", 0);

	
	if (_find_filter (s->apps, term[0])) 
		type = AFF_QUERY_APPLICATIONS;
		
	else if (_find_filter (s->books, term[0])) 
		type = AFF_QUERY_BOOKMARKS;
		
	else if (_find_filter (s->contacts, term[0])) 
		type = AFF_QUERY_CONTACTS;

	else if (_find_filter (s->docs, term[0])) 
		type = AFF_QUERY_DOCUMENTS;

	else if (_find_filter (s->emails, term[0])) 
		type = AFF_QUERY_EMAILS;

	else if (_find_filter (s->images, term[0])) 
		type = AFF_QUERY_IMAGES;
	
	else if (_find_filter (s->music, term[0])) 
		type = AFF_QUERY_MUSIC;

	else if (_find_filter (s->vids, term[0])) 
		type = AFF_QUERY_VIDEOS;

	else
		;

	if (type != AFF_QUERY_ALL)
		query = g_string_assign (query, term[1]);
		
	g_strfreev (term);
	return type;
}

static void 
_make_new_model (AffResults *results)
{
        GtkListStore *model = gtk_list_store_new (N_COLUMNS,
                                   		  GDK_TYPE_PIXBUF,
                                   		  G_TYPE_STRING, 
                                   		  G_TYPE_STRING,
                                   		  G_TYPE_STRING);
        
        gtk_tree_view_set_model(GTK_TREE_VIEW(results), GTK_TREE_MODEL(model));
	g_object_unref(G_OBJECT(model));
	
}

void 
aff_results_set_search_string (AffResults *results, const gchar *text)
{
	AffResultsPrivate *priv;
	AffQueryType type;
	GString *query = NULL;
	query = g_string_new (text);
	
	priv = AFF_RESULTS_GET_PRIVATE (results);
	
	_make_new_model (results);
	gtk_widget_queue_draw (priv->app->window);
	
	type = aff_results_find_type_for_string (results, query);
	
	priv->id++;

	aff_search_engine_set_query (priv->act_engine, results,
			             priv->id, query->str, type);	
	aff_search_engine_set_query (priv->app_engine, results,
			             priv->id, query->str, type);
	aff_search_engine_set_query (priv->doc_engine, results,
			             priv->id, query->str, type);
	g_string_free (query, TRUE);

	gtk_widget_queue_draw (priv->app->window);
}

void 
aff_results_add_uri (AffResults *this, gulong id,
				GdkPixbuf *pixbuf, 
				const gchar *name,
				const gchar *desc,
				const gchar *uri)
{
	AffResultsPrivate *priv;
	
	priv = AFF_RESULTS_GET_PRIVATE (this);
	
	if (priv->id != id)
		return;
	GtkTreeModel *model;
	GtkTreeIter iter;
	gchar *markup;
	
	model = gtk_tree_view_get_model (GTK_TREE_VIEW (this));
	if (model == NULL) {
		_make_new_model (this);
		model = gtk_tree_view_get_model (GTK_TREE_VIEW (this));
	}
	markup = g_strdup_printf ("<span size='larger' weight='bold'>%s</span>\n%s", name, desc);
	
	if (pixbuf == NULL) {
		pixbuf = aff_utils_get_icon (uri);
	}
	gtk_list_store_append (GTK_LIST_STORE(model), &iter);
      	gtk_list_store_set (GTK_LIST_STORE(model), &iter,
                            COLUMN_IMAGE, pixbuf,
                            COLUMN_STRING, markup,
                            COLUMN_URI, uri,
                            COLUMN_COMMAND, NULL,
                                        -1);	
                                        
 	g_object_unref (G_OBJECT (pixbuf));
 	g_free (markup);
	
	gtk_widget_queue_draw (priv->app->window);
}

void 
aff_results_add_command (AffResults *this, gulong id,  
					    GdkPixbuf *pixbuf,
					    const gchar *name,
					    const gchar *desc,
					    const gchar *command)
{
	AffResultsPrivate *priv;
	
	priv = AFF_RESULTS_GET_PRIVATE (this);
	
	if (priv->id != id)
		return;
	GtkTreeModel *model;
	GtkTreeIter iter;
	gchar *markup;
	
	model = gtk_tree_view_get_model (GTK_TREE_VIEW (this));
	if (model == NULL) {
		_make_new_model (this);
		model = gtk_tree_view_get_model (GTK_TREE_VIEW (this));
	}
	markup = g_strdup_printf ("<span size='larger' weight='bold'>%s</span>\n%s", name, desc);
	
	gtk_list_store_append (GTK_LIST_STORE(model), &iter);
      	gtk_list_store_set (GTK_LIST_STORE(model), &iter,
                            COLUMN_IMAGE, pixbuf,
                            COLUMN_STRING, markup,
                            COLUMN_URI, NULL,
                            COLUMN_COMMAND, command,
                                        -1);		
	g_free (markup);
	
	gtk_widget_queue_draw (priv->app->window);
}

/* CALLBACKS */

static AffResults *g_results = NULL; /* Yuk */

static void
aff_results_menu_item_activated (GtkMenuItem *item, GnomeVFSMimeApplication *app)
{
	GtkTreeView *treeview = GTK_TREE_VIEW (g_results);
        GtkTreeSelection *select;
        GtkTreeModel *model;
        GtkTreeIter iter;
        char *uri = NULL;
        select = gtk_tree_view_get_selection(treeview);
        gtk_tree_selection_get_selected( select, &model, &iter);
        
        gtk_tree_model_get (model, &iter, 
        		    COLUMN_URI, &uri,
        		    -1) ;
	
	if (uri == NULL) {
		return;
	}
	
	GnomeVFSResult res;
	GList *args = NULL;
	args = g_list_append (args, uri);
	const char *name = gnome_vfs_mime_application_get_name (app);
	g_print ("Launching with : %s", name);
	
	res = gnome_vfs_mime_application_launch (app, args);
	
	g_list_free (args);
	
	g_free (uri);
	
	//affinity_app_hide (priv->app);
}

static void
aff_results_popup_menu(AffResults *results)
{
	AffResultsPrivate *priv;
	
	priv = AFF_RESULTS_GET_PRIVATE (results);
	
	g_results = results;
	if (priv->menu)
		gtk_widget_destroy (priv->menu);
	
	GtkTreeView *treeview = GTK_TREE_VIEW (results);
        GtkTreeSelection *select;
        GtkTreeModel *model;
        GtkTreeIter iter;
        char *uri = NULL;
        const char *mimetype;
        select = gtk_tree_view_get_selection(treeview);
        gtk_tree_selection_get_selected( select, &model, &iter);
        
        gtk_tree_model_get (model, &iter, 
        		    COLUMN_URI, &uri,
        		    -1) ;
	
	if (uri == NULL) {
		return;
	}	
	
	mimetype = gnome_vfs_get_mime_type_for_name (uri);

	GList *apps, *a;
	GtkWidget *menu = gtk_menu_new ();
	priv->menu = menu;
	
	apps = gnome_vfs_mime_get_all_applications_for_uri (uri, mimetype);
	
	for (a = apps; a != NULL; a = a->next) {	
		GnomeVFSMimeApplication *app = (GnomeVFSMimeApplication *)a->data;
		const char *name = gnome_vfs_mime_application_get_name (app);
		const char *icon_name = gnome_vfs_mime_application_get_icon (app);
		char *markup = NULL;
		markup = g_strdup_printf (_("Open with \"%s\""), name);
		
		GdkPixbuf *icon = aff_utils_get_app_icon_sized (icon_name, 24, 24);
		GtkWidget *image = gtk_image_new_from_pixbuf (icon);
		GtkWidget *item = gtk_image_menu_item_new_with_label (markup);
		gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item), image);
		
		g_signal_connect (G_OBJECT (item), "activate",
				  G_CALLBACK (aff_results_menu_item_activated), (gpointer)app);
		
		gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);
		gtk_widget_show_all (item);
	}
	
	//gnome_vfs_mime_application_list_free (apps);
	g_list_free (apps);
	g_free(uri);
        
        gtk_menu_popup (GTK_MENU (menu), NULL, NULL, NULL, NULL, 3, gtk_get_current_event_time() );
}

static gboolean
aff_results_button_pressed (GtkWidget *treeview, GdkEventButton *event, gpointer userdata)
{
	if (event->type == GDK_BUTTON_PRESS  &&  event->button == 3)
		aff_results_popup_menu(AFF_RESULTS (treeview));

	return FALSE;
}

static gboolean
aff_results_show_menu (GtkWidget *treeview, gpointer userdata)
{
	return FALSE;
	aff_results_popup_menu(AFF_RESULTS (treeview));
	return TRUE;
}


/* AFF RESULTS NEW */

static void
aff_results_class_init( AffResultsClass *this_class )
{
        GObjectClass *g_obj_class;
        GtkWidgetClass *widget_class;
        
	parent_class = g_type_class_peek_parent(this_class); 
	
	g_obj_class = G_OBJECT_CLASS(this_class);
	g_type_class_add_private (g_obj_class, sizeof (AffResultsPrivate));       
        
        g_obj_class = G_OBJECT_CLASS( this_class );
        widget_class = GTK_WIDGET_CLASS( this_class );      
}

static void
aff_results_init( AffResults *results )
{
	AffResultsPrivate *priv;
	
	priv = AFF_RESULTS_GET_PRIVATE (results);
	
	priv->id = 0;
	
	priv->act_engine = aff_search_engine_actions_new ();
	priv->app_engine = aff_search_engine_apps_new ();
	priv->menu = NULL;
	
	
#ifdef HAVE_TRACKER
	priv->doc_engine = aff_search_engine_tracker_new ();
	g_print("Desktop Search Engine : Tracker\n");
#elif HAVE_BEAGLE
	priv->doc_engine = aff_search_engine_beagle_new ();
	g_print("Desktop Search Engine : Beagle\n");	
#else
	priv->doc_engine = NULL;	
	g_print("Desktop Search Engine : None\nYou may need to install development packages of either Beagle or Tracker.");		
#endif

}

GtkWidget *
aff_results_new (AffinityApp *app )
{
        AffResults *this = g_object_new(AFF_TYPE_RESULTS,
                                          "headers-visible", FALSE,
                                          "enable-search", FALSE,
                                          "rules-hint", TRUE,
                                          "hover-selection", TRUE,
                                          NULL);
        
	AffResultsPrivate *priv;
	
	priv = AFF_RESULTS_GET_PRIVATE (this);

	priv->app = app;	
	
        GtkTreeViewColumn   *col;
        GtkCellRenderer     *renderer;
        
        /* --- Column #1 --- */
  
        col = gtk_tree_view_column_new();

        gtk_tree_view_column_set_title(col, "Image");

        /* pack tree view column into tree view */
        gtk_tree_view_append_column(GTK_TREE_VIEW(this), col);

        renderer = gtk_cell_renderer_pixbuf_new();

        /* pack cell renderer into tree view column */
        gtk_tree_view_column_pack_start(col, renderer, TRUE);

        /* connect 'text' property of the cell renderer to
        *  model column that contains the first name */
        gtk_tree_view_column_add_attribute(col, renderer, "pixbuf", COLUMN_IMAGE);
        gtk_tree_view_column_set_spacing(col, 10);

        /* --- Column #2 --- */

        col = gtk_tree_view_column_new();
        gtk_tree_view_column_set_title(col, "Name");

        /* pack tree view column into tree view */
        gtk_tree_view_append_column(GTK_TREE_VIEW(this), col);

        renderer = gtk_cell_renderer_text_new();

        /* pack cell renderer into tree view column */
        gtk_tree_view_column_pack_start(col, renderer, TRUE);

        /* connect 'text' property of the cell renderer to
        *  model column that contains the last name */
        gtk_tree_view_column_add_attribute(col, renderer, "markup", COLUMN_STRING);
        gtk_tree_view_column_set_spacing(col, 10);
        
        g_signal_connect(G_OBJECT(this), "row-activated",
	                  G_CALLBACK(aff_results_row_activated),
	                  (gpointer)this);

	g_signal_connect(G_OBJECT(this), "button-press-event", 
			 G_CALLBACK (aff_results_button_pressed), NULL);
	g_signal_connect(G_OBJECT(this), "popup-menu", 
			 G_CALLBACK (aff_results_show_menu), NULL);	                  
	                  
        return GTK_WIDGET(this);
}

static void aff_results_row_activated(GtkTreeView       *treeview,
                                      GtkTreePath       *path,
                                      GtkTreeViewColumn *column,
                                      AffResults     *this)
{
	AffResultsPrivate *priv;
	
	priv = AFF_RESULTS_GET_PRIVATE (this);
	GtkTreeSelection *select;
        GtkTreeModel *model;
        GtkTreeIter iter;
        char *uri = NULL;
        char *command = NULL;
        char *exec = NULL;
        
        select = gtk_tree_view_get_selection(treeview);
        gtk_tree_selection_get_selected( select, &model, &iter);
        
        gtk_tree_model_get (model, &iter, 
        		    COLUMN_URI, &uri, 
        		    COLUMN_COMMAND, &command,
        		    -1) ;

	if (uri) {
		char *res = NULL;
		res = strstr (uri, ".desktop");
		if (res) {
			GnomeDesktopItem *item= NULL;
			item = gnome_desktop_item_new_from_file (uri, GNOME_DESKTOP_ITEM_LOAD_ONLY_IF_EXISTS, NULL);
			
			if (item != NULL) {
				GList *args = NULL;
				gnome_desktop_item_launch_on_screen (item,
                                             			     args,
                                             			     0,
                                                                     gdk_screen_get_default(),
                                             			     -1,
                                             			     NULL);
				gnome_desktop_item_unref (item);                                             		
				gtk_widget_hide (priv->app->window);
				priv->app->visible = FALSE;	
				aff_start_app_launched (AFF_START (priv->app->start), uri);	     
				return;
			}	
			
		} else {
			exec = g_strdup_printf ("%s %s", priv->app->settings->open_uri, uri);
			g_free (uri);
		}
	} else if (command) {
		exec = g_strdup (command);
		g_free (command);
	} else
		return;
	
	gdk_spawn_command_line_on_screen (gdk_screen_get_default (),
                                          exec,
                                          NULL);
        g_free(exec);
        
        affinity_app_hide (priv->app);
}

                                        
