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

#include <glibtop/mem.h>
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

#include "sysmem_component.h"
#include "dashboard_util.h"
#include "dashboard.h"
#include "config.h"
#include "gconf-config.h"
#undef NDEBUG
#include <assert.h>

#define GCONF_SYSMEM_SIZE_MULT GCONF_PATH  "/component_sysmem_scale"
#define GCONF_SYSMEM_FG  GCONF_PATH "/component_sysmem_fg"
#define GCONF_SYSMEM_BG  GCONF_PATH "/component_sysmem_bg"
#define GCONF_SYSMEM_FREE_COLOUR GCONF_PATH "/component_sysmem_free_colour"
#define GCONF_SYSMEM_USER_COLOUR GCONF_PATH "/component_sysmem_user_colour"
#define GCONF_SYSMEM_SHARED_COLOUR GCONF_PATH "/component_sysmem_shared_colour"
#define GCONF_SYSMEM_BUFFER_COLOUR GCONF_PATH "/component_sysmem_buffer_colour"
#define GCONF_SYSMEM_CACHED_COLOUR GCONF_PATH "/component_sysmem_cached_colour"

enum
{
  SYSMEM_USER,
  SYSMEM_FREE,
  SYSMEM_BUFFER,
  SYSMEM_CACHED,
  SYSMEM_SHARED
};

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
  AwnColor colours[5];

}Sysmem_plug_data;


static void _fn_set_bg(AwnColor * new_bg, Sysmem_plug_data **p);
static void _fn_set_fg(AwnColor * new_fg, Sysmem_plug_data **p);
static gboolean render(GtkWidget **pwidget, gint interval,
                       Sysmem_plug_data **p);
static gboolean query_support_multiple(void);
static void destruct(Sysmem_plug_data **p);
static void construct(Sysmem_plug_data **p);
static gboolean decrease_step(Sysmem_plug_data **p);
static gboolean increase_step(Sysmem_plug_data **p);
static GtkWidget* attach_right_click_menu(Sysmem_plug_data **p);

static void set_colour(Sysmem_plug_data *p, AwnColor* colour, const char *mess,
                       const char * gconf_key);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event,
                        Sysmem_plug_data *p);
static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event,
                        Sysmem_plug_data *p);

static const char* get_component_name(Sysmem_plug_data **p);
static const char* get_component_friendly_name(Sysmem_plug_data **p);


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
  _fn_set_fg
};

static void * check_ptr;


void * sysmem_plug_lookup(int fn_id)
{
  assert(fn_id < MAX_CALLBACK_FN);
  return plug_fns[fn_id];
}

static void _fn_set_bg(AwnColor * new_bg, Sysmem_plug_data **p)
{
  char *svalue;
  assert(check_ptr == *p);
  Sysmem_plug_data * plug_data = *p;
  plug_data->bg = *new_bg;
  svalue = dashboard_cairo_colour_to_string(new_bg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_BG,
                          svalue , NULL);
  free(svalue);
}


static void _fn_set_fg(AwnColor * new_fg, Sysmem_plug_data **p)
{
  char *svalue;
  assert(check_ptr == *p);
  Sysmem_plug_data * plug_data = *p;
  plug_data->fg = *new_fg;
  svalue = dashboard_cairo_colour_to_string(new_fg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_FG,
                          svalue , NULL);
  free(svalue);
}


static GtkWidget* attach_right_click_menu(Sysmem_plug_data **p)
{
  assert(check_ptr == *p);
  Sysmem_plug_data * plug_data = *p;
  GtkWidget * menu_items;
  GtkWidget *menu = gtk_menu_new();

  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_fg), "Foreground",
                                      plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_bg), "Background",
                                      plug_data);

  return menu;
}

static void set_colour(Sysmem_plug_data *p, AwnColor* colour, const char *mess,
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
                        Sysmem_plug_data *p)
{
  assert(check_ptr == p);
  set_colour(p, &p->fg, "Foreground Colour", GCONF_SYSMEM_FG);
  return TRUE;
}

