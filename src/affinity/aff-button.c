/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*- */
/*
 * Copyright (C) 2007 Neil J. Patel <njpatel@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * Authors: Neil J. Patel <njpatel@gmail.com>
 *
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <gtk/gtk.h>
#include <stdio.h>
#include <string.h>

#if !GTK_CHECK_VERSION(2,9,0)
#include <X11/Xlib.h>
#include <X11/extensions/shape.h>
#include <gdk/gdkx.h>
#endif

#include <libawn/awn-desktop-item.h>

#include "aff-button.h"
#include "aff-settings.h"
#include "aff-window.h"

#define AFF_BUTTON_GET_PRIVATE(obj) (G_TYPE_INSTANCE_GET_PRIVATE ((obj), AFF_TYPE_BUTTON, AffButtonPrivate))

#define M_PI		3.14159265358979323846 

G_DEFINE_TYPE (AffButton, aff_button, GTK_TYPE_BUTTON);
/* STRUCTS & ENUMS */
struct _AffButtonPrivate
{
	AffinityApp *app;

        GtkWidget *label;
        GtkWidget *hbox;
        
        gchar *text;
        gchar *uri;
        gchar *command;
        
};

/* FORWARDS */

static void aff_button_class_init (AffButtonClass *klass);
static void aff_button_init (AffButton *button);
static void aff_button_finalize (GObject *obj);
static gboolean aff_button_expose_event(GtkWidget *widget, GdkEventExpose *event);

static void aff_button_clicked (GtkButton *button);

static GtkButtonClass *parent_class;


/* CALLBACKS */
static void 
aff_button_clicked (GtkButton *button)
{
	AffButtonPrivate *priv;
	priv = AFF_BUTTON_GET_PRIVATE (button);
	
	GdkScreen *screen;
	gchar *command;
	
	if (priv->uri){ 
		char *res = NULL;
		res = strstr (priv->uri, ".desktop");
		if (res) {
			AwnDesktopItem *item = awn_desktop_item_new (priv->uri);
			
			if (item) {
				if (awn_desktop_item_exists (item)) {
					awn_desktop_item_launch (item, NULL, NULL);
					gtk_widget_hide (priv->app->window);
					priv->app->visible = FALSE;
				}
				awn_desktop_item_free (item);
				return;
			}	
			
		} else {
			command = g_strdup_printf ("%s %s", priv->app->settings->open_uri, priv->uri);
		}	
		
	} else if (priv->command) {
		command = g_strdup (priv->command);
	} else {
		return;
	}
	
	screen = gdk_screen_get_default ();
	gdk_spawn_command_line_on_screen (screen, command, NULL);
	g_free (command);

	affinity_app_hide (priv->app);
}

static gboolean 
aff_button_expose_event(GtkWidget *widget, GdkEventExpose *event)
{
	AffButtonPrivate *priv;
	priv = AFF_BUTTON_GET_PRIVATE (widget);
	
	gtk_container_propagate_expose (GTK_CONTAINER (widget),
                                        priv->hbox,
                                        event);	
	return TRUE;
}

/* AFF_BUTTON_NEW */
static void
aff_button_class_init(AffButtonClass *klass)
{
	GObjectClass *gobject_class;
	GtkWidgetClass *widget_class;
	parent_class = g_type_class_peek_parent(klass);

	gobject_class = G_OBJECT_CLASS(klass);
	g_type_class_add_private (gobject_class, sizeof (AffButtonPrivate));
	gobject_class->finalize = aff_button_finalize;
	
	widget_class = GTK_WIDGET_CLASS (klass);     
	widget_class->expose_event = aff_button_expose_event;
}

static void
aff_button_init(AffButton *button)
{
	AffButtonPrivate *priv;
	priv = AFF_BUTTON_GET_PRIVATE (button);

	priv->text = NULL;
	priv->uri = NULL;
	priv->command = NULL;
	gtk_widget_set_app_paintable (GTK_WIDGET(button), TRUE);
}	

static void
aff_button_finalize(GObject *obj)
{
	AffButton *button;
	AffButtonPrivate *priv;
	
	g_return_if_fail(obj != NULL);
	g_return_if_fail(AFF_IS_BUTTON(obj));

	button = AFF_BUTTON(obj);
	priv = AFF_BUTTON_GET_PRIVATE (button);

	g_free (priv->text);
	g_free (priv->uri);
	g_free (priv->command);	
		
	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(obj);
}

