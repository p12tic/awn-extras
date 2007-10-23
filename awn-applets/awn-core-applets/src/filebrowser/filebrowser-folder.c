/*
 * Copyright (c) 2007 Timon David Ter Braak
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#include <string.h>
#include <math.h>
#include <gtk/gtk.h>
#include <libawn/awn-applet-dialog.h>
#include <libgnomevfs/gnome-vfs.h>

#include "filebrowser-folder.h"
#include "filebrowser-icon.h"
#include "filebrowser-defines.h"
#include "filebrowser-gconf.h"
#include "filebrowser-utils.h"

G_DEFINE_TYPE( FileBrowserFolder, filebrowser_folder, GTK_TYPE_EVENT_BOX )

#define COL_FILEBROWSERICON 0

static GtkEventBoxClass *parent_class = NULL;

/**
 * Compare function for sorting the strings of the filebrowser icons
 * -dirs before files
 * -case insensitive
 */
static gint filebrowser_folder_sort_list(
    gconstpointer a,
    gconstpointer b ) {

    if ( a == NULL || b == NULL ) {
        return ( a - b );
    }

    GnomeVFSURI *uri_a = FILEBROWSER_ICON( a )->uri;
    GnomeVFSURI *uri_b = FILEBROWSER_ICON( b )->uri;

    if ( !( FILEBROWSER_ICON( a )->desktop_item || FILEBROWSER_ICON( b )->desktop_item ) ) {
        if ( uri_a == NULL || uri_b == NULL ) {
            return ( uri_a - uri_b );
        }
    }

    if ( is_directory( uri_a ) && !is_directory( uri_b ) ) {
        return -1;
    } else if ( !is_directory( uri_a ) && is_directory( uri_b ) ) {
        return 1;
    }

    gchar *name_a = FILEBROWSER_ICON( a )->name;
    gchar *name_b = FILEBROWSER_ICON( b )->name;
    gint retval = 0;

    if ( g_ascii_strcasecmp( name_a, name_b ) == 0 ) {
        retval = 0;
    } else {
        gchar *dota = strrchr( name_a, '.' ), *dotb = strrchr( name_b, '.' );

        if ( dota )
            *dota = '\0';
        if ( dotb )
            *dotb = '\0';

        retval = g_ascii_strcasecmp( name_a, name_b );

        if ( retval == 0 ) {
            if ( dota )
                *dota = '.';
            if ( dotb )
                *dotb = '.';
            retval = g_ascii_strcasecmp( name_a, name_b );
        }
    }

    return retval;
}

/**
 * Add a new icon to the filebrowser container
 * -checks for valid uri
 * -create icon widget
 * -compose applet icon
 */
