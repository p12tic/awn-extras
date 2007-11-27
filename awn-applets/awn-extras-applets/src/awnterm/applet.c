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

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-applet-dialog.h>
#include <vte/vte.h>
#include <gdk/gdkkeysyms.h>
#include <string.h>
#include "config.h"

typedef struct
{
	AwnApplet *applet;
	GdkPixbuf *icon;
	GtkWidget *dialog;
	GtkWidget *terminal;

}AwnTerm;

// Callback when the icon is clicked on.
static gboolean icon_clicked_cb (GtkWidget *widget, GdkEventButton *event, AwnTerm *term)
{
	if (!GTK_WIDGET_VISIBLE (term->dialog))
	{
		gtk_widget_show_all (term->dialog);
	}
	else
	{
		gtk_widget_hide (term->dialog);
	}
	return FALSE;
}

// Callback when the applet's dialog box loses focus
static gboolean focus_out_cb (GtkWidget *window, GdkEventFocus *event, gpointer null)
{
	gtk_widget_hide (window);
	return FALSE;
}
// Callback when a key is pressed. We check for the keyboard shortcuts for copy and paste. If they're found, we act accordingly.
static gboolean key_press_cb (GtkWidget *window, GdkEventKey *event, GtkWidget *terminal)
{
	// Checks if the modifiers control and shift are pressed
	if (event->state & GDK_CONTROL_MASK && event->state & GDK_SHIFT_MASK)
	{
		gchar *key = gdk_keyval_name (gdk_keyval_to_lower (event->keyval));
		
		// Copy
		if (! strncmp (key, "c", 1)) vte_terminal_copy_clipboard (VTE_TERMINAL (terminal));
		// Paste
		if (! strncmp (key, "v", 1)) vte_terminal_paste_clipboard (VTE_TERMINAL (terminal));
		// Signify that event has been handled
		return TRUE;
	}
	else
	{
		// Signify that event has not been handled
		return FALSE;
	}
}

AwnApplet* awn_applet_factory_initp (const gchar* uid, gint orient, gint height )
{
	AwnTerm *applet;
		
	// Set up the AwnTerm and the AwnApplet
	g_print ("Setting up the applet and the terminal...");
	applet = g_new0 (AwnTerm, 1);
	applet->applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
		
	// Set up the icon 
	applet->icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (), "terminal", height -2, 0, NULL);
	awn_applet_simple_set_icon (AWN_APPLET_SIMPLE (applet->applet), applet->icon);

	// Set up the dialog and the scrolled window
	applet->dialog = awn_applet_dialog_new (applet->applet);
	
	// Set up the vte terminal
	applet->terminal = vte_terminal_new ();
	vte_terminal_set_emulation (VTE_TERMINAL (applet->terminal), "xterm");
	vte_terminal_fork_command (VTE_TERMINAL (applet->terminal),
                                             NULL,
                                             NULL,
                                             NULL,
                                             "~/",
                                             FALSE,
                                             FALSE,
                                             FALSE);
	gtk_container_add (GTK_CONTAINER (applet->dialog), applet->terminal);
	
	// Connect the signals
	g_signal_connect (G_OBJECT (applet->applet), "button-press-event", G_CALLBACK (icon_clicked_cb), (gpointer)applet);
	g_signal_connect (G_OBJECT (applet->dialog), "focus-out-event", G_CALLBACK (focus_out_cb), NULL);
	g_signal_connect (G_OBJECT (applet->dialog), "key-press-event", G_CALLBACK (key_press_cb), applet->terminal);
	
	//Show the applet
	gtk_widget_show_all (GTK_WIDGET (applet->applet));
	
	return applet->applet;
}
