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

#include <gtk/gtk.h>
#include <vte/vte.h>
#include <gconf/gconf-client.h>
#include <string.h>

#include "awnterm.h"
#include "settings.h"

// See settings.h for a semi-logical explanation of what each function does.
// If gtk wasn't such a backwards system then we could get rid of most of them.
// GnuStep is both the past and the future. Unfortunately, it's not the present. ;)

GtkWidget* create_popup_menu ()
{
	GtkWidget *menu;
	GtkWidget *menuitem;
	
	menu = gtk_menu_new ();
	
	menuitem = gtk_menu_item_new_with_label ("Preferences");
	gtk_menu_shell_append (GTK_MENU_SHELL (menu), menuitem);
	g_signal_connect (G_OBJECT (menuitem), "activate", G_CALLBACK (show_settings_window), NULL);
	gtk_widget_show (menuitem);

	menuitem = gtk_menu_item_new_with_label ("About");
	gtk_menu_shell_append (GTK_MENU_SHELL (menu), menuitem);
	g_signal_connect (G_OBJECT (menuitem), "activate", G_CALLBACK (show_about), NULL);
	gtk_widget_show (menuitem);
	
	return menu;
}

void init_settings (AwnTerm *applet)
{
	applet->config = gconf_client_get_default ();
	gconf_client_add_dir (applet->config, GCONF_DIR, GCONF_CLIENT_PRELOAD_ONELEVEL, NULL);
	
	gconf_client_notify_add (applet->config, OPACITY, (GConfClientNotifyFunc) load_opacity, applet, NULL, NULL);
	gconf_client_notify (applet->config, OPACITY);
	
	gconf_client_notify_add (applet->config, BG_IMG, (GConfClientNotifyFunc) load_bg_img, applet, NULL, NULL);
	gconf_client_notify (applet->config, BG_IMG);
	
	gconf_client_notify_add (applet->config, HIDE_ON_UNFOCUS, (GConfClientNotifyFunc) load_hide_on_unfocus, applet, NULL, NULL);
	gconf_client_notify (applet->config, HIDE_ON_UNFOCUS);
}

void load_opacity (GConfClient *client, guint conxn, GConfEntry *entry, AwnTerm *applet)
{
	gtk_window_set_opacity (GTK_WINDOW (applet->dialog), gconf_value_get_float (entry->value));
}

void load_bg_img (GConfClient *client, guint conxn, GConfEntry *entry, AwnTerm *applet)
{
	const gchar *file = gconf_value_get_string (gconf_entry_get_value (entry));
	vte_terminal_set_background_image_file (VTE_TERMINAL (applet->terminal), file);
}

void load_hide_on_unfocus (GConfClient *client, guint conxn, GConfEntry *entry, AwnTerm *applet)
{
	if (!gconf_value_get_bool (gconf_entry_get_value (entry)))
		g_signal_handlers_block_by_func(applet->dialog, focus_out_cb, NULL);
	else
		g_signal_handlers_unblock_by_func(applet->dialog, focus_out_cb, NULL);
}

void save_opacity (GtkWidget *scale, GConfClient *config)
{
	gconf_client_set_float (config, OPACITY, gtk_range_get_value (GTK_RANGE (scale)), NULL);
}

void save_bg_img (GtkWidget *fc, GConfClient *config)
{
	gconf_client_set_string (config, BG_IMG, gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (fc)), NULL);
}

void save_hide_on_unfocus (GtkWidget *check, GConfClient *config)
{
	gconf_client_set_bool (config, HIDE_ON_UNFOCUS, gtk_toggle_button_get_active (GTK_TOGGLE_BUTTON (check)), NULL);
}

void show_about ()
{
	gtk_show_about_dialog (NULL, "program-name", "Awn Terminal", NULL);
}

void show_settings_window ()
{
	GtkWidget *window;
	GtkWidget *box;
	GtkWidget *widget;
	
	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
	
	box = gtk_vbox_new (FALSE, 10);
	gtk_container_add (GTK_CONTAINER (window), box);
	
	widget = gtk_check_button_new_with_label ("Hide On Unfocus");
	g_signal_connect (G_OBJECT (widget), "toggled", G_CALLBACK (save_hide_on_unfocus), applet->config);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (widget), gconf_client_get_bool (applet->config, HIDE_ON_UNFOCUS, NULL));
	gtk_box_pack_start_defaults (GTK_BOX (box), widget);
	
	widget = gtk_file_chooser_button_new ("Select a file", GTK_FILE_CHOOSER_ACTION_OPEN);
	gtk_file_chooser_set_filename (GTK_FILE_CHOOSER (widget), gconf_client_get_string (applet->config, BG_IMG, NULL));
	g_signal_connect (G_OBJECT (widget), "file-set", G_CALLBACK (save_bg_img), applet->config);
	gtk_box_pack_start_defaults (GTK_BOX (box), widget);
	
	widget = gtk_hscale_new_with_range (0.0, 1.0, 0.1);
	gtk_range_set_value (GTK_RANGE (widget), gconf_client_get_float (applet->config, OPACITY, NULL));
	g_signal_connect (G_OBJECT (widget), "value-changed", G_CALLBACK (save_opacity), applet->config);
	gtk_box_pack_start_defaults (GTK_BOX (box), widget);
	
	gtk_widget_show_all (window);
}
