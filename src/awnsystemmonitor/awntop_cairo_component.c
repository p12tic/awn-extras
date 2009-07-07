/*
 * Copyright (c) 2007
 *                      Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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
#include <glibtop/proclist.h>
#include <glibtop/procstate.h>
#include <glibtop/proctime.h>
#include <glibtop/procuid.h>
#include <glibtop/procmem.h>
#include <glibtop/cpu.h>
#include <glibtop/mem.h>
#include <glibtop/procargs.h>

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>
#include <signal.h>
#include <sys/types.h>

#include <dirent.h>
#include <libgen.h>


#include <libawn/awn-applet.h>
#include <glib/gmacros.h>
#include <glib/gerror.h>
#include <gconf/gconf-value.h>

#include <libawn/awn-dialog.h>
#include <libawn/awn-applet-simple.h>
#include <glib.h>
#include <gtk/gtk.h>


#include <libawn/awn-applet.h>
#include "cairo-utils.h"
#include <libawn/awn-tooltip.h>

#include "awntop_cairo_component.h"
#include "dashboard_util.h"
#include "dashboard.h"
#include "config.h"
#include "gconf-config.h"
//#undef NDEBUG
#include <assert.h>

#define GCONF_AWNTOP_CAIRO_SIZE_MULT GCONF_PATH  "/component_awntop_cairo_scale"
#define GCONF_AWNTOP_CAIRO_NO_GTK_FG  GCONF_PATH "/component_awntop_cairo_fg"
#define GCONF_AWNTOP_CAIRO_NO_GTK_BG  GCONF_PATH "/component_awntop_cairo_bg"
#define GCONF_AWNTOP_CAIRO_NUM_PROCS GCONF_PATH  "/component_awntop_cairo_num_procs"
#define GCONF_AWNTOP_CAIRO_KILL_SIG_METH GCONF_PATH  "/component_awntop_cairo_kill_sig_meth"
#define GCONF_AWNTOP_CAIRO_USER_FILTER GCONF_PATH  "/component_awntop_cairo_user_filter"

typedef struct
{
  guint64     proctime;
  gboolean    accessed;
}Proctimeinfo;

typedef struct
{
  dashboard_cairo_widget *w;
  guint64 *lookup_table;
  int size;
  int head;
  int tail;
}Small_Pixmap_cache;


typedef struct
{
  long     pid;
  int     uid;
  int     pri;
  int     nice;
  guint64    virt;
  guint64    res;
  long    shr;
  long     cpu;
  guint64     mem;
  long    time;
  char    cmd[40];
}Topentry;

typedef int (*AwnTopCompareFunc)(const void *, const void *);

typedef struct
{
  float size_mult;

  AwnColor    bg;             /*colours if gtk colours are overridden */
  AwnColor    fg;
  GtkWidget   *table;

  int maxtopentries;
  AwnTopCompareFunc compar;
  long    *   displayed_pid_list;
  GTree*  proctimes;
  GTree*  icons;
  GTree*  pixbufs;
  Topentry **topentries;
  int num_top_entries;
  int filterlevel;
  glibtop_mem libtop_mem;

  guint updateinterval;
  gboolean   forceupdatefixup;
  guint    accum_interval;
  GtkWidget * widgets[9][70];            /*FIXME*/
  long prev_pid[70];
  gboolean invalidate_pixmaps;

  Small_Pixmap_cache *pid_pixmaps;
  Small_Pixmap_cache *uid_pixmaps;
  Small_Pixmap_cache *virt_res_pixmaps;
  Small_Pixmap_cache *cpu_mem_pixmaps;
  Small_Pixmap_cache *procname_pixmaps;

}Awntop_cairo_plug_data;

typedef struct
{
  char    *   name;
  gboolean(*fn)(GtkWidget *, GdkEventButton *, Awntop_cairo_plug_data *);
  int     unscaled_width;

}Tableheader;


static int _Dummy_DUMMY = 0;
static int  G_kill_signal_method = 1;

static GdkPixbuf* Stock_Image_Used = (GdkPixbuf*)(&_Dummy_DUMMY);


static void * check_ptr;

static gboolean decrease_step(Awntop_cairo_plug_data **p);
static gboolean increase_step(Awntop_cairo_plug_data **p);
static gboolean render(GtkWidget ** pwidget, gint interval,
                       Awntop_cairo_plug_data **p);
static gboolean query_support_multiple(void);
static void destruct(Awntop_cairo_plug_data **p);
static void construct(Awntop_cairo_plug_data **p);
static const char* get_component_name(Awntop_cairo_plug_data **p);
static const char* get_component_friendly_name(Awntop_cairo_plug_data **p);
static GtkWidget* attach_right_click_menu(Awntop_cairo_plug_data **p);
static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event,
                        Awntop_cairo_plug_data *p);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event,
                        Awntop_cairo_plug_data *p);

static gboolean _increase_awntop_rows(GtkWidget *widget, GdkEventButton *event,
                                      Awntop_cairo_plug_data *awntop);
static gboolean _decrease_awntop_rows(GtkWidget *widget, GdkEventButton *event,
                                      Awntop_cairo_plug_data *awntop);
static gboolean _toggle_display_freeze(GtkWidget *widget, GdkEventButton *event,
                                       Awntop_cairo_plug_data *awntop);
static gboolean _click_set_term(GtkWidget *widget, GdkEventButton *event,
                                Awntop_cairo_plug_data*awntop);
static gboolean _click_set_kill(GtkWidget *widget, GdkEventButton *event,
                                Awntop_cairo_plug_data *awntop);
//static gboolean _click_set_term_kill(GtkWidget *widget, GdkEventButton *event,
//                                     Awntop_cairo_plug_data*awntop);
static gboolean _toggle_user_filter(GtkWidget *widget, GdkEventButton *event,
                                    Awntop_cairo_plug_data *awntop);


static void set_colour(Awntop_cairo_plug_data *p, AwnColor* colour,
                       const char * mess, const char * gconf_key);


static void build_top_table_headings(Awntop_cairo_plug_data * data);
static Topentry ** fill_topentries(Awntop_cairo_plug_data *awntop, int *numel);
static gboolean proctime_find_inactive(gpointer key, gpointer value,
                                       gpointer data);
static void proctimes_remove_inactive(gpointer data, gpointer user_data);
static gboolean proctime_reset_active(gpointer key, gpointer value,
                                      gpointer data);
static gint proctime_key_compare_func(gconstpointer a, gconstpointer b,
                                      gpointer user_data);

static int cmppid(const void *, const void *);
static int cmpuser(const void *, const void *);
static gint64 cmpvirt(const void *, const void *);
static gint64 cmpres(const void *, const void *);
static int cmpcpu(const void *, const void *);
static gint64 cmpmem(const void *, const void *);
static int cmpcommand(const void *, const void *);

static void invalidate_pixmap_cache(Small_Pixmap_cache *p);
static Small_Pixmap_cache * get_s_pixmap_cache(long size);
static GdkPixmap * lookup_pixmap(Small_Pixmap_cache *p, guint64 key);
static GtkWidget * lookup_icon(Awntop_cairo_plug_data * awntop,
                               Topentry **topentries, int i);
static void invalidate_pixmap_cache(Small_Pixmap_cache *p);

static void invalidate_all_pixmap_caches(Awntop_cairo_plug_data * data);

static gint icons_key_compare_func(gconstpointer a, gconstpointer b,
                                   gpointer user_data);
