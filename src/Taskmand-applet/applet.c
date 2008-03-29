/*
 * Copyright (C)  2008 Rodney Cryderman <rcryderman@gmail.com>
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
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
*/


#include <gtk/gtk.h>
#include <libawn/awn-applet-simple.h>
#include "client-bindings.h"

#define HEARTBEAT_INTERVAL  1

gboolean do_dbus_stuff(const char * uid)
{

    /* Somewhere in the code, we want to execute EchoString remote method */
    DBusGProxy *proxy;
    DBusGConnection *connection;
    GError *error = NULL;
    
    connection = dbus_g_bus_get (DBUS_BUS_SESSION, &error);
    if (connection == NULL)
    {
        g_warning("Unable to connect to dbus: %sn", error->message);
        g_error_free (error);
        /* Basically here, there is a problem, since there is no dbus :) */
        return;
    }

    /* This won't trigger activation! */
    proxy = dbus_g_proxy_new_for_name (connection,
            "org.awnproject.taskmand",
            "/org/awnproject/taskmand",
            "org.awnproject.taskmand");
    /* The method call will trigger activation, more on that later */
    if (!org_awnproject_taskmand_launcher__position(proxy, uid, &error))
    {
        /* Method failed, the GError is set, let's warn everyone */
        g_warning ("Woops remote method failed: %s", error->message);
        g_error_free (error);
        return;
    }

    /* Cleanup */ 
    g_object_unref (proxy);

    /* The DBusGConnection should never be unreffed, it lives once and is shared amongst the process */
    return TRUE;
}

static void _realized(GtkWidget *widget,AwnApplet *applet)
{
    GdkPixbuf *icon;
    
    icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,2,2);
    gdk_pixbuf_fill(icon,0x00000000);
    gtk_widget_set_size_request (GTK_WIDGET (applet),2,2);
    awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),icon);    
}

AwnApplet* awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
	GdkPixbuf *icon;
    
    AwnApplet *applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
    icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,height-2,height-2);
    gdk_pixbuf_fill(icon,0x11881133);
    gtk_widget_set_size_request (GTK_WIDGET (applet),height-2,height-2);
    awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),icon);
    g_signal_connect_after(G_OBJECT (applet), "realize", G_CALLBACK (_realized), applet);    
    do_dbus_stuff(uid);
    g_timeout_add_seconds(HEARTBEAT_INTERVAL,do_dbus_stuff,g_strdup(uid));    
    return applet;
}