static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event,
                        Sysmem_plug_data *p)
{
  assert(check_ptr == p);
  set_colour(p, &p->bg, "Background Colour", GCONF_SYSMEM_BG);
  return TRUE;
}

static gboolean query_support_multiple(void)
{
  return FALSE;
}

static void destruct(Sysmem_plug_data **p)
{
  assert(check_ptr == *p);
  g_free(*p);
  return;
}

static void construct(Sysmem_plug_data **p)
{
  *p = g_malloc(sizeof(Sysmem_plug_data));
  Sysmem_plug_data * data = *p;
  GConfValue *value;
  gchar * svalue;
  check_ptr = data;
  data->frequency = 1000;
  data->timer = 100;

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_BG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_BG, svalue = g_strdup("222299EE"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->bg);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_FG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_FG, svalue = g_strdup("00000000"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->fg);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_USER_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_USER_COLOUR, svalue = g_strdup("DD0000DD"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colours[SYSMEM_USER]);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_FREE_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_FREE_COLOUR, svalue = g_strdup("00DD22DD"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colours[SYSMEM_FREE]);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_BUFFER_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_BUFFER_COLOUR, svalue = g_strdup("0000DDDD"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colours[SYSMEM_BUFFER]);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_CACHED_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_CACHED_COLOUR, svalue = g_strdup("AA0099DD"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colours[SYSMEM_CACHED]);

  g_free(svalue);

  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_SYSMEM_SHARED_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_SYSMEM_SHARED_COLOUR, svalue = g_strdup("666666DD"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->colours[SYSMEM_SHARED]);

  g_free(svalue);


  value = gconf_client_get(get_dashboard_gconf(), GCONF_SYSMEM_SIZE_MULT, NULL);

  if (value)
  {
    data->size_mult = gconf_client_get_float(get_dashboard_gconf(), GCONF_SYSMEM_SIZE_MULT, NULL);
  }
  else
  {
    data->size_mult = 1.0;
  }
}

static gboolean decrease_step(Sysmem_plug_data **p)
{
  assert(check_ptr == *p);
  Sysmem_plug_data *data = *p;
  data->size_mult = data->size_mult * 5.0 / 6.0;

  gconf_client_set_float(get_dashboard_gconf(), GCONF_SYSMEM_SIZE_MULT, data->size_mult, NULL);
}

static gboolean increase_step(Sysmem_plug_data **p)
{
  assert(check_ptr == *p);
  Sysmem_plug_data *data = *p;
  data->size_mult = data->size_mult * 1.2;
  gconf_client_set_float(get_dashboard_gconf(), GCONF_SYSMEM_SIZE_MULT, data->size_mult, NULL);
}

static const char* get_component_name(Sysmem_plug_data **p)
{
  assert(check_ptr == *p);
  const char * name = "component_sysmem";
  return name;
}

static const char* get_component_friendly_name(Sysmem_plug_data **p)
{
  assert(check_ptr == *p);
  const char * name = "System Memory Usage";
  return name;
}

