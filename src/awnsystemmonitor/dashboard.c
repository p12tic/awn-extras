/*
 * Copyright (c) 2007 Rodney Cryderman <rcryderman@gmail.com>
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


#include <glibtop/uptime.h>
#include <glibtop/cpu.h>

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>
#include <signal.h>
#include <sys/types.h>
#include <glib.h>

#include <dirent.h>
#include <libgen.h>
#include <gdk/gdk.h>

#include "dashboard.h"
#include "dashboard_util.h"
#include "config.h"
#include "gconf-config.h"


#undef NDEBUG
#include <assert.h>

#define GCONF_DASHBOARD_PREFIX GCONF_PATH "/dashboard_component_mgmt_"
#define GCONF_DASHBOARD_IGNORE_GTK  GCONF_PATH "/dashboard_ignore_gtk_bg_fg"
#define GCONF_DASHBOARD_NO_GTK_FG  GCONF_PATH "/dashboard_no_gtk_fg"
#define GCONF_DASHBOARD_NO_GTK_BG  GCONF_PATH "/dashboard_no_gtk_bg"
#define GCONF_DASHBOARD_WIDTH  GCONF_PATH "/dashboard_width"
#define GCONF_DASHBOARD_HEIGHT  GCONF_PATH "/dashboard_height"
#define GCONF_DASHBOARD_RUN_ONCE GCONF_PATH "/runonce"
#define GCONF_DASHBOARD_SHOW_AWNDIAG GCONF_PATH "/dashboard_show_awn_diag"

static void draw_main_window(Dashboard *Dashboard);

static gboolean _Dashboard_time_handler(Dashboard *);

static void Dashboard_plugs_construct(gpointer data, gpointer user_data);

static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event,
                                 Dashboard * dashboard);
static gboolean _increase_step(GtkWidget *widget, GdkEventButton *event,
                               Dashboard_plugs_callbacks * node);
static gboolean _decrease_step(GtkWidget *widget, GdkEventButton *event,
                               Dashboard_plugs_callbacks * node);
static gboolean _remove(GtkWidget *widget, GdkEventButton *event,
                        Dashboard_plugs_callbacks * node);

static gboolean _move_(GtkWidget *widget, GdkEventButton *event,
                       Dashboard_plugs_callbacks * node);

static void _check_enabled(gpointer data, gpointer user_data);
static gboolean _dashboard_button_clicked_event(GtkWidget *widget,
    GdkEventButton *event, Dashboard  * dashboard);

static void update_pos(Dashboard_plugs_callbacks * node);
static void build_dashboard_right_click(Dashboard  * dashboard);
static gboolean _toggle_component(Dashboard_plugs_callbacks *p);


static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, Dashboard *p);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, Dashboard *p);
void _all_fixed_children(GtkFixedChild *node, Dashboard *p);
static gboolean _toggle_gtk(GtkWidget *widget, GdkEventButton *event, Dashboard *p);
static gboolean _apply_dash_colours(GtkWidget *widget, GdkEventButton *event, Dashboard *p);

/*FIXME  --- 
static void show_main_window(Dashboard *Dashboard);
static void hide_main_window(Dashboard *Dashboard);

static void set_background(Dashboard * data);*/
static void _notify_color_change_bg(Dashboard *p);
static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, gpointer data);


gboolean  _moving(GtkWidget *widget, GdkEventMotion *event, Dashboard_plugs_callbacks * node);
static void _apply_c_(gpointer data, gpointer user_data);

