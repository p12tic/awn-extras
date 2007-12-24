/*
 * Copyright (c) 2007 Mike Desjardins
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
 
#define WNCK_I_KNOW_THIS_IS_UNSTABLE 1

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <math.h>
#include <assert.h>

#include <gdk/gdk.h>
#include <gtk/gtk.h>
#include <gdk/gdkx.h>
#include <glib.h>
#include <libwnck/libwnck.h>
#include <time.h>
#include <X11/Xlib.h>

#ifdef USE_AWN_DESKTOP_AGNOSTIC
#include <libawn/awn-config-client.h>
#else
#include <gconf/gconf-client.h>
#endif
#include "shinyswitcherapplet.h"


#define CONFIG_ROWS 	CONFIG_KEY("rows")
#define CONFIG_COLUMNS  CONFIG_KEY("columns")
#define CONFIG_WALLPAPER_ALPHA_ACTIVE 	CONFIG_KEY("background_alpha_active")
#define CONFIG_WALLPAPER_ALPHA_INACTIVE   CONFIG_KEY("background_alpha_inactive")
#define CONFIG_APPLET_SCALE   CONFIG_KEY("applet_scale")
#define CONFIG_SHOW_ICON_MODE CONFIG_KEY("show_icon_mode")
#define CONFIG_SCALE_ICON_MODE CONFIG_KEY("scale_icon_mode")
#define CONFIG_SCALE_ICON_FACTOR CONFIG_KEY("scale_icon_factor")
#define CONFIG_WIN_GRAB_MODE CONFIG_KEY("win_grab_mode")
#define CONFIG_WIN_GRAB_METHOD CONFIG_KEY("win_grab_method")
#define CONFIG_WIN_ACTIVE_ICON_ALPHA CONFIG_KEY("win_active_icon_alpha")
#define CONFIG_WIN_INACTIVE_ICON_ALPHA CONFIG_KEY("win_inactive_icon_alpha")
#define CONFIG_MOUSEWHEEL CONFIG_KEY("mousewheel")
#define CONFIG_CACHE_EXPIRY CONFIG_KEY("cache_expiry")
#define CONFIG_SCALE_ICON_POSITION CONFIG_KEY("scale_icon_position")
#define CONFIG_APPLET_BORDER_WIDTH CONFIG_KEY("applet_border_width")
#define CONFIG_APPLET_BORDER_COLOUR CONFIG_KEY("applet_border_colour")


/*
 * STATIC FUNCTION DEFINITIONS
 */
static void shiny_switcher_render (cairo_t *cr, int width, int height);
static gboolean time_handler (Shiny_switcher *shinyswitcher);

// Events
static gboolean _expose_event_window(GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _expose_event_outer(GtkWidget *widget, GdkEventExpose *expose,Shiny_switcher *shinyswitcher);
static gboolean _expose_event_border(GtkWidget *widget, GdkEventExpose *expose,Shiny_switcher *shinyswitcher);
static gboolean _button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data);
static void _height_changed (AwnApplet *app, guint height, gpointer *data);
static void _orient_changed (AwnApplet *appt, guint orient, gpointer *data);



//CONF STUFF

#ifdef USE_AWN_DESKTOP_AGNOSTIC
static void config_get_string (AwnConfigClient *client, const gchar *key, gchar **str)
{
	*str = awn_config_client_get_string (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, key, NULL);
}
static void config_get_color (AwnConfigClient *client, const gchar *key, AwnColor *color)
{
	gchar *value = awn_config_client_get_string (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, key, NULL);
	awn_cairo_string_to_color (value, color);
	g_free (value);
}
#else
static void config_get_string (GConfClient *client, const gchar *key, gchar **str)
{
	gchar *value = gconf_client_get_string (client, key, NULL);
	*str = g_strdup (value);
	g_free (value);
}
static void config_get_color (GConfClient *client, const gchar *key, AwnColor *color)
{
	GConfValue *value = gconf_client_get_string (client, key, NULL);
	awn_cairo_string_to_color (value, color);
	g_free (value);
}
#endif

void init_config(Shiny_switcher *shinyswitcher)
{
#ifdef USE_AWN_DESKTOP_AGNOSTIC
	shinyswitcher->config = awn_config_client_new_for_applet ("shinyswitcher", NULL);
#else
	shinyswitcher->config = gconf_client_get_default();
#endif

#ifdef USE_AWN_DESKTOP_AGNOSTIC
	shinyswitcher->rows			= 	awn_config_client_get_int(shinyswitcher->config,AWN_CONFIG_CLIENT_DEFAULT_GROUP,
																CONFIG_ROWS,NULL);
	shinyswitcher->cols			=	awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_COLUMNS,     NULL);
	shinyswitcher->wallpaper_alpha_active  =	awn_config_client_get_float(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_WALLPAPER_ALPHA_ACTIVE,     NULL);
	shinyswitcher->wallpaper_alpha_inactive=	awn_config_client_get_float(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_WALLPAPER_ALPHA_INACTIVE,     NULL);	 
	shinyswitcher->applet_scale=	awn_config_client_get_float(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_APPLET_SCALE,     NULL);	 
						 										
	shinyswitcher->scale_icon_mode=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_SCALE_ICON_MODE,     NULL);
	shinyswitcher->scale_icon_factor=awn_config_client_get_float(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_SCALE_ICON_FACTOR,     NULL);	 
	shinyswitcher->show_icon_mode=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_SHOW_ICON_MODE,     NULL);
	shinyswitcher->win_grab_mode=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_WIN_GRAB_MODE ,     NULL);
	shinyswitcher->win_grab_method=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_WIN_GRAB_METHOD,     NULL);
	shinyswitcher->win_active_icon_alpha=awn_config_client_get_float(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_WIN_ACTIVE_ICON_ALPHA,     NULL);	 
	shinyswitcher->win_inactive_icon_alpha=awn_config_client_get_float(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_WIN_INACTIVE_ICON_ALPHA ,     NULL);	 
	shinyswitcher->mousewheel=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										CONFIG_MOUSEWHEEL  ,NULL);
	shinyswitcher->cache_expiry=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										 CONFIG_CACHE_EXPIRY,   NULL); 
	shinyswitcher->scale_icon_pos=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
						 										 CONFIG_SCALE_ICON_POSITION ,   NULL);  
	shinyswitcher->applet_border_width=awn_config_client_get_int(shinyswitcher->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
																CONFIG_APPLET_BORDER_WIDTH ,   NULL); 						 
#else
	shinyswitcher->rows              	= gconf_client_get_int   (shinyswitcher->config, CONFIG_ROWS,  NULL);
	shinyswitcher->cols                 = gconf_client_get_int   (shinyswitcher->config, CONFIG_COLUMNS,     NULL);
	shinyswitcher->wallpaper_alpha_active	= gconf_client_get_float(shinyswitcher->config,CONFIG_WALLPAPER_ALPHA_ACTIVE,  NULL);
	shinyswitcher->wallpaper_alpha_inactive = gconf_client_get_float(shinyswitcher->config, CONFIG_WALLPAPER_ALPHA_INACTIVE, NULL);
	shinyswitcher->applet_scale = gconf_client_get_float(shinyswitcher->config, CONFIG_APPLET_SCALE, NULL);	
	shinyswitcher->scale_icon_mode=gconf_client_get_int   (shinyswitcher->config, CONFIG_SCALE_ICON_MODE,     NULL);
	shinyswitcher->scale_icon_factor=gconf_client_get_float(shinyswitcher->config,CONFIG_SCALE_ICON_FACTOR,     NULL);	 
	shinyswitcher->show_icon_mode=gconf_client_get_int   (shinyswitcher->config, CONFIG_SHOW_ICON_MODE,     NULL);
	shinyswitcher->win_grab_mode=gconf_client_get_int   (shinyswitcher->config, CONFIG_WIN_GRAB_MODE ,     NULL);
	shinyswitcher->win_grab_method=gconf_client_get_int   (shinyswitcher->config, CONFIG_WIN_GRAB_METHOD,     NULL);
	shinyswitcher->win_active_icon_alpha=gconf_client_get_float(shinyswitcher->config,CONFIG_WIN_ACTIVE_ICON_ALPHA,     NULL);	 
	shinyswitcher->win_inactive_icon_alpha=gconf_client_get_float(shinyswitcher->config,CONFIG_WIN_INACTIVE_ICON_ALPHA ,     NULL);	 
	shinyswitcher->mousewheel=gconf_client_get_int   (shinyswitcher->config, CONFIG_MOUSEWHEEL  ,NULL);
	shinyswitcher->cache_expiry=gconf_client_get_int   (shinyswitcher->config, CONFIG_CACHE_EXPIRY,   NULL); 
	shinyswitcher->scale_icon_pos=gconf_client_get_int   (shinyswitcher->config, CONFIG_SCALE_ICON_POSITION ,   NULL); 
	shinyswitcher->applet_border_width=gconf_client_get_int   (shinyswitcher->config, CONFIG_APPLET_BORDER_WIDTH ,   NULL); 
