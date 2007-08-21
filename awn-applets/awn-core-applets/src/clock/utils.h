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

//-----------------------------------------------------
//Adapted from the stack applet taken from awn core => I think it need to be move to libawn so everybody can use it
//Mine don't use a char* from gconf

/**
 * Get the decimal value of a hex value
 */
int getdec(char hexchar);

/**
 * Convert a HexColor (including alpha) to a FloatColor
 */
void hex2float(char* HexColor, float* FloatColor);

/**
 * Get a color from a GConf key
 */
//AwnColor *
void 
convert_color (AwnColor *color, const gchar *str_color);
//--------------------------------------------------------



gboolean
awn_load_png (gchar *icon, GdkPixbuf **pixbuf, GError **error);

#ifdef HAVE_SVG
	//Adapted from kiba-dock
	gboolean
	awn_load_svg (RsvgHandle **handle, char* path, char* theme, char* file_name, GError **error);
#endif

#endif /*UTILS_H_*/
