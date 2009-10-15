#include "config.h"

#include "gnome-menu-builder.h"

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>
#include <glib/gi18n.h>
#include <libdesktop-agnostic/fdo.h>

#include <libawn/libawn.h>
#include "cairo-menu.h"
#include "cairo-menu-item.h"
#include "misc.h"
#include "cairo-menu-applet.h"

GtkWidget *  menu_build (AwnApplet * applet,GetRunCmdFunc run_func,
                          GetSearchCmdFunc,gint flags);

GetRunCmdFunc get_run_cmd;
GetSearchCmdFunc get_search_cmd;
static AwnApplet * Applet;
static guint   source_id;

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

static void 
_create_icon (GtkButton *widget,gchar * desktop)
{
  g_debug ("%s: %s",__func__,desktop);
}

gboolean 
_button_press_dir (GtkWidget *menu_item, GdkEventButton *event, gchar * desktop)
{
  GtkWidget * popup;
  GtkWidget * item;
  g_debug ("%s: %s",__func__,desktop);  
  switch (event->button)
  {
    case 3:
      popup = gtk_menu_new ();
      item = gtk_menu_item_new_with_label ("Create icon");
      gtk_menu_shell_append(GTK_MENU_SHELL(popup), item);
      g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(_create_icon), desktop);
      gtk_widget_show_all (popup);
      gtk_menu_popup(GTK_MENU(popup), NULL, NULL, NULL, NULL, event->button, event->time);
      break;
    default:
      break;
  }
}