#endif

	config_get_color(shinyswitcher->config,CONFIG_APPLET_BORDER_COLOUR,&shinyswitcher->applet_border_colour);						
	
	shinyswitcher->active_window_on_workspace_change_method=1;
	shinyswitcher->do_queue_freq=2;
	shinyswitcher->override_composite_check=FALSE;
	shinyswitcher->show_tooltips=FALSE;						//buggy at the moment will be a config option eventually
	
	shinyswitcher->show_right_click=!shinyswitcher->got_viewport;	//for the moment buggy in compiz.will be a config option eventually

	shinyswitcher->reconfigure=!shinyswitcher->got_viewport;		//for the moment... will be a config option eventually
//	AwnColor		background_colour;
	

		
#ifdef USE_AWN_DESKTOP_AGNOSTIC

#else
	
#endif	
}

#ifdef USE_AWN_DESKTOP_AGNOSTIC

static void save_config(Shiny_switcher *shinyswitcher)
{

}

#else

static void save_config(Shiny_switcher *shinyswitcher)
{
	gchar * svalue;

    gconf_client_set_int   (shinyswitcher->config, CONFIG_ROWS,shinyswitcher->rows ,NULL);        
	gconf_client_set_int   (shinyswitcher->config, CONFIG_COLUMNS,shinyswitcher->cols,NULL);    	
}

#endif



double vp_vscale(Shiny_switcher *shinyswitcher)
{
	return  (double)wnck_screen_get_height(shinyswitcher->wnck_screen )/(double)wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );

}

double vp_hscale(Shiny_switcher *shinyswitcher)
{
	return  (double)wnck_screen_get_width(shinyswitcher->wnck_screen )/(double)wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );

}


void calc_dimensions(Shiny_switcher *shinyswitcher)
{

//	wnck_screen_force_update(shinyswitcher->wnck_screen);  		
//FIXME this is no longer screen width/height  it's workspace
	int wnck_ws_width=wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );	
	int wnck_ws_height=wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );
	int wnck_scr_width=wnck_screen_get_width(shinyswitcher->wnck_screen );	
	int wnck_scr_height=wnck_screen_get_height(shinyswitcher->wnck_screen );

	double ws_ratio,scr_ratio;	
	
	ws_ratio=wnck_ws_width/ (double)wnck_ws_height;
	scr_ratio=wnck_scr_width/ (double)wnck_scr_height;

	printf("cols = %d,  rows=%d \n",shinyswitcher->cols,shinyswitcher->rows);		
	shinyswitcher->mini_work_height=shinyswitcher->height*shinyswitcher->applet_scale/shinyswitcher->rows;
	shinyswitcher->mini_work_width=shinyswitcher->mini_work_height*shinyswitcher->applet_scale*scr_ratio*
									(double)wnck_ws_width/(double)wnck_scr_width*vp_vscale(shinyswitcher);
	shinyswitcher->width=shinyswitcher->mini_work_width*shinyswitcher->cols;
}


GdkPixmap * copy_pixmap(Shiny_switcher *shinyswitcher,GdkPixmap * src)
{
    GdkScreen* pScreen;    
	GdkColormap*	cmap;    	
	GdkPixmap * copy;
	int		w,h;

	gdk_drawable_get_size(src,&w,&h);
	copy=gdk_pixmap_new(NULL,w,h,32);   //FIXME
	
    GtkWidget *widget=gtk_image_new_from_pixmap(copy,NULL);            
    pScreen = gtk_widget_get_screen ( shinyswitcher->applet   );
 	gdk_drawable_set_colormap(copy,gdk_screen_get_rgba_colormap (pScreen));

    cairo_t * destcr=gdk_cairo_create(copy);	

	gdk_cairo_set_source_pixmap(destcr,src,0,0);    
    cairo_set_operator (destcr, CAIRO_OPERATOR_SOURCE);
	cairo_paint(destcr);
	gtk_widget_destroy(widget);
	cairo_destroy(destcr);
	return copy;
}

