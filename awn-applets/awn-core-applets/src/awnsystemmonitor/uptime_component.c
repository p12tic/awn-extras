
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-gconf.h>
#include <libawn/awn-applet-dialog.h>
#include <libawn/awn-applet-simple.h>
#include <glib.h>

#include <glibtop/uptime.h>
#include <glibtop/cpu.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-title.h>

#include "uptime_component.h"
#include "dashboard_util.h"
#include "dashboard.h"
#include "config.h"

#undef NDEBUG
#include <assert.h>

#define GCONF_UPTIME_SIZE_MULT GCONF_PATH  "/component_uptime_scale"
#define GCONF_UPTIME_IGNORE_GTK  GCONF_PATH "/component_uptime_ignore_gtk_bg_fg"
#define GCONF_UPTIME_NO_GTK_FG  GCONF_PATH "/component_uptime_no_gtk_fg"
#define GCONF_UPTIME_NO_GTK_BG  GCONF_PATH "/component_uptime_no_gtk_bg"


typedef struct
{
	int timer;
	int seconds,minutes,hours,days;

    float size_mult;
    gboolean ignore_gtk;
    AwnColor    bg;             /*colours if gtk colours are overridden */
    AwnColor    fg;      
}Uptime_plug_data;

static gboolean decrease_step(Uptime_plug_data **p);
static gboolean increase_step(Uptime_plug_data **p);
static gboolean render(GtkWidget ** pwidget,gint interval,Uptime_plug_data **p);
static gboolean query_support_multiple(void);
static void destruct(Uptime_plug_data **p);
static void construct(Uptime_plug_data **p);
static const char* get_component_name(void *);
static const char* get_component_friendly_name(void *d);
static GtkWidget* attach_right_click_menu(Uptime_plug_data **p);
static gboolean _toggle_gtk(GtkWidget *widget, GdkEventButton *event, Uptime_plug_data *p);
static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, Uptime_plug_data *p);
static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, Uptime_plug_data *p);

static void set_colour(Uptime_plug_data *p,AwnColor* colour,const char * mess,const char * gconf_key);

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



void * uptime_plug_lookup(int fn_id)
{
    assert(fn_id<MAX_CALLBACK_FN);
    return plug_fns[fn_id];
}


static GtkWidget* attach_right_click_menu(Uptime_plug_data **p)
{
    Uptime_plug_data * plug_data=*p;
    GtkWidget * menu_items;
    GtkWidget *menu = gtk_menu_new ();
    
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_gtk),"Ignore gtk bg/fg",plug_data);        
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_fg),"Non GTK Foreground",plug_data);        
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_set_bg),"Non GTK Background",plug_data);                        
    return menu;     
}

static void _notify_color_change(void *p)
{
    Uptime_plug_data *data=p;
    assert(p);
}

static gboolean _toggle_gtk(GtkWidget *widget, GdkEventButton *event, Uptime_plug_data *p)
{  
    p->ignore_gtk=!p->ignore_gtk;
    gconf_client_set_bool(get_dashboard_gconf(),GCONF_UPTIME_IGNORE_GTK ,p->ignore_gtk, NULL );        
    return TRUE;
}

static void set_colour(Uptime_plug_data *p,AwnColor* colour,const char * mess,const char * gconf_key)
{
    char *svalue;
    pick_awn_color(colour,mess, p,NULL);
    svalue=dashboard_cairo_colour_to_string(colour);
    gconf_client_set_string( get_dashboard_gconf(), gconf_key,svalue , NULL );    
    free(svalue);
}

static gboolean _set_fg(GtkWidget *widget, GdkEventButton *event, Uptime_plug_data *p)
{  
    set_colour(p,&p->fg,"Foreground Colour if Ignore gtk",GCONF_UPTIME_NO_GTK_FG);
    return TRUE;
}

static gboolean _set_bg(GtkWidget *widget, GdkEventButton *event, Uptime_plug_data *p)
{  
    set_colour(p,&p->bg,"Background Colour if Ignore gtk",GCONF_UPTIME_NO_GTK_BG);
    return TRUE;
}


static const char* get_component_friendly_name(void *d)
{
    const char * name="Uptime";
    return name;
}   