static gboolean render(GtkWidget ** pwidget, gint interval, Sysmem_plug_data **p)
{
  char buf[200];
  time_t t;

  struct tm *tmp;
  static int width = -1;
  static int col_width = -1;
  static int height = -1;
  static int text_height = -1;
  Sysmem_plug_data * data = *p;
  dashboard_cairo_widget c_widge;
  float mult;
  cairo_text_extents_t    extents;
  glibtop_mem  mem;
  int i;
  double values[5];

  assert(check_ptr == *p);
  data->timer = data->timer - interval;

  if (data->timer <= 0)
  {
    data->timer = data->frequency;       /*FIXME... you might not want this refresh rate
                                if you're not displaying seconds...*/
    glibtop_get_mem(&mem);
    mult = data->size_mult;

    if (width < 0)
    {
      *pwidget = get_cairo_widget(&c_widge, 200, 15 * 3);
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
      cairo_rectangle(c_widge.cr, 0, 0, width*mult, height*mult);
      cairo_set_source_rgba(c_widge.cr, data->bg.red, data->bg.green, data->bg.blue, data->bg.alpha);
      cairo_fill(c_widge.cr);
    }

    snprintf(buf, sizeof(buf), "Total: ");

    cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(c_widge.cr, dashboard_get_font_size(DASHBOARD_FONT_SMALL)*mult);
    cairo_set_source_rgba(c_widge.cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);
    cairo_move_to(c_widge.cr, 5.0*mult, text_height*mult - 2*mult);

    if (width < 0)
    {
      cairo_text_extents(c_widge.cr, buf, &extents);

      height = (extents.height + 4) * 4;
      col_width = extents.width * 1.7;
      width = (col_width * 4) + 5 + height;
      text_height = extents.height + 4;
      return FALSE;
    }

    cairo_show_text(c_widge.cr, buf);



    snprintf(buf, sizeof(buf), "%0.2fM", mem.total / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*2*mult - extents.width - 5*mult, text_height*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);

    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*2, text_height*mult - 2*mult);
    snprintf(buf, sizeof(buf), "Used:");
    cairo_show_text(c_widge.cr, buf);

    snprintf(buf, sizeof(buf), "%0.2fM", mem.used / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*4 - extents.width - 5*mult, text_height*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);

    //line 2.
    cairo_move_to(c_widge.cr, 5.0*mult, text_height*2*mult - 2*mult);
    snprintf(buf, sizeof(buf), "Free:");
    cairo_show_text(c_widge.cr, buf);

    snprintf(buf, sizeof(buf), "%0.2fM", mem.free / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*2 - extents.width - 5*mult, text_height*2*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);

    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*2, text_height*2*mult - 2*mult);
    snprintf(buf, sizeof(buf), "User:");
    cairo_show_text(c_widge.cr, buf);

    snprintf(buf, sizeof(buf), "%0.2fM", mem.user / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*4 - extents.width - 5*mult, text_height*2*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);

    //line 3
    cairo_move_to(c_widge.cr, 5.0*mult, text_height*3*mult - 2*mult);
    snprintf(buf, sizeof(buf), "Shared:");
    cairo_show_text(c_widge.cr, buf);

    snprintf(buf, sizeof(buf), "%0.2fM", mem.shared / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*2*mult - extents.width - 5*mult, text_height*3*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);

    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*2, text_height*3*mult - 2*mult);
    snprintf(buf, sizeof(buf), "Buffer:");
    cairo_show_text(c_widge.cr, buf);

    snprintf(buf, sizeof(buf), "%0.2fM", mem.buffer / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*mult*4 - extents.width - 5*mult, text_height*3*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);
    //line 4
    cairo_move_to(c_widge.cr, 5.0*mult, text_height*4*mult - 2*mult);
    snprintf(buf, sizeof(buf), "Cached:");
    cairo_show_text(c_widge.cr, buf);

    snprintf(buf, sizeof(buf), "%0.2fM", mem.cached / 1024.0 / 1024.0);
    cairo_text_extents(c_widge.cr, buf, &extents);
    cairo_move_to(c_widge.cr, 5.0*mult + col_width*2*mult - extents.width - 5*mult, text_height*4*mult - 2*mult);
    cairo_show_text(c_widge.cr, buf);

    values[0] = mem.user * 100.0 / mem.total;
    values[1] = mem.free * 100.0 / mem.total;
    values[2] = mem.buffer * 100.0 / mem.total;
    values[3] = mem.cached * 100.0 / mem.total;
    values[4] = mem.shared * 100.0 / mem.total;

    draw_pie_graph(c_widge.cr, width*mult - height / 2*mult, height / 2.0*mult - height / 20.0*mult, height / 2.0*0.9*mult, 0, values, data->colours, 4);
    del_cairo_widget(&c_widge);
    return TRUE;
  }

  return FALSE;
}
