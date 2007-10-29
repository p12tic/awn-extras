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
#define GKEY_BROWSING "browsing"
#define GKEY_COMPOSITE "composite_icon"
#define GKEY_ICON_EMPTY "applet_icon_empty"
#define GKEY_ICON_FULL "applet_icon_full"

#define STACKS_APPLET "/usr/lib/awn/applets/stacks.desktop"
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

static void
volume_add(Plugger *app, GnomeVFSVolume *volume)
{
  GtkTreeIter iter;
  GnomeVFSDeviceType type = gnome_vfs_volume_get_device_type(volume);
  gchar *name = gnome_vfs_volume_get_display_name(volume);
  gchar *icon = gnome_vfs_volume_get_icon(volume);
  gchar *path = gnome_vfs_volume_get_activation_uri(volume);
  if(path == NULL)
        path = gnome_vfs_volume_get_device_path(volume);
  gchar *hudi = g_strrstr(gnome_vfs_volume_get_hal_udi(volume), "/");
  hudi += sizeof(gchar);

  gchar *key_prefix = g_strdup_printf("/apps/avant-window-navigator/applets/%s", hudi);
  gconf_client_set_string(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BACKEND), path, NULL);
  gconf_client_set_int(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BACKEND_TYPE), 1, NULL);
  gconf_client_set_bool(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_BROWSING), TRUE, NULL);
  gconf_client_set_bool(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_COMPOSITE), FALSE, NULL);
  gconf_client_set_string(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_ICON_EMPTY), icon, NULL);
  gconf_client_set_string(client,
          g_strdup_printf("%s/%s", key_prefix, GKEY_ICON_FULL), icon, NULL);
  gconf_client_suggest_sync(client, NULL);

  GtkWidget *socket = gtk_socket_new();
  gtk_widget_show(socket);
  gtk_container_add(GTK_CONTAINER(app->hbox), socket);
  gtk_widget_realize(socket);

  gchar *desktop_path;
  if(gnome_vfs_uri_exists(gnome_vfs_uri_new(STACKS_APPLET))){
    desktop_path = STACKS_APPLET;
  }else{
    desktop_path = STACKS_APPLET_LOCAL;
  }

  gchar *exec = g_strdup_printf(
       "awn-applet-activation -p %s -u %s -w %lld -o %d -h %d",
       desktop_path,
       hudi,
       (long long)gtk_socket_get_id(GTK_SOCKET(socket)),
       awn_applet_get_orientation(app->applet),
       awn_applet_get_height(app->applet));
  g_spawn_command_line_async (exec, NULL);

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
  Plugger *app = user_data;
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
        gtk_widget_destroy(socket);
        gnome_vfs_volume_unref(vol);
        return;
    }
    valid = gtk_tree_model_iter_next(GTK_TREE_MODEL(app->store), &iter);
  }
}

static void
drive_disconnected_cb(  GnomeVFSVolumeMonitor *volume_monitor,
                        GnomeVFSDrive *drive,
                        gpointer user_data)
{
  g_print("Drive disconnected\n");
}

AwnApplet*
awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
  AwnApplet *applet = awn_applet_new( uid, orient, height );
  Plugger *app = g_new0 (Plugger, 1);
  app->applet = applet;

  if(!monitor)
    monitor = gnome_vfs_get_volume_monitor();
    g_signal_connect(monitor, "volume-unmounted", G_CALLBACK(volume_unmounted_cb), app);
    g_signal_connect(monitor, "volume-mounted", G_CALLBACK(volume_mounted_cb), app);
    g_signal_connect(monitor, "drive-disconnected", G_CALLBACK(drive_disconnected_cb), app);

  if(!client)
    client = gconf_client_get_default();

  app->hbox = gtk_hbox_new(FALSE, 0);
  gtk_container_add(GTK_CONTAINER(applet), app->hbox);

  app->store = gtk_list_store_new(2, G_TYPE_OBJECT, G_TYPE_OBJECT);

  gtk_widget_show_all(GTK_WIDGET(applet));
  g_signal_connect_after(applet, "realize", G_CALLBACK(volumes_initialization), (gpointer)app);

  return applet;
}