//grabs the wallpaper as a gdkpixmap.
//FIXME	This needs a cleanup
void grab_wallpaper(Shiny_switcher *shinyswitcher)
{
	int w,h;
    GdkScreen* pScreen;    
	GdkColormap*	cmap;    	
	GtkWidget	*	widget;
    pScreen = gtk_widget_get_screen ( shinyswitcher->applet   );
	gulong wallpaper_xid=wnck_screen_get_background_pixmap(shinyswitcher->wnck_screen);
	GdkPixmap* wallpaper=gdk_pixmap_foreign_new (wallpaper_xid); 	
 	gdk_drawable_set_colormap(wallpaper,gdk_screen_get_rgb_colormap (pScreen));
	
    shinyswitcher->wallpaper_inactive=gdk_pixmap_new(NULL,shinyswitcher->mini_work_width*vp_hscale(shinyswitcher),shinyswitcher->mini_work_height*vp_vscale(shinyswitcher),32);   //FIXME
    widget=gtk_image_new_from_pixmap(shinyswitcher->wallpaper_inactive,NULL);  
 	gtk_widget_set_app_paintable(widget,TRUE);	          
    cmap = gdk_screen_get_rgba_colormap (pScreen);
    gdk_drawable_set_colormap(shinyswitcher->wallpaper_inactive,cmap);       
    cairo_t * destcr=gdk_cairo_create(shinyswitcher->wallpaper_inactive);	
    cairo_set_operator (destcr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(destcr);
	gdk_drawable_get_size(wallpaper,&w,&h);
	cairo_scale(destcr,shinyswitcher->mini_work_width/(double)w*vp_hscale(shinyswitcher),shinyswitcher->mini_work_height/(double)h*vp_vscale(shinyswitcher));
	gdk_cairo_set_source_pixmap(destcr,wallpaper,0, 0);    
	cairo_set_operator (destcr, CAIRO_OPERATOR_OVER);		
	cairo_paint_with_alpha(destcr,shinyswitcher->wallpaper_alpha_inactive);	
//	g_object_ref(shinyswitcher->wallpaper_alpha_inactive);
	gtk_widget_destroy(widget);

    shinyswitcher->wallpaper_active=gdk_pixmap_new(NULL,shinyswitcher->mini_work_width*vp_hscale(shinyswitcher),shinyswitcher->mini_work_height*vp_vscale(shinyswitcher),32);   //FIXME
    widget=gtk_image_new_from_pixmap(shinyswitcher->wallpaper_active,NULL);  
 	gtk_widget_set_app_paintable(widget,TRUE);	                    
//    cmap = gdk_screen_get_rgba_colormap (pScreen);
    gdk_drawable_set_colormap(shinyswitcher->wallpaper_active,cmap);       
    destcr=gdk_cairo_create(shinyswitcher->wallpaper_active);	
    cairo_set_operator (destcr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(destcr);
	cairo_scale(destcr,shinyswitcher->mini_work_width/(double)w*vp_hscale(shinyswitcher),shinyswitcher->mini_work_height/(double)h*vp_vscale(shinyswitcher));
	gdk_cairo_set_source_pixmap(destcr,wallpaper,0, 0);    
	cairo_set_operator (destcr, CAIRO_OPERATOR_OVER);		
	cairo_paint_with_alpha(destcr,shinyswitcher->wallpaper_alpha_active);	
//	g_object_ref(shinyswitcher->wallpaper_alpha_active);
	gtk_widget_destroy(widget);
	cairo_destroy(destcr);

}

gboolean  _button_workspace(GtkWidget *widget,GdkEventButton *event,Workplace_info	* ws)
{

	Shiny_switcher *shinyswitcher=ws->shinyswitcher;
//	printf("Button press: %lf,%lf\n",event->x,event->y);
	if (shinyswitcher->got_viewport)
	{	
		int vp_pos_col= 1.0/vp_hscale(shinyswitcher)*(event->x/(double)shinyswitcher->mini_work_width);
		int vp_pos_row= 1.0/vp_vscale(shinyswitcher)*(event->y/(double)shinyswitcher->mini_work_height);
		wnck_screen_move_viewport(shinyswitcher->wnck_screen,
				vp_pos_col*wnck_screen_get_width(shinyswitcher->wnck_screen ),
				vp_pos_row*wnck_screen_get_height(shinyswitcher->wnck_screen ));
	}
	wnck_workspace_activate(ws->space,time(NULL));
	return FALSE;
}

gboolean  _button_win(GtkWidget *widget,GdkEventButton *event,Win_press_data * data)
{
	WnckWindow*  wnck_win=data->wnck_window;
	printf("button click\n");	
	if (event->button == 1)
    {	
		WnckWorkspace* space=wnck_window_get_workspace(wnck_win);
		if (space)
		{
//			if (space !=wnck_screen_get_active_workspace(data->shinyswitcher->wnck_screen))
			{
				wnck_workspace_activate(space,time(NULL));	
				wnck_window_activate(wnck_win,time(NULL));
			}		
			return TRUE;		
		}
	}
	else if (event->button == 3)
	{				
		if (data->shinyswitcher->show_right_click)		
		{
			GtkWidget * menu=g_tree_lookup(data->shinyswitcher->win_menus,wnck_win);
			if (menu)
				gtk_menu_popup (menu, NULL, NULL, NULL, NULL,event->button, event->time);	
		}			
		return TRUE;			  					  			
	}
	return FALSE;			
}


static gboolean _scroll_event(GtkWidget *widget,GdkEventMotion *event,Shiny_switcher *shinyswitcher) 
{
	WnckWorkspace *cur_space=wnck_screen_get_active_workspace(shinyswitcher->wnck_screen);
	WnckWorkspace *new_space;
	if (cur_space)
	{
		if (event->type == GDK_SCROLL)
		{
			WnckMotionDirection direction1, direction2;
			switch(shinyswitcher->mousewheel)
			{
				case 1:
				case 3:
					direction1=  WNCK_MOTION_LEFT;
					direction2=  WNCK_MOTION_RIGHT;				
					break;
				case 2:
				case 4:
				default:
					direction1=  WNCK_MOTION_RIGHT;				
					direction2=  WNCK_MOTION_LEFT;				

			}

		 	if (event->state & GDK_SHIFT_MASK)
			{
				new_space=wnck_workspace_get_neighbor(cur_space,WNCK_MOTION_RIGHT);
			}
			else
			{
				new_space=wnck_workspace_get_neighbor(cur_space,WNCK_MOTION_LEFT);	
						
			}
		}
		if (new_space)
		{
		   wnck_workspace_activate(new_space,time(NULL) ); //FIXME
		}
	}		
	return TRUE;
}		

void create_containers(Shiny_switcher *shinyswitcher)
{
	int 	num_workspaces=shinyswitcher->rows*shinyswitcher->cols;
	int		x,y;
	GList* 	wnck_spaces;
	GList * iter;
	int		win_num;
	GtkFixed	*new_mini;
    GdkScreen* pScreen;    
	GdkColormap*	cmap;    
	cairo_t		*cr;
	int 		y_offset,x_offset;
	
	shinyswitcher->mini_wins=g_malloc(sizeof(GtkWidget*)*num_workspaces);	
	shinyswitcher->container=gtk_fixed_new();	
 	gtk_widget_set_app_paintable(shinyswitcher->container,TRUE);				

    GdkPixmap *border=gdk_pixmap_new(NULL,
    						shinyswitcher->width+shinyswitcher->width+shinyswitcher->applet_border_width *2,
    						(shinyswitcher->height+shinyswitcher->applet_border_width *2)*shinyswitcher->applet_scale,
    						32);   //FIXME
    GtkWidget *border_widget=gtk_image_new_from_pixmap(border,NULL);  
 	gtk_widget_set_app_paintable(border_widget,TRUE);	        
    pScreen = gtk_widget_get_screen ( shinyswitcher->applet   ); 	  
    cmap = gdk_screen_get_rgba_colormap (pScreen);
    gdk_drawable_set_colormap(border,cmap);       
    cr=gdk_cairo_create(border);		
    cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
	cairo_paint(cr);        	
    cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);	
	cairo_set_source_rgba (cr,shinyswitcher->applet_border_colour.red, shinyswitcher->applet_border_colour.green,
							shinyswitcher->applet_border_colour.blue, shinyswitcher->applet_border_colour.alpha);
	
	cairo_paint(cr);        		
	cairo_destroy(cr);
	g_object_unref(border);

	y_offset=(shinyswitcher->height - (shinyswitcher->mini_work_height * shinyswitcher->rows)) /2;

	gtk_fixed_put(GTK_CONTAINER(shinyswitcher->container),border_widget,0,shinyswitcher->height+y_offset);	
	y_offset=y_offset+shinyswitcher->applet_border_width;	
	x_offset=shinyswitcher->applet_border_width;	
//				shinyswitcher->mini_work_height*shinyswitcher->rows*((1.0-shinyswitcher->applet_scale)/2.0)
	wnck_spaces=wnck_screen_get_workspaces(shinyswitcher->wnck_screen);			
	for(iter=g_list_first(wnck_spaces);iter;iter=g_list_next(iter) )
	{
		GtkWidget * background;
		GtkWidget * ev;
		Workplace_info	* ws;				
		win_num=wnck_workspace_get_number(iter->data);				
		shinyswitcher->mini_wins[win_num]=gtk_fixed_new();
	 	gtk_widget_set_app_paintable(shinyswitcher->mini_wins[win_num],TRUE);
//		gtk_fixed_set_has_window(shinyswitcher->mini_wins[win_num],TRUE);

//		gtk_event_box_set_visible_window(ev,FALSE);		
		GdkPixmap	*copy;


		if (shinyswitcher->got_viewport)
		{	
			int	viewports_cols;
			int viewports_rows;
			int x,y;
			int i,j;
			GtkWidget 	*vp_bg;
			viewports_cols=wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) ) /
									wnck_screen_get_width(shinyswitcher->wnck_screen ) ;
			viewports_rows=wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) ) /
									wnck_screen_get_height(shinyswitcher->wnck_screen ) ;											
			ev=gtk_event_box_new();				
		 	gtk_widget_set_app_paintable(ev,TRUE);
			if (iter->data==wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) )
			{
				copy=shinyswitcher->wallpaper_active;		
			}
			else
			{
				copy=shinyswitcher->wallpaper_inactive;
			}			
			copy=copy_pixmap(shinyswitcher,copy);
	//		copy=gdk_pixmap_new(shinyswitcher->wallpaper_inactive,shinyswitcher->mini_work_width,shinyswitcher->mini_work_height,-1);		
			gtk_container_add (ev,gtk_image_new_from_pixmap(copy,NULL));
			g_object_unref(copy);
				
			
		}
		else
		{
			ev=gtk_event_box_new();		
		 	gtk_widget_set_app_paintable(ev,TRUE);
			if (iter->data==wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) )
			{
				copy=shinyswitcher->wallpaper_active;		
			}
			else
			{
				copy=shinyswitcher->wallpaper_inactive;
			}			
			copy=copy_pixmap(shinyswitcher,copy);
	//		copy=gdk_pixmap_new(shinyswitcher->wallpaper_inactive,shinyswitcher->mini_work_width,shinyswitcher->mini_work_height,-1);		
			gtk_container_add (ev,gtk_image_new_from_pixmap(copy,NULL));
			g_object_unref(copy);
		}			
		gtk_fixed_put(GTK_CONTAINER (shinyswitcher->mini_wins[win_num]),ev,0,0);
		
   		gtk_fixed_put(GTK_FIXED(shinyswitcher->container),shinyswitcher->mini_wins[win_num],
   								shinyswitcher->mini_work_width*wnck_workspace_get_layout_column(iter->data)+x_offset,
   								shinyswitcher->mini_work_height*wnck_workspace_get_layout_row(iter->data)+shinyswitcher->height
   								+y_offset );   								
		ws=g_malloc(sizeof(Workplace_info) );
		ws->shinyswitcher=shinyswitcher;
		ws->space=iter->data;
		ws->wallpaper_ev=ev;
		ws->mini_win_index=win_num;
		ws->event_boxes=NULL;
		g_tree_insert(shinyswitcher->ws_lookup_ev,iter->data,ws);
		g_signal_connect(G_OBJECT(ev),"button-press-event",G_CALLBACK (_button_workspace),ws);
		g_signal_connect (G_OBJECT (ev), "expose_event",G_CALLBACK (_expose_event_window), shinyswitcher);
		g_signal_connect (G_OBJECT (shinyswitcher->mini_wins[win_num] ), "expose_event",G_CALLBACK (_expose_event_window), NULL);			
	}	
	gtk_container_add (GTK_CONTAINER (shinyswitcher->applet),shinyswitcher->container);    		    	
	g_signal_connect(GTK_WIDGET(shinyswitcher->applet), "scroll-event" , G_CALLBACK (_scroll_event),shinyswitcher);			
}



