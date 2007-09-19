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
    gboolean (*construct_fn)(GtkWidget ** w,gint call_interval,void *data);
    gboolean (*destruct_fn)(GtkWidget ** w,void *data);
    void * data;
    int x1;
    int x2;
    int y1;
    int y2;
    GtkWidget * widget;     /*not sure if it is necessary to preserve this.  but keep it for now */
} Awntop_plugs_callbacks;

typedef struct
{
    long     pid;
    int     uid;
    int     pri;
    int     nice;
    long    virt;
    long    res;
    long    shr;
    long     cpu;
    long     mem;
    long    time;
    char    cmd[40];  //From _glibtop_proc_state structure.
        
}Topentry;

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
    GTree*  pixbufs;
    
    GSList *    awntop_plugs;
    long proctime_tree_reaping;
    

	GtkWidget *mainwindow;    
    GtkWidget *maintable;	
	
	GtkWidget *vbox;
	gboolean  mainwindowvisible;
	GtkWidget *box;	
	AwnApplet *applet ;	
    
    Topentry **topentries;  	
    int num_top_entries;    
	
	glibtop_mem libtop_mem;
	cairo_t *   demo_plug_cr;
} Awntop;


void toggle_awntop_window(Awntop *awntop);
void create_awntop_window(Awntop *awntop);
void destroy_awntop_window(Awntop *awntop);
void register_awntop( Awntop * awntop,AwnApplet *applet);

void register_awntop_plug(      Awntop * awntop,
                                gboolean (*construct_fn)(GtkWidget ** ,gint ,void *),
                                gboolean (*destruct_fn)(GtkWidget ** ,void *),
                                int x1, 
                                int x2, 
                                int y1, 
                                int y2,
                                void * arb_data
                          );                          
/*need an unregister*/                          

#define TOP_TABLE_VOFFSET 4

#endif
