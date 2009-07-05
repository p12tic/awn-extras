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
#include <glib/gi18n.h>
#include <math.h>

#include "awnterm.h"
#include "settings.h"

// See settings.h for a semi-logical explanation of what each function does.
// If gtk wasn't such a backwards system then we could get rid of most of them.
// GnuStep is both the past and the future. Unfortunately, it's not the present. ;)

static void set_opacity (AwnTerm *applet, gfloat opacity);
static void set_bg_img (AwnTerm *applet, gchar *path);
static void set_hide_on_unfocus (AwnTerm *applet, gboolean value);

static gchar*
format_value_callback (GtkScale *scale,
                       gdouble   value)
{
  return g_strdup_printf ("%d%%",
                          (int)rint(value*100.0));
}

GtkWidget* create_popup_menu (AwnTerm *applet)
{
	GtkWidget *menu;
	GtkWidget *menuitem;
	
	menu = awn_applet_create_default_menu (applet->applet);
	
	menuitem = gtk_image_menu_item_new_from_stock (GTK_STOCK_PREFERENCES, NULL);
	gtk_menu_shell_append (GTK_MENU_SHELL (menu), menuitem);
	g_signal_connect (G_OBJECT (menuitem), "activate", G_CALLBACK (show_settings_window), NULL);
	gtk_widget_show (menuitem);

  const gchar **authors[] = { "Natan Yellin (aantn)", NULL };

  menuitem = awn_applet_create_about_item(applet->applet,
                                          "Copyright 2007, 2008, 2009 Natan Yellin",
                                          AWN_APPLET_LICENSE_GPLV2,
                                          NULL,
                                          _("A simple popup terminal"),
                                          "http://wiki.awn-project.org/AWN_Terminal_Applet",
                                          "wiki.awn-project.org",
                                          "terminal",
                                          _("translator-credits"),
                                          authors,
                                          NULL, NULL);
	gtk_menu_shell_append (GTK_MENU_SHELL (menu), menuitem);
	gtk_widget_show (menuitem);
	
	
	return menu;
}

void init_settings (AwnTerm *applet)
{
	gfloat opacity = 1.0;
	applet->config = awn_config_client_new_for_applet ("awnterm", NULL);
	
	awn_config_client_notify_add (applet->config, 
		AWN_CONFIG_CLIENT_DEFAULT_GROUP,
		OPACITY,
		(AwnConfigClientNotifyFunc)load_opacity,
		applet);
	if (awn_config_client_entry_exists (applet->config,
			AWN_CONFIG_CLIENT_DEFAULT_GROUP, OPACITY))
		opacity = awn_config_client_get_float (applet->config,
				AWN_CONFIG_CLIENT_DEFAULT_GROUP,
				OPACITY,
				NULL);
	set_opacity (applet, opacity);
	
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
	GtkWidget *terminal;
	int i;

	for(i = 0; i <= applet->number_of_tabs; i++)
	{
		terminal = gtk_notebook_get_nth_page(GTK_NOTEBOOK(applet->notebook), i);
		if (VTE_IS_TERMINAL(terminal))
			vte_terminal_set_background_image_file (VTE_TERMINAL (terminal), path);
	}
}

void load_bg_img (AwnConfigClientNotifyEntry *entry, AwnTerm *applet)
{
	set_bg_img (applet, entry->value.str_val);
}

void save_bg_img (GtkWidget *fc, AwnConfigClient *config)
{
	awn_config_client_set_string (config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, gtk_file_chooser_get_filename (GTK_FILE_CHOOSER (fc)), NULL);
}

