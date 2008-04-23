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
//#include <libgnome/libgnome.h>
#include <libgnomevfs/gnome-vfs.h>

#define GKEY_BACKEND "backend"
#define GKEY_BACKEND_TYPE "backend_type"
#define GKEY_TITLE "title"
#define GKEY_BROWSING "browsing"
#define GKEY_COMPOSITE "composite_icon"
#define GKEY_ICON_EMPTY "applet_icon_empty"
#define GKEY_ICON_FULL "applet_icon_full"
#define GKEY_HIDE_VOLUME "hide_volume"
#define GKEY_FILE_OPERATIONS "file_operations"

#define STACKS_APPLET PREFIX "/lib/awn/applets/stacks.desktop"
#define STACKS_APPLET_LOCAL "/usr/local/lib/awn/applets/stacks.desktop"

typedef struct {
  AwnApplet *applet;
  GtkWidget *hbox;
  GtkListStore *store;
} Plugger;

enum
{
  SOCKET_COLUMN,
  VOLUME_COLUMN
};

static GConfClient *client = NULL;
static GnomeVFSVolumeMonitor *monitor = NULL;
static gchar *desktop_path = NULL;

static void
volume_remove(Plugger *app, GnomeVFSVolume *volume)
{
  GtkTreeIter iter;
  gboolean valid = gtk_tree_model_get_iter_first(GTK_TREE_MODEL(app->store), &iter);
  while(valid)
  {
    GtkWidget *socket = NULL;
    GnomeVFSVolume *vol = NULL;
    gtk_tree_model_get(GTK_TREE_MODEL(app->store), &iter,
            SOCKET_COLUMN, &socket, VOLUME_COLUMN, &vol, -1);
    if(g_str_equal(gnome_vfs_volume_get_hal_udi(volume), gnome_vfs_volume_get_hal_udi(vol))){
      gtk_list_store_remove(app->store, &iter);
      if(socket)
        gtk_widget_destroy(socket);
      if(vol)
        gnome_vfs_volume_unref(vol);
      return;
    }
    valid = gtk_tree_model_iter_next(GTK_TREE_MODEL(app->store), &iter);
  }
}

static void
volume_add(Plugger *app, GnomeVFSVolume *volume)
{
  // Get display name based on device type
  GnomeVFSDeviceType type = gnome_vfs_volume_get_device_type(volume);
  GnomeVFSDrive *drive = gnome_vfs_volume_get_drive(volume);
  gchar *name = gnome_vfs_drive_get_display_name(drive);

  // Get mount point or path from device
  gchar *path = gnome_vfs_volume_get_activation_uri(volume);
  if(path == NULL)
        path = gnome_vfs_volume_get_device_path(volume);

  // Get identifier for this device from HAL; use to store gconf settings
  
  gchar *hudi = gnome_vfs_volume_get_hal_udi(volume);
  if (hudi) {
    hudi = g_strrstr (hudi, "/");
    hudi += sizeof(gchar);
  } else {
    hudi = g_strdup_printf ("%lu", gnome_vfs_volume_get_id (volume));
  }

  // Get the appropriate icon for the device type
  gchar *icon = gnome_vfs_volume_get_icon(volume);

  // Store settings in gconf before loading stack applet
  gchar *key;
  gchar *key_prefix = g_strdup_printf("/apps/avant-window-navigator/applets/stacks/%s", hudi);

  // Check if this is a "hidden" (by applet) volume
  key = g_strdup_printf("%s/%s", key_prefix, GKEY_HIDE_VOLUME);
  if(gconf_client_get(client, key, NULL))
    return;

  // Set "required" gconf keys
  gconf_client_set_string(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BACKEND), path, NULL);

  gconf_client_set_int(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BACKEND_TYPE), 2, NULL);

  // Set "user customizable" gconf keys (if not already set)
  key = g_strdup_printf("%s/%s", key_prefix, GKEY_TITLE);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_string(client, key, name, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_BROWSING);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_bool(client, key, TRUE, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_COMPOSITE);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_bool(client, key, FALSE, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_ICON_EMPTY);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_string(client, key, icon, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_ICON_FULL);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_string(client, key, icon, NULL);

  key = g_strdup_printf("%s/%s", key_prefix, GKEY_FILE_OPERATIONS);
  if(!gconf_client_get(client, key, NULL))
    gconf_client_set_int(client, key, 14, NULL);

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
       hudi,
       (long long)gtk_socket_get_id(GTK_SOCKET(socket)),
       awn_applet_get_orientation(app->applet),
       awn_applet_get_height(app->applet));
  g_spawn_command_line_async (exec, NULL);

  // Store the socket and volume in a liststore for later use
  GtkTreeIter iter;
  gtk_tree_model_get_iter_first(GTK_TREE_MODEL(app->store), &iter);
  gtk_list_store_append(app->store, &iter);
  gtk_list_store_set(app->store, &iter, SOCKET_COLUMN, socket, VOLUME_COLUMN, volume, -1);
}

