/*
 *  Copyright (C) 2007 Neil Jagdish Patel <njpatel@gmail.com>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
 *  Author : Neil Jagdish Patel <njpatel@gmail.com>
 *
 *  Notes : This is the actual icon on the app, the "Application Icon" 
*/

#ifndef	_AFF_SETTINGS_H
#define	_AFF_SETTINGS_H

#include <glib.h>
#include <gtk/gtk.h>

#include <libawn/awn-config-client.h>

typedef struct {
	float red; 
	float green;
	float blue;
	float alpha;

} AffColor; /* spelt incorrectly, in the interest of brevity ;) */

typedef struct {
	/* exec */
	gchar *open_uri;
	gchar *file_manager;
	gchar *computer;
	gchar *network;
	
	/* keybinding */
	gchar *key_binding;
	
	/* favourites */
	gchar *favourites;
	
	/* window position */
	gint window_x;
	gint window_y;
	
        /* filters */
        gchar *apps;
	gchar *books;
	gchar *contacts;
	gchar *docs;
	gchar *emails;
	gchar *images;
	gchar *music;
	gchar *vids;
	
	/* system calls */
	gchar *config_software;
	gchar *control_panel;
	gchar *lock_screen;
	gchar *log_out;
	
	/* Appearence */
	gboolean rounded_corners;
	AffColor back_step_1;
	AffColor back_step_2;
	AffColor hi_step_1;
	AffColor hi_step_2;
	AffColor highlight;
	AffColor border;
	
	AffColor widget_border;
	AffColor widget_highlight;
	
	gchar *text_color; 
	
	/* Applet specific */
	gchar *applet_icon;
	gchar *applet_name;
	
} AffSettings;


AffSettings* aff_settings_new(void);

AffSettings* aff_Settings_get_default (void);

AwnConfigClient *aff_settings_get_client (void);

#endif /* _AFF_GCONF_H */
