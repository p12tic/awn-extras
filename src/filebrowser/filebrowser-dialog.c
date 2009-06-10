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
#include <libawn/awn-dialog.h>
#include <libgnomevfs/gnome-vfs.h>
#include <gdk/gdkkeysyms.h>
#include <glib/gi18n.h>
#include <math.h>

#include "filebrowser-dialog.h"
#include "filebrowser-applet.h"
#include "filebrowser-icon.h"
#include "filebrowser-gconf.h"
#include "filebrowser-defines.h"
#include "filebrowser-utils.h"
#include "filebrowser-folder.h"

G_DEFINE_TYPE( FileBrowserDialog, filebrowser_dialog, GTK_TYPE_VBOX )

enum {
    NONE = 0,
    FILEMANAGER = 1,
    FOLDER_LEFT = 2,
    FOLDER_RIGHT = 3,
    FOLDER_UP = 4
};

static GtkVBoxClass *parent_class = NULL;

static FileBrowserFolder *current_folder = NULL;
static GtkWidget *folder_up = NULL;
static GtkWidget *no_items_label = NULL;

static void setup_adjustment(FileBrowserDialog *dialog);
static void scroll_changed(GtkAdjustment *adj, FileBrowserDialog *dialog);

static void filebrowser_dialog_do_folder_up(
    GtkWidget * dialog ) {
    GnomeVFSURI *parent = gnome_vfs_uri_get_parent( current_folder->uri );

    if (parent == NULL) {
        return;
    }

    filebrowser_dialog_set_folder( FILEBROWSER_DIALOG( dialog ), parent, 0 );
}

/**
 * Eventbox clicked event
 * -find out source
 * -perform corresponding action
 */
static gboolean filebrowser_dialog_button_clicked(
    GtkWidget * widget,
    GdkEventButton * event,
    gpointer user_data ) {

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
        break;
    case FOLDER_UP:
        filebrowser_dialog_do_folder_up( GTK_WIDGET( current_folder->dialog ) );
        break;
    default:
        break;
    }
    return FALSE;
}

static gboolean filebrowser_dialog_key_press_event(
    GtkWidget * widget,
    GdkEventKey * event ) {

    g_return_val_if_fail( FILEBROWSER_IS_DIALOG( widget ), FALSE );
    FileBrowserDialog *dialog = FILEBROWSER_DIALOG(widget);

    if ( event->keyval == GDK_Left) {
      if (filebrowser_folder_has_prev_page(current_folder))
      {
        dialog->adj->value--;
        scroll_changed(dialog->adj, dialog);
      }
    } else if ( event->keyval == GDK_Right) {
      if (filebrowser_folder_has_next_page(current_folder))
      {
        dialog->adj->value++;
        scroll_changed(dialog->adj, dialog);
      }
    } else if ( event->keyval == GDK_Up && filebrowser_gconf_is_browsing()) {
      filebrowser_dialog_do_folder_up( widget );
    }

    return FALSE;
}

/**
 * Destroy event
 */
static void filebrowser_dialog_destroy(
    GtkObject * object ) {

    FileBrowserDialog *dialog = FILEBROWSER_DIALOG( object );

    ( *GTK_OBJECT_CLASS( filebrowser_dialog_parent_class )->destroy ) ( object );
}

/**
 * Focus out event
 */
static gboolean filebrowser_dialog_focus_out_event(
    GtkWidget * widget,
    GdkEventFocus * event,
    gpointer user_data ) {

    FileBrowserDialog *dialog = FILEBROWSER_DIALOG( user_data );

    if ( dialog->active ) {
        filebrowser_dialog_toggle_visiblity( GTK_WIDGET( dialog ) );
    }

    return FALSE;
}

