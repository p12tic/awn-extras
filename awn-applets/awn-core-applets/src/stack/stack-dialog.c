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

#include <math.h>
#include <string.h>
#include <gtk/gtk.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-dialog.h>
#include <libgnomevfs/gnome-vfs.h>
#include <gdk/gdkkeysyms.h>

#include "stack-dialog.h"
#include "stack-applet.h"
#include "stack-icon.h"
#include "stack-gconf.h"
#include "stack-defines.h"
#include "stack-utils.h"
#include "stack-folder.h"

G_DEFINE_TYPE( StackDialog, stack_dialog, GTK_TYPE_FIXED )

enum {
    NONE = 0,
    FILEMANAGER = 1,
    FOLDER_LEFT = 2,
    FOLDER_RIGHT = 3,
    FOLDER_UP = 4
};

static AwnAppletDialogClass *parent_class = NULL;

static StackFolder *backend_folder;
static StackFolder *current_folder;

static gint eventbox_hovering = NONE;


/**
 * Called on eventbox hover (general signal catcher)
 * -find out the source
 * -check if action is valid
 * -set cursor
 * -enable hover
 */ 
static gboolean stack_dialog_evbox_hover(
    GtkWidget * widget,
    GdkEventCrossing * event,
    gpointer user_data ) {

    GdkCursorType cursor;

    switch ( GPOINTER_TO_INT( user_data ) ) {
    case FILEMANAGER:

        cursor = GDK_HAND2;

        break;
    case FOLDER_LEFT:

        if ( !stack_folder_has_prev_page( current_folder ) ) {
            return TRUE;
        }
        cursor = GDK_SB_LEFT_ARROW;

        break;
    case FOLDER_RIGHT:

        if ( !stack_folder_has_next_page( current_folder ) ) {
            return TRUE;
        }
        cursor = GDK_SB_RIGHT_ARROW;

        break;
    case FOLDER_UP:

        if ( !stack_folder_has_parent_folder( current_folder ) ) {
            return TRUE;
        }
        cursor = GDK_SB_UP_ARROW;

        break;
    default:
        cursor = GDK_LEFT_PTR;
    }
    
    gdk_window_set_cursor( widget->window, gdk_cursor_new( cursor ) );
    eventbox_hovering = GPOINTER_TO_INT( user_data );
    gtk_widget_queue_draw( widget );

    return FALSE;
}

/**
 * Leave event
 * -disable hover effect
 */
static gboolean stack_dialog_evbox_leave(
    GtkWidget * widget,
    GdkEventCrossing * event,
    gpointer user_data ) {

    gdk_window_set_cursor( widget->window, gdk_cursor_new( GDK_LEFT_PTR ) );
    eventbox_hovering = NONE;
    gtk_widget_queue_draw( widget );

    return FALSE;
}

static void stack_dialog_do_folder_up(
    GtkWidget * dialog ) {
    GnomeVFSURI *parent = gnome_vfs_uri_get_parent( current_folder->uri );

    if ( parent == NULL ) {
        return;
    }

    stack_dialog_set_folder( STACK_DIALOG( dialog ), parent, 0 );
}

/**
 * Eventbox clicked event
 * -find out source
 * -perform corresponding action
 */
static void stack_dialog_evbox_clicked(
    GtkWidget * widget,
    GdkEventButton * event,
    gpointer user_data ) {

    StackDialog *dialog = STACK_DIALOG( widget->parent );
    GnomeVFSResult res;

    switch ( GPOINTER_TO_INT( user_data ) ) {
    case FILEMANAGER:

        res = gnome_vfs_url_show( gnome_vfs_uri_to_string
                                ( current_folder->uri, GNOME_VFS_URI_HIDE_NONE ) );

        if ( res != GNOME_VFS_OK ) {
            g_print( "Error launching url: %s\nError was: %s",
                     gnome_vfs_uri_get_path( current_folder->uri ),
                     gnome_vfs_result_to_string( res ) );
        }
        return;
    case FOLDER_LEFT:
        stack_folder_do_prev_page( current_folder);
        return;
    case FOLDER_RIGHT:
        stack_folder_do_next_page( current_folder );
        return;
    case FOLDER_UP:
        stack_dialog_do_folder_up( GTK_WIDGET( dialog ) );
        return;
    default:
        return;
    }
}

