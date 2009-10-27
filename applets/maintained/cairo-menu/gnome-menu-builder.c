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

#include "config.h"

#include "gnome-menu-builder.h"

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>
#include <glib/gi18n.h>
#include <libdesktop-agnostic/fdo.h>
#include <gio/gio.h>

#include <libawn/libawn.h>
#include "cairo-menu.h"
#include "cairo-menu-item.h"
#include "misc.h"
#include "cairo-menu-applet.h"

GMenuTree *  main_menu_tree = NULL;
GMenuTree *  settings_menu_tree = NULL;    

GtkWidget *  menu_build (MenuInstance * instance);

static GtkWidget *
get_image_from_gicon (GIcon * gicon)
{
  const gchar *const * icon_names =NULL;
  GtkWidget * image = NULL;
  if (G_IS_THEMED_ICON (gicon))
  {
    icon_names = g_themed_icon_get_names (G_THEMED_ICON(gicon));
  }
  if (icon_names)
  {
    const gchar *const *i;
    for (i=icon_names; *i; i++)
    {
      image = get_gtk_image (*i);
      if (image)
      {
        break;
      }
    }
  }
  return image;
}

static gboolean
add_special_item (GtkWidget * menu,
                  const gchar * name, 
                  const gchar * icon_name,
                  const gchar * binary,
                  const gchar *uri)
{
  GtkWidget * item;
  gchar *exec;
  GtkWidget * image;
  gchar * bin_path;

  bin_path = g_find_program_in_path (binary);
  g_return_val_if_fail (bin_path,FALSE);
  if (bin_path != binary)
  {
    g_free (bin_path);
  }
  item = cairo_menu_item_new_with_label (name);
  image = get_gtk_image (icon_name);  
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
  exec = g_strdup_printf("%s %s", binary ,uri);
  g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);
  g_object_weak_ref (G_OBJECT(item),(GWeakNotify) g_free,exec);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
  return TRUE;
}


static GtkWidget *
get_session_menu(void)
{
  GtkWidget *menu = cairo_menu_new();
  add_special_item (menu,_("Logout"),"gnome-logout","gnome-session-save","--logout-dialog --gui");
  if (!add_special_item (menu,_("Lock Screen"),"gnome-lockscreen","gnome-screensaver-command","--lock"))
  {
    add_special_item (menu,_("Lock Screen"),"system-lockscreen","xscreensaver-command","-lock");
  }  
  add_special_item (menu,_("Suspend"),"gnome-session-suspend","gnome-power-cmd","suspend");
  add_special_item (menu,_("Hibernate"),"gnome-session-hibernate","gnome-power-cmd","hibernate");
  add_special_item (menu,_("Shutdown"),"gnome-logout","gnome-session-save","--shutdown-dialog --gui");  
  gtk_widget_show_all (menu);
  return menu;
}
/*
 TODO:
  check for existence of the various bins.
  why are vfs network mounts not showing?
  The menu item order needs to be fixed.
 */
