/*
 * Copyright (c) 2007 Mike Desjardins
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

#include "helloworldapplet.h"

/*
 * STATIC FUNCTION DEFINITIONS
 */
static void hello_world_render (cairo_t *cr, int width, int height);
static gboolean time_handler (HelloWorld *helloworld);

// Events
static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _height_changed (AwnApplet *app, guint height, gpointer *data);
static void _orient_changed (AwnApplet *appt, guint orient, gpointer *data);

/**
 * Create new applet
 */
HelloWorld*
helloworld_applet_new (AwnApplet *applet)
{
	HelloWorld *helloworld = g_new0 (HelloWorld, 1);
	helloworld->applet = applet;
	helloworld->height = awn_applet_get_height(applet) * 2;

	// set the icon
	gtk_window_set_default_icon_name ("Hello World!");

	helloworld->size = 0;
	helloworld->new_size = 0;
	helloworld->y_offset = 0;
	helloworld->orient = GTK_ORIENTATION_HORIZONTAL;

	helloworld->tooltips = gtk_tooltips_new ();
	g_object_ref (helloworld->tooltips);
	gtk_object_sink (GTK_OBJECT (helloworld->tooltips));

	// connect to button events
	g_signal_connect (G_OBJECT (helloworld->applet), "button-release-event", G_CALLBACK (_button_release_event), (gpointer)helloworld );
	g_signal_connect (G_OBJECT (helloworld->applet), "expose-event", G_CALLBACK (_expose_event), helloworld);

	// connect to height and orientation changes
	g_signal_connect (G_OBJECT (helloworld->applet), "height-changed", G_CALLBACK (_height_changed), (gpointer)helloworld);
	g_signal_connect (G_OBJECT (helloworld->applet), "orientation-changed", G_CALLBACK (_orient_changed), (gpointer)helloworld);

	// return widget
	return helloworld;
}

/**
 * Actually draw the applet via cairo
 * -uses draw()
 */
static gboolean
_expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
	HelloWorld *helloworld = (HelloWorld *)data;
	cairo_t *cr = NULL;
	gint width, height;

	if (!GDK_IS_DRAWABLE (widget->window))
	{
		printf("Unexpected Error: Window is not drawable.\n");
		return FALSE;
	}

	cr = gdk_cairo_create (widget->window);
	if (!cr)
	{
		printf( "Unexpected Error: Failed to create a Cairo Drawing Context.\n");
		return FALSE;
	}
	
	gtk_widget_get_size_request (widget, &width, &height);

	hello_world_render (cr, width, height);

	/* Clean up */
	cairo_destroy (cr);

	return TRUE;
}

/*
 * Graphics Drawing Functions
 */
static void
hello_world_render (cairo_t *cr, int width, int height)
{
  /* Clear the background to transparent */
  cairo_set_source_rgba (cr, 1.0f, 1.0f, 1.0f, 0.0f);
  cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint (cr);

  /* Set back to opaque */
  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);
  cairo_set_source_rgb(cr, 1.0, 1.0, 1.0);

  cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_BOLD);
  cairo_set_font_size (cr, 11.0);
  cairo_move_to(cr, 15.0, 65.0);
  cairo_show_text(cr, "Hello");
  cairo_move_to(cr, 10.0, 85.0);
  cairo_show_text(cr, "World!");
}


static gboolean 
time_handler (HelloWorld *helloworld)
{
	gtk_widget_queue_draw (GTK_WIDGET(helloworld->applet));
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
