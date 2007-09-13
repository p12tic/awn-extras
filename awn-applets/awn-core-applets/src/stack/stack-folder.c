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

#include "stack-folder.h"
#include "stack-icon.h"
#include "stack-defines.h"
#include "stack-gconf.h"
#include "stack-utils.h"

G_DEFINE_TYPE( StackFolder, stack_folder, GTK_TYPE_VIEWPORT )

static GtkViewportClass *parent_class = NULL;
static gdouble anim_time = 0.0;

/**
 * Compare function for sorting the strings of the stack icons
 * -dirs before files
 * -case insensitive
 */
static gint stack_folder_sort_list(
    gconstpointer a,
    gconstpointer b ) {

    if ( a == NULL || b == NULL ) {
        return ( a - b );
    }

    GnomeVFSURI *uri_a = STACK_ICON( a )->uri;
    GnomeVFSURI *uri_b = STACK_ICON( b )->uri;

    if ( !( STACK_ICON( a )->desktop_item || STACK_ICON( b )->desktop_item ) ) {
        if ( uri_a == NULL || uri_b == NULL ) {
            return ( uri_a - uri_b );
        }
    }

    if ( is_directory( uri_a ) && !is_directory( uri_b ) ) {
        return -1;
    } else if ( !is_directory( uri_a ) && is_directory( uri_b ) ) {
        return 1;
    }

    gchar *name_a = STACK_ICON( a )->name;
    gchar *name_b = STACK_ICON( b )->name;

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
 * Get a page of icons from the directory list
 */
static GList *stack_folder_list_get_page(
    GList * list,
    gint icon_page ) {

    if( !list ){
    	return NULL;
    }

    gint n_per_page = stack_gconf_get_max_rows() * stack_gconf_get_max_cols();

    GList *page = g_list_copy( list );

    g_return_val_if_fail( page, NULL );

    gint i;

    for ( i = 0; i < ( icon_page * n_per_page ); i++ ) {
        page = g_list_remove_link( page, g_list_first( page ) );
    }

    if ( g_list_length( page ) < n_per_page ) {
        return page;
    }

    for ( i = n_per_page; n_per_page < g_list_length( page ); i++ ) {
        page = g_list_remove_link( page, g_list_last( page ) );
    }

    return page;
}

/**
 * Add a new icon to the stack container
 * -checks for valid uri
 * -create icon widget
 * -compose applet icon
 */
static gboolean stack_folder_add(
    StackFolder * folder,
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
	if( !stack_gconf_show_files() && info->type == GNOME_VFS_FILE_TYPE_REGULAR ){
		return FALSE;
	}
	
	// do not show folders if not desired
	if( !stack_gconf_show_folders() && info->type == GNOME_VFS_FILE_TYPE_DIRECTORY ){
		return FALSE;
	}

	const gchar *name = gnome_vfs_uri_extract_short_name( file );
	
	// do not show hidden files if not desired
	if( !stack_gconf_show_hidden_files() && g_str_has_prefix( name, "." ) ){
		return FALSE;
	}

	if( !stack_gconf_show_desktop_items() && g_str_has_suffix( name, ".desktop" ) ){
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

    GList *item = g_list_first( folder->icon_list );

    while ( item ) {
        StackIcon      *icon = STACK_ICON( item->data );

        if ( icon->uri && gnome_vfs_uri_equal( icon->uri, file ) ) {
            return FALSE;
        }
        item = g_list_next( item );
    }

    GtkWidget *stack_icon = stack_icon_new( folder, file );
    gtk_widget_show( stack_icon );
    
    g_return_val_if_fail( stack_icon, FALSE );

    // create a 3-icon applet icon
    if ( stack_gconf_is_composite_applet_icon() ) {  	
    	gint n = g_list_length( folder->icon_list );
       	GdkPixbuf *old = folder->applet_icon;
        	    	
    	if( n == 0 ){
	    	folder->applet_icon = gdk_pixbuf_copy(STACK_ICON( stack_icon )->icon);
	    }else{
	    	gint rnd0 = g_random_int_range (0, n);
	    	gint rnd1 = g_random_int_range (0, n);
   	
    		GdkPixbuf *icon2 = STACK_ICON(g_list_nth_data( folder->icon_list, rnd0))->icon;
    		GdkPixbuf *icon3 = NULL;
    		if( n > 1 ){
				icon3 = STACK_ICON(g_list_nth_data( folder->icon_list, rnd1 ))->icon;   
			}
	  	
    		folder->applet_icon = compose_applet_icon(STACK_ICON( stack_icon )->icon, 
    			icon2, icon3, awn_applet_get_height( AWN_APPLET( folder->dialog->applet->awn_applet ) ) - PADDING );
    	}

    	if( old ){
	    	g_object_unref( G_OBJECT( old ) );
	    }
    }

    folder->icon_list = g_list_insert_sorted( folder->icon_list, stack_icon,
                        stack_folder_sort_list );

	g_object_ref_sink( STACK_ICON( stack_icon ) );

    return TRUE;
}

/**
 * Remove an icon from the stack based on the uri
 * -destroy widget
 */
void stack_folder_remove(
    StackFolder * folder,
    GnomeVFSURI * file ) {

	g_return_if_fail( folder && folder->icon_list );

    GList *item = g_list_first( folder->icon_list );

    while ( item ) {
        StackIcon  *icon = STACK_ICON( item->data );

        if ( gnome_vfs_uri_equal( icon->uri, file ) ) {
            folder->icon_list = g_list_remove_link( folder->icon_list, item );
            gtk_widget_destroy( GTK_WIDGET( item->data ) );
            g_list_free_1( item );
            break;
        }
        item = g_list_next( item );
    }
}

/**
 * If the table is not completely filled, it shows the ugly widget background
 * Repaint that!
 */
static gboolean stack_folder_expose_event(
    GtkWidget * widget,
    GdkEventExpose * expose ) {

    StackFolder *folder = STACK_FOLDER( widget );
    GtkStyle *style;
    GdkColor bg;
    gfloat alpha;

    GdkWindow *window = GDK_WINDOW( folder->table->window );
    cairo_t *cr = NULL;

    g_return_val_if_fail( GDK_IS_DRAWABLE( window ), FALSE );
    cr = gdk_cairo_create( window );
    g_return_val_if_fail( cr, FALSE );

    /* Get the correct colours from the theme */
    gtk_widget_style_get (GTK_WIDGET (folder->dialog->awn_dialog),
                          "bg_alpha",
                          &alpha, NULL);
    style = gtk_widget_get_style (widget);
    bg = style->base[GTK_STATE_NORMAL];

    // paint background same as dialog
    cairo_set_operator( cr, CAIRO_OPERATOR_CLEAR );
    cairo_set_source_rgba( cr, 0, 0, 0, 0.0 );
    cairo_paint( cr );    
    cairo_set_operator( cr, CAIRO_OPERATOR_OVER );
   	cairo_set_source_rgba( cr, bg.red/65335.0, 
                               bg.green/65335.0, 
                               bg.blue/65335.0, 
                               alpha );
    cairo_paint( cr );  
    
    cairo_destroy( cr );
    return FALSE;
}

/**
 * Destroy event
 */
static void stack_folder_destroy( GtkObject * object ) {
    
    StackFolder *folder = STACK_FOLDER( object );
  
    if ( folder->monitor ) {
        gnome_vfs_monitor_cancel( folder->monitor );
    }
    folder->monitor = NULL;

    if ( folder->uri ) {
        gnome_vfs_uri_unref( folder->uri );
    }
    folder->uri = NULL;

    if ( folder->icon_list ) {
        g_list_free( folder->icon_list );
    }
    folder->icon_list = NULL;

    if ( folder->table ) {
        gtk_widget_destroy( folder->table );
    }
    folder->table = NULL;
    
    if ( folder->applet_icon ) {
        g_object_unref( G_OBJECT( folder->applet_icon ) );
    }
    folder->applet_icon = NULL;
    
    ( *GTK_OBJECT_CLASS( stack_folder_parent_class )->destroy ) ( object );
}

/**
 * Handle monitor callbacks
 * -add/remove file from list
 * -bounce applet-icon to get attention
 */
static void stack_folder_monitor_callback(
    GnomeVFSMonitorHandle * handle,
    const gchar * monitor_uri,
    const gchar * info_uri,
    GnomeVFSMonitorEventType event_type,
    gpointer user_data ) {

    StackFolder *folder = ( StackFolder * ) user_data;
    g_return_if_fail( STACK_IS_FOLDER( folder ) );
    
    gboolean something_changed = FALSE;

    switch ( event_type ) {
    case GNOME_VFS_MONITOR_EVENT_CREATED:
        something_changed = stack_folder_add( folder, gnome_vfs_uri_new( info_uri ) );
        break;

    case GNOME_VFS_MONITOR_EVENT_DELETED:
        stack_folder_remove( folder, gnome_vfs_uri_new( info_uri ) );
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
    
	    stack_dialog_set_folder(folder->dialog, folder->uri, folder->page );
	    
        // TODO: get attention
    }

    return;
}

/**
 * Recalculate the stack layout
 * -iterate through the list of icons and position each one
 */
static void stack_folder_relayout(
    StackFolder * folder) {  

    gint width = 0, height = 0, page = 0;
	
	GList *tmplist = folder->icon_list;        
    if ( tmplist != NULL) {
        GtkWidget *icon = GTK_WIDGET( tmplist->data );

        gint iw = 0, ih = 0;

        gtk_widget_get_size_request( icon, &iw, &ih );

        gint n = g_list_length( tmplist );
        gint cols = stack_gconf_get_max_cols();
        gint rows = stack_gconf_get_max_rows();

        while ( ( cols * rows ) > n ) {
            if ( cols > rows ) {
                if ( ( ( cols - 1 ) * rows ) < n ) {
                    break;
                }
                cols--;

            } else {
                if ( ( cols * ( rows - 1 ) ) < n ) {
                    break;
                }
                rows--;
            }
        }

        gint item = 0;
        GtkWidget *vbox = NULL;
		GtkWidget *hbox = NULL;
        while ( tmplist ) {

			if( item % (cols * rows ) == 0 ){
	        		vbox = gtk_vbox_new(FALSE, 0);
        			gtk_widget_show( vbox );
					gtk_table_attach_defaults( GTK_TABLE(folder->table), vbox, page, page + 1, 0, 1);
					page++;
        	}
        	if( item % cols == 0 ){
        		hbox = gtk_hbox_new(FALSE, 0);
        		gtk_widget_show( hbox );
        		gtk_box_pack_start (GTK_BOX (vbox), hbox, FALSE, FALSE, 0);
        	}
        
            GtkWidget *icon = GTK_WIDGET( tmplist->data );
            gtk_box_pack_start (GTK_BOX (hbox), icon, FALSE, FALSE, 0);

            tmplist = g_list_next( tmplist );

            item++;
        }

        width = ( cols * iw );
        height = ( rows * ih );
    }else{
    	g_print("folder empty\n");
    	width = MIN_WIDTH;
    	height = MIN_HEIGHT;
    }
    folder->pages = page;

    gtk_widget_set_size_request( GTK_WIDGET( folder ), width, height );

    GtkObject *v_adjust = gtk_adjustment_new(0.0, 0.0, height, height, height, height);
    gtk_viewport_set_vadjustment( GTK_VIEWPORT( folder ), GTK_ADJUSTMENT( v_adjust ) );

    GtkObject *h_adjust = gtk_adjustment_new(0.0, 0.0, folder->pages * width, width, width, width);
    gtk_viewport_set_hadjustment( GTK_VIEWPORT( folder ), GTK_ADJUSTMENT( h_adjust ) );
}

/**
 * Checks if the folder has a next page
 */
gboolean stack_folder_has_next_page(
    StackFolder * folder ) {

	if( !folder || !folder->icon_list ){
		return FALSE;
	}

    gint total = stack_gconf_get_max_rows() * stack_gconf_get_max_cols();
    
    return ( g_list_length( folder->icon_list ) >
             ( ( folder->page + 1 ) * total ) );
}

/**
 * Checks if the folder has a previous page
 */
gboolean stack_folder_has_prev_page(
    StackFolder * folder ) {

	if( !folder ){
		return FALSE;
	}

    return ( folder->page > 0 );
}

gboolean move_left(
    StackFolder * folder ){

	if(anim_time == 0.0){
		anim_time = 2.0;
	}
    anim_time -= 0.2;    
    
    gint width = 0, height = 0;  
    gtk_widget_get_size_request( GTK_WIDGET( folder ), &width, &height );   

    gdouble replacement = 0.5 * ( 1 + cbrt( anim_time - 1.0 ) );
    if(replacement < 0.0){
    	replacement = 0.0;
    }

	gint value = (gint)(folder->page * width + replacement * width);

    GtkObject *h_adjust = gtk_adjustment_new(value, 0.0, folder->pages * width, width, width, width);
    gtk_viewport_set_hadjustment( GTK_VIEWPORT( folder ), GTK_ADJUSTMENT( h_adjust ) );

    gtk_widget_queue_draw( GTK_WIDGET( folder ) );
    
    if(anim_time < 0.0 ){
    	anim_time = 0.0;
	    gtk_widget_queue_draw( GTK_WIDGET( folder->dialog ) );
    	return FALSE;
    }
   	return TRUE;
}

gboolean move_right(
    StackFolder * folder ){

    anim_time += 0.2;    
    gint width = 0, height = 0;  
    gtk_widget_get_size_request( GTK_WIDGET( folder ), &width, &height );   

    gdouble replacement = 0.5 * ( 1 + cbrt( anim_time - 1.0 ) );
    if(replacement > 1.0){
    	replacement = 1.0;
    }    
    
    gint value = (gint)((folder->page - 1) * width + replacement * width);
    
    GtkObject *h_adjust = gtk_adjustment_new(value, 0.0, folder->pages * width, width, width, width);
    gtk_viewport_set_hadjustment( GTK_VIEWPORT( folder ), GTK_ADJUSTMENT( h_adjust ) );
    
    gtk_widget_queue_draw( GTK_WIDGET( folder ) );
    
    if(anim_time > 2.0 ){
    	anim_time = 0.0;
	    gtk_widget_queue_draw( GTK_WIDGET( folder->dialog ) );
    	return FALSE;
    }
   	return TRUE;
}

void stack_folder_do_next_page(
    StackFolder * folder ){

	if( !stack_folder_has_next_page( folder ) || anim_time != 0.0 ){
		return;
	}
	folder->page = folder->page + 1;    
    gtk_widget_show_all( GTK_WIDGET( folder ) );    
    g_timeout_add( 20, ( GSourceFunc ) move_right, ( gpointer ) folder );

}
    
void stack_folder_do_prev_page(
    StackFolder * folder ){

	if( !stack_folder_has_prev_page( folder ) || anim_time != 0.0 ){
		return;
	}
	folder->page = folder->page - 1;    
    gtk_widget_show_all( GTK_WIDGET( folder ) );    
    g_timeout_add( 20, ( GSourceFunc ) move_left, ( gpointer ) folder );
}

/**
 * Checks if the folder has a parent folder
 */
gboolean stack_folder_has_parent_folder(
    StackFolder * folder ) {

	if( !folder ){
		return FALSE;
	}
	
    return ( gnome_vfs_uri_get_parent( folder->uri ) != NULL );
}

/**
 * Class init function
 * -connect to events
 */
static void stack_folder_class_init(
    StackFolderClass * klass ) {
    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

	parent_class = gtk_type_class (GTK_TYPE_VIEWPORT);

    object_class->destroy = stack_folder_destroy;
    
    widget_class->expose_event = stack_folder_expose_event;
}

/**
 * Object init function
 */
static void stack_folder_init(
    StackFolder * stack_folder ) {
	return;
}

/**
 * Create a new stack folder
 * -sets properties (uri, name, etc.)
 * -creates new folder if not exists
 * -reads folder and adds icons
 * -sets monitor on directory
 * -calculate layout
 */
GtkWidget *stack_folder_new(
    StackDialog * dialog,
    GnomeVFSURI * uri) {

	g_return_val_if_fail( dialog && uri, NULL );

    StackFolder *stack_folder = g_object_new( STACK_TYPE_FOLDER, NULL );

    stack_folder->dialog = dialog;
    stack_folder->uri = uri;
    stack_folder->name = gnome_vfs_uri_extract_short_name( stack_folder->uri );

    GnomeVFSDirectoryHandle *handle;
    GnomeVFSResult  result;
    GnomeVFSFileInfo *info = gnome_vfs_file_info_new(  );
    GnomeVFSFileInfoOptions options;

    options = GNOME_VFS_FILE_INFO_GET_MIME_TYPE;
    options |= GNOME_VFS_FILE_INFO_FOLLOW_LINKS;
    options |= GNOME_VFS_FILE_INFO_FORCE_FAST_MIME_TYPE;

    if ( !gnome_vfs_uri_exists( stack_folder->uri ) ) {
        result = gnome_vfs_make_directory_for_uri( stack_folder->uri, 0766 );

        if ( result != GNOME_VFS_OK ) {
            g_print( "Could not create backend folder \"%s\" due: %s\n",
                     gnome_vfs_uri_to_string( stack_folder->uri, 0 ),
                     gnome_vfs_result_to_string( result ) );
            return NULL;
        }
    }

    gnome_vfs_directory_open_from_uri( &handle, stack_folder->uri, options );
    while ( gnome_vfs_directory_read_next( handle, info ) == GNOME_VFS_OK ) {
        if ( info->type != GNOME_VFS_FILE_TYPE_REGULAR &&
                info->type != GNOME_VFS_FILE_TYPE_SYMBOLIC_LINK &&
                info->type != GNOME_VFS_FILE_TYPE_DIRECTORY ) {
            continue;
        }

        GnomeVFSURI *file_uri = gnome_vfs_uri_append_file_name( stack_folder->uri, info->name );

        stack_folder_add( stack_folder, file_uri );
    }

    if ( !stack_folder->monitor ) {
        GnomeVFSResult result = gnome_vfs_monitor_add( &stack_folder->monitor,
                                gnome_vfs_uri_to_string( stack_folder->uri,
								GNOME_VFS_URI_HIDE_NONE ),
                                GNOME_VFS_MONITOR_DIRECTORY,
                                stack_folder_monitor_callback,
                                stack_folder );

        if ( result != GNOME_VFS_OK ) {
            g_print( "Could not set a monitor on the backend folder due: %s\n",
                     gnome_vfs_result_to_string( result ) );
        }
    }

	stack_folder->table = gtk_table_new(1,1, TRUE);
	gtk_table_set_row_spacings( GTK_TABLE(stack_folder->table), 0);
	gtk_table_set_col_spacings( GTK_TABLE(stack_folder->table), 0);
	gtk_widget_show( stack_folder->table );
	gtk_container_add( GTK_CONTAINER( stack_folder), stack_folder->table );

	gtk_viewport_set_shadow_type( GTK_VIEWPORT( stack_folder ), GTK_SHADOW_NONE );
	gtk_widget_set_no_show_all( GTK_WIDGET( stack_folder ), FALSE );

    stack_folder_relayout( stack_folder );

	gtk_widget_show( GTK_WIDGET( stack_folder ) );

    return GTK_WIDGET( stack_folder );

}