static gboolean stack_dialog_key_press_event(
    GtkWidget * widget,
    GdkEventKey * event ) {

    g_return_val_if_fail( STACK_IS_DIALOG( widget ), FALSE );

    if ( event->keyval == GDK_Left) {
	    stack_folder_do_prev_page( current_folder);
    } else if ( event->keyval == GDK_Right) {
        stack_folder_do_next_page( current_folder );
    } else if ( event->keyval == GDK_Up && stack_gconf_is_browsing()) {
        stack_dialog_do_folder_up( widget );
    }

    return FALSE;
}

/**
 * Destroy event
 */
static void stack_dialog_destroy(
    GtkObject * object ) {

    StackDialog *dialog = STACK_DIALOG( object );

	if( dialog->frt_box ){
		gtk_widget_destroy( dialog->frt_box );
	}
	dialog->frt_box = NULL;

	if( dialog->flt_box ){
		gtk_widget_destroy( dialog->flt_box );
	}
	dialog->flt_box = NULL;

	if( dialog->fup_box ){
		gtk_widget_destroy( dialog->fup_box );
	}
	dialog->fup_box = NULL;

	if( dialog->fm_box ){
		gtk_widget_destroy( dialog->fm_box );
	}
	dialog->fm_box = NULL;

	if( dialog->awn_dialog ){
		gtk_widget_destroy( dialog->fup_box );
	}
	dialog->awn_dialog = NULL;

    ( *GTK_OBJECT_CLASS( stack_dialog_parent_class )->destroy ) ( object );
}

/**
 * Expose event
 */
