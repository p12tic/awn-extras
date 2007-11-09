/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
 *
 * This is a CPU Load Applet for the Avant Window Navigator.  It
 * borrows heavily from the Gnome system monitor, so kudos go to
 * the authors of that program:
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
 
 
#ifndef __CAIRO_MENU_CONFIG_
#define __CAIRO_MENU_CONFIG_


typedef struct
{
	AwnColor	bg;
	AwnColor	fg;	

}Menu_item_color;

typedef struct
{
	Menu_item_color	normal;
	Menu_item_color hover;
	Menu_item_color selected;
	int			text_size;
	GTree *		submenu_deps;
	
	gboolean	show_search;
	char		*	search_cmd;
	gboolean	show_run;	
	gboolean	do_fade;		
	int			menu_item_text_len;
	float 		menu_item_gradient_factor;
	gboolean	honour_gtk;
}Cairo_menu_config;

void read_config(void);

#endif

