#ifndef Dashboard_H_
#define Dashboard_H_

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


typedef gboolean (*Construct_head_foot)(GtkWidget ** );

typedef struct
{
    gboolean (*construct_fn)(GtkWidget ** w,gint call_interval,void *data);
    gboolean (*destruct_fn)(GtkWidget ** w,void *data);
    void * data;
    int x1;
    int x2;
    int y1;
    int y2;
    Construct_head_foot * headers_footers;
    GtkWidget * widge_wrap;
    GtkWidget * widget;     /*not sure if it is necessary to preserve this.  but keep it for now */
} Dashboard_plugs_callbacks;



typedef struct
{
	guint	updateinterval;
	Uptimedata uptimedata;	

	long    user;
	long    idle;
	long    sys;
    long        accum_user;
    long        accum_idle;
    long        accum_sys;
    
    GSList *    Dashboard_plugs;
	gboolean    need_win_update;
	gboolean    force_update;
		
	GtkWidget *mainwindow;    
    GtkWidget *maintable;	
    GtkWidget *vbox;
	gboolean  mainwindowvisible;
	GtkWidget *box;	
	AwnApplet *applet ;	

	cairo_t *   demo_plug_cr;
	

} Dashboard;


void toggle_Dashboard_window(Dashboard *Dashboard);
void create_Dashboard_window(Dashboard *Dashboard);
void destroy_Dashboard_window(Dashboard *Dashboard);
void register_Dashboard( Dashboard * Dashboard,AwnApplet *applet);

Dashboard_plugs_callbacks * register_Dashboard_plug(      Dashboard * Dashboard,
                                gboolean (*construct_fn)(GtkWidget ** ,gint ,void *),
                                gboolean (*destruct_fn)(GtkWidget ** ,void *),
                                int x1, 
                                int x2, 
                                int y1, 
                                int y2,
                                void * arb_data
                          );            
                          
void dashboard_redraw_signal(Dashboard * );


                                        
/*need an unregister*/                          


#endif
