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
#include <gtk/gtk.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>
#include <libgnomevfs/gnome-vfs.h>
#include <libgnome/gnome-desktop-item.h>
#include <libgnomevfs/gnome-vfs-mime-utils.h>
#include <libgnomevfs/gnome-vfs-mime.h>

#include "stack-icon.h"
#include "stack-applet.h"
#include "stack-utils.h"
#include "stack-gconf.h"
#include "stack-defines.h"
#include "stack-folder.h"

G_DEFINE_TYPE( StackIcon, stack_icon, GTK_TYPE_DRAWING_AREA )

static gboolean just_dragged = FALSE;

static GtkDrawingAreaClass *parent_class = NULL;

/**
 * Destroy events of the applet
 */
static void stack_icon_destroy(
    GtkObject * object ) {

    StackIcon      *icon = STACK_ICON( object );

    if ( icon->uri ) {
        gnome_vfs_uri_unref( icon->uri );
    }
    icon->uri = NULL;

    if ( icon->desktop_item ) {
        gnome_desktop_item_unref( icon->desktop_item );
    }
    icon->desktop_item = NULL;

    if ( icon->icon ) {
        g_object_unref( G_OBJECT( icon->icon ) );
    }
    icon->icon = NULL;

    if ( icon->name ) {
        g_free( icon->name );
    }
    icon->name = NULL;

    ( *GTK_OBJECT_CLASS( stack_icon_parent_class )->destroy ) ( object );
}

static gchar *desktop_file_get_link_icon_from_desktop(
    GnomeDesktopItem * desktop_file ) {
    gchar          *icon_uri;
    const gchar    *icon;
    GnomeDesktopItemType desktop_type;

	icon_uri = g_strdup(gnome_desktop_item_get_icon( desktop_file, gtk_icon_theme_get_default() ) );
	if( icon_uri != NULL ){
		return icon_uri;
	}

    icon = gnome_desktop_item_get_string( desktop_file, GNOME_DESKTOP_ITEM_ICON );
    if ( icon != NULL ) {
        return g_strdup( icon );
    }

    icon_uri = g_strdup( gnome_desktop_item_get_string( desktop_file, "X-Nautilus-Icon" ) );
    if ( icon_uri != NULL ) {
        return icon_uri;
    }

    desktop_type = gnome_desktop_item_get_entry_type( desktop_file );
    switch ( desktop_type ) {
    case GNOME_DESKTOP_ITEM_TYPE_APPLICATION:
        return g_strdup( "gnome-fs-executable" );

    case GNOME_DESKTOP_ITEM_TYPE_LINK:
        return g_strdup( "gnome-dev-symlink" );

    case GNOME_DESKTOP_ITEM_TYPE_FSDEVICE:
        return g_strdup( "gnome-dev-harddisk" );

    case GNOME_DESKTOP_ITEM_TYPE_DIRECTORY:
        return g_strdup( "gnome-fs-directory" );

    case GNOME_DESKTOP_ITEM_TYPE_SERVICE:
    case GNOME_DESKTOP_ITEM_TYPE_SERVICE_TYPE:
        return g_strdup( "gnome-fs-web" );

    default:
        return g_strdup( "gnome-fs-regular" );
    }

    g_assert_not_reached(  );
    return NULL;
}

static void stack_icon_calculate_size_and_position(
    GtkWidget * widget ) {

    StackIcon      *icon = STACK_ICON( widget );

    guint           icon_size = stack_gconf_get_icon_size(  );
    guint           icon_width = gdk_pixbuf_get_width( icon->icon );
    guint           icon_height = gdk_pixbuf_get_height( icon->icon );

    icon->icon_x = ICON_MARGIN_X;
    if ( icon_width < icon_size ) {
        icon->icon_x += ( icon_size - icon_width ) / 2;
    }

    icon->icon_y = ICON_MARGIN_Y;
    if ( icon_height < icon_size ) {
        icon->icon_y += ( icon_size - icon_height ) / 2;
    }

    icon->name_x = ICON_MARGIN_X;
    icon->name_y = ICON_MARGIN_Y + icon_size + ICON_NAME_MARGIN;

    icon->rect_x = 0;
    icon->rect_y = 0;
    icon->rect_w = icon_size + 2 * ICON_MARGIN_X;
    icon->rect_h = icon_size + 2 * ICON_MARGIN_Y + ICON_NAME_MARGIN + ICON_NAME_HEIGHT;

    gtk_widget_set_size_request( GTK_WIDGET( icon ), ( gint ) icon->rect_w, ( gint ) icon->rect_h );
}