Dashboard_plugs_callbacks* register_Dashboard_plug(Dashboard * Dashboard,
    void * (*lookup_fn)(int),
    int x1,
    int y1,
    long flags,
    void * arb_data
                                                  )
{
  Dashboard_plugs_callbacks *node = g_malloc(sizeof(Dashboard_plugs_callbacks));
  construct_fn construct;
  GtkWidget *menu_items;
  GtkWidget *component_menu_items;
  attach_right_click_menu_fn attach_right_fn;
  get_component_name_fn   get_component_name;
  get_component_friendly_name_fn   get_component_friendly_name;
  char * comp_name = NULL;
  char * comp_friendly_name = NULL;
  GConfValue *value;
  char * keyname;
  int tmp;

  node->dashboard = Dashboard;
  node->updatepos = FALSE;
  node->container = Dashboard->mainfixed;
  node->lookup_fn = lookup_fn;
  construct = node->lookup_fn(DASHBOARD_CALLBACK_CONSTRUCT);

  if (construct)
  {
    construct(arb_data);
  }

  node->data = arb_data;

  get_component_name = node->lookup_fn(
                         DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN
                       );
  /*at this point in time I don't want any anonymous components :-) */
  assert(get_component_name);

  if (get_component_name)
  {
    comp_name = g_strdup((char *) get_component_name(node->data));
  }

  get_component_friendly_name = node->lookup_fn(

                                  DASHBOARD_CALLBACK_GET_COMPONENT_FRIENDLY_NAME_FN
                                );
  assert(get_component_friendly_name);

  if (get_component_friendly_name)
  {
    comp_friendly_name = g_strdup((char *) get_component_friendly_name(node->data));
  }

  node->enabled = (flags & 0x01 ? TRUE : FALSE);

  node->dead_but_does_not_know_it = FALSE;


  tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name) + strlen("_enabled") + 1;
  keyname = g_malloc(tmp);

  if (keyname)
  {
    strcpy(keyname, GCONF_DASHBOARD_PREFIX);
    strcat(keyname, comp_name);
    strcat(keyname, "_enabled");
    value = gconf_client_get(get_dashboard_gconf(), keyname, NULL);

    if (value)
    {
      node->enabled = gconf_client_get_bool(get_dashboard_gconf(),
                                            keyname, NULL);
    }
    else
    {
      gconf_client_set_bool(get_dashboard_gconf(), keyname,
                            node->enabled, NULL);
    }

  }

  g_free(keyname);

  node->x1 = x1;
  tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name) + strlen("_posx1-v2") + 1;
  keyname = g_malloc(tmp);

  if (keyname)
  {
    strcpy(keyname, GCONF_DASHBOARD_PREFIX);
    strcat(keyname, comp_name);
    strcat(keyname, "_posx1-v2");
    value = gconf_client_get(get_dashboard_gconf(), keyname, NULL);

    if (value)
    {
      node->x1 = gconf_client_get_int(get_dashboard_gconf(), keyname, NULL);
    }
  }

  g_free(keyname);

  node->y1 = y1;
  tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name) + strlen("_posy1-v2") + 1;
  keyname = g_malloc(tmp);

  if (keyname)
  {
    strcpy(keyname, GCONF_DASHBOARD_PREFIX);
    strcat(keyname, comp_name);
    strcat(keyname, "_posy1-v2");
    value = gconf_client_get(get_dashboard_gconf(), keyname, NULL);

    if (value)
    {
      node->y1 = gconf_client_get_int(get_dashboard_gconf(), keyname, NULL);
    }
  }

  g_free(keyname);

  g_free(comp_name);
  g_free(comp_friendly_name);
  node->widget = NULL;
  node->widge_wrap = NULL;

  node->right_click_menu = gtk_menu_new();
  gtk_menu_set_screen(GTK_MENU(node->right_click_menu), NULL);

  if (lookup_fn(DASHBOARD_CALLBACK_INCREASE_STEP_FN))
    dashboard_build_clickable_menu_item(node->right_click_menu,
                                        G_CALLBACK(_increase_step), "Larger", node
                                       );

  if (lookup_fn(DASHBOARD_CALLBACK_DECREASE_STEP_FN))
    dashboard_build_clickable_menu_item(node->right_click_menu,
                                        G_CALLBACK(_decrease_step), "Smaller", node
                                       );

  dashboard_build_clickable_menu_item(node->right_click_menu, G_CALLBACK(_move_),
                                      "Move", node
                                     );

  dashboard_build_clickable_menu_item(node->right_click_menu,
                                      G_CALLBACK(_remove), "Remove", node
                                     );

  if ((attach_right_fn = lookup_fn(DASHBOARD_CALLBACK_ATTACH_RIGHT_CLICK_MENU_FN)))
  {

    component_menu_items = attach_right_fn(node->data);
    assert(component_menu_items);
    menu_items = gtk_menu_item_new_with_label("Component");
    gtk_menu_shell_append(GTK_MENU_SHELL(node->right_click_menu),
                          menu_items);
    gtk_widget_show(menu_items);
    gtk_menu_item_set_submenu(GTK_MENU_ITEM(menu_items),
                              component_menu_items);
  }

  Dashboard->Dashboard_plugs = g_slist_prepend(Dashboard->Dashboard_plugs, node);

  build_dashboard_right_click(Dashboard);

  return node;
}


