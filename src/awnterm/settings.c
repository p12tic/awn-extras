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
#include <string.h>

#include "awnterm.h"
#include "settings.h"

// See settings.h for a semi-logical explanation of what each function does.
// If gtk wasn't such a backwards system then we could get rid of most of them.
// GnuStep is both the past and the future. Unfortunately, it's not the present. ;)

static void set_opacity (AwnTerm *applet, gfloat opacity);
static void set_bg_img (AwnTerm *applet, gchar *path);
static void set_hide_on_unfocus (AwnTerm *applet, gboolean value);

GtkWidget* create_popup_menu (AwnTerm *applet)
{
	GtkWidget *menu;
	GtkWidget *menuitem;
	
	menu = awn_applet_create_default_menu (applet->applet);
	
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
	applet->config = awn_config_client_new_for_applet ("awn-terminal", NULL);
	
	awn_config_client_notify_add (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, OPACITY, (AwnConfigClientNotifyFunc)load_opacity, applet);
	set_opacity (applet, awn_config_client_get_float (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, OPACITY, NULL));
	
	awn_config_client_notify_add (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, (AwnConfigClientNotifyFunc)load_bg_img, applet);
	set_bg_img (applet, awn_config_client_get_string (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, NULL));
	
	awn_config_client_notify_add (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, HIDE_ON_UNFOCUS, (AwnConfigClientNotifyFunc)load_hide_on_unfocus, applet);
	set_hide_on_unfocus (applet, awn_config_client_get_bool (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, HIDE_ON_UNFOCUS, NULL));
}

static void set_opacity (AwnTerm *applet, gfloat opacity)
{
	gtk_window_set_opacity (GTK_WINDOW (applet->dialog), opacity);
}

void load_opacity (AwnConfigClientNotifyEntry *entry, AwnTerm *applet)
{
	set_opacity (applet, entry->value.float_val);
}

void save_opacity (GtkWidget *scale, AwnConfigClient *config)
{
	awn_config_client_set_float (config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, OPACITY, gtk_range_get_value (GTK_RANGE (scale)), NULL);
}

static void set_bg_img (AwnTerm *applet, gchar *path)
{
	vte_terminal_set_background_image_file (VTE_TERMINAL (applet->terminal), path);
}

void load_bg_img (AwnConfigClientNotifyEntry *entry, AwnTerm *applet)
{
	set_bg_img (applet, entry->value.str_val);
}

void save_bg_img (GtkWidget *fc, AwnConfigClient *config)
{
	awn_config_client_set_string (config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (fc)), NULL);
}

static void set_hide_on_unfocus (AwnTerm *applet, gboolean value)
{
	if (value)
	{
		g_signal_handlers_unblock_by_func(applet->dialog, focus_out_cb, NULL);
	}
	else
	{
		g_signal_handlers_block_by_func(applet->dialog, focus_out_cb, NULL);
	}
}

void load_hide_on_unfocus (AwnConfigClientNotifyEntry *entry, AwnTerm *applet)
{
	set_hide_on_unfocus (applet, entry->value.bool_val);
}

void save_hide_on_unfocus (GtkWidget *check, AwnConfigClient *config)
{
	awn_config_client_set_bool (config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, HIDE_ON_UNFOCUS, gtk_toggle_button_get_active (GTK_TOGGLE_BUTTON (check)), NULL);
}

void save_main_terminal (GtkWidget *entry, AwnConfigClient *config)
{
	awn_config_client_set_string (config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, MAIN_TERMINAL, (gchar*)gtk_entry_get_text (GTK_ENTRY (entry)), NULL);
}

void show_about ()
{
	gtk_show_about_dialog (NULL, "program-name", "Awn Terminal", NULL);
}

void show_settings_window ()
{
	GtkWidget *window;
	GtkWidget *box;
	GtkWidget *main_terminal_box;
	GtkWidget *widget;
	
	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
	
	box = gtk_vbox_new (FALSE, 10);
	gtk_container_add (GTK_CONTAINER (window), box);
	
	widget = gtk_check_button_new_with_label ("Hide On Unfocus");
	g_signal_connect (G_OBJECT (widget), "toggled", G_CALLBACK (save_hide_on_unfocus), applet->config);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (widget), awn_config_client_get_bool (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, HIDE_ON_UNFOCUS, NULL));
	gtk_box_pack_start_defaults (GTK_BOX (box), widget);
	
	widget = gtk_file_chooser_button_new ("Select a file", GTK_FILE_CHOOSER_ACTION_OPEN);
	gtk_file_chooser_set_filename (GTK_FILE_CHOOSER (widget), awn_config_client_get_string (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, NULL));
	g_signal_connect (G_OBJECT (widget), "file-set", G_CALLBACK (save_bg_img), applet->config);
	gtk_box_pack_start_defaults (GTK_BOX (box), widget);
	
	widget = gtk_hscale_new_with_range (0.0, 1.0, 0.1);
	gtk_range_set_value (GTK_RANGE (widget), awn_config_client_get_float (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, OPACITY, NULL));
	g_signal_connect (G_OBJECT (widget), "value-changed", G_CALLBACK (save_opacity), applet->config);
	gtk_box_pack_start_defaults (GTK_BOX (box), widget);
	
	main_terminal_box = gtk_hbox_new (FALSE, 0);
	gtk_box_pack_start_defaults (GTK_BOX (box), main_terminal_box);
	
	widget = gtk_label_new ("Main terminal:");
	gtk_box_pack_start_defaults (GTK_BOX (main_terminal_box), widget);
	
	widget = gtk_entry_new ();
	char *main_terminal = awn_config_client_get_string (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, MAIN_TERMINAL, NULL);
	if (!main_terminal) main_terminal = g_strdup ("gnome-terminal");
	gtk_entry_set_text (GTK_ENTRY (widget), main_terminal);
	g_free (main_terminal);
	g_signal_connect (G_OBJECT (widget), "activate", G_CALLBACK (save_main_terminal), applet->config);
	gtk_box_pack_start_defaults (GTK_BOX (main_terminal_box), widget);
	
	gtk_widget_show_all (window);
}
