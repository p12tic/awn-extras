/*
 * Copyright (C) 2007, 2008, 2009 Rodney Cryderman <rcryderman@gmail.com>
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

#include "misc.h"
#include <glib/gi18n.h>
#include <gdk/gdkx.h>
#include <gtk/gtk.h>
#include <libdesktop-agnostic/vfs.h>
#include <sys/types.h>
#include <unistd.h>

#include "cairo-menu-applet.h"

#if !GTK_CHECK_VERSION(2,14,0)
#define GTK_ICON_LOOKUP_FORCE_SIZE 0
#endif


static GtkWidget * _get_recent_menu (GtkWidget * menu);

void
_free_callback_container (CallbackContainer * c)
{  
  /* yeah... this is a bit peculiar and needs to be changed */
  g_free(c->display_name);
  g_free(c->file_path);
  g_free(c->icon_name);
  g_free(c);
}

static void 
_create_icon (GtkButton *widget,CallbackContainer * c)
{
  gtk_widget_hide (c->instance->menu);
  gtk_menu_popdown (GTK_MENU(c->context_menu));
  c->instance->add_icon_fn (c->instance->applet,c->file_path,c->display_name,c->icon_name);
}

gboolean 
_button_press_dir (GtkWidget *menu_item, GdkEventButton *event, CallbackContainer * c)
{
  GtkWidget * popup;
  GtkWidget * item; 
  switch (event->button)
  {
    case 3:
      popup = gtk_menu_new ();
      item = gtk_menu_item_new_with_label ("Create icon");
      gtk_menu_shell_append(GTK_MENU_SHELL(popup), item);
      c->context_menu = popup;
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_create_icon), c);
      gtk_widget_show_all (popup);
      gtk_menu_popup(GTK_MENU(popup), NULL, NULL, NULL, NULL, event->button, event->time);
      break;
    default:
      break;
  }
}


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
    return NULL;
  }

  if (file == NULL || !desktop_agnostic_vfs_file_exists (file))
  {
    if (file)
    {
      g_object_unref (file);
    }
    g_critical ("File not found: '%s'", desktop_file);
    return NULL;
  }

  entry = desktop_agnostic_fdo_desktop_entry_new_for_file (file, &error);

  g_object_unref (file);
  if (error)
  {
    g_critical ("Error when trying to load the launcher: %s", error->message);
    g_error_free (error);
    return NULL;
  }
  return entry;
}

/*
 FIXME
 activate works much nicer as it doesn't fire if the item was dragged and dropped.
 But i need event->time*/
void
_launch (GtkWidget *widget,GdkEventButton *event,gchar * desktop_file)
{
  DesktopAgnosticFDODesktopEntry *entry;
  GError * error = NULL;
  gboolean startup_set = FALSE;
  
  entry = get_desktop_entry (desktop_file);
  
  if (entry == NULL)
  {
    return;
  }

  if (!desktop_agnostic_fdo_desktop_entry_key_exists (entry,"Exec"))
  {
    return;
  }

  /*
   An incredibly hackish way to detect that we had a drag and drop
   */
  if ( ! lround (event->x) && !lround (event->y) && !lround (event->x_root) && !lround (event->y_root) )
  {
    return;
  }

  if (desktop_agnostic_fdo_desktop_entry_key_exists (entry,G_KEY_FILE_DESKTOP_KEY_STARTUP_NOTIFY))
  {
    GStrv tokens1;
    GStrv tokens2;
    gchar * screen_name = NULL;
    gchar * id = g_strdup_printf("cairo_menu_%u_TIME%u",getpid(),event->time);
    gchar * display_name = gdk_screen_make_display_name (gdk_screen_get_default());
    gchar * name = desktop_agnostic_fdo_desktop_entry_get_name (entry);

    tokens1 = g_strsplit (display_name,":",2);
    if (tokens1 && tokens1[1])
    {
      tokens2 = g_strsplit(tokens1[1],".",2);
      g_strfreev (tokens1);
      if (tokens2 && tokens2[1])
      {
        screen_name = g_strdup (tokens2[1]);
        g_strfreev (tokens2);
      }
      else
      {
        if (tokens2)
        {
          g_strfreev (tokens2);
          screen_name = g_strdup ("0");          
        }
      }
    }
    else
    {
      if (tokens1)
      {
        g_strfreev (tokens1);
      }
      screen_name = g_strdup ("0");
    }
    
    gdk_x11_display_broadcast_startup_message (gdk_display_get_default(),
                                               "new",
                                               "ID",id,
                                               "NAME",name,
                                               "SCREEN",screen_name,
                                               NULL);
    g_setenv ("DESKTOP_STARTUP_ID",id,TRUE);
    startup_set = TRUE;
    g_free (id);
    g_free (name);
    g_free (screen_name);
  }
  
  desktop_agnostic_fdo_desktop_entry_launch (entry,0, NULL, &error);
  if (startup_set)
  {
    g_unsetenv ("DESKTOP_STARTUP_ID");
  }
  
  if (error)
  {
    g_critical ("Error when launching: %s", error->message);
    g_error_free (error);
  }

  g_object_unref (entry);
}

