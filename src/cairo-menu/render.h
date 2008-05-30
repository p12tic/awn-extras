/*
 * Copyright (C) 2007, 2008 Rodney Cryderman <rcryderman@gmail.com>
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


#ifndef __CAIRO_MENU_RENDER_
#define __CAIRO_MENU_RENDER_
#include <gtk/gtk.h>
#include "menu_list_item.h"
#include "menu.h"

void render_entry(Menu_list_item *entry, int max_width);
void render_directory(Menu_list_item *directory, int max_width);
void _fixup_menus(GtkWidget * node, GtkWidget * subwidget);

void render_menu_widgets(Menu_list_item * menu_item, GtkWidget * mainbox);
void hide_search(void);
void measure_width(Menu_list_item * menu_item, int * max_width);
gboolean _hide_all_windows(gpointer null);

GtkWidget * build_menu_widget(Menu_item_color * mic, char * text, GdkPixbuf *pbuf, GdkPixbuf *pover, int max_width);

#endif
