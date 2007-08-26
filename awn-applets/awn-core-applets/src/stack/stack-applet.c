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

#include "stack-applet.h"
#include "stack-gconf.h"
#include "stack-cairo.h"
#include "stack-defines.h"
#include "stack-dialog.h"

G_DEFINE_TYPE( StackApplet, stack_applet, GTK_TYPE_DRAWING_AREA )

static void stack_applet_class_init(
    StackAppletClass * klass );

static void stack_applet_init(
    StackApplet * applet );

static void stack_applet_destroy(
    GtkObject * object );

static void stack_applet_drag_leave(
    GtkWidget * widget,
    GdkDragContext * context,
    guint time_, 
    StackApplet *applet );

static gboolean stack_applet_drag_motion(
    GtkWidget * widget,
    GdkDragContext * context,
    gint x,
    gint y,
    guint time_, 
    StackApplet *applet );

static void stack_applet_drag_data_received(
    GtkWidget * widget,
    GdkDragContext * context,
    gint x,
    gint y,
    GtkSelectionData * selectiondata,
    guint info,
    guint time_, 
    StackApplet *applet );

static gboolean stack_applet_button_release_event(
    GtkWidget * widget,
    GdkEventButton * event,
    StackApplet *applet );

static GtkWidget *stack_applet_new_dialog(
    StackApplet * applet );

static void stack_applet_activate_dialog(
    GtkEntry * entry,
    gpointer data );

static gboolean stack_applet_enter_notify_event (GtkWidget *window, GdkEventButton *event, StackApplet *applet);
static gboolean stack_applet_leave_notify_event (GtkWidget *window, GdkEventButton *event, StackApplet *applet);

static AwnAppletClass *parent_class = NULL;

static const GtkTargetEntry drop_types[] = { {"text/uri-list", 0, 0} };

/**
 * Create the new applet
 * -set AwnApplet properties
 * -initialize gconf
 * -create stack for default backend folder
 * -update icons
 */
AwnApplet *awn_applet_factory_initp(
    gchar * uid,
    gint orient,
    gint height ) {

	GtkWidget *awn_applet = awn_applet_simple_new( uid, orient, height );
	
    StackApplet *applet = g_object_new( STACK_TYPE_APPLET, NULL );
	applet->awn_applet = awn_applet;

    stack_gconf_init( AWN_APPLET( awn_applet ) );

    stack_applet_set_icon( applet, NULL );
    
    applet->stack = stack_dialog_new( applet );

   	applet->title = AWN_TITLE(awn_title_get_default ());
	applet->title_text = g_strdup (stack_gconf_get_backend_folder());

	gtk_widget_add_events( GTK_WIDGET( applet->awn_applet ), GDK_ALL_EVENTS_MASK );
	
	/* connect to mouse enter/leave events */
	g_signal_connect (G_OBJECT (applet->awn_applet), "enter-notify-event",
			  G_CALLBACK (stack_applet_enter_notify_event),
			  applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "leave-notify-event",
			  G_CALLBACK (stack_applet_leave_notify_event),
			  applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "button-release-event",
              G_CALLBACK (stack_applet_button_release_event), 
              applet);
              
    // set up DnD target
    gtk_drag_dest_set( GTK_WIDGET( applet->awn_applet ), GTK_DEST_DEFAULT_ALL, drop_types,
                       G_N_ELEMENTS( drop_types ),
                       GDK_ACTION_LINK | GDK_ACTION_COPY | GDK_ACTION_MOVE );           
	g_signal_connect (G_OBJECT (applet->awn_applet), "drag-leave",
              G_CALLBACK (stack_applet_drag_leave), 
              applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "drag-motion",
              G_CALLBACK (stack_applet_drag_motion), 
              applet);
	g_signal_connect (G_OBJECT (applet->awn_applet), "drag-data-received",
              G_CALLBACK (stack_applet_drag_data_received), 
              applet);                   
                                           
//    gtk_widget_set_size_request( awn_applet, awn_applet_get_height ( AWN_APPLET(awn_applet)), 
//                               ( awn_applet_get_height (AWN_APPLET(awn_applet)) + 2 ) * 2 );


    gtk_widget_show_all( awn_applet );

    return AWN_APPLET( awn_applet );
}

