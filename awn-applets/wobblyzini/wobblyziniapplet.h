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

#ifndef WOBBLYZINIAPPLET_H_
#define WOBBLYZINIAPPLET_H_

#include <libawn/awn-applet.h>

#include <math.h>
#include <sys/time.h>

#define MS_INTERVAL 10
struct timeval	g_timeValue;
typedef struct 
{
	AwnApplet *applet;

	guint size;
	guint new_size;
	GtkOrientation orient;

	GtkTooltips *tooltips;
	GdkPixbuf *icon;

	/* Effect stuff */
	guint height;
	gint y_offset;

}WobblyZini;

// Applet
WobblyZini* wobblyzini_applet_new (AwnApplet *applet);

#endif /*WOBBLYZINIAPPLET_H_*/