static GtkWidget * 
_get_places_menu (GtkWidget * menu)
{  
  static GVolumeMonitor* vol_monitor = NULL;
  static DesktopAgnosticVFSGtkBookmarks *bookmarks_parser = NULL;  
  
  GtkWidget *item = NULL;
  GError *error = NULL;
  GtkWidget * image;
  gchar * exec;
  const gchar *desktop_dir = g_get_user_special_dir (G_USER_DIRECTORY_DESKTOP);
  const gchar *homedir = g_get_home_dir();

  g_debug ("%s",__func__);
  gtk_container_foreach (GTK_CONTAINER (menu),(GtkCallback)_remove_menu_item,menu);

  add_special_item (menu,_("Computer"),"computer","nautilus","computer:///");
  add_special_item (menu,_("Home"),"stock_home","nautilus",homedir);
  add_special_item (menu,_("Desktop"),"desktop",XDG_OPEN,desktop_dir?desktop_dir:homedir);
/*
TODO: check the trash and set to stock_trash_empty if trash is empty
                     */
  add_special_item (menu,_("Trash"),"stock_trash_full",XDG_OPEN,desktop_dir?desktop_dir:homedir);
  add_special_item (menu,_("File System"),"system",XDG_OPEN,"/");
    
  if (!vol_monitor)
  {
    /*this is structured like this because get_places() is
    invoked any time there is a change in places... only want perform
    these actions once.*/
    vol_monitor = g_volume_monitor_get();
    bookmarks_parser = desktop_agnostic_vfs_gtk_bookmarks_new (NULL, TRUE);
  }
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);    
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);
  g_signal_handlers_disconnect_by_func (vol_monitor, G_CALLBACK(_get_places_menu), menu);
  g_signal_handlers_disconnect_by_func (G_OBJECT (bookmarks_parser), G_CALLBACK (_get_places_menu), menu);
    
  g_signal_connect_swapped(vol_monitor, "volume-changed", G_CALLBACK(_get_places_menu), menu);
  g_signal_connect_swapped(vol_monitor, "drive-changed", G_CALLBACK(_get_places_menu), menu);
  g_signal_connect_swapped(vol_monitor, "drive-connected", G_CALLBACK(_get_places_menu), menu);
  g_signal_connect_swapped(vol_monitor, "drive-disconnected", G_CALLBACK(_get_places_menu), menu);    
  g_signal_connect_swapped(vol_monitor, "mount-changed", G_CALLBACK(_get_places_menu), menu);
  g_signal_connect_swapped(vol_monitor, "mount-added", G_CALLBACK(_get_places_menu), menu);
  g_signal_connect_swapped(vol_monitor, "mount-removed", G_CALLBACK(_get_places_menu), menu);
  g_signal_connect_swapped (G_OBJECT (bookmarks_parser), "changed",
                      G_CALLBACK (_get_places_menu), menu);

    /*process mount etc*/
  GList *drives = g_volume_monitor_get_connected_drives(vol_monitor);
  GList *mounts = g_volume_monitor_get_mounts (vol_monitor);
  GList * iter;

/*  if (volumes)
  {
    g_message("Number of volumes: %d", g_list_length(volumes));
    g_list_foreach(volumes, (GFunc)_fillin_connected, menu);
  }*/
