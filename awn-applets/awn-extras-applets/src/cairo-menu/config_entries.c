/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
 *
 * This is a CPU Load Applet for the Avant Window Navigator.  It
 * borrows heavily from the Gnome system monitor, so kudos go to
 * the authors of that program:
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
#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-applet-gconf.h>
#include "config_entries.h"
#include <gconf/gconf-client.h>
#include <glib.h>

#define GCONF_MENU "/apps/avant-window-navigator/applets/cairo-menu"

#define GCONF_NORMAL_BG GCONF_MENU "/bg_normal_colour"
#define GCONF_NORMAL_FG GCONF_MENU "/text_normal_colour"
#define GCONF_HOVER_BG GCONF_MENU "/bg_hover_colour"
#define GCONF_HOVER_FG GCONF_MENU "/text_hover_colour"

#define GCONF_TEXT_SIZE GCONF_MENU "/text_size"

#define GCONF_SEARCH_CMD GCONF_MENU "/search_cmd"
#define GCONF_SHOW_SEARCH GCONF_MENU "/search_show"

#define GCONF_MENU_GRADIENT GCONF_MENU "/menu_item_gradient_factor"
#define GCONF_MENU_ITEM_TEXT_LEN GCONF_MENU "/menu_item_text_len"

#define GCONF_HONOUR_GTK GCONF_MENU "/honour_gtk"

Cairo_menu_config G_cairo_menu_conf;

static GConfClient *gconf_client;

extern AwnApplet *G_applet;

void read_config(void)
{
	gchar	* svalue;
	GConfValue*	 value;	
	gconf_client = gconf_client_get_default();
	
    svalue = gconf_client_get_string(gconf_client,GCONF_NORMAL_BG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_NORMAL_BG, svalue=g_strdup("DDDDDDEE"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_cairo_menu_conf.normal.bg );    
    g_free(svalue);     	

    svalue = gconf_client_get_string(gconf_client,GCONF_NORMAL_FG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_NORMAL_FG, svalue=g_strdup("000000FF"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_cairo_menu_conf.normal.fg );    
    g_free(svalue);     	

    svalue = gconf_client_get_string(gconf_client,GCONF_HOVER_BG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_HOVER_BG, svalue=g_strdup("0022DDf0"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_cairo_menu_conf.hover.bg );    
    g_free(svalue);     	

    svalue = gconf_client_get_string(gconf_client,GCONF_HOVER_FG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_HOVER_FG, svalue=g_strdup("000000FF"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_cairo_menu_conf.hover.fg );    
    g_free(svalue);     

    value=gconf_client_get(gconf_client,GCONF_TEXT_SIZE,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.text_size=gconf_client_get_int(gconf_client,GCONF_TEXT_SIZE,NULL) ;
    }
    else             							
    {
        G_cairo_menu_conf.text_size=12;
        gconf_client_set_int (gconf_client,GCONF_TEXT_SIZE,G_cairo_menu_conf.text_size ,NULL);        
    }

    value=gconf_client_get(gconf_client,GCONF_SHOW_SEARCH,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.show_search=gconf_client_get_bool(gconf_client,GCONF_SHOW_SEARCH,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.show_search=TRUE;
        gconf_client_set_bool(gconf_client,GCONF_SHOW_SEARCH,G_cairo_menu_conf.show_search,NULL);        
    }    

    svalue = gconf_client_get_string(gconf_client,GCONF_SEARCH_CMD, NULL );
    if ( !svalue ) 
    {
		if (g_find_program_in_path("tracker-search-tool") )
		{
			svalue==g_strdup("tracker-search-tool");
		}    
		else if (g_find_program_in_path( "beagle-search") )
		{
			svalue==g_strdup("beagle-search");
		}    
		else
		{
			svalue==g_strdup("");
	        gconf_client_set_bool(gconf_client,GCONF_SHOW_SEARCH,FALSE,NULL);        			
		}
		
        gconf_client_set_string(gconf_client , GCONF_SEARCH_CMD, svalue, NULL );
    }
    G_cairo_menu_conf.search_cmd=g_strdup(svalue);
    if (strlen(svalue)==0)
    {
        gconf_client_set_string(gconf_client , GCONF_SEARCH_CMD, svalue, NULL );
    }
    g_free(svalue);     


    value=gconf_client_get(gconf_client,GCONF_MENU_GRADIENT,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.menu_item_gradient_factor=gconf_client_get_float(gconf_client,GCONF_MENU_GRADIENT,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.menu_item_gradient_factor=0.8;
        gconf_client_set_float(gconf_client,GCONF_MENU_GRADIENT,G_cairo_menu_conf.menu_item_gradient_factor,NULL);        
    }


    value=gconf_client_get(gconf_client,GCONF_MENU_ITEM_TEXT_LEN,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.menu_item_text_len=gconf_client_get_int(gconf_client,GCONF_MENU_ITEM_TEXT_LEN,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.menu_item_text_len=12;
        gconf_client_set_int(gconf_client,GCONF_MENU_ITEM_TEXT_LEN,G_cairo_menu_conf.menu_item_text_len,NULL);        
    }	
    
    value=gconf_client_get(gconf_client,GCONF_HONOUR_GTK,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.honour_gtk=gconf_client_get_bool(gconf_client,GCONF_HONOUR_GTK,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.honour_gtk=TRUE;
        gconf_client_set_bool(gconf_client,GCONF_HONOUR_GTK,G_cairo_menu_conf.honour_gtk,NULL);        
    } 
       
   	if (G_cairo_menu_conf.honour_gtk)
   	{  	  
		GdkColor d;  
		GtkWidget *top_win=GTK_WIDGET(G_applet);
		
		d=top_win->style->base[0];
		G_cairo_menu_conf.normal.bg.red=d.red/65535.0;
		G_cairo_menu_conf.normal.bg.green=d.green/65535.0;    
		G_cairo_menu_conf.normal.bg.blue=d.blue/65535.0;
		G_cairo_menu_conf.normal.bg.alpha=0.9;    

	   	d=top_win->style->fg[0];
		G_cairo_menu_conf.normal.fg.red=d.red/65535.0;
		G_cairo_menu_conf.normal.fg.green=d.green/65535.0;    
		G_cairo_menu_conf.normal.fg.blue=d.blue/65535.0;
		G_cairo_menu_conf.normal.fg.alpha=0.9;    


		d=top_win->style->base[GTK_STATE_PRELIGHT];
		G_cairo_menu_conf.hover.bg.red=d.red/65535.0;
		G_cairo_menu_conf.hover.bg.green=d.green/65535.0;    
		G_cairo_menu_conf.hover.bg.blue=d.blue/65535.0;
		G_cairo_menu_conf.hover.bg.alpha=0.9;    

	   	d=top_win->style->fg[GTK_STATE_PRELIGHT];
		G_cairo_menu_conf.hover.fg.red=d.red/65535.0;
		G_cairo_menu_conf.hover.fg.green=d.green/65535.0;    
		G_cairo_menu_conf.hover.fg.blue=d.blue/65535.0;
		G_cairo_menu_conf.hover.fg.alpha=0.9;   
		
		G_cairo_menu_conf.menu_item_gradient_factor=1.0;
	}		 
    
}
