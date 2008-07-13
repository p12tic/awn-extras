/*
 * Copyright (C) 2007, 2008 Rodney Cryderman <rcryderman@gmail.com>
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

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>
#include "render.h"

#define APPLET_NAME "Cairo Menu"

#include "backend-gnome.h"
#include "menu.h"

extern gboolean  G_repression;
extern Cairo_menu_config G_cairo_menu_conf;
AwnApplet *G_applet;
extern Win_man *G_win_man;
extern GtkWidget * G_toplevel;
gint G_Height;
static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu);

static gboolean _show_prefs(GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu)
{

  show_prefs();
  return TRUE;
}

static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;
  G_repression = FALSE;
//   printf("_button_clicked_event\n");

  if (event->button == 1)
  {
    if (GTK_WIDGET_VISIBLE(G_toplevel->parent->parent))
    {
//   g_list_foreach(G_win_man->children,_fixup_menus,NULL);
      hide_all_menus();
    }
    else
    {
      gtk_widget_show_all(G_toplevel->parent->parent);
      fixed_move(G_toplevel, 0, G_win_man->height - G_toplevel->allocation.height);
      pos_dialog(G_toplevel->parent->parent);

    }
  }
  else if (event->button == 3)
  {
    static GtkWidget * menu=NULL;
    static GtkWidget * item;

    if (!menu)
    {
      menu = awn_applet_create_default_menu (G_applet);
      item = gtk_menu_item_new_with_label("Preferences");
      gtk_widget_show(item);
      gtk_menu_set_screen(GTK_MENU(menu), NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);
      g_signal_connect(G_OBJECT(item), "button-press-event", G_CALLBACK(_show_prefs), NULL);
    }

    gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL,event_button->button, event_button->time);
  }

  return TRUE;
}

static gboolean _icon_done(gpointer null)
{
  static gboolean done_once = FALSE;

  if (!done_once)
  {
    GdkPixbuf *icon;
    Cairo_main_menu * menu;
    menu = dialog_new(G_applet);
    gtk_widget_show_all(G_toplevel);
    g_list_foreach(G_win_man->children, _fixup_menus, NULL);
    gtk_widget_hide(G_toplevel);
    g_signal_connect(G_OBJECT(menu->applet), "button-press-event", G_CALLBACK(_button_clicked_event), menu);

    hide_all_menus();

    gtk_window_set_opacity(GTK_WINDOW(G_toplevel->parent->parent), 1.0);
  }

  done_once = TRUE;

  return FALSE;
}

static gboolean _map_event(GtkWidget *widget, gpointer null)
{
  static gboolean done_once = FALSE;

  if (!done_once)
  {
    g_timeout_add(1000,_icon_done,null);    
    done_once = TRUE;    
  }
  return FALSE;
}
AwnApplet* awn_applet_factory_initp(gchar* uid, gint orient, gint height)
{

  AwnApplet *applet = AWN_APPLET(awn_applet_simple_new(uid, orient, height));
  G_applet = applet;
  gtk_widget_set_size_request(GTK_WIDGET(applet), height, -1);
  GdkPixbuf *icon;
  G_Height = height;
  
  read_config();
  
  
  awn_applet_simple_set_awn_icon(applet,
                                    APPLET_NAME,
                                    G_cairo_menu_conf.applet_icon)  ;
  
  icon = gtk_icon_theme_load_icon(gtk_icon_theme_get_default(),
                                  G_cairo_menu_conf.applet_icon,
                                  height ,
                                  0, NULL);
  gtk_widget_show_all(GTK_WIDGET(applet));

  g_signal_connect_after(G_OBJECT(applet),"map" , G_CALLBACK(_map_event), NULL);
  
  return applet;

}


