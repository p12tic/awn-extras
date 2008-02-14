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
#include <glib/gi18n.h>
#include <gtk/gtk.h>
#include <gdk/gdkkeysyms.h>
#include <string.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>

#include "affinity.h"

//#include "aff-metabar.h"
#include "aff-results.h"
#include "aff-sidebar.h"
#include "aff-start.h"
#include "aff-window.h"
#include "tomboykeybinder.h"

static AffinityApp *app;

static void affinity_toggle (GtkWidget *widget, GdkEventButton *event, AffinityApp *app);

AwnApplet*
awn_applet_factory_initp (const gchar* uid, gint orient, gint height )
{
    AwnApplet *applet;
    GdkPixbuf *icon;

    applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));

    icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (), "search", height -2, 0, NULL);
    awn_applet_simple_set_icon (AWN_APPLET_SIMPLE (applet), icon);

    app = affinity_app_new( TRUE, applet);
    affinity_app_hide(app);
    g_signal_connect(G_OBJECT(applet), "button-press-event",
            G_CALLBACK(affinity_toggle), (gpointer)app);
    return applet;
}

static void 
affinity_toggle (GtkWidget *widget, GdkEventButton *event, AffinityApp *app)
{
	if (app->visible){
		affinity_app_hide (app);
	}else{
		affinity_app_show (app);
    }
}

