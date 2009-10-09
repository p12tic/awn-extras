#include "config.h"

#include "gnome-menu-builder.h"

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>
#include <glib/gi18n.h>
#include <libdesktop-agnostic/fdo.h>

#include "cairo-menu.h"
#include "cairo-menu-item.h"


static DesktopAgnosticFDODesktopEntry *
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

static void
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

static GtkWidget *
get_gtk_image (gchar * icon_name)
{
  GtkWidget *image;
  
  if (icon_name)
  {
    gint width,height;
    image = NULL;

    gtk_icon_size_lookup (GTK_ICON_SIZE_MENU,&width,&height);  
    image = gtk_image_new_from_icon_name (icon_name,width);

    if (!image)
    {
      image = gtk_image_new_from_file (icon_name);
    }
  }
  return image;
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
        icon_name = g_strdup(gmenu_tree_directory_get_icon ((GMenuTreeDirectory *)item));
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

      case GMENU_TREE_ITEM_HEADER:
//    printf("GMENU_TREE_ITEM_HEADER\n");
        break;

      case GMENU_TREE_ITEM_SEPARATOR:
//    printf("GMENU_TREE_ITEM_HEADER\n");
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
gnome_menu_build (void)
{
  GMenuTree *  menu_tree;
  GMenuTreeDirectory *root;
  GtkWidget     * menu = NULL;
  
  menu_tree = gmenu_tree_lookup("applications.menu", GMENU_TREE_FLAGS_NONE);

  if (menu_tree)
  {
    root = gmenu_tree_get_root_directory(menu_tree);
    if (root)
    {
      menu = fill_er_up(root);
      gmenu_tree_item_unref(root);
    }
  }
  gtk_widget_show_all (menu);
  return menu;
}
