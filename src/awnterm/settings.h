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

#ifndef SETTINGS_H_
#define SETTINGS_H_

#define OPACITY "opacity"
#define BG_IMG "bg_img"
#define HIDE_ON_UNFOCUS "hide_on_unfocus"
#define MAIN_TERMINAL "main_terminal"

#include <libdesktop-agnostic/desktop-agnostic.h>
#include <gtk/gtk.h>

#include "awnterm.h"

// Create the right click popup menu.
GtkWidget* create_popup_menu (AwnTerm *applet);

// Shows the about box which is currently empty :)
void show_about ();

// Set up the config client when the applet starts up
void init_settings (AwnTerm *applet);

/* Each of the following functions is called once on startup, and whenever a setting is changed.
 * They each read a key from config and set a property by wrapping a gtk_window_set or vte_terminal_set function.
 * Its done this way because gtk is too stupid to handle things otherwise. */
void load_opacity (const gchar *group, const gchar *key, const GValue *value, gpointer user_data);
void load_bg_img (const gchar *group, const gchar *key, const GValue *value, gpointer user_data);
void load_hide_on_unfocus (const gchar *group, const gchar *key, const GValue *value, gpointer user_data);

/* Each of the following functions is called whenever a setting is changed from the settings window
 * For ever load_* function, there exists a save_* function. */
void save_opacity (GtkWidget *scale, DesktopAgnosticConfigClient *config);
void save_bg_img (GtkWidget *fc, DesktopAgnosticConfigClient *config);
void save_hide_on_unfocus (GtkWidget *check, DesktopAgnosticConfigClient *config);

// Show the preference window
void show_settings_window ();


#endif /*SETTINGS_H_*/
