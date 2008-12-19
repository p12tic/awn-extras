/*
 * Copyright (c) 2007 Natan Yellin (Aantn)
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

#include "config.h"

#define APPLET_NAME "awnterm"

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-applet-dialog.h>
#include <vte/vte.h>
#include <gtk/gtk.h>

#include "awnterm.h"
#include "settings.h"

// This function will automatically be called by awn when your applet is added to the dock.
AwnApplet* awn_applet_factory_initp (const gchar* uid, gint orient, gint height )
{
	// Set up the AwnTerm and the AwnApplet. applet is global.
	applet = g_new0 (AwnTerm, 1);
	applet->applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
	
	// Set up the icon
	awn_applet_simple_set_awn_icon(AWN_APPLET_SIMPLE(applet->applet),
									APPLET_NAME,
									"terminal");
	
	// Set up the dialog
	applet->dialog = awn_applet_dialog_new (applet->applet);
	applet->number_of_tabs = 0;
	
	// FIXME
	// Set up a VBox
	// We only use this to avoid problems with size changes during new_tab
	applet->box = gtk_vbox_new (TRUE, 0);
	gtk_container_add (GTK_CONTAINER(applet->dialog), applet->box);
	
	// Set up the notebook
	applet->notebook = gtk_notebook_new();
	gtk_notebook_set_tab_pos (GTK_NOTEBOOK (applet->notebook), GTK_POS_TOP);
	gtk_notebook_set_scrollable(GTK_NOTEBOOK (applet->notebook), TRUE);
	gtk_box_pack_start(GTK_BOX(applet->box), applet->notebook, FALSE, FALSE, 0);
	
	// Hide tabs bar
	gtk_notebook_set_show_tabs (applet->notebook, FALSE);
	
	// Set up a tab with a vte terminal inside of it
	create_new_tab();
	
	// Set up the right click popup menu
	// applet->menu = create_popup_menu ();
	applet->menu = NULL;
	
	// Connect the signals
	g_signal_connect (G_OBJECT (applet->applet), "button-press-event", G_CALLBACK (icon_clicked_cb), NULL);
	g_signal_connect (G_OBJECT (applet->dialog), "focus-out-event", G_CALLBACK (focus_out_cb), NULL);
	
	// Set up the config client
	init_settings (applet);
	
	//Show the applet
	gtk_widget_show_all (GTK_WIDGET (applet->applet));
	
	// Return the AwnApplet
	return applet->applet;
}