static gboolean stack_dialog_expose_event(
    GtkWidget * widget,
    GdkEventExpose * expose ) {

    StackDialog *dialog = STACK_DIALOG( widget );
    GtkStyle *style;
    GdkColor text;
    gfloat alpha;

    GdkWindow *window = GDK_WINDOW( dialog->awn_dialog->window );
    cairo_t *cr = NULL;

    g_return_val_if_fail( GDK_IS_DRAWABLE( window ), FALSE );
    cr = gdk_cairo_create( window );
    g_return_val_if_fail( cr, FALSE );

    /* Get the correct theme colours */
    style = gtk_widget_get_style (widget);
    text = style->text[GTK_STATE_NORMAL];
    gtk_widget_style_get (GTK_WIDGET (dialog->awn_dialog),
                          "bg_alpha", &alpha, NULL);
                          
    cairo_set_operator( cr, CAIRO_OPERATOR_OVER );


    /*
       Paint "Open Filemanager" link
     */
    cairo_select_font_face( cr, "Sans", 
                            CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD );
    cairo_set_font_size( cr, 14.0 );
    
    cairo_text_extents_t extents;
    cairo_text_extents (cr, STACK_TEXT_OPEN_FILEMANAGER, &extents);
    
    gint x = dialog->fm_box->allocation.x + ((dialog->fm_box->allocation.width - extents.width) / 2);
    gint y = dialog->fm_box->allocation.y + dialog->fm_box->allocation.height - ((dialog->fm_box->allocation.height - extents.height) / 2);
        
    cairo_move_to( cr, x, y);
    cairo_text_path( cr, STACK_TEXT_OPEN_FILEMANAGER );
    if ( eventbox_hovering == FILEMANAGER ) {
        cairo_set_source_rgba( cr, text.red/65535.0, 
                                   text.green/65535.0, 
                                   text.blue/65535.0, 
                                   0.6 );
    } else {
        cairo_set_source_rgba( cr, text.red/65535.0, 
                                   text.green/65535.0, 
                                   text.blue/65535.0, 
                                   1.0 );
    }
    cairo_fill( cr );

    /*
       Paint folder right link
     */

	if(current_folder && stack_folder_has_next_page( current_folder ) ){
    
	    cairo_text_extents (cr, "⇨", &extents);
    
    	x = dialog->frt_box->allocation.x + ((dialog->frt_box->allocation.width - extents.width) / 2);
	    y = dialog->frt_box->allocation.y + dialog->frt_box->allocation.height - (extents.height/2 );
        
    	cairo_move_to( cr, x, y);
	    cairo_text_path( cr, "⇨" );
    	if ( eventbox_hovering == FOLDER_RIGHT ) {
    	    cairo_set_source_rgba( cr, text.red/65535.0, 
                                   text.green/65535.0, 
                                   text.blue/65535.0, 
                                   0.6 );
    	} else {
    	    cairo_set_source_rgba( cr,  text.red/65535.0, 
                                   text.green/65535.0, 
                                   text.blue/65535.0, 
                                   1.0 );
    	}
    	cairo_stroke( cr );
    }

    /*
       Paint folder left link
     */

	if(current_folder && stack_folder_has_prev_page( current_folder ) ){
	    cairo_text_extents (cr, "⇦", &extents);
    
    	x = dialog->flt_box->allocation.x + ((dialog->flt_box->allocation.width - extents.width) / 2);
	    y = dialog->flt_box->allocation.y + dialog->flt_box->allocation.height - (extents.height / 2);
        
    	cairo_move_to( cr, x, y);
	    cairo_text_path( cr, "⇦" );
    	if ( eventbox_hovering == FOLDER_LEFT ) {
    	    cairo_set_source_rgba( cr, text.red/65535.0, 
                                     text.green/65535.0, 
                                     text.blue/65535.0, 
                                     0.6 );
    	} else {
    	    cairo_set_source_rgba( cr, text.red/65535.0, 
                                     text.green/65535.0, 
                                     text.blue/65535.0, 
                                     1.0 );
    	}
	    cairo_stroke( cr );
	}

    /*
       Paint folder up link
	*/
    if(current_folder && dialog->fup_box && gnome_vfs_uri_get_parent( current_folder->uri ) ){
	    cairo_text_extents (cr, "⇧", &extents);
    
    	x = dialog->fup_box->allocation.x + (extents.width / 2);
	    y = dialog->fup_box->allocation.y + dialog->fup_box->allocation.height - (extents.height / 2);
        
		cairo_move_to( cr, x, y);
	    cairo_text_path( cr, "⇧" );
	    if ( eventbox_hovering == FOLDER_UP ) {
	        cairo_set_source_rgba( cr, text.red/65535.0, 
                                     text.green/65535.0, 
                                     text.blue/65535.0, 
                                     0.6 );
	    } else {
	        cairo_set_source_rgba( cr, text.red/65535.0, 
                                     text.green/65535.0, 
                                     text.blue/65535.0, 
                                     1.0 );
	    }
	    cairo_stroke( cr );
	}

    cairo_destroy( cr );

    return FALSE;
}

/**
 * Focus out event
 */
static gboolean stack_dialog_focus_out_event(
    GtkWidget * widget,
    GdkEventFocus * event ) {

    StackDialog *dialog = STACK_DIALOG( widget );

    if ( dialog->active ) {
        stack_dialog_toggle_visiblity( widget );
    }

    return FALSE;
}

/**
 * Recalculate the stack layout
 * -iterate through the list of icons and position each one
 */