static GtkWidget * get_icon_event_box(Awntop_cairo_plug_data * awntop,
                                      char *name, const gchar *stock_id, GtkIconSize size);

static void parse_desktop_entries(Awntop_cairo_plug_data * awntop);
static void free_topentries(Topentry **topentries, int num_top_entries);


static void set_foreground(Awntop_cairo_plug_data * data, cairo_t * cr);
static void set_background(Awntop_cairo_plug_data * data, cairo_t * cr);

static gboolean _time_to_kill(GtkWidget *widget, GdkEventButton *event,
                              long * pid);

static gboolean _click_pid(GtkWidget *widget, GdkEventButton *event,
                           Awntop_cairo_plug_data*);
static gboolean _click_user(GtkWidget *widget, GdkEventButton *event,
                            Awntop_cairo_plug_data *);
static gboolean _click_virt(GtkWidget *widget, GdkEventButton *event,
                            Awntop_cairo_plug_data *);
static gboolean _click_res(GtkWidget *widget, GdkEventButton *event,
                           Awntop_cairo_plug_data *);
static gboolean _click_cpu(GtkWidget *widget, GdkEventButton *event,
                           Awntop_cairo_plug_data *);
static gboolean _click_mem(GtkWidget *widget, GdkEventButton *event,
                           Awntop_cairo_plug_data*);
static gboolean _click_command(GtkWidget *widget, GdkEventButton *event,
                               Awntop_cairo_plug_data*);

static void _fn_set_bg(AwnColor * new_bg, Awntop_cairo_plug_data **p);
static void _fn_set_fg(AwnColor * new_fg, Awntop_cairo_plug_data **p);

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

static Tableheader Global_tableheadings[] =
{
  {   "Process", _click_pid, 70},
  {   "Username", _click_user, 100},
  {   "Virtual", _click_virt, 55},
  {   "Resident",   _click_res, 55},
  {   "%CPU",  _click_cpu, 50},
  {   "%MEM", _click_mem, 50},
  {   " ", NULL, 16},
  {   "Command Line",  _click_command, 120},
  {   " ",  NULL, 16}

};


static int compmethod = 1;

static int     gcomparedir;
static gboolean     top_state;

void * awntop_cairo_plug_lookup(int fn_id)
{
  assert(fn_id < MAX_CALLBACK_FN);
  return plug_fns[fn_id];
}

static void _fn_set_bg(AwnColor * new_bg, Awntop_cairo_plug_data **p)
{
  char *svalue;
  assert(check_ptr == *p);
  Awntop_cairo_plug_data * plug_data = *p;
  plug_data->bg = *new_bg;
  plug_data->invalidate_pixmaps = TRUE;
//    build_top_table_headings(plug_data);
  svalue = dashboard_cairo_colour_to_string(new_bg);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NO_GTK_BG, svalue , NULL);
  free(svalue);
}


static void _fn_set_fg(AwnColor * new_fg, Awntop_cairo_plug_data **p)
{
  char *svalue;
  assert(check_ptr == *p);
  Awntop_cairo_plug_data * plug_data = *p;
  plug_data->fg = *new_fg;
  plug_data->invalidate_pixmaps = TRUE;
  svalue = dashboard_cairo_colour_to_string(new_fg);
//    build_top_table_headings(plug_data);
  gconf_client_set_string(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NO_GTK_FG, svalue , NULL);
  free(svalue);
}

static GtkWidget* attach_right_click_menu(Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  Awntop_cairo_plug_data * plug_data = *p;
  GtkWidget * menu_items;
  GtkWidget *kill_menu = gtk_menu_new();
  GtkWidget *menu = gtk_menu_new();

  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_increase_awntop_rows),
                                      "Increase Entries", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_decrease_awntop_rows),
                                      "Decrease Entries", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_display_freeze),
                                      "Pause", plug_data);
  dashboard_build_clickable_menu_item(kill_menu, G_CALLBACK(_click_set_term),
                                      "SIGTERM", plug_data);
  dashboard_build_clickable_menu_item(kill_menu, G_CALLBACK(_click_set_kill),
                                      "SIGKILL", plug_data);
#if 0
  dashboard_build_clickable_menu_item(kill_menu,
                                      G_CALLBACK(_click_set_term_kill),
                                      "SIGTERM Followed by SIGKILL", data);
#endif
  menu_items = gtk_menu_item_new_with_label("Kill Signal");
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menu_items);
  gtk_menu_item_set_submenu(GTK_MENU_ITEM(menu_items), kill_menu);
  gtk_widget_show(menu_items);

  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_user_filter),
                                      "Toggle User filter", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_fg),
                                      "Non GTK Foreground", plug_data);
  dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_bg),
                                      "Non GTK Background", plug_data);
  return menu;
}

static void set_colour(Awntop_cairo_plug_data *p, AwnColor* colour,
                       const char * mess, const char * gconf_key)
{
  assert(check_ptr == p);
  char *svalue;
  pick_awn_color(colour, mess, p, (DashboardNotifyColorChange)invalidate_all_pixmap_caches);
  svalue = dashboard_cairo_colour_to_string(colour);
  gconf_client_set_string(get_dashboard_gconf(), gconf_key, svalue , NULL);
  p->invalidate_pixmaps = TRUE;
  free(svalue);
}

static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event,
                        Awntop_cairo_plug_data *p)
{
  assert(check_ptr == p);
  set_colour(p, &p->fg, "Foreground Colour if Ignore gtk",
             GCONF_AWNTOP_CAIRO_NO_GTK_FG);
  return TRUE;
}

static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event,
                        Awntop_cairo_plug_data *p)
{
  assert(check_ptr == p);
  set_colour(p, &p->bg, "Background Colour if Ignore gtk",
             GCONF_AWNTOP_CAIRO_NO_GTK_BG);
  return TRUE;
}


static const char* get_component_friendly_name(Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  const char * name = "Top (Cairo) Component";
  return name;
}


static const char* get_component_name(Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  const char * name = "component_awntop_cairo";
  return name;
}


static gboolean decrease_step(Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  Awntop_cairo_plug_data *data = *p;
  data->size_mult = data->size_mult * 5.0 / 6.0;
  gconf_client_set_float(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_SIZE_MULT,
                         data->size_mult, NULL);
  data->invalidate_pixmaps = TRUE;
  build_top_table_headings(data);
  return TRUE;
}

static gboolean increase_step(Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  Awntop_cairo_plug_data *data = *p;
  data->size_mult = data->size_mult * 1.2;
  gconf_client_set_float(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_SIZE_MULT,
                         data->size_mult, NULL);
  data->invalidate_pixmaps = TRUE;
  build_top_table_headings(data);
  return TRUE;
}

static gboolean query_support_multiple(void)
{
  return FALSE;
}

