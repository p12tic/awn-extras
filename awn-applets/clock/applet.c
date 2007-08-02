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

#include "config.h"

#include <libawn/awn-applet.h>
	
#include "clock-applet.h"

AwnApplet*
awn_applet_factory_init ( gchar* uid, gint orient, gint height )
{
	AwnApplet *applet;
	Clock *clock;

	printf ("avant init\n");
	applet = awn_applet_new( uid, orient, height );
	gtk_widget_set_size_request (GTK_WIDGET (applet), awn_applet_get_height (applet) * 2, awn_applet_get_height (applet) );
	clock = clock_applet_new(applet);
	printf ("apres init\n");
	
	return applet;
}