gint _cmp_ptrs(gconstpointer a,gconstpointer b)
{
	return a-b;
}


void prepare_to_render_workspace(Shiny_switcher *shinyswitcher, WnckWorkspace * space)
{

	GdkPixmap *	copy;
	Workplace_info	* ws2;
	ws2=g_tree_lookup(shinyswitcher->ws_lookup_ev,space);	
	assert(ws2);
	GdkGC * gdkgc=NULL;

	if (!gdkgc)
	{
		gdkgc=gdk_gc_new(shinyswitcher->wallpaper_active);			
	}		
	if (shinyswitcher->got_viewport)
	{
/*		if (  wnck_screen_get_active_workspace(shinyswitcher->wnck_screen)==space)	
		{
			copy=copy_pixmap(shinyswitcher,shinyswitcher->wallpaper_active);
		}
		else
		{
			copy=copy_pixmap(shinyswitcher,shinyswitcher->wallpaper_inactive);	
		}		*/
		int	viewports_cols;
		int viewports_rows;
		int x,y;
		int i,j;
		GtkWidget 	*vp_bg;
		viewports_cols=wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) ) /
								wnck_screen_get_width(shinyswitcher->wnck_screen ) ;
		viewports_rows=wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) ) /
								wnck_screen_get_height(shinyswitcher->wnck_screen ) ;	
								
		copy=gdk_pixmap_new(NULL,shinyswitcher->mini_work_width,shinyswitcher->mini_work_height,32);
	    GdkScreen* pScreen;    
		GdkColormap*	cmap;    	
	
    	pScreen = gtk_widget_get_screen ( shinyswitcher->applet   );
 		gdk_drawable_set_colormap(copy,gdk_screen_get_rgba_colormap (pScreen));		
		
		gdk_draw_rectangle(copy,gdkgc,TRUE,0,0,shinyswitcher->mini_work_width,shinyswitcher->mini_work_height);		
		int vp_active_x=1.0/vp_hscale(shinyswitcher)*
						wnck_workspace_get_viewport_x(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen))/
						wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) )
						;
		
		int vp_active_y=1.0/vp_vscale(shinyswitcher)*
						wnck_workspace_get_viewport_y(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen))/
						wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) ) ;
	//	printf("Looking for: %d,%d\n",vp_active_x,vp_active_y);
		for(i=0;i<viewports_rows;i++)
		{
														
// wnck_workspace_get_viewport_x       (WnckWorkspace *space);			
//wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );
//int wnck_scr_width=wnck_screen_get_width(shinyswitcher->wnck_screen );			
			for(j=0;j<viewports_cols;j++)
			{
			   GdkPixmap * to_copy;
			   to_copy=((i==vp_active_y)&&(j==vp_active_x))?shinyswitcher->wallpaper_active:shinyswitcher->wallpaper_inactive;
			   gdk_draw_drawable(copy,gdkgc,to_copy,0,0,
											j*shinyswitcher->mini_work_width*vp_hscale(shinyswitcher),
											i*shinyswitcher->mini_work_height*vp_vscale(shinyswitcher),
                                            -1,-1);
			}
		}			
	}
	else
	{	
		if (  wnck_screen_get_active_workspace(shinyswitcher->wnck_screen)==space)	
		{
			copy=copy_pixmap(shinyswitcher,shinyswitcher->wallpaper_active);
		}
		else
		{
			copy=copy_pixmap(shinyswitcher,shinyswitcher->wallpaper_inactive);	
		}		
	}		
	if (copy)
	{	
		GtkWidget *new_pixmap;		
	
//			gtk_container_remove(ws2->wallpaper_ev,gtk_bin_get_child(ws2->wallpaper_ev));	
		gtk_widget_destroy( gtk_bin_get_child(ws2->wallpaper_ev));
		new_pixmap=gtk_image_new_from_pixmap(copy,NULL);
	 	gtk_widget_set_app_paintable(new_pixmap,TRUE);		
		gtk_container_add(ws2->wallpaper_ev,new_pixmap);	
		g_object_unref(copy);
		gtk_widget_show_all(ws2->wallpaper_ev);	
	}
	if (ws2->event_boxes)
	{
		GList * ev_iter;
		for(ev_iter=g_list_first(ws2->event_boxes);ev_iter;ev_iter=g_list_next(ev_iter) )
		{
			gtk_widget_hide(ev_iter->data);	
			gtk_widget_destroy(ev_iter->data);
		}
		g_list_free(ws2->event_boxes);
		ws2->event_boxes=NULL;					
	}
}

void image_cache_insert_pixbuf(GTree*  cache, gpointer key,  GdkPixbuf * pbuf)
{
	int w,h;
	Image_cache_item * leaf;
	assert( !g_tree_lookup(cache,pbuf) );
	leaf=g_malloc(sizeof(Image_cache_item) );
	h=gdk_pixbuf_get_height(pbuf);
	w=gdk_pixbuf_get_width(pbuf);
	leaf->data=pbuf;
	leaf->width=w;
	leaf->height=h;
	leaf->time_stamp=time(NULL);
	leaf->img_type=IMAGE_CACHE_PIXBUF;
	g_tree_insert(cache,key,leaf);		

}


void image_cache_insert_surface(GTree*  cache, gpointer key,  cairo_surface_t *surface)
{
	int w,h;
	Image_cache_item * leaf;
	assert( !g_tree_lookup(cache,surface) );
	leaf=g_malloc(sizeof(Image_cache_item) );

	h=cairo_image_surface_get_height(surface);
	w=cairo_image_surface_get_width(surface);
	leaf->data=surface;
	leaf->width=w;
	leaf->height=h;
	leaf->time_stamp=time(NULL);
	leaf->img_type=IMAGE_CACHE_SURFACE;
	g_tree_insert(cache,key,leaf);		

}

void image_cache_unref_data(Image_cache_item * leaf)
{
	switch (leaf->img_type)
	{
		case IMAGE_CACHE_SURFACE:
			cairo_surface_destroy(leaf->data);
			break;
		case IMAGE_CACHE_PIXBUF:
		default:
			g_object_unref(G_OBJECT(leaf->data));
			break;
	}		
}

gpointer image_cache_lookup_key_width_height(Shiny_switcher *shinyswitcher,GTree*  cache, 
											gpointer key,gint width, gint height,gboolean allow_time_expire)
{	
	Image_cache_item * leaf;
	leaf=g_tree_lookup(cache,key);
	if (leaf)
	{
		if ( (leaf->height==height)  && (leaf->width==width)  )
		{
			if ((  time(NULL)-shinyswitcher->cache_expiry  < leaf->time_stamp)|| !allow_time_expire)
			{
				return leaf->data;
			}				
		}
		else
		{

		}
		//if the leaf cached drawable is not a perfect match we get rid of it...
		image_cache_unref_data(leaf);
		g_tree_remove(cache,key);
		g_free(leaf);		
	}
	return NULL;					
}

void image_cache_remove(GTree*  cache, gpointer key)
{
	Image_cache_item * leaf;
	leaf=g_tree_lookup(cache,key);
	if (leaf)
	{
		image_cache_unref_data(leaf);
		g_tree_remove(cache,key);
		g_free(leaf);		
	}
}

void image_cache_expire(Shiny_switcher *shinyswitcher,GTree*  cache, gpointer key)
{
	Image_cache_item * leaf;
	leaf=g_tree_lookup(cache,key);
	if (leaf)
	{
		leaf->time_stamp=leaf->time_stamp-shinyswitcher->cache_expiry;
	}
}

void grab_window_xrender_meth(Shiny_switcher *shinyswitcher,cairo_t *destcr,WnckWindow *win,double scaled_x,double scaled_y, 
						double scaled_width,double scaled_height,int x, int y, int width,int height,gboolean allow_update)
{
	int event_base, error_base;
	gboolean  hasNamePixmap = FALSE;
	
	Display* dpy=gdk_x11_get_default_xdisplay();

	if ( XCompositeQueryExtension( dpy, &event_base, &error_base ) )
	{
		// If we get here the server supports the extension

		int major = 0, minor = 2; // The highest version we support
		XCompositeQueryVersion( dpy, &major, &minor );	

		// major and minor will now contain the highest version the server supports.
		// The protocol specifies that the returned version will never be higher
		// then the one requested. Version 0.2 is the first version to have the
		// XCompositeNameWindowPixmap() request.
		if ( major > 0 || minor >= 2 )
			hasNamePixmap = TRUE;
	}
	XWindowAttributes attr;
//	if ( XGetWindowAttributes( dpy, wId, &attr ) )
	{
	
	
	
	}
	
}	