static void construct(Awntop_cairo_plug_data **p)
{

  *p = g_malloc(sizeof(Awntop_cairo_plug_data));

  Awntop_cairo_plug_data * data = *p;
  GConfValue *value;
  gchar * svalue;
  int i;

  assert(sizeof(data->widgets) == sizeof(GtkWidget *)*9*70);      /*FIXME*/

  check_ptr = data;

  memset(data->widgets, 0, sizeof(data->widgets));

  data->compar = cmpcpu;
  data->invalidate_pixmaps = FALSE;
  top_state = TRUE;
  gcomparedir = -1;
  compmethod = 1;     /*sort by CPU*/


  data->pid_pixmaps = get_s_pixmap_cache(200);
  data->uid_pixmaps = get_s_pixmap_cache(20);
  data->virt_res_pixmaps = get_s_pixmap_cache(500);
//    data->res_pixmaps=get_s_pixmap_cache(250);
  data->cpu_mem_pixmaps = get_s_pixmap_cache(101);
  data->procname_pixmaps = get_s_pixmap_cache(100);

  for (i = 0;i < (sizeof(data->prev_pid) / sizeof(long)) ;i++)
  {
    data->prev_pid[i] = -1;
  }

  assert(check_ptr == *p);

  data->updateinterval = 2000;
  data->forceupdatefixup = FALSE;



  data->displayed_pid_list = NULL;
  data->proctimes = g_tree_new_full(proctime_key_compare_func, NULL, g_free, g_free);

  data->icons = g_tree_new_full(icons_key_compare_func, NULL, free, free);

  data->pixbufs = g_tree_new_full(icons_key_compare_func, NULL, free, free);
  parse_desktop_entries(data);


  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NO_GTK_BG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NO_GTK_BG, svalue = g_strdup("999999d4"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->bg);

  g_free(svalue);


  svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NO_GTK_FG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NO_GTK_FG, svalue = g_strdup("FFFFFFBB"), NULL);
  }

  awn_cairo_string_to_color(svalue, &data->fg);

  g_free(svalue);


  value = gconf_client_get(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_SIZE_MULT, NULL);

  if (value)
  {
    data->size_mult = gconf_client_get_float(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_SIZE_MULT, NULL);
  }
  else
  {
    data->size_mult = 1.2;
  }

  value = gconf_client_get(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NUM_PROCS, NULL);

  if (value)
  {
    data->maxtopentries = gconf_client_get_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NUM_PROCS, NULL);
  }
  else
  {
    data->maxtopentries = 17;
  }

  value = gconf_client_get(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_USER_FILTER, NULL);

  if (value)
  {
    data->filterlevel = gconf_client_get_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_USER_FILTER, NULL);
  }
  else
  {
    data->filterlevel = 1;
  }

  value = gconf_client_get(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_KILL_SIG_METH, NULL);

  if (value)
  {
    G_kill_signal_method = gconf_client_get_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_KILL_SIG_METH, NULL);
  }
  else
  {
    G_kill_signal_method = 2;
  }

  data->accum_interval = data->updateinterval;

  data->table = gtk_table_new(9, data->maxtopentries, FALSE); /*FIXME*/
  gtk_table_set_col_spacings(GTK_TABLE(data->table), 0);
  gtk_table_set_row_spacings(GTK_TABLE(data->table), 0);

}

static void destruct(Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  g_free(*p);
}

static Small_Pixmap_cache * get_s_pixmap_cache(long size)
{
  int i;
  Small_Pixmap_cache * p = g_malloc(sizeof(Small_Pixmap_cache)) ;
  p->w = g_malloc(sizeof(dashboard_cairo_widget) * (size));
#if 1

  for (i = 0;i < size;i++)  /*FIXME - use memset*/
  {
    p->w[i].pixmap = NULL;
  }

#endif
  p->lookup_table = g_malloc(sizeof(guint64) * (size));

  p->size = size;

  p->head = 0;

  p->tail = 0;

  return p;
}

static void invalidate_pixmap_cache(Small_Pixmap_cache *p)
{
  int i;

  for (i = 0;i < p->size ;i++)
  {
    if (p->w[i].pixmap)
    {

      g_object_unref(p->w[i].pixmap);
      cairo_destroy(p->w[i].cr);
      p->w[i].pixmap = NULL;
    }
  }

  p->head = 0;

  p->tail = 0;
}

static GdkPixmap * lookup_pixmap(Small_Pixmap_cache *p, guint64 key)
{
  int i;

  /*dumbing down the logic for now */

  for (i = 0;i < p->size;i++)
  {
    if (p->w[i].pixmap)
    {
      if (p->lookup_table[i] == key)
      {
        return p->w[i].pixmap;
      }
    }
  }

  return NULL;

#if 0

  if (p->head > p->tail)   /*this indicates it is not full*/
  {
    for (i = p->tail;i < p->head;i++)
    {
      if (p->lookup_table[i] == key)
      {
        printf("Hit!\n");
        //              g_object_ref(p->w[i].pixmap);
        return p->w[i].pixmap;
      }
    }
  }

  else if (p->head != p->tail)
  {
    for (i = 0;i < p->size;i++)
    {
      if (p->lookup_table[i] == key)
      {
        printf("Hit!\n");
        //           g_object_ref(p->w[i].pixmap);
        return p->w[i].pixmap;
      }
    }
  }

  return NULL;

#endif
}

static void add_pixmap(Small_Pixmap_cache *p, dashboard_cairo_widget c_widge, guint64 key)
{
//    dashboard_cairo_widget old= p->w[ p->tail ];
  p->w[p->head] = c_widge;
//   g_object_ref(c_widge.pixmap);
  p->lookup_table[p->head] = key;
  p->head++;

  if (p->head == p->size)
  {
    p->head = 0;
  }

  if (p->tail == p->head)
  {
    p->tail++;

    if (p->tail == p->size)
      p->tail = 0;

    if (p->w[p->tail].pixmap)
    {
      g_object_unref(p->w[p->tail].pixmap);
      cairo_destroy(p->w[p->tail].cr);
      p->w[p->tail].pixmap = NULL;
    }
  }

}

static void set_background(Awntop_cairo_plug_data * data, cairo_t * cr)
{

  cairo_set_source_rgba(cr, data->bg.red, data->bg.green, data->bg.blue, data->bg.alpha);

}

static void set_foreground(Awntop_cairo_plug_data * data, cairo_t * cr)
{

  cairo_set_source_rgba(cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);

}

static void invalidate_all_pixmap_caches(Awntop_cairo_plug_data * data)
{
  invalidate_pixmap_cache(data->pid_pixmaps);
  invalidate_pixmap_cache(data->uid_pixmaps);
  invalidate_pixmap_cache(data->virt_res_pixmaps);
  invalidate_pixmap_cache(data->cpu_mem_pixmaps);
  invalidate_pixmap_cache(data->procname_pixmaps);
}


