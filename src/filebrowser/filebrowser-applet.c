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
#include <libawn/awn-applet-simple.h>
#include <libgnomevfs/gnome-vfs.h>

#include "filebrowser-applet.h"
#include "filebrowser-gconf.h"
#include "filebrowser-utils.h"
#include "filebrowser-defines.h"
#include "filebrowser-dialog.h"

G_DEFINE_TYPE( FileBrowserApplet, filebrowser_applet, GTK_TYPE_DRAWING_AREA )

static AwnAppletClass *parent_class = NULL;

static const GtkTargetEntry drop_types[] = { {"text/uri-list", 0, 0} };

/**
 * Activate the file (folder) chooser.
 * -limit to create/select folders
 * -run dialog and retrieve a folder path
 */
static void filebrowser_applet_activate_dialog(
    GtkEntry * entry,
    gpointer data ) {

    FileBrowserApplet *applet = FILEBROWSER_APPLET( data );
    GnomeVFSURI *uri = gnome_vfs_uri_new(filebrowser_gconf_get_backend_folder());
    GtkWidget *dialog;

    dialog = gtk_file_chooser_dialog_new( FILEBROWSER_TEXT_SELECT_FOLDER, NULL,
                                          GTK_FILE_CHOOSER_ACTION_CREATE_FOLDER,
                                          GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL,
                                          GTK_STOCK_APPLY, GTK_RESPONSE_ACCEPT, NULL );

    gtk_window_set_skip_taskbar_hint( GTK_WINDOW( dialog ), TRUE );
    gtk_window_set_skip_pager_hint( GTK_WINDOW( dialog ), TRUE );

    if ( uri ) {
       gtk_file_chooser_set_current_folder( GTK_FILE_CHOOSER( dialog ),
                                             gnome_vfs_uri_get_path( uri ) );
    }

    if ( gtk_dialog_run( GTK_DIALOG( dialog ) ) == GTK_RESPONSE_ACCEPT ) {

        gchar *filename = gtk_file_chooser_get_filename( GTK_FILE_CHOOSER( dialog ) );
        filebrowser_gconf_set_backend_folder( filename );

        GtkWidget *old = applet->filebrowser;
        applet->filebrowser = filebrowser_dialog_new( applet );
        if ( old ) {
            gtk_widget_destroy( old );
        }
        g_free( filename );

	applet->title = AWN_TITLE(awn_title_get_default ());
        applet->title_text = g_strdup (filebrowser_gconf_get_backend_folder());
    }

    gtk_widget_destroy( dialog );
}

/**
 * Create the context menu
 * -get default menu
 * -add properties item
 */
static GtkWidget *filebrowser_applet_new_dialog(
    FileBrowserApplet * applet ) {

    GtkWidget *item;
    GtkWidget *menu;

    menu = awn_applet_create_default_menu( AWN_APPLET( applet->awn_applet ) );
    item = gtk_image_menu_item_new_from_stock( GTK_STOCK_PROPERTIES, NULL );
    gtk_menu_shell_prepend( GTK_MENU_SHELL( menu ), item );

    g_signal_connect( G_OBJECT( item ), "activate",
                      G_CALLBACK( filebrowser_applet_activate_dialog ), applet );

    gtk_widget_show_all( GTK_WIDGET( menu ) );

    return menu;
}

/**
 * Destroy applet
 * -unref applet data
 */
static void filebrowser_applet_destroy(
    GtkObject * object ) {

    FileBrowserApplet *applet = FILEBROWSER_APPLET( object );

	if (applet->title){
		g_object_unref (applet->title);
	}
	applet->title = NULL;

    if ( applet->context_menu ) {
        gtk_widget_destroy( applet->context_menu );
    }
    applet->context_menu = NULL;

    if ( applet->filebrowser ) {
        gtk_widget_destroy( applet->filebrowser );
    }
    applet->filebrowser = NULL;

    ( *GTK_OBJECT_CLASS( filebrowser_applet_parent_class )->destroy ) ( object );
}

/**
 * Drag leave event
 * -disable hover -> no bounce
 */
