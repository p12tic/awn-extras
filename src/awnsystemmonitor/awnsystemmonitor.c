/*
 * Copyright (c) 2007   Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
 *                      Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
 *
 * This is a CPU Load Applet for the Avant Window Navigator.  It
 * borrows heavily from the Gnome system monitor, so kudos go to
 * the authors of that program:
 *
 * Kevin Vandersloot <kfv101@psu.edu>
 * Erik Johnsson <zaphod@linux.nu> - icon support
 * Jorgen Scheibengruber
 * Benoît Dejean <benoit@placenet.org> - maintainer
 * Paolo Borelli <pborelli@katamail.com>
 * Baptiste Mille-Mathias - artwork
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
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <math.h>
#include "awnsystemmonitor.h"
#include "cpumetergconf.h"
#include "uptime_component.h"
#include "cpu_component.h"
#include "awntop_cairo_component.h"
#include "date_time_component.h"
#include "loadavg_component.h"
#include "sysmem_component.h"
#include "config.h"
#include "gconf-config.h"

//#undef NDEBUG
#include <assert.h>


/*
 * FUNCTION DEFINITIONS
 */
gboolean cpu_meter_render(gpointer cpumeter);
static gboolean time_handler(gpointer cpumeter);
static void get_load(LoadGraph *g);
static void init_load_graph(LoadGraph *g);
static void emit_data(LoadGraph *g);


// Events
static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _button_release_event(GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _height_changed(AwnApplet *app, guint height, gpointer *data);
static void _orient_changed(AwnApplet *appt, guint orient, gpointer *data);
static gboolean _enter_notify_event(GtkWidget *window, GdkEventButton *event, gpointer *data);
static gboolean _leave_notify_event(GtkWidget *window, GdkEvent *event, gpointer *data);
static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event, CpuMeter * applet);
static gboolean _die_die_exclamation(GtkWidget *window, GdkEvent *event, gpointer *data);
void render_graph(cairo_t * cr, LoadGraph * g, char *, int width, int height, CpuMeter* cpumeter);

static void set_colour(CpuMeter *p, AwnColor* colour, const char * mess, const char * gconf_key);

static gboolean _set_icon_graph_fg(GtkWidget *widget, GdkEventButton *event, CpuMeter *p);
static gboolean _set_icon_graph_bg(GtkWidget *widget, GdkEventButton *event, CpuMeter *p);
static gboolean _set_icon_text(GtkWidget *widget, GdkEventButton *event, CpuMeter *p);

#define GCONF_FG  GCONF_PATH "/graph_color"
#define GCONF_BG  GCONF_PATH "/bg_color"
#define GCONF_TEXT  GCONF_PATH "/border_color"


//static gint width, height;

/**
 * Create new applet
 */