/*
     this iterating through mounts then drives may change.
     May go to using mounts and volumes.
     */
  for (iter = mounts; iter ; iter = g_list_next (iter))
  {
    GMount *mount = iter->data;
    gchar * name = g_mount_get_name (mount);
    GIcon * gicon = g_mount_get_icon (mount);
    GFile * file = g_mount_get_root (mount);
    gchar * uri = g_file_get_uri (file);
    item = cairo_menu_item_new_with_label (name);    
    image = get_image_from_gicon (gicon);
    if (image)
    {
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
    }    
    gtk_menu_shell_append (GTK_MENU_SHELL(menu),item);

    exec = g_strdup_printf("%s %s", XDG_OPEN, uri);
    g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);  
    g_object_weak_ref (G_OBJECT(item), (GWeakNotify)g_free,exec);
    
    g_free (name);
    g_free (uri);
    g_object_unref (file);
    g_object_unref (gicon);
  }

  if (drives)
  {
    item = gtk_separator_menu_item_new ();
    gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
  }
    
  for (iter = drives; iter ; iter = g_list_next (iter))
  {
    GDrive * drive = iter->data;
    if (g_drive_has_volumes (drive))
    {
      GList * drive_volumes = g_drive_get_volumes (drive);
      GList * vol_iter = NULL;
      for (vol_iter =drive_volumes;vol_iter;vol_iter=g_list_next(vol_iter))
      {
        GVolume * volume = vol_iter->data;
        GIcon * gicon = g_volume_get_icon (volume);
        gchar * name = g_volume_get_name (volume);
        
        item = cairo_menu_item_new_with_label (name);
        image = get_image_from_gicon (gicon);
        if (image)
        {
          gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
        }            
        gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
        g_free (name);
      }
      g_list_foreach (drive_volumes,(GFunc)g_object_unref,NULL);
      g_list_free (drive_volumes);
    }
    else
    {
      gboolean mounted = FALSE;
      gchar * name = g_drive_get_name (drive);
      GIcon * gicon = g_drive_get_icon (drive);
      
      item = cairo_menu_item_new_with_label (name);
      image = get_image_from_gicon (gicon);
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
      }          
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
      g_free (name);      
    }
  }
    
  g_list_foreach (drives,(GFunc)g_object_unref,NULL);
  g_list_free (drives);
  g_list_foreach (mounts,(GFunc)g_object_unref,NULL);
  g_list_free (mounts);

  add_special_item (menu,_("Network"),"network","nautilus","network:/");
  add_special_item (menu,_("Connect to Server"),"stock_connect","nautilus-connect-server","");
  item = gtk_separator_menu_item_new ();
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);

    
  /* bookmarks    */
  GSList *bookmarks;
  GSList *node;

  bookmarks = desktop_agnostic_vfs_gtk_bookmarks_get_bookmarks (bookmarks_parser);
  for (node = bookmarks; node != NULL; node = node->next)
  {
    DesktopAgnosticVFSBookmark *bookmark;
    DesktopAgnosticVFSFile *b_file;
    const gchar *b_alias;
    gchar *b_path;
    gchar *b_uri;
    gchar *shell_quoted = NULL;
    gchar *icon_name = NULL;
    
    bookmark = (DesktopAgnosticVFSBookmark*)node->data;
    b_file = desktop_agnostic_vfs_bookmark_get_file (bookmark);
    b_alias = desktop_agnostic_vfs_bookmark_get_alias (bookmark);
    b_path = desktop_agnostic_vfs_file_get_path (b_file);
    b_uri = desktop_agnostic_vfs_file_get_uri (b_file);

    if (b_path)
    {
      shell_quoted = g_shell_quote (b_path);
      exec = g_strdup_printf("%s %s", XDG_OPEN,shell_quoted);
      g_free (shell_quoted);
      if (b_alias)
      {
        item = cairo_menu_item_new_with_label (b_alias);
        icon_name = g_utf8_strdown (b_alias,-1);
      }
      else
      {
        gchar * base = g_path_get_basename (b_path);
        item = cairo_menu_item_new_with_label (base);        
        icon_name = g_utf8_strdown (base,-1);        
        g_free (base);
      }
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);              
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    }
    else if ( strncmp(b_uri, "http", 4)==0 )
    {
      shell_quoted = g_shell_quote (b_uri);
      exec = g_strdup_printf("%s %s",XDG_OPEN,shell_quoted);
      g_free (shell_quoted);
      if (b_alias)
      {
        item = cairo_menu_item_new_with_label (b_alias);
        icon_name = g_utf8_strdown (b_alias,-1);        
      }
      else
      {
        gchar * base = g_path_get_basename (b_uri);
        item = cairo_menu_item_new_with_label (b_uri);
        icon_name = g_utf8_strdown (base,-1);        
        g_free (base);
      }
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);              
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    }
    /*
     non-http(s) uris.  open with nautils.  obviously we should be smarter about
     this
     */
    else if (b_uri)
    {
      shell_quoted = g_shell_quote (b_uri);
      exec = g_strdup_printf("%s %s", "nautilus" ,shell_quoted);
      g_free (shell_quoted);
      if (b_alias)
      {
        item = cairo_menu_item_new_with_label (b_alias);
        icon_name = g_utf8_strdown (b_alias,-1);        
      }
      else
      {
        gchar * base = g_path_get_basename (b_uri);
        item = cairo_menu_item_new_with_label (base);
        icon_name = g_utf8_strdown (base,-1);        
        g_free (base);
      }
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);      
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    }
    else
    {
      g_object_ref_sink (item);
      item = NULL;
    }

    if (item)
    {
      if (icon_name)
      {
        gchar * folderfied_icon_name = g_strdup_printf("folder-%s",icon_name);
        g_free (icon_name);
        icon_name = folderfied_icon_name;
        image = get_gtk_image (icon_name);
        g_free (icon_name);
      }
      if (!image)
      {
        image = get_gtk_image ("stock_folder");
      }
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
      }
    }
    g_free (b_path);
    g_free (b_uri);
  }
  gtk_widget_show_all (menu);
  return menu;
}

