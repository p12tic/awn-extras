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

#include <libawn/awn-applet.h>
#include <glib/gmacros.h>
#include <glib/gerror.h>
#include <gconf/gconf-value.h>

#include <libawn/awn-applet-dialog.h>
#include <libawn/awn-applet-simple.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <gdk/gdk.h>
#include <string.h>


#include <glibtop/mem.h>
#include <glibtop/cpu.h>


#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-title.h>



#include "cpu_component.h"
#include "dashboard_util.h"
#include "dashboard.h"
#include "config.h"
#include "gconf-config.h"
#define GCONF_CPU_REFRESH GCONF_PATH  "/component_cpu_refresh_rate"
#define GCONF_CPU_METER GCONF_PATH  "/component_cpu_shiny_meter"
#define GCONF_CPU_SIZE_MULT GCONF_PATH  "/component_cpu_scale"
#define GCONF_CPU_METER_START_COLOUR GCONF_PATH  "/component_cpu_meter_start_c"
#define GCONF_CPU_METER_STOP_COLOUR GCONF_PATH  "/component_cpu_meter_end_c"
#define GCONF_CPU_METER_MIDDLE_COLOUR GCONF_PATH  "/component_cpu_meter_middle_c"
#define GCONF_CPU_METER_USE_2_COLOUR_GRADIENT GCONF_PATH "/component_cpu_use_2_colour_gradient"

#define GCONF_CPU_METER_NO_GTK_FG  GCONF_PATH "/component_cpu_fg"
#define GCONF_CPU_METER_NO_GTK_BG  GCONF_PATH "/component_cpu_bg"

//#undef NDEBUG
#include <assert.h>

typedef struct
{
  double max_width_left;
  double max_width_right;
  double width;
  double height;
  double move_down;
  int timer;
  int refresh;
  long     accum_user, accum_sys, accum_idle, accum_iowait ;
  float user;
  float  sys;
  float idle;
  float iowait;
  float size_mult;
  cairo_pattern_t *pats[4];
  gboolean shiny_graphs;
  AwnColor colour_meter_start;
  AwnColor colour_meter_end;
  AwnColor colour_meter_middle;
  gboolean two_colour_gradient;
  AwnColor    bg;             /*colours if gtk colours are overridden */
  AwnColor    fg;
  gboolean    emotive_text;
}CPU_plug_data;

static gboolean render(GtkWidget ** pwidget, gint interval, CPU_plug_data **p);
static gboolean query_support_multiple(void);
static void destruct(CPU_plug_data **p);
static void construct(CPU_plug_data **p);
static gboolean decrease_step(CPU_plug_data **p);
static gboolean increase_step(CPU_plug_data **p);
static GtkWidget* attach_right_click_menu(CPU_plug_data **p);
static const char* get_component_name(void *);
static const char* get_component_friendly_name(void *);

