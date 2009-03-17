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

#include <glib.h>
#include <gtk/gtk.h>
#include <gdk/gdkkeysyms.h>
#include <string.h>

#include <libawn/awn-dialog.h>
#include <libawn/awn-applet.h>

#include "affinity.h"

#include "aff-results.h"
#include "aff-sidebar.h"
#include "aff-start.h"
#include "aff-window.h"
#include "tomboykeybinder.h"


static void  affinity_app_class_init       (AffinityAppClass *class);
static void  affinity_app_init             (AffinityApp      *app);

static void on_search_string_changed( GtkEditable *editable, AffinityApp *app );
static gboolean aff_key_press_event (GtkWidget   *widget, GdkEventKey *event, AffinityApp *app);
static gboolean aff_focus_out (GtkWidget *widget, GdkEventFocus *event, AffinityApp *app);
static gboolean aff_leave_notify_event (GtkWidget *widget, GdkEventCrossing *event, AffinityApp *app);
static void aff_global_modifier (char *key, AffinityApp *app);
static gboolean aff_grab_broken (GtkWidget *widget, GdkEvent  *event, AffinityApp *app);
static gboolean aff_window_button_press (GtkWidget *widget, GdkEventButton *event, AffinityApp *app);

G_DEFINE_TYPE (AffinityApp,
			affinity_app,
			G_TYPE_OBJECT);

static GObjectClass *parent_class = NULL;

enum
{
	AFFINITY_SHOWN,
	AFFINITY_HIDDEN,
	LAST_SIGNAL
};

static guint affinity_app_signals[LAST_SIGNAL] = { 0 };

static void
finalize (GObject *object)
{
	AffinityApp *app;

	app = AFFINITY_APP (object);
	
	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(object);
}

static void
affinity_app_class_init (AffinityAppClass *class)
{
	GObjectClass *gobject_class;

	parent_class = g_type_class_peek_parent (class);

	gobject_class = G_OBJECT_CLASS (class);
	gobject_class->finalize = finalize;

	affinity_app_signals[AFFINITY_SHOWN] =
		g_signal_new ("affinity-shown",
			      G_OBJECT_CLASS_TYPE (gobject_class),
			      G_SIGNAL_RUN_LAST,
			      G_STRUCT_OFFSET (AffinityAppClass, affinity_shown),
			      NULL, NULL,
			      g_cclosure_marshal_VOID__VOID,
			      G_TYPE_NONE,
			      0);

	affinity_app_signals[AFFINITY_HIDDEN] =
		g_signal_new ("affinity-hidden",
			      G_OBJECT_CLASS_TYPE (gobject_class),
			      G_SIGNAL_RUN_LAST,
			      G_STRUCT_OFFSET (AffinityAppClass, affinity_hidden),
			      NULL, NULL,
			      g_cclosure_marshal_VOID__VOID,
			      G_TYPE_NONE,
			      0);
}

static void
affinity_app_init (AffinityApp *app)
{

}