static void
volumes_initialization(GtkWidget *widget, gpointer user_data)
{
  Plugger *app = user_data;

  GtkIconTheme *theme = gtk_icon_theme_get_default();
  GList *drives = gnome_vfs_volume_monitor_get_connected_drives(monitor);
  GList *dlist = NULL;
  for(dlist = drives; dlist != NULL; dlist = g_list_next(dlist)){
    GnomeVFSDrive *drive = dlist->data;
    GList *volumes = gnome_vfs_drive_get_mounted_volumes(drive);
    GList *vlist = NULL;
    for(vlist = volumes; vlist != NULL; vlist = g_list_next(vlist)){
      GnomeVFSVolume *volume = vlist->data;
      if (!gnome_vfs_volume_is_user_visible(volume))
        continue;
      volume_add(app, volume);
    }
    gnome_vfs_drive_volume_list_free(volumes);
    gnome_vfs_drive_unref(drive);
  }
  g_list_free(drives);
}

static void
volume_mounted_cb(  GnomeVFSVolumeMonitor *volume_monitor,
                    GnomeVFSVolume        *volume,
                    gpointer               user_data)
{
  Plugger *app = user_data;
  if(!gnome_vfs_volume_is_user_visible(volume))
    return;
  volume_add(app, volume);
}

static void
volume_unmounted_cb(    GnomeVFSVolumeMonitor *volume_monitor,
                        GnomeVFSVolume        *volume,
                        gpointer               user_data)
{
  volume_remove(user_data, volume);
}

AwnApplet*
awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
  gnome_vfs_init ();
  // Create a new applet and set a reference to the new Plugger
  AwnApplet *applet = awn_applet_new( uid, orient, height );
  Plugger *app = g_new0 (Plugger, 1);
  app->applet = applet;

  // Monitor the vfs volumes and connect to its signals
  monitor = gnome_vfs_get_volume_monitor();
  g_signal_connect(monitor, "volume-unmounted", G_CALLBACK(volume_unmounted_cb), app);
  g_signal_connect(monitor, "volume-mounted", G_CALLBACK(volume_mounted_cb), app);

  // Get a reference to the gconf client
  client = gconf_client_get_default();

  // Create a new store which holds < GtkWidget, GnomeVFSVolume >
  app->store = gtk_list_store_new(2, G_TYPE_OBJECT, G_TYPE_OBJECT);

  // Set the path to the stacks applet
  if(gnome_vfs_uri_exists(gnome_vfs_uri_new(STACKS_APPLET))){
    desktop_path = STACKS_APPLET;
  }else if(gnome_vfs_uri_exists(gnome_vfs_uri_new(STACKS_APPLET_LOCAL))){
    desktop_path = STACKS_APPLET_LOCAL;
  }else{
    g_print("!! Stacks Plugger Error: dependency on Stacks Applet not met:\n \
             !! Could not find stacks.desktop file at:\n \
             !! %s or %s\n", STACKS_APPLET, STACKS_APPLET_LOCAL);
  }

  // Create a box that will hold the stacks applets
  app->hbox = gtk_hbox_new(FALSE, 0);
  gtk_container_add(GTK_CONTAINER(applet), app->hbox);
  gtk_widget_show_all(GTK_WIDGET(applet));

  // We first have to create (return) this applet, before we can add sockets
  g_signal_connect_after(applet, "realize", G_CALLBACK(volumes_initialization), (gpointer)app);

  return applet;
}