static gboolean _toggle_2_gradient(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _toggle_shiny(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);

static gboolean _set_100(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_200(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_500(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_1000(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_5000(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);

static gboolean _set_good(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_bad(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_middling(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p);

static void set_colour_gradient(CPU_plug_data *p, AwnColor* colour, const char * mess, const char * gconf_key);

static void _notify_color_change(void *);

static void _fn_set_bg(AwnColor * new_bg, CPU_plug_data **p);
static void _fn_set_fg(AwnColor * new_fg, CPU_plug_data **p);


static void * plug_fns[MAX_CALLBACK_FN] =
{
  construct,
  destruct,
  render,
  query_support_multiple,
  NULL,
  increase_step,
  decrease_step,
  attach_right_click_menu,
  get_component_name,
  get_component_friendly_name,
  _fn_set_bg,
  _fn_set_fg,
  NULL
};


void * cpu_plug_lookup(int fn_id)
{
  assert(fn_id < MAX_CALLBACK_FN);
  return plug_fns[fn_id];
}

static void _fn_set_bg(AwnColor * new_bg, CPU_plug_data **p)
{
  char *svalue;
  CPU_plug_data  * plug_data = *p;
  plug_data->bg = *new_bg;
  svalue = dashboard_cairo_colour_to_string(new_bg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_NO_GTK_BG, svalue , NULL);
  free(svalue);
}


static void _fn_set_fg(AwnColor * new_fg, CPU_plug_data **p)
{
  char *svalue;
  CPU_plug_data  * plug_data = *p;
  plug_data->fg = *new_fg;
  svalue = dashboard_cairo_colour_to_string(new_fg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_NO_GTK_FG, svalue , NULL);
  free(svalue);
}


static const char* get_component_name(void *d)
{
  const char * name = "component_cpu";
  return name;
}

static const char* get_component_friendly_name(void *d)
{
  const char * name = "CPU Stats";
  return name;
}



static GtkWidget* attach_right_click_menu(CPU_plug_data **p)
{
  CPU_plug_data * plug_data = *p;
  GtkWidget * menu_items;
  GtkWidget *menu = gtk_menu_new();
//    GtkWidget *graphs_sub_menu = gtk_menu_new ();
  GtkWidget *graphs_refresh_menu = gtk_menu_new();
  GtkWidget *graphs_colour_menu = gtk_menu_new();

  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_shiny), "Shiny On/Off", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_fg), "Foreground", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_bg), "Background", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_2_gradient), "2 Colour Gradient", plug_data);
  dashboard_build_clickable_menu_item(graphs_refresh_menu, G_CALLBACK(_set_100), "100ms", plug_data);
  dashboard_build_clickable_menu_item(graphs_refresh_menu, G_CALLBACK(_set_200), "200ms", plug_data);
  dashboard_build_clickable_menu_item(graphs_refresh_menu, G_CALLBACK(_set_500), "500ms", plug_data);
  dashboard_build_clickable_menu_item(graphs_refresh_menu, G_CALLBACK(_set_1000), "1000ms", plug_data);
  dashboard_build_clickable_menu_item(graphs_refresh_menu, G_CALLBACK(_set_5000), "5000ms", plug_data);
  menu_items = gtk_menu_item_new_with_label("Refresh");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menu_items);
  gtk_menu_item_set_submenu(menu_items, graphs_refresh_menu);
  gtk_widget_show(menu_items);
  dashboard_build_clickable_menu_item(graphs_colour_menu, G_CALLBACK(_set_good), "Good", plug_data);
  dashboard_build_clickable_menu_item(graphs_colour_menu, G_CALLBACK(_set_middling), "Middling", plug_data);
  dashboard_build_clickable_menu_item(graphs_colour_menu, G_CALLBACK(_set_bad), "Bad", plug_data);
  gtk_widget_show(menu_items);
  menu_items = gtk_menu_item_new_with_label("Meter Colours");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menu_items);
  gtk_menu_item_set_submenu(menu_items, graphs_colour_menu);
  gtk_widget_show(menu_items);
  return menu;

}

static gboolean _toggle_shiny(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  p->shiny_graphs = !p->shiny_graphs;
  gconf_client_set_bool(get_dashboard_gconf(), GCONF_CPU_METER, p->shiny_graphs, NULL);
  return TRUE;
}

static gboolean _toggle_2_gradient(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  p->two_colour_gradient = !p->two_colour_gradient;
  gconf_client_set_bool(get_dashboard_gconf(), GCONF_CPU_METER_USE_2_COLOUR_GRADIENT, p->two_colour_gradient, NULL);
  _notify_color_change(p);
  return TRUE;
}

static gboolean set_refresh(CPU_plug_data *p, int val)
{
  p->refresh = val;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_CPU_REFRESH, p->refresh, NULL);
  return TRUE;
}

static gboolean _set_100(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  return set_refresh(p, 100);
}

static gboolean _set_200(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  return set_refresh(p, 200);
}

static gboolean _set_500(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  return set_refresh(p, 500);
}

static gboolean _set_1000(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  return set_refresh(p, 1000);
}

static gboolean _set_5000(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  return set_refresh(p, 5000);
}


static void _notify_color_change(void *p)
{
  CPU_plug_data *data = p;
  assert(p);
  data->max_width_left = -1;
}


static void set_colour_gradient(CPU_plug_data *p, AwnColor* colour, const char * mess, const char * gconf_key)
{
  char *svalue;
  enable_suppress_hide_main();
  pick_awn_color(colour, mess, p, _notify_color_change);
  svalue = dashboard_cairo_colour_to_string(colour);
  gconf_client_set_string(get_dashboard_gconf(), gconf_key, svalue , NULL);
  free(svalue);

}


