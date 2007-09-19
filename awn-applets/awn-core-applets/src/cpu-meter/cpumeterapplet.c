/*
 * Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
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

#include <math.h>
#include "cpumeterapplet.h"
#include "cpumetergconf.h"
#include "config.h"

#define NDEBUG
#include <assert.h>

/*
 * FUNCTION DEFINITIONS
 */
gboolean cpu_meter_render (gpointer cpumeter);
static gboolean time_handler (gpointer cpumeter);
static void get_load (LoadGraph *g);
static void init_load_graph (LoadGraph *g);
static void emit_data(LoadGraph *g);


// Events
static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _height_changed (AwnApplet *app, guint height, gpointer *data);
static void _orient_changed (AwnApplet *appt, guint orient, gpointer *data);
static gboolean _enter_notify_event (GtkWidget *window, GdkEventButton *event, gpointer *data);
static gboolean _leave_notify_event (GtkWidget *window, GdkEvent *event, gpointer *data);
static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event, CpuMeter * applet);

/**
 * Create new applet
 */
CpuMeter*
cpumeter_applet_new (AwnApplet *applet)
{
  CpuMeter *cpumeter = g_new0 (CpuMeter, 1);
  cpumeter->loadgraph = g_new0 (LoadGraph, 1);
  cpumeter->applet = applet;
  cpumeter->height = awn_applet_get_height(applet) * 2;
  cpumeter->timer_id = -1;
	cpumeter->show_title = FALSE;
  cpumeter->title = AWN_TITLE(awn_title_get_default());
  
  register_awntop(&cpumeter->awntop,cpumeter->applet);
  
  init_load_graph(cpumeter->loadgraph);
  
  // set the icon
  gtk_window_set_default_icon_name ("CPU Meter");
  
  cpumeter->size = 0;
  cpumeter->new_size = 0;
  cpumeter->y_offset = 0;
  cpumeter->orient = GTK_ORIENTATION_HORIZONTAL;
  
  cpumeter->tooltips = gtk_tooltips_new ();
  g_object_ref (cpumeter->tooltips);
  gtk_object_sink (GTK_OBJECT (cpumeter->tooltips));
  
  cpumeter_gconf_init(cpumeter);
  cpumeter_gconf_event(cpumeter->client, 0, NULL, cpumeter);

  // connect to button events
  g_signal_connect (G_OBJECT (cpumeter->applet), "button-release-event", G_CALLBACK (_button_release_event), (gpointer)cpumeter );
  g_signal_connect (G_OBJECT (cpumeter->applet), "expose-event", G_CALLBACK (_expose_event), cpumeter);
 
 g_signal_connect (G_OBJECT (cpumeter->applet), "button-press-event",G_CALLBACK (_button_clicked_event), (gpointer)cpumeter);
  
  // connect to height and orientation changes
  g_signal_connect (G_OBJECT (cpumeter->applet), "height-changed", G_CALLBACK (_height_changed), (gpointer)cpumeter);
  g_signal_connect (G_OBJECT (cpumeter->applet), "orientation-changed", G_CALLBACK (_orient_changed), (gpointer)cpumeter);
  
	// connect to enter/leave
	g_signal_connect (G_OBJECT(cpumeter->applet), "enter-notify-event", G_CALLBACK (_enter_notify_event), (gpointer)cpumeter);
	g_signal_connect(G_OBJECT(cpumeter->applet), "leave-notify-event", G_CALLBACK (_leave_notify_event), (gpointer)cpumeter);
  	
  return cpumeter;
}

/**
 * Actually draw the applet via cairo
 * -uses draw()
 */
static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
  CpuMeter *cpumeter = (CpuMeter *)data;
  cpu_meter_render (cpumeter);
  return TRUE;
}

/**
 * Draws everything.  Should be refactored so that we don't draw the
 * entire image every time, just the graph.
 */
