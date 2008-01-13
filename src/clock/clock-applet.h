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
 *
 *
 *
 *
 * Thanks to Miika-Petteri Matikainen for his help, his ideas and some piece of code 
 * (especially for the digital clok, and the function wich let uses a format for the date&time)
 *
 */

#ifndef CLOCK_APPLET_H
#define CLOCK_APPLET_H

#define HAVE_SVG 1

#include <math.h>
#include <sys/time.h>
#include <gtk/gtk.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>
#include <glib/gmacros.h>
#include <glib/gerror.h>
#include <gconf/gconf-value.h> 

#include <libawn/awn-title.h>


#ifdef HAVE_SVG
	#include <librsvg/rsvg.h>
	#include <librsvg/rsvg-cairo.h>
#endif

#define CLOCK_ANALOGIC 10
#define CLOCK_DIGITAL 20
#define SECOND_INTERVAL  1000
#define MINUTE_INTERVAL 60000

typedef struct
{
	// Reference interne
	AwnApplet *applet;
	
	gint timeout_id;
	GtkOrientation orient;
	AwnTitle *title;
	
	//Les image pour l'heure
	//Version png
	GdkPixbuf	*bg_handle;
	GdkPixbuf	*mark_pixbuf;
	GdkPixbuf	*shadow_pixbuf;
	GdkPixbuf	*glass_pixbuf;
	GdkPixbuf	*hour_hand_pixbuf;
	GdkPixbuf	*minute_hand_pixbuf;
	GdkPixbuf	*second_hand_pixbuf;

	//Version svg
	#ifdef HAVE_SVG
		RsvgHandle	*bg_svg_handle;
		RsvgHandle	*mark_svg_handle;
		RsvgHandle	*shadow_svg_handle;
		RsvgHandle	*glass_svg_handle;
		RsvgHandle	*hour_hand_svg_handle;
		RsvgHandle	*minute_hand_svg_handle;
		RsvgHandle	*second_hand_svg_handle;
		RsvgHandle	*hour_hand_shadow_svg_handle;
		RsvgHandle	*minute_hand_shadow_svg_handle;
		RsvgHandle	*second_hand_shadow_svg_handle;
		RsvgHandle	*drop_shadow_svg_handle;
		RsvgHandle	*face_svg_handle;
	#endif

	//Les informations sur la date et l'heure
	gint seconds, minutes, hours, day, month, year;
	char txt_date[200];
	char txt_time[200];

	// Les options
	gint type;
	gchar *theme_path;
	gchar *theme_name;
	
	gboolean show_second;
	gboolean show_date;
	gboolean b_24h_mode;
	
	gchar *format_date;
	gchar *format_time;
	gboolean utc;
	
	gint font_size;
	gchar *font_face;
	gchar *font_color;
	gchar *rectangle_color;

	guint height;
	gint y_offset;

	GtkWidget *context_menu;
}Clock;

// Applet
Clock* clock_applet_new (AwnApplet *applet);

#endif /*CLOCK_APPLET_H*/

