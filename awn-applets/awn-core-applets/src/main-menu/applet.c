/*
 * Copyright (c) 2007 Neil Jagdish Patel
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

/* This is one of the most basic applets you can make, it just embeds the 
   WnckPager into the applet container*/ 

#include "config.h"
#define GMENU_I_KNOW_THIS_IS_UNSTABLE 1
#include <gmenu-tree.h>
#include <libgnome/gnome-desktop-item.h>

#include <gtk/gtk.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-gconf.h>
#include <libawn/awn-applet-dialog.h>
#include <libawn/awn-applet-simple.h>

#define PAGER_ROWS 2
#define BAR_HEIGHT 100
#define PADDING 4

typedef struct {

  AwnApplet *applet;
  GtkWidget *window;
  GtkWidget *box;
  GtkWidget *icons;

  GMenuTree *tree;
  GMenuTreeDirectory *root;

} Menu;

static Menu *menu;
static GQuark item_quark = 0;

static void populate (Menu *app);

static void
launch (GMenuTreeEntry *entry)
{
  GnomeDesktopItem *item;

 item = gnome_desktop_item_new_from_file  (
            gmenu_tree_entry_get_desktop_file_path (entry),
            0,
            NULL);
  if (!item)
    return;

  gnome_desktop_item_launch (item, NULL, 0, NULL);

  gnome_desktop_item_unref (item);
} 

static void
on_item_clicked (GtkButton *button, GMenuTreeItem *item)
{
  switch (gmenu_tree_item_get_type (item))
  {
    case GMENU_TREE_ITEM_DIRECTORY:
      menu->root = GMENU_TREE_DIRECTORY (item);
      populate (menu);
      break;
    case GMENU_TREE_ITEM_ENTRY:
        launch (GMENU_TREE_ENTRY (item));  
      break;    
    default:
      return;
  }
}

static GtkWidget*
make_item (GMenuTreeItem *item)
{
  GtkWidget *button;
  GtkWidget *vbox;
  GtkWidget *image;
  GdkPixbuf *pixbuf;
  GtkWidget *label;
  const gchar *name;
  const gchar *icon;

  switch (gmenu_tree_item_get_type (item))
  {
    case GMENU_TREE_ITEM_DIRECTORY:
      name = gmenu_tree_directory_get_name (GMENU_TREE_DIRECTORY (item));
      icon = gmenu_tree_directory_get_icon (GMENU_TREE_DIRECTORY (item));
      break;
    case GMENU_TREE_ITEM_ENTRY:
      name = gmenu_tree_entry_get_name (GMENU_TREE_ENTRY (item));
      icon = gmenu_tree_entry_get_icon (GMENU_TREE_ENTRY (item));
      break;    
    default:
      return NULL;
  }
  
  button = gtk_button_new ();
  gtk_button_set_relief (GTK_BUTTON (button), GTK_RELIEF_NONE);
  g_signal_connect (G_OBJECT (button), "clicked",
                    G_CALLBACK (on_item_clicked), (gpointer)item);

  vbox = gtk_vbox_new (FALSE, 2);
  gtk_container_add (GTK_CONTAINER (button), vbox);
  
  image = gtk_image_new_from_icon_name (icon, GTK_ICON_SIZE_DND);
  label = gtk_label_new (name);
  gtk_widget_set_size_request (label, 130, 24);

  gtk_box_pack_start (GTK_BOX (vbox), image, TRUE, TRUE, 0);
  gtk_box_pack_start (GTK_BOX (vbox), label, FALSE, FALSE, 0);
  
  return button;
}
static void
on_back_clicked (GtkButton *button, gpointer null)
{
  GMenuTreeDirectory *temp= menu->root;
  menu->root = gmenu_tree_item_get_parent (GMENU_TREE_ITEM (temp));
  populate (menu);
}