AffinityApp *
affinity_app_new (gboolean menu_mode, AwnApplet *applet)
{
	AffinityApp *app;

	app = g_object_new(AFFINITY_TYPE_APP, 
					  NULL);
	GtkWidget *window;
	GtkWidget *main_box, *eb, *hbox, *vbox, *hbx;
	GtkWidget *icon, *entry;
	GtkWidget *scroll1, *treeview, *metabar;
	GtkWidget *start, *sidebar;
	
	tomboy_keybinder_init ();
	
	app->visible = FALSE;
	app->lock_focus = FALSE;
	app->ptr_is_grabbed = FALSE;
	app->kbd_is_grabbed = FALSE;
	app->settings = aff_settings_new ();
	
	tomboy_keybinder_bind (app->settings->key_binding, (TomboyBindkeyHandler)aff_global_modifier, 
								(gpointer)app);

	window = aff_window_new (app, applet);
	app->window = window;
    app->applet = applet;

	//gtk_window_move (GTK_WINDOW (window), app->settings->window_x, app->settings->window_y);
	gtk_window_stick (GTK_WINDOW (app->window));

	g_signal_connect (G_OBJECT (window), "key-press-event",
			 G_CALLBACK (aff_key_press_event), (gpointer)app);
	
	eb = gtk_event_box_new ();
	gtk_event_box_set_above_child (GTK_EVENT_BOX (eb), FALSE);
	gtk_event_box_set_visible_window (GTK_EVENT_BOX (eb), FALSE);
	gtk_container_set_border_width (GTK_CONTAINER (eb), 12);
	gtk_container_add (GTK_CONTAINER (window), eb);
	
	main_box = gtk_vbox_new (FALSE, 12);
	gtk_container_add (GTK_CONTAINER (eb), main_box);
	
	hbox = gtk_hbox_new (FALSE, 6);
	gtk_box_pack_start (GTK_BOX (main_box), hbox, FALSE, FALSE, 0);
	
	icon = gtk_image_new_from_icon_name ("search", GTK_ICON_SIZE_SMALL_TOOLBAR);
	app->icon = icon;
	gtk_box_pack_start (GTK_BOX (hbox), icon, FALSE, FALSE, 0);
	
	entry = gtk_entry_new ();
	app->entry = entry;
	gtk_entry_set_has_frame (GTK_ENTRY (entry), FALSE);
	gtk_entry_set_inner_border (GTK_ENTRY (entry), NULL);
	gtk_box_pack_start (GTK_BOX (hbox), entry, TRUE, TRUE, 0);
	
	g_signal_connect (G_OBJECT (entry), "changed",
			  G_CALLBACK (on_search_string_changed), (gpointer)app);
				  
	/*spinner = aff_spinner_new ();
	app->spinner = spinner;
	gtk_box_pack_start (GTK_BOX (hbox), spinner, FALSE, FALSE, 0); */	

	hbox = gtk_hbox_new (FALSE,6);
	gtk_box_pack_start (GTK_BOX (main_box), hbox, TRUE, TRUE, 0);

	/*Start Box*/
	hbx = gtk_hbox_new (FALSE, 6);
	app->start_box = hbx;
	gtk_box_pack_start (GTK_BOX (hbox), hbx, TRUE, TRUE, 0);
	
	start = aff_start_new (app);
	app->start = start;
	gtk_box_pack_start (GTK_BOX (hbx), start, TRUE, TRUE, 0);
	
	gtk_widget_show_all (eb);	 
	
	/* Results Box */
	hbx = gtk_hbox_new (FALSE, 6);
	app->results_box = hbx;
	gtk_box_pack_start (GTK_BOX (hbox), hbx, TRUE, TRUE, 0);
	
	vbox = gtk_vbox_new (FALSE, 8);
	gtk_box_pack_start (GTK_BOX (hbx), vbox, TRUE, TRUE, 0);

	scroll1 = gtk_scrolled_window_new (NULL, NULL);
	gtk_box_pack_end (GTK_BOX (vbox), scroll1, TRUE, TRUE, 0);
	app->scroll = scroll1;
	gtk_scrolled_window_set_policy (GTK_SCROLLED_WINDOW (scroll1),GTK_POLICY_AUTOMATIC,GTK_POLICY_AUTOMATIC);
	
	gtk_scrolled_window_set_shadow_type (GTK_SCROLLED_WINDOW (scroll1), GTK_SHADOW_NONE);  
	
	treeview = aff_results_new (app);
	app->treeview = treeview;
	gtk_container_add (GTK_CONTAINER (scroll1), treeview);
	/*
	metabar = aff_metabar_new (app);
	app->metabar = metabar;
	gtk_box_pack_start (GTK_BOX (hbx), metabar, FALSE, TRUE, 0);
	
	g_signal_connect (G_OBJECT (treeview), "cursor-changed",
			  G_CALLBACK (aff_metabar_cursor_changed), (gpointer)app);	
	*/

	sidebar = aff_sidebar_new (app);
	gtk_widget_show_all (sidebar);	
	app->sidebar = sidebar;
	gtk_box_pack_start (GTK_BOX (hbox), sidebar, FALSE, TRUE, 0);
	
	on_search_string_changed (NULL, app);
	
	g_signal_connect (G_OBJECT (app->window), "grab-broken-event",
			  G_CALLBACK (aff_grab_broken), (gpointer)app);
	
	g_signal_connect (G_OBJECT (app->window), "button-press-event",
			  G_CALLBACK (aff_window_button_press), (gpointer)app);	

	g_signal_connect (G_OBJECT (app->window), "focus-out-event",
			  G_CALLBACK (aff_focus_out), (gpointer)app);				  		  

	g_signal_connect (G_OBJECT (app->treeview), "focus-out-event",
			  G_CALLBACK (aff_focus_out), (gpointer)app);		

	return app;
}
static gboolean
aff_window_button_press (GtkWidget *widget, GdkEventButton *event, AffinityApp *app)
{
	GdkWindow *ptr_window;
	
	ptr_window = gdk_window_at_pointer (NULL, NULL);

	if (app->window->window != ptr_window) {
		affinity_app_hide (app);

		return TRUE;
	}

	return FALSE;
}