void register_Dashboard(Dashboard * dashboard, AwnApplet *applet)
{
  GdkScreen* pScreen;
//    int width,height;
  gchar *svalue;
  GConfValue *value;

  dashboard->rounded = TRUE;          /*FIXME make configurable*/
  dashboard->move_widget = NULL;


  value = gconf_client_get(get_dashboard_gconf(), GCONF_DASHBOARD_SHOW_AWNDIAG , NULL);

  if (value)
  {
    dashboard->show_awn_dialog = gconf_client_get_bool(get_dashboard_gconf(), GCONF_DASHBOARD_SHOW_AWNDIAG , NULL);
  }
  else
  {
    dashboard->show_awn_dialog = TRUE;
    gconf_client_set_bool(get_dashboard_gconf(), GCONF_DASHBOARD_SHOW_AWNDIAG, dashboard->show_awn_dialog , NULL);
  }


  value = gconf_client_get(get_dashboard_gconf(), GCONF_DASHBOARD_IGNORE_GTK , NULL);

  if (value)
  {
    dashboard->ignore_gtk = gconf_client_get_bool(get_dashboard_gconf(), GCONF_DASHBOARD_IGNORE_GTK , NULL);
  }
  else
  {
    dashboard->ignore_gtk = FALSE;
    gconf_client_set_bool(get_dashboard_gconf(), GCONF_DASHBOARD_IGNORE_GTK, dashboard->ignore_gtk , NULL);
  }

  if (value)
  {
    int ver;
    value = gconf_client_get(get_dashboard_gconf(), GCONF_DASHBOARD_RUN_ONCE , NULL);

    if (value)
    {
      ver = gconf_client_get_int(get_dashboard_gconf(), GCONF_DASHBOARD_RUN_ONCE , NULL);
    }

    if (ver != 1)
    {
      quick_message("This message will only appear once.\nIt appears that this may be an upgrade from an older version.\n  If there are any display issues please run\n 'gconftool-2 --recursive-unset /apps/avant-window-navigator/applets/awn-system-monitor'\n  and then restart the applet.", GTK_WIDGET(applet));

    }
  }

  gconf_client_set_int(get_dashboard_gconf(), GCONF_DASHBOARD_RUN_ONCE , 1, NULL);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_BG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_BG, svalue = g_strdup("999999d4"), NULL);
  }

  awn_cairo_string_to_color(svalue, &dashboard->bg);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_FG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_FG, svalue = g_strdup("FFFFFFBB"), NULL);
  }

  awn_cairo_string_to_color(svalue, &dashboard->fg);

  g_free(svalue);



  dashboard->updateinterval = DASHBOARD_TIMER_FREQ;
  dashboard->force_update = FALSE;
  dashboard->applet = applet;
  dashboard->Dashboard_plugs = NULL;   /*there are no plugs registered yet*/

  dashboard->mainwindow = awn_dialog_new_for_widget (GTK_WIDGET(applet));

  dashboard->right_click_menu = NULL;

  gtk_window_set_focus_on_map(GTK_WINDOW(dashboard->mainwindow), TRUE);
  dashboard->mainfixed =  gtk_fixed_new();
  gtk_container_add(GTK_CONTAINER(dashboard->mainwindow), dashboard->mainfixed);
  gtk_fixed_set_has_window(GTK_FIXED(dashboard->mainfixed), FALSE);
  pScreen = gtk_widget_get_screen(dashboard->mainwindow);
  g_signal_connect(G_OBJECT(dashboard->mainwindow), "focus-out-event",
                   G_CALLBACK(_focus_out_event), (gpointer)dashboard);
  g_timeout_add_full(G_PRIORITY_DEFAULT, dashboard->updateinterval,
                     (GSourceFunc)_Dashboard_time_handler, (gpointer)dashboard
                     , NULL
                    );
  build_dashboard_right_click(dashboard);
  g_signal_connect(G_OBJECT(dashboard->mainwindow), "button-press-event",
                   G_CALLBACK(_dashboard_button_clicked_event),
                   (gpointer)dashboard
                  );

  if (!dashboard->show_awn_dialog)
  {
    dashboard->expose_handler_id = g_signal_connect(G_OBJECT(dashboard->mainwindow),
                                   "expose-event", G_CALLBACK(_expose_event), dashboard);
  }
  else
  {
    dashboard->expose_handler_id = g_signal_connect(G_OBJECT(dashboard->mainfixed),
                                   "expose-event", G_CALLBACK(_expose_event), dashboard);
  }

}