/**
 * Initialize applet class
 * -set class functions
 * -connect to some applet-signals
 */
static void stack_applet_class_init(
    StackAppletClass * klass ) {

    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

	parent_class = gtk_type_class (GTK_TYPE_DRAWING_AREA);

    object_class->destroy = stack_applet_destroy;
}

/**
 * Initialize the new applet
 * -set default values
 * -connect to external events
 * -set dnd area
 * -TODO: let user decide what the default action is on dnd (copy/move/symlink)
 */
static void stack_applet_init(
    StackApplet * applet ) {

    return;
}

/**
 * Destroy applet
 * -unref applet data
 */
static void stack_applet_destroy(
    GtkObject * object ) {

    StackApplet *applet = STACK_APPLET( object );

	if (applet->title){
		g_object_unref (applet->title);
	}
	applet->title = NULL;

    if ( applet->context_menu ) {
        gtk_widget_destroy( applet->context_menu );
    }
    applet->context_menu = NULL;

    if ( applet->stack ) {
        gtk_widget_destroy( applet->stack );
    }
    applet->stack = NULL;

    ( *GTK_OBJECT_CLASS( stack_applet_parent_class )->destroy ) ( object );
}

/**
 * Drag leave event
 * -disable hover -> no bounce
 */
static void stack_applet_drag_leave(
    GtkWidget * widget,
    GdkDragContext * context,
    guint time_, 
    StackApplet *applet ) {
   
	return;
}

/**
 * Drag motion event
 * -bounce applet icon
 */
static gboolean stack_applet_drag_motion(
    GtkWidget * widget,
    GdkDragContext * context,
    gint x,
    gint y,
    guint time_, 
    StackApplet *applet ) {

       
    return FALSE;
}

/**
 * Callback on transferring files
 * -ask for file overwrites
 * -display errors
 * -TODO: display progressbar
 */
