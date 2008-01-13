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

#ifndef __CAIRO_MENU__
#define __CAIRO_MENU__

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-cairo-utils.h>
#include "config_entries.h"


typedef struct
{
	AwnApplet 	*applet;
	GtkWidget 	*mainwindow;    
    GtkWidget 	*mainfixed;
    GtkWidget 	*mainbox;
    GSList		*menu_data;
    

}Cairo_main_menu;

Cairo_main_menu * dialog_new(AwnApplet *applet);
void pos_dialog(GtkWidget * mainwindow);

#endif 

