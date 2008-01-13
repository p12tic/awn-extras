/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
 *
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
#include "awn-extras.h" 

#include <math.h>

gchar * awncolor_to_string(AwnColor * colour)
{

	return g_strdup_printf("%02x%02x%02x%02x",
								(unsigned int) round((colour->red*255)),
								(unsigned int) round((colour->green*255)),
								(unsigned int) round((colour->blue*255)),
								(unsigned int) round((colour->alpha*255))
								);
}

AwnColor gdkcolor_to_awncolor_with_alpha( GdkColor * gdk_color,double alpha)
{
	AwnColor colour;
	
	colour.red=gdk_color->red/65535.0;
	colour.green=gdk_color->green/65535.0;    
	colour.blue=gdk_color->blue/65535.0;
	colour.alpha=alpha;  
	return colour;
}

AwnColor gdkcolor_to_awncolor( GdkColor * gdk_colour)
{
	return gdkcolor_to_awncolor_with_alpha(gdk_colour,0.9);
}