static gboolean filebrowser_folder_add(
    FileBrowserFolder * folder,
    GnomeVFSURI * file ) {
    
    if( !file || !gnome_vfs_uri_exists( file ) ){
    	return FALSE;
    }

    GnomeVFSFileInfo *info = gnome_vfs_file_info_new(  );
    GnomeVFSFileInfoOptions options;

    options = GNOME_VFS_FILE_INFO_GET_MIME_TYPE;
    options |= GNOME_VFS_FILE_INFO_FOLLOW_LINKS;
    options |= GNOME_VFS_FILE_INFO_FORCE_FAST_MIME_TYPE;

    GnomeVFSResult res = gnome_vfs_get_file_info_uri( file, info, options );

    if ( res != GNOME_VFS_OK ) {
        g_print( "Could not read file info for \"%s\" due: %s\n",
                 gnome_vfs_uri_to_string( file, 0 ), gnome_vfs_result_to_string( res ) );
        return FALSE;
    }

	// do not show files if not desired
	if( !filebrowser_gconf_show_files() && info->type == GNOME_VFS_FILE_TYPE_REGULAR ){
		return FALSE;
	}
	
	// do not show folders if not desired
	if( !filebrowser_gconf_show_folders() && info->type == GNOME_VFS_FILE_TYPE_DIRECTORY ){
		return FALSE;
	}

	const gchar *name = gnome_vfs_uri_extract_short_name( file );
	
	// do not show hidden files if not desired
	if( !filebrowser_gconf_show_hidden_files() && g_str_has_prefix( name, "." ) ){
		return FALSE;
	}

	if( !filebrowser_gconf_show_desktop_items() && g_str_has_suffix( name, ".desktop" ) ){
		return FALSE;
	}
 
	// do not show backup files
    if ( g_str_has_suffix( name, "~" ) ) {
        return FALSE;
    }

	// do not show this folder
    if ( gnome_vfs_uri_equal( folder->uri, file ) ) {
        return FALSE;
    }

	// do not show parent directory
    GnomeVFSURI *parent = gnome_vfs_uri_get_parent( folder->uri );
    if ( (parent && gnome_vfs_uri_equal( parent, file )) || g_str_has_prefix( name, ".." ) ) {
        return FALSE;
    }

	// do not show things we cannot handle
    if ( info->type != GNOME_VFS_FILE_TYPE_REGULAR &&
            info->type != GNOME_VFS_FILE_TYPE_SYMBOLIC_LINK &&
            info->type != GNOME_VFS_FILE_TYPE_DIRECTORY ) {
        return FALSE;
    }

    GtkWidget *filebrowser_icon = filebrowser_icon_new( folder, file );
    g_return_val_if_fail( filebrowser_icon, FALSE );
    g_object_ref(filebrowser_icon);
    g_object_ref_sink(GTK_OBJECT(filebrowser_icon));
 
    GtkTreeIter iter;
    gboolean valid;

    valid = gtk_tree_model_get_iter_first(GTK_TREE_MODEL(folder->store), &iter);
    while(valid){
        gpointer icon;

        gtk_tree_model_get(GTK_TREE_MODEL(folder->store), &iter, COL_FILEBROWSERICON, &icon, -1);

        gint sorted = filebrowser_folder_sort_list(filebrowser_icon, icon);
        if(sorted < 0){
            break;
        }
        valid = gtk_tree_model_iter_next(GTK_TREE_MODEL(folder->store), &iter );
    }

    GtkTreeIter insert_iter;
    if(!valid){
        gtk_list_store_append(folder->store, &insert_iter);
    }else{
        gtk_list_store_insert_before(folder->store, &insert_iter, &iter);
    }

    filebrowser_icon = g_object_ref_sink( G_OBJECT(filebrowser_icon));
//    gtk_list_store_set(folder->store, &insert_iter, 0, FILEBROWSER_ICON(filebrowser_icon)->icon, 1, 
//            FILEBROWSER_ICON(filebrowser_icon)->name, 2, filebrowser_icon, -1);
    gtk_list_store_set(folder->store, &insert_iter, COL_FILEBROWSERICON, filebrowser_icon, -1);

    /* create a 3-icon applet icon
    if ( filebrowser_gconf_is_composite_applet_icon() ) {  	
       	GdkPixbuf *old = folder->applet_icon;

    	if( n == 0 ){
	    	folder->applet_icon = gdk_pixbuf_copy(FILEBROWSER_ICON( filebrowser_icon )->icon);
	    }else{
	    	gint rnd0 = g_random_int_range (0, n);
	    	gint rnd1 = g_random_int_range (0, n);
   	
    		GdkPixbuf *icon2 = FILEBROWSER_ICON(g_list_nth_data( folder->icon_list, rnd0))->icon;
    		GdkPixbuf *icon3 = NULL;
    		if( n > 1 ){
				icon3 = FILEBROWSER_ICON(g_list_nth_data( folder->icon_list, rnd1 ))->icon;   
			}
	  	
    		folder->applet_icon = compose_applet_icon(FILEBROWSER_ICON( filebrowser_icon )->icon, 
    			icon2, icon3, awn_applet_get_height( AWN_APPLET( folder->dialog->applet->awn_applet ) ));
    	}

    	if( old ){
	    	g_object_unref( G_OBJECT( old ) );
	    }
    }
    */
    
    folder->total = folder->total + 1;
    return TRUE;
}