static void build_top_table(Awntop_cairo_plug_data * data)
{
  int i;
  GtkWidget *eb;
  Topentry **topentries = data->topentries;
  int num_top_entries = data->num_top_entries;
  GtkWidget * widget;
  GdkPixmap * pixmap = NULL;
  gboolean force;
  dashboard_cairo_widget c_widge;
  g_free(data->displayed_pid_list);
  gboolean samepid;
  cairo_text_extents_t     te;

  data->displayed_pid_list = g_malloc(sizeof(long) * data->maxtopentries);

  force = data->invalidate_pixmaps; /*saving because state might change mid render*/

  if (force)
  {
    invalidate_all_pixmap_caches(data);
    build_top_table_headings(data);
    data->invalidate_pixmaps = FALSE;
  }

  for (i = 0;(i < num_top_entries) && (i < data->maxtopentries);i++)
  {
    char buf[100];

    struct passwd * userinfo;
    assert(i <= data->maxtopentries);
    data->displayed_pid_list[i] = topentries[i]->pid; /*array of pids that show in top.  Used for kill events*/
#if 0

    if (!force)   //&& topentries[i]->pid==data->prev_pid[i] )
    {
      continue;
    }

#endif
    samepid = (data->prev_pid[i] == topentries[i]->pid);

    data->prev_pid[i] = topentries[i]->pid;

    /*look for a widget for pid if not found then create one*/
    if (!samepid || force)
    {
      pixmap = lookup_pixmap(data->pid_pixmaps, topentries[i]->pid);
      eb = gtk_event_box_new();
      gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

      if (pixmap)
      {
        widget = gtk_image_new_from_pixmap(pixmap, NULL);
      }
      else
      {
        /*ok... not turning this into functions just so I can micromanage*/
        widget = get_cairo_widget(&c_widge,
                                  Global_tableheadings[0].unscaled_width * data->size_mult,
                                  15 * data->size_mult);
        set_background(data, c_widge.cr);
        cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
        cairo_paint(c_widge.cr);
        set_foreground(data, c_widge.cr);
        cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
        cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
        snprintf(buf, sizeof(buf), "%ld", topentries[i]->pid);
        cairo_text_extents(c_widge.cr, buf, &te);
//                cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);
        cairo_move_to(c_widge.cr, Global_tableheadings[0].unscaled_width*data->size_mult*0.6 - te.width, 12*data->size_mult);
        cairo_show_text(c_widge.cr, buf);
        add_pixmap(data->pid_pixmaps, c_widge, topentries[i]->pid);
      }

      gtk_container_add(GTK_CONTAINER(eb), widget);

      gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                                0, 1, i + 2, i + 3);

      if (data->widgets[0][i])
      {
        gtk_widget_hide(data->widgets[0][i]);
        gtk_widget_destroy(data->widgets[0][i]);
        data->widgets[0][i] = NULL;
      }

      gtk_widget_show_all(eb);

      data->widgets[0][i] = eb;
    }

//=================================================
    if (!samepid || force)
    {

      userinfo = getpwuid(topentries[i]->uid);
      /*look for a widget for pid if not found then create one*/
      pixmap = lookup_pixmap(data->uid_pixmaps, topentries[i]->uid);
      eb = gtk_event_box_new();
      gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

      if (pixmap)
      {
        widget = gtk_image_new_from_pixmap(pixmap, NULL);
      }
      else
      {
        widget = get_cairo_widget(&c_widge,
                                  Global_tableheadings[1].unscaled_width * data->size_mult,
                                  15 * data->size_mult);
        set_background(data, c_widge.cr);
        cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
        cairo_paint(c_widge.cr);
        set_foreground(data, c_widge.cr);
        cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
        cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
//                cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);

        if (userinfo)
        {
          cairo_text_extents(c_widge.cr, userinfo->pw_name, &te);
          cairo_move_to(c_widge.cr, Global_tableheadings[1].unscaled_width*data->size_mult*0.8 - te.width, 12*data->size_mult);
          cairo_show_text(c_widge.cr, userinfo->pw_name);
        }
        else
        {
          snprintf(buf, sizeof(buf), "%ld", topentries[i]->pid);
          cairo_text_extents(c_widge.cr, buf, &te);
          cairo_move_to(c_widge.cr, Global_tableheadings[1].unscaled_width*data->size_mult*0.8 - te.width, 12*data->size_mult);
          cairo_show_text(c_widge.cr, buf);
        }

        g_object_ref(c_widge.pixmap);

        add_pixmap(data->uid_pixmaps, c_widge, topentries[i]->uid);
      }

      gtk_container_add(GTK_CONTAINER(eb), widget);

      gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                                1, 2, i + 2, i + 3);

      if (data->widgets[1][i])
      {
        gtk_widget_hide(data->widgets[1][i]);
        gtk_widget_destroy(data->widgets[1][i]);
        data->widgets[1][i] = NULL;
      }

      gtk_widget_show_all(eb);

      data->widgets[1][i] = eb;
    }

//=================================================
    guint64 tmp_virt2, tmp_virt;

    tmp_virt2 = tmp_virt = topentries[i]->virt / 1024;         /*FIXME?? consider as a fn*/

    pixmap = lookup_pixmap(data->virt_res_pixmaps, tmp_virt);

    eb = gtk_event_box_new();

    gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

    if (pixmap)
    {
      widget = gtk_image_new_from_pixmap(pixmap, NULL);
    }
    else
    {
      if (tmp_virt >= 10000)
      {
        tmp_virt = tmp_virt / 1024;   //convert K into M
        snprintf(buf, sizeof(buf), "%0.0lfM", (double)tmp_virt);
      }
      else
      {
        snprintf(buf, sizeof(buf), "%0.0lf", (double)tmp_virt);
      }

      widget = get_cairo_widget(&c_widge,

                                Global_tableheadings[2].unscaled_width * data->size_mult,
                                15 * data->size_mult);
      set_background(data, c_widge.cr);
      cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(c_widge.cr);
      set_foreground(data, c_widge.cr);
      cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
      cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
      cairo_text_extents(c_widge.cr, buf, &te);
//            cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);
      cairo_move_to(c_widge.cr, Global_tableheadings[2].unscaled_width*data->size_mult*0.9 - te.width, 12*data->size_mult);
      cairo_show_text(c_widge.cr, buf);
      g_object_ref(c_widge.pixmap);
      add_pixmap(data->virt_res_pixmaps, c_widge, tmp_virt2);
    }

    gtk_container_add(GTK_CONTAINER(eb), widget);

    gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                              2, 3, i + 2, i + 3);

    if (data->widgets[2][i])
    {
      gtk_widget_hide(data->widgets[2][i]);
      gtk_widget_destroy(data->widgets[2][i]);
      data->widgets[2][i] = NULL;
    }

    gtk_widget_show_all(eb);

    data->widgets[2][i] = eb;

//=================================================

    tmp_virt2 = tmp_virt = topentries[i]->res / 1024;              /*FIXME?? consider as a fn*/
    pixmap = lookup_pixmap(data->virt_res_pixmaps, tmp_virt);
    eb = gtk_event_box_new();
    gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

    if (pixmap)
    {
      widget = gtk_image_new_from_pixmap(pixmap, NULL);
    }
    else
    {
      if (tmp_virt >= 10000)
      {
        tmp_virt = tmp_virt / 1024;   //convert K into M
        snprintf(buf, sizeof(buf), "%0.0lfM", (double)tmp_virt);
      }
      else
      {
        snprintf(buf, sizeof(buf), "%0.0lf", (double)tmp_virt);
      }

      widget = get_cairo_widget(&c_widge,

                                Global_tableheadings[3].unscaled_width * data->size_mult,
                                15 * data->size_mult);
      set_background(data, c_widge.cr);
      cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(c_widge.cr);
      set_foreground(data, c_widge.cr);
      cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
      cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
      cairo_text_extents(c_widge.cr, buf, &te);
      cairo_move_to(c_widge.cr, Global_tableheadings[3].unscaled_width*data->size_mult*0.9 - te.width, 12*data->size_mult);
//            cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);
      cairo_show_text(c_widge.cr, buf);
      g_object_ref(c_widge.pixmap);
      add_pixmap(data->virt_res_pixmaps, c_widge, tmp_virt2);
    }

    gtk_container_add(GTK_CONTAINER(eb), widget);

    gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                              3, 4, i + 2, i + 3);

    if (data->widgets[3][i])
    {
      gtk_widget_hide(data->widgets[3][i]);
      gtk_widget_destroy(data->widgets[3][i]);
      data->widgets[3][i] = NULL;
    }

    gtk_widget_show_all(eb);

    data->widgets[3][i] = eb;


