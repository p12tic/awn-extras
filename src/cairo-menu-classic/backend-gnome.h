/*
 * Copyright (C) 2007 Rodney Cryderman <rcryderman@gmail.com>
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

#ifndef _BACKEND_GNOME_
#define _BACKEND_GNOME_
#include "menu_list_item.h"
GSList* get_menu_data(gboolean show_search,gboolean show_run,gboolean show_places,gboolean show_logout,char* file_manager,char*logout);
void monitor_places(gpointer callback, gpointer data);

gboolean display_message(gchar * summary, gchar * body,glong timeout);

void backend_eject(Menu_list_item * menu_item);
void backend_unmount(Menu_list_item * menu_item);

#endif

