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
#include <gdk/gdk.h>
#include <string.h>
#include <time.h>

#include "date_time_component.h"
#include "dashboard_util.h"
#include "dashboard.h"
#include "config.h"

#undef NDEBUG
#include <assert.h>

#define GCONF_DATE_TIME_SIZE_MULT GCONF_PATH  "/component_date_time_scale"
#define GCONF_DATE_TIME_IGNORE_GTK  GCONF_PATH "/component_date_time_ignore_gtk_bg_fg"
#define GCONF_DATE_TIME_NO_GTK_FG  GCONF_PATH "/component_date_time_no_gtk_fg"
#define GCONF_DATE_TIME_NO_GTK_BG  GCONF_PATH "/component_date_time_no_gtk_bg"


typedef struct
{
    double width;
    double height;
	int timer;
	int refresh;
    gboolean ignore_gtk;
    AwnColor    bg;             /*colours if gtk colours are overridden */
    AwnColor    fg;            
    float size_mult;               
}Time_Date_plug_data;

static gboolean render(GtkWidget ** pwidget,gint interval,Time_Date_plug_data **p);
static gboolean query_support_multiple(void);
static void destruct(Time_Date_plug_data **p);
static void construct(Time_Date_plug_data **p);
static gboolean decrease_step(Time_Date_plug_data **p);
static gboolean increase_step(Time_Date_plug_data **p);
static GtkWidget* attach_right_click_menu(Time_Date_plug_data **p);

static gboolean _toggle_gtk(GtkWidget *widget, GdkEventButton *event, Time_Date_plug_data *p);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, Time_Date_plug_data *p);
static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, Time_Date_plug_data *p);

static const char* get_component_name(void *);
static const char* get_component_friendly_name(void *);


static void * plug_fns[MAX_CALLBACK_FN]={
                        construct,
                        destruct,
                        render,
                        query_support_multiple,
                        NULL,
                        increase_step,
                        decrease_step,
                        attach_right_click_menu,
                        get_component_name,
                        get_component_friendly_name          
                        };




void * date_time_plug_lookup(int fn_id)
{
    assert(fn_id<MAX_CALLBACK_FN);
    return plug_fns[fn_id];
}

static GtkWidget* attach_right_click_menu(Time_Date_plug_data **p)
{
    Time_Date_plug_data * plug_data=*p;
    GtkWidget * menu_items;
    GtkWidget *menu = gtk_menu_new ();
    
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_gtk),"Ignore gtk bg/fg",plug_data);        
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_fg),"Non GTK Foreground",plug_data);        
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_bg),"Non GTK Background",plug_data);                        
    return menu;     
}

static gboolean _toggle_gtk(GtkWidget *widget, GdkEventButton *event, Time_Date_plug_data *p)
{  
    p->ignore_gtk=!p->ignore_gtk;
    gconf_client_set_bool(get_dashboard_gconf(),GCONF_DATE_TIME_IGNORE_GTK ,p->ignore_gtk, NULL );        
    return TRUE;
}

static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, Time_Date_plug_data *p)
{  
    set_colour(p,&p->fg,"Foreground Colour if Ignore gtk",GCONF_DATE_TIME_NO_GTK_FG);
    return TRUE;
}

static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, Time_Date_plug_data *p)
{  
    set_colour(p,&p->bg,"Foreground Colour if Ignore gtk",GCONF_DATE_TIME_NO_GTK_BG);
    return TRUE;
}

static gboolean query_support_multiple(void)
{
    return FALSE;
}