GtkWidget * 
get_places_menu (void)
{
  g_debug ("%s",__func__);
  GtkWidget *menu = cairo_menu_new();
  _get_places_menu (menu);
  return menu;
}

static GtkWidget *
fill_er_up(MenuInstance * instance,GMenuTreeDirectory *directory, GtkWidget * menu)
{
  static gint sanity_depth_count = 0;
  GSList * items = gmenu_tree_directory_get_contents(directory);
  GSList * tmp = items;
  GtkWidget * menu_item = NULL;
  GtkWidget * sub_menu = NULL;
  const gchar * txt;
  gchar * desktop_file;
  DesktopAgnosticFDODesktopEntry *entry;
  GtkWidget * image;
  gboolean detached_sub = FALSE;
  gchar * uri;

  sanity_depth_count++;
  if (sanity_depth_count>6)
  {
    sanity_depth_count--;
    g_warning ("%s: Exceeded max menu depth of 6 at %s",__func__,gmenu_tree_directory_get_name((GMenuTreeDirectory*)directory));
    return cairo_menu_new ();
  }
  if (!menu)
  {
    menu = cairo_menu_new ();
  }
  
  while (tmp != NULL)
  {
    GMenuTreeItem *item = tmp->data;

    switch (gmenu_tree_item_get_type(item))
    {

      case GMENU_TREE_ITEM_ENTRY:
        entry = NULL;
        if (gmenu_tree_entry_get_is_excluded ((GMenuTreeEntry *) item))
        {
          break;
        }
        if (gmenu_tree_entry_get_is_nodisplay ((GMenuTreeEntry *) item))
        {
          break;
        }
        txt = gmenu_tree_entry_get_name( (GMenuTreeEntry*)item);
        desktop_file = g_strdup (gmenu_tree_entry_get_desktop_file_path ((GMenuTreeEntry*)item));
        uri = g_strdup_printf("file://%s\n",desktop_file);
        if (desktop_file)
        {
          entry = get_desktop_entry (desktop_file);
        }
        if (entry)
        {
          gchar * icon_name;
          if (desktop_agnostic_fdo_desktop_entry_key_exists (entry,"Icon"))
          {
            icon_name = g_strdup(desktop_agnostic_fdo_desktop_entry_get_icon (entry));
          }
          else
          {
            icon_name = g_strdup ("stock_missing-image");
          }
          image = get_gtk_image (icon_name);
          menu_item = cairo_menu_item_new_with_label (txt?txt:"unknown");
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }
          gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
          gtk_widget_show_all (menu_item);
          g_signal_connect(G_OBJECT(menu_item), "button-release-event", G_CALLBACK(_launch), desktop_file);
          cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),uri);
          g_free (uri);          
          g_object_unref (entry);
          g_free (icon_name);          
        }
        break;

      case GMENU_TREE_ITEM_DIRECTORY:
        if (!gmenu_tree_directory_get_is_nodisplay ( (GMenuTreeDirectory *) item) )
        {
          CallbackContainer * c;
          gchar * drop_data;
          c = g_malloc0 (sizeof(CallbackContainer));          
          c->icon_name = g_strdup(gmenu_tree_directory_get_icon ((GMenuTreeDirectory *)item));
          image = get_gtk_image (c->icon_name);
          if (!image)
          {
            image = get_gtk_image ("stock_folder");
          }
          sub_menu = GTK_WIDGET(fill_er_up( instance,(GMenuTreeDirectory*)item,NULL));
          txt = gmenu_tree_directory_get_name((GMenuTreeDirectory*)item);          
          menu_item = cairo_menu_item_new_with_label (txt?txt:"unknown");
          gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }        
          gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
          c->file_path = g_strdup(gmenu_tree_directory_get_desktop_file_path ((GMenuTreeDirectory*)item));          
          c->display_name = g_strdup (gmenu_tree_directory_get_name ((GMenuTreeDirectory*)item));
          c->instance = instance;          
          /*
           TODO: possibly change data
           */
          drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",c->file_path,c->display_name,c->icon_name);
          cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
          g_free (drop_data);
          g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
          g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)_free_callback_container,c);
          break;
        }
        break;
      case GMENU_TREE_ITEM_HEADER:
//    printf("GMENU_TREE_ITEM_HEADER\n");
        break;

      case GMENU_TREE_ITEM_SEPARATOR:
        menu_item = gtk_separator_menu_item_new ();
        gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);          
        break;

      case GMENU_TREE_ITEM_ALIAS:
//    printf("GMENU_TREE_ITEM_ALIAS\n");
        /*      {
             GMenuTreeItem *aliased_item;

             aliased_item = gmenu_tree_alias_get_item (GMENU_TREE_ALIAS (item));
             if (gmenu_tree_item_get_type (aliased_item) == GMENU_TREE_ITEM_ENTRY)
                print_entry (GMENU_TREE_ENTRY (aliased_item), path);
              }*/
        break;

      default:
        g_assert_not_reached();
        break;
    }

    gmenu_tree_item_unref(tmp->data);
    tmp = tmp->next;
  }
  g_slist_free(items);  
  if (menu)
  {
    gtk_widget_show_all (menu);
  }
  sanity_depth_count--;
  return menu;
}

static void
_run_dialog (GtkMenuItem * item, MenuInstance *instance)
{
  const gchar * cmd;
  gchar * file_path;
  cmd = instance->run_cmd_fn (AWN_APPLET(instance->applet));
  if (cmd)
  {
    g_spawn_command_line_async (cmd,NULL);
  }
}

static void
_search_dialog (GtkMenuItem * item, MenuInstance * instance)
{
  const gchar * cmd;
  cmd = instance->search_cmd_fn (AWN_APPLET(instance->applet));
  if (cmd)
  {
    g_spawn_command_line_async (cmd,NULL);
  }
}


static gboolean
_delay_menu_update (MenuInstance * instance)
{
  instance->menu = menu_build (instance);
  instance->source_id = 0;
  return FALSE;
}

/*
 Multiples seem to get generated with a typical software install.
 thus the timeout.
 */

static void 
_menu_modified_cb(GMenuTree *tree,MenuInstance * instance)
{
  if (!instance->source_id)
  {
    instance->source_id = g_timeout_add_seconds (5, (GSourceFunc)_delay_menu_update,instance);
  }
}

static GMenuTreeDirectory *
find_menu_dir (MenuInstance * instance, GMenuTreeDirectory * root)
{
  g_return_val_if_fail (root,NULL);
  GSList * items = NULL;
  GSList * tmp;
  GMenuTreeDirectory * result = NULL;
  const gchar * txt = NULL;

  txt = gmenu_tree_directory_get_desktop_file_path (root);
  if (g_strcmp0(txt,instance->submenu_name)==0 )
  {
    return root;
  }

  items = gmenu_tree_directory_get_contents(root);  
  tmp = items;
  while (tmp != NULL)
  {
    GMenuTreeItem *item = tmp->data;

    switch (gmenu_tree_item_get_type(item))
    {
      case GMENU_TREE_ITEM_DIRECTORY:
        if (!gmenu_tree_directory_get_is_nodisplay ( (GMenuTreeDirectory *) item) )
        {
          txt = gmenu_tree_directory_get_desktop_file_path ((GMenuTreeDirectory*)item);
          if (g_strcmp0(txt,instance->submenu_name)==0 )
          {
            result = (GMenuTreeDirectory*)item;
            break;            
          }
          else if (!result)  /*we're continuing looping if result to unref the remaining items*/
          {
            result = find_menu_dir (instance, (GMenuTreeDirectory *) item);
          }
        }
        /*deliberately falling through*/
      case GMENU_TREE_ITEM_ENTRY:
      case GMENU_TREE_ITEM_HEADER:
      case GMENU_TREE_ITEM_SEPARATOR:
      case GMENU_TREE_ITEM_ALIAS:
        gmenu_tree_item_unref(tmp->data);        
        break;
      default:
        g_assert_not_reached();
        break;
    }
    tmp = tmp->next;
  }
  g_slist_free(items);  
  return result;
}