GtkWidget *
get_gtk_image (const gchar const * icon_name)
{
  GtkWidget *image = NULL;
  GdkPixbuf *pbuf = NULL;  
  gint width,height;
  
  if (icon_name)
  {
    gtk_icon_size_lookup (GTK_ICON_SIZE_MENU,&width,&height);
    /*TODO Need to listen for icon theme changes*/
    if ( gtk_icon_theme_has_icon (gtk_icon_theme_get_default(),icon_name) )
    {
      pbuf = gtk_icon_theme_load_icon (gtk_icon_theme_get_default(),
                                       icon_name,
                                       height,
                                       GTK_ICON_LOOKUP_FORCE_SIZE,
                                       NULL);
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
    }
    if (pbuf && GDK_IS_PIXBUF (pbuf)&&gdk_pixbuf_get_width(pbuf) > width)
    {
      GdkPixbuf *scaled;
      height = height * ( (gdouble)width / gdk_pixbuf_get_width(pbuf) );
      scaled = gdk_pixbuf_scale_simple (pbuf,
                                        width,
                                        height,
                                        GDK_INTERP_BILINEAR);
      g_object_unref (pbuf);
      pbuf = scaled;
    }
    
    if (pbuf && GDK_IS_PIXBUF (pbuf))
    {
      image = gtk_image_new_from_pixbuf (pbuf);
      g_object_unref (pbuf);        
    }      
  }
  return image;
}

void
_exec (GtkMenuItem *menuitem,gchar * cmd)
{
  g_spawn_command_line_async (cmd,NULL);
}

void
_remove_menu_item  (GtkWidget *menu_item,GtkWidget * menu)
{
  gtk_container_remove (GTK_CONTAINER(menu),menu_item);
}


static void
_remove_get_recent ( gpointer data,   GObject *where_the_object_was)
{
  GtkRecentManager *recent = gtk_recent_manager_get_default ();  
  guint id = GPOINTER_TO_UINT (data);
  g_signal_handler_disconnect (recent,id);
}

static void
_purge_recent (GtkMenuItem *menuitem, GtkRecentManager *recent)
{
  g_message ("%s: Purged %d items from Recent Documents",__func__,
             gtk_recent_manager_purge_items (recent,NULL));
  
}

/*
 Updates the recent menu.
 This is also called by signal handler when there are updates to the 
 recent docs 
 */