/* update_preview_cb copied completely from gtk documentation */
static void
update_preview_cb (GtkFileChooser *file_chooser, gpointer data)
{
  GtkWidget *preview;
  char *filename;
  GdkPixbuf *pixbuf;
  gboolean have_preview;
  preview = GTK_WIDGET (data);
  filename = gtk_file_chooser_get_preview_filename (file_chooser);
  pixbuf = gdk_pixbuf_new_from_file_at_size (filename, 128, 128, NULL);
  have_preview = (pixbuf != NULL);
  g_free (filename);
  gtk_image_set_from_pixbuf (GTK_IMAGE (preview), pixbuf);
  if (pixbuf)
    g_object_unref (pixbuf);
  gtk_file_chooser_set_preview_widget_active (file_chooser, have_preview);
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

static gboolean save_main_terminal (GtkWidget *entry,
								GdkEventFocus *event,
								AwnConfigClient *config)
{
	awn_config_client_set_string (config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, MAIN_TERMINAL, (gchar*)gtk_entry_get_text (GTK_ENTRY (entry)), NULL);

	return FALSE;
}

static void
clear_bg(GtkButton *button, GtkWidget *chooser)
{
	gtk_file_chooser_set_filename(GTK_FILE_CHOOSER(chooser), "");

	/* I don't think there is a signal to connect to a change by the above
	 * function, so save the non-image manually. */
	awn_config_client_set_string (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, "", NULL);
}

void show_settings_window ()
{
	GtkWidget *window, *box, *section_box, *widget, *widget2, *align, *box2;
	gchar *ext_term;
	gdouble val;

	window = gtk_window_new (GTK_WINDOW_TOPLEVEL);
	gtk_window_set_title (GTK_WINDOW (window), _("Preferences"));
	gtk_window_set_default_icon_name ("terminal");
	gtk_container_set_border_width (GTK_CONTAINER (window), 6);

	box = gtk_vbox_new (FALSE, 6);
	gtk_container_add (GTK_CONTAINER (window), box);

	widget = gtk_check_button_new_with_label (_("Hide when focus is lost"));
	g_signal_connect (G_OBJECT (widget), "toggled", G_CALLBACK (save_hide_on_unfocus), applet->config);
	gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (widget), awn_config_client_get_bool (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, HIDE_ON_UNFOCUS, NULL));
	gtk_box_pack_start (GTK_BOX (box), widget, FALSE, FALSE, 0);

	section_box = gtk_vbox_new (FALSE, 0);
	gtk_box_pack_start(GTK_BOX(box), section_box, FALSE, FALSE, 0);

	widget = gtk_label_new ("");
	gtk_label_set_markup(GTK_LABEL(widget),
						 g_strdup_printf("<b>%s</b>", _("Background image")));
	gtk_misc_set_alignment(GTK_MISC(widget), 0.0, 0.5);
	gtk_box_pack_start(GTK_BOX(section_box), widget, FALSE, FALSE, 0);

	align = gtk_alignment_new(0.5, 0.5, 1.0, 0.0);
	gtk_alignment_set_padding(GTK_ALIGNMENT(align), 0, 0, 10, 0);
	gtk_box_pack_start(GTK_BOX(section_box), align, FALSE, FALSE, 0);

	box2 = gtk_hbox_new(FALSE, 3);
	gtk_container_add(GTK_CONTAINER(align), box2);

	widget2 = gtk_image_new();

	widget = gtk_file_chooser_button_new (_("Select a file"), GTK_FILE_CHOOSER_ACTION_OPEN);
	gtk_file_chooser_set_filename (GTK_FILE_CHOOSER (widget), awn_config_client_get_string (applet->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, BG_IMG, NULL));
	gtk_file_chooser_set_preview_widget (GTK_FILE_CHOOSER(widget), widget2);
	gtk_widget_set_size_request(widget, 200, -1);
	g_signal_connect (G_OBJECT (widget), "file-set", G_CALLBACK (save_bg_img), applet->config);
	g_signal_connect (widget, "update-preview", G_CALLBACK (update_preview_cb), widget2);

	gtk_box_pack_start(GTK_BOX(box2), widget, TRUE, TRUE, 0);

	widget2 = gtk_button_new_from_stock(GTK_STOCK_CLEAR);
	g_signal_connect(G_OBJECT(widget2), "clicked", G_CALLBACK(clear_bg), (gpointer)widget);
	gtk_box_pack_start(GTK_BOX(box2), widget2, FALSE, FALSE, 0);

	section_box = gtk_vbox_new(FALSE, 0);
	gtk_box_pack_start(GTK_BOX(box), section_box, FALSE, FALSE, 0);

	widget = gtk_label_new ("");
	gtk_label_set_markup(GTK_LABEL(widget),
						 g_strdup_printf("<b>%s</b>", _("Terminal Opacity")));
	gtk_misc_set_alignment(GTK_MISC(widget), 0.0, 0.5);
	gtk_box_pack_start(GTK_BOX(section_box), widget, FALSE, FALSE, 3);

	align = gtk_alignment_new(0.5, 0.5, 1.0, 0.0);
	gtk_alignment_set_padding(GTK_ALIGNMENT(align), 0, 0, 10, 0);
	gtk_box_pack_start(GTK_BOX(section_box), align, FALSE, FALSE, 0);

	val = awn_config_client_get_float (applet->config,
									   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
									   OPACITY, NULL);

	widget = gtk_hscale_new_with_range (0.1, 1.0, 0.1);
	gtk_range_set_value (GTK_RANGE (widget), val);
	g_signal_connect (G_OBJECT (widget), "value-changed",
					  G_CALLBACK (save_opacity), applet->config);
	g_signal_connect (G_OBJECT (widget), "format-value",
					  G_CALLBACK (format_value_callback), NULL);
	gtk_container_add(GTK_CONTAINER(align), widget);

	section_box = gtk_vbox_new(FALSE, 0);
	gtk_box_pack_start(GTK_BOX(box), section_box, FALSE, FALSE, 0);

	widget = gtk_label_new ("");
	gtk_label_set_markup(GTK_LABEL(widget),
						 g_strdup_printf("<b>%s</b>", _("External Terminal")));
	gtk_misc_set_alignment(GTK_MISC(widget), 0.0, 0.5);
	gtk_box_pack_start(GTK_BOX(section_box), widget, FALSE, FALSE, 0);

	align = gtk_alignment_new(0.5, 0.5, 1.0, 0.0);
	gtk_alignment_set_padding(GTK_ALIGNMENT(align), 0, 0, 10, 0);
	gtk_box_pack_start(GTK_BOX(section_box), align, FALSE, FALSE, 0);

	ext_term = awn_config_client_get_string (applet->config,
											 AWN_CONFIG_CLIENT_DEFAULT_GROUP,
											 MAIN_TERMINAL, NULL);
	if (!ext_term) ext_term = g_strdup ("gnome-terminal");

	widget = gtk_entry_new ();
	gtk_entry_set_text (GTK_ENTRY (widget), ext_term);
	g_signal_connect (G_OBJECT (widget), "focus-out-event",
					  G_CALLBACK (save_main_terminal), applet->config);
	gtk_container_add(GTK_CONTAINER(align), widget);

	box2 = gtk_hbutton_box_new();
	gtk_button_box_set_layout(GTK_BUTTON_BOX(box2), GTK_BUTTONBOX_END);
	gtk_box_pack_end(GTK_BOX(box), box2, FALSE, FALSE, 0);

	widget = gtk_button_new_from_stock(GTK_STOCK_CLOSE);
	gtk_box_pack_start(GTK_BOX(box2), widget, FALSE, FALSE, 0);
	g_signal_connect_swapped(G_OBJECT(widget), "clicked", G_CALLBACK(gtk_widget_destroy), window);

	widget = gtk_hseparator_new ();
	gtk_box_pack_end(GTK_BOX(box), widget, FALSE, FALSE, 3);

	g_free (ext_term);

	gtk_widget_show_all (window);
}
