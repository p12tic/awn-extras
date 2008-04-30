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

#ifndef __CAIRO_MENU__
#define __CAIRO_MENU__

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-cairo-utils.h>
#include "config_entries.h"



typedef struct 
{
	gint 	x;
	gint	y;
	gint	width;
	gint	height;
	GList* children;
		
}Win_man;


typedef struct
{

	AwnApplet 			*applet;
    GSList				*menu_data;
        
    Win_man				*window_manage;
	Cairo_menu_config 	cairo_menu_config;
}Cairo_main_menu;


Cairo_main_menu * dialog_new(AwnApplet *applet);
void pos_dialog(GtkWidget * mainwindow);
void fixed_move(GtkWidget *widget,gint x,gint y);
void fixed_put(GtkWidget *widget,gint x,gint y);
void hide_all_menus(void);
GtkWidget * menu_new(GtkWidget * parent_menu);

#endif 