//=================================================

    pixmap = lookup_pixmap(data->cpu_mem_pixmaps, topentries[i]->cpu);
    eb = gtk_event_box_new();
    gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

    if (pixmap)
    {
      widget = gtk_image_new_from_pixmap(pixmap, NULL);
    }
    else
    {
      snprintf(buf, sizeof(buf), "%ld", topentries[i]->cpu);
      widget = get_cairo_widget(&c_widge,
                                Global_tableheadings[4].unscaled_width * data->size_mult,
                                15 * data->size_mult);
      set_background(data, c_widge.cr);
      cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(c_widge.cr);
      set_foreground(data, c_widge.cr);
      cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
      cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
      cairo_text_extents(c_widge.cr, buf, &te);
      cairo_move_to(c_widge.cr, Global_tableheadings[4].unscaled_width*data->size_mult*0.7 - te.width, 12*data->size_mult);
//            cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);
      cairo_show_text(c_widge.cr, buf);
      g_object_ref(c_widge.pixmap);
      add_pixmap(data->cpu_mem_pixmaps, c_widge, topentries[i]->cpu);
    }

    gtk_container_add(GTK_CONTAINER(eb), widget);

    gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                              4, 5, i + 2, i + 3);

    if (data->widgets[4][i])
    {
      gtk_widget_hide(data->widgets[4][i]);
      gtk_widget_destroy(data->widgets[4][i]);
      data->widgets[4][i] = NULL;
    }

    gtk_widget_show_all(eb);

    data->widgets[4][i] = eb;


    /*we can reuse the cpu pixmap cache */

    pixmap = lookup_pixmap(data->cpu_mem_pixmaps, topentries[i]->mem);
    eb = gtk_event_box_new();
    gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

    if (pixmap)
    {
      widget = gtk_image_new_from_pixmap(pixmap, NULL);
    }
    else
    {
      snprintf(buf, sizeof(buf), "%0.0lf", (double)topentries[i]->mem);
      widget = get_cairo_widget(&c_widge,
                                Global_tableheadings[5].unscaled_width * data->size_mult,
                                15 * data->size_mult);
      set_background(data, c_widge.cr);
      cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(c_widge.cr);
      set_foreground(data, c_widge.cr);
      cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
      cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
//            cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);
      cairo_text_extents(c_widge.cr, buf, &te);
      cairo_move_to(c_widge.cr, Global_tableheadings[5].unscaled_width*data->size_mult*0.7 - te.width, 12*data->size_mult);
      cairo_show_text(c_widge.cr, buf);
      g_object_ref(c_widge.pixmap);
      add_pixmap(data->cpu_mem_pixmaps, c_widge, topentries[i]->mem);
    }

    gtk_container_add(GTK_CONTAINER(eb), widget);

    gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                              5, 6, i + 2, i + 3);

    if (data->widgets[5][i])
    {
      gtk_widget_hide(data->widgets[5][i]);
      gtk_widget_destroy(data->widgets[5][i]);
      data->widgets[5][i] = NULL;

    }

    gtk_widget_show_all(eb);

    data->widgets[5][i] = eb;

#if 1

    if (!samepid || force)
    {

      eb = gtk_event_box_new();
      gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);
      widget = lookup_icon(data, topentries, i);

      gtk_container_add(GTK_CONTAINER(eb), widget);
      gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                                6, 7, i + 2, i + 3);

      if (data->widgets[6][i])
      {
        gtk_widget_hide(data->widgets[6][i]);
        gtk_widget_destroy(data->widgets[6][i]);
        data->widgets[6][i] = NULL;

      }

      gtk_widget_show_all(eb);

      data->widgets[6][i] = eb;
    }

#endif
    if (!samepid || force)
    {

      pixmap = lookup_pixmap(data->procname_pixmaps, topentries[i]->pid);
      eb = gtk_event_box_new();
      gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);

      if (pixmap)
      {
        widget = gtk_image_new_from_pixmap(pixmap, NULL);
      }
      else
      {
        widget = get_cairo_widget(&c_widge,
                                  Global_tableheadings[7].unscaled_width * data->size_mult,
                                  15 * data->size_mult);
        set_background(data, c_widge.cr);
        cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
        cairo_paint(c_widge.cr);
        set_foreground(data, c_widge.cr);
        cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
        cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
        cairo_move_to(c_widge.cr, 9*data->size_mult, 12*data->size_mult);
        cairo_show_text(c_widge.cr, topentries[i]->cmd);
        g_object_ref(c_widge.pixmap);
        add_pixmap(data->procname_pixmaps, c_widge, topentries[i]->pid);
      }

      gtk_container_add(GTK_CONTAINER(eb), widget);

      gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                                7, 8, i + 2, i + 3);

      if (data->widgets[7][i])
      {
        gtk_widget_hide(data->widgets[7][i]);
        gtk_widget_destroy(data->widgets[7][i]);
        data->widgets[7][i] = NULL;

      }

      gtk_widget_show_all(eb);

      data->widgets[7][i] = eb;
    }

#if 1

    /*FIXME yes... we can optimize this*/
    if (!samepid || force)
    {
      eb = get_icon_event_box(data, "xkill", GTK_STOCK_CLOSE, GTK_ICON_SIZE_MENU);

      g_signal_connect(G_OBJECT(eb), "button-press-event",
                       G_CALLBACK(_time_to_kill),
                       (gpointer)&data->displayed_pid_list[i]);

      gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                                8, 9, i + 2, i + 3);

      if (data->widgets[8][i])
      {
        gtk_widget_hide(data->widgets[8][i]);
        gtk_widget_destroy(data->widgets[8][i]);
        data->widgets[8][i] = NULL;

      }

      gtk_widget_show_all(eb);

      data->widgets[8][i] = eb;
    }

#endif

  }
}

