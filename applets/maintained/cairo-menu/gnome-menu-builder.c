#include "config.h"

#include "gnome-menu-builder.h"

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>
#include <glib/gi18n.h>
#include <libdesktop-agnostic/fdo.h>

#include "cairo-menu.h"
#include "cairo-menu-item.h"
#include "misc.h"

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
  
  menu_tree = gmenu_tree_lookup("gnome-applications.menu", GMENU_TREE_FLAGS_NONE);

  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);
    if (root)
    {
      menu = fill_er_up(root);
      gmenu_tree_item_unref(root);
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
