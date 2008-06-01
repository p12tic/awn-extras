/* -*- Mode: C; tab-width: 2; indent-tabs-mode: t; c-basic-offset: 2 -*- */
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
#include <libawn-extras/awn-extras.h>

#include "affinity.h"

//#include "aff-metabar.h"
#include "aff-results.h"
#include "aff-sidebar.h"
#include "aff-start.h"
#include "aff-window.h"
#include "tomboykeybinder.h"

static AffinityApp *app;

static gboolean affinity_toggle (GtkWidget *widget, GdkEventButton *event, AffinityApp *app);
static gboolean affinity_right_click (GtkWidget *widget, GdkEventButton *event, AwnApplet *app);


AwnApplet*
awn_applet_factory_initp (const gchar* uid, gint orient, gint height )
{
    AwnApplet *applet;
    GdkPixbuf *icon;

    applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));

    icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (), "search", height -2, 0, NULL);
    //gtk_icon_theme_load_icon () doesn't always give us a properly sized icon
    if (icon)
    {
      int difference=gdk_pixbuf_get_height (icon) - (height-2);
      difference=ABS(difference);
      if ( difference > (height-2)*0.1 )  //within 10%?
      {
	g_warning("gtk_icon_theme_load_icon() failed to scale icon\n");
	icon=gdk_pixbuf_scale_simple(icon,height-2,height-2,GDK_INTERP_HYPER);
      }
    }
    if (!icon)//failsafe
    {
      icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,height-2,height-2);
      gdk_pixbuf_fill(icon,0x11881133);     
    }    
    awn_applet_simple_set_icon (AWN_APPLET_SIMPLE (applet), icon);	
    app = affinity_app_new( TRUE, applet);
    affinity_app_hide(app);
    g_signal_connect(G_OBJECT(applet), "button-press-event",
            G_CALLBACK(affinity_toggle), (gpointer)app);
    g_signal_connect(G_OBJECT(applet), "button-press-event",
            G_CALLBACK(affinity_right_click), (gpointer)applet);
	
    return applet;
}

static gboolean 
affinity_toggle (GtkWidget *widget, GdkEventButton *event, AffinityApp *app)
{
  if (event->button == 1)
  {	
		if (app->visible){
			affinity_app_hide (app);
		}else{
			affinity_app_show (app);
		}
  }
	return FALSE;
}

static gboolean  
affinity_right_click (GtkWidget *widget, GdkEventButton *event, AwnApplet *app)
{
  if (event->button == 3)
  {
	    static GtkWidget * menu=NULL;
			GtkWidget * item=NULL;
			if (!menu)
			{
    		menu = awn_applet_create_default_menu (AWN_APPLET(app));
				//using a string here instead of APPLET_NAME which is defined in aff-settings.c
				//don't feel like determining how it is being used in said file...
				item = shared_menuitem_create_applet_prefs("affinity",NULL);
				if (item) //generic preferences is enabled
				{
				  gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);          
				}        				
			}
      gtk_menu_set_screen(GTK_MENU(menu), NULL);		
  		gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL,event->button, event->time);			
	}
	return FALSE;	
}