void grab_window_gdk_meth(Shiny_switcher *shinyswitcher,cairo_t *destcr,WnckWindow *win,double scaled_x,double scaled_y, 
						double scaled_width,double scaled_height,int x, int y, int width,int height,gboolean allow_update)
{
	int 			w,h;
	GdkScreen		*pScreen;    
	GdkColormap		*cmap; 
//	printf("BEGIN:    	grab_window_gdk_meth\n");
	
	gint 			err_code;
	cairo_surface_t* cached_srfc=NULL;
	cairo_surface_t* srfc=NULL;	
	cairo_t			*cr;	
	cached_srfc=image_cache_lookup_key_width_height(shinyswitcher,shinyswitcher->surface_cache,win,scaled_width,scaled_height,allow_update);
//	printf("xid=%ld\n",Xid);
	if (cached_srfc)
	{
//		printf("Surface cache HIT\n");
	}
	else if(allow_update)
	{
//		printf("Surface cache MISS\n");
		gulong 			Xid=wnck_window_get_xid(win );
		gdk_error_trap_push ();
		pScreen = gtk_widget_get_screen( GTK_WIDGET(shinyswitcher->applet));
		GdkPixmap * pmap=gdk_pixmap_foreign_new(Xid);	
		if (!pmap)
		{
			//ok... our window is no longer here.  we can bail safely.
			printf("Shinyswitcher Message: window gone!.  bailing oout of grab_window_gdk_meth\n");		
			goto error_out;
		}
		if (!GDK_IS_PIXMAP(pmap))
		{
			printf("Shinyswitcher Message: not a gdkpixmap!.  bailing oout of grab_window_gdk_meth\n");
			g_object_unref(pmap);
			goto error_out;
		}
		/*FIXME... suspecing that we have a race that causes occasional crash. this is to minimize chance	of this happening*/

		gdk_drawable_get_size(pmap,&w,&h);							
		if ( (h<5) || (w<5) )
		{
			printf("Shinyswitcher Message: pixmpap too small or non-existent.  bailing oout of grab_window_gdk_meth\n");
			g_object_unref(pmap);
			goto error_out;
		}
		assert(pmap);							
		if ( gdk_drawable_get_depth (pmap)==32)
		{
			cmap = gdk_screen_get_rgba_colormap (pScreen);
		}
		else if(gdk_drawable_get_depth (pmap)>=15) 
		{
			cmap = gdk_screen_get_rgb_colormap (pScreen);
		}
		else
		{
			printf("Shinyswitcher Message: dunno what's up with the pixmaps depth.  bailing oout of grab_window_gdk_meth\n");
			g_object_unref(pmap);
			goto error_out;
		}
	
		gdk_drawable_set_colormap(pmap,cmap); 
		//adjusting for the fact the pixmap does not have the wm frame...  
		double cairo_scaling_y=scaled_height / (double)h;
		double cairo_scaling_x=scaled_width  / (double)w;						    

		srfc=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,width,height);
		cairo_t *src=cairo_create(srfc);					
		cairo_set_operator(src, CAIRO_OPERATOR_SOURCE);	  					
		gdk_cairo_set_source_pixmap(src,pmap,(width-w)/2.0,(height-h)/2.0);
		cairo_rectangle(src,(width-w)/2.0,(height-h)/2.0,w,h);							
		cairo_fill(src);
		cairo_destroy(src);
		
		cached_srfc=cairo_image_surface_create(CAIRO_FORMAT_ARGB32,scaled_width,scaled_height);	
		cr=cairo_create(cached_srfc);
		cairo_scale(cr,cairo_scaling_x,cairo_scaling_y);
		cairo_set_source_surface (cr,srfc, 0, 0);
		cairo_set_operator(cr, CAIRO_OPERATOR_OVER);
		cairo_rectangle(cr,0,0,width,height);							
		cairo_fill(cr);

		cairo_destroy(cr);		
		g_object_unref(pmap);		
		image_cache_insert_surface(shinyswitcher->surface_cache,win,cached_srfc);
		cairo_surface_destroy(srfc);				
	}
	else
	{
		return;	//we  got nothing...
	}

	cairo_set_source_surface (destcr,cached_srfc, scaled_x, scaled_y);
	cairo_set_operator(destcr, CAIRO_OPERATOR_OVER);
	cairo_rectangle(destcr,scaled_x,scaled_y,scaled_width,scaled_height);							
	cairo_fill(destcr);
	
	return;	
//	cairo_surface_destroy(cached_srfc);				
	
error_out:
//	gdk_flush();
	err_code=gdk_error_trap_pop ();	
	if (err_code)
	{
		printf("Shinyswitcher Message:  A (trapped) X error occured in grab_window_gdk_meth: %d\n",err_code);
	}
}								

void do_win_grabs(Shiny_switcher *shinyswitcher,cairo_t *destcr,WnckWindow *win,double scaled_x,double scaled_y, 
						double scaled_width,double scaled_height,int x, int y, int width,int height,gboolean on_active_space)
{						
	//Do we grab the window in this particular circumstance?
	if ( ( shinyswitcher->win_grab_mode==1) || ( (shinyswitcher->win_grab_mode==2) &&  on_active_space) 
		|| ( (shinyswitcher->win_grab_mode==3) && wnck_window_is_active (win))){
		/*window grab method 0... on xfwm only works for active space unless win sticky - so specified behaviour 
		in mode may be overriden.  FIXME  cache pixmaps for inactive workspaces.
		*/
		switch(shinyswitcher->win_grab_method)
		{
			case	0:									
//				if ( on_active_space || wnck_window_is_pinned(win))
				{
					grab_window_gdk_meth(shinyswitcher,destcr,win,scaled_x,scaled_y,
									scaled_width,scaled_height,x,y,width,height,
									on_active_space || wnck_window_is_pinned(win));
				}
				break;
			default:
				printf("INVALID CONFIG OPTION: window grab method\n");
				break;
		}								
	}
}


void do_icon_overlays(Shiny_switcher *shinyswitcher,cairo_t *destcr,WnckWindow *win,double scaled_x,double scaled_y, 
						double scaled_width,double scaled_height,int x, int y, int width,int height,gboolean on_active_space)
{						
	double scale=scaled_width>scaled_height?scaled_height:scaled_width;						
	if( ( (shinyswitcher->show_icon_mode==1) && !on_active_space) ||(  (shinyswitcher->show_icon_mode==2) && !wnck_window_is_active (win) )
		||   (shinyswitcher->show_icon_mode==3) )							
	{			
		GdkPixbuf *pbuf=NULL;						
		double	icon_scaling=1.0;
		if ((shinyswitcher->scale_icon_mode==3)||( wnck_window_is_active (win) && (shinyswitcher->scale_icon_mode==2))
			||(on_active_space && (shinyswitcher->scale_icon_mode==1)))								
		{
			icon_scaling=shinyswitcher->scale_icon_factor;
		}								

		if ( scale*icon_scaling <1.2)
		{
			return;
		}					
		
		pbuf=image_cache_lookup_key_width_height(shinyswitcher,shinyswitcher->pixbuf_cache,win,scale*icon_scaling,scale*icon_scaling,TRUE);
		if (!pbuf)
		{		
			pbuf=wnck_window_get_icon(win);
			assert(pbuf);
			if ( !GDK_IS_PIXBUF (pbuf) )
			{
				pbuf=wnck_window_get_mini_icon(win);
			}
			if ( !GDK_IS_PIXBUF (pbuf) )
			{
				pbuf=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,scaled_width,scaled_height);
				gdk_pixbuf_fill(pbuf,0x00A00022); 
				printf("Bad pixbuf \n"); 
			}			
			pbuf=gdk_pixbuf_scale_simple(pbuf,scale*icon_scaling,scale*icon_scaling,GDK_INTERP_BILINEAR); 
			image_cache_insert_pixbuf(shinyswitcher->pixbuf_cache,win,pbuf);
		}			

		cairo_set_operator (destcr, CAIRO_OPERATOR_OVER);	   				
							

		double alpha=1.0;
		if (icon_scaling>0.999)
		{
			gdk_cairo_set_source_pixbuf(destcr,pbuf,scaled_x+(scaled_width-scale)/2.0,scaled_y+(scaled_height-scale)/2.0); 		
			cairo_rectangle(destcr,scaled_x+(scaled_width-scale)/2.0,scaled_y+(scaled_height-scale)/2.0,scale,scale);	
		}
		else
		{
			
			switch (shinyswitcher->scale_icon_pos)
			{
				case NW:
					gdk_cairo_set_source_pixbuf(destcr,pbuf,scaled_x,scaled_y);   		
					cairo_rectangle(destcr,scaled_x,scaled_y,scale*icon_scaling,scale*icon_scaling);			
					break;
				case NE:
					gdk_cairo_set_source_pixbuf(destcr,pbuf,scaled_x+scaled_width-scale*icon_scaling,scaled_y);   		
					cairo_rectangle(destcr,scaled_x+scaled_width-scale*icon_scaling,scaled_y,
												scale*icon_scaling,scale*icon_scaling);			
					break;
				case SE:
					gdk_cairo_set_source_pixbuf(destcr,pbuf,scaled_x+scaled_width-scale*icon_scaling,
												scaled_y+scaled_height-scale*icon_scaling);
					cairo_rectangle(destcr,scaled_x+scaled_width-scale*icon_scaling,scaled_y+scaled_height-scale*icon_scaling,
												scale*icon_scaling,scale*icon_scaling);			
					break;
				case SW:
					gdk_cairo_set_source_pixbuf(destcr,pbuf,scaled_x,
												scaled_y+scaled_height-scale*icon_scaling);
					cairo_rectangle(destcr,scaled_x,scaled_y+scaled_height-scale*icon_scaling,
												scale*icon_scaling,scale*icon_scaling);			
					break;
				case CENTRE:
				default:
					gdk_cairo_set_source_pixbuf(destcr,pbuf,scaled_x+(scaled_width-scale*icon_scaling)/2.0,
												scaled_y+(scaled_height-scale*icon_scaling)/2.0); 		
					cairo_rectangle(destcr,scaled_x+(scaled_width-scale*icon_scaling)/2.0,
												scaled_y+(scaled_height-scale*icon_scaling)/2.0,scale,scale);				
					break;
			}
		}			
		if ( wnck_window_is_active (win) )
		{
			alpha=shinyswitcher->win_active_icon_alpha;
		}
		else
		{
			alpha=shinyswitcher->win_inactive_icon_alpha;														
		}
		cairo_paint_with_alpha(destcr,alpha);
//		g_object_unref(pbuf);
	}							
}


