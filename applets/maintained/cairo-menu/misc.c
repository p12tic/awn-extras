#include "misc.h"


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