/**
 * Expose event of the applet
 */
static gboolean stack_icon_expose_event(
    GtkWidget * widget,
    GdkEventExpose * expose ) {

    StackIcon *icon = STACK_ICON( widget );
    cairo_t *cr = NULL;
    AwnColor color;
    GtkStyle *style;
    GdkColor bg;
    GdkColor border;
    GdkColor hover;
    gfloat alpha = 0.9;

	GdkWindow *window = widget->window; 

    g_return_val_if_fail( GDK_IS_DRAWABLE( window ), FALSE );
    cr = gdk_cairo_create( window );
    g_return_val_if_fail( cr, FALSE );

    /* Get the colours from the theme */
    gtk_widget_style_get (STACK_FOLDER (icon->folder)->dialog->awn_dialog, "bg_alpha", &alpha, NULL);
    
    style = gtk_widget_get_style (STACK_FOLDER(icon->folder)->dialog->awn_dialog);
    bg = style->base[GTK_STATE_NORMAL];
    border = style->bg[GTK_STATE_SELECTED];
    hover = style->base[GTK_STATE_SELECTED];

    // paint background same as dialog
    cairo_set_operator( cr, CAIRO_OPERATOR_CLEAR );
    cairo_set_source_rgba( cr, 0.0, 0.0, 0.0, 0.0 );
    cairo_paint( cr );    

    cairo_set_operator( cr, CAIRO_OPERATOR_OVER );
    cairo_set_source_rgba( cr, bg.red/65335.0,
                               bg.green/65335.0,
                               bg.blue/65335.0,
                               alpha );
    cairo_paint( cr );   

    if ( icon->hovering ) {
       
        awn_cairo_rounded_rect( cr, icon->rect_x + 1, icon->rect_y + 1,
                                icon->rect_w - 2, icon->rect_h - 2,
                                STACK_ICON_RECT_RADIUS, ROUND_ALL );     

		// clear the area inside the hover rectangle
    	cairo_set_operator( cr, CAIRO_OPERATOR_CLEAR );    
        cairo_set_source_rgba( cr, 0.0, 0.0, 0.0, 0.0 );
	    cairo_fill_preserve( cr );    

	    cairo_set_operator( cr, CAIRO_OPERATOR_OVER );  	                                   
		cairo_set_source_rgba( cr, hover.red/65335.0,
                               hover.green/65335.0,
                               hover.blue/65335.0,
                               alpha );		
        cairo_fill_preserve( cr );

		cairo_set_source_rgba( cr, border.red/65335.0,
                               border.green/65335.0,
                               border.blue/65335.0,
                               alpha );       
        cairo_set_line_width( cr, 2.5f );
        cairo_stroke( cr );
    }                              

    paint_icon( cr, icon->icon, icon->icon_x, icon->icon_y, 1.0f );

    paint_icon_name( cr, icon->name, icon->name_x, icon->name_y, style->text[GTK_STATE_NORMAL] );

}

/**
 * Enter notify (hover) event
 */
static gboolean stack_icon_enter_notify_event(
    GtkWidget * widget,
    GdkEventCrossing * event ) {

    StackIcon *icon = STACK_ICON( widget );

    icon->hovering = TRUE;
    gtk_widget_queue_draw( widget );

    return TRUE;
}

/**
 * Leave notify (hover) event
 */