void _unrealize_window_ev(GtkWidget *widget,Win_press_data * data)  
{
	g_free(data);
}


void do_event_boxes(Shiny_switcher *shinyswitcher,WnckWindow *win,Workplace_info *ws,double scaled_x,double scaled_y,
										double scaled_width,double scaled_height)
{
	if ( (shinyswitcher->active_window_on_workspace_change_method) && (scaled_height>1.0) &&(scaled_width>1.0) )
	{
		GtkWidget *ev=gtk_event_box_new();
	 	gtk_widget_set_app_paintable(ev,TRUE);
	 	gtk_event_box_set_visible_window(ev,FALSE);
	 	gtk_widget_set_size_request(ev,scaled_width,scaled_height);
	 	gtk_fixed_put(ws->wallpaper_ev->parent,ev,scaled_x,scaled_y);

	 	ws->event_boxes=g_list_append(ws->event_boxes,ev);	
	 	gtk_widget_show(ev);
		#if GTK_CHECK_VERSION(2,12,0)
		if (shinyswitcher->show_tooltips)
			if (wnck_window_has_name(win) )
				gtk_widget_set_tooltip_text(ev,wnck_window_get_name(win));
		#endif
		Win_press_data * data=g_malloc(sizeof(Win_press_data) );
		if (data)
		{
			data->wnck_window=win;
			data->shinyswitcher=shinyswitcher;
		 	g_signal_connect(G_OBJECT(ev),"button-press-event",G_CALLBACK (_button_win),data);			
			g_signal_connect(G_OBJECT(ev),"unrealize",G_CALLBACK (_unrealize_window_ev),data);			
		}			
	}
}


void remove_queued_render(Shiny_switcher *shinyswitcher,WnckWorkspace *space)
{
	if (space)
	{
		if (g_tree_lookup(shinyswitcher->ws_changes,space) )
		{
			g_tree_remove(shinyswitcher->ws_changes,space);
		}	
	}
}

void render_windows_to_wallpaper(Shiny_switcher *shinyswitcher,  WnckWorkspace * space)
{
	GList* wnck_spaces=wnck_screen_get_workspaces(shinyswitcher->wnck_screen);	
	GList * iter;
	WnckWindow * top_win=NULL;
	Workplace_info	* ws=NULL;
	GdkScreen* pScreen;    
	GdkColormap*	cmap;    	

	pScreen = gtk_widget_get_screen( shinyswitcher->applet);					
    cmap = gdk_screen_get_rgb_colormap (pScreen);

	for(iter=g_list_first(wnck_spaces);iter;iter=g_list_next(iter) )
	{
		if ( (!space) || (space==iter->data) )
		{

			int workspace_num;
			GList*  wnck_windows;	
			GList*	win_iter;

			remove_queued_render(shinyswitcher,iter->data);
			prepare_to_render_workspace(shinyswitcher,iter->data);						
			workspace_num=wnck_workspace_get_number(iter->data);
			wnck_windows=wnck_screen_get_windows_stacked(shinyswitcher->wnck_screen);	
			win_iter;
			
			for(win_iter=g_list_first(wnck_windows);win_iter;win_iter=g_list_next(win_iter) )
			{

				if ( wnck_window_is_visible_on_workspace (win_iter->data,iter->data) )
				{
					if (!wnck_window_is_skip_pager(win_iter->data) )
					{
						top_win=iter->data;
						gboolean on_active_space= (wnck_screen_get_active_workspace(shinyswitcher->wnck_screen)==iter->data);

						int x,y,width,height;
						wnck_window_get_geometry(win_iter->data,&x,&y,&width,&height);

#if 0			
						double scaled_width= (double)shinyswitcher->mini_work_width* (double)width / 
											(double)wnck_screen_get_width(shinyswitcher->wnck_screen);
						double scaled_height= (double)shinyswitcher->mini_work_height* (double) height / 
											(double)wnck_screen_get_height(shinyswitcher->wnck_screen);
						double scaled_x= (double)x* (double)shinyswitcher->mini_work_width/ 
											(double)wnck_screen_get_width(shinyswitcher->wnck_screen);
						double scaled_y= (double)y* (double)shinyswitcher->mini_work_height/ 
											(double)wnck_screen_get_height(shinyswitcher->wnck_screen);
#else
						double scaled_width= (double)shinyswitcher->mini_work_width* (double)width / 
											(double)wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );
						double scaled_height= (double)shinyswitcher->mini_work_height* (double) height / 
										(double)wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );

						double scaled_x, scaled_y;

						
						scaled_x= (double)x* (double)shinyswitcher->mini_work_width/ 
											(double)wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen))
											+
											wnck_workspace_get_viewport_x(iter->data)*(double)shinyswitcher->mini_work_width/
											(double)wnck_workspace_get_width(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen))
											;
						scaled_y= (double)y* (double)shinyswitcher->mini_work_height/ 
											(double)wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen))
											+
											wnck_workspace_get_viewport_y(iter->data)*(double)shinyswitcher->mini_work_height/
											(double)wnck_workspace_get_height(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) )
											;

#endif						
						ws=g_tree_lookup(shinyswitcher->ws_lookup_ev,iter->data);											
						GdkPixmap *pixmap;
						gtk_image_get_pixmap(gtk_bin_get_child(ws->wallpaper_ev),&pixmap,NULL);						
						assert(pixmap);
						assert(GDK_IS_PIXMAP(pixmap));						
						cairo_t * destcr=gdk_cairo_create(pixmap );							
						cairo_set_operator (destcr, CAIRO_OPERATOR_CLEAR);	
						cairo_fill(destcr);						
						//simple rectangle underneath it all
						if (1)//FIXME
						{
							cairo_set_operator (destcr, CAIRO_OPERATOR_OVER);	
							cairo_rectangle(destcr,scaled_x,scaled_y,scaled_width,scaled_height);
		  					cairo_set_source_rgba (destcr, 1.0f, 1.0f, 1.0f, 0.2f);	//FIXME ... pref.
							cairo_fill(destcr);
						}
					
						if ( (scaled_height	>8 ) && (scaled_width>8)  )	//FIME
						{
							do_win_grabs(shinyswitcher,destcr, win_iter->data,scaled_x,scaled_y,scaled_width,scaled_height,
									x,y,width,height,on_active_space);
						}
						if ( (scaled_height	>4 ) && (scaled_width>4)  )	//FIME
						{
						
							do_icon_overlays(shinyswitcher,destcr, win_iter->data,scaled_x,scaled_y,scaled_width,scaled_height,
									x,y,width,height,on_active_space);
						}									
						cairo_destroy(destcr);
						do_event_boxes(shinyswitcher,win_iter->data,ws,scaled_x,scaled_y,scaled_width,scaled_height);		
					}
				}
			}
		//	printf("\n");
		}			
		if (!space)
		{
			if (ws)
			{
				GtkFixed * container=ws->wallpaper_ev->parent;		
				gtk_widget_hide(container);
				gtk_widget_show(container);		
			}				
		}
	}
	if (space)
	{
		if (top_win)
		{
			GtkFixed * container=ws->wallpaper_ev->parent;
			GtkFixedChild * child = container->children->data;
			assert( child->widget == ws->wallpaper_ev) ;
			gtk_widget_hide(container);
			gtk_widget_show(container);
		}
	}
}