static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  set_colour_gradient(p, &p->fg, "Foreground Colour if Ignore gtk", GCONF_CPU_METER_NO_GTK_FG);
  return TRUE;
}

static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  set_colour_gradient(p, &p->bg, "Foreground Colour if Ignore gtk", GCONF_CPU_METER_NO_GTK_BG);
  return TRUE;
}


static gboolean _set_good(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  set_colour_gradient(p, &p->colour_meter_start, "Changing Good Colour", GCONF_CPU_METER_START_COLOUR);
  return TRUE;
}


static gboolean _set_bad(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  set_colour_gradient(p, &p->colour_meter_end, "Changing Bad Colour", GCONF_CPU_METER_STOP_COLOUR);
  return TRUE;
}

static gboolean _set_middling(GtkWidget *widget, GdkEventButton *event, CPU_plug_data *p)
{
  set_colour_gradient(p, &p->colour_meter_middle, "Changing Middle Colour", GCONF_CPU_METER_MIDDLE_COLOUR);
  return TRUE;
}

static gboolean decrease_step(CPU_plug_data **p)
{
  CPU_plug_data *data = *p;
  data->size_mult = data->size_mult * 5.0 / 6.0;
  data->max_width_left = -1;
  gconf_client_set_float(get_dashboard_gconf(), GCONF_CPU_SIZE_MULT, data->size_mult, NULL);
  return TRUE;
}

static gboolean increase_step(CPU_plug_data **p)
{
  CPU_plug_data *data = *p;
  data->size_mult = data->size_mult  * 1.2;
  data->max_width_left = -1;
  gconf_client_set_float(get_dashboard_gconf(), GCONF_CPU_SIZE_MULT, data->size_mult, NULL);
  return TRUE;
}



static gboolean query_support_multiple(void)
{
  return FALSE;
}

static void construct(CPU_plug_data **p)
{
  GConfValue *value;
  *p = g_malloc(sizeof(CPU_plug_data));
  CPU_plug_data * data = *p;
  gchar * svalue;
  data->max_width_left = -1;
  data->max_width_right = -1;
  data->timer = 100;
  data->user = 0;
  data->sys = 0;
  data->idle = 100;
  data->iowait = 0;

  data->emotive_text = FALSE;

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_CPU_METER_NO_GTK_BG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_NO_GTK_BG, svalue = g_strdup("999999ee"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->bg);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_CPU_METER_NO_GTK_FG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_NO_GTK_FG, svalue = g_strdup("000000ff"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->fg);

  g_free(svalue);

  value = gconf_client_get(get_dashboard_gconf(), GCONF_CPU_SIZE_MULT, NULL);

  if (value)
  {
    data->size_mult = gconf_client_get_float(get_dashboard_gconf(), GCONF_CPU_SIZE_MULT, NULL);
  }
  else
  {
    data->size_mult = 1.72;
    gconf_client_set_float(get_dashboard_gconf(), GCONF_CPU_SIZE_MULT, data->size_mult, NULL);
  }

  value = gconf_client_get(get_dashboard_gconf(), GCONF_CPU_REFRESH, NULL);

  if (value)
  {
    data->refresh = gconf_client_get_int(get_dashboard_gconf(), GCONF_CPU_REFRESH, NULL);
  }
  else
  {
    data->refresh = 500;
    set_refresh(p, data->refresh);
  }

  value = gconf_client_get(get_dashboard_gconf(), GCONF_CPU_METER, NULL);

  if (value)
  {
    data->shiny_graphs = gconf_client_get_bool(get_dashboard_gconf(), GCONF_CPU_METER, NULL);
  }
  else
  {
    data->shiny_graphs = TRUE;
    gconf_client_set_bool(get_dashboard_gconf(), GCONF_CPU_METER,
                          data->shiny_graphs, NULL);
  }

  value = gconf_client_get(get_dashboard_gconf(), GCONF_CPU_METER_USE_2_COLOUR_GRADIENT    , NULL);

  if (value)
  {
    data->two_colour_gradient = gconf_client_get_bool(get_dashboard_gconf(), GCONF_CPU_METER_USE_2_COLOUR_GRADIENT    , NULL);
  }
  else
  {
    data->two_colour_gradient = FALSE;
    gconf_client_set_bool(get_dashboard_gconf(), GCONF_CPU_METER_USE_2_COLOUR_GRADIENT, data->two_colour_gradient, NULL);
  }

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_CPU_METER_START_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_START_COLOUR, svalue = g_strdup("00FF10bb"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colour_meter_start);

  g_free(svalue);
  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_CPU_METER_MIDDLE_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_MIDDLE_COLOUR, svalue = g_strdup("EEC83177"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colour_meter_middle);

  g_free(svalue);
  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_CPU_METER_STOP_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_CPU_METER_STOP_COLOUR, svalue = g_strdup("FF0010ee"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colour_meter_end);

  g_free(svalue);
  //data->pats[] is initialized once i render.. then needs to be free'd in constructor

}

