#include "config.h"

#include "gnome-menu-builder.h"

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>
#include <glib/gi18n.h>
#include <libdesktop-agnostic/fdo.h>

#include "cairo-menu.h"
#include "cairo-menu-item.h"
#include "misc.h"


/*
 TODO:
  check for existence of the various bins.
  why are vfs network mounts not showing?
  The menu item order needs to be fixed.
 */
static GtkWidget * 
_get_places_menu (GtkWidget * menu)
{  
  static DesktopAgnosticVFSVolumeMonitor* vol_monitor = NULL;
  static DesktopAgnosticVFSGtkBookmarks *bookmarks_parser = NULL;  
  
  GtkWidget *item = NULL;
  GError *error = NULL;
  GtkWidget * image;
  gchar * exec;
  const gchar *desktop_dir = g_get_user_special_dir (G_USER_DIRECTORY_DESKTOP);
  const gchar *homedir = g_get_home_dir();

  gtk_container_foreach (GTK_CONTAINER (menu),(GtkCallback)_remove_menu_item,menu);

  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("Computer"));
  image = get_gtk_image ("computer");  
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
  exec = g_strdup_printf("%s %s", "nautilus", "computer:///");
  g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);  
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    
  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("Home"));
  image = get_gtk_image ("stock_home");  
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
  exec = g_strdup_printf("%s %s", XDG_OPEN, homedir);
  g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);  
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
  
  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("Desktop"));