static void filebrowser_applet_drag_leave(
    GtkWidget * widget,
    GdkDragContext * context,
    guint time_, 
    FileBrowserApplet *applet ) {
   
	return;
}

/**
 * Drag motion event
 * -bounce applet icon
 */
static gboolean filebrowser_applet_drag_motion(
    GtkWidget * widget,
    GdkDragContext * context,
    gint x,
    gint y,
    guint time_, 
    FileBrowserApplet *applet ) {

       
    return FALSE;
}

/**
 * Callback on transferring files
 * -ask for file overwrites
 * -display errors
 * -TODO: display progressbar
 */
static gint filebrowser_applet_xfer_callback(
    GnomeVFSAsyncHandle * handle,
    GnomeVFSXferProgressInfo * info,
    gpointer user_data ) {

    GtkWidget *dialog;
    gint response;

    switch ( info->status ) {
    case GNOME_VFS_XFER_PROGRESS_STATUS_DUPLICATE:	// cannot happen
        return 0;
    case GNOME_VFS_XFER_PROGRESS_STATUS_OVERWRITE:

        dialog = gtk_message_dialog_new( NULL,
                                         GTK_DIALOG_MODAL |
                                         GTK_DIALOG_DESTROY_WITH_PARENT,
                                         GTK_MESSAGE_QUESTION,
                                         GTK_BUTTONS_NONE,
                                         "Target already exists.\nWhat to do with \"%s\" ?\n",
                                         info->target_name );
        gtk_dialog_add_buttons( GTK_DIALOG( dialog ),
                                "Replace",
                                GNOME_VFS_XFER_OVERWRITE_ACTION_REPLACE, "Skip",
                                GNOME_VFS_XFER_OVERWRITE_ACTION_SKIP, "Abort",
                                GNOME_VFS_XFER_OVERWRITE_ACTION_ABORT, NULL );
        response = gtk_dialog_run( GTK_DIALOG( dialog ) );
        gtk_widget_destroy( dialog );

        return response;
    case GNOME_VFS_XFER_PROGRESS_STATUS_VFSERROR:

        if ( info->vfs_status == GNOME_VFS_ERROR_FILE_EXISTS ) {
            return 0;
        }
        dialog = gtk_message_dialog_new( NULL,
                                         GTK_DIALOG_MODAL |
                                         GTK_DIALOG_DESTROY_WITH_PARENT,
                                         GTK_MESSAGE_ERROR,
                                         GTK_BUTTONS_YES_NO,
                                         "Error occurred:\n%s\n\nAbort transfer?",
                                         gnome_vfs_result_to_string( info->vfs_status ) );
        response = gtk_dialog_run( GTK_DIALOG( dialog ) );
        gtk_widget_destroy( dialog );

        return ( response != GTK_RESPONSE_YES );
    case GNOME_VFS_XFER_PROGRESS_STATUS_OK:
    default:
        return 1;
    }
}

/**
 * Drag data received event
 * -scan the list of (possible more) source(s)
 * -create target filenames
 * -transfer files
 * -finish dnd
 */
