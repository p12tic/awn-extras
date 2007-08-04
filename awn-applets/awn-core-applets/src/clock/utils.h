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

/*
 *
 * There are parts of code take from kiba-dock project
 *
 */

#ifndef UTILS_H_
#define UTILS_H_

void
convert_color (const char *html_color, double *r, double *g, double *b);

gboolean
awn_load_png (gchar *icon, GdkPixbuf **pixbuf, GError **error);

#ifdef HAVE_SVG
	//From kiba-dock
	gboolean
	awn_load_svg (char* path, RsvgHandle **handle, GError **error);
#endif

#endif /*UTILS_H_*/