static void destruct(Time_Date_plug_data **p)
{
    g_free(*p);
    return;
}
static void construct(Time_Date_plug_data **p)
{
    *p=g_malloc(sizeof(Time_Date_plug_data ));
    Time_Date_plug_data * data=*p;
    GConfValue *value;  
    gchar * svalue;  
    
    data->timer=1000;    
    
    value = gconf_client_get( get_dashboard_gconf(),GCONF_DATE_TIME_IGNORE_GTK, NULL );
    if ( value ) 
    {
        data->ignore_gtk = gconf_client_get_bool(get_dashboard_gconf(),GCONF_DATE_TIME_IGNORE_GTK, NULL );
    } 
    else 
    {
        data->ignore_gtk=FALSE;    
        gconf_client_set_bool(get_dashboard_gconf(),GCONF_DATE_TIME_IGNORE_GTK,
                    data->ignore_gtk,NULL );                        
    }


    svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_DATE_TIME_NO_GTK_BG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string( get_dashboard_gconf(), GCONF_DATE_TIME_NO_GTK_BG, svalue=strdup("222299EE"), NULL );
    }
    awn_cairo_string_to_color( svalue,&data->bg );    
    g_free(svalue);


    svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_DATE_TIME_NO_GTK_FG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string( get_dashboard_gconf(), GCONF_DATE_TIME_NO_GTK_FG, svalue=strdup("00000000"), NULL );
    }
    awn_cairo_string_to_color( svalue,&data->fg );    
    g_free(svalue);
    

    value = gconf_client_get( get_dashboard_gconf(), GCONF_DATE_TIME_SIZE_MULT, NULL );
    if ( value ) 
    {
        data->size_mult = gconf_client_get_float(get_dashboard_gconf(), GCONF_DATE_TIME_SIZE_MULT, NULL );
    } 
    else 
    {
        data->size_mult=1.0;
    }    
    
}

static gboolean decrease_step(Time_Date_plug_data **p)
{
    Time_Date_plug_data *data=*p;
    data->size_mult=data->size_mult * 1.2;
//    gconf_client_set_float(get_dashboard_gconf(),GCONF_UPTIME_SIZE_MULT,data->size_mult, NULL );        
}
static gboolean increase_step(Time_Date_plug_data **p)
{
    Time_Date_plug_data *data=*p;
    data->size_mult=data->size_mult * 5.0 /6.0;
//    gconf_client_set_float(get_dashboard_gconf(),GCONF_UPTIME_SIZE_MULT,data->size_mult, NULL );       
}

static const char* get_component_name(void *p)
{
    const char * name="Date/Time";
    return name;
}
static const char* get_component_friendly_name(void *p)
{
    const char * name="component_date_time";
    return name;
}

static gboolean render(GtkWidget ** pwidget,gint interval,Time_Date_plug_data **p)
{
    char buf[200];
    time_t t;
    struct tm *tmp;
    char * format="%r";
    static int width=-1;
    static int height=-1;
    Time_Date_plug_data * data=*p;
    dashboard_cairo_widget c_widge; 
    float mult;
    cairo_text_extents_t    extents;            

    data->timer=data->timer-interval;
	if (data->timer<=0)
	{
        data->timer=1000;       /*FIXME... you might not want this refresh rate
                                if you're not displaying seconds...*/
        t = time(NULL);
        tmp = localtime(&t);
        if (tmp == NULL) 
        {
            printf("Failure calling localtime()\n");
            return FALSE;
        }

        if (strftime(buf, sizeof(buf), format, tmp) == 0) 
        {
            printf("strftime result undefined\n");
            return FALSE;
        }

        if( width<0)
        {
            *pwidget=get_cairo_widget(&c_widge,200,30);            
            mult=1;
            use_bg_rgba_colour(c_widge.cr);        
            cairo_set_operator (c_widge.cr, CAIRO_OPERATOR_SOURCE);
            cairo_paint(c_widge.cr);                    
        }
        else
        {
            mult=data->size_mult;
            *pwidget=get_cairo_widget(&c_widge,width*mult,height*mult);
            awn_cairo_rounded_rect (c_widge.cr,0,0,width*mult,height*mult,height*mult*0.1,ROUND_ALL);                    
            if (data->ignore_gtk)
            {
                cairo_set_source_rgba (c_widge.cr,data->bg.red,data->bg.green,data->bg.blue,data->bg.alpha);
            }
            else
            use_bg_rgba_colour(c_widge.cr);                        
            cairo_fill(c_widge.cr);            
        }        
        
	    cairo_select_font_face (c_widge.cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
	    cairo_set_font_size (c_widge.cr, dashboard_get_font_size( DASHBOARD_FONT_SMALL)*mult );
        
        if (data->ignore_gtk)
        {
            cairo_set_source_rgba (c_widge.cr,data->fg.red,data->fg.green,data->fg.blue,data->fg.alpha);
        }
        else
            use_fg_rgb_colour(c_widge.cr);
        cairo_move_to(c_widge.cr, 5.0*mult, height*mult*0.7);        
        if( width<0)
        {
            cairo_text_extents(c_widge.cr,buf,&extents);                          
            height=extents.height+2;
            width=extents.width+5;  
            return;          
        }
        cairo_show_text(c_widge.cr, buf);                    
        del_cairo_widget(&c_widge);        
        
    }       

}