gboolean do_queued_renders(Shiny_switcher *shinyswitcher)
{
	GList* wnck_spaces=wnck_screen_get_workspaces(shinyswitcher->wnck_screen);	
	GList * iter;
	for(iter=g_list_first(wnck_spaces);iter;iter=g_list_next(iter) )
	{
		if (g_tree_lookup(shinyswitcher->ws_changes,iter->data) )
		{
			g_tree_remove(shinyswitcher->ws_changes,iter->data);
			render_windows_to_wallpaper(shinyswitcher,iter->data);				
		}
	}						
	return TRUE;
}

void queue_render(Shiny_switcher *shinyswitcher,WnckWorkspace *space)
{
	if (space)
	{
		if ( ! g_tree_lookup(shinyswitcher->ws_changes,space)  )
		{
			g_tree_insert(shinyswitcher->ws_changes,space,space);
		}	
	}		
}

void queue_all_render(Shiny_switcher *shinyswitcher)
{
	GList* wnck_spaces=wnck_screen_get_workspaces(shinyswitcher->wnck_screen);	
	GList * iter;
	for(iter=g_list_first(wnck_spaces);iter;iter=g_list_next(iter) )
	{
		queue_render(shinyswitcher,iter->data);
	}						
}

void _activewin_change(WnckScreen *screen,WnckWindow *previously_active_window,Shiny_switcher *shinyswitcher)
{
	WnckWorkspace *prev_space=NULL;
	WnckWindow * act_win=NULL;
	WnckWorkspace * act_space=NULL;
	
	act_space=wnck_screen_get_active_workspace(shinyswitcher->wnck_screen)	;
	if (previously_active_window)
	{
		prev_space=wnck_window_get_workspace(previously_active_window);		
	}		
	if (!act_space)
	{	
		act_win=wnck_screen_get_active_window(shinyswitcher->wnck_screen);
		if (act_win)
		{
			act_space=wnck_window_get_workspace(act_win);
		}
	}
	
	if (prev_space==act_space)
	{
		render_windows_to_wallpaper(shinyswitcher,act_space);		
	}
	else
	{
		if ( act_space && prev_space)
		{
			render_windows_to_wallpaper(shinyswitcher,act_space);				
			queue_render(shinyswitcher,prev_space);				
		}
		else if (act_space)
		{
			queue_all_render(shinyswitcher);			
			render_windows_to_wallpaper(shinyswitcher,act_space);//this will remove act_space from queue.		
		}
		else
		{
			render_windows_to_wallpaper(shinyswitcher,NULL);
		}
	}
	if (act_win)
	{
		image_cache_expire(shinyswitcher,shinyswitcher->surface_cache,act_win);					
	}		
}


void _workspace_change(WnckScreen *screen,WnckWorkspace *previously_active_space,Shiny_switcher *shinyswitcher)   
{	
	WnckWorkspace *act_space=wnck_screen_get_active_workspace(shinyswitcher->wnck_screen);
		
	if (act_space && previously_active_space)
	{
		render_windows_to_wallpaper(shinyswitcher,act_space);		
		if (act_space != previously_active_space)
		{
			queue_render(shinyswitcher,previously_active_space);
		}			
	}		
	else if (act_space)
	{
		queue_all_render(shinyswitcher);			
		render_windows_to_wallpaper(shinyswitcher,act_space);//this will remove act_space from queue.			
	}
	else
	{
		render_windows_to_wallpaper(shinyswitcher,NULL);		
	}
	
}


void _window_stacking_change(WnckScreen *screen,Shiny_switcher *shinyswitcher)  
{
	WnckWorkspace *space=wnck_screen_get_active_workspace(shinyswitcher->wnck_screen);
	if (space)
	{
		render_windows_to_wallpaper(shinyswitcher,space);	
	}
	else
	{
		render_windows_to_wallpaper(shinyswitcher,NULL);	
	}		
}



void _win_geom_change(WnckWindow *window,Shiny_switcher *shinyswitcher) 
{
	WnckWorkspace *space=wnck_window_get_workspace(window);
	if (!space)
	{
		space=wnck_screen_get_active_workspace(shinyswitcher->wnck_screen);	
	}		
	if (space)
	{
		queue_render(shinyswitcher,space);
	}		
	else
	{
		queue_all_render(shinyswitcher);		
	}
}                                          
           

void _win_state_change(WnckWindow *window,WnckWindowState changed_mask,WnckWindowState new_state,Shiny_switcher *shinyswitcher) 
{
	_win_geom_change(window,shinyswitcher);
}    

void _win_ws_change(WnckWindow *window,Shiny_switcher *shinyswitcher) 
{
	queue_all_render(shinyswitcher);	
}    
        
gboolean create_windows(Shiny_switcher *shinyswitcher)
{
	GList* wnck_spaces=wnck_screen_get_workspaces(shinyswitcher->wnck_screen);	
	GList * iter;
	
	render_windows_to_wallpaper(shinyswitcher,NULL);
	
	for(iter=g_list_first(wnck_spaces);iter;iter=g_list_next(iter) )
	{
		int workspace_num=wnck_workspace_get_number(iter->data);
		GList*  wnck_windows=wnck_screen_get_windows_stacked(shinyswitcher->wnck_screen);	
		GList*	win_iter;
		for(win_iter=g_list_first(wnck_windows);win_iter;win_iter=g_list_next(win_iter) )
		{

			if (!wnck_window_is_skip_pager(win_iter->data) )
			{
				g_signal_connect(G_OBJECT(win_iter->data),"state-changed",G_CALLBACK(_win_state_change),shinyswitcher);
				g_signal_connect(G_OBJECT(win_iter->data),"geometry-changed",G_CALLBACK(_win_geom_change),shinyswitcher);
				g_signal_connect(G_OBJECT(win_iter->data),"workspace-changed",G_CALLBACK(_win_ws_change),shinyswitcher);
				if (  shinyswitcher->show_right_click && WNCK_IS_WINDOW(win_iter->data) )
				{
					GtkWidget	*widget=wnck_create_window_action_menu(win_iter->data);
					if (widget)
					{
						if (GTK_IS_WIDGET(widget) )
						{
							g_tree_insert(shinyswitcher->win_menus,G_OBJECT(win_iter->data),widget);
						}
					}
				}
			}
		}
	}					
	return FALSE;
}

void _wallpaper_change(WnckScreen *screen,Shiny_switcher *shinyswitcher)
{
	g_object_unref(shinyswitcher->wallpaper_inactive);
	g_object_unref(shinyswitcher->wallpaper_active);	
	grab_wallpaper(shinyswitcher);	
}

void _window_opened(WnckScreen *screen,WnckWindow *window,Shiny_switcher *shinyswitcher)
{
	g_signal_connect(G_OBJECT(window),"state-changed",G_CALLBACK(_win_state_change),shinyswitcher);
	g_signal_connect(G_OBJECT(window),"geometry-changed",G_CALLBACK(_win_geom_change),shinyswitcher);	
	g_signal_connect(G_OBJECT(window),"workspace-changed",G_CALLBACK(_win_ws_change),shinyswitcher);	
	if (WNCK_IS_WINDOW(window) && shinyswitcher->show_right_click)
	{
		GtkWidget	*widget=wnck_create_window_action_menu(window);
		if (widget )
		{
			if (GTK_IS_WIDGET(widget) )
			{
				g_tree_insert(shinyswitcher->win_menus,window, widget );
			}			
		}			
	}		
	
}

void _window_closed(WnckScreen *screen,WnckWindow *window,Shiny_switcher *shinyswitcher)
{
	image_cache_remove(shinyswitcher->pixbuf_cache,window);
	image_cache_remove(shinyswitcher->surface_cache,window);
	if (shinyswitcher->show_right_click)
		g_tree_remove(shinyswitcher->win_menus,window);	
	g_signal_handlers_disconnect_by_func(G_OBJECT(window),G_CALLBACK(_win_state_change),shinyswitcher);
	g_signal_handlers_disconnect_by_func(G_OBJECT(window),G_CALLBACK(_win_geom_change),shinyswitcher);
	g_signal_handlers_disconnect_by_func(G_OBJECT(window),G_CALLBACK(_win_ws_change),shinyswitcher);			
} 


