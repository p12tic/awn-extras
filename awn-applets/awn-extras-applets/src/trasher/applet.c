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
#define GKEY_TRASH_DIRS "trash_dirs"
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

enum
{
  ADD_VOLUME,
  DEL_VOLUME
};

static GConfClient *client = NULL;
static GnomeVFSVolumeMonitor *monitor = NULL;
static gchar *desktop_path = NULL;
static gchar *key_prefix = "/apps/avant-window-navigator/applets/trasher";

static void
volume_sync_with_gconf(GnomeVFSAsyncHandle *handle, GList *results, gpointer data){

  gchar *key = g_strdup_printf("%s/%s", key_prefix, GKEY_TRASH_DIRS);
  GSList *list = gconf_client_get_list(client, key, GCONF_VALUE_STRING, NULL);
  GSList *entry;
  GList *element;

  for (element = results; element != NULL; element = element->next) {
    GnomeVFSFindDirectoryResult *result_item = (GnomeVFSFindDirectoryResult *)element->data;

    if (result_item->result == GNOME_VFS_OK) {
      for(entry = list; entry != NULL; entry = entry->next){
        GnomeVFSURI *data_uri = gnome_vfs_uri_new((gchar *)entry->data);
        if (gnome_vfs_uri_equal(data_uri, result_item->uri)){
          list = g_slist_delete_link(list, entry);
        }
      }
      if(GPOINTER_TO_INT(data) == ADD_VOLUME){
        list = g_slist_prepend(list,
            gnome_vfs_uri_to_string(result_item->uri, GNOME_VFS_URI_HIDE_PASSWORD));
      }
    }
  }
  gconf_client_set_list(client, key, GCONF_VALUE_STRING, list, NULL);
  g_slist_free(list);
}

static void
volume_find_trash(GnomeVFSVolume *volume, gint operation)
{
  if (!gnome_vfs_volume_handles_trash(volume))
    return;

  /* get the mount point for this volume */
  gchar *uri_str = gnome_vfs_volume_get_activation_uri (volume);
  GnomeVFSURI *mount_uri = gnome_vfs_uri_new (uri_str);
  GnomeVFSURI *trash_uri = NULL;
  g_free (uri_str);

  if(mount_uri != NULL){
    GnomeVFSAsyncHandle *handle;
    GList *near_uri_list = NULL;
    near_uri_list = g_list_append(near_uri_list, mount_uri);
    gnome_vfs_async_find_directory(
        &handle,
        near_uri_list,
        GNOME_VFS_DIRECTORY_KIND_TRASH,
        FALSE, TRUE, 0777,
        GNOME_VFS_PRIORITY_DEFAULT,
        volume_sync_with_gconf,
        GINT_TO_POINTER(operation));
    gnome_vfs_uri_unref (mount_uri);
  }
 
}

static void
volumes_initialization(GtkWidget *widget, gpointer user_data)
{
  Trasher *app = user_data;

  gchar *key = g_strdup_printf("%s/%s", key_prefix, GKEY_TRASH_DIRS);
  gconf_client_unset(client, key, NULL);

  GList *volumes = gnome_vfs_volume_monitor_get_mounted_volumes(monitor);
  GList *vlist = NULL;
  for(vlist = volumes; vlist != NULL; vlist = g_list_next(vlist)){
    GnomeVFSVolume *volume = vlist->data;
    volume_find_trash(volume, ADD_VOLUME);
  }
  g_list_free(volumes);

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

static void
volume_mounted_cb(  GnomeVFSVolumeMonitor *volume_monitor,
                    GnomeVFSVolume        *volume,
                    gpointer               user_data)
{
  volume_find_trash(volume, ADD_VOLUME);
}

static void
volume_pre_unmount_cb(  GnomeVFSVolumeMonitor *volume_monitor,
                        GnomeVFSVolume        *volume,
                        gpointer               user_data)
{
  volume_find_trash(volume, DEL_VOLUME);
}

AwnApplet*
awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
  // Create a new applet and set a reference to the new Trasher
  AwnApplet *applet = awn_applet_new( uid, orient, height );
  Trasher *app = g_new0(Trasher, 1);
  app->applet = applet;

  // Monitor the vfs volumes and connect to its signals
  monitor = gnome_vfs_get_volume_monitor();
  g_signal_connect(monitor, "volume-pre-unmount", G_CALLBACK(volume_pre_unmount_cb), app);
  g_signal_connect(monitor, "volume-mounted", G_CALLBACK(volume_mounted_cb), app);

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
  g_signal_connect_after(applet, "realize", G_CALLBACK(volumes_initialization), (gpointer)app);
  return applet;
}