static void stack_dialog_relayout(
    StackDialog * dialog ) {
    gint width = 0, height = 0;

	if ( current_folder ){
	    gtk_widget_get_size_request( GTK_WIDGET( current_folder ), &width, &height );
	}

    if ( width < MIN_WIDTH ) {
        width = MIN_WIDTH;
    }

    if ( height < MIN_HEIGHT ) {
        height = MIN_HEIGHT;
    }

	/* Relayout filemanager: */

    dialog->fm_alloc.width = 150;
    dialog->fm_alloc.height = 20;
    dialog->fm_alloc.x = (width - dialog->fm_alloc.width ) / 2;
    dialog->fm_alloc.y = height + 10;

    gtk_widget_set_size_request( dialog->fm_box, dialog->fm_alloc.width, dialog->fm_alloc.height );
    gtk_fixed_move( GTK_FIXED( dialog ), dialog->fm_box,
                    dialog->fm_alloc.x, dialog->fm_alloc.y );
                    
	/* Relayout folder-left */                    

    dialog->flt_alloc.width = 20;
    dialog->flt_alloc.height = 20;
    dialog->flt_alloc.x = -5;
    dialog->flt_alloc.y = height + 10;

    gtk_widget_set_size_request( dialog->flt_box, dialog->flt_alloc.width,
                                 dialog->flt_alloc.height );
    gtk_fixed_move( GTK_FIXED( dialog ), dialog->flt_box,
                    dialog->flt_alloc.x, dialog->flt_alloc.y );
                    
	/* Relayout folder-right */                    

    dialog->frt_alloc.width = 20;
    dialog->frt_alloc.height = 20;
    dialog->frt_alloc.x = width - dialog->frt_alloc.width + 5;
    dialog->frt_alloc.y = height + 10;

    gtk_widget_set_size_request( dialog->frt_box, dialog->frt_alloc.width,
                                 dialog->frt_alloc.height );
    gtk_fixed_move( GTK_FIXED( dialog ), dialog->frt_box,
                    dialog->frt_alloc.x, dialog->frt_alloc.y );
                    
	/* Relayout folder up */
	if( dialog->fup_box ){                    

	    dialog->fup_alloc.width = 20;
    	dialog->fup_alloc.height = 20;
    	dialog->fup_alloc.x = width - dialog->fup_alloc.width + 5;
	    dialog->fup_alloc.y = -25;

    	gtk_widget_set_size_request( dialog->fup_box, dialog->fup_alloc.width,
                                 dialog->fup_alloc.height );
    	gtk_fixed_move( GTK_FIXED( dialog ), dialog->fup_box,
                    dialog->fup_alloc.x, dialog->fup_alloc.y );
	}

    gtk_widget_set_size_request( GTK_WIDGET( dialog ), width, height + DIALOG_CONTROLS_HEIGHT);
    gtk_widget_queue_resize( GTK_WIDGET( dialog ) );
    
}

void stack_dialog_set_folder(
    StackDialog * dialog,
    GnomeVFSURI * uri,
    gint page ) {
    
    GtkWidget *folder = stack_folder_new( STACK_DIALOG( dialog ), uri );

    g_return_if_fail( GTK_IS_WIDGET( folder ) );
    
    gtk_window_set_title( GTK_WINDOW( dialog->awn_dialog ), STACK_FOLDER(folder)->name );

    if ( current_folder ){
    	if( current_folder == backend_folder) {
    		gtk_widget_hide( GTK_WIDGET( backend_folder ) );
    	}else{
	        gtk_widget_destroy( GTK_WIDGET( current_folder ) );
	    }
    }
    gtk_fixed_put( GTK_FIXED( dialog ), folder, 0, 0 );
	
    current_folder = STACK_FOLDER(folder);
    gtk_widget_show( GTK_WIDGET( current_folder ) );
    stack_dialog_relayout( dialog );
}

/**
 * Toggle the visibility of the container
 */
void stack_dialog_toggle_visiblity(
    GtkWidget * widget ) {

    g_return_if_fail( current_folder );
	g_return_if_fail( STACK_IS_DIALOG( widget ) );

    StackDialog *dialog = STACK_DIALOG( widget );

    // toggle visibility
    dialog->active = !dialog->active;
    if ( dialog->active ) {
    	// hide title
        awn_title_hide (dialog->applet->title, GTK_WIDGET(dialog->applet->awn_applet));
		// set icon
        stack_applet_set_icon( dialog->applet, NULL );        
        // recalculate layout
		stack_dialog_relayout( dialog );
		// show the dialog
        gtk_widget_show_all( GTK_WIDGET( dialog->awn_dialog ) );
    } else {
    	// hide dialog
        gtk_widget_hide( dialog->awn_dialog );
		
		// reset to backend folder
		if(current_folder != backend_folder ){
			// destroy current_folder
			gtk_widget_destroy( GTK_WIDGET( current_folder ) );
			// refer to backend folder
			current_folder = backend_folder;
			// reset title
			gtk_window_set_title( GTK_WINDOW( dialog->awn_dialog ), STACK_FOLDER(current_folder)->name );
		}
		
		// set applet icon
		stack_applet_set_icon( dialog->applet, current_folder->applet_icon );
    }
}