static gint stack_applet_xfer_callback(
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
static void stack_applet_drag_data_received(
    GtkWidget * widget,
    GdkDragContext * context,
    gint x,
    gint y,
    GtkSelectionData * selectiondata,
    guint info,
    guint time_, 
    StackApplet *applet ) {

    GList *source, *target = NULL, *scan;
    GnomeVFSAsyncHandle *hnd;
    GnomeVFSXferOptions options = GNOME_VFS_XFER_DEFAULT;

    options |= GNOME_VFS_XFER_FOLLOW_LINKS;
    options |= GNOME_VFS_XFER_RECURSIVE;
    options |= GNOME_VFS_XFER_FOLLOW_LINKS_RECURSIVE;
    options |= GNOME_VFS_XFER_TARGET_DEFAULT_PERMS;
    //options |= GNOME_VFS_XFER_SAMEFS;

    // TODO: lookup default action set by user
    switch ( context->suggested_action ) {

	    case GDK_ACTION_LINK:
	        options |= GNOME_VFS_XFER_LINK_ITEMS;
	        break;
	    case GDK_ACTION_MOVE:
	        options |= GNOME_VFS_XFER_REMOVESOURCE;
	        break;
	    case GDK_ACTION_COPY:
	        //options |= GNOME_VFS_XFER_DEFAULT;
	        break;    	
	    default:
			options |= GNOME_VFS_XFER_LINK_ITEMS;
	        break;
    }

    source = gnome_vfs_uri_list_parse( ( gchar * ) selectiondata->data );

    for ( scan = g_list_first( source ); scan; scan = g_list_next( scan ) ) {
        GnomeVFSURI *uri = scan->data;
        gchar *name = gnome_vfs_uri_extract_short_name( uri );

        GnomeVFSURI *link = gnome_vfs_uri_append_file_name( stack_dialog_get_backend_folder(  ),
                            name );

        target = g_list_append( target, link );
        
        g_free( name );
    }

    GnomeVFSResult res = gnome_vfs_async_xfer( &hnd, source, target, options,
                         GNOME_VFS_XFER_ERROR_MODE_QUERY,
                         GNOME_VFS_XFER_OVERWRITE_MODE_QUERY,
                         GNOME_VFS_PRIORITY_DEFAULT,
                         stack_applet_xfer_callback, NULL,
                         NULL, NULL );

    if ( res != GNOME_VFS_OK ) {
        g_print( "Could not perform action due: %s\n", gnome_vfs_result_to_string( res ) );
        return;
    }

    gnome_vfs_uri_list_free( source );
    gnome_vfs_uri_list_free( target );

    gtk_drag_finish( context, TRUE, FALSE, time_ );
}

/**
 * Button release event
 * -on (button 1) toggle container visibility
 * -on rightclick (button 3) show context menu
 */
static gboolean stack_applet_button_release_event(
    GtkWidget * widget,
    GdkEventButton * event,
    StackApplet *applet ) {

    // toggle visibility
    if ( event->button == 1 ) {
        stack_dialog_toggle_visiblity( applet->stack );
        return FALSE;
    
    // create and popup context menu
    } else if ( event->button == 3 ) {

        if ( !applet->context_menu ) {
            applet->context_menu = stack_applet_new_dialog( applet );
        }
        gtk_menu_popup( GTK_MENU( applet->context_menu ), NULL, NULL, NULL, NULL,
                        event->button, event->time );

    }

    if ( GTK_WIDGET_CLASS( stack_applet_parent_class )->button_release_event ) {
        return ( *GTK_WIDGET_CLASS( stack_applet_parent_class )->
                 button_release_event ) ( widget, event );
    }

    return FALSE;
}

static gboolean stack_applet_enter_notify_event (GtkWidget *window, GdkEventButton *event, StackApplet *applet){

	if( !STACK_DIALOG(applet->stack )->active ){
		awn_title_show (applet->title, GTK_WIDGET(applet->awn_applet), applet->title_text);
	}
	
	return TRUE;
}

static gboolean stack_applet_leave_notify_event (GtkWidget *window, GdkEventButton *event, StackApplet *applet){

	awn_title_hide (applet->title, GTK_WIDGET(applet->awn_applet));
	
	return TRUE;
}

/**
 * Set the applet-icon
 */
void stack_applet_set_icon(
    StackApplet * applet,
    GdkPixbuf * icon ) {
    
    if(!icon){
    	GtkIconTheme *theme = gtk_icon_theme_get_default(  );
	    gchar *applet_icon = stack_gconf_get_applet_icon(  );
    	icon = gtk_icon_theme_load_icon( theme, applet_icon,
                       awn_applet_get_height
                       ( AWN_APPLET( applet->awn_applet ) ) - PADDING, 0, NULL );
    }
    awn_applet_simple_set_icon (AWN_APPLET_SIMPLE(applet->awn_applet), icon);
}

/**
 * Create the context menu
 * -get default menu
 * -add properties item
 */
static GtkWidget *stack_applet_new_dialog(
    StackApplet * applet ) {

    GtkWidget *item;
    GtkWidget *menu;

    menu = awn_applet_create_default_menu( AWN_APPLET( applet->awn_applet ) );
    item = gtk_image_menu_item_new_from_stock( GTK_STOCK_PROPERTIES, NULL );
    gtk_menu_shell_prepend( GTK_MENU_SHELL( menu ), item );

    g_signal_connect( G_OBJECT( item ), "activate",
                      G_CALLBACK( stack_applet_activate_dialog ), applet );

    gtk_widget_show_all( GTK_WIDGET( menu ) );

    return menu;
}

/**
 * Activate the file (folder) chooser.
 * -limit to create/select folders
 * -run dialog and retrieve a folder path
 */
static void stack_applet_activate_dialog(
    GtkEntry * entry,
    gpointer data ) {

    StackApplet *applet = STACK_APPLET( data );
    GnomeVFSURI *uri = stack_dialog_get_backend_folder(  );
    GtkWidget *dialog;

    dialog = gtk_file_chooser_dialog_new( STACK_TEXT_SELECT_FOLDER, NULL,
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
        gchar *filename;

        filename = gtk_file_chooser_get_filename( GTK_FILE_CHOOSER( dialog ) );
        stack_gconf_set_backend_folder( filename );

		//applet->title_text = g_strdup (_("No Items in Trash"));

        GtkWidget *old = applet->stack;

        applet->stack = stack_dialog_new( applet );
        if ( old ) {
            gtk_widget_destroy( old );
        }
    }

    gtk_widget_destroy( dialog );
}