static void destruct(CPU_plug_data **p)
{
  CPU_plug_data *data = *p;
  int i;

  for (i = 0;i < 4;i++)
  {
    cairo_pattern_destroy(data->pats[i]);
  }

  g_free(*p);
}

static gboolean render(GtkWidget ** pwidget, gint interval, CPU_plug_data **p)
{
  CPU_plug_data * data = *p;
  char buf[256];
  glibtop_cpu         cpu;

  float old_user, old_sys, old_idle, old_iowait;
  dashboard_cairo_widget c_widge;
  char * content[2][4];
  int i;
  cairo_text_extents_t    extents;
  double x, y;
  float cpu_mult;

  data->timer = data->timer - interval;

  if (data->timer <= 0)
  {
    cpu_mult = (1000.0 / data->refresh);
    glibtop_get_cpu(&cpu);      //could as easily do this in render icon.  seems more appropriate here.     FIXME

    old_user = data->user;
    data->user = (cpu.user - data->accum_user) * cpu_mult;
    data->accum_user = cpu.user;

    old_sys = data->sys;
    data->sys = (cpu.sys - data->accum_sys) * cpu_mult;
    data->accum_sys = cpu.sys;

    old_idle = data->idle;
    data->idle = (cpu.idle - data->accum_idle) * cpu_mult;
    data->accum_idle = cpu.idle;

    old_iowait = data->iowait;
    data->iowait = (cpu.iowait - data->accum_iowait) * cpu_mult ;
    data->accum_iowait = cpu.iowait;

    data->user = (data->user > 100) ? (100 + old_user) / 2 : (data->user + old_user) / 2;
    data->sys = (data->sys > 100) ? (100 + old_sys) / 2 : (data->sys + old_sys) / 2;
    data->idle = (data->idle > 100) ? (100 + old_idle) / 2 : (data->idle + old_idle) / 2;
    data->iowait = (data->iowait > 100) ? (100 + old_iowait) / 2 : (data->iowait + old_iowait) / 2;

    if (data->user + data->sys + data->idle + data->iowait > 102)
    {
      data->idle = old_idle;
      data->sys = old_sys;
      data->user = old_user;
      data->iowait = old_iowait;
    }

    content[0][0] = strdup("User");

    content[0][1] = strdup("Sys");
    content[0][2] = strdup("Wait");
    content[0][3] = strdup("Idle");

    snprintf(buf, sizeof(buf), "%3.1f%%", data->user);
    content[1][0] = strdup(buf);

    snprintf(buf, sizeof(buf), "%3.1f%%", data->sys);
    content[1][1] = strdup(buf);

    snprintf(buf, sizeof(buf), "%3.1f%%", data->iowait);
    content[1][2] = strdup(buf);

    snprintf(buf, sizeof(buf), "%3.1f%%", data->idle);
    content[1][3] = strdup(buf);

goto_bad_heheh:

    if (data->max_width_left < 0)
    {
      *pwidget = get_cairo_widget(&c_widge, dashboard_get_font_size(DASHBOARD_FONT_SMALL) * 9 * data->size_mult, dashboard_get_font_size(DASHBOARD_FONT_SMALL) * 4 * data->size_mult);
      use_bg_rgba_colour(c_widge.cr);
      cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(c_widge.cr);
    }
    else
    {
      *pwidget = get_cairo_widget(&c_widge, data->width, data->height);
      cairo_rectangle(c_widge.cr, 0, 0, data->width, data->height);

      cairo_set_source_rgba(c_widge.cr, data->bg.red, data->bg.green, data->bg.blue, data->bg.alpha);

      cairo_fill(c_widge.cr);
    }

    cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);

    cairo_set_font_size(c_widge.cr, dashboard_get_font_size(DASHBOARD_FONT_SMALL)*data->size_mult);


    cairo_set_source_rgba(c_widge.cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);

    cairo_move_to(c_widge.cr, 10.0*data->size_mult, 15.0*data->size_mult);

    if (data->max_width_left < 0)
    {
      for (i = 0;i < 4;i++)
      {
        cairo_text_extents(c_widge.cr, content[0][i], &extents);

        if (extents.width > data->max_width_left)
        {
          data->max_width_left = extents.width;
        }

      }

      data->move_down = extents.height * 1.4;

      for (i = 0;i < 4;i++)
      {
        cairo_text_extents(c_widge.cr, content[1][i], &extents);

        if (extents.width > data->max_width_right)
        {
          data->max_width_right = extents.width;
        }
      }

      data->width = (data->max_width_right + data->max_width_left) * 1.25 + 100 * data->size_mult;

      data->height = extents.height * 6.8;
      del_cairo_widget(&c_widge);
      y = dashboard_get_font_size(DASHBOARD_FONT_SMALL) * data->size_mult ;
      data->pats[0] = cairo_pattern_create_linear(data->width - 100 * data->size_mult, y - data->move_down * 0.8, data->width, data->move_down * 0.6);
      cairo_pattern_add_color_stop_rgba(data->pats[0], 0, data->colour_meter_start.red ,
                                        data->colour_meter_start.green,
                                        data->colour_meter_start.blue,
                                        data->colour_meter_start.alpha);

      if (!data->two_colour_gradient)
        cairo_pattern_add_color_stop_rgba(data->pats[0], 0.5, data->colour_meter_middle.red ,
                                          data->colour_meter_middle.green,
                                          data->colour_meter_middle.blue,
                                          data->colour_meter_middle.alpha);

      cairo_pattern_add_color_stop_rgba(data->pats[0], 1, data->colour_meter_end.red ,
                                        data->colour_meter_end.green,
                                        data->colour_meter_end.blue,
                                        data->colour_meter_end.alpha);

      data->pats[1] = cairo_pattern_create_linear(data->width - 100 * data->size_mult, y - data->move_down * 0.8, data->width, data->move_down * 0.6);

      cairo_pattern_add_color_stop_rgba(data->pats[1], 0, data->colour_meter_start.red ,
                                        data->colour_meter_start.green,
                                        data->colour_meter_start.blue,
                                        data->colour_meter_start.alpha);

      if (!data->two_colour_gradient)
        cairo_pattern_add_color_stop_rgba(data->pats[1], 0.5, data->colour_meter_middle.red ,
                                          data->colour_meter_middle.green,
                                          data->colour_meter_middle.blue,
                                          data->colour_meter_middle.alpha);

      cairo_pattern_add_color_stop_rgba(data->pats[1], 1, data->colour_meter_end.red ,
                                        data->colour_meter_end.green,
                                        data->colour_meter_end.blue,
                                        data->colour_meter_end.alpha);

      data->pats[2] = cairo_pattern_create_linear(data->width - 100 * data->size_mult, y - data->move_down * 0.8, data->width, data->move_down * 0.6);

      cairo_pattern_add_color_stop_rgba(data->pats[2], 0, data->colour_meter_start.red ,
                                        data->colour_meter_start.green,
                                        data->colour_meter_start.blue,
                                        data->colour_meter_start.alpha);

      if (!data->two_colour_gradient)
        cairo_pattern_add_color_stop_rgba(data->pats[2], 0.5, data->colour_meter_middle.red ,
                                          data->colour_meter_middle.green,
                                          data->colour_meter_middle.blue,
                                          data->colour_meter_middle.alpha);

      cairo_pattern_add_color_stop_rgba(data->pats[2], 1, data->colour_meter_end.red ,
                                        data->colour_meter_end.green,
                                        data->colour_meter_end.blue,
                                        data->colour_meter_end.alpha);

      data->pats[3] = cairo_pattern_create_linear(data->width - 100 * data->size_mult, y - data->move_down * 0.8 , data->width, data->move_down * 0.6);

      cairo_pattern_add_color_stop_rgba(data->pats[3], 0, data->colour_meter_end.red ,
                                        data->colour_meter_end.green,
                                        data->colour_meter_end.blue,
                                        data->colour_meter_end.alpha);

      if (!data->two_colour_gradient)
        cairo_pattern_add_color_stop_rgba(data->pats[3], 0.5, data->colour_meter_middle.red ,
                                          data->colour_meter_middle.green,
                                          data->colour_meter_middle.blue,
                                          data->colour_meter_middle.alpha);

      cairo_pattern_add_color_stop_rgba(data->pats[3], 1, data->colour_meter_start.red ,
                                        data->colour_meter_start.green,
                                        data->colour_meter_start.blue,
                                        data->colour_meter_start.alpha);

      goto goto_bad_heheh;
    }

    cairo_move_to(c_widge.cr, x = dashboard_get_font_size(DASHBOARD_FONT_SMALL) * data->size_mult, y = dashboard_get_font_size(DASHBOARD_FONT_SMALL) * data->size_mult);

    for (i = 0;i < 4;i++)
    {
      cairo_show_text(c_widge.cr, content[0][i]);
      x = x + data->max_width_left * 1.1;
      cairo_text_extents(c_widge.cr, content[1][i], &extents);

      if (data->emotive_text)
      {
        switch (i)
        {

          case 0:
            cairo_set_source_rgb(c_widge.cr, data->user / 100.0, 1.0 - data->user / 100.0, 0.4);

            break;

          case 1:
            cairo_set_source_rgb(c_widge.cr, (data->sys) / 100.0, 1.0 - (data->sys) / 100.0, 0.4);
            break;

          case 2:
            cairo_set_source_rgb(c_widge.cr, (data->iowait) / 100.0, 1.0 - (data->iowait) / 100.0, 0.4);
            break;

          case 3:
            cairo_set_source_rgb(c_widge.cr, 1.0 - data->idle / 100.0, data->idle / 100.0, 0.4);
            break;
        }
      }
      else
      {
        cairo_set_source_rgba(c_widge.cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);
      }

      cairo_move_to(c_widge.cr,

                    x + (data->max_width_right - extents.width)
                    , y);
      cairo_show_text(c_widge.cr, content[1][i]);
//            cairo_pattern_t *pat;

//            pat = cairo_pattern_create_linear (0.0, 0.0,  0.0, 256.0);

      switch (i)
      {

        case 0:

          if (data->user)
          {
            cairo_rectangle(c_widge.cr, data->width - 100*data->size_mult, y - data->move_down*0.6, data->user*data->size_mult, data->move_down*0.6);

            if (data->shiny_graphs)
              cairo_set_source(c_widge.cr, data->pats[i]);

            cairo_fill(c_widge.cr);
          }

          break;

        case 1:

          if (data->sys)
          {

            cairo_rectangle(c_widge.cr, data->width - 100*data->size_mult, y - data->move_down*0.6, data->sys*data->size_mult, data->move_down*0.6);

            if (data->shiny_graphs)
              cairo_set_source(c_widge.cr, data->pats[i]);

            cairo_fill(c_widge.cr);
          }

          break;

        case 2:

          if (data->iowait)
          {

            cairo_rectangle(c_widge.cr, data->width - 100*data->size_mult, y - data->move_down*0.6, data->iowait*data->size_mult, data->move_down*0.6);

            if (data->shiny_graphs)
              cairo_set_source(c_widge.cr, data->pats[i]);

            cairo_fill(c_widge.cr);
          }

          break;

        case 3:

          if (data->user)
          {

            cairo_rectangle(c_widge.cr, data->width - 100*data->size_mult, y - data->move_down*0.6, data->idle*data->size_mult, data->move_down*0.6);

            if (data->shiny_graphs)
              cairo_set_source(c_widge.cr, data->pats[i]);

            cairo_fill(c_widge.cr);
          }

          break;
      }

      cairo_set_source_rgba(c_widge.cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);

      x = dashboard_get_font_size(DASHBOARD_FONT_SMALL) * data->size_mult;
      y = y + data->move_down;
      cairo_move_to(c_widge.cr, x, y);
    }

    del_cairo_widget(&c_widge);

    data->timer = data->refresh;

    for (i = 0;i < 4;i++)
    {
      free(content[0][i]);
      free(content[1][i]);
    }

    return TRUE;
  }
  else
  {
    return FALSE;
  }
}