void  _composited_changed(GdkScreen *screen,Shiny_switcher *shinyswitcher) 
{
	screen = gtk_widget_get_screen(GTK_WIDGET(shinyswitcher->applet));	
	if ( gdk_screen_is_composited (screen) )
	{
		printf("screen is now composited... maybe we should do something\n");
	}
	else
	{
		printf("screen is now not composited... maybe we should do something\n");	
	}
}

void  _screen_size_changed(GdkScreen *screen,Shiny_switcher *shinyswitcher) 
{
	calc_dimensions(shinyswitcher);
}


gboolean  do_queue_act_ws(Shiny_switcher *shinyswitcher)
{			
	WnckWorkspace *space;
	space=wnck_screen_get_active_workspace(shinyswitcher->wnck_screen);	
	if (space)
	{
		queue_render(shinyswitcher,space);
	}			
	return TRUE;
}


gboolean _waited(Shiny_switcher *shinyswitcher) 
{
	GdkScreen *screen;
 	screen = gtk_widget_get_screen(GTK_WIDGET(shinyswitcher->applet));		
	wnck_screen_force_update(shinyswitcher->wnck_screen);  			
	
	shinyswitcher->rows=wnck_workspace_get_layout_row (wnck_screen_get_workspace(shinyswitcher->wnck_screen,
									wnck_screen_get_workspace_count(shinyswitcher->wnck_screen)-1)
										 )+1;
	shinyswitcher->cols=wnck_workspace_get_layout_column (wnck_screen_get_workspace(shinyswitcher->wnck_screen,
									wnck_screen_get_workspace_count(shinyswitcher->wnck_screen)-1)
										 )+1 ;	

	gtk_window_set_default_icon_name ("Shiny!");	
	

	calc_dimensions(shinyswitcher);
	grab_wallpaper(shinyswitcher);		
	create_containers(shinyswitcher);		
	create_windows(shinyswitcher);

	g_signal_connect(G_OBJECT(shinyswitcher->wnck_screen),"active-workspace-changed",G_CALLBACK (_workspace_change),shinyswitcher);
	g_signal_connect(G_OBJECT(shinyswitcher->wnck_screen),"active-window-changed",G_CALLBACK (_activewin_change),shinyswitcher); 	
	g_signal_connect(G_OBJECT(shinyswitcher->wnck_screen),"background-changed",G_CALLBACK (_wallpaper_change),shinyswitcher); 		 
	g_signal_connect(G_OBJECT(shinyswitcher->wnck_screen),"window-stacking-changed",G_CALLBACK (_window_stacking_change),shinyswitcher);  
	g_signal_connect(G_OBJECT(shinyswitcher->wnck_screen),"window-closed",G_CALLBACK (_window_closed),shinyswitcher);  
	g_signal_connect(G_OBJECT(shinyswitcher->wnck_screen),"window-opened",G_CALLBACK (_window_opened),shinyswitcher);  

	#if GLIB_CHECK_VERSION(2,14,0)
	g_timeout_add_seconds(shinyswitcher->do_queue_freq,(GSourceFunc)do_queued_renders,shinyswitcher);
	g_timeout_add_seconds(shinyswitcher->do_queue_freq+1,(GSourceFunc)do_queue_act_ws,shinyswitcher);	//FIXME
	#else
	g_timeout_add( (shinyswitcher->do_queue_freq)*1000,(GSourceFunc)do_queued_renders,shinyswitcher);
	g_timeout_add( (shinyswitcher->do_queue_freq+1)*1000,(GSourceFunc)do_queue_act_ws,shinyswitcher);	//FIXME
	#endif	

	g_signal_connect (G_OBJECT (shinyswitcher->applet), "height-changed", G_CALLBACK (_height_changed), (gpointer)shinyswitcher);
	g_signal_connect (G_OBJECT (shinyswitcher->applet), "orientation-changed", G_CALLBACK (_orient_changed), (gpointer)shinyswitcher);

	gtk_widget_show_all(shinyswitcher->container);
	
	gtk_widget_show_all(GTK_WIDGET(shinyswitcher->applet));

	g_signal_connect ( G_OBJECT(screen), "composited-changed", G_CALLBACK(_composited_changed), shinyswitcher);
	g_signal_connect ( G_OBJECT(screen), "size-changed", G_CALLBACK(_screen_size_changed), shinyswitcher);	
	
	g_signal_connect (G_OBJECT (shinyswitcher->applet), "expose_event",G_CALLBACK (_expose_event_outer), shinyswitcher);	
	gtk_widget_set_size_request (GTK_WIDGET (shinyswitcher->applet), shinyswitcher->width+shinyswitcher->applet_border_width*2,
								shinyswitcher->height*2.5);		
	return FALSE;
}

/**
 * Create new applet
 */
Shiny_switcher*
applet_new (AwnApplet *applet,int width,int height)
{
	GdkScreen *screen;

	Shiny_switcher *shinyswitcher = g_malloc(sizeof(Shiny_switcher)) ;
	shinyswitcher->applet = applet;
	shinyswitcher->ws_lookup_ev=g_tree_new(_cmp_ptrs);

	//doing this as a tree right now..  cause it's easy and I think I'll need a complex data structure eventually.
	shinyswitcher->ws_changes=g_tree_new(_cmp_ptrs);
	shinyswitcher->pixbuf_cache=g_tree_new(_cmp_ptrs);
	shinyswitcher->surface_cache=g_tree_new(_cmp_ptrs);
	shinyswitcher->win_menus=g_tree_new(_cmp_ptrs);			
	shinyswitcher->height = height;

	wnck_set_client_type(WNCK_CLIENT_TYPE_PAGER )	;
	shinyswitcher->wnck_screen=wnck_screen_get_default();

	wnck_screen_force_update(shinyswitcher->wnck_screen);  	
	printf("WM=%s\n",wnck_screen_get_window_manager_name(shinyswitcher->wnck_screen));	
	shinyswitcher->got_viewport=wnck_workspace_is_virtual(wnck_screen_get_active_workspace(shinyswitcher->wnck_screen) );
	if (wnck_screen_get_window_manager_name(shinyswitcher->wnck_screen) )
		if (strcmp(wnck_screen_get_window_manager_name(shinyswitcher->wnck_screen),"compiz") == 0)
		{
			printf("ShinySwitcher Message:  compiz detected\n");
			shinyswitcher->got_viewport=TRUE;
		}
	init_config	(shinyswitcher);
//	printf("cols = %d,  rows=%d \n",shinyswitcher->cols,shinyswitcher->rows);		
 	screen = gtk_widget_get_screen(GTK_WIDGET(shinyswitcher->applet));	
 	while(! gdk_screen_is_composited (screen) )		//FIXME
 	{
 		printf("Shinyswitcher startup:  screen not composited.. waiting 1 second\n");
 		g_usleep(G_USEC_PER_SEC);
	}
//	printf("COLUMNS=%d, ROWS=%d \n",shinyswitcher->cols,shinyswitcher->rows);
	if (shinyswitcher->reconfigure)
	{
		printf("ShinySwitcher Message:  attempting to configure workspaces\n");	
	  	wnck_screen_change_workspace_count(shinyswitcher->wnck_screen,shinyswitcher->cols*shinyswitcher->rows);	
		shinyswitcher->wnck_token =wnck_screen_try_set_workspace_layout(shinyswitcher->wnck_screen,0,shinyswitcher->rows,0);	
		
		if (!shinyswitcher->wnck_token)
		{
			printf("Failed to acquire ownership of workspace layout\n");			
		}			
	}
	else
	{
		printf("ShinySwitcher Message:  viewport/compiz detected.. using existing workspace config\n");
	}
	g_timeout_add(1000,(GSourceFunc)_waited,shinyswitcher);	//don't need to do this as seconds... happens once.
	return shinyswitcher;
}

static gboolean _expose_event_window(GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
	return FALSE;
}


static gboolean _expose_event_border(GtkWidget *widget, GdkEventExpose *expose,Shiny_switcher *shinyswitcher)
{
//	static cairo_t 	*	cr=NULL;
	return FALSE;

}
static gboolean _expose_event_outer(GtkWidget *widget, GdkEventExpose *expose,Shiny_switcher *shinyswitcher)
{

	return FALSE;

}

static gboolean
_button_release_event (GtkWidget *widget, GdkEventButton *event, gpointer *data)
{
	return TRUE;
}


static void
_height_changed (AwnApplet *app, guint height, gpointer *data)
{

}


static void
_orient_changed (AwnApplet *app, guint orient, gpointer *data)
{

}