static GtkWidget * 
_get_recent_menu (GtkWidget * menu)
{  
  g_return_val_if_fail (GTK_IS_MENU(menu),NULL);
  static gboolean done_once = FALSE;
  GtkRecentManager *recent = gtk_recent_manager_get_default ();
  GtkWidget * menu_item;
  GtkWidget * image = NULL;  
  GList * recent_list;
  GList * iter;
  gint width,height;
  guint id;

  gtk_container_foreach (GTK_CONTAINER (menu),(GtkCallback)_remove_menu_item,menu);  
  gtk_icon_size_lookup (GTK_ICON_SIZE_MENU,&width,&height);
  recent_list = gtk_recent_manager_get_items (recent);
  if (recent_list)
  {
    for (iter = recent_list; iter; iter = iter->next)
    {
      if (gtk_recent_info_get_age(iter->data) <=2)
      {
        gchar * app_name = gtk_recent_info_last_application (iter->data);
        GdkPixbuf * pbuf = NULL;
        const gchar * app_exec=NULL;
        guint count;
        time_t time_;
        const gchar * txt = gtk_recent_info_get_display_name (iter->data);
        menu_item = cairo_menu_item_new_with_label (txt);

        pbuf = gtk_recent_info_get_icon (iter->data,height);
        if (pbuf)
        {
          image = gtk_image_new_from_pixbuf (pbuf);
          g_object_unref (pbuf);
        }
        if (image)
        {
          gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);          
        }
        if (gtk_recent_info_get_application_info (iter->data,app_name,
#if GTK_CHECK_VERSION(2,16,0)
                                                         &app_exec,
#else
                                                         (gchar**)&app_exec,
#endif
                                                         &count,
                                                         &time_))
        {
          gchar * exec = g_strdup_printf ("%s %s",app_exec,
                                          gtk_recent_info_get_uri (iter->data));
          g_signal_connect(G_OBJECT(menu_item), "activate", G_CALLBACK(_exec), exec);
          g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify) g_free,exec);          
        }
        gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
        g_free (app_name);
      }
    }
  }
  menu_item = cairo_menu_item_new_with_label (_("Clear Recent Documents"));
  image = get_gtk_image ("gtk-clear");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);          
  }
  g_signal_connect(G_OBJECT(menu_item), "activate", G_CALLBACK(_purge_recent),recent);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);  
  
  g_list_foreach (recent_list, (GFunc)gtk_recent_info_unref,NULL);
  g_list_free (recent_list);
  gtk_widget_show_all (menu); 

  done_once = TRUE;
  return menu;
}

/*
 Returns a new recent menu widget every time it is called
 */
GtkWidget * 
get_recent_menu (void)
{
  guint id;
  GtkRecentManager *recent = gtk_recent_manager_get_default ();
  
  GtkWidget *menu = cairo_menu_new();
  g_signal_handlers_disconnect_by_func (recent,G_CALLBACK(_get_recent_menu),menu);  
  _get_recent_menu (menu);
  id = g_signal_connect_swapped (recent,"changed",G_CALLBACK(_get_recent_menu),menu);
  g_object_weak_ref (G_OBJECT(menu),(GWeakNotify)_remove_get_recent,GUINT_TO_POINTER(id));                   
  return menu;
}

/*
 Prepares data for use by menu_build
 */
MenuInstance *
get_menu_instance ( AwnApplet * applet,
                                  GetRunCmdFunc run_cmd_fn,
                                  GetSearchCmdFunc search_cmd_fn,
                                  AddIconFunc add_icon_fn,
                                  CheckMenuHiddenFunc check_menu_hidden_fn,
                                  gchar * submenu_name,
                                  gint flags)
{
  MenuInstance *instance = g_malloc (sizeof (MenuInstance));
  instance->applet = applet;
  instance->run_cmd_fn = run_cmd_fn;
  instance->search_cmd_fn = search_cmd_fn;
  instance->add_icon_fn = add_icon_fn;
  instance->check_menu_hidden_fn = check_menu_hidden_fn;
  instance->flags = flags;
  instance->done_once = FALSE;
  instance->places=NULL;
  instance->recent=NULL;
  instance->menu = NULL; 
  instance->submenu_name = g_strdup(submenu_name);
  return instance;
}

