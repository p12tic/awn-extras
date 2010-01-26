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

#include <glibtop/loadavg.h>
#include <libawn/awn-applet.h>
#include <glib/gmacros.h>
#include <glib/gerror.h>
#include <gconf/gconf-value.h>

#include <libawn/awn-dialog.h>
#include <libawn/awn-applet-simple.h>
#include <glib.h>
#include <gtk/gtk.h>
#include <gdk/gdk.h>
#include <string.h>
#include <time.h>

#include "loadavg_component.h"
#include "dashboard_util.h"
#include "dashboard.h"
#include "config.h"
#include "gconf-config.h"
//#undef NDEBUG
#include <assert.h>

#define GCONF_LOADAVG_SIZE_MULT GCONF_PATH  "/component_loadavg_scale"
#define GCONF_LOADAVG_FG  GCONF_PATH "/component_loadavg_fg"
#define GCONF_LOADAVG_BG  GCONF_PATH "/component_loadavg_bg"

typedef struct
{
  double width;
  double height;
  int timer;
  int frequency;
  int refresh;
  AwnColor    bg;             /*colours if gtk colours are overridden */
  AwnColor    fg;
  float size_mult;
}Loadavg_plug_data;


static void _fn_set_bg(AwnColor * new_bg, Loadavg_plug_data **p);
static void _fn_set_fg(AwnColor * new_fg, Loadavg_plug_data **p);
static gboolean render(GtkWidget **pwidget, gint interval,
                       Loadavg_plug_data **p);
static gboolean query_support_multiple(void);
static void destruct(Loadavg_plug_data **p);
static void construct(Loadavg_plug_data **p);
static gboolean decrease_step(Loadavg_plug_data **p);
static gboolean increase_step(Loadavg_plug_data **p);
static GtkWidget* attach_right_click_menu(Loadavg_plug_data **p);

static void set_colour(Loadavg_plug_data *p, AwnColor* colour, const char *mess,
                       const char * gconf_key);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event,
                        Loadavg_plug_data *p);
static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event,
                        Loadavg_plug_data *p);

static const char* get_component_name(Loadavg_plug_data **p);
static const char* get_component_friendly_name(Loadavg_plug_data **p);


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

static void * check_ptr;


void * loadavg_plug_lookup(int fn_id)
{
  assert(fn_id < MAX_CALLBACK_FN);
  return plug_fns[fn_id];
}

static void _fn_set_bg(AwnColor * new_bg, Loadavg_plug_data **p)
{
  char *svalue;
  assert(check_ptr == *p);
  Loadavg_plug_data * plug_data = *p;
  plug_data->bg = *new_bg;
  svalue = dashboard_cairo_colour_to_string(new_bg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_LOADAVG_BG,
                          svalue , NULL);
  free(svalue);
}


static void _fn_set_fg(AwnColor * new_fg, Loadavg_plug_data **p)
{
  char *svalue;
  assert(check_ptr == *p);
  Loadavg_plug_data * plug_data = *p;
  plug_data->fg = *new_fg;
  svalue = dashboard_cairo_colour_to_string(new_fg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_LOADAVG_FG,
                          svalue , NULL);
  free(svalue);
}


static GtkWidget* attach_right_click_menu(Loadavg_plug_data **p)
{
  assert(check_ptr == *p);
  Loadavg_plug_data * plug_data = *p;
  GtkWidget *menu = gtk_menu_new();

  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_fg), "Foreground",
                                      plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_bg), "Background",
                                      plug_data);
  return menu;
}

static void set_colour(Loadavg_plug_data *p, AwnColor* colour, const char *mess,
                       const char * gconf_key)
{
  assert(check_ptr == p);
  char *svalue;
  pick_awn_color(colour, mess, p, NULL);
  svalue = dashboard_cairo_colour_to_string(colour);
  gconf_client_set_string(get_dashboard_gconf(), gconf_key, svalue , NULL);
  free(svalue);
}

static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event,
                        Loadavg_plug_data *p)
{
  assert(check_ptr == p);
  set_colour(p, &p->fg, "Foreground Colour", GCONF_LOADAVG_FG);
  return TRUE;
}

static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event,
                        Loadavg_plug_data *p)
{
  assert(check_ptr == p);
  set_colour(p, &p->bg, "Background Colour", GCONF_LOADAVG_BG);
  return TRUE;
}

