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

#ifndef AWNTERM_H_
#define AWNTERM_H_

#include <libawn/awn-applet.h>
#include <gtk/gtk.h>
#include <gconf/gconf-client.h>

typedef struct
{
	AwnApplet *applet;
	GdkPixbuf *icon;
	GtkWidget *dialog;
	GtkWidget *terminal;
	GtkWidget *menu;
	GConfClient *config;
}AwnTerm;

// The applet instance. We need to make it global so that we can access it in a bunch of callbacks.
AwnTerm *applet;

// Callback when the icon is clicked on.
gboolean icon_clicked_cb (GtkWidget *widget, GdkEventButton *event, gpointer null);

// Callback when the applet's dialog box loses focus
gboolean focus_out_cb (GtkWidget *window, GdkEventFocus *event, gpointer null);

// Callback when a key is pressed. We check for the keyboard shortcuts for copy and paste. If they're found, we act accordingly.
gboolean key_press_cb (GtkWidget *window, GdkEventKey *event, GtkWidget *terminal);

// Callback when the vte terminal widget quits. This doesn't do anything yet.
void exited_cb (GtkWidget *terminal, gpointer null);
#endif /*AWNTERM_H_*/