CpuMeter*
cpumeter_applet_new(AwnApplet *applet)
{
  int width, height;
  CpuMeter *cpumeter = g_new0(CpuMeter, 1);
  cpumeter->loadgraph = g_new0(LoadGraph, 1);
  cpumeter->applet = applet;
  cpumeter->height = awn_applet_get_height(applet) * 2;
  cpumeter->timer_id = -1;
  cpumeter->show_title = FALSE;
  cpumeter->title = AWN_TITLE(awn_title_get_default());
  GdkScreen* pScreen;


  init_load_graph(cpumeter->loadgraph);

  // set the icon
  gtk_window_set_default_icon_name("CPU Meter");

  cpumeter->size = 0;
  cpumeter->new_size = 0;
  cpumeter->y_offset = 0;
  cpumeter->orient = GTK_ORIENTATION_HORIZONTAL;
  cpumeter->doneonce = FALSE;
  cpumeter->tooltips = gtk_tooltips_new();
  g_object_ref(cpumeter->tooltips);
  gtk_object_sink(GTK_OBJECT(cpumeter->tooltips));

  cpumeter_gconf_init(cpumeter);
  cpumeter_gconf_event(cpumeter->client, 0, NULL, cpumeter);
  set_dashboard_gconf(cpumeter->client);
  register_Dashboard(&cpumeter->dashboard, cpumeter->applet);


  pScreen = gtk_widget_get_screen(cpumeter->applet);
  height = gdk_screen_get_height(pScreen) / 2;        /*FIXME*/
  width = height * 5 / 3;


  register_Dashboard_plug(&cpumeter->dashboard, date_time_plug_lookup, width / 2, 21*2, 0x01, &cpumeter->date_time_plug);
  register_Dashboard_plug(&cpumeter->dashboard, cpu_plug_lookup, 0, 2, 0x01, &cpumeter->cpu_plug);
  register_Dashboard_plug(&cpumeter->dashboard, uptime_plug_lookup, width / 2, 21, 0x01, &cpumeter->uptime_plug);
  register_Dashboard_plug(&cpumeter->dashboard, loadavg_plug_lookup, width / 2, 21*2.5, 0x01, &cpumeter->loadavg_plug);
  register_Dashboard_plug(&cpumeter->dashboard, sysmem_plug_lookup, width / 2, 21*3.5, 0x01, &cpumeter->sysmem_plug);
//    register_Dashboard_plug(&cpumeter->dashboard,awntop_plug_lookup,0,height/5,0x00,&cpumeter->awntop);
  register_Dashboard_plug(&cpumeter->dashboard, awntop_cairo_plug_lookup, 40, height / 4.4, 0x01, &cpumeter->awntop_cairo_plug);



  // connect to button events
  g_signal_connect(G_OBJECT(cpumeter->applet), "button-release-event", G_CALLBACK(_button_release_event), (gpointer)cpumeter);
//    g_signal_connect (G_OBJECT (cpumeter->applet), "expose-event", G_CALLBACK (_expose_event), cpumeter);

  g_signal_connect(G_OBJECT(cpumeter->applet), "button-press-event", G_CALLBACK(_button_clicked_event), (gpointer)cpumeter);

  // connect to height and orientation changes
  g_signal_connect(G_OBJECT(cpumeter->applet), "height-changed", G_CALLBACK(_height_changed), (gpointer)cpumeter);
  g_signal_connect(G_OBJECT(cpumeter->applet), "orientation-changed", G_CALLBACK(_orient_changed), (gpointer)cpumeter);

  /*FIXME why doesn't this work????*/
  g_signal_connect(G_OBJECT(cpumeter->applet), "applet-deleted", G_CALLBACK(_die_die_exclamation), (gpointer)cpumeter);
  // connect to enter/leave
  g_signal_connect(G_OBJECT(cpumeter->applet), "enter-notify-event", G_CALLBACK(_enter_notify_event), (gpointer)cpumeter);
  g_signal_connect(G_OBJECT(cpumeter->applet), "leave-notify-event", G_CALLBACK(_leave_notify_event), (gpointer)cpumeter);


  cpumeter->right_click_menu = awn_applet_create_default_menu(applet);
  dashboard_build_clickable_menu_item(cpumeter->right_click_menu,
                                      G_CALLBACK(_set_icon_graph_fg), "Icon Foreground", (gpointer)cpumeter
                                     );
  dashboard_build_clickable_menu_item(cpumeter->right_click_menu,
                                      G_CALLBACK(_set_icon_graph_bg), "Icon Background", (gpointer)cpumeter
                                     );
  dashboard_build_clickable_menu_item(cpumeter->right_click_menu,
                                      G_CALLBACK(_set_icon_text), "Icon Text", (gpointer)cpumeter
                                     );
  cpumeter->timer_id = g_timeout_add(cpumeter->update_freq, (GSourceFunc*)cpu_meter_render, cpumeter);
  return cpumeter;
}

static void set_colour(CpuMeter *p, AwnColor* colour, const char * mess, const char * gconf_key)
{
  char *svalue;
  pick_awn_color(colour, mess, p, NULL);
  svalue = dashboard_cairo_colour_to_string(colour);
  gconf_client_set_string(get_dashboard_gconf(), gconf_key, svalue , NULL);
  free(svalue);
}

