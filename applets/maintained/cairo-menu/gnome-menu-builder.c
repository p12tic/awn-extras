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

static void
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
  g_return_if_fail (bin_path);
  if (bin_path != binary)
  {
    g_free (bin_path);
  }
  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),name);
  image = get_gtk_image (icon_name);  
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
  exec = g_strdup_printf("%s %s", binary ,uri);
  g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);
  g_object_weak_ref (G_OBJECT(item),(GWeakNotify) g_free,exec);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
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
    
    item = cairo_menu_item_new ();
    bookmark = (DesktopAgnosticVFSBookmark*)node->data;
    b_file = desktop_agnostic_vfs_bookmark_get_file (bookmark);
    b_alias = desktop_agnostic_vfs_bookmark_get_alias (bookmark);
    b_path = desktop_agnostic_vfs_file_get_path (b_file);
    b_uri = desktop_agnostic_vfs_file_get_uri (b_file);

    if (b_path)
    {
      shell_quoted = g_shell_quote (b_path);
      exec = g_strdup_printf("%s %s", XDG_OPEN,shell_quoted);
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);        
      g_free (shell_quoted);
      if (b_alias)
      {
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),b_alias);
        icon_name = g_utf8_strdown (b_alias,-1);
      }
      else
      {
        gchar * base = g_path_get_basename (b_path);
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),base);
        icon_name = g_utf8_strdown (base,-1);        
        g_free (base);
      }
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    }
    else if ( strncmp(b_uri, "http", 4)==0 )
    {
      shell_quoted = g_shell_quote (b_uri);
      exec = g_strdup_printf("%s %s",XDG_OPEN,shell_quoted);
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);        
      g_free (shell_quoted);
      if (b_alias)
      {
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),b_alias);
        icon_name = g_utf8_strdown (b_alias,-1);        
      }
      else
      {
        gchar * base = g_path_get_basename (b_uri);
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),base);
        icon_name = g_utf8_strdown (base,-1);        
        g_free (base);
      }
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
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);        
      g_free (shell_quoted);
      if (b_alias)
      {
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),b_alias);
        icon_name = g_utf8_strdown (b_alias,-1);        
      }
      else
      {
        gchar * base = g_path_get_basename (b_uri);
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),base);
        icon_name = g_utf8_strdown (base,-1);        
        g_free (base);
      }
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
  GtkWidget *menu = cairo_menu_new();
  _get_places_menu (menu);
  return menu;
}

static GtkWidget *
fill_er_up(MenuInstance * instance,GMenuTreeDirectory *directory, GtkWidget * menu)
{
  GSList * items = gmenu_tree_directory_get_contents(directory);
  GSList * tmp = items;
  GtkWidget * menu_item = NULL;
  GtkWidget * sub_menu = NULL;
  const gchar * txt;
  gchar * desktop_file;
  DesktopAgnosticFDODesktopEntry *entry;
  gchar * icon_name;
  gchar *file_path;
  gchar * display_name;
  GtkWidget * image;
  gboolean detached_sub = FALSE;
  gchar * uri;

  if (!menu && !instance->submenu_name)
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
        if (instance->submenu_name)
        {
          break;
        }
        menu_item = cairo_menu_item_new ();
        txt = gmenu_tree_entry_get_name( (GMenuTreeEntry*)item);
        desktop_file = g_strdup (gmenu_tree_entry_get_desktop_file_path ((GMenuTreeEntry*)item));
        uri = g_strdup_printf("file://%s\n",desktop_file);
        if (desktop_file)
        {
          entry = get_desktop_entry (desktop_file);
        }
        if (entry)
        {
          if (desktop_agnostic_fdo_desktop_entry_key_exists (entry,"Icon"))
          {
            icon_name = g_strdup(desktop_agnostic_fdo_desktop_entry_get_icon (entry));
          }
          else
          {
            icon_name = g_strdup ("stock_missing-image");
          }
          image = get_gtk_image (icon_name);
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }
          gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
          gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
          gtk_widget_show_all (menu_item);
          g_signal_connect(G_OBJECT(menu_item), "activate", G_CALLBACK(_launch), desktop_file);
          cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),uri);
          g_free (uri);          
          g_object_unref (entry);
          g_free (icon_name);          
        }
        break;

      case GMENU_TREE_ITEM_DIRECTORY:
        detached_sub = instance->submenu_name && g_strcmp0 (instance->submenu_name, gmenu_tree_directory_get_desktop_file_path ((GMenuTreeDirectory *) item) );
        if (instance->submenu_name && !detached_sub)
        {
          g_assert (!menu);
          gchar * tmp = instance->submenu_name;
          instance->submenu_name = NULL;
          menu = fill_er_up( instance,(GMenuTreeDirectory*)item,NULL);
          g_assert (menu); 
          instance->submenu_name = tmp;
          break;
        }
        if (instance->submenu_name)
        {
          GtkWidget *x;
          x = fill_er_up( instance,(GMenuTreeDirectory*)item,NULL);
          if (x)
          {
            menu=x;
          }
        }
        if (!instance->submenu_name && !gmenu_tree_directory_get_is_nodisplay ( (GMenuTreeDirectory *) item) )
        {
          CallbackContainer * c;
          gchar * drop_data;
          icon_name = g_strdup(gmenu_tree_directory_get_icon ((GMenuTreeDirectory *)item));
          image = get_gtk_image (icon_name);
          if (!image)
          {
            image = get_gtk_image ("stock_folder");
          }
          sub_menu = GTK_WIDGET(fill_er_up( instance,(GMenuTreeDirectory*)item,NULL));
          menu_item = cairo_menu_item_new ();
          gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
          txt = gmenu_tree_directory_get_name((GMenuTreeDirectory*)item);
          gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }        
          gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
          file_path = g_strdup(gmenu_tree_directory_get_desktop_file_path ((GMenuTreeDirectory*)item));
          c = g_malloc (sizeof(CallbackContainer));
          c->arr[0].str = file_path;
          display_name = g_strdup (gmenu_tree_directory_get_name ((GMenuTreeDirectory*)item));
          /*
           TODO: possibly change data
           */
          drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",file_path,display_name,icon_name);
          cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
          g_free (drop_data);
          c->arr[1].str = display_name;
          c->arr[3].str = icon_name;
          c->instance = instance;
          g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
          g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,file_path);
          g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,display_name);
          g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,icon_name);                                      
          g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,c);
          break;
        }
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
  menu_build (instance);
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

