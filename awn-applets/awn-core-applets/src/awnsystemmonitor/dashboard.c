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


#include <glibtop/uptime.h>
#include <glibtop/cpu.h>

#define _GNU_SOURCE
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>
#include <signal.h>
#include <sys/types.h>

#include <dirent.h>
#include <libgen.h>
#include <gdk/gdk.h>


#include "dashboard.h"
#include "dashboard_util.h"
#include "config.h"

#undef NDEBUG
#include <assert.h>

#define GCONF_DASHBOARD_PREFIX GCONF_PATH "/dashboard_component_mgmt_"

static void draw_main_window(Dashboard *Dashboard);

static gboolean _Dashboard_time_handler (Dashboard *);

static void Dashboard_plugs_construct(gpointer data,gpointer user_data);
static void Dashboard_plugs_destruct(gpointer data,gpointer user_data);

static gboolean _visibility_notify_event(GtkWidget *widget, 
                                GdkEventButton *event, Dashboard * dashboard);
static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event, 
                                Dashboard * dashboard);
static gboolean _increase_step (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static gboolean _decrease_step (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static gboolean _remove (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static gboolean _move_left (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static gboolean _move_right (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static gboolean _move_up (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static gboolean _move_down (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node );
static void _check_enabled  (gpointer data,gpointer user_data);
static gboolean _dashboard_button_clicked_event (GtkWidget *widget, 
                                GdkEventButton *event,Dashboard  * dashboard );
static void update_pos(Dashboard_plugs_callbacks * node);
static void build_dashboard_right_click(Dashboard  * dashboard);
static gboolean _toggle_component(Dashboard_plugs_callbacks *p);

/*FIXME  --- */
static void show_main_window(Dashboard *Dashboard);
static void hide_main_window(Dashboard *Dashboard);


static    int tiles_x;
static    int tiles_y;
	

Dashboard_plugs_callbacks* register_Dashboard_plug(      Dashboard * Dashboard,
                                void * (*lookup_fn)(int),
                                int x1, 
                                int x2, 
                                int y1, 
                                int y2,
                                void * arb_data
                          )
{
    Dashboard_plugs_callbacks *node=g_malloc(sizeof(Dashboard_plugs_callbacks));
    construct_fn construct;
    GtkWidget *menu_items;
    GtkWidget *component_menu_items;   
    GtkWidget *movemenu;
    attach_right_click_menu_fn attach_right_fn;
    get_component_name_fn   get_component_name;
    get_component_friendly_name_fn   get_component_friendly_name;    
    char * comp_name=NULL;
    char * comp_friendly_name=NULL;    
    GConfValue *value;
    char * keyname;
    int tmp;
                
                    
    node->lookup_fn=lookup_fn;
    construct=node->lookup_fn(DASHBOARD_CALLBACK_CONSTRUCT);
    if(construct)
    {
        construct(arb_data );
    }      
    node->data=arb_data;
        
    get_component_name=node->lookup_fn(
                                        DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN
                                        );
    /*at this point in time I don't want any anonymous components :-) */
    assert(get_component_name);
    if (get_component_name)
    {
        comp_name=(char *) get_component_name(node->data);
    }        

    get_component_friendly_name=node->lookup_fn(
                            DASHBOARD_CALLBACK_GET_COMPONENT_FRIENDLY_NAME_FN
                            );
    assert(get_component_friendly_name);
    if (get_component_friendly_name)
    {
        comp_friendly_name=(char *) get_component_friendly_name(node->data);
    }        


    node->enabled=TRUE;
        
    node->dead_but_does_not_know_it=FALSE;


    tmp=strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name)+strlen("_enabled")+1;
    keyname=g_malloc(tmp);
    if (keyname)
    {
        strcpy(keyname,GCONF_DASHBOARD_PREFIX);
        strcat(keyname,comp_name);
        strcat(keyname,"_enabled");
        value = gconf_client_get( get_dashboard_gconf(),keyname,NULL );
        if ( value ) 
        {
            node->enabled = gconf_client_get_bool(get_dashboard_gconf(),
                                                keyname, NULL 
                                                );
        }         
    }
    g_free(keyname);        

    node->x1=x1;
    node->x2=x2;    
    tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name)+strlen("_posx1")+1;
    keyname=g_malloc(tmp);
    if (keyname)
    {
        strcpy(keyname,GCONF_DASHBOARD_PREFIX);
        strcat(keyname,comp_name);
        strcat(keyname,"_posx1");
        value = gconf_client_get( get_dashboard_gconf(),keyname,NULL );
        if ( value ) 
        {
            node->x1 = gconf_client_get_int(get_dashboard_gconf(),keyname,NULL);
        }         
    }
    g_free(keyname);        
    node->y1=y1;
    node->y2=y2;            
    tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name)+strlen("_posy1")+1;
    keyname=g_malloc(tmp);
    if (keyname)
    {
        strcpy(keyname,GCONF_DASHBOARD_PREFIX);
        strcat(keyname,comp_name);
        strcat(keyname,"_posy1");
        value = gconf_client_get( get_dashboard_gconf(),keyname,NULL );
        if ( value ) 
        {
            node->y1 = gconf_client_get_int(get_dashboard_gconf(),keyname,NULL);
        }         
    }
    g_free(keyname);    
    node->widget=NULL;
    node->headers_footers=NULL;
    node->widge_wrap=NULL;    
    
    node->right_click_menu=gtk_menu_new ();
    gtk_menu_set_screen(node->right_click_menu,NULL);

    if (lookup_fn(DASHBOARD_CALLBACK_INCREASE_STEP_FN) )
        dashboard_build_clickable_menu_item(    node->right_click_menu, 
                                    G_CALLBACK(_increase_step),"Larger",node
                                    );    
                                
    if (lookup_fn(DASHBOARD_CALLBACK_DECREASE_STEP_FN) )
        dashboard_build_clickable_menu_item(    node->right_click_menu, 
                                    G_CALLBACK(_decrease_step),"Smaller",node
                                    );    
    movemenu = gtk_menu_new ();

    dashboard_build_clickable_menu_item(movemenu,G_CALLBACK(_move_left),
                                        "Left",node
                                        );    
    dashboard_build_clickable_menu_item(movemenu,G_CALLBACK(_move_right),
                                        "Right",node
                                        );    
    dashboard_build_clickable_menu_item(movemenu,G_CALLBACK(_move_up),
                                        "Up",node
                                        );    
    dashboard_build_clickable_menu_item(movemenu,G_CALLBACK(_move_down),
                                        "Down",node
                                        );    

    menu_items = gtk_menu_item_new_with_label ("Move");
    gtk_menu_shell_append (GTK_MENU_SHELL (node->right_click_menu), menu_items);
    gtk_menu_item_set_submenu(menu_items,movemenu);        
    gtk_widget_show (menu_items);    

    dashboard_build_clickable_menu_item(    node->right_click_menu, 
                                G_CALLBACK(_remove),"Remove",node
                                );    
    
    if(attach_right_fn=lookup_fn(DASHBOARD_CALLBACK_ATTACH_RIGHT_CLICK_MENU_FN))
    {
        
        component_menu_items = attach_right_fn(node->data);
        assert(component_menu_items);
        menu_items = gtk_menu_item_new_with_label ("Component");        
        gtk_menu_shell_append (GTK_MENU_SHELL (node->right_click_menu), 
                                menu_items);
        gtk_widget_show (menu_items);    
        gtk_menu_item_set_submenu (GTK_MENU_ITEM (menu_items),
                                    component_menu_items);        
    }
    Dashboard->Dashboard_plugs=g_slist_prepend(Dashboard->Dashboard_plugs,node);
    build_dashboard_right_click(Dashboard);
    return node;
}                                


void register_Dashboard( Dashboard * dashboard,AwnApplet *applet)
{
    int i;
    GdkColor color;
    GdkScreen* pScreen;  
    int width,height;
               
    dashboard->updateinterval=DASHBOARD_TIMER_FREQ;		
    dashboard->force_update=FALSE;
    dashboard->applet=applet;
    dashboard->Dashboard_plugs=NULL;     /*there are no plugs registered yet*/
    dashboard->box = gtk_alignment_new (0.5, 0.5, 1, 1);
    dashboard->mainwindow = awn_applet_dialog_new (applet);
    dashboard->right_click_menu=NULL;
    tiles_x=DASHBOARD_DEFAULT_X_TILES;
    tiles_y=DASHBOARD_DEFAULT_Y_TILES;    

    
    gtk_window_set_focus_on_map (GTK_WINDOW (dashboard->mainwindow), TRUE);
    gtk_container_add (GTK_CONTAINER (dashboard->mainwindow), dashboard->box);
    dashboard->vbox = gtk_vbox_new (FALSE, 8);   
    dashboard->maintable = gtk_table_new (tiles_x, tiles_y, FALSE);        
    gtk_container_add (GTK_CONTAINER (dashboard->box), dashboard->vbox);        
    gtk_table_set_col_spacings (GTK_TABLE(dashboard->maintable),0);    
    gtk_box_pack_end (GTK_BOX (dashboard->vbox), dashboard->maintable, TRUE, 
                        TRUE, 0);  
    pScreen = gtk_widget_get_screen (dashboard->mainwindow);
    width=gdk_screen_get_width(pScreen)/2/tiles_x;
    height=gdk_screen_get_height(pScreen)/2/tiles_y;    

    for(i=0;i<tiles_x-1;i++)
    {
        dashboard_cairo_widget c_widget;
        GtkWidget * widget=get_cairo_widget(&c_widget,width,height/6);
        rgba_colour fg;
//        get_bg_rgba_colour(&fg);
        cairo_set_source_rgba (c_widget.cr,0,0,0,0.2);
        cairo_set_operator (c_widget.cr, CAIRO_OPERATOR_SOURCE);
        cairo_paint (c_widget.cr);
        gtk_table_attach_defaults (GTK_TABLE (dashboard->maintable), widget,
                                 i, i+1, 0, 1);        
        del_cairo_widget(&c_widget);                
    }   
    for(i=1;i<tiles_y-1;i++)
    {
        dashboard_cairo_widget c_widget;
        GtkWidget * widget=get_cairo_widget(&c_widget,width/6,height);
        //cairo_set_source_rgba (c_widget.cr,0.3, 0.3,0.8,0.5);
        cairo_set_source_rgba (c_widget.cr,0,0,0,0.2);                
//        use_bg_rgba_colour(c_widget.cr) ;       
        cairo_set_operator (c_widget.cr, CAIRO_OPERATOR_SOURCE);
        cairo_paint (c_widget.cr);
        gtk_table_attach_defaults (GTK_TABLE (dashboard->maintable), widget,
                                 tiles_x, tiles_x+1, i, i+1);                
        del_cairo_widget(&c_widget);
    }                    
    g_signal_connect(G_OBJECT(dashboard->mainwindow),"focus-out-event",
                    G_CALLBACK (_focus_out_event),(gpointer)dashboard);    
	g_timeout_add_full(G_PRIORITY_DEFAULT,dashboard->updateinterval,
	                    (GSourceFunc)_Dashboard_time_handler,(gpointer)dashboard
	                    ,NULL
	                    );
    build_dashboard_right_click(dashboard);
    g_signal_connect(G_OBJECT (dashboard->mainwindow), "button-press-event",
                    G_CALLBACK (_dashboard_button_clicked_event),
                    (gpointer)dashboard
                    );    
    gtk_widget_show_all(dashboard->vbox);
    gtk_widget_hide(dashboard->vbox);        
                    
}    


void toggle_Dashboard_window(Dashboard *dashboard)
{
    if (GTK_WIDGET_VISIBLE(dashboard->mainwindow) )
    {
        gtk_widget_hide (dashboard->mainwindow);    
    }
    else
    {
        gtk_widget_show_all (dashboard->mainwindow);                
    }
}

void create_Dashboard_window(Dashboard *Dashboard)
{
    draw_main_window(Dashboard);
}

void destroy_Dashboard_window(Dashboard *Dashboard)
{
    gtk_widget_hide (Dashboard->mainwindow);
}


static gboolean _toggle_component(Dashboard_plugs_callbacks *p)
{
    get_component_name_fn   get_component_name;
    char * comp_name=NULL;
    GConfValue *value;
    char * keyname;
    int tmp;

    p->enabled=!p->enabled;
                    
    get_component_name=p->lookup_fn(DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN);
    if (get_component_name)
    {
        comp_name=(char *) get_component_name(p->data);
    }            
    tmp=strlen(GCONF_DASHBOARD_PREFIX)+ strlen(comp_name)+strlen("_enabled")+1;
    keyname=g_malloc(tmp);
    if (keyname)
    {
        strcpy(keyname,GCONF_DASHBOARD_PREFIX);
        strcat(keyname,comp_name);
        strcat(keyname,"_enabled");
        gconf_client_set_bool(get_dashboard_gconf(),keyname,p->enabled, NULL );  
    }
    g_free(keyname);

}

static gboolean _enable_component(GtkWidget *widget, GdkEventButton *event, 
                                    Dashboard_plugs_callbacks *p)
{  
    _toggle_component(p);
    return TRUE;
}

static void _check_enabled  (gpointer data,gpointer user_data)
{
    Dashboard_plugs_callbacks * node=data;
    Dashboard * dashboard = user_data;
    get_component_friendly_name_fn get_component_friendly_name;
    gchar * sname;
    if (!node->enabled)    
    {
    
        get_component_friendly_name=node->lookup_fn(
                            DASHBOARD_CALLBACK_GET_COMPONENT_FRIENDLY_NAME_FN
                            );
        sname=get_component_friendly_name(node->data);
        dashboard_build_clickable_menu_item(dashboard->right_click_menu, 
                            G_CALLBACK(_enable_component),sname,node
                            );                        
    }
    
}

static void build_dashboard_right_click(Dashboard  * dashboard)
{
    GtkWidget * menu_items;
    gboolean found=FALSE;
    

    if (dashboard->right_click_menu)
        gtk_widget_destroy(dashboard->right_click_menu);
  
    dashboard->right_click_menu=gtk_menu_new ();
    menu_items = gtk_menu_item_new_with_label ("Add Component");
    gtk_menu_shell_append (GTK_MENU_SHELL (dashboard->right_click_menu), 
                                            menu_items
                                            );     
    gtk_widget_show (menu_items);        
    g_slist_foreach(dashboard->Dashboard_plugs,_check_enabled,dashboard);    

}
    
static gboolean _dashboard_button_clicked_event (GtkWidget *widget, 
                                GdkEventButton *event,Dashboard  * dashboard )
{
    GdkEventButton *event_button;
    event_button = (GdkEventButton *) event; 
    enable_suppress_hide_main();
    if (event->button == 3)
    {
        gtk_menu_popup (dashboard->right_click_menu, NULL, NULL, NULL, NULL, 
			  event_button->button, event_button->time);
    }
    return FALSE;
}

/*used for plugs linked list */


static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event,
                                            Dashboard_plugs_callbacks * node )
{
    GdkEventButton *event_button;
    event_button = (GdkEventButton *) event; 
    enable_suppress_hide_main();    
    if (event->button == 3)
    {
        gtk_menu_popup (node->right_click_menu, NULL, NULL, NULL, NULL, 
			  event_button->button, event_button->time);
    }
    return TRUE;
}

static gboolean _increase_step (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node )
{
    increase_step_fn increase=node->lookup_fn(
                                        DASHBOARD_CALLBACK_INCREASE_STEP_FN);
    assert(increase);
    increase(node->data);
    return TRUE;
}

static gboolean _decrease_step (GtkWidget *widget, GdkEventButton *event,    
                                Dashboard_plugs_callbacks * node )
{
    increase_step_fn decrease=node->lookup_fn(
                                        DASHBOARD_CALLBACK_DECREASE_STEP_FN);
    assert(decrease);
    decrease(node->data);
    return TRUE;
}

static gboolean _remove(GtkWidget *widget, GdkEventButton *event,    
                            Dashboard_plugs_callbacks * node )
{
    node->dead_but_does_not_know_it=TRUE;
    return TRUE;
}

static void update_pos(Dashboard_plugs_callbacks * node)
{
    get_component_name_fn   get_component_name;
    char * comp_name=NULL;
    GConfValue *value;
    char * keyname;
    int tmp;
                    
    get_component_name=node->lookup_fn(DASHBOARD_CALLBACK_GET_COMPONENT_NAME_FN);
    if (get_component_name)
    {
        comp_name=(char *) get_component_name(node->data);
    }            
    tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name)+strlen("_posx1")+1;
    keyname=g_malloc(tmp);
    if (keyname)
    {
        strcpy(keyname,GCONF_DASHBOARD_PREFIX);
        strcat(keyname,comp_name);
        strcat(keyname,"_posx1");
        gconf_client_set_int(get_dashboard_gconf(),keyname,node->x1, NULL );  
    }
    g_free(keyname);
    tmp = strlen(GCONF_DASHBOARD_PREFIX) + strlen(comp_name)+strlen("_posy1")+1;
    keyname=g_malloc(tmp);
    if (keyname)
    {
        strcpy(keyname,GCONF_DASHBOARD_PREFIX);
        strcat(keyname,comp_name);
        strcat(keyname,"_posy1");
        gconf_client_set_int(get_dashboard_gconf(),keyname,node->y1, NULL );  
    }
    g_free(keyname);
    
    
}

static gboolean _move_left(GtkWidget *widget, GdkEventButton *event,    
                            Dashboard_plugs_callbacks * node )
{
    if (node->x1>0)
    {
        node->x1--;
        node->x2--;
    }
    update_pos(node);
    return TRUE;    
}

static gboolean _move_right(GtkWidget *widget, GdkEventButton *event,    
                            Dashboard_plugs_callbacks * node )
{
    if (node->x2< tiles_x)
    {
        node->x1++;
        node->x2++;
    }
    update_pos(node);    
    return TRUE;
}

static gboolean _move_up(GtkWidget *widget, GdkEventButton *event,    
                            Dashboard_plugs_callbacks * node )
{
    if (node->y1>1)
    {
        node->y1--;
        node->y2--;
    }
    update_pos(node);    
    return TRUE;
}

static gboolean _move_down(GtkWidget *widget, GdkEventButton *event,    
                            Dashboard_plugs_callbacks * node )
{
    if (node->y2<tiles_y)
    {
        node->y1++;
        node->y2++;
    }
    update_pos(node);    
    return TRUE;
}


static void Dashboard_plugs_construct(gpointer data,gpointer user_data)
{
    
    Dashboard_plugs_callbacks * node=data;
    Dashboard *dashboard=user_data;
    int i,j;
    float col_width=dashboard->maintable->allocation.width/tiles_x;    
    float col_height=dashboard->maintable->allocation.height/tiles_y;    
    int xcols,yrows,over;
    GtkRequisition dims;
    GtkWidget *old_widget=NULL;
    if (!node->enabled)
        return;

    if (node->dead_but_does_not_know_it)
    {        
        gtk_widget_destroy(node->widge_wrap);
        gtk_widget_destroy(node->widget);
        _toggle_component(node);
        node->dead_but_does_not_know_it=FALSE;        
        build_dashboard_right_click(dashboard);
        return;
    }
    render_fn render=node->lookup_fn(DASHBOARD_CALLBACK_RENDER);
    if(render)
    {
        if (dashboard->need_win_update=render(&node->widget,
                                        dashboard->updateinterval,node->data 
                                        ))
        {              
            int j;
            if (node->widge_wrap)
            {         
                old_widget=node->widge_wrap;                
            }        
            else
            {
                build_dashboard_right_click(dashboard);
            }
            node->widge_wrap = gtk_event_box_new();
            gtk_event_box_set_visible_window(node->widge_wrap,FALSE);            
            gtk_container_add (GTK_CONTAINER (node->widge_wrap), node->widget);                                   
            g_signal_connect (G_OBJECT (node->widge_wrap), "button-press-event",
                            G_CALLBACK (_button_clicked_event), (gpointer)node
                            );
            
            gtk_table_attach_defaults (GTK_TABLE (dashboard->maintable), 
                                    node->widge_wrap,node->x1, node->x2,
                                    node->y1, node->y2
                                    );  
            if (old_widget)
            {
                gtk_widget_hide(old_widget);                            
                gtk_widget_destroy(old_widget);
            }               
            gtk_widget_show_all(node->widge_wrap);                                           

            gtk_widget_size_request(node->widget,&dims);            
            if (  ( dims.width!=0) && (dims.height!=0)  ) 
            {                                
                xcols=dims.width/col_width + 1;
                yrows=dims.height/col_height+1;            
                node->x2=node->x1+xcols;
                node->y2=node->y1+yrows;
            }
                        
        }      
    }
}

static void Dashboard_plugs_destruct(gpointer data,gpointer user_data)
{
    
    Dashboard_plugs_callbacks * node=data;
    Dashboard *Dashboard=user_data;
    destruct_fn destruct=node->lookup_fn(DASHBOARD_CALLBACK_DESTRUCT);
    if(destruct)
    {
        destruct(node->data );
    }      
}


static gboolean _Dashboard_time_handler (Dashboard * Dashboard)
{

    long tmp;
    static gboolean    in_handler=FALSE;    
    if (in_handler) 
    {        /*FIXME - I actually don't think glib will let this happen.*/
        return TRUE;
    }
    in_handler=TRUE;                
   
    if (GTK_WIDGET_VISIBLE(Dashboard->mainwindow))
    {
        draw_main_window(Dashboard);                
    }	
    in_handler=FALSE;
	return TRUE;
}


/************Section:  main window events-------------*/

static gboolean _button_clicked_test_event (GtkWidget *widget,
                            GdkEventButton *event,Dashboard * dashboard)
{       
	return TRUE;
}

static gboolean _visibility_notify_event(GtkWidget *widget,
                            GdkEventButton *event,Dashboard * dashboard)
{
    return TRUE;
}

static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event, 
                                Dashboard * dashboard)
{
    if (!get_suppress_hide_main() )
    {
        if (  gdk_window_get_window_type (event->window) !=GDK_WINDOW_TEMP)
        {        
            gtk_widget_hide(dashboard->mainwindow);
        }
    }
    disable_suppress_hide_main();        
    return TRUE;
}

/*

-draws the main window.
-interates though the list of dashboard plugs and they draw their widgets.

*/
static void draw_main_window(Dashboard *dashboard)
{
    /*have dashboard plugs that have registered draw their widgets*/
    dashboard->need_win_update=FALSE;    
    g_slist_foreach(dashboard->Dashboard_plugs,Dashboard_plugs_construct,dashboard);    
       
    /*we're done laying out the damn thing - let's show it*/

    awn_applet_dialog_position_reset (AWN_APPLET_DIALOG (dashboard->mainwindow));        
    if (!dashboard->need_win_update )
    {
//        dashboard->force_update=FALSE;

    }
    gtk_widget_show_all (dashboard->mainwindow);                
    set_bg_rbg(&dashboard->mainwindow->style->base[0]);
    set_fg_rbg(&dashboard->mainwindow->style->fg[0]);    
    
    GtkRequisition dims;
    gtk_widget_size_request(dashboard->maintable,&dims);            
}






