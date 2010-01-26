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
#include <string.h>

/*
 * STATIC FUNCTION DEFINITIONS
 */
static void wobbly_zini_render (cairo_t *cr);
static gboolean time_handler (WobblyZini *wobblyzini);

// Events
static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _size_changed (AwnApplet *app, guint size, gpointer *data);
static void _orient_changed (AwnApplet *appt, GtkPositionType orient, gpointer *data);
static void _offset_changed (AwnApplet *appt, guint offset, gpointer *data);

/**
 * Create new applet
 */
WobblyZini*
wobblyzini_applet_new (AwnApplet *applet)
{
	// this applet is very simple - it just uses a simple structure
	WobblyZini *wobblyzini = g_new0 (WobblyZini, 1);
	// we'll save the applet, it could be useful
	wobblyzini->applet = applet;
	// to determine our size we'll ask the applet
	wobblyzini->size = awn_applet_get_size(applet);

	// set the icon
	gtk_window_set_default_icon_name ("Wobbly Zini");

	// AwnIcon supports nicely orientation, size and effects
	GtkWidget *icon = awn_icon_new();
	wobblyzini->icon = AWN_ICON (icon);
	// we'll set correct orientation, so icon can be painted properly
	awn_icon_set_pos_type (AWN_ICON(icon), awn_applet_get_pos_type(applet));
        // set also offset
        awn_icon_set_offset (AWN_ICON (icon), awn_applet_get_offset (applet));

	// this applet paints itself, no static icon
	awn_icon_set_custom_paint(AWN_ICON(icon),
	                          wobblyzini->size, wobblyzini->size);
	// to paint the icon we'll use standard expose event
	g_signal_connect (icon, "expose-event",
                          G_CALLBACK (_expose_event), wobblyzini);
	// add the AwnIcon to the container
        gtk_container_add(GTK_CONTAINER(applet), icon);

	// connect to button events
	g_signal_connect (G_OBJECT (wobblyzini->applet), "button-release-event", G_CALLBACK (_button_release_event), (gpointer)wobblyzini );

	// connect to height and orientation changes
	g_signal_connect (wobblyzini->applet, "size-changed",
                          G_CALLBACK (_size_changed), wobblyzini);
	g_signal_connect (wobblyzini->applet, "position-changed",
                          G_CALLBACK (_orient_changed), wobblyzini);
	g_signal_connect (wobblyzini->applet, "offset-changed",
                          G_CALLBACK (_offset_changed), wobblyzini);

	// update the icon a few times per second
	gtk_timeout_add (MS_INTERVAL, (GtkFunction) time_handler, wobblyzini);
	memset (&g_timeValue, '\0', sizeof (g_timeValue));

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

  AwnOverlayable *overlayable = AWN_OVERLAYABLE (widget);
  AwnEffects *fx = awn_overlayable_get_effects (overlayable);

	cr = awn_effects_cairo_create_clipped (fx, expose);
	if (!cr)
	{
		/*printf( "eee\n");*/
		return FALSE;
	}

	// the render method paints to [0,0] - [1,1], so we will scale
  cairo_scale(cr, wobblyzini->size, wobblyzini->size);
	// actual drawing
	wobbly_zini_render (cr);

	/* Clean up */
	awn_effects_cairo_destroy (fx);

	return TRUE;
}

/*
 * Graphics Drawing Functions
 */
static void
wobbly_zini_render (cairo_t *cr)
{
	//printf("render debut\n");
	double fLength = 1.0f / 25.0f;
	double fY;
	int i;
	unsigned long ulMilliSeconds;

	gettimeofday (&g_timeValue, NULL);
	ulMilliSeconds = g_timeValue.tv_usec / 1000.0f;

	cairo_save (cr);
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
#ifndef X_EVENT_WATCHING
  AwnOverlayable *overlayable = AWN_OVERLAYABLE (wobblyzini->icon);
  AwnEffects *fx = awn_overlayable_get_effects (overlayable);
  awn_effects_redraw (fx);
#endif
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
_size_changed (AwnApplet *app, guint size, gpointer *data)
{
	WobblyZini *wobblyzini = (WobblyZini *)data;
	AwnIcon *icon = AWN_ICON(wobblyzini->icon);

	// update our size
        wobblyzini->size = size;
	// this call is necessary, so the AwnIcon requests more space etc.
	awn_icon_set_custom_paint(icon, size, size);
}

/**
 * Called on applet orientation changes
 * -set orientation and redraw applet
 */
static void
_orient_changed (AwnApplet *app, GtkPositionType orient, gpointer *data)
{
	WobblyZini *wobblyzini = (WobblyZini *)data;
	AwnIcon *icon = AWN_ICON(wobblyzini->icon);

	// update the orientation
	awn_icon_set_pos_type(icon, orient);
}

/**
 * Called on offset change
 */
static void
_offset_changed (AwnApplet *appt, guint offset, gpointer *data)
{
	WobblyZini *wobblyzini = (WobblyZini *)data;
	AwnIcon *icon = AWN_ICON(wobblyzini->icon);

	// update the offset
	awn_icon_set_offset(icon, offset);
}