GtkWidget *
aff_button_new(AffinityApp *app, GtkImage *image, const char *text, const char *uri)
{
	AffButtonPrivate *priv;
	AffSettings *s;
	GtkWidget *label;
	GtkWidget *hbox;
	gchar *markup;
	
	GtkWidget *button = g_object_new(AFF_TYPE_BUTTON, 
					 NULL);
	priv = AFF_BUTTON_GET_PRIVATE (button);					 
	priv->app = app;
	s = app->settings;
	
	priv->text = g_strdup (text);
	priv->uri = g_strdup (uri);
	
	hbox = gtk_hbox_new (FALSE, 10);
	priv->hbox = hbox;
	gtk_container_add (GTK_CONTAINER (button), hbox);
	
	gtk_box_pack_start (GTK_BOX (hbox), GTK_WIDGET (image), FALSE, TRUE, 0);
	
	label = gtk_label_new (" ");
	priv->label = label;
	gtk_label_set_ellipsize (GTK_LABEL (label), PANGO_ELLIPSIZE_END);
	gtk_box_pack_start (GTK_BOX (hbox), label, TRUE, TRUE, 0);
	
	markup = g_strdup_printf ("<span foreground='%s'>%s</span>", s->text_color, text);
		
	gtk_label_set_markup (GTK_LABEL (label), markup);
	g_free (markup);
	
	gtk_misc_set_alignment (GTK_MISC (label), 0.0, 0.5);
	
	
	gtk_widget_show_all (button);
	
	gtk_button_set_relief (GTK_BUTTON (button), GTK_RELIEF_NONE);

	g_signal_connect (G_OBJECT (button), "clicked",
			  G_CALLBACK (aff_button_clicked), NULL);	

	g_signal_connect (G_OBJECT (button), "enter",
			  G_CALLBACK (aff_window_enter_button), (gpointer)app->window);
	g_signal_connect (G_OBJECT (button), "leave",
			  G_CALLBACK (aff_window_leave_button), (gpointer)app->window);	
	g_signal_connect (G_OBJECT (button), "focus-in-event",
			  G_CALLBACK (aff_window_focus_in_button), (gpointer)app->window);
	g_signal_connect (G_OBJECT (button), "focus-out-event",
			  G_CALLBACK (aff_window_focus_out_button), (gpointer)app->window);			  		  			  		
	return GTK_WIDGET(button);
}

GtkWidget *
aff_button_new_with_command(AffinityApp *app, GtkImage *image, const char *text, const char *command)
{
	AffButtonPrivate *priv;
	AffSettings *s;
	GtkWidget *label;
	GtkWidget *hbox;
	gchar *markup;
	
	GtkWidget *button = g_object_new(AFF_TYPE_BUTTON, 
					 NULL);
	priv = AFF_BUTTON_GET_PRIVATE (button);					 
	priv->app = app;
	s = app->settings;
	
	priv->text = g_strdup (text);
	priv->command = g_strdup (command);
	
	hbox = gtk_hbox_new (FALSE, 10);
	priv->hbox = hbox;
	gtk_container_add (GTK_CONTAINER (button), hbox);
	
	gtk_box_pack_start (GTK_BOX (hbox), GTK_WIDGET (image), FALSE, TRUE, 0);
	
	label = gtk_label_new (" ");
	priv->label = label;
	//gtk_label_set_ellipsize (GTK_LABEL (label), PANGO_ELLIPSIZE_END);
	gtk_box_pack_start (GTK_BOX (hbox), label, TRUE, TRUE, 0);
	
	markup = g_strdup_printf ("<span foreground='%s'>%s</span>", s->text_color, text);
	gtk_label_set_markup (GTK_LABEL (label), markup);
	g_free (markup);
	
	gtk_misc_set_alignment (GTK_MISC (label), 0.0, 0.5);
	
	
	gtk_widget_show_all (button);
	
	gtk_button_set_relief (GTK_BUTTON (button), GTK_RELIEF_NONE);

	g_signal_connect (G_OBJECT (button), "clicked",
			  G_CALLBACK (aff_button_clicked), NULL);
	g_signal_connect (G_OBJECT (button), "enter",
			  G_CALLBACK (aff_window_enter_button), (gpointer)app->window);
	g_signal_connect (G_OBJECT (button), "leave",
			  G_CALLBACK (aff_window_leave_button), (gpointer)app->window);	
	g_signal_connect (G_OBJECT (button), "focus-in-event",
			  G_CALLBACK (aff_window_focus_in_button), (gpointer)app->window);
	g_signal_connect (G_OBJECT (button), "focus-out-event",
			  G_CALLBACK (aff_window_focus_out_button), (gpointer)app->window);		
	  			  			
	return GTK_WIDGET(button);
}