/**
 * Remove an icon from the filebrowser based on the uri
 * -destroy widget
 */
void filebrowser_folder_remove(
    FileBrowserFolder * folder,
    GnomeVFSURI * file ) {

	g_return_if_fail( folder && file );

    GtkTreeIter iter;
    gboolean valid;

    valid = gtk_tree_model_get_iter_first(GTK_TREE_MODEL(folder->store), &iter);
    while(valid){
        //find item
        gpointer icon;
        
        gtk_tree_model_get(GTK_TREE_MODEL(folder->store), &iter, COL_FILEBROWSERICON, &icon, -1);
        if ( gnome_vfs_uri_equal( FILEBROWSER_ICON(icon)->uri, file ) ) {
            gtk_list_store_remove(GTK_LIST_STORE(folder->store), &iter);
            g_object_unref(icon);
            //gtk_widget_destroy( GTK_WIDGET( icon ) );
            break;
        }
        
        valid = gtk_tree_model_iter_next(GTK_TREE_MODEL(folder->store), &iter);
    }
    gtk_tree_iter_free(&iter);

    if(valid){
        folder->total = folder->total - 1;
        filebrowser_folder_layout(folder, folder->offset);
    }
}

/**
 * Destroy event
 */
static void filebrowser_folder_destroy( GtkObject * object ) {
    
    FileBrowserFolder *folder = FILEBROWSER_FOLDER( object );
  
    if ( folder->monitor ) {
        gnome_vfs_monitor_cancel( folder->monitor );
    }
    folder->monitor = NULL;

    if ( folder->uri ) {
        gnome_vfs_uri_unref( folder->uri );
    }
    folder->uri = NULL;

    if ( folder->applet_icon ) {
        g_object_unref( G_OBJECT( folder->applet_icon ) );
    }
    folder->applet_icon = NULL;
    
    ( *GTK_OBJECT_CLASS( filebrowser_folder_parent_class )->destroy ) ( object );
}

/**
 * Handle monitor callbacks
 * -add/remove file from list
 * -bounce applet-icon to get attention
 */
static void filebrowser_folder_monitor_callback(
    GnomeVFSMonitorHandle * handle,
    const gchar * monitor_uri,
    const gchar * info_uri,
    GnomeVFSMonitorEventType event_type,
    gpointer user_data ) {

    FileBrowserFolder *folder = ( FileBrowserFolder * ) user_data;
    g_return_if_fail( FILEBROWSER_IS_FOLDER( folder ) );
    
    gboolean something_changed = FALSE;

    switch ( event_type ) {
    case GNOME_VFS_MONITOR_EVENT_CREATED:
        g_print("monitor_callback: EVENT_CREATED\n");
        something_changed = filebrowser_folder_add( folder, gnome_vfs_uri_new( info_uri ) );
        break;

    case GNOME_VFS_MONITOR_EVENT_DELETED:
        g_print("monitor callback: EVENT_DELETED\n");
        filebrowser_folder_remove( folder, gnome_vfs_uri_new( info_uri ) );
        something_changed = TRUE;
        break;

    case GNOME_VFS_MONITOR_EVENT_CHANGED:
    case GNOME_VFS_MONITOR_EVENT_STARTEXECUTING:
    case GNOME_VFS_MONITOR_EVENT_STOPEXECUTING:
    case GNOME_VFS_MONITOR_EVENT_METADATA_CHANGED:
    default:
        return;
    }

	if( something_changed ){
    
        // TODO: get attention
    }

    return;
}

/**
 * Checks if the folder has a next page
 */