static void
grab_pointer_and_keyboard (AffinityApp *app, gboolean grab)
{
	GdkGrabStatus status;

	guint time = GDK_CURRENT_TIME;

	if (grab) {
		gtk_widget_grab_focus (app->window);
		gtk_grab_add          (app->window);

		status = gdk_pointer_grab (
			app->window->window, TRUE, GDK_BUTTON_PRESS_MASK,
			NULL, NULL, time);

		app->ptr_is_grabbed = (status == GDK_GRAB_SUCCESS);

		status = gdk_keyboard_grab (app->window->window, TRUE, time);

		app->kbd_is_grabbed = (status == GDK_GRAB_SUCCESS);
	}
	else {
		if (app->ptr_is_grabbed) {
			gdk_pointer_ungrab (time);
			app->ptr_is_grabbed = FALSE;
		}

		if (app->kbd_is_grabbed) {
			gdk_keyboard_ungrab (time);
			app->kbd_is_grabbed = FALSE;
		}

		gtk_grab_remove (app->window);
	}
}

static 
gboolean aff_grab_broken (GtkWidget *widget, GdkEvent  *event, AffinityApp *app)
{
	grab_pointer_and_keyboard (app, FALSE);
}

static void
aff_global_modifier (char *key, AffinityApp *app)
{
	if (app->visible) {
		affinity_app_hide (app);
	} else {
		affinity_app_show (app);
	}
}

void 
affinity_app_show (AffinityApp *app)
{
    gint ax, ay, aw, ah;
    gint x, y, w, h;

    AwnConfigClient *client = awn_config_client_new ();
    gint offset = awn_config_client_get_int (client, "bar", "icon_offset", NULL);

    gdk_window_get_origin (GTK_WIDGET (app->applet)->window, &ax, &ay);
    gtk_widget_get_size_request (GTK_WIDGET (app->applet), &aw, &ah);
    gtk_window_get_size (GTK_WINDOW (app->window), &w, &h);
        
    x = ax - w/2 + aw/2;
    y = ay - h + offset;
         
    if (x < 0)
         x = 2;
 
    if ((x+w) > gdk_screen_get_width (gdk_screen_get_default()))
         x = gdk_screen_get_width (gdk_screen_get_default ()) - w -20;

    gtk_window_move (GTK_WINDOW (app->window), x, y);

	gtk_window_set_focus_on_map (GTK_WINDOW (app->window), TRUE);
	gtk_window_present (GTK_WINDOW (app->window));

	gtk_widget_grab_focus (app->entry);
		
	grab_pointer_and_keyboard (app, TRUE);	
	app->visible = TRUE;
	
	g_signal_emit (G_OBJECT (app), affinity_app_signals[AFFINITY_SHOWN], 0,NULL);	
}