static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
  cairo_t *cr;
  Dashboard *dashboard = data;

//        gtk_container_propagate_expose(dashboard->mainwindow,dashboard->mainfixed,expose);

  if (!dashboard->show_awn_dialog)
  {
    cr = gdk_cairo_create(dashboard->mainwindow->window);

    cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(cr);
    cairo_set_source_rgba(cr, dashboard->bg.red, dashboard->bg.green, dashboard->bg.blue, dashboard->bg.alpha);
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);

    if (dashboard->rounded)
    {
      awn_cairo_rounded_rect(cr, 5, 5, widget->allocation.width - 10, widget->allocation.height - 10, 20, ROUND_ALL);
      cairo_fill(cr);
    }

    cairo_destroy(cr);

    gtk_widget_send_expose(dashboard->mainfixed, (GdkEvent*)expose);
    return TRUE;
  }
  else
  {
    cr = gdk_cairo_create(dashboard->mainfixed->window);
    cairo_set_source_rgba(cr, dashboard->bg.red, dashboard->bg.green, dashboard->bg.blue, dashboard->bg.alpha);
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
    awn_cairo_rounded_rect(cr, 5, 5, widget->allocation.width + 10, widget->allocation.height + 10, 10, ROUND_ALL);
    cairo_fill(cr);
    cairo_destroy(cr);
  }

  return FALSE;


}

void toggle_Dashboard_window(Dashboard *dashboard)
{
  if (GTK_WIDGET_VISIBLE(dashboard->mainwindow))
  {
    gtk_widget_hide(dashboard->mainwindow);
  }
  else
  {
    if (dashboard->mainwindow)
    {
      gtk_widget_show_all(dashboard->mainwindow);
    }
  }
}

static gboolean _toggle_component(Dashboard_plugs_callbacks *p)
{
  get_component_name_fn   get_component_name;
  char * comp_name = NULL;
  char * keyname;
  int tmp;

  p->enabled = !p->enabled;

  if (p->enabled)
  {
    if (p->widge_wrap);

    gtk_widget_show_all(p->widge_wrap);
  }

  get_component_name = p->lookup_fn(DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN);

  if (get_component_name)
  {
    comp_name = g_strdup((char *) get_component_name(p->data));
  }

  tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name) + strlen("_enabled") + 1;

  keyname = g_malloc(tmp);

  if (keyname)
  {
    strcpy(keyname, GCONF_DASHBOARD_PREFIX);
    strcat(keyname, comp_name);
    strcat(keyname, "_enabled");
    gconf_client_set_bool(get_dashboard_gconf(), keyname, p->enabled, NULL);
  }

  g_free(keyname);

  g_free(comp_name);

  return TRUE; /* FIXME?! */
}

static void _notify_color_change_fg(Dashboard *p)
{
  /*FIXME */

}


static void _apply_c_(gpointer data, gpointer user_data)
{
  Dashboard_plugs_callbacks * node = data;
  Dashboard *dashboard = user_data;

  set_bg_fn bg_fn = node->lookup_fn(DASHBOARD_CALLBACK_SET_BG);
  bg_fn(&dashboard->bg, node->data);
  set_fg_fn fg_fn = node->lookup_fn(DASHBOARD_CALLBACK_SET_FG);
  fg_fn(&dashboard->fg, node->data);
}

static gboolean _apply_dash_colours(GtkWidget *widget, GdkEventButton *event, Dashboard *p)
{
  g_slist_foreach(p->Dashboard_plugs, _apply_c_ , p);
  return TRUE;
}

static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, Dashboard *p)
{

  char *svalue;

  if (p->ignore_gtk)
  {
    pick_awn_color(&p->fg, "Foreground Colour" , p, (DashboardNotifyColorChange)_notify_color_change_fg);
    svalue = dashboard_cairo_colour_to_string(&p->fg);
    gconf_client_set_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_FG, svalue , NULL);

    //    gtk_widget_modify_base(windata->win,GTK_STATE_SELECTED,&bg);
    //        gtk_widget_modify_base(windata->win,GTK_STATE_NORMAL,&bg);
    free(svalue);
  }

  return TRUE;
}