gboolean cpu_meter_render (gpointer data)
{
  CpuMeter* cpumeter = (CpuMeter *)data;
  cairo_t *cr = NULL;
  gint width, height;
  GtkWidget* widget = GTK_WIDGET(cpumeter->applet);
  cairo_pattern_t *pattern;
  gint i, j;
  gfloat percent;
  AwnApplet* applet = cpumeter->applet;
  

  if (!GDK_IS_DRAWABLE (widget->window)) {
    printf("Unexpected Error: Window is not drawable.\n");
    return FALSE;
  }

  cr = gdk_cairo_create (widget->window);
  if (!cr) {
    printf( "Unexpected Error: Failed to create a Cairo Drawing Context.\n");
    return FALSE;
  }
  
  gtk_widget_get_size_request (widget, &width, &height);
  
  LoadGraph* g = cpumeter->loadgraph;
  
  /* Clear the background to transparent */
  cairo_set_source_rgba (cr, 1.0, 1.0, 1.0, 0.0);
  cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint (cr);

  /* Set back to opaque */
  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);

  /* Set the background color */
  awn_cairo_rounded_rect(cr, PAD-1, height+1, width-PAD, height-PAD-1, ARC, ROUND_ALL);
  cairo_set_source_rgba( cr, cpumeter->bg.red, cpumeter->bg.green, cpumeter->bg.blue, cpumeter->bg.alpha );
  cairo_fill(cr);
  
  /* Get the load and paint it */
  get_load(g);
  assert((g->index) <= NUM_POINTS);
  assert((g->index) >= 0);
  guint percent_now;
  if (g->index>0)
  {
      percent_now = round(g->data[(g->index)-1]*100.0); 
      percent_now = percent_now>100?100:percent_now;
  }
  else
  {
        percent_now=0;
  }
  i = width - 2;
  j = g->index-1;
  if (j < 0) {
    j = NUM_POINTS-1;
  }

  guint top = height + PAD;
  guint bottom = height*2 - PAD;
  guint tallest = bottom - top;
  cairo_set_line_width (cr, 1.0);
  while (i > PAD) {
    assert(j< NUM_POINTS);
    assert(j>=0);
    percent = g->data[j];
    if (percent > 0 && percent <= 1.0) {
      cairo_set_source_rgba( cr, cpumeter->graph.red, cpumeter->graph.green, cpumeter->graph.blue, cpumeter->graph.alpha );
      cairo_move_to(cr, i, bottom - round((float)tallest * percent));
      cairo_line_to(cr, i, bottom);
      cairo_stroke(cr);
    }
    if (j == 0) {
      j = NUM_POINTS-1;
    } else {
      j--;
    }
    i--;
  }

  cairo_set_line_width (cr, cpumeter->border_width);
  cairo_set_source_rgba (cr, cpumeter->border.red, cpumeter->border.green, cpumeter->border.blue, cpumeter->border.alpha);
  awn_cairo_rounded_rect(cr, PAD-1, height+1, width-PAD, height-PAD-1, ARC, ROUND_ALL);
  cairo_stroke (cr);

  if (cpumeter->do_gradient) {
    awn_cairo_rounded_rect(cr, PAD-1, height+1, width-PAD, height-PAD-1, ARC, ROUND_ALL);
    pattern = cairo_pattern_create_linear (28, 68, 28, 48);
    cairo_pattern_add_color_stop_rgba (pattern, 0.00,  .1, .1, .1, .5);
    cairo_pattern_add_color_stop_rgba (pattern, 1.00,  .6, .6, .6, .5);
    cairo_set_source(cr, pattern);
    cairo_fill(cr);
  }

  char text[20];
  bzero(text,sizeof(text));
  snprintf(text, sizeof(text), "CPU: %d%%", percent_now);
  if (cpumeter->do_subtitle) {
    cairo_set_source_rgba (cr, cpumeter->border.red, cpumeter->border.green, cpumeter->border.blue, cpumeter->border.alpha);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size (cr, 7.0);
    cairo_move_to(cr, PAD+2, bottom+8);
    cairo_show_text(cr, text);
  }

	if(cpumeter->show_title) {
		awn_title_show(cpumeter->title,GTK_WIDGET(cpumeter->applet), text);
	} else {
		awn_title_hide(cpumeter->title, GTK_WIDGET(cpumeter->applet));
	}
  