static void filebrowser_applet_drag_data_received(
    GtkWidget * widget,
    GdkDragContext * context,
    gint x,
    gint y,
    GtkSelectionData * selectiondata,
    guint info,
    guint time_, 
    FileBrowserApplet *applet ) {

    GList *source, *target = NULL, *scan;
    GnomeVFSAsyncHandle *hnd;
    GnomeVFSXferOptions options = GNOME_VFS_XFER_DEFAULT;
    gboolean delete_original = FALSE;

    options |= GNOME_VFS_XFER_FOLLOW_LINKS;
    options |= GNOME_VFS_XFER_RECURSIVE;
    options |= GNOME_VFS_XFER_FOLLOW_LINKS_RECURSIVE;
    options |= GNOME_VFS_XFER_TARGET_DEFAULT_PERMS;
    //options |= GNOME_VFS_XFER_SAMEFS;

    gchar *default_action = filebrowser_gconf_get_default_drag_action();
    if( g_str_equal(default_action, DRAG_ACTION_LINK ) ){
	    options |= GNOME_VFS_XFER_LINK_ITEMS;
	}else if(g_str_equal(default_action, DRAG_ACTION_MOVE ) ){
		options |= GNOME_VFS_XFER_REMOVESOURCE;
		delete_original = TRUE;
	}else if(g_str_equal(default_action, DRAG_ACTION_COPY ) ){	
		//options |= GNOME_VFS_XFER_DEFAULT;
   	}else{ // if not specified or DRAG_ACTION_SYSTEM
	    switch ( context->suggested_action ) {

		    case GDK_ACTION_LINK:
		        options |= GNOME_VFS_XFER_LINK_ITEMS;
		        break;
		    case GDK_ACTION_MOVE:
		        options |= GNOME_VFS_XFER_REMOVESOURCE;
		        break;
		    case GDK_ACTION_COPY:
		    default:
		        //options |= GNOME_VFS_XFER_DEFAULT;
		        break;
	    }
	}

    source = gnome_vfs_uri_list_parse( ( gchar * ) selectiondata->data );

    for ( scan = g_list_first( source ); scan; scan = g_list_next( scan ) ) {
        GnomeVFSURI *uri = scan->data;
        gchar *name = gnome_vfs_uri_extract_short_name( uri );

        GnomeVFSURI *link = gnome_vfs_uri_append_file_name( gnome_vfs_uri_new(filebrowser_gconf_get_backend_folder()),
                            name );

        target = g_list_append( target, link );
        
        g_free( name );
    }

    GnomeVFSResult res = gnome_vfs_async_xfer( &hnd, source, target, options,
                         GNOME_VFS_XFER_ERROR_MODE_QUERY,
                         GNOME_VFS_XFER_OVERWRITE_MODE_QUERY,
                         GNOME_VFS_PRIORITY_DEFAULT,
                         filebrowser_applet_xfer_callback, NULL,
                         NULL, NULL );

    if ( res != GNOME_VFS_OK ) {
        g_print( "Could not perform action due: %s\n", gnome_vfs_result_to_string( res ) );
        gtk_drag_finish( context, FALSE, FALSE, time_ );
        return;
    }

    gnome_vfs_uri_list_free( source );
    gnome_vfs_uri_list_free( target );

    gtk_drag_finish( context, TRUE, delete_original, time_ );
}

/**
 * Button release event
 * -on (button 1) toggle container visibility
 * -on rightclick (button 3) show context menu
 */
static gboolean filebrowser_applet_button_release_event(
    GtkWidget * widget,
    GdkEventButton * event,
    FileBrowserApplet *applet ) {

    // toggle visibility
    if ( event->button == 1 ) {
	filebrowser_dialog_set_folder( applet->filebrowser, NULL, 0 );
        filebrowser_dialog_toggle_visiblity( applet->filebrowser );
        return FALSE;
    
    // create and popup context menu
    } else if ( event->button == 3 ) {

        if ( !applet->context_menu ) {
            applet->context_menu = filebrowser_applet_new_dialog( applet );
        }
        gtk_menu_popup( GTK_MENU( applet->context_menu ), NULL, NULL, NULL, NULL,
                        event->button, event->time );

    }

    return FALSE;
}

/**
 * Only show the Awn title when the dialog is not visible
 */
static gboolean filebrowser_applet_enter_notify_event (GtkWidget *window, GdkEventButton *event, FileBrowserApplet *applet){

	if( !FILEBROWSER_DIALOG(applet->filebrowser )->active ){
		awn_title_show (applet->title, GTK_WIDGET(applet->awn_applet), applet->title_text);
	}
	
	return TRUE;
}

/**
 * Hide the awn title
 */
static gboolean filebrowser_applet_leave_notify_event (GtkWidget *window, GdkEventButton *event, FileBrowserApplet *applet){

	awn_title_hide (applet->title, GTK_WIDGET(applet->awn_applet));
	
	return TRUE;
}

/**
 * Set the applet-icon
 */