static void
populate (Menu *app)
{
  GtkSizeGroup *group;
  GtkWidget *vbox, *hbox, *label, *table;
  const gchar *name;
  GSList *list, *l;
  gint x = 0;
  gint y = 0;

  vbox = gtk_vbox_new (FALSE, 8);
  table = gtk_table_new (1, 1, TRUE);
  gtk_box_pack_start (GTK_BOX (vbox), table, TRUE, TRUE, 0);

  list = gmenu_tree_directory_get_contents (app->root);
  for (l = list; l != NULL; l = l->next)
  {
    label = make_item (l->data);

    if (!label)
      continue;
    gtk_table_attach_defaults (GTK_TABLE (table), label,
                                 x, x+1, y, y+1);
    x++;
    if (x == 4)
    {
      x = 0;
      y++;
    }
  }
  
  if (app->root == gmenu_tree_get_root_directory (app->tree))
  {
    name = gmenu_tree_directory_get_name (app->root);
    gtk_window_set_title (GTK_WINDOW (app->window),  
                          gmenu_tree_directory_get_name (app->root));
    label = gtk_label_new ("");
    gtk_box_pack_start (GTK_BOX (vbox), label, FALSE, FALSE, 0);
  }
  else
  {
    hbox = gtk_hbox_new (FALSE, 4);
    GtkWidget *image = gtk_button_new_from_stock (GTK_STOCK_GO_BACK);
    g_signal_connect (G_OBJECT (image), "clicked",
                      G_CALLBACK (on_back_clicked), NULL);
    gtk_box_pack_start (GTK_BOX (hbox), image, FALSE, FALSE, 0);
    
    gtk_window_set_title (GTK_WINDOW (app->window),  
                          gmenu_tree_directory_get_name (app->root));
    label = gtk_label_new ("");
    gtk_box_pack_start (GTK_BOX (hbox), label, TRUE, TRUE, 0);
    gtk_box_pack_start (GTK_BOX (vbox), hbox, FALSE, FALSE, 0);
  }

  if (GTK_WIDGET (app->icons))
    gtk_widget_destroy (app->icons);

  app->icons = vbox;
  gtk_container_add (GTK_CONTAINER (app->box), vbox);

  awn_applet_dialog_position_reset (AWN_APPLET_DIALOG (app->window));
  gtk_widget_show_all (app->window);
}

static gboolean
on_icon_clicked (GtkWidget *eb,
                 GdkEventButton *event,
                 Menu *app)
{
  populate (app);
}

static gboolean
on_focus_out (GtkWidget *window, GdkEventFocus *event, gpointer null)
{
  
    gtk_widget_hide (window);
}


#if 0
gboolean 
awn_applet_factory_init (AwnApplet *applet)
{
  Menu      *app = menu =  g_new0 (Menu, 1);
 
  app->tree = gmenu_tree_lookup ("applications.menu", GMENU_TREE_FLAGS_NONE);
  if (!app->tree)
  {
    g_warning ("Unable to find applications.menu");
    return FALSE;
  }
  app->window = awn_applet_dialog_new (applet);
  gtk_window_set_focus_on_map (GTK_WINDOW (app->window), TRUE);

  app->box = gtk_alignment_new (0.5, 0.5, 1, 1);

  gtk_container_add (GTK_CONTAINER (app->window), app->box);
  g_signal_connect (G_OBJECT (app->window), "focus-out-event",
                    G_CALLBACK (on_focus_out), NULL);

  //gtk_window_set_policy (GTK_WINDOW (app->window), FALSE, FALSE, TRUE);
  //gtk_window_set_title (GTK_WINDOW (app->window), "Hello there stranger");
  gtk_widget_show_all (app->window);
  app->root = gmenu_tree_get_root_directory (app->tree);
 
  gtk_widget_set_size_request (GTK_WIDGET (applet), 60, -1);
 
  g_signal_connect (G_OBJECT (applet), "button-press-event",
                    G_CALLBACK (on_icon_clicked), (gpointer)app);
  gtk_widget_show_all (GTK_WIDGET (applet));
  return TRUE;
}
#endif

AwnApplet *
awn_applet_factory_initp (const gchar * uid, gint orient, gint height ) 
{
  AwnApplet *applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
  Menu      *app = menu =  g_new0 (Menu, 1);
 
  app->tree = gmenu_tree_lookup ("applications.menu", GMENU_TREE_FLAGS_NONE);
  if (!app->tree)
  {
    g_warning ("Unable to find applications.menu");
    return FALSE;
  }
  app->window = awn_applet_dialog_new (applet);
  gtk_window_set_focus_on_map (GTK_WINDOW (app->window), TRUE);

  app->box = gtk_alignment_new (0.5, 0.5, 1, 1);

  gtk_container_add (GTK_CONTAINER (app->window), app->box);
  g_signal_connect (G_OBJECT (app->window), "focus-out-event",
                    G_CALLBACK (on_focus_out), NULL);

  gtk_widget_show_all (app->window);
  gtk_widget_hide (app->window);
  app->root = gmenu_tree_get_root_directory (app->tree);
 
  gtk_widget_set_size_request (GTK_WIDGET (applet), 60, -1);
 
  g_signal_connect (G_OBJECT (applet), "button-press-event",
                    G_CALLBACK (on_icon_clicked), (gpointer)app);

  GdkPixbuf *icon;
  icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (),
                                   "gnome-main-menu",
                                   height-2,
                                   0, NULL);
  awn_applet_simple_set_icon (AWN_APPLET_SIMPLE (applet), icon);

  gtk_widget_show_all (GTK_WIDGET (applet));
  return applet;
}