static void _notify_color_change_bg(Dashboard *p)
{


}


static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, Dashboard *p)
{
  char *svalue;

  if (p->ignore_gtk)
  {
    pick_awn_color(&p->bg, "Background Colour" , p, (DashboardNotifyColorChange)_notify_color_change_bg);
    svalue = dashboard_cairo_colour_to_string(&p->bg);
    gconf_client_set_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_BG, svalue , NULL);
    free(svalue);
  }

  return TRUE;
}

static gboolean _toggle_gtk(GtkWidget *widget, GdkEventButton *event, Dashboard *p)
{
  char *svalue;

  p->ignore_gtk = !p->ignore_gtk;

  if (!p->ignore_gtk)
  {
    set_bg_rbg(&p->mainwindow->style->base[0]);
    set_fg_rbg(&p->mainwindow->style->fg[0]);
    get_fg_rgba_colour(&p->fg);
    get_bg_rgba_colour(&p->bg);
  }

  gconf_client_set_bool(get_dashboard_gconf(), GCONF_DASHBOARD_IGNORE_GTK , p->ignore_gtk, NULL);

  svalue = dashboard_cairo_colour_to_string(&p->bg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_BG, svalue , NULL);
  free(svalue);

  svalue = dashboard_cairo_colour_to_string(&p->fg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_DASHBOARD_NO_GTK_FG, svalue , NULL);
  free(svalue);

  _expose_event(p->mainfixed, NULL, p);
  return TRUE;
}


static gboolean _enable_component(GtkWidget *widget, GdkEventButton *event,
                                  Dashboard_plugs_callbacks *p)
{
  _toggle_component(p);
  return TRUE;
}

static void _check_enabled(gpointer data, gpointer user_data)
{
  Dashboard_plugs_callbacks * node = data;
  Dashboard * dashboard = user_data;
  get_component_friendly_name_fn get_component_friendly_name;
  gchar * sname;

  if (!node->enabled)
  {

    get_component_friendly_name = node->lookup_fn(
                                    DASHBOARD_CALLBACK_GET_COMPONENT_FRIENDLY_NAME_FN
                                  );
    assert(get_component_friendly_name);
    sname = g_strdup(get_component_friendly_name(node->data));
    dashboard_build_clickable_menu_item(dashboard->right_click_menu,
                                        G_CALLBACK(_enable_component), sname, node
                                       );
    g_free(sname);
  }

}

static gboolean _toggle_awn_diag(GtkWidget *widget, GdkEventButton *event, Dashboard *p)
{
//    p->show_awn_dialog=!p->show_awn_dialog;
  gtk_widget_hide(p->mainwindow);
#if 0

  if (p->show_awn_dialog)
  {
    g_signal_handler_disconnect(G_OBJECT(p->mainfixed), p->expose_handler_id);
    p->expose_handler_id = g_signal_connect(G_OBJECT(p->mainwindow),
                                            "expose-event", G_CALLBACK(_expose_event), p);
  }
  else
  {
    g_signal_handler_disconnect(G_OBJECT(p->mainwindow), p->expose_handler_id);
    p->expose_handler_id = g_signal_connect(G_OBJECT(p->mainfixed),
                                            "expose-event", G_CALLBACK(_expose_event), p);
  }

#else
  quick_message("This change will not be reflected until the applet is restarted.", p->mainwindow);

#endif
  gconf_client_set_bool(get_dashboard_gconf(), GCONF_DASHBOARD_SHOW_AWNDIAG, !p->show_awn_dialog , NULL);

  return TRUE;
}


static void build_dashboard_right_click(Dashboard  * dashboard)
{
  if (dashboard->right_click_menu)
    gtk_widget_destroy(dashboard->right_click_menu);

  dashboard->right_click_menu = gtk_menu_new();

  dashboard_build_clickable_check_menu_item(dashboard->right_click_menu,
      G_CALLBACK(_toggle_awn_diag), "Display Awn Dialog", dashboard, dashboard->show_awn_dialog);

  dashboard_build_clickable_check_menu_item(dashboard->right_click_menu,
      G_CALLBACK(_toggle_gtk), "Gtk Colours", dashboard, !dashboard->ignore_gtk);


  dashboard_build_clickable_menu_item(dashboard->right_click_menu, G_CALLBACK(_set_fg), "Foreground", dashboard);

  dashboard_build_clickable_menu_item(dashboard->right_click_menu, G_CALLBACK(_set_bg), "Background", dashboard);

  dashboard_build_clickable_menu_item(dashboard->right_click_menu, G_CALLBACK(_apply_dash_colours), "Propagate", dashboard);

  g_slist_foreach(dashboard->Dashboard_plugs, _check_enabled, dashboard);

}