static gboolean stack_icon_leave_notify_event(
    GtkWidget * widget,
    GdkEventCrossing * event ) {

    StackIcon *icon = STACK_ICON( widget );

    icon->hovering = FALSE;
    gtk_widget_queue_draw( widget );

    return TRUE;
}

/**
 * Button released event
 * -shows/launched the file associated with this icon
 */
static gboolean stack_icon_button_release_event(
    GtkWidget * widget,
    GdkEventButton * event ) {

    StackIcon *icon = STACK_ICON( widget );

    if ( just_dragged ) {
        just_dragged = FALSE;
        return FALSE;
    }

    if ( icon->desktop_item ) {
        // with dnd files?
        gnome_desktop_item_launch_with_env( icon->desktop_item, NULL,
                                            GNOME_DESKTOP_ITEM_LAUNCH_ONLY_ONE, NULL, NULL );
    } else if ( icon->uri ) {
        if ( stack_gconf_is_browsing() && is_directory( icon->uri ) ) {
            stack_dialog_set_folder( STACK_DIALOG( STACK_FOLDER( icon->folder )->dialog ),
                                   icon->uri, 0 );
        } else {
            GnomeVFSResult  res =
                gnome_vfs_url_show_with_env( gnome_vfs_uri_to_string( icon->uri, GNOME_VFS_URI_HIDE_NONE ), NULL );

            if ( res != GNOME_VFS_OK ) {
                g_print( "Error launching url: %s\nError was: %s",
                         gnome_vfs_uri_get_path( icon->uri ), gnome_vfs_result_to_string( res ) );
            }
        }
    } else {
        g_print( "Could not launch url: url not set?" );
    }

    return TRUE;
}

/**
 * Drag begin event
 */
static void stack_icon_drag_begin(
    GtkWidget * widget,
    GdkDragContext * drag_context ) {

    StackIcon *icon = STACK_ICON( widget );

    gtk_drag_source_set_icon_pixbuf( widget, icon->icon );
    
    // set up DnD target
    gchar *default_action = stack_gconf_get_default_drag_action();
    if( g_str_equal(default_action, DRAG_ACTION_LINK ) ){
	    drag_context->actions = GDK_ACTION_LINK;
	}else if(g_str_equal(default_action, DRAG_ACTION_MOVE ) ){
		drag_context->actions = GDK_ACTION_MOVE;
	}else if(g_str_equal(default_action, DRAG_ACTION_COPY ) ){	
		drag_context->actions = GDK_ACTION_COPY;
	}else{
		drag_context->actions = GDK_ACTION_LINK | GDK_ACTION_COPY | GDK_ACTION_MOVE;
	}
	
	drag_context->suggested_action = GDK_ACTION_ASK;
	   
    just_dragged = TRUE;
}

/**
 * Drag delete data event
 */
static void stack_icon_drag_data_delete(
    GtkWidget * widget,
    GdkDragContext * drag_context ) {

    // remove icon from container
    g_print( "drag_data_delete\n" );
}

/**
 * Drag data get event
 */
static void stack_icon_drag_data_get(
    GtkWidget * widget,
    GdkDragContext * context,
    GtkSelectionData * selection_data,
    guint info,
    guint time ) {

    StackIcon *icon = STACK_ICON( widget );

    gchar *uri = gnome_vfs_uri_to_string( icon->uri, GNOME_VFS_URI_HIDE_NONE );

    gtk_selection_data_set( selection_data, GDK_SELECTION_TYPE_STRING, 8,
                            ( guchar * ) uri, ( gint ) strlen( uri ) );

    g_free( uri );
}

/**
 * Drag end event
 */
static void stack_icon_drag_end(
    GtkWidget * widget,
    GdkDragContext * drag_context ) {

    g_print( "drag_end\n" );
    just_dragged = FALSE;
}

/**
 * Initialize applet class
 * Set class functions
 */
