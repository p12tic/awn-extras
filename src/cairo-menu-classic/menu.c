/*
 * Copyright (C) 2007 Rodney Cryderman <rcryderman@gmail.com>
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


#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-dialog.h>
#include <libawn/awn-cairo-utils.h>

#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>

#include "backend-gnome.h"
#include "menu.h"
#include "render.h"


extern gboolean  G_repression;
extern gboolean  G_total_repression;


static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, Cairo_main_menu * menu);


extern GtkWidget * G_Fixed;
extern GtkWidget * G_toplevel;
extern GtkWidget * G_mainwindow;
extern AwnApplet *G_applet;
extern int G_max_width;

extern Cairo_menu_config G_cairo_menu_conf;

void pos_dialog(GtkWidget * mainwindow)
{
  gint x, y;
  gint scrwidth;
  gint scrheight;
  gint xsize, ysize;
  gint  monitor_number;
  GdkRectangle rect;

  GdkScreen * screen = gdk_screen_get_default();
  monitor_number = gdk_screen_get_monitor_at_window(screen, GTK_WIDGET(G_applet)->window);
  gdk_screen_get_monitor_geometry(screen, monitor_number, &rect);
  scrwidth = rect.width;
  scrheight = rect.height;
  gdk_window_get_origin(GTK_WIDGET(G_applet)->window, &x, &y);
  xsize = (scrwidth + rect.x) - x;

  if (xsize < 10)
  {
    xsize = 300;
  };

  ysize = (scrheight + rect.y) - (scrheight - y);

  if (ysize < 10)
  {
    ysize = 550;
  }

  if (x > scrwidth)
    x = 0;

  if (y > scrheight)
    y = scrheight / 2;

  if (xsize > scrwidth)
    xsize = scrwidth / 2;

  if (ysize > scrheight)
    ysize = scrheight / 2;

  gtk_widget_set_size_request(mainwindow, xsize, ysize);  //FIXME

  gtk_window_resize(GTK_WINDOW(mainwindow), xsize, ysize);

  gtk_window_move(GTK_WINDOW(mainwindow), x, y - G_Fixed->allocation.height + GTK_WIDGET(G_applet)->allocation.height / 3);

}

GtkWidget * build_dialog_window(void)
{

  int scrwidth;
  GdkColormap *colormap;
  GdkScreen *screen;
  GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);

  gtk_window_set_decorated(GTK_WINDOW(win), FALSE);
  gtk_window_set_type_hint(GTK_WINDOW(win), GDK_WINDOW_TYPE_HINT_POPUP_MENU);
  gtk_window_stick(GTK_WINDOW(win));

  gtk_window_set_skip_taskbar_hint(GTK_WINDOW(win), TRUE);
  gtk_window_set_keep_above(GTK_WINDOW(win), TRUE);
  gtk_window_set_accept_focus(GTK_WINDOW(win), TRUE);
  gtk_window_set_focus_on_map(GTK_WINDOW(win), FALSE);
  screen = gtk_window_get_screen(GTK_WINDOW(win));
  colormap = gdk_screen_get_rgba_colormap(screen);

  if (colormap != NULL && gdk_screen_is_composited(screen))
  {
    gtk_widget_set_colormap(win, colormap);
  }

  gtk_widget_add_events(win, GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK | GDK_FOCUS_CHANGE_MASK);

  gtk_widget_set_app_paintable(win, TRUE);

  if (G_cairo_menu_conf.do_fade)
    gtk_window_set_opacity(GTK_WINDOW(win), 0.0) ;

  gtk_widget_set_redraw_on_allocate(GTK_WINDOW(win), FALSE);

  return win;
}

gboolean _cmp_pointer(gconstpointer a, gconstpointer b)
{
  return a -b;
}

static gboolean _button_clicked_mainwindow(GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu)
{
  GdkEventButton *event_button;

  if (!G_total_repression)
  {
    event_button = (GdkEventButton *) event;
    gtk_widget_hide(menu->mainwindow);
    G_repression = FALSE;
  }

  G_total_repression = FALSE;

  return FALSE;
}

static gboolean _focus_out_mainwindow(GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu)
{
  if (!G_total_repression)
  {
    g_list_foreach(GTK_FIXED(G_Fixed)->children, _fixup_menus, NULL);
    gtk_widget_hide(menu->mainwindow);
  }

  G_total_repression = FALSE;

  return FALSE;
}

Cairo_main_menu * dialog_new(AwnApplet *applet)
{

  read_config();
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
  G_mainwindow = menu->mainwindow = build_dialog_window();

  gtk_window_set_focus_on_map(GTK_WINDOW(menu->mainwindow), TRUE);
  G_Fixed = menu->mainfixed =  gtk_fixed_new();
  gtk_widget_set_app_paintable(menu->mainfixed , TRUE);
  gtk_widget_show_all(menu->mainfixed);

  gtk_fixed_set_has_window(GTK_FIXED(menu->mainfixed), FALSE);
  gtk_widget_set_size_request(menu->mainfixed, 222, 555);  //FIXME
  gtk_container_add(GTK_CONTAINER(menu->mainwindow), menu->mainfixed);
  G_toplevel = menu->mainbox = gtk_vbox_new(FALSE, 0);
  gtk_widget_set_app_paintable(menu->mainbox , TRUE);
  gtk_fixed_put(GTK_FIXED(menu->mainfixed), menu->mainbox, 0, 0);

  g_slist_foreach(menu->menu_data, measure_width, &G_max_width);
  g_slist_foreach(menu->menu_data, render_menu_widgets, menu->mainbox);
  gtk_widget_show_all(menu->mainbox);

  g_signal_connect(G_OBJECT(menu->mainfixed), "expose-event", G_CALLBACK(_expose_event), menu);

  g_signal_connect(G_OBJECT(menu->mainwindow), "button-press-event", G_CALLBACK(_button_clicked_mainwindow), menu);
  g_signal_connect(G_OBJECT(menu->mainwindow), "focus-out-event", G_CALLBACK(_focus_out_mainwindow), menu);
  g_signal_connect(G_OBJECT(menu->mainfixed), "focus-out-event", G_CALLBACK(_focus_out_mainwindow), menu);
  return menu;
}


static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, Cairo_main_menu * menu)
{
  cairo_t *cr;
  cr = gdk_cairo_create(widget->window);
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint(cr);
  return FALSE;
}