gboolean filebrowser_folder_has_next_page(
    FileBrowserFolder * folder ) {

	if( !folder ){
		return FALSE;
	}

    gint total = filebrowser_gconf_get_max_rows() * filebrowser_gconf_get_max_cols();
    
    return (folder->offset + total < folder->total);
}

/**
 * Checks if the folder has a previous page
 */
gboolean filebrowser_folder_has_prev_page(
    FileBrowserFolder * folder ) {

	if( !folder ){
		return FALSE;
	}

    return ( folder->offset > 0 );
}

void filebrowser_folder_do_next_page(
    FileBrowserFolder * folder ){

    if(filebrowser_folder_has_next_page(folder)){
        gint n_offset = folder->offset + (filebrowser_gconf_get_max_cols() * filebrowser_gconf_get_max_rows());
        filebrowser_folder_layout(folder, n_offset);
        gtk_widget_show_all( GTK_WIDGET( folder ) );    
    }
}
    
void filebrowser_folder_do_prev_page(
    FileBrowserFolder * folder ){

    gint n_offset = folder->offset - (filebrowser_gconf_get_max_cols() * filebrowser_gconf_get_max_rows());
    if(n_offset >= 0){
        filebrowser_folder_layout(folder, n_offset);
        gtk_widget_show_all( GTK_WIDGET( folder ) );    
    }
}

/**
 * Checks if the folder has a parent folder
 */
gboolean filebrowser_folder_has_parent_folder(
    FileBrowserFolder * folder ) {

	if( !folder ){
		return FALSE;
	}
	
    return ( gnome_vfs_uri_get_parent( folder->uri ) != NULL );
}

static void keep_icons(gpointer data, gpointer user_data){
    if(GTK_IS_CONTAINER(user_data) && GTK_IS_WIDGET(data)){
        gtk_container_remove(GTK_CONTAINER(user_data), GTK_WIDGET(data));
    }
}

void filebrowser_folder_layout(FileBrowserFolder *folder, gint offset){

    GList *children = gtk_container_get_children(GTK_CONTAINER(folder));
    
    gpointer old = g_list_nth_data(children, 0);
    if(old != NULL){
        g_print("old != NULL\n");
        GList *icons = gtk_container_get_children(GTK_CONTAINER(old));
        g_list_foreach(icons, keep_icons, old);
        gtk_widget_destroy(GTK_WIDGET(old));
        g_list_free(icons);
    }
    

    folder->offset = offset;
    gint o = offset;
    gint c = filebrowser_gconf_get_max_cols();
    gint r = filebrowser_gconf_get_max_rows();

    GtkWidget *table = gtk_table_new(1,1, TRUE);
    GtkTreeIter iter;
    gboolean valid;
    valid = gtk_tree_model_get_iter_first(GTK_TREE_MODEL(folder->store), &iter);
    gint x=0, y=0;
    while(valid){
        if(o == 0){
            FileBrowserIcon *sic;
            gtk_tree_model_get(GTK_TREE_MODEL(folder->store), &iter, COL_FILEBROWSERICON, &sic, -1);
            gtk_table_attach_defaults(GTK_TABLE(table), GTK_WIDGET(sic), x,x+1,y,y+1);
            if((x+1) == c){
                y++;
                x = 0;
            }else{
                x++;
            }

            if(y == r)
                break;
        }else{
            o--;
        }

        valid = gtk_tree_model_iter_next(GTK_TREE_MODEL(folder->store), &iter);
    }
    gtk_widget_show_all(GTK_WIDGET(folder));
    gtk_container_add(GTK_CONTAINER(folder), GTK_WIDGET(table));
}

/**
 * Class init function
 * -connect to events
 */
static void filebrowser_folder_class_init(
    FileBrowserFolderClass * klass ) {
    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

    parent_class = gtk_type_class (GTK_TYPE_EVENT_BOX);

    object_class->destroy = filebrowser_folder_destroy;
}