static gboolean _dashboard_button_clicked_event(GtkWidget *widget,
    GdkEventButton *event, Dashboard  * dashboard)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;
  enable_suppress_hide_main();

  if (event->button == 3)
  {
    gtk_menu_popup(GTK_MENU(dashboard->right_click_menu), NULL, NULL, NULL, NULL,
                   event_button->button, event_button->time);
    return TRUE;
  }
  else if (event->button == 1)
  {
    if (dashboard->move_widget)
    {

      dashboard->move_widget->x1 = event->x - 10;
      dashboard->move_widget->y1 = event->y - 10;
      update_pos(dashboard->move_widget);
      dashboard->move_widget->updatepos = TRUE;
      dashboard->move_widget = NULL;
    }

    return TRUE;
  }

  return FALSE;
}

static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event,
                                      Dashboard_plugs_callbacks * node)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;
  enable_suppress_hide_main();

  if (event->button == 3)
  {
    gtk_menu_popup(GTK_MENU(node->right_click_menu), NULL, NULL, NULL, NULL,
                   event_button->button, event_button->time);
    return TRUE;
  }

  return FALSE;
}


static gboolean _increase_step(GtkWidget *widget, GdkEventButton *event,
                               Dashboard_plugs_callbacks * node)
{
  increase_step_fn increase = node->lookup_fn(
                                DASHBOARD_CALLBACK_INCREASE_STEP_FN);
  assert(increase);

  increase(node->data);
  return TRUE;
}

static gboolean _decrease_step(GtkWidget *widget, GdkEventButton *event,
                               Dashboard_plugs_callbacks * node)
{
  increase_step_fn decrease = node->lookup_fn(
                                DASHBOARD_CALLBACK_DECREASE_STEP_FN);
  assert(decrease);
  decrease(node->data);
  return TRUE;
}

static gboolean _remove(GtkWidget *widget, GdkEventButton *event,
                        Dashboard_plugs_callbacks * node)
{
  node->dead_but_does_not_know_it = TRUE;
  return TRUE;
}

static void update_pos(Dashboard_plugs_callbacks * node)
{
  get_component_name_fn   get_component_name;
  char * comp_name = NULL;
  char * keyname;
  int tmp;

  get_component_name = node->lookup_fn(DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN);

  if (get_component_name)
  {
    comp_name = (char *) get_component_name(node->data);
  }

  tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name) + strlen("_posx1-v2") + 1;

  keyname = g_malloc(tmp);

  if (keyname)
  {
    strcpy(keyname, GCONF_DASHBOARD_PREFIX);
    strcat(keyname, comp_name);
    strcat(keyname, "_posx1-v2");
    gconf_client_set_int(get_dashboard_gconf(), keyname, node->x1, NULL);
  }

  g_free(keyname);

  tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name) + strlen("_posy1-v2") + 1;
  keyname = g_malloc(tmp);

  if (keyname)
  {
    strcpy(keyname, GCONF_DASHBOARD_PREFIX);
    strcat(keyname, comp_name);
    strcat(keyname, "_posy1-v2");
    gconf_client_set_int(get_dashboard_gconf(), keyname, node->y1, NULL);
  }

  g_free(keyname);


}


static gboolean _move_(GtkWidget *widget, GdkEventButton *event,
                       Dashboard_plugs_callbacks * node)
{
  Dashboard * dashboard = node->dashboard;
  dashboard->move_widget = node;
  return TRUE;
}



