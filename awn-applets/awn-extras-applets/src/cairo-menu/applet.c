/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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
 
#include "config.h"

#define GMENU_I_KNOW_THIS_IS_UNSTABLE
#include <gnome-menus/gmenu-tree.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>
#include "render.h"

#include "backend-gnome.h"
#include "menu.h"

AwnApplet *G_applet;
extern GtkWidget * G_Fixed;
extern Cairo_menu_config G_cairo_menu_conf;

static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu);


gboolean _fade_in(GtkWidget * window)
{
	static	float	opacity=0.2;
	
	opacity=opacity+0.1;
	
	if (opacity>=0.95)
	{
		gtk_window_set_opacity(GTK_WINDOW(window),1.0);	
		opacity=0.2;
		return FALSE;
	}
	gtk_window_set_opacity(GTK_WINDOW(window),opacity);				
	return TRUE;
}			

static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu)
{
    GdkEventButton *event_button;
    event_button = (GdkEventButton *) event; 
    if (event->button == 1)
    {
    	/*the gtk_window_set_opacity is a hack because the mainwindow window flickers, 
    	  	visibly, briefly on the screen sometimes without it*/
		if (GTK_WIDGET_VISIBLE(menu->mainwindow) )
		{
			if (G_cairo_menu_conf.do_fade)
				gtk_window_set_opacity(GTK_WINDOW(menu->mainwindow),0.0)	;	
			g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL);      
		    gtk_widget_hide (menu->mainwindow);    
		}
		else
		{

			gtk_widget_show(menu->mainwindow);  
			gtk_fixed_move(menu->mainfixed,menu->mainbox,0,menu->mainwindow->allocation.height-menu->mainbox->allocation.height);								
			pos_dialog(menu->mainwindow);		
			if (G_cairo_menu_conf.do_fade)
				g_timeout_add (120,_fade_in,menu->mainwindow);
		}    
    }
 	return TRUE;
}


int G_Height=40;
static _build_away(gpointer null)
{
	GdkPixbuf *icon;
	Cairo_main_menu * menu;
	menu=dialog_new(G_applet);
	gtk_widget_show_all(menu->mainwindow);	

	gtk_widget_show(menu->mainwindow);	
	pos_dialog(menu->mainwindow);	
	g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL); 		
	gtk_widget_hide(menu->mainwindow);	
    g_signal_connect (G_OBJECT (menu->applet), "button-press-event",G_CALLBACK (_button_clicked_event), menu);		
	icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (),
			                       G_cairo_menu_conf.applet_icon,
			                       G_Height-2,
			                       G_Height-2, NULL);
	if (!icon)
		icon=gdk_pixbuf_new_from_file_at_size(G_cairo_menu_conf.applet_icon,-G_Height-2,
			                       G_Height-2,NULL);
	if (!icon)
	{
		printf("failed to load icon: %s\n",G_cairo_menu_conf.applet_icon);
		icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (),"stock_missing-image",
			                       G_Height-2,
			                       G_Height-2, NULL);		
	}		     
	if (!icon)
	{

		icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (),"gnome-main-menu",
			                       G_Height-2,
			                       G_Height-2, NULL);					                       
	}	
	if (icon)                      
	{
		awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (G_applet),icon);				
	}		
	else
	{
	    icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,G_Height-2,G_Height-2);
		gdk_pixbuf_fill(icon,0x00000000);  
		awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (G_applet),icon);                                   	
	}
	return FALSE;
}


static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer null)
{
	static gboolean done_once=FALSE;
		
	if (!done_once)
	{
		g_timeout_add(500,_build_away,null);
                              	
	}		
	done_once=TRUE;
	return FALSE;
}	

	
AwnApplet* awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{

  	AwnApplet *applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
  	G_applet=applet;
	gtk_widget_set_size_request (GTK_WIDGET (applet), height, -1);
	GdkPixbuf *icon;
	G_Height=height;
	printf("height = %d\n");
    icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,1,height);
    gdk_pixbuf_fill(icon,0x00000000);  
	awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),icon);                                   
	gtk_widget_show_all (GTK_WIDGET (applet));
	
	g_signal_connect (G_OBJECT (applet),"expose-event", G_CALLBACK (_expose_event), NULL);	

	return applet;

}