/**
 * Object init function
 */
static void filebrowser_folder_init(
    FileBrowserFolder * filebrowser_folder ) {
    filebrowser_folder->offset = 0;
    filebrowser_folder->total = 0;
}

/**
 * Create a new filebrowser folder
 * -sets properties (uri, name, etc.)
 * -creates new folder if not exists
 * -reads folder and adds icons
 * -sets monitor on directory
 * -calculate layout
 */
GtkWidget *filebrowser_folder_new(
    FileBrowserDialog * dialog,
    GnomeVFSURI * uri) {

	g_return_val_if_fail( dialog && uri, NULL );

    FileBrowserFolder *filebrowser_folder = g_object_new( FILEBROWSER_TYPE_FOLDER, NULL );

    filebrowser_folder->dialog = dialog;
    filebrowser_folder->uri = uri;
    filebrowser_folder->name = gnome_vfs_uri_extract_short_name( filebrowser_folder->uri );
    gtk_event_box_set_visible_window(GTK_EVENT_BOX(filebrowser_folder), FALSE);

//    filebrowser_folder->store = gtk_list_store_new(3, GDK_TYPE_PIXBUF, G_TYPE_STRING, G_TYPE_POINTER);
    filebrowser_folder->store = gtk_list_store_new(1, G_TYPE_POINTER);
    
    GnomeVFSDirectoryHandle *handle;
    GnomeVFSResult  result;
    GnomeVFSFileInfo *info = gnome_vfs_file_info_new(  );
    GnomeVFSFileInfoOptions options;

    options = GNOME_VFS_FILE_INFO_GET_MIME_TYPE;
    options |= GNOME_VFS_FILE_INFO_FOLLOW_LINKS;
    options |= GNOME_VFS_FILE_INFO_FORCE_FAST_MIME_TYPE;

    if ( !gnome_vfs_uri_exists( filebrowser_folder->uri ) ) {
        result = gnome_vfs_make_directory_for_uri( filebrowser_folder->uri, 0766 );

        if ( result != GNOME_VFS_OK ) {
            g_print( "Could not create backend folder \"%s\" due: %s\n",
                     gnome_vfs_uri_to_string( filebrowser_folder->uri, 0 ),
                     gnome_vfs_result_to_string( result ) );
            return NULL;
        }
    }

    gnome_vfs_directory_open_from_uri( &handle, filebrowser_folder->uri, options );
    while ( gnome_vfs_directory_read_next( handle, info ) == GNOME_VFS_OK ) {
        if ( info->type != GNOME_VFS_FILE_TYPE_REGULAR &&
                info->type != GNOME_VFS_FILE_TYPE_SYMBOLIC_LINK &&
                info->type != GNOME_VFS_FILE_TYPE_DIRECTORY ) {
            continue;
        }

        GnomeVFSURI *file_uri = gnome_vfs_uri_append_file_name( filebrowser_folder->uri, info->name );

        filebrowser_folder_add( filebrowser_folder, file_uri );
    }

    if ( !filebrowser_folder->monitor ) {/*
        GnomeVFSResult result = gnome_vfs_monitor_add( &filebrowser_folder->monitor,
                                gnome_vfs_uri_to_string( filebrowser_folder->uri,
								GNOME_VFS_URI_HIDE_NONE ),
                                GNOME_VFS_MONITOR_DIRECTORY,
                                filebrowser_folder_monitor_callback,
                                filebrowser_folder );

        if ( result != GNOME_VFS_OK ) {
            g_print( "Could not set a monitor on the backend folder due: %s\n",
                     gnome_vfs_result_to_string( result ) );
        }
    */}

    filebrowser_folder_layout(filebrowser_folder, 0);
	gtk_widget_show( GTK_WIDGET( filebrowser_folder ) );

    return GTK_WIDGET( filebrowser_folder );

}