static void build_top_table_headings(Awntop_cairo_plug_data * data)
{
  assert(check_ptr == data);
  int i;
  GtkWidget * eb;
  GtkWidget * widget;
  dashboard_cairo_widget c_widge;
  static GtkWidget * widgets[9] = {NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL}; /*FIXME*/

  for (i = 0;i < 9;i++)  /*FIXME*/
  {
    widget = get_cairo_widget(&c_widge, Global_tableheadings[i].unscaled_width * data->size_mult, 20 * data->size_mult);
    use_bg_rgba_colour(c_widge.cr);
    cairo_set_source_rgba(c_widge.cr, data->fg.red, data->fg.green, data->fg.blue, data->fg.alpha);
    cairo_set_operator(c_widge.cr, CAIRO_OPERATOR_SOURCE);
    cairo_paint(c_widge.cr);
    cairo_set_source_rgba(c_widge.cr, data->bg.red, data->bg.green, data->bg.blue, data->bg.alpha);
    cairo_select_font_face(c_widge.cr, "Sans", CAIRO_FONT_SLANT_ITALIC, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(c_widge.cr, 10.0*data->size_mult);
    cairo_move_to(c_widge.cr, 10*data->size_mult, 15*data->size_mult);
    cairo_show_text(c_widge.cr, Global_tableheadings[i].name);

    if (Global_tableheadings[i].fn)
    {
      eb = gtk_button_new();
      eb = gtk_event_box_new();
      g_signal_connect(G_OBJECT(eb), "button-press-event", G_CALLBACK(Global_tableheadings[i].fn), (gpointer)data);
//            gtk_button_set_relief (GTK_BUTTON (eb), GTK_RELIEF_NONE);
      gtk_container_add(GTK_CONTAINER(eb), widget);
    }
    else
    {
      eb = gtk_event_box_new();
      gtk_event_box_set_visible_window((GtkEventBox *)eb, FALSE);
      gtk_container_add(GTK_CONTAINER(eb), widget);
    }


    /*eb may be an eventbox or a button*/
    gtk_table_attach_defaults(GTK_TABLE(data->table), eb,
                              i, i + 1, 0, 1);

    if (widgets[i])
    {
      gtk_widget_destroy(widgets[i]);
    }

    gtk_widget_show_all(eb);

    widgets[i] = eb;
    del_cairo_widget(&c_widge);
  }

}

static gboolean render(GtkWidget ** pwidget, gint interval, Awntop_cairo_plug_data **p)
{
  assert(check_ptr == *p);
  Awntop_cairo_plug_data * data = *p;
  GSList* removelist;

  if (! *pwidget)
  {
    *pwidget = data->table;
    build_top_table_headings(data);
    return TRUE;
  }

  data->accum_interval = data->accum_interval + interval;

  if (!top_state)
  {
    return FALSE;
  }

  if ((data->accum_interval < data->updateinterval) && (!data->forceupdatefixup))
  {
    return FALSE;
  }

  if (data->topentries)
  {
    free_topentries(data->topentries, data->num_top_entries);
  }

  data->topentries = fill_topentries(data, &data->num_top_entries);      /*call free_topentries when done*/

  qsort(data->topentries, (size_t) data->num_top_entries , sizeof(Topentry *), data->compar);
  removelist = NULL;
  g_tree_foreach(data->proctimes, proctime_find_inactive, &removelist);
  g_slist_foreach(removelist, proctimes_remove_inactive, data->proctimes);
  g_slist_free(removelist);

  if (!data->displayed_pid_list)
  {
    data->displayed_pid_list = g_malloc(sizeof(long) * data->maxtopentries);
  }

  build_top_table(data);

  data->forceupdatefixup = FALSE;
  data->accum_interval = 0;
  return FALSE;
}

/*filles up topentries with pointers to struct vars(did this way to make qsort faster).
numel is number of elements
*/
static Topentry ** fill_topentries(Awntop_cairo_plug_data *awntop, int *numel)
{
  glibtop_proclist proclist;
  glibtop_proc_state proc_state;
  glibtop_proc_time  proc_time;
  glibtop_proc_uid   proc_uid;
  glibtop_proc_mem   proc_mem;
  glibtop_cpu         cpu;
  static guint64 old_total_jiffies = 0;
  guint64 total_jiffies;
  pid_t * p;
  long percent;
  int i;
  Topentry **topentries;
  Proctimeinfo *value;
  int *ptmp;
  double jiffies;

  glibtop_get_cpu(&cpu);
  total_jiffies = cpu.total;
  glibtop_get_mem(&awntop->libtop_mem);

  switch (awntop->filterlevel)
  {

    case 0:
      p = glibtop_get_proclist(&proclist, GLIBTOP_KERN_PROC_RUID, getuid());
      break;

    case 1:
      p = glibtop_get_proclist(&proclist, GLIBTOP_KERN_PROC_ALL, -1);
      break;
  }



  *numel = proclist.number;

  topentries = g_malloc(sizeof(Topentry*) * proclist.number);
  g_tree_foreach(awntop->proctimes, proctime_reset_active, NULL);

  for (i = 0;i < proclist.number;i++)
  {
    topentries[i] = g_malloc(sizeof(Topentry));
    topentries[i]->pid = p[i];
    glibtop_get_proc_state(&proc_state, p[i]);
    strncpy(topentries[i]->cmd, proc_state.cmd, sizeof(topentries[i]->cmd));

    /*  Leave this here - gets full command line.
    {
            glibtop_proc_args buf;
            char *a=glibtop_get_proc_args(&buf,p[i],256 );
            printf("%s\n",a);

    }*/
    glibtop_get_proc_time(&proc_time, p[i]);
    value = g_tree_lookup(awntop->proctimes, &p[i]);

    if (value)
    {
      long time_diff;
      jiffies = total_jiffies - old_total_jiffies;
      time_diff = (proc_time.utime + proc_time.stime) - value->proctime;
      value->proctime = proc_time.utime + proc_time.stime;
      percent = round(time_diff / (jiffies / cpu.frequency)) ;
    }
    else
    {
      ptmp = g_malloc(sizeof(guint64));
      *ptmp = p[i];
      value = g_malloc(sizeof(Proctimeinfo));
      value->proctime = proc_time.utime + proc_time.stime;
      g_tree_insert(awntop->proctimes, ptmp, value);
      percent = 0;
    }

    value->accessed = TRUE;

    topentries[i]->cpu = percent ;

    glibtop_get_proc_uid(&proc_uid, p[i]);
    topentries[i]->uid = proc_uid.uid ;
    topentries[i]->nice = proc_uid.nice ;
    glibtop_get_proc_mem(&proc_mem, p[i]);
    topentries[i]->mem = proc_mem.resident * 100 / awntop->libtop_mem.total  ;
    topentries[i]->res = proc_mem.resident ;
    topentries[i]->virt = proc_mem.vsize ;
  }

  old_total_jiffies = total_jiffies;

  g_free(p);
  return topentries;
}

static gboolean proctime_find_inactive(gpointer key, gpointer value, gpointer data)
{
  Proctimeinfo * p = value;
  GSList** removelist = data;

  if (! p->accessed)
  {
//        printf("dummy=%d\n",p->dummy);
    *removelist = g_slist_prepend(*removelist, key);
  }

  return FALSE;
}

static void proctimes_remove_inactive(gpointer data, gpointer user_data)
{
  int *p = data;
  GTree *tree = user_data;
  g_tree_remove(tree, p);

}

static gboolean proctime_reset_active(gpointer key, gpointer value, gpointer data)
{
  Proctimeinfo * p;

  p = value;
  p->accessed = FALSE;
  return FALSE;
}


static void free_topentries(Topentry **topentries, int num_top_entries)
{
  int i;

  for (i = 0;i < num_top_entries;i++)
  {
    g_free(topentries[i]);
  }

  g_free(topentries);
}


/*used for binary tree of proctime*/
static gint proctime_key_compare_func(gconstpointer a, gconstpointer b,   gpointer user_data)
{
  /*Returns :  negative value if a < b; zero if a = b; positive value if a > b.*/
  const int *p1, *p2;
  p1 = a;
  p2 = b;
  return (*p1 - *p2);
}


/*used for binary tree of icons and binary tree of pixbufs*/
static gint icons_key_compare_func(gconstpointer a, gconstpointer b,   gpointer user_data)
{
  /*Returns :  negative value if a < b; zero if a = b; positive value if a > b.*/
  const char *p1, *p2;
  p1 = a;
  p2 = b;
  return (strcmp(p1, p2));
}

/************Section:  qsort compare functions-------------*/
static int cmppid(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return ((*l)->pid - (*r)->pid) * gcomparedir;
}

/*FIXME ???  currently sort on uid not user name */
static int cmpuser(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return ((*l)->uid - (*r)->uid) * gcomparedir;
}

static gint64 cmpvirt(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return ((*l)->virt - (*r)->virt) * gcomparedir;
}

static gint64 cmpres(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return ((*l)->res - (*r)->res) * gcomparedir;
}

static int cmpcpu(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return ((*l)->cpu - (*r)->cpu) * gcomparedir;
}

static gint64 cmpmem(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return ((*l)->mem - (*r)->mem) * gcomparedir;
}

static int cmpcommand(const void * p1 , const void * p2)
{
  Topentry ** l = (Topentry **) p1;
  Topentry ** r = (Topentry **) p2;

  return strcmp((*l)->cmd, (*r)->cmd) * gcomparedir;
}




static void parse_desktop_entries(Awntop_cairo_plug_data * awntop)
{

  struct dirent **namelist;
  int n;
  char * pXDG_desktop_dir;
  char * pXDG_desktop_dir_home;
  char * pXDG_alldirs;
  char * ptmp;
  char * tok;
  GKeyFile*   keyfile;
  char *pvalue;

  pXDG_desktop_dir = strdup(ptmp = getenv("XDG_DATA_DIRS") ? ptmp : "/usr/share");   /*FIXME if strdup return NULL...  I guess it could happen*/

  pXDG_desktop_dir_home = strdup(ptmp = getenv("XDG_DATA_HOME") ? ptmp : "/usr/local/share");

  pXDG_alldirs = malloc(strlen(pXDG_desktop_dir) + strlen(pXDG_desktop_dir_home) + 2);

  if (pXDG_alldirs)
  {
    strcpy(pXDG_alldirs, pXDG_desktop_dir_home);
    strcat(pXDG_alldirs, ":");
    strcat(pXDG_alldirs, pXDG_desktop_dir);

//        printf("pXDG_desktop_dir = %s\n",pXDG_alldirs);

    for (tok = strtok(pXDG_alldirs, ":");tok;tok = strtok(NULL, ":"))      /*FIXME - hard coded token*/
    {
      char * pdirname;
      pdirname = malloc(strlen(tok) + strlen("/applications") + 1);      /*FIXME*/
      strcpy(pdirname, tok);
      strcat(pdirname, "/applications");
//            printf("%s\n",pdirname);

      n = scandir(pdirname, &namelist, 0, alphasort);

      if (n < 0)
        perror("error opening desktop files");
      else
      {
        while (n--)
        {
          char *fullpath;
          fullpath = malloc(strlen(pdirname) + strlen(namelist[n]->d_name) + 2);

          if (fullpath)
          {
            strcpy(fullpath, pdirname);             /*FIXME -need to look into the variations on g_key_file_load_from_file*/
            strcat(fullpath, "/");
            strcat(fullpath, namelist[n]->d_name);
            keyfile = g_key_file_new();

            if (g_key_file_load_from_file(keyfile, fullpath, 0, NULL))
            {
              char *iconname;

              if ((iconname = g_key_file_get_string(keyfile, "Desktop Entry", "Icon", NULL)) != NULL)
              {
                char * execname;

                if ((execname = g_key_file_get_string(keyfile, "Desktop Entry", "Exec", NULL)) != NULL)
                {
                  ptmp = strchr(execname, ' ');

                  if (ptmp)
                    *ptmp = '\0';

                  pvalue = g_tree_lookup(awntop->icons, execname);

                  if (!pvalue)
                  {
                    g_tree_insert(awntop->icons, execname, strdup(iconname)); /*FIXME*/
                  }
                  else
                  {
                    g_free(execname);
                  }
                }

                g_free(iconname);
              }
              else
              {
                //                              printf("key not found \n");
              }

            }
            else
            {
//                            printf("Failed to load keyfile: %s\n",fullpath);
            }

            g_key_file_free(keyfile);

            free(namelist[n]);
            free(fullpath);
          }
        }

        free(namelist);
      }

      free(pdirname);
    }
  }

  free(pXDG_alldirs);

  /*FIXME --- below - obviously*/

  if (!g_tree_lookup(awntop->icons, "firefox-bin"))
  {
    g_tree_insert(awntop->icons, "firefox-bin", strdup("firefox-icon.png"));
  }

  if (!g_tree_lookup(awntop->icons, "bash"))
  {
    g_tree_insert(awntop->icons, "bash", strdup("terminal"));
  }

  if (!g_tree_lookup(awntop->icons, "sh"))
  {
    g_tree_insert(awntop->icons, "sh", strdup("terminal"));
  }

  if (!g_tree_lookup(awntop->icons, "dash"))
  {
    g_tree_insert(awntop->icons, "dash", strdup("terminal"));
  }

  if (!g_tree_lookup(awntop->icons, "ash"))
  {
    g_tree_insert(awntop->icons, "ash", strdup("terminal"));
  }

  if (!g_tree_lookup(awntop->icons, "csh"))
  {
    g_tree_insert(awntop->icons, "csh", strdup("terminal"));
  }

//    free(ptmp);
}

/*FIXME  - clean this function up*/
static GtkWidget * lookup_icon(Awntop_cairo_plug_data * awntop, Topentry **topentries, int i)
{
  GtkIconTheme*  g;
  GdkPixbuf* pbuf = NULL;
  char* parg;
  glibtop_proc_args     procargs;
  char *ptmp;
  GtkWidget *image;
  char *pvalue = NULL;
  char *p;

  parg = glibtop_get_proc_args(&procargs, topentries[i]->pid, 256);
  ptmp = strchr(parg, ' ');

  if (ptmp)
    *ptmp = '\0';

  pbuf = g_tree_lookup(awntop->pixbufs, parg);

  if (pbuf)
  {
    if (pbuf == Stock_Image_Used)
    {
      image = gtk_image_new_from_stock(GTK_STOCK_EXECUTE, GTK_ICON_SIZE_MENU);
    }
    else
    {
#if 0
      cairo_t *cr;
      GdkPixmap * pixma;

      pixma = gdk_pixmap_new(NULL, 16, 16, 32);
      image = gtk_image_new_from_pixmap(pixma, NULL);
      gdk_drawable_set_colormap(pixma, gdk_screen_get_rgba_colormap(gtk_widget_get_screen(awntop->table)));
      cr = gdk_cairo_create(pixma);
      cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
      cairo_paint(cr);
      gdk_cairo_set_source_pixbuf(cr, pbuf, 0, 0);
      cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
      cairo_paint(cr);
      cairo_destroy(cr);
      g_object_unref(pixma);
#endif
      image = gtk_image_new_from_pixbuf(pbuf);
    }

    g_free(parg);

    return image;
  }


  if (!parg && !(*parg))
  {
    pvalue = g_tree_lookup(awntop->icons, topentries[i]->cmd);

    if (!pvalue)
    {
      pvalue = g_tree_lookup(awntop->icons, basename(topentries[i]->cmd));
    }
  }
  else
  {

    pvalue = g_tree_lookup(awntop->icons, parg);

    if (!pvalue)
    {
      pvalue = g_tree_lookup(awntop->icons, basename(parg));
    }

  }

  if (pvalue)
  {
    g = gtk_icon_theme_get_default();
    pbuf = gtk_icon_theme_load_icon(g, pvalue, 16, 0, NULL);

    if (!pbuf)
    {

      p = malloc(strlen("/usr/share/pixmaps/") + strlen(basename(pvalue)) + 1);
      strcpy(p, "/usr/share/pixmaps/");
      strcat(p, basename(pvalue));
      pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
      free(p);

      if (!pbuf)
      {
        p = malloc(strlen("/usr/local/share/pixmaps/") + strlen(basename(pvalue)) + 1);
        strcpy(p, "/usr/local/share/pixmaps/");
        strcat(p, basename(pvalue));
        pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
        free(p);
      }
    }


  }
  else
  {
    p = malloc(strlen("/usr/share/pixmaps/") + strlen(basename(parg)) + 1 + strlen(".png"));
    strcpy(p, "/usr/share/pixmaps/");
    strcat(p, basename(parg));
    strcat(p, ".png");
    pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
    free(p);

    if (!pbuf)
    {
      p = malloc(strlen("/usr/local/share/pixmaps/") + strlen(basename(parg)) + 1 + strlen(".png"));
      strcpy(p, "/usr/local/share/pixmaps/");
      strcat(p, basename(parg));
      strcat(p, ".png");
      pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
      free(p);

      if (!pbuf)
      {
        p = malloc(strlen("/usr/share/pixmaps/") + strlen(basename(parg)) + 1 + strlen(".xpm"));
        strcpy(p, "/usr/share/pixmaps/");
        strcat(p, basename(parg));
        strcat(p, ".xpm");
        pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
        free(p);

        if (!pbuf)
        {
          p = malloc(strlen("/usr/local/share/pixmaps/") + strlen(basename(parg)) + 1 + strlen(".xpm"));
          strcpy(p, "/usr/local/share/pixmaps/");
          strcat(p, basename(parg));
          strcat(p, ".xpm");
          pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
          free(p);
        }
      }
    }
  }

  if (!pbuf)
  {
    image = gtk_image_new_from_stock(GTK_STOCK_EXECUTE, GTK_ICON_SIZE_MENU);
  }
  else
  {
    image = gtk_image_new_from_pixbuf(pbuf);
    g_tree_insert(awntop->pixbufs, strdup(parg), pbuf);
//        g_object_unref (pbuf);
  }

  g_free(parg);

  return image;

}

static GtkWidget * get_icon_event_box(Awntop_cairo_plug_data * awntop, char *name, const gchar *stock_id, GtkIconSize size)
{
  GtkIconTheme*  g;
  GdkPixbuf* pbuf;
  GtkWidget *image = NULL;
  GtkWidget *eventbox;
  char *p;

  pbuf = g_tree_lookup(awntop->pixbufs, name);

  if (!pbuf)
  {
    g = gtk_icon_theme_get_default();
    pbuf = gtk_icon_theme_load_icon(g, name, 16, 0, NULL);

    if (!pbuf)
    {
      p = malloc(strlen("/usr/share/pixmaps/") + strlen(name) + 1 + strlen(".png"));
      strcpy(p, "/usr/share/pixmaps/");
      strcat(p, name);
      strcat(p, ".png");
      pbuf = gdk_pixbuf_new_from_file_at_scale(p, 16, 16, FALSE, NULL);
      free(p);

      if (!pbuf)
      {
        image = gtk_image_new_from_stock(stock_id, size);
        assert(image);
        g_tree_insert(awntop->pixbufs, strdup(name), Stock_Image_Used);

        //doesn't work if it's  GTK_IMAGE_STOCK
        /*                pbuf=gtk_image_get_pixbuf(image);
                        g_object_ref(pbuf);    */
      }
    }

    if (pbuf)
    {
      g_tree_insert(awntop->pixbufs, strdup(name), pbuf);
    }
  }

  if (!image)
  {
    if (pbuf == Stock_Image_Used)
    {
      image = gtk_image_new_from_stock(stock_id, size);
    }
    else
    {
      image = gtk_image_new_from_pixbuf(pbuf);
    }
  }

  eventbox = gtk_event_box_new();

  gtk_event_box_set_visible_window(GTK_EVENT_BOX(eventbox), FALSE);
  gtk_container_add(GTK_CONTAINER(eventbox), image);

  return eventbox;
}

static gboolean _time_to_kill(GtkWidget *widget, GdkEventButton *event, long * pid)
{
  assert((G_kill_signal_method > 0) && (G_kill_signal_method < 4));

  if (G_kill_signal_method == 1)
  {
    kill(*pid, SIGTERM);   /*I'd don't really care about detecting the result at the moment...  FIXME??*/

#if 0

    if (G_kill_signal_method & 2)
    {
      kill(*pid, SIGKILL);   /*I'd don't really care about detecting the result at the moment...  FIXME??*/
    }

#endif
  }
  else if (G_kill_signal_method == 2)
  {
    printf("kill %d \n", (int) *pid);
    kill(*pid, SIGKILL);   /*I'd don't really care about detecting the result at the moment...  FIXME??*/
  }

  top_state = 1;

  return TRUE;
}


static gboolean _increase_awntop_rows(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  awntop->forceupdatefixup = TRUE;
  awntop->maxtopentries++;
  awntop->invalidate_pixmaps = TRUE;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NUM_PROCS, awntop->maxtopentries, NULL);
  return TRUE;
}

