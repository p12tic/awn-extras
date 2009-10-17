/*
 * Copyright (C) 2009 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
*/
/* cairo-menu-applet.h */

#ifndef _CAIRO_AUX_ICON
#define _CAIRO_AUX_ICON

#include <libawn/libawn.h>
#include <glib-object.h>

G_BEGIN_DECLS

#define AWN_TYPE_CAIRO_AUX_ICON cairo_aux_icon_get_type()

#define AWN_CAIRO_AUX_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_AUX_ICON, CairoAuxIcon))

#define AWN_CAIRO_AUX_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_AUX_ICON, CairoMainAuxClass))

#define AWN_IS_CAIRO_AUX_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_AUX_ICON))

#define AWN_IS_CAIRO_AUX_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_AUX_ICON))

#define AWN_CAIRO_AUX_ICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_AUX_ICON, CairoMainAuxClass))

typedef struct {
  AwnThemedIcon parent;
} CairoAuxIcon;

typedef struct {
  AwnThemedIconClass parent_class;
} CairoAuxIconClass;

GType cairo_aux_icon_get_type (void);

GtkWidget* cairo_aux_icon_new (AwnApplet * applet, gchar * menu_name,gchar * display_name, gchar * icon_name);

G_END_DECLS

#endif 
