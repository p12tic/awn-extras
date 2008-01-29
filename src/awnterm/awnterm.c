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
#include <gtk/gtk.h>
#include <gdk/gdkkeysyms.h>
#include <gconf/gconf-client.h>
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
			}
			else
			{
				gtk_widget_hide (applet->dialog);
			}
			break;
		case 2:
			main_terminal = gconf_client_get_string (applet->config, MAIN_TERMINAL, NULL);
			if (!main_terminal) main_terminal = g_strdup ("gnome-terminal");
			gdk_spawn_command_line_on_screen (gtk_widget_get_screen (widget), main_terminal, NULL);
			g_free (main_terminal);
			break;
		case 3:
			// Create the popup menu if we haven't already done so
			if (applet->menu == NULL)
			{
				applet->menu = create_popup_menu ();
			}
			gtk_menu_popup (GTK_MENU (applet->menu), NULL, NULL, NULL, NULL, 3, event->time);
			break;
	}
	return FALSE;
}

// Callback when the applet's dialog box loses focus
gboolean focus_out_cb (GtkWidget *window, GdkEventFocus *event, gpointer null)
{
	gtk_widget_hide (window);
	return FALSE;
}

// Callback when a key is pressed. We check for the keyboard shortcuts for copy and paste. If they're found, we act accordingly.
gboolean key_press_cb (GtkWidget *window, GdkEventKey *event, GtkWidget *terminal)
{
	// Checks if the modifiers control and shift are pressed
	if (event->state & GDK_CONTROL_MASK && event->state & GDK_SHIFT_MASK)
	{
		gchar *key = gdk_keyval_name (gdk_keyval_to_lower (event->keyval));
		
		// Copy
		if (! strncmp (key, "c", 1)) vte_terminal_copy_clipboard (VTE_TERMINAL (terminal));
		// Paste
		if (! strncmp (key, "v", 1)) vte_terminal_paste_clipboard (VTE_TERMINAL (terminal));
		// Free the memory
		g_free (key);
		// Signify that event has been handled
		return TRUE;
	}
	else
	{
		// Signify that event has not been handled
		return FALSE;
	}
}