void 
affinity_app_hide (AffinityApp *app)
{
	gtk_widget_hide (app->window);
	grab_pointer_and_keyboard (app, FALSE);
	
	app->visible = FALSE;
	g_signal_emit (G_OBJECT (app), affinity_app_signals[AFFINITY_HIDDEN], 0 ,NULL);	
}

void 
affinity_app_close (AffinityApp *app)
{
	tomboy_keybinder_unbind (app->settings->key_binding, (TomboyBindkeyHandler)aff_global_modifier);
}

static gboolean 
aff_leave_notify_event (GtkWidget *widget, GdkEventCrossing *event, AffinityApp *app)
{
	gint x, y, w, h;
	gtk_window_get_position (GTK_WINDOW (app->window), &x, &y);
	gtk_window_get_size (GTK_WINDOW (app->window), &w, &h);
		
	gint x_root, y_root;
	gtk_widget_get_pointer (app->window, &x_root, &y_root);
	
	
	gint real_x = x_root + x;
	gint real_y = y_root + y;
	
	if ((real_x > x) && (real_x < (x+w))) {
		
		if ((real_y > y) && (real_y < (y+h))) 
			return;
	}
	
	affinity_app_hide (app);
	app->visible = FALSE;
}

static gboolean            
aff_focus_out (GtkWidget *widget, GdkEventFocus *event, AffinityApp *app)
{
	gint x, y, w, h;
	gtk_window_get_position (GTK_WINDOW (app->window), &x, &y);
	gtk_window_get_size (GTK_WINDOW (app->window), &w, &h);
		
	gint x_root, y_root;
	gtk_widget_get_pointer (app->window, &x_root, &y_root);
	
	
	gint real_x = x_root + x;
	gint real_y = y_root + y;
	
	if ((real_x > x) && (real_x < (x+w))) {
		
		if ((real_y > y) && (real_y < (y+h))) 
			return;
	}
	
	affinity_app_hide (app);
}

static gboolean 
aff_key_press_event (GtkWidget   *widget, GdkEventKey *event, AffinityApp *app)
{
	switch (event->keyval) {
		case GDK_Escape:
			gtk_widget_hide (app->window);
			app->visible = FALSE;
			break;
		
		case GDK_l:
			if ((event->state & GDK_CONTROL_MASK) > 0)
				gtk_widget_grab_focus (app->entry);
			break;
		default:
			break;
	}
	return FALSE;
}

typedef struct {
	AffinityApp *app;
	gchar *query;
} AffTypingTerm;

static gboolean
_check_typing (AffTypingTerm *term)
{
	const gchar *text = gtk_entry_get_text (GTK_ENTRY (term->app->entry));
	if (strcmp (text, term->query) == 0) {
		aff_results_set_search_string (AFF_RESULTS (term->app->treeview), text);
                gtk_widget_hide (GTK_WIDGET (term->app->start_box));
                gtk_widget_show_all (GTK_WIDGET (term->app->results_box));
                term->app->searching = TRUE;
		g_print ("Searching : %s\n", text);
	}
	g_free (term->query);
	g_free (term);
	return FALSE;
}

static void
on_search_string_changed( GtkEditable *editable, AffinityApp *app )
{
        AffTypingTerm *term = g_new (AffTypingTerm, 1);
        const char *text = gtk_entry_get_text (GTK_ENTRY (app->entry));
        term->app = app;
        term->query = g_strdup (text);
        size_t len = strlen(text);
        switch (len) {
                case 0:
                        gtk_widget_hide (GTK_WIDGET (app->results_box));
                        gtk_widget_show_all (GTK_WIDGET (app->start_box));
                        app->searching = FALSE;
                        g_free (term->query);
                        g_free (term);
                        break;
                default:
			g_timeout_add (500, (GSourceFunc)_check_typing, (gpointer)term);
			break;
        }
        gtk_widget_queue_draw (app->window);
}
				