static gboolean _decrease_awntop_rows(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  int i;
  awntop->forceupdatefixup = TRUE;
  awntop->maxtopentries--;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_NUM_PROCS, awntop->maxtopentries, NULL);

  for (i = 0;i < 9;i++)   /*FIXME*/
  {
    gtk_widget_hide(awntop->widgets[i][awntop->maxtopentries]);
    gtk_widget_destroy(awntop->widgets[i][awntop->maxtopentries]);
    awntop->widgets[i][awntop->maxtopentries] = NULL;
  }

  return TRUE;
}

static gboolean _toggle_user_filter(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  awntop->filterlevel = !awntop->filterlevel;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_USER_FILTER, awntop->filterlevel, NULL);
  return TRUE;
}

static gboolean _toggle_display_freeze(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  top_state = !top_state;
  awntop->forceupdatefixup = TRUE;
  return TRUE;
}


static gboolean _click_set_term(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data*awntop)
{
  G_kill_signal_method = 1;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_KILL_SIG_METH, G_kill_signal_method, NULL);
  return TRUE;
}

static gboolean _click_set_kill(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  G_kill_signal_method = 2;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_KILL_SIG_METH, G_kill_signal_method, NULL);
  return TRUE;
}

#if 0
static gboolean _click_set_term_kill(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data*awntop)
{
  G_kill_signal_method = 3;
  gconf_client_set_int(get_dashboard_gconf(), GCONF_AWNTOP_CAIRO_KILL_SIG_METH, G_kill_signal_method, NULL);
  return TRUE;
}
#endif

