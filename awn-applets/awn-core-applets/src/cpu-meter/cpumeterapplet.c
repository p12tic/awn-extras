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

#include "cpumeterapplet.h"
#include "config.h"

/*
 * STATIC FUNCTION DEFINITIONS
 */
static gboolean cpu_meter_render (gpointer cpumeter);
static gboolean time_handler (gpointer cpumeter);
static void get_load (LoadGraph *g);
static void init_load_graph (LoadGraph *g);
static void emit_data(LoadGraph *g);
static void draw_round_rect(cairo_t* cr, double x, double y, double w, double h, double r);
// Events
static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _height_changed (AwnApplet *app, guint height, gpointer *data);
static void _orient_changed (AwnApplet *appt, guint orient, gpointer *data);


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

  init_load_graph(cpumeter->loadgraph);

	// set the icon
	gtk_window_set_default_icon_name ("Hello World!");

	cpumeter->size = 0;
	cpumeter->new_size = 0;
	cpumeter->y_offset = 0;
	cpumeter->orient = GTK_ORIENTATION_HORIZONTAL;

	cpumeter->tooltips = gtk_tooltips_new ();
	g_object_ref (cpumeter->tooltips);
	gtk_object_sink (GTK_OBJECT (cpumeter->tooltips));

	// connect to button events
	g_signal_connect (G_OBJECT (cpumeter->applet), "button-release-event", G_CALLBACK (_button_release_event), (gpointer)cpumeter );
	g_signal_connect (G_OBJECT (cpumeter->applet), "expose-event", G_CALLBACK (_expose_event), cpumeter);

	// connect to height and orientation changes
	g_signal_connect (G_OBJECT (cpumeter->applet), "height-changed", G_CALLBACK (_height_changed), (gpointer)cpumeter);
	g_signal_connect (G_OBJECT (cpumeter->applet), "orientation-changed", G_CALLBACK (_orient_changed), (gpointer)cpumeter);

  g_timeout_add (UPDATE_FREQ,	cpu_meter_render, cpumeter);


	// return widget
	return cpumeter;
}

/**
 * Actually draw the applet via cairo
 * -uses draw()
 */
static gboolean
_expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
	CpuMeter *cpumeter = (CpuMeter *)data;
	cpu_meter_render (cpumeter);
	return TRUE;
}

// Draws everything.  Should be refactored so that we don't draw the
// entire image every time, just the graph.
//
static gboolean
cpu_meter_render (gpointer data)
{
  CpuMeter* cpumeter = (CpuMeter *)data;
	cairo_t *cr = NULL;
  gint width, height;
  GtkWidget* widget = GTK_WIDGET(cpumeter->applet);
  cairo_pattern_t *pattern;
  gint i, j;
  gfloat percent;

  if (!GDK_IS_DRAWABLE (widget->window)) {
  	printf("Unexpected Error: Window is not drawable.\n");
  	return;
  }

  cr = gdk_cairo_create (widget->window);
  if (!cr) {
 		printf( "Unexpected Error: Failed to create a Cairo Drawing Context.\n");
 	}

 	gtk_widget_get_size_request (widget, &width, &height);

  LoadGraph* g = cpumeter->loadgraph;

  /* Clear the background to transparent */
  cairo_set_source_rgba (cr, 1.0, 1.0, 1.0, 0.0);
  cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint (cr);

  /* Set back to opaque */
  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);

  get_load(g);
  guint percent_now = round(g->data[(g->index)-1]*100); 

  //i = width-PAD;
  i = width;
  j = g->index-1;
  if (j < 0) {
    j = NUM_POINTS-1;
  }
 
  //g_message("previous index: %d\n", j);
  guint top = height + PAD;
  guint bottom = height*2 - PAD;
  guint tallest = bottom - top;
  cairo_set_line_width (cr, 1.0);
  while (i > PAD) {
    percent = g->data[j];
    //g_message("percent[%d] = %f%%\n", j, percent);
    if (percent > 0) {
      cairo_set_source_rgba( cr, GRAPH_COLOR_R, GRAPH_COLOR_G, GRAPH_COLOR_B, 1.0 );
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

  cairo_set_line_width (cr, BORDER_WIDTH);
  cairo_set_source_rgb (cr, BORDER_COLOR_R, BORDER_COLOR_G, BORDER_COLOR_B);
  draw_round_rect (cr, PAD-1, height+1, width-PAD, height-PAD-1, ARC);
  cairo_stroke (cr);

#if DO_GRADIENT
  draw_round_rect (cr, PAD-1, height+1, width-PAD, height-PAD-1, ARC);
  pattern = cairo_pattern_create_linear (28, 68, 28, 48);
  cairo_pattern_add_color_stop_rgba (pattern, 0.00,  .1, .1, .1, .5);
  cairo_pattern_add_color_stop_rgba (pattern, 1.00,  .6, .6, .6, .5);
  cairo_set_source(cr, pattern);
  cairo_fill(cr);
#endif

  cairo_set_source_rgb(cr, 1.0, 1.0, 1.0);
  cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
  cairo_set_font_size (cr, 7.0);
  cairo_move_to(cr, PAD+2, bottom+8);

  char text[20];
  bzero(text,sizeof(text));
  snprintf(text, sizeof(text), "CPU - %d%%", percent_now);
  cairo_show_text(cr, text);

  /* Clean up */
  cairo_destroy (cr);
  
  return TRUE;
}

// Draws a rounded rectangle.  Adapted from "Method C" on
// http://cairographics.org/cookbook/roundedrectangles/
//
static void
draw_round_rect(cairo_t* cr, double x, double y, double w, double h, double r)
{
  cairo_move_to(cr,x+r,y);
  cairo_line_to(cr,x+w-r,y);
  cairo_curve_to(cr,x+w,y,x+w,y,x+w,y+r);
  cairo_line_to(cr,x+w,y+h-r);
  cairo_curve_to(cr,x+w,y+h,x+w,y+h,x+w-r,y+h);
  cairo_line_to(cr,x+r,y+h);
  cairo_curve_to(cr,x,y+h,x,y+h,x,y+h-r);
  cairo_line_to(cr,x,y+r);
  cairo_curve_to(cr,x,y,x,y,x+r,y);
  return;
}

// Debug function.
//
static void
emit_data(LoadGraph *g) {
  int i;
  for (i=0; i<NUM_POINTS; i++) {
    printf("point %d: %3.2f", i, g->data[i]);
  }
}

// Almost a one-for-one ripoff from Gnome Process Monitor's
// get_load function in load-graph.cpp:
//
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

// Initializes the LoadGraph object.  The Java/C++ guy in me would
// prefer a constructor.
//
static void
init_load_graph (LoadGraph *g) {
  g->index = 0;
  g->initialized = FALSE;
  g->now = 0;
  bzero(g->data,NUM_POINTS);

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

// This is our periodic quasi-interrupt thing.
//
static gboolean 
time_handler (gpointer data) {
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
