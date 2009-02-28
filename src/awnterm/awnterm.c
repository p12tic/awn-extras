/*
 * Copyright (c) 2007 Aantn
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

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn-extras/awn-extras.h>
#include <gtk/gtk.h>
#include <gdk/gdkkeysyms.h>
#include <vte/vte.h>
#include <string.h>

#include "awnterm.h"
#include "settings.h"

// Callback when the icon is clicked on.
gboolean icon_clicked_cb (GtkWidget *widget, GdkEventButton *event, gpointer null)
{
	char *main_terminal;
	
	switch (event->button)
	{
		case 1:
			if (!GTK_WIDGET_VISIBLE (applet->dialog))
			{
				gtk_widget_show_all (applet->dialog);
	//			awn_applet_simple_set_title_visibility (AWN_APPLET_SIMPLE (applet->applet), FALSE);
			}
			else
			{
				gtk_widget_hide (applet->dialog);
			}
			break;
		case 2:
			main_terminal = awn_config_client_get_string (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, MAIN_TERMINAL, NULL);
			if (!main_terminal) main_terminal = g_strdup ("gnome-terminal");
			gdk_spawn_command_line_on_screen (gtk_widget_get_screen (widget), main_terminal, NULL);
			g_free (main_terminal);
			break;
		case 3:
			// Create the popup menu if we haven't already done so
			if (applet->menu == NULL)
			{
				applet->menu = create_popup_menu (applet);
			}
			gtk_menu_popup (GTK_MENU (applet->menu), NULL, NULL, NULL, NULL, 3, event->time);
			break;
	}
	return FALSE;
}

// Callback when the applet's dialog box loses focus
gboolean focus_out_cb (GtkWidget *window, GdkEventFocus *event, gpointer null)
{
    if (share_config_bool(SHR_KEY_FOCUS_LOSS) )
    {
    	gtk_widget_hide (window);
    }        
	return FALSE;
}

// Callback when a key is pressed. We check for the keyboard shortcuts for copy and paste. If they're found, we act accordingly.
gboolean key_press_cb (GtkWidget *terminal, GdkEventKey *event)
{
	// Checks if the modifiers control and shift are pressed
	if (event->state & GDK_CONTROL_MASK && event->state & GDK_SHIFT_MASK)
	{
		gchar *key = gdk_keyval_name (gdk_keyval_to_lower (event->keyval));
		// Copy
		if (! strncmp (key, "c", 1))
			vte_terminal_copy_clipboard (VTE_TERMINAL (terminal));
		
		// Paste
		if (! strncmp (key, "v", 1))
			vte_terminal_paste_clipboard (VTE_TERMINAL (terminal));
		
		// New tab
		if (! strncmp (key, "t", 1))
			create_new_tab();
		
		// Signify that the event has been handled
		return TRUE;
	}
	else
	{
		// Signify that event has not been handled
		return FALSE;
	}
}

// Callback when "exit" command is executed
void exited_cb (GtkWidget *terminal, gpointer null)
{
	gint page;
	
	gint n_page = gtk_notebook_get_n_pages (GTK_NOTEBOOK(applet->notebook));

	if (n_page > 1)
	{
		page = gtk_notebook_current_page(GTK_NOTEBOOK(applet->notebook));
		gtk_notebook_remove_page (GTK_NOTEBOOK(applet->notebook), page);
		gtk_widget_show_all(GTK_WIDGET(applet->dialog));
		
		if (n_page == 2)
		{
			gtk_notebook_set_show_tabs (GTK_NOTEBOOK(applet->notebook), FALSE);
		}
		
		gtk_widget_show_all(GTK_WIDGET(applet->dialog));
	}
	else {
		// fork new vte
		vte_terminal_fork_command (VTE_TERMINAL (terminal),
								NULL,
								NULL,
								NULL,
								"~/",
								FALSE,
								FALSE,
								FALSE);
		gtk_widget_hide (applet->dialog);
	}
}

// Create a new tab
gboolean create_new_tab()
{
	GtkWidget *terminal;
	char buffer[32];
	
	// Set up the new vte terminal
	terminal = vte_terminal_new ();
	vte_terminal_set_emulation (VTE_TERMINAL (terminal), "xterm");
	vte_terminal_fork_command (VTE_TERMINAL (terminal),
								NULL,
								NULL,
								NULL,
								"~/",
								FALSE,
								FALSE,
								FALSE);

	// New Label
	applet->number_of_tabs += 1;
	sprintf(buffer, "Term #%d", applet->number_of_tabs);
	applet->label = gtk_label_new(buffer);

	// New Page
	applet->label = gtk_label_new(buffer);
	gtk_notebook_append_page (GTK_NOTEBOOK (applet->notebook), GTK_WIDGET(terminal), applet->label);
	
	// Show Tab
	if(gtk_notebook_get_n_pages(GTK_NOTEBOOK(applet->notebook)) > 1)
	{
		gtk_notebook_set_show_tabs (GTK_NOTEBOOK(applet->notebook), TRUE);
		gtk_widget_show_all(GTK_WIDGET(applet->dialog));
	}
	
	// Connect to signals and events
	g_signal_connect (G_OBJECT (terminal), "child-exited", G_CALLBACK (exited_cb), NULL);
	g_signal_connect (G_OBJECT (terminal), "key-press-event", G_CALLBACK (key_press_cb), NULL);
	
	return TRUE;
}
