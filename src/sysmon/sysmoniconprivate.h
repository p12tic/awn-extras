/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */
 
#ifndef _AWN_SYSMONICON_PRIV
#define _AWN_SYSMONICON_PRIV

#include <gtk/gtk.h>
#include "sysmonicon.h"
#include "defines.h"

#define AWN_SYSMONICON_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_SYSMONICON, AwnSysmoniconPrivate))

typedef struct _AwnSysmoniconPrivate AwnSysmoniconPrivate;

struct _AwnSysmoniconPrivate 
{
  AwnApplet * applet;
  GtkWidget * tooltip;
  cairo_surface_t *graph_surface;
  cairo_surface_t *bg_surface;
  cairo_surface_t *fg_surface;
  cairo_t *graph_cr;
  cairo_t *bg_cr;
  cairo_t *fg_cr;
  AwnGraph * graph; 
  
  gchar * id;
  AwnGraphType graph_type; 

};

#endif
