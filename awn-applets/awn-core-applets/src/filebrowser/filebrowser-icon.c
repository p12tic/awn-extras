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

#include "filebrowser-icon.h"
#include "filebrowser-applet.h"
#include "filebrowser-utils.h"
#include "filebrowser-gconf.h"
#include "filebrowser-defines.h"
#include "filebrowser-folder.h"

G_DEFINE_TYPE( FileBrowserIcon, filebrowser_icon, GTK_TYPE_BUTTON )

static gboolean just_dragged = FALSE;

static GtkButtonClass *parent_class = NULL;

/**
 * Destroy events of the applet
 */
static void filebrowser_icon_destroy(
    GtkObject * object ) {

    FileBrowserIcon      *icon = FILEBROWSER_ICON( object );

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

    ( *GTK_OBJECT_CLASS( filebrowser_icon_parent_class )->destroy ) ( object );
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

/**
 * Button released event
 * -shows/launched the file associated with this icon
 */
static gboolean filebrowser_icon_button_release_event(
    GtkWidget * widget,
    GdkEventButton * event ) {

    FileBrowserIcon *icon = FILEBROWSER_ICON( widget );

    if(just_dragged){
        just_dragged = FALSE;
        return FALSE;
    }

    if ( icon->desktop_item ) {
        // with dnd files?
        gnome_desktop_item_launch_with_env( icon->desktop_item, NULL,
                                            GNOME_DESKTOP_ITEM_LAUNCH_ONLY_ONE, NULL, NULL );
    } else if ( icon->uri ) {
        if ( filebrowser_gconf_is_browsing() && is_directory( icon->uri ) ) {
            filebrowser_dialog_set_folder( FILEBROWSER_DIALOG( FILEBROWSER_FOLDER( icon->folder )->dialog ),
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

    return FALSE;
}

/**
 * Drag begin event
 */
static void filebrowser_icon_drag_begin(
    GtkWidget * widget,
    GdkDragContext * drag_context ) {

    FileBrowserIcon *icon = FILEBROWSER_ICON( widget );

    gtk_drag_source_set_icon_pixbuf( widget, icon->icon );
    
    // set up DnD target
    gchar *default_action = filebrowser_gconf_get_default_drag_action();
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
static void filebrowser_icon_drag_data_delete(
    GtkWidget * widget,
    GdkDragContext * drag_context ) {

    // remove icon from container
    g_print( "drag_data_delete\n" );
}

/**
 * Drag data get event
 */
static void filebrowser_icon_drag_data_get(
    GtkWidget * widget,
    GdkDragContext * context,
    GtkSelectionData * selection_data,
    guint info,
    guint time ) {

    FileBrowserIcon *icon = FILEBROWSER_ICON( widget );

    gchar *uri = gnome_vfs_uri_to_string( icon->uri, GNOME_VFS_URI_HIDE_NONE );

    gtk_selection_data_set( selection_data, GDK_SELECTION_TYPE_STRING, 8,
                            ( guchar * ) uri, ( gint ) strlen( uri ) );

    g_free( uri );
}

/**
 * Drag end event
 */
static void filebrowser_icon_drag_end(
    GtkWidget * widget,
    GdkDragContext * drag_context ) {

    g_print( "drag_end\n" );
    just_dragged = FALSE;
}

/**
 * Initialize applet class
 * Set class functions
 */
static void filebrowser_icon_class_init(
    FileBrowserIconClass * klass ) {

    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

    parent_class = gtk_type_class (GTK_TYPE_BUTTON);

    object_class->destroy = filebrowser_icon_destroy;

   	/* Messages for outgoing drag. */
    widget_class->drag_begin = filebrowser_icon_drag_begin;
    widget_class->drag_data_get = filebrowser_icon_drag_data_get;
    //widget_class->drag_end = filebrowser_icon_drag_end;  
    //widget_class->drag_data_delete = filebrowser_icon_drag_data_delete;

	/* Messages for incoming drag. */	
	//widget_class->drag_data_delete = filebrowser_icon_drag_data_received;
	//widget_class->drag_data_delete = filebrowser_icon_drag_data_motion;
	//widget_class->drag_data_delete = filebrowser_icon_drag_data_drop;
	//widget_class->drag_data_delete = filebrowser_icon_drag_data_leave;

}

/**
 * Initialize the new applet
 */
static void filebrowser_icon_init(
    FileBrowserIcon * icon ) {

    gtk_widget_add_events( GTK_WIDGET( icon ), GDK_ALL_EVENTS_MASK );
}

/**
 * Create a new filebrowser icon
 */
GtkWidget *filebrowser_icon_new(
    FileBrowserFolder * folder,
    GnomeVFSURI * uri ) {

	g_return_val_if_fail( folder && uri, NULL );

    FileBrowserIcon      *icon = g_object_new( FILEBROWSER_TYPE_ICON, NULL );

    const gchar    *name = gnome_vfs_uri_extract_short_name( uri );
    const gchar    *file_path = gnome_vfs_uri_get_path( uri );
    guint           icon_size = filebrowser_gconf_get_icon_size(  );


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
        icon->icon = get_icon( desktop_file_get_link_icon_from_desktop( icon->desktop_item ), uri, icon_size ); 
    } else {
        icon->uri = gnome_vfs_uri_dup( uri );
    }

	// If we do not assigned an icon yet
    if ( !icon->icon ) {
        icon->icon = get_icon( file_path, uri, icon_size );
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


    GtkWidget *vbox;
    GtkWidget *image;
    GdkPixbuf *pixbuf;
    GtkWidget *label;

    gtk_button_set_relief (GTK_BUTTON (icon), GTK_RELIEF_NONE);
    g_signal_connect (G_OBJECT (icon), "button-release-event",
                    G_CALLBACK (filebrowser_icon_button_release_event), (gpointer)icon);

    vbox = gtk_vbox_new (FALSE, 2);
    gtk_container_add (GTK_CONTAINER (icon), vbox);
  
    image = gtk_image_new_from_pixbuf (icon->icon);
    //gint w = gdk_pixbuf_get_width(icon->icon);
    //gint h = gdk_pixbuf_get_height(icon->icon);
    //gtk_widget_set_size_request(image, w > h ? 48 : -1, w > h ? -1 : 48);

    label = gtk_label_new(icon->name);
    gtk_widget_set_size_request (label, icon_size*5/4, icon_size/2);

    g_object_set(label,
            "justify", GTK_JUSTIFY_CENTER,
            "use-markup", TRUE,
            "wrap", TRUE,
            "wrap-mode", PANGO_WRAP_WORD,
            NULL);

    PangoLayout *layout = gtk_label_get_layout(GTK_LABEL(label));

    char *newText = g_strdup_printf("");
    int i, k=0;
    int lines = pango_layout_get_line_count(layout);
    for (i=0; i<lines; i++) {
        int len = pango_layout_get_line(layout, i)->length;
        int startIndex = pango_layout_get_line(layout, i)->start_index;
        char *trimmedText = g_strdup(gtk_label_get_text(GTK_LABEL(label))+startIndex);
        trimmedText[len] = '\0';
        char *lastText = newText;
        newText = g_strdup_printf(i != lines-1 ? "%s%s\n" : "%s%s", lastText, trimmedText);
        k = len;
        g_free(trimmedText);
        g_free(lastText);
    }
    gtk_label_set_text(GTK_LABEL(label), newText);
    gtk_label_set_ellipsize(GTK_LABEL(label), PANGO_ELLIPSIZE_END);
    g_free(newText);

    gtk_box_pack_start (GTK_BOX (vbox), image, FALSE, FALSE, 0);
    gtk_box_pack_start (GTK_BOX (vbox), label, TRUE, TRUE, 0);

    gtk_widget_set_size_request(vbox, icon_size*5/4, icon_size*7/4);

    return GTK_WIDGET( icon );
}