static gboolean _click_pid(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data*awntop)
{
  top_state = 1;

  if (awntop->compar == cmppid)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = cmppid;
    gcomparedir = 1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}

static gboolean _click_user(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  top_state = 1;

  if (awntop->compar == cmpuser)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = cmpuser;
    gcomparedir = 1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}

static gboolean _click_virt(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  top_state = 1;

  if (awntop->compar == (AwnTopCompareFunc)cmpvirt)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = (AwnTopCompareFunc)cmpvirt;
    gcomparedir = -1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}

static gboolean _click_res(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  top_state = 1;

  if (awntop->compar == (AwnTopCompareFunc)cmpres)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = (AwnTopCompareFunc)cmpres;
    gcomparedir = -1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}

static gboolean _click_cpu(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  top_state = 1;

  if (awntop->compar == cmpcpu)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = cmpcpu;
    gcomparedir = -1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}

static gboolean _click_mem(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data*awntop)
{
  top_state = 1;

  if (awntop->compar == (AwnTopCompareFunc)cmpmem)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = (AwnTopCompareFunc)cmpmem;
    gcomparedir = -1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}

static gboolean _click_command(GtkWidget *widget, GdkEventButton *event, Awntop_cairo_plug_data *awntop)
{
  top_state = 1;

  if (awntop->compar == cmpcommand)
  {
    gcomparedir = gcomparedir * -1;
  }
  else
  {
    awntop->compar = cmpcommand;
    gcomparedir = 1;
  }

  awntop->forceupdatefixup = TRUE;

  return TRUE;
}