void filebrowser_dialog_set_folder(
    FileBrowserDialog * dialog,
    GnomeVFSURI * uri,
    gint page ) {
    
    GtkWidget *folder;

    if (!uri) uri = gnome_vfs_uri_new( filebrowser_gconf_get_backend_folder() );

    /* Check if we're actually changing the folder */
    if (current_folder)
    {
      gchar *new_folder = uri->text;
      gchar *current = current_folder->uri->text;
      if (strcmp(new_folder, current) == 0)
      {
        filebrowser_folder_layout(current_folder, 0);
        setup_adjustment(dialog);
        return;
      }
    }

    folder = filebrowser_folder_new( FILEBROWSER_DIALOG( dialog ), uri );

    g_return_if_fail( GTK_IS_WIDGET( folder ) );
    
    gtk_window_set_title( GTK_WINDOW( dialog->awn_dialog ), FILEBROWSER_FOLDER(folder)->name );

    if ( current_folder ){
        gtk_widget_destroy( GTK_WIDGET( current_folder ) );
    }

    gtk_container_add( GTK_CONTAINER( dialog->viewport), folder);
	
    current_folder = FILEBROWSER_FOLDER(folder);

    gtk_widget_set_sensitive(folder_up, filebrowser_folder_has_parent_folder(current_folder));

    // no items label
    if (current_folder->total > 0) {
        gtk_label_set_text(GTK_LABEL(no_items_label), "");
	gtk_widget_set_size_request(no_items_label, 1, 1);
    } else {
        gtk_label_set_text(GTK_LABEL(no_items_label), _("There are no items to display."));
	gtk_widget_set_size_request(no_items_label, 192, 192);
    }

    setup_adjustment(dialog);

    gtk_widget_show_all( GTK_WIDGET( current_folder ) );
}

/**
 * Toggle the visibility of the container
 */
void filebrowser_dialog_toggle_visiblity(
    GtkWidget * widget ) {

    g_return_if_fail( current_folder );
    g_return_if_fail( FILEBROWSER_IS_DIALOG( widget ) );

    FileBrowserDialog *dialog = FILEBROWSER_DIALOG( widget );

    // toggle visibility
    dialog->active = !dialog->active;
    if ( dialog->active ) {
	// set icon
        filebrowser_applet_set_icon( dialog->applet, NULL ); 
	// show the dialog
        gtk_widget_show_all( GTK_WIDGET( dialog->awn_dialog ) );
    } else {
	// hide dialog
	gtk_widget_hide( dialog->awn_dialog );

	// reset to backend folder
	//filebrowser_dialog_set_folder( dialog, gnome_vfs_uri_new( filebrowser_gconf_get_backend_folder() ), 0 );
	// reset title
	//gtk_window_set_title( GTK_WINDOW( dialog->awn_dialog ), FILEBROWSER_FOLDER(current_folder)->name );
	gtk_window_set_title( GTK_WINDOW( dialog->awn_dialog ), filebrowser_gconf_get_backend_folder() );

  filebrowser_dialog_set_folder( dialog, NULL, 0 );
	// set applet icon
	//filebrowser_applet_set_icon( dialog->applet, current_folder->applet_icon );
    }
}

/* Set up the GtkAdjustment for the HScrollBar */
static void
setup_adjustment(FileBrowserDialog *dialog)
{
  gint total, rows, cols, mult, pages, current;
  gfloat num;
  total = current_folder->total;
  rows = filebrowser_gconf_get_max_rows();
  cols = filebrowser_gconf_get_max_cols();
  mult = rows * cols;
  num = (gfloat)total / mult;
  num = ceil(num);
  pages = (int)num;
  current = current_folder->offset / mult;

  dialog->last_page = current;
  dialog->adj->value = current;
  dialog->adj->upper = pages;
}

/* Called when the value of the scrollbar changes */
static void
scroll_changed(GtkAdjustment *adj, FileBrowserDialog *dialog)
{
  gint page, rows, cols, new_offset;

  page = round(adj->value);
  if (page == dialog->last_page)
    return;

  rows = filebrowser_gconf_get_max_rows();
  cols = filebrowser_gconf_get_max_cols();
  new_offset = current_folder->offset + (page - dialog->last_page) * (rows * cols);
  filebrowser_folder_layout(current_folder, new_offset);
  gtk_widget_show_all(GTK_WIDGET(current_folder));

  dialog->last_page = page;
}

/**
 * Initialize dialog class
 * Set class functions
 */
static void filebrowser_dialog_class_init(
    FileBrowserDialogClass * klass ) {

    GtkObjectClass *object_class;
    GtkWidgetClass *widget_class;

    object_class = ( GtkObjectClass * ) klass;
    widget_class = ( GtkWidgetClass * ) klass;

	parent_class = gtk_type_class (GTK_TYPE_VBOX);

    object_class->destroy = filebrowser_dialog_destroy;

    widget_class->key_press_event = filebrowser_dialog_key_press_event;
}

/**
 * Initialize the dialog object
 */