/**
 * Initialize an eventbox
 * -create a new one
 * -put it into the GtkFixed
 * -show the box
 * -set event handlers
 */
static GtkWidget *stack_dialog_evbox_init(
    StackDialog * dialog,
    gint target ) {

    GtkWidget *box = gtk_event_box_new(  );

    gtk_fixed_put( GTK_FIXED( dialog ), box, 0, 0 );
    gtk_event_box_set_visible_window( GTK_EVENT_BOX( box ), FALSE );
    gtk_widget_set_events( box, GDK_BUTTON_RELEASE_MASK );
    gtk_widget_show( box );

    g_signal_connect( box, "button-release-event",
                      GTK_SIGNAL_FUNC( stack_dialog_evbox_clicked ), GINT_TO_POINTER( target ) );
    g_signal_connect( box, "enter-notify-event",
                      GTK_SIGNAL_FUNC( stack_dialog_evbox_hover ), GINT_TO_POINTER( target ) );
    g_signal_connect( box, "leave-notify-event",
                      GTK_SIGNAL_FUNC( stack_dialog_evbox_leave ), GINT_TO_POINTER( target ) );

    return box;
}

/**
 * Initialize dialog class
 * Set class functions
 */
static void stack_dialog_class_init(
    StackDialogClass * klass ) {

    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

	parent_class = gtk_type_class (GTK_TYPE_FIXED);

    object_class->destroy = stack_dialog_destroy;

    widget_class->key_press_event = stack_dialog_key_press_event;
    widget_class->expose_event = stack_dialog_expose_event;
    widget_class->focus_out_event = stack_dialog_focus_out_event;
}

/**
 * Initialize the dialog object
 */
static void stack_dialog_init(
    StackDialog * dialog ) {

    dialog->active = FALSE;
    dialog->anim_time = 0.0;

    gtk_widget_add_events( GTK_WIDGET( dialog ), GDK_ALL_EVENTS_MASK );
    GTK_WIDGET_SET_FLAGS ( GTK_WIDGET( dialog ), GTK_CAN_DEFAULT | GTK_CAN_FOCUS );
}

/**
 * Create a new dialog
 * -create dialog from libawn
 * -create eventboxes for action links
 * -open the backend folder specified in the config
 */
GtkWidget *stack_dialog_new(
    StackApplet * applet ) {
    
    StackDialog *dialog = g_object_new( STACK_TYPE_DIALOG, NULL );
    
	dialog->awn_dialog = awn_applet_dialog_new (AWN_APPLET(applet->awn_applet));
    dialog->applet = applet;

    gtk_container_add( GTK_CONTAINER(dialog->awn_dialog), GTK_WIDGET( dialog ) );

	gtk_window_set_focus_on_map (GTK_WINDOW (dialog->awn_dialog), TRUE);

    // Create the filemanager link
    dialog->fm_box = stack_dialog_evbox_init( dialog, FILEMANAGER );
    if( stack_gconf_is_browsing() ){
	    // Create the folder up link
    	dialog->fup_box = stack_dialog_evbox_init( dialog, FOLDER_UP );
    }
    // Create the folder left link
    dialog->flt_box = stack_dialog_evbox_init( dialog, FOLDER_LEFT );
    // Create the folder right link
    dialog->frt_box = stack_dialog_evbox_init( dialog, FOLDER_RIGHT );

	// Create a folder of the backend folder
    stack_dialog_set_folder( dialog, gnome_vfs_uri_new( stack_gconf_get_backend_folder(  ) ), 0 );
    // Set the applet-icon
    stack_applet_set_icon( dialog->applet, current_folder->applet_icon );
    // Reference as backend folder
    backend_folder = current_folder;
	
	gtk_widget_show( GTK_WIDGET( dialog ) );

    return GTK_WIDGET( dialog );
}

