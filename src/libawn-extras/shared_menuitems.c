/*
 * Copyright (C) 2008 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */

#include <gtk/gtk.h>
#include "awn-extras.h"

typedef struct
{
  gchar * instance;
  gchar * base;
  gchar * applet_name;
} PrefsLocation;  

static gboolean 
_start_applet_prefs(GtkMenuItem *menuitem,PrefsLocation  * prefs_location)
{ 
  GError *err = NULL;
  gchar * editor = "gconf-editor";  //temporary...
  gchar * folder = "/apps/avant-window-navigator/applets/"; //temporary
  gchar * cmdline;
  cmdline = g_strdup_printf("%s %s%s", editor, folder, prefs_location->instance);
  g_printf("1) launching... %s\n", cmdline);
  g_spawn_command_line_async(cmdline, &err);//FIXME
  if (err)
  {
    g_warning("Failed to launch applet preferences dialog (%s): %s\n", cmdline, err->message);
    g_error_free(err);
  }
  g_free(cmdline);
  
  if (prefs_location->base)
  {
    cmdline = g_strdup_printf("%s %s%s", editor, folder, prefs_location->base);
    g_printf("2) launching... %s\n", cmdline);    
    g_spawn_command_line_async(cmdline, &err);//FIXME
    if (err)
    {
      g_warning("Failed to launch applet preferences dialog (%s): %s\n", cmdline, err->message);
      g_error_free(err);
    }
    g_free(cmdline);    
  }
  return TRUE;
}


static gboolean
_cleanup_applet_prefs_item(GtkWidget *widget, GdkEvent *event,
                           PrefsLocation  * prefs_location)
{
  g_free(prefs_location->instance);  
  g_free(prefs_location->base);
  g_free(prefs_location->applet_name);
  g_free(prefs_location);
  return FALSE;
}

/**
 * awn_applet_create_preferences:
 *
 * @instance: The folder name containing the configuration key within the
 * applets configuration folder.
 * @baseconf: If there is a default configuration location that is different
 * than the instance provided.  Otherwise %NULL.
 * @applet_name: applet name used to reference the associated schema-ini
 *
 * Create a menu item that invokes a generic applet preferences dialog.
 * Notes:
 * * There is no need to attach the returned item to a signal, as this is
 *   handled by the function.
 *
 * Returns: A #GtkMenuItem or %NULL if the generic applet preferences
 * configuration is disabled.
 *
 */
GtkWidget *
awn_applet_create_preferences (gchar *instance,
                               gchar *baseconf,
                               gchar *applet_name)
{
  g_return_val_if_fail(instance,NULL);
  g_return_val_if_fail(applet_name,NULL);

  GtkWidget * item = NULL;
  gchar * keysdir_copy = NULL;
  PrefsLocation  * prefs_location = g_malloc(sizeof(PrefsLocation));

  prefs_location->instance = g_strdup(instance);
  prefs_location->base = baseconf?g_strdup(baseconf):NULL;
  prefs_location->applet_name = g_strdup(applet_name);
  if (share_config_bool(SHR_KEY_GENERIC_PREFS))
  {
    item = gtk_image_menu_item_new_with_label("Applet Preferences");
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),
          gtk_image_new_from_stock (GTK_STOCK_PREFERENCES,GTK_ICON_SIZE_MENU));
    gtk_widget_show_all(item);
    g_signal_connect(G_OBJECT(item), "activate",
                     G_CALLBACK(_start_applet_prefs), prefs_location);
    g_signal_connect(G_OBJECT(item), "destroy-event",
                     G_CALLBACK(_cleanup_applet_prefs_item), prefs_location);
  }
  else
  {
      g_warning("Generic Preferences Requested but support is not enabled in configuration\n");
  }

  return item;
}