static void
clear_menu (MenuInstance * instance)
{
  if (instance->menu)
  {
    GList * children = gtk_container_get_children (GTK_CONTAINER(instance->menu));
    GList * iter;
    for (iter = children;iter;iter=g_list_next (iter))
    {
      if ( (iter->data !=instance->places) && (iter->data!=instance->recent))
      {
        gtk_container_remove (GTK_CONTAINER (instance->menu),iter->data);
        /*TODO  check if this is necessary*/
        g_list_free (children);        
        children = iter = gtk_container_get_children (GTK_CONTAINER(instance->menu));
      }
    }
    if (children)
    {
      g_list_free (children);
    }
  }
}

GtkWidget *
submenu_build (MenuInstance * instance)
{
  GMenuTreeDirectory *main_root;
  GMenuTreeDirectory *settings_root;
  GtkWidget * menu = NULL;

  /*
   if the menu is set then clear any menu items (except for places or recent)
   */
  clear_menu (instance);
  if (!main_menu_tree)
  {
    main_menu_tree = gmenu_tree_lookup("applications.menu", GMENU_TREE_FLAGS_NONE);
  }
  if (!settings_menu_tree)
  {
    settings_menu_tree = gmenu_tree_lookup("settings.menu", GMENU_TREE_FLAGS_NONE);
  }
  g_assert (main_menu_tree);
  /*
   get_places_menu() and get_recent_menu() are 
   responsible for managing updates in place.  Session should only need
   to be created once or may eventually need to follow the previously mentioned
   behaviour.   Regardless... they should only need to be created here from scratch,
   this fn should _not_ be invoked in a refresh of those menus.

   We don't want to rebuild the whole menu tree everytime a vfs change occurs 
   or a document is accessed
   */
  if (g_strcmp0(instance->submenu_name,":::PLACES")==0)
  {
    g_assert (!instance->menu);
    menu = get_places_menu ();
  }
  else if (g_strcmp0(instance->submenu_name,":::RECENT")==0)
  {
    g_assert (!instance->menu);    
    menu = get_recent_menu ();
  }
  else if (g_strcmp0(instance->submenu_name,":::SESSION")==0)
  {
    g_assert (!instance->menu);    
    menu = get_session_menu ();
  }
  else
  {
    GMenuTreeDirectory * menu_dir = NULL;    
    
    main_root = gmenu_tree_get_root_directory(main_menu_tree);
    g_assert (gmenu_tree_item_get_type( (GMenuTreeItem*)main_root) == GMENU_TREE_ITEM_DIRECTORY);
    g_assert (main_root);
    settings_root = gmenu_tree_get_root_directory(settings_menu_tree);
    if ( menu_dir = find_menu_dir (instance,main_root) )
    {
      /* if instance->menu then we're refreshing in a monitor callback*/
      gmenu_tree_remove_monitor (main_menu_tree,(GMenuTreeChangedFunc)submenu_build,instance);
      gmenu_tree_add_monitor (main_menu_tree,(GMenuTreeChangedFunc)submenu_build,instance);
      menu = fill_er_up(instance,menu_dir,instance->menu);      
    }
    else if ( menu_dir = find_menu_dir (instance,settings_root) )
    {
      gmenu_tree_remove_monitor (main_menu_tree,(GMenuTreeChangedFunc)submenu_build,instance);
      gmenu_tree_add_monitor (main_menu_tree,(GMenuTreeChangedFunc)submenu_build,instance);
      menu = fill_er_up(instance,menu_dir,instance->menu);     
    }
    if (menu_dir)
    {      
      gmenu_tree_item_unref(menu_dir);
    }
    gmenu_tree_item_unref(main_root);
    gmenu_tree_item_unref(settings_root);                               
  }
  return instance->menu = menu;
}

