

#include "misc.h"
#include "cairo-menu-item.h"
#include "cairo-menu.h"
#include <glib/gi18n.h>
#include <libdesktop-agnostic/gtk.h>
#include <libdesktop-agnostic/vfs.h>


DesktopAgnosticFDODesktopEntry *
get_desktop_entry (gchar * desktop_file)
{
  DesktopAgnosticVFSFile *file;
  DesktopAgnosticFDODesktopEntry *entry;
  GError * error = NULL;
  file = desktop_agnostic_vfs_file_new_for_path (desktop_file, &error);
  if (error)
  {
    g_critical ("Error when trying to load the launcher: %s", error->message);
    g_error_free (error);
    return;
  }

  if (file == NULL || !desktop_agnostic_vfs_file_exists (file))
  {
    if (file)
    {
      g_object_unref (file);
    }
    g_critical ("File not found: '%s'", desktop_file);
    return;
  }

  entry = desktop_agnostic_fdo_desktop_entry_new_for_file (file, &error);

  g_object_unref (file);
  if (error)
  {
    g_critical ("Error when trying to load the launcher: %s", error->message);
    g_error_free (error);
    return;
  }
  return entry;
}

void
_launch (GtkMenuItem *menu_item,gchar * desktop_file)
{
  DesktopAgnosticFDODesktopEntry *entry;
  GError * error = NULL;
  
  entry = get_desktop_entry (desktop_file);
  
  if (entry == NULL)
  {
    return;
  }

  if (!desktop_agnostic_fdo_desktop_entry_key_exists (entry,"Exec"))
  {
    return;
  }

  desktop_agnostic_fdo_desktop_entry_launch (entry,0, NULL, &error);
  if (error)
  {
    g_critical ("Error when launching: %s", error->message);
    g_error_free (error);
  }

  g_object_unref (entry);
}

GtkWidget *
get_gtk_image (gchar * icon_name)
{
  GtkWidget *image = NULL;
  GdkPixbuf *pbuf;  
  gint width,height;

  if (icon_name)
  {
    gtk_icon_size_lookup (GTK_ICON_SIZE_MENU,&width,&height);
    /*TODO Need to listen for icon theme changes*/

    if ( gtk_icon_theme_has_icon (gtk_icon_theme_get_default(),icon_name) )
    {
      image = gtk_image_new_from_icon_name (icon_name,width);
    }
    
    if (!image)
    {
      if (!pbuf)
      {
        pbuf = gdk_pixbuf_new_from_file_at_scale (icon_name,
                                         -1,
                                         height,
                                         TRUE,
                                         NULL);
      }
      
      if (!pbuf)
      {
        if ( gtk_icon_theme_has_icon (gtk_icon_theme_get_default(),"stock_folder") )
        {
          image = gtk_image_new_from_icon_name ("stock_folder",width);
        }
      }      
      else
      {
        image = gtk_image_new_from_pixbuf (pbuf);
        g_object_unref (pbuf);        
      }
    }
  }
  return image;
}

static void 
_fillin_connected(DesktopAgnosticVFSVolume *volume,CairoMenu *menu)
{
  GtkWidget *item;
  DesktopAgnosticVFSFile *uri;
  const gchar *uri_str;
  GtkWidget * image;
  
  g_message("Attempting to add %s...", desktop_agnostic_vfs_volume_get_name(volume));

  /* don't use g_return_if_fail because it runs g_critical */
  if (!desktop_agnostic_vfs_volume_is_mounted(volume))
  {
    return;
  }

  item = cairo_menu_item_new();
  
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),desktop_agnostic_vfs_volume_get_name(volume));
  image = get_gtk_image ( desktop_agnostic_vfs_volume_get_icon(volume));
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
  
//  uri = desktop_agnostic_vfs_volume_get_uri(volume);
//  uri_str = desktop_agnostic_vfs_file_get_uri(uri);
//  item->exec = g_strdup_printf("%s %s", places->file_manager, uri_str);
//  g_object_unref(uri);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
}


GtkWidget * 
get_places_menu (void)
{
  static DesktopAgnosticVFSVolumeMonitor* vol_monitor = NULL;
  static DesktopAgnosticVFSGtkBookmarks *bookmarks_parser = NULL;  
  GtkWidget *menu = cairo_menu_new();
  GtkWidget *item = NULL;
  GError *error = NULL;
  GtkWidget * image;
  const gchar *desktop_dir = g_get_user_special_dir (G_USER_DIRECTORY_DESKTOP);
  const gchar *homedir = g_get_home_dir();

  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("Home"));
  image = get_gtk_image ("stock_home");  
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
//  item->exec = g_strdup_printf("%s %s", file_manager, homedir);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
  
  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("Desktop"));
/*if desktop_dir then use that otherwise use homedir*/
  image = get_gtk_image ("desktop");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }  
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);

  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("File System"));
  image = get_gtk_image ("system");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }  
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);

  if (!vol_monitor)
  {
    /*this is structured like this because get_places() is
    invoked any time there is a change in places... only want perform
    these actions once.*/
    vol_monitor = desktop_agnostic_vfs_volume_monitor_get_default(&error);
    if (error)
    {
      g_critical("Could not get the volume monitor: %s", error->message);
      g_error_free(error);
      return;
    }
    else if (!vol_monitor)
    {
      g_critical("Could not get the volume monitor.");
      return;
    }
//    g_signal_connect(vol_monitor, "volume-mounted", G_CALLBACK(_vfs_changed), menu);
//    g_signal_connect(vol_monitor, "volume-unmounted", G_CALLBACK(_vfs_changed), menu);

    bookmarks_parser = desktop_agnostic_vfs_gtk_bookmarks_new (NULL, TRUE);
//    g_signal_connect (G_OBJECT (bookmarks_parser), "changed",
//                      G_CALLBACK (_on_bookmarks_changed), menu);
  }

  GList *volumes = desktop_agnostic_vfs_volume_monitor_get_volumes(vol_monitor);

  if (volumes)
  {
    g_message("Number of volumes: %d", g_list_length(volumes));
    g_list_foreach(volumes, (GFunc)_fillin_connected, menu);
  }

  g_list_free (volumes);
  // bookmarks
  GSList *bookmarks;
  GSList *node;

  bookmarks = desktop_agnostic_vfs_gtk_bookmarks_get_bookmarks (bookmarks_parser);
  for (node = bookmarks; node != NULL; node = node->next)
  {
    DesktopAgnosticVFSBookmark *bookmark;
    DesktopAgnosticVFSFile *b_file;
    const gchar *b_alias;
    gchar *b_path;
    gchar *shell_quoted = NULL;

    item = cairo_menu_item_new ();
    bookmark = (DesktopAgnosticVFSBookmark*)node->data;
    b_file = desktop_agnostic_vfs_bookmark_get_file (bookmark);
    b_alias = desktop_agnostic_vfs_bookmark_get_alias (bookmark);
    b_path = desktop_agnostic_vfs_file_get_path (b_file);

    image = get_gtk_image ("stock_folder");    
    if (image)
    {
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
    }  
    
    if (b_path)
    {
      shell_quoted = g_shell_quote (b_path);
//      item->exec = g_strdup_printf("%s %s", places->file_manager, shell_quoted);
//      item->comment = desktop_agnostic_vfs_file_get_uri (b_file);
      g_free (shell_quoted);

      if (b_alias)
      {
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),b_alias);
      }
      else
      {
        gchar * base = g_path_get_basename (b_path);
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),base);
        g_free (base);
      }
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    }
    else
    {
      g_free (item);
    }
    g_free (b_path);
  }
  return menu;
}