void filebrowser_applet_set_icon(
    FileBrowserApplet * applet,
    GdkPixbuf * icon ) {
    
    if(!icon){
    	GtkIconTheme *theme = gtk_icon_theme_get_default(  );
	    gchar *applet_icon = filebrowser_gconf_get_applet_icon(  );
    	icon = gtk_icon_theme_load_icon( theme, applet_icon,
                       awn_applet_get_height
                       ( AWN_APPLET( applet->awn_applet ) ), 0, NULL );
    }else{
		icon = gdk_pixbuf_copy( icon );
    }

    awn_applet_simple_set_icon (AWN_APPLET_SIMPLE(applet->awn_applet), icon);
    gtk_widget_queue_draw( GTK_WIDGET(applet->awn_applet));
}

/**
 * Initialize applet class
 * -set class functions
 * -connect to some applet-signals
 */
static void filebrowser_applet_class_init(
    FileBrowserAppletClass * klass ) {

    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

	parent_class = gtk_type_class (GTK_TYPE_DRAWING_AREA);

    object_class->destroy = filebrowser_applet_destroy;
}

/**
 * Initialize the new applet
 * -set default values
 * -connect to external events
 * -set dnd area
 * -TODO: let user decide what the default action is on dnd (copy/move/symlink)
 */
static void filebrowser_applet_init(
    FileBrowserApplet * applet ) {

    return;
}

/**
 * Create the new applet
 * -set AwnApplet properties
 * -initialize gconf
 * -create filebrowser for default backend folder
 * -update icons
 */
AwnApplet *awn_applet_factory_initp(
    gchar * uid,
    gint orient,
    gint height ) {

    gnome_vfs_init ();

	GtkWidget *awn_applet = awn_applet_simple_new( uid, orient, height );
    FileBrowserApplet *applet = g_object_new( FILEBROWSER_TYPE_APPLET, NULL );
	applet->awn_applet = awn_applet;

    filebrowser_gconf_init( AWN_APPLET( awn_applet ), uid );
    filebrowser_applet_set_icon( applet, NULL );

    applet->filebrowser = filebrowser_dialog_new( applet );
   	applet->title = AWN_TITLE(awn_title_get_default ());
	applet->title_text = g_strdup (filebrowser_gconf_get_backend_folder());

	gtk_widget_add_events( GTK_WIDGET( applet->awn_applet ), GDK_ALL_EVENTS_MASK );
	
	/* connect to mouse enter/leave events */
	g_signal_connect (G_OBJECT (applet->awn_applet), "enter-notify-event",
			  G_CALLBACK (filebrowser_applet_enter_notify_event),
			  applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "leave-notify-event",
			  G_CALLBACK (filebrowser_applet_leave_notify_event),
			  applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "button-release-event",
              G_CALLBACK (filebrowser_applet_button_release_event), 
              applet);

    // set up DnD target
    GdkDragAction actions;
    gchar *default_action = filebrowser_gconf_get_default_drag_action();
    if( g_str_equal(default_action, DRAG_ACTION_LINK ) ){
	    actions = GDK_ACTION_LINK;
	}else if(g_str_equal(default_action, DRAG_ACTION_MOVE ) ){
		actions = GDK_ACTION_MOVE;
	}else if(g_str_equal(default_action, DRAG_ACTION_COPY ) ){	
		actions = GDK_ACTION_COPY;
	}else{
		actions = GDK_ACTION_LINK | GDK_ACTION_COPY | GDK_ACTION_MOVE;
	}

    gtk_drag_dest_set( GTK_WIDGET( applet->awn_applet ), GTK_DEST_DEFAULT_ALL, drop_types,
                       G_N_ELEMENTS( drop_types ),
                       actions );           

	g_signal_connect (G_OBJECT (applet->awn_applet), "drag-leave",
              G_CALLBACK (filebrowser_applet_drag_leave), 
              applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "drag-motion",
              G_CALLBACK (filebrowser_applet_drag_motion), 
              applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "drag-data-received",
              G_CALLBACK (filebrowser_applet_drag_data_received), 
              applet);                   
                                       
	/* Size request and show */    
    gtk_widget_set_size_request( awn_applet, awn_applet_get_height ( AWN_APPLET(awn_applet)), 
                                awn_applet_get_height (AWN_APPLET(awn_applet)) * 2);

    gtk_widget_show_all( awn_applet );
    g_print("return\n");
    return AWN_APPLET( awn_applet );
}

