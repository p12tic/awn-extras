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

#ifndef _CAIRO_MAIN_ICON
#define _CAIRO_MAIN_ICON

#include <libawn/libawn.h>
#include <glib-object.h>

G_BEGIN_DECLS

#define AWN_TYPE_CAIRO_MAIN_ICON cairo_main_icon_get_type()

#define AWN_CAIRO_MAIN_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_MAIN_ICON, CairoMainIcon))

#define AWN_CAIRO_MAIN_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_MAIN_ICON, CairoMainIconClass))

#define AWN_IS_CAIRO_MAIN_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_MAIN_ICON))

#define AWN_IS_CAIRO_MAIN_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_MAIN_ICON))

#define AWN_CAIRO_MAIN_ICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_MAIN_ICON, CairoMainIconClass))

typedef struct {
  AwnThemedIcon parent;
} CairoMainIcon;

typedef struct {
  AwnThemedIconClass parent_class;
} CairoMainIconClass;

GType cairo_main_icon_get_type (void);

GtkWidget* cairo_main_icon_new (AwnApplet * applet);

void cairo_main_icon_refresh_menu (CairoMainIcon * icon);

G_END_DECLS

#endif /* _CAIRO_MENU_APPLET */
