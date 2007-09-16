#ifndef AWNTOP_H_
#define AWNTOP_H_

/*
 * Copyright (c) 2007 Rodney Cryderman <rcryderman@gmail.com>
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



#include <libawn/awn-applet.h>
#include <libawn/awn-applet-gconf.h>
#include <libawn/awn-applet-dialog.h>
#include <libawn/awn-applet-simple.h>
#include <glib.h>
#include <gtk/gtk.h>

#include <glibtop/mem.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-title.h>


typedef struct
{
	long 	days;
	long 	hours;
	long	minutes;
	long 	seconds;
} Uptimedata;


typedef struct
{
	guint	updateinterval;
	Uptimedata uptimedata;	
	int maxtopentries;
	long    user;
	long    idle;
	long    sys;
    long        accum_user;
    long        accum_idle;
    long        accum_sys;
    int(*compar)(const void *, const void *);
    
    long    *   displayed_pid_list;
    GTree*  proctimes;
    GTree*  icons;    
    long proctime_tree_reaping;
    

	GtkWidget *mainwindow;
	GtkWidget *table;
	GtkWidget *vbox;
	gboolean  mainwindowvisible;
	GtkWidget *box;	
	AwnApplet *applet ;	
	
	glibtop_mem libtop_mem;
} Awntop;


void toggle_awntop_window(Awntop *awntop);
void create_awntop_window(Awntop *awntop);
void destroy_awntop_window(Awntop *awntop);
void register_awntop( Awntop * awntop,AwnApplet *applet);

void embed_cairo(Awntop *awntop,cairo_t *cr, gint x1,gint x2,gint y1, gint y2);
#define TOP_TABLE_VOFFSET 4

#endif