static GtkWidget *
fill_er_up(GMenuTreeDirectory *directory, GtkWidget * menu)
{
  GSList * items = gmenu_tree_directory_get_contents(directory);
  GSList * tmp = items;
  GtkWidget * menu_item = NULL;
  GtkWidget * sub_menu = NULL;
  const gchar * txt;
  gchar * desktop_file;
  DesktopAgnosticFDODesktopEntry *entry;
  gchar * icon_name;
  GtkWidget * image;

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
          continue;
        }
        if (gmenu_tree_entry_get_is_nodisplay ((GMenuTreeEntry *) item))
        {
          continue;
        }
        menu_item = cairo_menu_item_new ();
        txt = gmenu_tree_entry_get_name( (GMenuTreeEntry*)item);
        desktop_file = g_strdup (gmenu_tree_entry_get_desktop_file_path ((GMenuTreeEntry*)item));
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
          g_object_unref (entry);
          g_free (icon_name);          
        }
        break;

      case GMENU_TREE_ITEM_DIRECTORY:
        if (!gmenu_tree_directory_get_is_nodisplay ( (GMenuTreeDirectory *) item) )
        {
          icon_name = g_strdup(gmenu_tree_directory_get_icon ((GMenuTreeDirectory *)item));
          image = get_gtk_image (icon_name);
          sub_menu = GTK_WIDGET(fill_er_up( (GMenuTreeDirectory*)item,NULL));
          menu_item = cairo_menu_item_new ();
          gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
          txt = gmenu_tree_directory_get_name((GMenuTreeDirectory*)item);
          gtk_menu_item_set_label (GTK_MENU_ITEM(menu_item),txt?txt:"unknown");
          if (image)
          {
            gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
          }        
          gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
          g_signal_connect (menu_item, "button-press-event",G_CALLBACK(_button_press_dir),
            g_strdup(gmenu_tree_directory_get_desktop_file_path ((GMenuTreeDirectory*)item)));
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

static void
_run_dialog (GtkMenuItem * item, CairoMenuApplet * applet)
{
  const gchar * cmd;
  cmd = get_run_cmd (AWN_APPLET(applet));
  if (cmd)
  {
    g_spawn_command_line_async (cmd,NULL);
  }
}

static void
_search_dialog (GtkMenuItem * item, CairoMenuApplet * applet)
{
  const gchar * cmd;
  cmd = get_search_cmd (AWN_APPLET(applet));
  if (cmd)
  {
    g_spawn_command_line_async (cmd,NULL);
  }
}


static gboolean
_delay_menu_update (CairoMenu * menu)
{
  menu_build (NULL,NULL,NULL,-1);
  source_id = 0;
  return FALSE;
}

/*
 Multiples seem to get generated with a typical software install.
 thus the timeout.
 */
static void 
_menu_modified_cb(GMenuTree *tree,CairoMenu *menu)
{
  g_debug ("%s: tree = %p",__func__,tree);
//  menu_build (NULL);
  if (!source_id)
  {
    source_id = g_timeout_add_seconds (5, (GSourceFunc)_delay_menu_update,menu);
  }
}

GtkWidget * 
menu_build (AwnApplet * applet,GetRunCmdFunc run_func,GetSearchCmdFunc search_func,
            gint new_flags)
{
  static done_once = FALSE;
  static GMenuTree *  main_menu_tree = NULL;
  static GMenuTree *  settings_menu_tree = NULL;  
  static GtkWidget * places=NULL;
  static GtkWidget * recent=NULL;
  GMenuTreeDirectory *root;
  static GtkWidget     * menu = NULL;
  static flags = 0;
  GtkWidget     * settings_menu = NULL;
  gchar * icon_name = NULL;
  GtkWidget * image = NULL;
  GtkWidget   *menu_item;
  GtkWidget * sub_menu;
  const gchar * txt;

  g_debug ("new_flags = %d",new_flags);
  if (menu)
  {
    GList * children = gtk_container_get_children (GTK_CONTAINER(menu));
    GList * iter;
    for (iter = children;iter;iter=iter->next)
    {
      if ( (iter->data !=places) && (iter->data!=recent))
      {
        gtk_container_remove (GTK_CONTAINER (menu),iter->data);
        /*TODO  check if this is necessary*/
        iter = gtk_container_get_children (GTK_CONTAINER(menu));
      }
    }
  }

  
  if (new_flags != -1)
  {
    flags = new_flags;
  }
  if (run_func)
  {
    get_run_cmd = run_func;
  }
  if (search_func)
  {
    get_search_cmd = search_func;
  }
  
  if (applet)
  {
    Applet = applet;
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
      menu = fill_er_up(root,menu);
      if (done_once)
      {
        gmenu_tree_remove_monitor (main_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,menu);
      }
      gmenu_tree_add_monitor (main_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,menu);      
      gmenu_tree_item_unref(root);
    }
    else
    {
      menu = cairo_menu_new ();
    }
  }

  menu_item = gtk_separator_menu_item_new ();
  gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);  

  if (!settings_menu_tree)
  {
    settings_menu_tree = gmenu_tree_lookup("settings.menu", GMENU_TREE_FLAGS_NONE);
  }
  if (settings_menu_tree)
  {
    root = gmenu_tree_get_root_directory(settings_menu_tree);
    if (root)
    {
      if (done_once)
      {
        gmenu_tree_remove_monitor (settings_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,menu);
      }
      gmenu_tree_add_monitor (settings_menu_tree,(GMenuTreeChangedFunc)_menu_modified_cb,menu);
      icon_name = g_strdup(gmenu_tree_directory_get_icon (root));
      image = get_gtk_image (icon_name);
      sub_menu = GTK_WIDGET(fill_er_up(root,NULL));
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

  if (! (flags & MENU_BUILD_NO_PLACES))
  {
    if (places)
    {
      menu_item = places;
      gtk_menu_reorder_child (GTK_MENU(menu),menu_item,100);
    }
    else
    {
      places = menu_item = cairo_menu_item_new_with_label (_("Places"));
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
    }    
  }
  
  if (! (flags & MENU_BUILD_NO_RECENT))
  {
    if (recent)
    {
      menu_item = recent;
      gtk_menu_reorder_child (GTK_MENU(menu),menu_item,100);      
    }
    else
    {
      recent = menu_item = cairo_menu_item_new_with_label (_("Recent Documents"));
      image = get_gtk_image ("document-open-recent");
      if (!image)
      {
        image = get_gtk_image("stock_folder");
      }
      if (image)
      {
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
      }        
      sub_menu = get_recent_menu ();
      gtk_menu_item_set_submenu (GTK_MENU_ITEM(menu_item),sub_menu);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
    }
  }
  
  if (! (flags & MENU_BUILD_NO_SESSION))
  {
    menu_item = cairo_menu_item_new_with_label (_("Session"));
    image = get_gtk_image ("session-properties");
    if (image)
    {
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
    }        
    gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
  }
  
  if (! (flags & MENU_BUILD_NO_SEARCH))
  {  
    menu_item = cairo_menu_item_new_with_label (_("Search"));
    /* add proper ellipse*/
    image = get_gtk_image ("stock_search");
    if (image)
    {
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
    }        
    gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
    g_signal_connect (menu_item,"activate",G_CALLBACK(_search_dialog),Applet);
  }
  
  if (! (flags & MENU_BUILD_NO_RUN))
  {
    menu_item = cairo_menu_item_new_with_label (_("Run Program"));
    /* add proper ellipse*/
    image = get_gtk_image ("stock_execute");
    if (image)
    {
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (menu_item),image);
    }        
    gtk_menu_shell_append(GTK_MENU_SHELL(menu),menu_item);
    g_signal_connect (menu_item,"activate",G_CALLBACK(_run_dialog),Applet);
  }
  
  gtk_widget_show_all (menu);
  done_once = TRUE;
  g_debug ("done:  menu = %p",menu);  
  return menu;
}