static gboolean query_support_multiple(void)
{
  return FALSE;
}

static void destruct(Loadavg_plug_data **p)
{
  assert(check_ptr == *p);
  g_free(*p);
  return;
}

static void construct(Loadavg_plug_data **p)
{
  *p = g_malloc(sizeof(Loadavg_plug_data));
  Loadavg_plug_data * data = *p;
  GConfValue *value;
  gchar * svalue;
  check_ptr = data;
  data->frequency = 1000;
  data->timer = 100;

  svalue = gconf_client_get_string(get_dashboard_gconf(),
                                   GCONF_LOADAVG_BG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_LOADAVG_BG,
                            svalue = g_strdup("222299EE"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->bg);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(),
                                   GCONF_LOADAVG_FG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_LOADAVG_FG,
                            svalue = g_strdup("00000000"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->fg);

  g_free(svalue);

  value = gconf_client_get(get_dashboard_gconf(), GCONF_LOADAVG_SIZE_MULT, NULL);

  if (value)
  {
    data->size_mult = gconf_client_get_float(get_dashboard_gconf(), GCONF_LOADAVG_SIZE_MULT, NULL);
  }
  else
  {
    data->size_mult = 1.0;
  }
}

static gboolean decrease_step(Loadavg_plug_data **p)
{
  assert(check_ptr == *p);
  Loadavg_plug_data *data = *p;
  data->size_mult = data->size_mult * 5.0 / 6.0;

  gconf_client_set_float(get_dashboard_gconf(), GCONF_LOADAVG_SIZE_MULT, data->size_mult, NULL);
  return TRUE;
}

static gboolean increase_step(Loadavg_plug_data **p)
{
  assert(check_ptr == *p);
  Loadavg_plug_data *data = *p;
  data->size_mult = data->size_mult * 1.2;
  gconf_client_set_float(get_dashboard_gconf(), GCONF_LOADAVG_SIZE_MULT, data->size_mult, NULL);
  return TRUE;
}

static const char* get_component_name(Loadavg_plug_data **p)
{
  assert(check_ptr == *p);
  const char * name = "component_loadavg";
  return name;
}

static const char* get_component_friendly_name(Loadavg_plug_data **p)
{
  assert(check_ptr == *p);
  const char * name = "Load Average";
  return name;
}

static gboolean render(GtkWidget ** pwidget, gint interval, Loadavg_plug_data **p)
{
  char buf[200];
  static int width = -1;
  static int height = -1;
  Loadavg_plug_data * data = *p;
  dashboard_cairo_widget c_widge;
  float mult;
  cairo_text_extents_t    extents;
  glibtop_loadavg load;

  assert(check_ptr == *p);
  data->timer = data->timer - interval;

  if (data->timer <= 0)
  {
    data->timer = data->frequency;       /*FIXME... you might not want this refresh rate
                                if you're not displaying seconds...*/
    glibtop_get_loadavg(&load);
    snprintf(buf, sizeof(buf), "Load Average: %0.2f, %0.2f, %0.2f", load.loadavg[0],
             load.loadavg[1], load.loadavg[2]);

    if (width < 0)
    {
      *pwidget = get_cairo_widget(&c_widge, 200, 30);
      mult = 1;
      use_bg_rgba_colour(c_widge.cr);
      cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(c_widge.cr);
      data->timer = interval;
    }
    else
    {
      mult = data->size_mult;
      *pwidget = get_cairo_widget(&c_widge, width * mult, height * mult);
      awn_cairo_rounded_rect(c_widge.cr, 0, 0, width*mult, height*mult, height*mult*0.1, ROUND_ALL);
      cairo_set_source_rgba(c_widge.cr, data->bg.red, data->bg.green, data->bg.blue, data->bg.alpha);
      cairo_fill(c_widge.cr);
    }

    cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);

    cairo_set_font_size(c_widge.cr, dashboard_get_font_size(DASHBOARD_FONT_SMALL)*mult);

    cairo_set_source_rgba(c_widge.cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);

    cairo_move_to(c_widge.cr, 5.0*mult, height*mult - 2*mult);

    if (width < 0)
    {
      cairo_text_extents(c_widge.cr, buf, &extents);
      height = extents.height + 4;
      width = extents.width + 8;
      return FALSE;
    }

    cairo_show_text(c_widge.cr, buf);

    del_cairo_widget(&c_widge);
    return TRUE;
  }

  return FALSE;
}
