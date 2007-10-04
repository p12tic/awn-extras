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


#define MAX_CALLBACK_FN 10

enum {  DASHBOARD_CALLBACK_CONSTRUCT, 
        DASHBOARD_CALLBACK_DESTRUCT, 
        DASHBOARD_CALLBACK_RENDER, 
        DASHBOARD_CALLBACK_QUERY_SUPPORT_MULTIPLE,
        DASHBOARD_CALLBACK_DUMMY_FN,
        DASHBOARD_CALLBACK_INCREASE_STEP_FN,
        DASHBOARD_CALLBACK_DECREASE_STEP_FN,
        DASHBOARD_CALLBACK_ATTACH_RIGHT_CLICK_MENU_FN,
        DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN,
        DASHBOARD_CALLBACK_GET_COMPONENT_FRIENDLY_NAME_FN                      
        };
        
#define DASHBOARD_DEFAULT_X_TILES 41
#define DASHBOARD_DEFAULT_Y_TILES 41
#define DASHBOARD_TIMER_FREQ 100     

typedef gboolean (*Construct_head_foot)(GtkWidget ** );

typedef struct
{
    void * (*lookup_fn)(int);
    void * data;
    int x1;
    int x2;
    int y1;
    int y2;
    Construct_head_foot * headers_footers;
    GtkWidget * widge_wrap;
    GtkWidget * widget;     
    GtkWidget*  right_click_menu;
    gboolean dead_but_does_not_know_it;
    gboolean enabled;
} Dashboard_plugs_callbacks;



typedef struct
{
	guint	updateinterval;

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

	GtkWidget *box;	
	AwnApplet *applet ;	

	cairo_t *   demo_plug_cr;
	
    GtkWidget * toptile;	
    GtkWidget *right_click_menu;

} Dashboard;

typedef const char* (*get_component_name_fn)(void *);
typedef const char* (*get_component_friendly_name_fn)(void *);
typedef GtkWidget* (*attach_right_click_menu_fn)(void *);
typedef void (*destruct_fn)(void *);
typedef void (*construct_fn)(void *);
typedef gboolean (*render_fn)(GtkWidget ** ,gint ,void *);
typedef gboolean (*query_support_multiple_fn)(void);
typedef gboolean (*increase_step_fn)(void*);
typedef gboolean (*decrease_step_fn)(void*);
gboolean _cairo_demo_plug(GtkWidget ** pwidget,gint interval,void * data);
void toggle_Dashboard_window(Dashboard *Dashboard);
void create_Dashboard_window(Dashboard *Dashboard);
void destroy_Dashboard_window(Dashboard *Dashboard);
void register_Dashboard( Dashboard * Dashboard,AwnApplet *applet);

Dashboard_plugs_callbacks * register_Dashboard_plug(      Dashboard * Dashboard,
                                void * (*lookup_fn)(int),
                                int x1, 
                                int x2, 
                                int y1, 
                                int y2,
                                void * arb_data
                          );            
                          
void dashboard_redraw_signal(Dashboard * );


                                        
/*need an unregister*/                          


#endif
