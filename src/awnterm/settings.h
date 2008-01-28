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

#define GCONF_DIR "/apps/avant-window-navigator/applets/awn-terminal"
#define OPACITY GCONF_DIR"/opacity"
#define BG_IMG GCONF_DIR"/bg_img"
#define HIDE_ON_UNFOCUS GCONF_DIR"/hide_on_unfocus"
#define MAIN_TERMINAL GCONF_DIR"/main_terminal"
#define KEY(a) GCONF_DIR#a; 

#include <gtk/gtk.h>

#include "awnterm.h"

// Create the right click popup menu.
GtkWidget* create_popup_menu ();

// Shows the about box which is currently empty :)
void show_about ();

// Set up the gconf client when the applet starts up
void init_settings (AwnTerm *applet);

//void add_key (AwnTerm *applet, gchar *key, (GConfClientNotifyFunc) func)

/* Each of the following functions is called once on startup, and whenever a gconf key is changed.
 * They each read a key from gconf and set a property by wrapping a gtk_window_set or vte_terminal_set function.
 * Its done this way because gtk is too stupid to handle things otherwise. */
void load_opacity (GConfClient *client, guint conxn, GConfEntry *entry, AwnTerm *applet);
void load_bg_img (GConfClient *client, guint conxn, GConfEntry *entry, AwnTerm *applet);
void load_hide_on_unfocus (GConfClient *client, guint conxn, GConfEntry *entry, AwnTerm *applet);

/* Each of the following functions is called whenever a setting is changed from the settings window
 * For ever load_* function, there exists a save_* function. */
void save_opacity (GtkWidget *scale, GConfClient *config);
void save_bg_img (GtkWidget *fc, GConfClient *config);
void save_hide_on_unfocus (GtkWidget *check, GConfClient *config);

/* The following function is called when the main terminal option is changed from the preferences window
 * By design, there is no load_main_terminal () because that setting is loaded on an as need basis. */
void save_main_terminal (GtkWidget *entry, GConfClient *config);

// Show the preference window
void show_settings_window ();


#endif /*SETTINGS_H_*/