static gboolean _set_icon_graph_fg(GtkWidget *widget, GdkEventButton *event, CpuMeter*p)
{
  set_colour(p, &p->graph, "Icon Graph Colour", GCONF_FG);
  return TRUE;
}

static gboolean _set_icon_graph_bg(GtkWidget *widget, GdkEventButton *event, CpuMeter *p)
{
  set_colour(p, &p->bg, "Icon Background Colour", GCONF_BG);
  return TRUE;
}

static gboolean _set_icon_text(GtkWidget *widget, GdkEventButton *event, CpuMeter *p)
{
  set_colour(p, &p->border, "Icon Text Colour", GCONF_TEXT);
  return TRUE;
}


/**
 * Actually draw the applet via cairo
 * -uses draw()
 */
#if 0
static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
  CpuMeter *cpumeter = (CpuMeter *)data;
  cpu_meter_render(cpumeter);
  return TRUE;
}

#endif

/**
 * Draws everything.  Should be refactored so that we don't draw the
 * entire image every time, just the graph.
 */
gboolean cpu_meter_render(gpointer data)
{
  char text[20];

  static cairo_surface_t *surface;
  static GdkPixbuf * apixbuf;
  CpuMeter* cpumeter = (CpuMeter *)data;
  static cairo_t *cr = NULL;

  GtkWidget* widget = GTK_WIDGET(cpumeter->applet);


  AwnApplet* applet = cpumeter->applet;


#if 0
  /*me trying to trigger something in awn  Please ignore :-) */
  static GdkPixbuf * icon;
  gtk_widget_get_size_request(widget, &width, &height);
  icon = gdk_pixbuf_new(GDK_COLORSPACE_RGB, TRUE, 8, 44, 44);
  gdk_pixbuf_fill(icon, 0xff4444ee);
  awn_applet_simple_set_temp_icon(AWN_APPLET_SIMPLE(applet), icon);
  return;
#endif

  if (!cpumeter->doneonce)
  {
    if (cr)
    {
      cairo_destroy(cr);
      cr = NULL;
    }

    if (surface)
    {
      cairo_surface_destroy(surface);
      surface = NULL;
    }

    gtk_widget_get_size_request(widget, &cpumeter->width, &cpumeter->height);

    cpumeter->width = cpumeter->width - 2;
    cpumeter->height = cpumeter->height / 2 - 3;
    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, cpumeter->width, cpumeter->height * 2);
    cr = cairo_create(surface);
    assert(cr);
    cpumeter->doneonce = TRUE;


  }

  /*recreating this on every render as if I reuse it some
  bug(s) seem to get triggered in awn-applet-simple or awn-effects*/
  apixbuf = gdk_pixbuf_new(GDK_COLORSPACE_RGB, TRUE, 8, cpumeter->width, cpumeter->height * 2);

  LoadGraph* g = cpumeter->loadgraph;

  render_graph(cr, g, text, cpumeter->width, cpumeter->height, cpumeter);

  surface_2_pixbuf(apixbuf, surface);

  awn_applet_simple_set_temp_icon(AWN_APPLET_SIMPLE(cpumeter->applet),
                                  apixbuf);

  if (cpumeter->show_title)
  {
    awn_title_show(cpumeter->title, GTK_WIDGET(cpumeter->applet), text);
  }
  else
  {
    awn_title_hide(cpumeter->title, GTK_WIDGET(cpumeter->applet));
  }

  return TRUE;
}