static void stack_icon_class_init(
    StackIconClass * klass ) {

    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

    parent_class = gtk_type_class (GTK_TYPE_DRAWING_AREA);

    object_class->destroy = stack_icon_destroy;

    widget_class->expose_event = stack_icon_expose_event;
    widget_class->enter_notify_event = stack_icon_enter_notify_event;
    widget_class->leave_notify_event = stack_icon_leave_notify_event;
    widget_class->button_release_event = stack_icon_button_release_event;

   	/* Messages for outgoing drag. */
    widget_class->drag_begin = stack_icon_drag_begin;
    widget_class->drag_data_get = stack_icon_drag_data_get;
    //widget_class->drag_end = stack_icon_drag_end;  
    //widget_class->drag_data_delete = stack_icon_drag_data_delete;

	/* Messages for incoming drag. */	
	//widget_class->drag_data_delete = stack_icon_drag_data_received;
	//widget_class->drag_data_delete = stack_icon_drag_data_motion;
	//widget_class->drag_data_delete = stack_icon_drag_data_drop;
	//widget_class->drag_data_delete = stack_icon_drag_data_leave;

}

/**
 * Initialize the new applet
 */
static void stack_icon_init(
    StackIcon * icon ) {

    icon->hovering = FALSE;

    gtk_widget_add_events( GTK_WIDGET( icon ), GDK_ALL_EVENTS_MASK );
}

/**
 * Create a new stack icon
 */
GtkWidget *stack_icon_new(
    StackFolder * folder,
    GnomeVFSURI * uri ) {

	g_return_val_if_fail( folder && uri, NULL );

    StackIcon      *icon = g_object_new( STACK_TYPE_ICON, NULL );

    const gchar    *name = gnome_vfs_uri_extract_short_name( uri );
    const gchar    *file_path = gnome_vfs_uri_get_path( uri );
    guint           icon_size = stack_gconf_get_icon_size(  );


    g_return_val_if_fail (uri != NULL, NULL);

    // is .desktop?
    
	gchar *desktop_mime_type = "application/x-desktop";
	const char *mime_type = gnome_vfs_get_mime_type_common( uri );

	if(g_str_equal(mime_type, desktop_mime_type)){
		GError *error = NULL;
		icon->desktop_item =
    		        gnome_desktop_item_new_from_uri( file_path, 0, &error );
		if( error ){
    				g_error_free( error );
    				error = NULL;
    				icon->desktop_item = NULL;
    	}
    	if( !gnome_desktop_item_exists( icon->desktop_item ) ){
    		gnome_desktop_item_unref( icon->desktop_item );
			icon->desktop_item = NULL;
    	}
    }else{
    	icon->desktop_item = NULL;
    }

    // Possibly could not get a desktop_item from the file
    if ( icon->desktop_item ) {
        icon->name =
            g_strdup( gnome_desktop_item_get_localestring( icon->desktop_item, GNOME_DESKTOP_ITEM_NAME ) );
        icon->icon = get_icon( desktop_file_get_link_icon_from_desktop( icon->desktop_item ), icon_size );        
    } else {
        icon->uri = gnome_vfs_uri_dup( uri );
    }

	// If we do not assigned an icon yet
    if ( !icon->icon ) {
        icon->icon = get_icon( file_path, icon_size );
    }
    
    // If the name is still blank
    if ( !icon->name ) {
        icon->name = g_strdup( name );
    }

    icon->folder = GTK_WIDGET( folder );


	/* Setup Drag & Drop */
	enum { TARGET_URILIST, };
	GtkTargetEntry target_table[] = { {"text/uri-list", 0, TARGET_URILIST}, };
	guint n_targets = sizeof( target_table ) / sizeof( target_table[0] );

    gtk_drag_source_set( GTK_WIDGET( icon ), GDK_BUTTON1_MASK, target_table,
                         n_targets, GDK_ACTION_COPY | GDK_ACTION_MOVE );

	// TODO: also setup as destination

    stack_icon_calculate_size_and_position( GTK_WIDGET( icon ) );

    return GTK_WIDGET( icon );
}

