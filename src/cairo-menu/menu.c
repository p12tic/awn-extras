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

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-applet-dialog.h>
#include <libawn/awn-cairo-utils.h>

#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>

#include "backend-gnome.h"
#include "menu.h"
#include "render.h"
#include "config_entries.h"


extern gboolean  G_repression;
extern GtkWidget * G_toplevel;
extern AwnApplet *G_applet;
extern int G_max_width;
Win_man * G_win_man;

extern Cairo_menu_config G_cairo_menu_conf;
gboolean  G_focus = FALSE;
gboolean  G_entered = FALSE;
guint32  G_last_motion = 0;
guint32  G_focus_out_time = 0;



void init_win_man(void)
{
  gint  monitor_number;
  GdkRectangle rect;
  GdkScreen * screen = gdk_screen_get_default();
  monitor_number = gdk_screen_get_monitor_at_window(screen, GTK_WIDGET(G_applet)->window);
  gdk_screen_get_monitor_geometry(screen, monitor_number, &rect);

  G_win_man = g_malloc(sizeof(Win_man));
  G_win_man->x = rect.x;
  G_win_man->y = rect.y;
  G_win_man->width = rect.width;
  G_win_man->height = rect.height;
  G_win_man->children = NULL;

}

void fixed_move(GtkWidget *widget, gint x, gint y)
{
  gtk_window_move(widget->parent->parent, G_win_man->x + x, G_win_man->y + y);
}

void fixed_put(GtkWidget *widget, gint x, gint y)
{
  G_win_man->children = g_list_append(G_win_man->children, widget);
  gtk_window_move(widget->parent->parent, G_win_man->x + x, G_win_man->y + y);
}


void pos_dialog(GtkWidget * window)
{
  gint x, y;
  gdk_window_get_origin(GTK_WIDGET(G_applet)->window, &x, &y);
  gtk_window_move(GTK_WINDOW(window), x, y - window->allocation.height + GTK_WIDGET(G_applet)->allocation.height / 3);

}

void hide_all_menus(void)
{
  if (!G_repression)
  {
    gtk_widget_hide(G_toplevel->parent->parent);
    _hide_all_windows(NULL);
//  G_repression=FALSE;
    G_focus = FALSE;
    G_entered = FALSE;
  }
}


gboolean _cmp_pointer(gconstpointer a, gconstpointer b)
{
  return a -b;
}

gboolean _enter_menu(GtkWidget *widget, GdkEventButton *event, GtkWidget * parent_menu)
{
  G_entered = TRUE;
  G_last_motion = event->time;
// printf("Enter Menu: %d\n",G_entered);
  gtk_widget_grab_focus(widget);
  return FALSE;
}

gboolean _leave_menu(GtkWidget *widget, GdkEventButton *event, GtkWidget * parent_menu)
{
  G_entered = FALSE;
  G_last_motion = event->time;
// printf("Leave Menu: %d\n",G_entered);

  if (parent_menu)
    gtk_widget_grab_focus(parent_menu);

  return FALSE;
}


gboolean _focus_in_menu(GtkWidget *widget, GdkEventButton *event, GtkWidget * parent_menu)
{
  gtk_widget_grab_focus(widget);
  G_focus = TRUE;
  G_last_motion = event->time;
  //printf("Focus in: %d\n",G_focus);
  return FALSE;
}

gboolean _check_if_really_done(GtkWidget * parent_menu)
{
// printf("check_if_really_done\n");
  if (!G_focus &&  !G_entered)
  {
//  if ( ( G_focus_out_time-G_last_motion) >100 )
    {
      hide_all_menus();
      G_focus = FALSE;
      G_entered = FALSE;
      return FALSE;
    }
  }

  if (parent_menu)
    gtk_widget_grab_focus(parent_menu);

  return FALSE;
}

gboolean _focus_out_menu(GtkWidget *widget, GdkEventButton *event, GtkWidget * parent_menu)
{
  G_focus = FALSE;
// printf("Focus out: %d\n",G_focus);
  G_focus_out_time = event->time;

  if (!G_entered)
  {
    g_timeout_add(250, _check_if_really_done, parent_menu);
  }

  if (parent_menu)
    gtk_widget_grab_focus(parent_menu);

  return FALSE;
}

gboolean _motion_menu(GtkWidget *widget, GdkEventMotion *event, GtkWidget * parent_menu)
{

  gtk_widget_grab_focus(widget);
  G_entered = TRUE;
// printf("Motion\n");
  G_last_motion = event->time;
  return FALSE;
}