/*if desktop_dir then use that otherwise use homedir*/
  image = get_gtk_image ("desktop");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }  
  exec = g_strdup_printf("%s %s", XDG_OPEN, desktop_dir?desktop_dir:homedir);
  g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);  
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);

  item = cairo_menu_item_new ();
  gtk_menu_item_set_label (GTK_MENU_ITEM(item),_("File System"));
  image = get_gtk_image ("system");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
  }
  exec = g_strdup_printf("%s /", XDG_OPEN);
  g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);  
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
    g_signal_connect_swapped(vol_monitor, "volume-mounted", G_CALLBACK(_get_places_menu), menu);
    g_signal_connect_swapped(vol_monitor, "volume-unmounted", G_CALLBACK(_get_places_menu), menu);

    bookmarks_parser = desktop_agnostic_vfs_gtk_bookmarks_new (NULL, TRUE);
    g_signal_connect_swapped (G_OBJECT (bookmarks_parser), "changed",
                      G_CALLBACK (_get_places_menu), menu);
  }

  GList *volumes = desktop_agnostic_vfs_volume_monitor_get_volumes(vol_monitor);

  if (volumes)
  {
    g_message("Number of volumes: %d", g_list_length(volumes));
    g_list_foreach(volumes, (GFunc)_fillin_connected, menu);
  }

  g_list_free (volumes);

  item = gtk_separator_menu_item_new ();
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    
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
    gchar *b_uri;
    gchar *shell_quoted = NULL;

    item = cairo_menu_item_new ();
    bookmark = (DesktopAgnosticVFSBookmark*)node->data;
    b_file = desktop_agnostic_vfs_bookmark_get_file (bookmark);
    b_alias = desktop_agnostic_vfs_bookmark_get_alias (bookmark);
    b_path = desktop_agnostic_vfs_file_get_path (b_file);
    b_uri = desktop_agnostic_vfs_file_get_uri (b_file);

    image = get_gtk_image ("stock_folder");    
    if (image)
    {
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),image);
    }  
    g_debug ("%s, %s",b_alias,b_path);
    if (b_path)
    {
      shell_quoted = g_shell_quote (b_path);
      exec = g_strdup_printf("%s %s", XDG_OPEN,shell_quoted);
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);        
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
    else if ( strncmp(b_uri, "http", 4)==0 )
    {
      shell_quoted = g_shell_quote (b_uri);
      exec = g_strdup_printf("%s %s",XDG_OPEN,shell_quoted);
      g_debug ("http exec = %s",exec);
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);        
      g_free (shell_quoted);
      if (b_alias)
      {
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),b_alias);
      }
      else
      {
        gchar * base = g_path_get_basename (b_uri);
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),base);
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
      g_debug ("uri exec = %s",exec);
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_exec), exec);        
      g_free (shell_quoted);
      if (b_alias)
      {
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),b_alias);
      }
      else
      {
        gchar * base = g_path_get_basename (b_uri);
        gtk_menu_item_set_label(GTK_MENU_ITEM(item),base);
        g_free (base);
      }
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),item);
    }
    else
    {
      g_object_ref_sink (item);
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
fill_er_up(GMenuTreeDirectory *directory)
{
  GtkWidget * menu = cairo_menu_new ();
  GSList * items = gmenu_tree_directory_get_contents(directory);
  GSList * tmp = items;
  GtkWidget * menu_item = NULL;
  GtkWidget * sub_menu = NULL;
  const gchar * txt;
  gchar * desktop_file;
  DesktopAgnosticFDODesktopEntry *entry;
  gchar * icon_name;
  GtkWidget * image;
  
  while (tmp != NULL)
  {
    GMenuTreeItem *item = tmp->data;

    switch (gmenu_tree_item_get_type(item))
    {

      case GMENU_TREE_ITEM_ENTRY:
        
        if (gmenu_tree_entry_get_is_excluded ((GMenuTreeEntry *) item))
        {
          continue;
        }
        if (gmenu_tree_entry_get_is_nodisplay ((GMenuTreeEntry *) item))
        {
          continue;
        }
        menu_item = cairo_menu_item_new ();
        txt = gmenu_tree_entry_get_name( (GMenuTreeEntry*)item);
        desktop_file = g_strdup(gmenu_tree_entry_get_desktop_file_path ((GMenuTreeEntry*)item));
        entry = get_desktop_entry (desktop_file);
        if (entry)
        {
          icon_name = desktop_agnostic_fdo_desktop_entry_get_icon (entry);
          image = get_gtk_image (icon_name);
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }
        }
        gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
        gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
        gtk_widget_show_all (menu_item);
        g_signal_connect(G_OBJECT(menu_item), "activate", G_CALLBACK(_launch), desktop_file);
        g_object_unref (entry);
        break;

      case GMENU_TREE_ITEM_DIRECTORY:
        if (!gmenu_tree_directory_get_is_nodisplay ( (GMenuTreeDirectory *) item) )
        {
          icon_name = g_strdup(gmenu_tree_directory_get_icon ((GMenuTreeDirectory *)item));
          g_debug ("%s",icon_name);
          image = get_gtk_image (icon_name);
          sub_menu = GTK_WIDGET(fill_er_up( (GMenuTreeDirectory*)item));
          menu_item = cairo_menu_item_new ();
          gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
          txt = gmenu_tree_entry_get_name((GMenuTreeEntry*)item);
          gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }        
          gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
          g_free (icon_name);
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
  gtk_widget_show_all (menu);
  return menu;
}


GtkWidget * 
menu_build (void)
{
  GMenuTree *  menu_tree;
  GMenuTreeDirectory *root;
  GtkWidget     * menu = NULL;
  GtkWidget     * settings_menu = NULL;
  gchar * icon_name = NULL;
  GtkWidget * image = NULL;
  GtkWidget   *menu_item;
  GtkWidget * sub_menu;
  const gchar * txt;
  
  menu_tree = gmenu_tree_lookup("applications.menu", GMENU_TREE_FLAGS_NONE);

  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);
    if (root)
    {
      menu = fill_er_up(root);
      gmenu_tree_item_unref(root);
    }
    else
    {
      menu = cairo_menu_new ();
    }
  }

  menu_item = gtk_separator_menu_item_new ();
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);  

  menu_tree = gmenu_tree_lookup("settings.menu", GMENU_TREE_FLAGS_NONE);
  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);
    if (root)
    {
//      settings_menu = fill_er_up(root);
//      gmenu_tree_item_unref(root);

      icon_name = g_strdup(gmenu_tree_directory_get_icon (root));
      image = get_gtk_image (icon_name);
      sub_menu = GTK_WIDGET(fill_er_up(root));
      menu_item = cairo_menu_item_new ();
      gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
      txt = gmenu_tree_entry_get_name((GMenuTreeEntry*)root);
      gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
      g_free (icon_name);
      gmenu_tree_item_unref (root);
    }
  }

  menu_item = gtk_separator_menu_item_new ();
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);  

  menu_item = cairo_menu_item_new_with_label (_("Places"));
  image = get_gtk_image ("places");
  if (!image)
  {
    image = get_gtk_image("stock_folder");
  }
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
  }
  sub_menu = get_places_menu ();
  gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);

  
  menu_item = cairo_menu_item_new_with_label (_("Recent Documents"));
  image = get_gtk_image ("document-open-recent");
  if (!image)
  {
    image = get_gtk_image("stock_folder");
  }
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
  }        
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);

  menu_item = cairo_menu_item_new_with_label (_("Session"));
  image = get_gtk_image ("session-properties");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
  }        
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);

  menu_item = cairo_menu_item_new_with_label (_("Search"));
  /* add proper ellipse*/
  image = get_gtk_image ("stock_search");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
  }        
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);

  menu_item = cairo_menu_item_new_with_label (_("Run Program"));
  /* add proper ellipse*/
  image = get_gtk_image ("stock_execute");
  if (image)
  {
    gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
  }        
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);

  
  gtk_widget_show_all (menu);
  
  return menu;
}