/*
 TODO: add network, and trash

 */
GtkWidget * 
menu_build (MenuInstance * instance)
{
  GMenuTreeDirectory *root;
  GtkWidget * image = NULL;
  GtkWidget   *menu_item;
  GtkWidget * sub_menu;
  const gchar * txt;
  CallbackContainer * c;
  gchar * drop_data;

  if (instance->submenu_name)
  {
    return instance->menu = submenu_build (instance);
  }
  
  clear_menu (instance);    
  if (!main_menu_tree)
  {
    main_menu_tree = gmenu_tree_lookup("applications.menu", GMENU_TREE_FLAGS_NONE);
  }
  if (!settings_menu_tree)
  {
    settings_menu_tree = gmenu_tree_lookup("settings.menu", GMENU_TREE_FLAGS_NONE);
  }

  if (main_menu_tree)
  {
    root = gmenu_tree_get_root_directory(main_menu_tree);
    g_assert (!instance->submenu_name);
    gmenu_tree_remove_monitor (main_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);    
    gmenu_tree_add_monitor (main_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);
    instance->menu = fill_er_up(instance,root,instance->menu);
    gmenu_tree_item_unref(root);    
  }
  if  (instance->menu)
  {  
      menu_item = gtk_separator_menu_item_new ();
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);  
  }
  if (settings_menu_tree)
  {
    root = gmenu_tree_get_root_directory(settings_menu_tree);
    gmenu_tree_remove_monitor (settings_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);
    gmenu_tree_add_monitor (settings_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);
    if (!instance->menu)
    {
      g_debug ("%s:  No applications menu????",__func__);
      instance->menu = fill_er_up(instance,root,instance->menu);
    }
    else
    {
      sub_menu = fill_er_up(instance,root,NULL);
      c = g_malloc0 (sizeof(CallbackContainer));        
      c->icon_name = g_strdup(gmenu_tree_directory_get_icon (root));
      image = get_gtk_image (c->icon_name);
      txt = gmenu_tree_entry_get_name((GMenuTreeEntry*)root);        
      menu_item = cairo_menu_item_new_with_label (txt?txt:"unknown");        
      gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);
      c->file_path = g_strdup(":::SETTINGS");
      c->display_name = g_strdup ("Settings");
      drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",c->file_path,c->display_name,c->icon_name);
      cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
      g_free (drop_data);
      c->instance = instance;
      g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
      g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)_free_callback_container,c);      
    }
    gmenu_tree_item_unref(root);    
  }
    
    /*TODO Check to make sure it is needed. Should not be displayed if 
      all flags are of the NO persuasion.*/
  if  (instance->menu)
  {
     menu_item = gtk_separator_menu_item_new ();
     gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);  
  }
  
  if (! (instance->flags & MENU_BUILD_NO_PLACES) )
  {
    if ( !instance->check_menu_hidden_fn || !instance->check_menu_hidden_fn (instance->applet,":::PLACES"))
    {    
      if (instance->places)
      {
        GList * children = gtk_container_get_children (GTK_CONTAINER(instance->menu));
        menu_item =instance->places;
        gtk_menu_reorder_child (GTK_MENU(instance->menu),menu_item,g_list_length (children));
        g_list_free (children);
      }
      else
      {
        sub_menu = get_places_menu ();
        gchar * icon_name;
        instance->places = menu_item = cairo_menu_item_new_with_label (_("Places"));
        image = get_gtk_image (icon_name = "places");
        if (!image)
        {
          image = get_gtk_image(icon_name = "stock_folder");
        }
        if (image)
        {
          gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
        }
        gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);            
        gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);
        c = g_malloc0 (sizeof(CallbackContainer));
        c->file_path = g_strdup(":::PLACES");
        c->display_name = g_strdup ("Places");
        c->icon_name = g_strdup(icon_name);        
        drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",c->file_path,c->display_name,c->icon_name);
        cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
        g_free (drop_data);
        c->instance = instance;
        g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
        g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)_free_callback_container,c);
      }
    }    
  }
  
  if (! (instance->flags & MENU_BUILD_NO_RECENT))
  {
    if ( !instance->check_menu_hidden_fn || !instance->check_menu_hidden_fn (instance->applet,":::RECENT"))
    {
      if (instance->recent)
      {
        GList * children = gtk_container_get_children (GTK_CONTAINER(instance->menu));
        menu_item =instance->recent;
        gtk_menu_reorder_child (GTK_MENU(instance->menu),menu_item,g_list_length (children));
        g_list_free (children);        
      }
      else
      {
        sub_menu = get_recent_menu ();        
        gchar * icon_name;
        instance->recent = menu_item = cairo_menu_item_new_with_label (_("Recent Documents"));
        image = get_gtk_image (icon_name = "document-open-recent");
        if (!image)
        {
          image = get_gtk_image(icon_name = "stock_folder");
        }
        if (image)
        {
          gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
        }
        gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
        gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);
        c = g_malloc0 (sizeof(CallbackContainer));
        c->file_path = g_strdup(":::RECENT");
        c->display_name = g_strdup ("Recent Documents");
        c->icon_name = g_strdup (icon_name);        
        drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",c->file_path,c->display_name,c->icon_name);
        cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
        g_free (drop_data);
        c->instance = instance;
        g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
        g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)_free_callback_container,c);
      }
    }
  }

  /*TODO Check to make sure it is needed. avoid double separators*/
  if  (instance->menu &&  (!(instance->flags & MENU_BUILD_NO_RECENT) || !(instance->flags & MENU_BUILD_NO_PLACES))&&
     (!instance->check_menu_hidden_fn (instance->applet,":::RECENT") || !instance->check_menu_hidden_fn (instance->applet,":::PLACES")) )
  {
    menu_item = gtk_separator_menu_item_new ();
    gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);  
  }

  if (! (instance->flags & MENU_BUILD_NO_SESSION))
  {
    if ( !instance->check_menu_hidden_fn || !instance->check_menu_hidden_fn (instance->applet,":::SESSION"))
    {    
      sub_menu = get_session_menu ();
      menu_item = cairo_menu_item_new_with_label (_("Session"));
      image = get_gtk_image ("session-properties");
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);

      c = g_malloc0 (sizeof(CallbackContainer));
      c->file_path = g_strdup(":::SESSION");
      c->display_name = g_strdup ("Session");
      c->icon_name = g_strdup ("session-properties");      
      drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",c->file_path,c->display_name,c->icon_name);
      cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
      g_free (drop_data);
      c->instance = instance;
      g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
      g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)_free_callback_container,c);
    }
  }
  
  if (! (instance->flags & MENU_BUILD_NO_SEARCH))
  {  
    if ( !instance->submenu_name)
    {    
      /*generates a compiler warning due to the ellipse*/
      menu_item = cairo_menu_item_new_with_label (_("Search\u2026"));
      /* add proper ellipse*/
      image = get_gtk_image ("stock_search");
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);
      g_signal_connect (menu_item,"activate",G_CALLBACK(_search_dialog),instance);
    }
  }
  
  if (! (instance->flags & MENU_BUILD_NO_RUN))
  {
    if ( !instance->submenu_name)
    {    
      /*generates a compiler warning due to the ellipse*/    
      menu_item = cairo_menu_item_new_with_label (_("Launch\u2026"));
      /* add proper ellipse*/
      image = get_gtk_image ("gnome-run");
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);
      g_signal_connect (menu_item,"activate",G_CALLBACK(_run_dialog),instance);
    }
  }

  gtk_widget_show_all (instance->menu);
  instance->done_once = TRUE;
  return instance->menu;
}