static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, gpointer null)
{
  cairo_t *cr;
  cr = gdk_cairo_create(widget->window);
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint(cr);
  cairo_destroy(cr);
  return FALSE;
}

GtkWidget * menu_new(GtkWidget * parent_menu)
{
  int scrwidth;
  GdkColormap *colormap;
  GdkScreen *screen;
  GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);

  gtk_window_set_type_hint(GTK_WINDOW(win), GDK_WINDOW_TYPE_HINT_DIALOG);
  gtk_window_set_skip_taskbar_hint(GTK_WINDOW(win), TRUE);

  gtk_window_set_decorated(GTK_WINDOW(win), FALSE);
  gtk_window_set_accept_focus(GTK_WINDOW(win), TRUE);
  gtk_window_set_focus_on_map(GTK_WINDOW(win), TRUE);
  gtk_window_set_keep_above(GTK_WINDOW(win), TRUE);
  gtk_window_set_skip_pager_hint(GTK_WINDOW(win), TRUE);
  gtk_window_stick(GTK_WINDOW(win));

// gtk_window_set_opacity(GTK_WINDOW (win),0.0);
#if 0
  gtk_window_set_type_hint(GTK_WINDOW(win), GDK_WINDOW_TYPE_HINT_POPUP_MENU);

#endif
  screen = gtk_window_get_screen(GTK_WINDOW(win));
  colormap = gdk_screen_get_rgba_colormap(screen);

  if (colormap != NULL && gdk_screen_is_composited(screen))
  {
    gtk_widget_set_colormap(win, colormap);
  }

  gtk_widget_set_events(win, GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK | GDK_FOCUS_CHANGE_MASK | GDK_POINTER_MOTION_MASK);

  gtk_widget_set_app_paintable(win, TRUE);
  GtkWidget *vbox = gtk_vbox_new(FALSE, 0);
  gtk_widget_set_app_paintable(vbox, TRUE);
  GtkWidget * fixed = gtk_fixed_new();
  gtk_widget_set_app_paintable(fixed, TRUE);
  gtk_fixed_set_has_window(fixed, TRUE);

  gtk_fixed_put(fixed, vbox, 0, 0);
  gtk_container_add(GTK_CONTAINER(win), fixed);
  g_signal_connect(G_OBJECT(win), "focus-in-event", G_CALLBACK(_focus_in_menu), parent_menu);
  //g_signal_connect (G_OBJECT (win), "move-focus",G_CALLBACK (_focus_in_menu), parent_menu);
  g_signal_connect(G_OBJECT(win), "focus-out-event", G_CALLBACK(_focus_out_menu), parent_menu);
  g_signal_connect(G_OBJECT(win), "enter-notify-event", G_CALLBACK(_enter_menu), parent_menu);
  g_signal_connect(G_OBJECT(win), "leave-notify-event", G_CALLBACK(_leave_menu), parent_menu);
  g_signal_connect(G_OBJECT(win), "motion-notify-event", G_CALLBACK(_motion_menu), parent_menu);


  g_signal_connect(G_OBJECT(win), "expose-event", G_CALLBACK(_expose_event), NULL);
  g_signal_connect(G_OBJECT(fixed), "expose-event", G_CALLBACK(_expose_event), NULL);
  g_signal_connect(G_OBJECT(vbox), "expose-event", G_CALLBACK(_expose_event), NULL);

  if (parent_menu)
    gtk_window_set_transient_for(parent_menu, win);

  return vbox;

}

static gboolean _map_window(GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu)
{

// printf("map\n");
  return FALSE;
}

Cairo_main_menu * dialog_new(AwnApplet *applet)
{
  read_config();
  init_win_man();
  G_cairo_menu_conf.submenu_deps = g_tree_new(_cmp_pointer);

  Cairo_main_menu * menu = g_malloc(sizeof(Cairo_main_menu));
  menu->menu_data = get_menu_data(G_cairo_menu_conf.show_search,
                                  G_cairo_menu_conf.show_run,
                                  G_cairo_menu_conf.show_places,
                                  G_cairo_menu_conf.show_logout,
                                  G_cairo_menu_conf.filemanager,
                                  G_cairo_menu_conf.logout
                                 );
  menu->applet = applet;
  G_toplevel = menu_new(NULL);
  gtk_widget_set_size_request(G_toplevel->parent, -1, -1);
  g_slist_foreach(menu->menu_data, measure_width, &G_max_width);
  g_slist_foreach(menu->menu_data, render_menu_widgets, G_toplevel);
  g_signal_connect(G_OBJECT(G_toplevel->parent->parent), "map", G_CALLBACK(_map_window), menu);

  return menu;
}