static void Dashboard_plugs_construct(gpointer data, gpointer user_data)
{

  Dashboard_plugs_callbacks * node = data;
  Dashboard *dashboard = user_data;
  GtkWidget *old_widget = NULL;

  if (!node->enabled)
  {
    if (node->widge_wrap)
      gtk_widget_hide_all(node->widge_wrap);

    return;
  }

  if (node->dead_but_does_not_know_it)
  {
    gtk_widget_hide_all(node->widge_wrap);
    _toggle_component(node);
    node->dead_but_does_not_know_it = FALSE;
    build_dashboard_right_click(dashboard);
    return;
  }

  render_fn render = node->lookup_fn(DASHBOARD_CALLBACK_RENDER);

  if (render)
  {
    if ((dashboard->need_win_update = render(&node->widget,
                                            dashboard->updateinterval, node->data
                                           )))
    {

      if (node->widge_wrap)
      {
        old_widget = node->widge_wrap;
      }
      else
      {
        build_dashboard_right_click(dashboard);
      }

      node->widge_wrap = gtk_event_box_new();

      gtk_event_box_set_visible_window(GTK_EVENT_BOX(node->widge_wrap), FALSE);
      gtk_container_add(GTK_CONTAINER(node->widge_wrap), node->widget);
      g_signal_connect(G_OBJECT(node->widge_wrap), "button-press-event",
                       G_CALLBACK(_button_clicked_event), (gpointer)node
                      );

      gtk_fixed_put(GTK_FIXED(dashboard->mainfixed), node->widge_wrap, node->x1, node->y1);

      if (old_widget)
      {
        gtk_widget_hide(old_widget);
        gtk_widget_destroy(old_widget);
      }

      assert(node->widge_wrap);

      gtk_widget_show_all(node->widge_wrap);
    }

    if (node->updatepos)
      gtk_fixed_move(GTK_FIXED(dashboard->mainfixed), node->widge_wrap, node->x1, node->y1);
  }
}


static void dashboard_ticks(gpointer data, gpointer user_data)
{
  Dashboard_plugs_callbacks * node = data;
  Dashboard *dashboard = user_data;
  tick_fn tick;

  if (!node->enabled)
  {
    return;
  }

  tick = node->lookup_fn(DASHBOARD_CALLBACK_TICK);

  if (tick)
  {
    tick(node->data , dashboard->updateinterval);
  }
}

static gboolean _Dashboard_time_handler(Dashboard * Dashboard)
{
  static gboolean    in_handler = FALSE;

  if (in_handler)
  {        /*FIXME - I actually don't think glib will let this happen.*/
    return TRUE;
  }

  in_handler = TRUE;

  if ((GTK_WIDGET_VISIBLE(Dashboard->mainwindow)))
  {
    draw_main_window(Dashboard);
  }

  in_handler = FALSE;

  return TRUE;
}


/************Section:  main window events-------------*/

static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event,
                                 Dashboard * dashboard)
{
  if (!get_suppress_hide_main())
  {
    if (gdk_window_get_window_type(event->window) != GDK_WINDOW_TEMP)
    {
      AwnConfigClient *client = awn_config_client_new();
      if (awn_config_client_get_bool(client, "shared", "dialog_focus_loss_behavior", NULL))
      {
        gtk_widget_hide(dashboard->mainwindow);
      }
    }
  }

  disable_suppress_hide_main();

  return TRUE;
}

/*

-draws the main window.
-interates though the list of dashboard plugs and they draw their widgets.

*/
static void draw_main_window(Dashboard *dashboard)
{
  if (!dashboard->ignore_gtk)
  {
    static gboolean doneonce = FALSE;
    set_bg_rbg(&dashboard->mainwindow->style->base[0]);
    set_fg_rbg(&dashboard->mainwindow->style->fg[0]);
    get_fg_rgba_colour(&dashboard->fg);
    get_bg_rgba_colour(&dashboard->bg);
    if (!doneonce)
    {
      _apply_dash_colours(NULL, NULL, dashboard);
      doneonce = TRUE;
    }
    /*FIXME - decide if forcing propagation of gtk colours is good.
    right no choosing no */
//        g_slist_foreach(dashboard->Dashboard_plugs,_apply_c_ ,dashboard);
  }

  /*have dashboard plugs that have registered draw their widgets*/
  dashboard->need_win_update = FALSE;

  g_slist_foreach(dashboard->Dashboard_plugs, Dashboard_plugs_construct, dashboard);

  g_slist_foreach(dashboard->Dashboard_plugs, dashboard_ticks, dashboard);

  /*we're done laying out the damn thing - let's show it*/

  gtk_widget_show(dashboard->mainwindow);


}






