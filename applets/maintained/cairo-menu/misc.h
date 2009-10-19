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

#ifndef _CAIRO_MISC
#define _CAIRO_MISC

#include <libdesktop-agnostic/fdo.h>
#include <gtk/gtk.h>
#include <libdesktop-agnostic/gtk.h>
#include <libdesktop-agnostic/vfs.h>
#include "cairo-menu-item.h"
#include "cairo-menu.h"
#include "cairo-menu-applet.h"

#define XDG_OPEN "xdg-open"

DesktopAgnosticFDODesktopEntry * get_desktop_entry (gchar * desktop_file);

void _launch (GtkMenuItem *menu_item,gchar * desktop_file);

GtkWidget * get_gtk_image (const gchar const * icon_name);

GtkWidget * get_recent_menu (void);


void  _remove_menu_item  (GtkWidget *menu_item,GtkWidget * menu);
void  _fillin_connected(DesktopAgnosticVFSVolume *volume,CairoMenu *menu);
void _exec (GtkMenuItem *menuitem,gchar * cmd);

gboolean _button_press_dir (GtkWidget *menu_item, GdkEventButton *event, CallbackContainer * c);

MenuInstance * get_menu_instance ( AwnApplet * applet,
                                  GetRunCmdFunc run_cmd_fn,
                                  GetSearchCmdFunc search_cmd_fn,
                                  AddIconFunc add_icon_fn,
                                  CheckMenuHiddenFunc check_menu_hidden_fn,
                                  gchar * submenu_name,
                                  gint flags);

#endif /* _CAIRO_MISC */