void render_graph(cairo_t * cr, LoadGraph * g, char* text, int width, int height, CpuMeter* cpumeter)
{
  gint i, j;
  gfloat percent;
  cairo_pattern_t *pattern = NULL;

  /* Clear the background to transparent */
  cairo_set_source_rgba(cr, 1.0, 1.0, 1.0, 0.0);
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint(cr);

  /* Set back to opaque */
  cairo_set_operator(cr, CAIRO_OPERATOR_OVER);

  /* Set the background color */
  awn_cairo_rounded_rect(cr, PAD - 1, height + 1, width - PAD - 4, height - PAD - 1, ARC, ROUND_ALL);
  cairo_set_source_rgba(cr, cpumeter->bg.red, cpumeter->bg.green, cpumeter->bg.blue, cpumeter->bg.alpha);
  cairo_fill(cr);

  /* Get the load and paint it */
  get_load(g);
  assert((g->index) <= NUM_POINTS);
  assert((g->index) >= 0);
  guint percent_now;

  if (g->index > 0)
  {
    percent_now = round(g->data[(g->index)-1] * 100.0);
    percent_now = percent_now > 100 ? 100 : percent_now;
  }
  else
  {
    percent_now = 0;
  }

  i = width - 6;

  j = g->index - 1;

  if (j < 0)
  {
    j = NUM_POINTS - 1;
  }

  guint top = height + PAD;

  guint bottom = height * 2 - PAD;
  guint tallest = bottom - top;
  cairo_set_line_width(cr, 1.0);

  while (i > PAD)
  {
    assert(j < NUM_POINTS);
    assert(j >= 0);
    percent = g->data[j];

    if (percent > 0 && percent <= 1.0)
    {
      cairo_set_source_rgba(cr, cpumeter->graph.red, cpumeter->graph.green, cpumeter->graph.blue, cpumeter->graph.alpha);
      cairo_move_to(cr, i, bottom - round((float)tallest * percent));
      cairo_line_to(cr, i, bottom);
      cairo_stroke(cr);
    }

    if (j == 0)
    {
      j = NUM_POINTS - 1;
    }
    else
    {
      j--;
    }

    i--;
  }

  cairo_set_line_width(cr, cpumeter->border_width);

  cairo_set_source_rgba(cr, cpumeter->border.red, cpumeter->border.green, cpumeter->border.blue, cpumeter->border.alpha);
  awn_cairo_rounded_rect(cr, PAD - 1, height + 1, width - PAD - 4, height - PAD - 1, ARC, ROUND_ALL);
  cairo_stroke(cr);

  if (cpumeter->do_gradient)
  {
    awn_cairo_rounded_rect(cr, PAD - 1, height + 1, width - PAD - 4, height - PAD - 1, ARC, ROUND_ALL);
    pattern = cairo_pattern_create_linear(28, 68, 28, 48);
    cairo_pattern_add_color_stop_rgba(pattern, 0.00,  .1, .1, .1, .1);
    cairo_pattern_add_color_stop_rgba(pattern, 1.00,  .99, .99, .99, .1);
    cairo_set_source(cr, pattern);
    cairo_fill(cr);
  }

  bzero(text, sizeof(text));

  snprintf(text, 20, "CPU %d%%", percent_now);

  if (cpumeter->do_subtitle)
  {
    cairo_set_source_rgba(cr, cpumeter->border.red, cpumeter->border.green, cpumeter->border.blue, cpumeter->border.alpha);
    cairo_select_font_face(cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size(cr, 8.0);
    cairo_move_to(cr, PAD - 2, bottom + 7);
    cairo_show_text(cr, text);
  }

  if (pattern)
    cairo_pattern_destroy(pattern);

}


/**
 * Almost a one-for-one ripoff from Gnome Process Monitor's
 * get_load function in load-graph.cpp:
 */
static void
get_load(LoadGraph *g)
{
  guint i;
  glibtop_cpu cpu;

  glibtop_get_cpu(&cpu);

#undef NOW
#undef LAST
#define NOW  (g->times[g->now])
#define LAST (g->times[g->now ^ 1])

  if (g->num_cpus == 1)
  {
    NOW[0][CPU_TOTAL] = cpu.total;
    NOW[0][CPU_USED] = cpu.user + cpu.nice + cpu.sys;
  }
  else
  {
    for (i = 0; i < g->num_cpus; i++)
    {
      NOW[i][CPU_TOTAL] = cpu.xcpu_total[i];
      NOW[i][CPU_USED] = cpu.xcpu_user[i] + cpu.xcpu_nice[i] + cpu.xcpu_sys[i];
    }
  }

  if (G_UNLIKELY(!g->initialized))
  {
    g->initialized = TRUE;

  }
  else
  {
    // for machines with more than one CPU, average their usage
    // to get a total.
    float load, total, used;
    load = total = used = 0.0;

    for (i = 0; i < g->num_cpus; i++)
    {
      total = total + NOW[i][CPU_TOTAL] - LAST[i][CPU_TOTAL];
      used  = used + NOW[i][CPU_USED]  - LAST[i][CPU_USED];
    }

    load = used / MAX(total, (float)g->num_cpus * 1.0f);

    g->data[g->index] = load;
    g->index = (g->index == (NUM_POINTS - 1) ? 0 : g->index + 1);
  }

  // toggle the buffer index.
  g->now ^= 1;

#undef NOW
#undef LAST
}

/**
 * Initializes the LoadGraph object.  The Java/C++ guy in me would
 * prefer a constructor.  :P
 */
static void init_load_graph(LoadGraph *g)
{
  g->index = 0;
  g->initialized = FALSE;
  g->now = 0;
  memset(g->data, 0, NUM_POINTS*sizeof(gfloat));

  int num_cpus = 0;
  glibtop_cpu cpu;
  glibtop_get_cpu(&cpu);
  int i = 0;

  while (i < GLIBTOP_NCPU && cpu.xcpu_total[i] != 0)
  {
    num_cpus++;
    i++;
  }

  if (num_cpus == 0)
  {
    num_cpus = 1;
  }

  g->num_cpus = num_cpus;
}

/**
 * This is our periodic quasi-interrupt thing.
 */
#if 0
static gboolean time_handler(gpointer data)
{
  CpuMeter* cpumeter = (CpuMeter *)data;
  gtk_widget_queue_draw(GTK_WIDGET(cpumeter->applet));
  return TRUE;
}

#endif

/*
 * Events
 */

/**
 * Event for button released
 * -calls popup_menu
 */
static gboolean
_button_release_event(GtkWidget *widget, GdkEventButton *event, gpointer *data)
{
  return TRUE;
}


static gboolean _die_die_exclamation(GtkWidget *window, GdkEvent *event, gpointer *data)
{
  printf("Awn System Manger Removed\n");
  /*applet->height = height;
    gtk_widget_queue_draw (GTK_WIDGET (applet));
    update_icons (applet);*/
  return TRUE;
}


/**
 * Called on applet height changes
 * -set height and redraw applet
 */
static void
_height_changed(AwnApplet *app, guint height, gpointer *data)
{

  /*applet->height = height;
    gtk_widget_queue_draw (GTK_WIDGET (applet));
    update_icons (applet);*/
  CpuMeter* cpumeter = data;
  gtk_widget_set_size_request(GTK_WIDGET(cpumeter->applet), height*1.25, height*2);
  cpumeter->doneonce = FALSE;
}

/**
 * Called on applet orientation changes
 * -set orientation and redraw applet
 */
static void
_orient_changed(AwnApplet *app, guint orient, gpointer *data)
{
  /*applet->orient = orient;
  gtk_widget_queue_draw (GTK_WIDGET (applet));*/
}

static gboolean
_enter_notify_event(GtkWidget *window, GdkEventButton *event, gpointer *data)
{
  CpuMeter *cpumeter = (CpuMeter *)data;
  cpumeter->show_title = TRUE;
  //awn_title_show (clock->title,GTK_WIDGET(clock->applet), clock->txt_time);
}

static gboolean
_leave_notify_event(GtkWidget *window, GdkEvent *event, gpointer *data)
{
  CpuMeter *cpumeter = (CpuMeter *)data;
  cpumeter->show_title = FALSE;
  //awn_title_hide (clock->title, GTK_WIDGET(clock->applet));
}

static gboolean
_button_clicked_event(GtkWidget *widget, GdkEventButton *event, CpuMeter * cpumeter)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;

  if (event->button == 1)
  {
    toggle_Dashboard_window(&cpumeter->dashboard);
  }
  else if (event->button == 3)
  {
    enable_suppress_hide_main();
    gtk_menu_popup(cpumeter->right_click_menu, NULL, NULL, NULL, NULL,
                   event_button->button, event_button->time);
  }

  return TRUE;
}