static const char* get_component_name(void *d)
{
    const char * name="component_uptime";
    return name;
}   


static gboolean decrease_step(Uptime_plug_data **p)
{
    Uptime_plug_data *data=*p;
    data->size_mult=data->size_mult * 5.0 /6.0;
    gconf_client_set_float(get_dashboard_gconf(),GCONF_UPTIME_SIZE_MULT,data->size_mult, NULL );                    
}
static gboolean increase_step(Uptime_plug_data **p)
{
    Uptime_plug_data *data=*p;
    data->size_mult=data->size_mult * 1.2;
    gconf_client_set_float(get_dashboard_gconf(),GCONF_UPTIME_SIZE_MULT,data->size_mult, NULL );                    
}
static gboolean query_support_multiple(void)
{

    return FALSE;
}

static void construct(Uptime_plug_data **p)
{
    *p=g_malloc(sizeof(Uptime_plug_data ));
    Uptime_plug_data * data=*p;
    GConfValue *value;  
    gchar * svalue;  
    
    data->timer=1000;
    
    value = gconf_client_get( get_dashboard_gconf(),GCONF_UPTIME_IGNORE_GTK, NULL );
    if ( value ) 
    {
        data->ignore_gtk = gconf_client_get_bool(get_dashboard_gconf(),GCONF_UPTIME_IGNORE_GTK, NULL );
    } 
    else 
    {
        data->ignore_gtk=FALSE;    
        gconf_client_set_bool(get_dashboard_gconf(),GCONF_UPTIME_IGNORE_GTK,
                    data->ignore_gtk,NULL );                        
    }


    svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_UPTIME_NO_GTK_BG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string( get_dashboard_gconf(), GCONF_UPTIME_NO_GTK_BG, svalue=strdup("222299EE"), NULL );
    }
    awn_cairo_string_to_color( svalue,&data->bg );    
    g_free(svalue);


    svalue = gconf_client_get_string(get_dashboard_gconf(), GCONF_UPTIME_NO_GTK_FG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string( get_dashboard_gconf(), GCONF_UPTIME_NO_GTK_FG, svalue=strdup("00000000"), NULL );
    }
    awn_cairo_string_to_color( svalue,&data->fg );    
    g_free(svalue);
    
    
    value = gconf_client_get( get_dashboard_gconf(), GCONF_UPTIME_SIZE_MULT, NULL );
    if ( value ) 
    {
        data->size_mult = gconf_client_get_float(get_dashboard_gconf(),GCONF_UPTIME_SIZE_MULT, NULL );
    } 
    else 
    {
        data->size_mult=1.0;
    }    
}

static void destruct(Uptime_plug_data **p)
{
    g_free(*p);
}



static gboolean render(GtkWidget ** pwidget,gint interval,Uptime_plug_data **p)
{
    char buf[256];
	glibtop_uptime uptime;
	long tmp;
    Uptime_plug_data * data=*p;
    static int width=-1;
    static int height=-1;
    cairo_text_extents_t    extents;
    dashboard_cairo_widget c_widge;           
    float mult;
        
    data->timer=data->timer-interval;
	if (data->timer<=0)
	{
	    glibtop_get_uptime(&uptime);	
	    tmp=uptime.uptime;
	    data->seconds=tmp % 60;
	    tmp=tmp/60;	//tmp is now minutes
	    data->minutes=tmp%60;
	    tmp=tmp / 60;	//tmp now hours
	    data->hours=tmp % 24;
	    tmp=tmp / 24;
	    data->days=tmp;    
     	snprintf(buf,sizeof(buf),"Up Time:%ld:%02ld:%02ld:%02ld",data->days,
	                            data->hours,data->minutes,
	                            data->seconds);
        data->timer=1000;
        /*there is an issue if this widget starts out overly large... the maintable sizes itself too 
        and doesn't properly resize itself downwards...  So we start small for the first second
        and that way give it time to shrink before adjusting to a large scale */
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
            width=extents.width+10;  
            return;          
        }
        cairo_show_text(c_widge.cr, buf);                    
        del_cairo_widget(&c_widge);        
        
        return TRUE;	                        
    }
    else
    {
        return FALSE;
    }
}