//  embed_cairo(&cpumeter->awntop,cr,2,3,2,3);
  
  /* Clean up */
  cairo_destroy (cr);
  
  return TRUE;
}

/** 
 * Almost a one-for-one ripoff from Gnome Process Monitor's
 * get_load function in load-graph.cpp:
 */
static void
get_load (LoadGraph *g)
{
  guint i;
  glibtop_cpu cpu;

  glibtop_get_cpu (&cpu);
  
#undef NOW
#undef LAST
#define NOW  (g->times[g->now])
#define LAST (g->times[g->now ^ 1])
  
  if (g->num_cpus == 1) {
    NOW[0][CPU_TOTAL] = cpu.total;
    NOW[0][CPU_USED] = cpu.user + cpu.nice + cpu.sys;
  } else {
    for (i = 0; i < g->num_cpus; i++) {
      NOW[i][CPU_TOTAL] = cpu.xcpu_total[i];
      NOW[i][CPU_USED] = cpu.xcpu_user[i] + cpu.xcpu_nice[i] + cpu.xcpu_sys[i];
    }
  }

  if (G_UNLIKELY(!g->initialized)) {
    g->initialized = TRUE;
    
  } else {
    // for machines with more than one CPU, average their usage
    // to get a total.
    float load, total, used;
    load = total = used = 0.0;
    for (i = 0; i < g->num_cpus; i++) {
      total = total + NOW[i][CPU_TOTAL] - LAST[i][CPU_TOTAL];
      used  = used + NOW[i][CPU_USED]  - LAST[i][CPU_USED];
    }
    
    load = used / MAX(total, (float)g->num_cpus * 1.0f);
    g->data[g->index] = load;
    g->index = (g->index == (NUM_POINTS-1) ? 0 : g->index + 1);
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
static void init_load_graph (LoadGraph *g) {
  g->index = 0;
  g->initialized = FALSE;
  g->now = 0;
  memset(g->data, 0, NUM_POINTS*sizeof(gfloat));

  int num_cpus = 0;
  glibtop_cpu cpu;
  glibtop_get_cpu (&cpu);
  int i=0;
  while (i < GLIBTOP_NCPU && cpu.xcpu_total[i] != 0) {
    num_cpus++;
    i++;
  }
  if (num_cpus == 0) {
    num_cpus = 1;
  }
  g->num_cpus = num_cpus;
}

/**
 * This is our periodic quasi-interrupt thing.
 */
static gboolean time_handler (gpointer data) {
  CpuMeter* cpumeter = (CpuMeter *)data;
  gtk_widget_queue_draw (GTK_WIDGET(cpumeter->applet));
  return TRUE;
}

/*
 * Events
 */

/**
 * Event for button released
 * -calls popup_menu
 */
static gboolean
_button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data)
{
  return TRUE;
}

/**
 * Called on applet height changes
 * -set height and redraw applet
 */
static void
_height_changed (AwnApplet *app, guint height, gpointer *data)
{
  /*applet->height = height;
    gtk_widget_queue_draw (GTK_WIDGET (applet));
    update_icons (applet);*/
}

/**
 * Called on applet orientation changes
 * -set orientation and redraw applet
 */
static void
_orient_changed (AwnApplet *app, guint orient, gpointer *data)
{
  /*applet->orient = orient;
  gtk_widget_queue_draw (GTK_WIDGET (applet));*/
}

static gboolean
_enter_notify_event (GtkWidget *window, GdkEventButton *event, gpointer *data)
{
	CpuMeter *cpumeter = (CpuMeter *)data;
	cpumeter->show_title = TRUE;
	//awn_title_show (clock->title,GTK_WIDGET(clock->applet), clock->txt_time);
}

static gboolean
_leave_notify_event (GtkWidget *window, GdkEvent *event, gpointer *data)
{
	CpuMeter *cpumeter = (CpuMeter *)data;
	cpumeter->show_title = FALSE;
	//awn_title_hide (clock->title, GTK_WIDGET(clock->applet));
}

static gboolean
_button_clicked_event (GtkWidget *widget, GdkEventButton *event, CpuMeter * applet)
{
  toggle_awntop_window(&applet->awntop);
  return TRUE;
}