static void filebrowser_dialog_init(
    FileBrowserDialog * dialog ) {

    dialog->active = FALSE;

    gtk_widget_add_events( GTK_WIDGET( dialog ), GDK_ALL_EVENTS_MASK );
    GTK_WIDGET_SET_FLAGS ( GTK_WIDGET( dialog ), GTK_CAN_DEFAULT | GTK_CAN_FOCUS );
}

/**
 * Create a new dialog
 * -create dialog from libawn
 * -create eventboxes for action links
 * -open the backend folder specified in the config
 */
GtkWidget *filebrowser_dialog_new(
	FileBrowserApplet * applet ) {
    
	FileBrowserDialog *dialog = g_object_new( FILEBROWSER_TYPE_DIALOG, NULL );

	dialog->awn_dialog = awn_dialog_new_for_widget (applet->awn_applet);
	dialog->applet = applet;

	gtk_container_add( GTK_CONTAINER(dialog->awn_dialog), GTK_WIDGET( dialog ) );

	gtk_window_set_focus_on_map (GTK_WINDOW (dialog->awn_dialog), TRUE);
	g_signal_connect (G_OBJECT (dialog->awn_dialog), "focus-out-event",
			G_CALLBACK (filebrowser_dialog_focus_out_event), dialog);
	
	if( filebrowser_gconf_is_browsing() ){
		GtkWidget *hbox1 = gtk_hbox_new(FALSE, 0);
		gtk_container_add(GTK_CONTAINER(dialog), hbox1);
		folder_up = gtk_button_new_from_stock(GTK_STOCK_GO_UP);
		gtk_button_set_relief(GTK_BUTTON(folder_up), GTK_RELIEF_NONE);
		g_signal_connect( folder_up, "button-release-event",
                      GTK_SIGNAL_FUNC( filebrowser_dialog_button_clicked ), GINT_TO_POINTER( FOLDER_UP ) );
		GtkWidget *upper_bin = gtk_alignment_new(0, 0.5, 0, 0);
		gtk_container_add(GTK_CONTAINER(upper_bin), folder_up);
		gtk_box_pack_start(GTK_BOX(hbox1), upper_bin, TRUE, TRUE, 0);

		GtkWidget *filemanager = gtk_button_new_with_label(_("Open filemanager"));
		gtk_button_set_relief(GTK_BUTTON(filemanager), GTK_RELIEF_NONE);
		g_signal_connect( filemanager, "button-release-event",
			GTK_SIGNAL_FUNC( filebrowser_dialog_button_clicked ), GINT_TO_POINTER( FILEMANAGER ) );
		gtk_box_pack_start(GTK_BOX(hbox1), filemanager, FALSE, FALSE, 0);
	}

	no_items_label = gtk_label_new("");
	gtk_widget_set_size_request(no_items_label, 1, 1);
	gtk_label_set_line_wrap(GTK_LABEL(no_items_label), TRUE);
	gtk_label_set_justify(GTK_LABEL(no_items_label), GTK_JUSTIFY_CENTER);
	gtk_container_add(GTK_CONTAINER(dialog), no_items_label);

	dialog->viewport = gtk_event_box_new();
	gtk_event_box_set_visible_window(GTK_EVENT_BOX(dialog->viewport), FALSE);
	gtk_container_add(GTK_CONTAINER(dialog), dialog->viewport);
	

  /* HScrollBar with GtkAdjustment*/
  dialog->adj = gtk_adjustment_new(0, 0, 0, 1, 1, 1);
  dialog->hscroll = gtk_hscrollbar_new(NULL);
  gtk_range_set_adjustment(GTK_RANGE(dialog->hscroll), dialog->adj);
  g_signal_connect(G_OBJECT(dialog->adj), "value-changed",
                   G_CALLBACK(scroll_changed), (gpointer)dialog);

  /* GtkAlignment for the scroll bar */
  GtkWidget *align = gtk_alignment_new(0.5, 1.0, 1.0, 0.0);
  gtk_alignment_set_padding(GTK_ALIGNMENT(align), 3, 0, 0, 0);
  gtk_container_add(GTK_CONTAINER(align), dialog->hscroll);
  gtk_container_add(GTK_CONTAINER(dialog), align);

	// Create a folder of the backend folder
	filebrowser_dialog_set_folder( dialog, gnome_vfs_uri_new( filebrowser_gconf_get_backend_folder() ), 0 );

	// Set the applet-icon
	filebrowser_applet_set_icon( dialog->applet, current_folder->applet_icon );

	gtk_widget_show_all( GTK_WIDGET( dialog ) );

    return GTK_WIDGET( dialog );
}