/*
 TODO: add network, and trash

 */
GtkWidget * 
menu_build (MenuInstance * instance)
{
  GMenuTreeDirectory *root;
  static GMenuTree *  main_menu_tree = NULL;
  static GMenuTree *  settings_menu_tree = NULL;    
  gchar * icon_name = NULL;
  GtkWidget * image = NULL;
  GtkWidget   *menu_item;
  GtkWidget * sub_menu;
  const gchar * txt;
  CallbackContainer * c;
  gchar * display_name;
  gchar * drop_data;
  gchar * file_path;

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
        iter = gtk_container_get_children (GTK_CONTAINER(instance->menu));
      }
    }
  }
  
  if (!main_menu_tree)
  {
    main_menu_tree = gmenu_tree_lookup("applications.menu", GMENU_TREE_FLAGS_NONE);
  }

  if (main_menu_tree)
  {
    root = gmenu_tree_get_root_directory(main_menu_tree);
    if (root)
    {
      instance->menu = fill_er_up(instance,root,instance->menu);
      if (instance->done_once)
      {
        gmenu_tree_remove_monitor (main_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);
      }
      gmenu_tree_add_monitor (main_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);      
      gmenu_tree_item_unref(root);
    }
  }
  if  (! instance->submenu_name && instance->menu)
  {  
      menu_item = gtk_separator_menu_item_new ();
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);  
  }
  if (!settings_menu_tree)
  {
    settings_menu_tree = gmenu_tree_lookup("settings.menu", GMENU_TREE_FLAGS_NONE);
  }
  if (settings_menu_tree && (! instance->submenu_name || !instance->menu))
  {
    root = gmenu_tree_get_root_directory(settings_menu_tree);
    if (root)
    {
      if (instance->done_once)
      {
        gmenu_tree_remove_monitor (settings_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);
      }
      gmenu_tree_add_monitor (settings_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,instance);

      if ( !instance->submenu_name )
      {
        sub_menu = GTK_WIDGET(fill_er_up(instance,root,NULL));        
        icon_name = g_strdup(gmenu_tree_directory_get_icon (root));
        image = get_gtk_image (icon_name);
        menu_item = cairo_menu_item_new ();
        gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
        txt = gmenu_tree_entry_get_name((GMenuTreeEntry*)root);
        gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
        if (image)
        {
          gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
        }        
        gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);

        c = g_malloc (sizeof(CallbackContainer));
        file_path = g_strdup(":::SETTINGS");
        c->arr[0].str = file_path;
        display_name = g_strdup ("Settings");
        drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",file_path,display_name,icon_name);
        cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
        g_free (drop_data);
        c->arr[1].str = display_name;
        c->arr[3].str = g_strdup (icon_name);
        c->instance = instance;
        g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
        g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,file_path);
        g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,display_name);
        g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,icon_name);                                      
        g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,c);
      }
      else if ( !instance->menu)
      {
        if (instance->submenu_name && ( g_strcmp0 (instance->submenu_name,":::SETTINGS")==0))
        {
          gchar * t = instance->submenu_name;
          instance->submenu_name = NULL;
          sub_menu = GTK_WIDGET(fill_er_up(instance,root,NULL));
          instance->submenu_name = t;
          instance->menu = sub_menu;          
        }
        else
        {
          sub_menu = GTK_WIDGET(fill_er_up(instance,root,NULL));
          instance->menu = sub_menu;
        }
      }
      gmenu_tree_item_unref (root);
    }
  }

    /*TODO Check to make sure it is needed. Should not be displayed if 
      all flags are of the NO persuasion.*/
  if  (! instance->submenu_name && instance->menu)
  {
     menu_item = gtk_separator_menu_item_new ();
     gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);  
  }
  
  if (! (instance->flags & MENU_BUILD_NO_PLACES) && (! instance->submenu_name || !instance->menu))
  {
    if ( !instance->check_menu_hidden_fn || !instance->check_menu_hidden_fn (instance->applet,":::PLACES"))
    {    
      if (instance->places)
      {
        menu_item =instance->places;
        gtk_menu_reorder_child (GTK_MENU(instance->menu),menu_item,100);
      }
      else
      {
        if ( !instance->submenu_name || ( g_strcmp0 (instance->submenu_name,":::PLACES")==0))
        {      
          sub_menu = get_places_menu ();
          if (instance->menu)
          {
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

            c = g_malloc (sizeof(CallbackContainer));
            file_path = g_strdup(":::PLACES");
            c->arr[0].str = file_path;
            display_name = g_strdup ("Places");
            drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",file_path,display_name,icon_name);
            cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
            g_free (drop_data);
            c->arr[1].str = display_name;
            icon_name = g_strdup (icon_name);
            c->arr[3].str = icon_name;
            c->instance = instance;
            g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,file_path);
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,display_name);
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,icon_name);                                      
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,c);
          }
          else
          {
           instance->menu = sub_menu;
          }
        }
      }
    }    
  }
  
  if (! (instance->flags & MENU_BUILD_NO_RECENT)&& (! instance->submenu_name || !instance->menu))
  {
    if ( !instance->check_menu_hidden_fn || !instance->check_menu_hidden_fn (instance->applet,":::RECENT"))
    {
      if (instance->recent)
      {
        menu_item = instance->recent;
        gtk_menu_reorder_child (GTK_MENU(instance->menu),menu_item,100);      
      }
      else
      {
        if ( !instance->submenu_name || ( g_strcmp0 (instance->submenu_name,":::RECENT")==0))
        {
          sub_menu = get_recent_menu ();        
          if (instance->menu)
          {        
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
            c = g_malloc (sizeof(CallbackContainer));
            file_path = g_strdup(":::RECENT");
            c->arr[0].str = file_path;
            display_name = g_strdup ("Recent Documents");
            drop_data = g_strdup_printf("cairo_menu_item_dir:///@@@%s@@@%s@@@%s\n",file_path,display_name,icon_name);
            cairo_menu_item_set_source (AWN_CAIRO_MENU_ITEM(menu_item),drop_data);
            g_free (drop_data);
            c->arr[1].str = display_name;
            icon_name = c->arr[3].str = g_strdup (icon_name);
            c->instance = instance;
            g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),c);
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,file_path);
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,display_name);
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,icon_name);                                      
            g_object_weak_ref (G_OBJECT(menu_item),(GWeakNotify)g_free,c);
          }
          else
          {
            instance->menu = sub_menu;
          }
        }
      }
    }
  }

  /*TODO Check to make sure it is needed. avoid double separators*/
  if  (! instance->submenu_name && instance->menu)
  {
      menu_item = gtk_separator_menu_item_new ();
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);  
  }

  if (! (instance->flags & MENU_BUILD_NO_SESSION)&& (! instance->submenu_name || !instance->menu))
  {
    if ( !instance->submenu_name )
    {    
      menu_item = cairo_menu_item_new_with_label (_("Session"));
      image = get_gtk_image ("session-properties");
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      gtk_menu_shell_append(GTK_MENU_SHELL(instance->menu),menu_item);
    }
  }
  
  if (! (instance->flags & MENU_BUILD_NO_SEARCH)&& (! instance->submenu_name || !instance->menu))
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
  
  if (! (instance->flags & MENU_BUILD_NO_RUN)&& (! instance->submenu_name || !instance->menu))
  {
    if ( !instance->submenu_name)
    {    
      /*generates a compiler warning due to the ellipse*/    
      menu_item = cairo_menu_item_new_with_label (_("Run Program\u2026"));
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
