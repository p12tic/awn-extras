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

static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event, Cairo_main_menu * menu);

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
			gtk_window_set_opacity(GTK_WINDOW(menu->mainwindow),0.0)	;	
			g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL);      
		    gtk_widget_hide (menu->mainwindow);    
		}
		else
		{
		//	g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL);				
						    
    
			gtk_widget_show(menu->mainwindow);  
			gtk_fixed_move(menu->mainfixed,menu->mainbox,0,menu->mainwindow->allocation.height-menu->mainbox->allocation.height);								
			pos_dialog(menu->mainwindow);		
			gtk_window_set_opacity(GTK_WINDOW(menu->mainwindow),1.0)	;				  		    
		}    
    }
 	return TRUE;
}

static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, gpointer null)
{
	static gboolean done_once=FALSE;
	
	if (!done_once)
	{
		Cairo_main_menu * menu;
		menu=dialog_new(G_applet);
		gtk_widget_show_all(menu->mainwindow);	

		gtk_widget_show(menu->mainwindow);	
		pos_dialog(menu->mainwindow);	
		g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL); 		
		gtk_widget_hide(menu->mainwindow);	
	    g_signal_connect (G_OBJECT (menu->applet), "button-press-event",G_CALLBACK (_button_clicked_event), menu);		
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

	icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (),
		                           "gnome-main-menu",
		                           height-2,
		                           0, NULL);
	awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),icon);                                   
	gtk_widget_show_all (GTK_WIDGET (applet));
	
	g_signal_connect (G_OBJECT (applet),"expose-event", G_CALLBACK (_expose_event), NULL);	

	return applet;

}

