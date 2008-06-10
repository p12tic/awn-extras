/*
 * Original code from abiword (http://www.abisource.com/)  go-image.c
 * Function name:  static void pixbuf_to_cairo (GOImage *image);
 * Copyright (C) 2004, 2005 Jody Goldberg (jody@gnome.org)
 *
 * Thanks to Jody Goldberg for permission to relicense the conversion code
 *          as LGP2 v2 or later.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 * 
 * You should have received a copy of the GNU Lesser General Public
 * License along with main.c; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 *
 *
 */

 
#include <glib.h> 
#include "awn-extras.h"




GdkPixbuf * get_pixbuf_from_surface(cairo_surface_t * surface)
{
    GdkPixbuf *pixbuf;
    pixbuf=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,cairo_image_surface_get_width (surface),cairo_image_surface_get_height (surface));    
    g_return_if_fail( pixbuf !=NULL);
    return surface_2_pixbuf(pixbuf,surface);
}



/*
GdkPixbuf * surface_2_pixbuf( GdkPixbuf * pixbuf, cairo_surface_t * surface)

original code from abiword (http://www.abisource.com/)  go-image.c
Function name:  static void pixbuf_to_cairo (GOImage *image);
Copyright (C) 2004, 2005 Jody Goldberg (jody@gnome.org)

modified by Rodney Cryderman (rcryderman@gmail.com).

Send it a allocated pixbuff and cairo image surface.  the heights and width 
must match.  Both must be ARGB.
will copy from the surface to the pixbuf.

*/

GdkPixbuf * surface_2_pixbuf( GdkPixbuf * pixbuf, cairo_surface_t * surface)
{
	guint i,j;
	
	guint src_rowstride,dst_rowstride;
	guint src_height, src_width, dst_height, dst_width;
	
	unsigned char *src, *dst;
	guint t;

#define MULT(d,c,a,t) G_STMT_START { t = (a)? c * 255 / a: 0; d = t;} G_STMT_END

	dst = gdk_pixbuf_get_pixels (pixbuf);
	dst_rowstride = gdk_pixbuf_get_rowstride (pixbuf);
	dst_width=gdk_pixbuf_get_width (pixbuf);
	dst_height= gdk_pixbuf_get_height (pixbuf);
	src_width=cairo_image_surface_get_width (surface);
	src_height=cairo_image_surface_get_height (surface);
	src_rowstride=cairo_image_surface_get_stride (surface);
	src = cairo_image_surface_get_data (surface);

  g_return_val_if_fail( src_width == dst_width,NULL  );
  g_return_val_if_fail( src_height == dst_height,NULL  );   
  g_return_val_if_fail( cairo_image_surface_get_format(surface) == CAIRO_FORMAT_ARGB32,NULL);

	for (i = 0; i < dst_height; i++) 
	{
		for (j = 0; j < dst_width; j++) {
#if G_BYTE_ORDER == G_LITTLE_ENDIAN
			MULT(dst[0], src[2], src[3], t);
			MULT(dst[1], src[1], src[3], t);
			MULT(dst[2], src[0], src[3], t);
			dst[3] = src[3];
#else	  
			MULT(dst[3], src[2], src[3], t);
			MULT(dst[2], src[1], src[3], t);
			MULT(dst[1], src[0], src[3], t);
			dst[0] = src[3];
#endif
			src += 4;
			dst += 4;
		}
		dst += dst_rowstride - dst_width * 4;
		src += src_rowstride - src_width * 4;
			
	}
#undef MULT
    return pixbuf;
}

