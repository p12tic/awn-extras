/*
 * Copyright (c) 2007 Timon D. ter Braak
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
#include <gconf/gconf-client.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-plug.h>
#include <libgnome/libgnome.h>
#include <libgnomevfs/gnome-vfs.h>

#define GKEY_BACKEND "backend"
#define GKEY_BACKEND_TYPE "backend_type"
#define GKEY_FILE_OPERATIONS "file_operations"
#define GKEY_BROWSING "browsing"
#define GKEY_COMPOSITE "composite_icon"
#define GKEY_ICON_EMPTY "applet_icon_empty"
#define GKEY_ICON_FULL "applet_icon_full"

#define STACKS_APPLET "/usr/lib/awn/applets/stacks.desktop"
#define STACKS_APPLET_LOCAL "/usr/local/lib/awn/applets/stacks.desktop"

typedef struct {
  AwnApplet *applet;
  GtkWidget *hbox;
} Trasher;

static GConfClient *client = NULL;
static gchar *desktop_path = NULL;
static gchar *key_prefix = "/apps/avant-window-navigator/applets/stacks/trasher";

static void
trasher_initialization(GtkWidget *widget, gpointer user_data)
{
  Trasher *app = user_data;
  gchar *key = NULL;

  // Set "required" gconf keys
  gconf_client_set_string(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BACKEND), "trash:", NULL);

  gconf_client_set_int(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BACKEND_TYPE), 3, NULL);

  // Only "allow" file operation "Move"
  gconf_client_set_int(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_FILE_OPERATIONS), 4, NULL);

  // Set "user customizable" gconf keys (if not already set)
  key = g_strdup_printf("%s/%s", key_prefix, GKEY_BROWSING);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_bool(client, key, TRUE, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_COMPOSITE);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_bool(client, key, FALSE, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_ICON_EMPTY);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_string(client, key, "gnome-stock-trash", NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_ICON_FULL);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_string(client, key, "gnome-stock-trash-full", NULL);

  gconf_client_suggest_sync(client, NULL);

  // Create a new socket and add it to this applet
  GtkWidget *socket = gtk_socket_new();
  gtk_widget_show(socket);
  gtk_container_add(GTK_CONTAINER(app->hbox), socket);
  gtk_widget_realize(socket);

  // Execute the stack applet. All settings should be set now.
  gchar *exec = g_strdup_printf(
       "awn-applet-activation -p %s -u %s -w %lld -o %d -h %d",
       desktop_path,
       "trasher",
       (long long)gtk_socket_get_id(GTK_SOCKET(socket)),
       awn_applet_get_orientation(app->applet),
       awn_applet_get_height(app->applet));
  g_spawn_command_line_async (exec, NULL);
}

AwnApplet*
awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
  // Create a new applet and set a reference to the new Trasher
  AwnApplet *applet = awn_applet_new( uid, orient, height );
  Trasher *app = g_new0(Trasher, 1);
  app->applet = applet;

  // Get a reference to the gconf client
  client = gconf_client_get_default();

  // Set the path to the stacks applet
  if(gnome_vfs_uri_exists(gnome_vfs_uri_new(STACKS_APPLET))){
    desktop_path = STACKS_APPLET;
  }else if(gnome_vfs_uri_exists(gnome_vfs_uri_new(STACKS_APPLET_LOCAL))){
    desktop_path = STACKS_APPLET_LOCAL;
  }else{
    g_print("!! Stacks Trasher Error: dependency on Stacks Applet not met:\n \
             !! Could not find stacks.desktop file at:\n \
             !! %s or %s\n", STACKS_APPLET, STACKS_APPLET_LOCAL);
  }

  // Create a box that will hold the stacks applets
  app->hbox = gtk_hbox_new(FALSE, 0);
  gtk_container_add(GTK_CONTAINER(applet), app->hbox);
  gtk_widget_show_all(GTK_WIDGET(applet));

  // We first have to create (return) this applet, before we can add sockets
  g_signal_connect_after(applet, "realize", G_CALLBACK(trasher_initialization), (gpointer)app);
  return applet;
}

