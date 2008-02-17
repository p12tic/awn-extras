/*
 * Copyright (c) 2007 Nicolas de BONFILS
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

#include "wobblyziniapplet.h"

/*
 * STATIC FUNCTION DEFINITIONS
 */
static void wobbly_zini_render (cairo_t *cr, int width, int height);
static gboolean time_handler (WobblyZini *wobblyzini);

// Events
static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _height_changed (AwnApplet *app, guint height, gpointer *data);
static void _orient_changed (AwnApplet *appt, guint orient, gpointer *data);

/**
 * Create new applet
 */
WobblyZini*
wobblyzini_applet_new (AwnApplet *applet)
{
	WobblyZini *wobblyzini = g_new0 (WobblyZini, 1);
	wobblyzini->applet = applet;
	wobblyzini->height = awn_applet_get_height(applet) * 2;

	// set the icon
	gtk_window_set_default_icon_name ("Wobbly Zini");

	wobblyzini->size = 0;
	wobblyzini->new_size = 0;
	wobblyzini->y_offset = 0;
	wobblyzini->orient = GTK_ORIENTATION_HORIZONTAL;

	wobblyzini->tooltips = gtk_tooltips_new ();
	g_object_ref (wobblyzini->tooltips);
	gtk_object_sink (GTK_OBJECT (wobblyzini->tooltips));

	/*printf ("signal\n");*/
	// connect to button events
	g_signal_connect (G_OBJECT (wobblyzini->applet), "button-release-event", G_CALLBACK (_button_release_event), (gpointer)wobblyzini );
	g_signal_connect (G_OBJECT (wobblyzini->applet), "expose-event", G_CALLBACK (_expose_event), wobblyzini);

	// connect to height and orientation changes
	g_signal_connect (G_OBJECT (wobblyzini->applet), "height-changed", G_CALLBACK (_height_changed), (gpointer)wobblyzini);
	g_signal_connect (G_OBJECT (wobblyzini->applet), "orientation-changed", G_CALLBACK (_orient_changed), (gpointer)wobblyzini);

	gtk_timeout_add (MS_INTERVAL, (GtkFunction) time_handler, wobblyzini);
	bzero (&g_timeValue, sizeof (g_timeValue));

	// return widget
	return wobblyzini;
}

/**
 * Actually draw the applet via cairo
 * -uses draw()
 */
static gboolean
_expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
	//printf ("expose applet\n");

	WobblyZini *wobblyzini = (WobblyZini *)data;
	cairo_t *cr = NULL;
	gint width, height;

	if (!GDK_IS_DRAWABLE (widget->window))
	{
		/*printf("pas drawable !!\n");*/
		return FALSE;
	}

	cr = gdk_cairo_create (widget->window);
	if (!cr)
	{
		/*printf( "eee\n");*/
		return FALSE;
	}

	gtk_widget_get_size_request (widget, &width, &height);

	wobbly_zini_render (cr, width, height);

	/* Clean up */
	cairo_destroy (cr);

	return TRUE;
}

/*
 * Graphics Drawing Functions
 */
static void
wobbly_zini_render (cairo_t *cr, int width, int height)
{
	//printf("render debut\n");
	double fLength = 1.0f / 25.0f;
	double fY;
	int i;
	unsigned long ulMilliSeconds;

	gettimeofday (&g_timeValue, NULL);
	ulMilliSeconds = g_timeValue.tv_usec / 1000.0f;

	/* Clear the background to transparent */
	cairo_set_source_rgba (cr, 1.0f, 1.0f, 1.0f, 0.0f);
	cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
	cairo_paint (cr);

	cairo_save (cr);
	cairo_translate(cr, 0, 40);
	cairo_scale (cr, (double) width / 1.0f, (double) height / 1.0f);
	cairo_set_operator (cr, CAIRO_OPERATOR_OVER);
	cairo_set_line_cap (cr, CAIRO_LINE_CAP_ROUND);
	for (i = 0; i < 60; i++)
	{
		cairo_save (cr);
		cairo_set_line_width (cr, fLength);
		cairo_translate (cr, 0.5f, 0.5f);
		cairo_rotate (cr, M_PI/180.0f * (ulMilliSeconds + 10.0f*i) * 0.36f);
		fY = 0.33f + 0.0825f * sin ((ulMilliSeconds + 10.0f*i)/1000 * 10 * M_PI);
		cairo_translate (cr, 0, fY);
		cairo_rotate (cr, M_PI/180.0f * 6.0f * i);
		cairo_set_source_rgba (cr, 1.0f, 0.5f, 0.0f, i*0.01f);
		cairo_move_to (cr, -fLength, 0);
		cairo_line_to (cr, fLength, 0);
		cairo_stroke (cr);
		cairo_restore (cr);

		//cairo_paint (cr);
	}
	//printf("render fin\n");
}


static gboolean
time_handler (WobblyZini *wobblyzini)
{
	gtk_widget_queue_draw (GTK_WIDGET(wobblyzini->applet));
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
