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
/* cairo-menu-item.h */

#ifndef _CAIRO_MENU_ITEM
#define _CAIRO_MENU_ITEM

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define AWN_TYPE_CAIRO_MENU_ITEM cairo_menu_item_get_type()

#define AWN_CAIRO_MENU_ITEM(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItem))

#define AWN_CAIRO_MENU_ITEM_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItemClass))

#define AWN_IS_CAIRO_MENU_ITEM(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_MENU_ITEM))

#define AWN_IS_CAIRO_MENU_ITEM_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_MENU_ITEM))

#define AWN_CAIRO_MENU_ITEM_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItemClass))

typedef struct {
  GtkImageMenuItem parent;
} CairoMenuItem;

typedef struct {
  GtkImageMenuItemClass parent_class;
} CairoMenuItemClass;

GType cairo_menu_item_get_type (void);

GtkWidget* cairo_menu_item_new (void);

GtkWidget* cairo_menu_item_new_with_label (const gchar * label);

void cairo_menu_item_set_source (CairoMenuItem *item, gchar * drag_data);


G_END_DECLS

#endif /* _CAIRO_MENU_ITEM */
