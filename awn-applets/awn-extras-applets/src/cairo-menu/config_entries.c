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
#include <string.h>
#include <unistd.h>
#include <stdlib.h>


#include "render.h"

Cairo_menu_config G_cairo_menu_conf;

static Cairo_menu_config G_cairo_menu_conf_copy;

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
        G_cairo_menu_conf.text_size=14;
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
		svalue=g_find_program_in_path("tracker-search-tool");
		if (!svalue)
		{
			svalue=g_find_program_in_path("beagle-search");
		}    
		if (!svalue)
		{
			svalue=g_strdup("terminal -x locate");
	        //gconf_client_set_bool(gconf_client,GCONF_SHOW_SEARCH,FALSE,NULL);        			
		}    		
        gconf_client_set_string(gconf_client , GCONF_SEARCH_CMD, svalue, NULL );

//    svalue==g_strdup("tracker-search-tool");
    }
    G_cairo_menu_conf.search_cmd=g_strdup(svalue);
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
    

    value=gconf_client_get(gconf_client,GCONF_SHOW_RUN,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.show_run=gconf_client_get_bool(gconf_client,GCONF_SHOW_RUN,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.show_run=TRUE;    
        gconf_client_set_bool(gconf_client,GCONF_SHOW_RUN,G_cairo_menu_conf.show_run,NULL);        
    }    
    

    value=gconf_client_get(gconf_client,GCONF_DO_FADE,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.do_fade=gconf_client_get_bool(gconf_client,GCONF_DO_FADE,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.do_fade=FALSE;
        gconf_client_set_bool(gconf_client,GCONF_DO_FADE,G_cairo_menu_conf.do_fade,NULL);        
    } 

    value=gconf_client_get(gconf_client,GCONF_SHOW_PLACES,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.show_places=gconf_client_get_bool(gconf_client,GCONF_SHOW_PLACES,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.show_places=TRUE;
        gconf_client_set_bool(gconf_client,GCONF_SHOW_PLACES,G_cairo_menu_conf.show_places,NULL);        
    } 

    svalue = gconf_client_get_string(gconf_client,GCONF_FILEMANAGER, NULL );
    if ( !svalue ) 
    {
		svalue=g_find_program_in_path("xdg-open");
		if (!svalue)
		{
			svalue=g_find_program_in_path("nautilus");
		}    
		if (!svalue)
		{
			svalue=g_strdup("thunar");
	        //gconf_client_set_bool(gconf_client,GCONF_SHOW_SEARCH,FALSE,NULL);        			
		}    		
		else
		{
			svalue=g_strdup("terminal -x less");		
		}
        gconf_client_set_string(gconf_client , GCONF_FILEMANAGER, svalue, NULL );
    }
	G_cairo_menu_conf.filemanager=strdup(svalue);
    g_free(svalue);     
    
    
    svalue = gconf_client_get_string(gconf_client,GCONF_APPLET_ICON, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_APPLET_ICON, svalue=g_strdup("gnome-main-menu"), NULL );
    }
	G_cairo_menu_conf.applet_icon=strdup(svalue);
    g_free(svalue);   
        
	
    value=gconf_client_get(gconf_client,GCONF_ON_BUTTON_RELEASE,NULL);		
    if (value)
    {																		
        G_cairo_menu_conf.on_button_release=gconf_client_get_bool(gconf_client,GCONF_ON_BUTTON_RELEASE,NULL) ;
    }
    else             							
    {
		G_cairo_menu_conf.on_button_release=TRUE;        
        gconf_client_set_bool(gconf_client,GCONF_ON_BUTTON_RELEASE,G_cairo_menu_conf.on_button_release,NULL);        
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


/*



#define GCONF_APPLET_ICON GCONF_MENU "/applet_icon"

#define GCONF_ON_BUTTON_RELEASE GCONF_MENU "/activate_on_release"

*/

char * awncolor_to_string(AwnColor * colour)
{

	return g_strdup_printf("%02x%02x%02x%02x",
								(unsigned int) round((colour->red*255)),
								(unsigned int) round((colour->green*255)),
								(unsigned int) round((colour->blue*255)),
								(unsigned int) round((colour->alpha*255))
								);
}


static void _save_config(void)
{
	gchar * svalue;
	
	gconf_client = gconf_client_get_default();
	
	svalue=awncolor_to_string(&G_cairo_menu_conf.normal.bg);	
    gconf_client_set_string(gconf_client , GCONF_NORMAL_BG,svalue, NULL );
    g_free(svalue);

    svalue = awncolor_to_string(&G_cairo_menu_conf.normal.fg);
	gconf_client_set_string(gconf_client , GCONF_NORMAL_FG, svalue, NULL );
    g_free(svalue);     	

    svalue = awncolor_to_string(&G_cairo_menu_conf.hover.bg);
	gconf_client_set_string(gconf_client , GCONF_HOVER_BG, svalue, NULL );
    g_free(svalue);     	
   	
    svalue = awncolor_to_string(&G_cairo_menu_conf.hover.fg);
	gconf_client_set_string(gconf_client, GCONF_HOVER_FG, svalue, NULL );
    g_free(svalue);     	
 
    gconf_client_set_int (gconf_client,GCONF_TEXT_SIZE,G_cairo_menu_conf.text_size ,NULL);        

    gconf_client_set_bool(gconf_client,GCONF_SHOW_SEARCH,G_cairo_menu_conf.show_search,NULL);        

    gconf_client_set_string(gconf_client ,  G_cairo_menu_conf.search_cmd, svalue, NULL );

    gconf_client_set_float(gconf_client,GCONF_MENU_GRADIENT,G_cairo_menu_conf.menu_item_gradient_factor,NULL);        

    gconf_client_set_int(gconf_client,GCONF_MENU_ITEM_TEXT_LEN,G_cairo_menu_conf.menu_item_text_len,NULL);        

    gconf_client_set_bool(gconf_client,GCONF_SHOW_RUN,G_cairo_menu_conf.show_run,NULL);        

    gconf_client_set_bool(gconf_client,GCONF_DO_FADE,G_cairo_menu_conf.do_fade,NULL);        

    gconf_client_set_bool(gconf_client,GCONF_SHOW_PLACES,G_cairo_menu_conf.show_places,NULL);        

    gconf_client_set_string(gconf_client , GCONF_FILEMANAGER, G_cairo_menu_conf.filemanager, NULL );

    gconf_client_set_string(gconf_client , GCONF_APPLET_ICON,G_cairo_menu_conf.applet_icon, NULL );
	
    gconf_client_set_bool(gconf_client,GCONF_ON_BUTTON_RELEASE,G_cairo_menu_conf.on_button_release,NULL);        
    
    gconf_client_set_bool(gconf_client,GCONF_HONOUR_GTK,G_cairo_menu_conf.honour_gtk,NULL);        
}

static gboolean _press_ok(GtkWidget *widget, GdkEventButton *event,GtkWidget * win)
{
	_save_config();
	gtk_widget_destroy(win);
	g_object_unref(gconf_client) ;
	GError *err=NULL;	
   GtkWidget *dialog, *label;
   
   dialog = gtk_dialog_new_with_buttons ("Cairo Menu Message",
                                         NULL,
                                         GTK_DIALOG_DESTROY_WITH_PARENT,
                                         GTK_STOCK_OK,
                                         GTK_RESPONSE_NONE,
                                         NULL);
   label = gtk_label_new ("About to restart Cairo Menu.  Please shutdown any instances of awn-manager");
   
   /* Ensure that the dialog box is destroyed when the user responds. */
   
   g_signal_connect_swapped (dialog,
                             "response", 
                             G_CALLBACK (gtk_widget_destroy),
                             dialog);
   gtk_container_add (GTK_CONTAINER (GTK_DIALOG(dialog)->vbox),
                      label);
	gtk_widget_show_all(dialog);                     
   gtk_dialog_run(dialog);	
	g_spawn_command_line_async("sh -c  'export T_STAMP=`date +\"%s\"`&& export AWN_G_ORIG=`gconftool-2 -g /apps/avant-window-navigator/applets_list | sed -e \"s/cairo_main_menu\.desktop::[0-9]*/cairo_main_menu\.desktop::$T_STAMP/\"` && export AWN_G_MOD=`echo $AWN_G_ORIG |sed -e \"s/[^,^\[]*cairo_main_menu\.desktop::[0-9]*,?//\"` && gconftool-2 --type list --list-type=string -s /apps/avant-window-navigator/applets_list \"$AWN_G_MOD\" && sleep 2 && gconftool-2 --type list --list-type=string -s /apps/avant-window-navigator/applets_list \"$AWN_G_ORIG\"'",&err); 
	exit(0);
 	return FALSE;

	
}


static gboolean _toggle_(GtkWidget *widget,gboolean * value)
{
	*value=!*value;

	return FALSE;
}

static gboolean _toggle_gtk(GtkWidget *widget,GtkWidget * gtk_off_section)
{
//	gtk_toggle_button_set_active(widget,G_cairo_menu_conf.honour_gtk);	
	G_cairo_menu_conf.honour_gtk=gtk_toggle_button_get_active(widget);
	if (G_cairo_menu_conf.honour_gtk)
	{
		gtk_widget_hide(gtk_off_section);
	}
	else
	{
		gtk_widget_show_all(gtk_off_section);
	}	
	return TRUE;	
}

int activate(GtkWidget *w,gchar **p)
{
	gchar * svalue=*p;
	g_free(svalue);
	svalue=g_strdup(gtk_entry_get_text (w) );
	*p=svalue;
	return FALSE;
}

/*I'm lazy.. and I do not like doing pref dialogs....*/
GtkWidget *gtk_off_table;
GtkWidget * hover_ex;
GtkWidget * normal_ex;

void _mod_colour(GtkColorButton *widget,AwnColor * user_data) 
{
	GdkColor colr;
	gtk_color_button_get_color(widget,&colr);
	user_data->red=colr.red/65535.0;
	user_data->green=colr.green/65535.0;	
	user_data->blue=colr.blue/65535.0;	
	user_data->alpha=gtk_color_button_get_alpha(widget)/65535.0;	
	
	gtk_widget_destroy(hover_ex);
	gtk_widget_destroy(normal_ex);
	hover_ex=build_menu_widget(&G_cairo_menu_conf.hover,"Hover",NULL,NULL,MENU_WIDGET_NORMAL);	
	normal_ex=build_menu_widget(&G_cairo_menu_conf.normal,"Normal",NULL,NULL,MENU_WIDGET_NORMAL);
	
	gtk_table_attach_defaults(gtk_off_table,normal_ex,3,4,0,1);	
	gtk_table_attach_defaults(gtk_off_table,hover_ex,3,4,1,2);	
	gtk_widget_show(hover_ex);
	gtk_widget_show(normal_ex);
}

void spin_change(GtkSpinButton *spinbutton,double * val)
{
	*val=gtk_spin_button_get_value(spinbutton);
}

void spin_int_change(GtkSpinButton *spinbutton,int * val)
{
	*val=gtk_spin_button_get_value(spinbutton);
}

void show_prefs(void)
{
	G_cairo_menu_conf_copy=G_cairo_menu_conf;
	
	GtkWidget * prefs_win=gtk_window_new (GTK_WINDOW_TOPLEVEL);	
	GdkColormap *colormap;
	GdkScreen *screen;
		
	screen = gtk_window_get_screen(GTK_WINDOW(prefs_win));
	colormap = gdk_screen_get_rgba_colormap(screen);
	if (colormap != NULL && gdk_screen_is_composited(screen))
	{
		gtk_widget_set_colormap(prefs_win, colormap);
	}	    	
	gtk_window_set_title (prefs_win,"Cairo Menu Preferences");
	GtkWidget* vbox=gtk_vbox_new(FALSE,0);
	GtkWidget * gtk=gtk_check_button_new_with_label("Use Gtk");
	GtkWidget * places=gtk_check_button_new_with_label("Show Places");
	GtkWidget * search=gtk_check_button_new_with_label("Show Search");
	GtkWidget * run=gtk_check_button_new_with_label("Show Run");
	GtkWidget * fade_in=gtk_check_button_new_with_label("Fade in menu");	
	GtkWidget * release=gtk_check_button_new_with_label("Activate On Release");
	
	GtkWidget* gtk_off_section=gtk_vbox_new(FALSE,0);	
	gtk_off_table=gtk_table_new(2,4,FALSE);
	
	GtkWidget *normal_label=gtk_label_new("Normal");
	GdkColor 	colr;
		
//	GtkWidget *normal_bg=gtk_button_new_with_label("Background");
	colr.red=G_cairo_menu_conf.normal.bg.red*65535;
	colr.green=G_cairo_menu_conf.normal.bg.green*65535;	
	colr.blue=G_cairo_menu_conf.normal.bg.blue*65535;	
	GtkWidget *normal_bg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (normal_bg,TRUE);
	gtk_color_button_set_alpha (normal_bg,G_cairo_menu_conf.normal.bg.alpha*65535);
	g_signal_connect (G_OBJECT (normal_bg), "color-set",G_CALLBACK (_mod_colour),&G_cairo_menu_conf.normal.bg);		
	
//	GtkWidget *normal_fg=gtk_button_new_with_label("Foreground");
	colr.red=G_cairo_menu_conf.normal.fg.red*65535;
	colr.green=G_cairo_menu_conf.normal.fg.green*65535;	
	colr.blue=G_cairo_menu_conf.normal.fg.blue*65535;	
	GtkWidget *normal_fg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (normal_fg,TRUE);
	gtk_color_button_set_alpha (normal_fg,G_cairo_menu_conf.normal.fg.alpha*65535);
	g_signal_connect (G_OBJECT (normal_fg), "color-set",G_CALLBACK (_mod_colour),&G_cairo_menu_conf.normal.fg);		
	
	GtkWidget *hover_label=gtk_label_new("Hover");
//	GtkWidget *hover_bg=gtk_button_new_with_label("Background");

	colr.red=G_cairo_menu_conf.hover.bg.red*65535;
	colr.green=G_cairo_menu_conf.hover.bg.green*65535;	
	colr.blue=G_cairo_menu_conf.hover.bg.blue*65535;	
	GtkWidget *hover_bg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (hover_bg,TRUE);
	gtk_color_button_set_alpha (hover_bg,G_cairo_menu_conf.hover.bg.alpha*65535);
	g_signal_connect (G_OBJECT (hover_bg), "color-set",G_CALLBACK (_mod_colour),&G_cairo_menu_conf.hover.bg);		
	
//	GtkWidget *hover_fg=gtk_button_new_with_label("Foreground");
	colr.red=G_cairo_menu_conf.hover.fg.red*65535;
	colr.green=G_cairo_menu_conf.hover.fg.green*65535;	
	colr.blue=G_cairo_menu_conf.hover.fg.blue*65535;	
	GtkWidget *hover_fg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (hover_fg,TRUE);
	gtk_color_button_set_alpha (hover_fg,G_cairo_menu_conf.hover.fg.alpha*65535);	
	g_signal_connect (G_OBJECT (hover_fg), "color-set",G_CALLBACK (_mod_colour),&G_cairo_menu_conf.hover.fg);		

	GtkWidget * text_table=gtk_table_new(2,4,FALSE);
	GtkWidget * search_cmd=gtk_entry_new();
	GtkWidget * filemanager=gtk_entry_new();
	GtkWidget * adjust_gradient=gtk_spin_button_new_with_range(0.0,1.0,0.01);

	GtkWidget * adjust_textlen=gtk_spin_button_new_with_range(5,30,1);
	GtkWidget * adjust_textsize=gtk_spin_button_new_with_range(4,40,1);	
	
	GtkWidget* buttons=gtk_hbox_new(FALSE,0);	
	GtkWidget* ok=gtk_button_new_with_label("Ok");
	
	Menu_item_color mic;
	mic.bg=G_cairo_menu_conf.normal.bg;
	mic.fg=G_cairo_menu_conf.normal.fg;
	normal_ex=build_menu_widget(&mic,"Normal",NULL,NULL,MENU_WIDGET_NORMAL);

	mic.bg=G_cairo_menu_conf.hover.bg;
	mic.fg=G_cairo_menu_conf.hover.fg;
	hover_ex=build_menu_widget(&mic,"Hover",NULL,NULL,MENU_WIDGET_NORMAL);


    gtk_window_set_keep_above (GTK_WINDOW (prefs_win),TRUE);
    gtk_window_set_accept_focus(GTK_WINDOW (prefs_win),TRUE);
	gtk_window_set_focus_on_map (GTK_WINDOW (prefs_win),TRUE);	

	gtk_spin_button_set_value(adjust_gradient,G_cairo_menu_conf.menu_item_gradient_factor);
	gtk_spin_button_set_value(adjust_textlen,G_cairo_menu_conf.menu_item_text_len);
	gtk_spin_button_set_value(adjust_textsize,G_cairo_menu_conf.text_size);			
	g_signal_connect (G_OBJECT (adjust_gradient), "value-changed",G_CALLBACK (spin_change),
									&G_cairo_menu_conf.menu_item_gradient_factor);	
	g_signal_connect (G_OBJECT (adjust_textlen), "value-changed",G_CALLBACK (spin_int_change),
									&G_cairo_menu_conf.menu_item_text_len);	
	g_signal_connect (G_OBJECT (adjust_textsize), "value-changed",G_CALLBACK (spin_int_change),
									&G_cairo_menu_conf.text_size);	
	
	gtk_entry_set_text(search_cmd,G_cairo_menu_conf.search_cmd);
	g_signal_connect (G_OBJECT(search_cmd), "activate",G_CALLBACK (activate), &G_cairo_menu_conf.search_cmd);	
	gtk_entry_set_text(filemanager,G_cairo_menu_conf.filemanager);	
	g_signal_connect (G_OBJECT(filemanager), "activate",G_CALLBACK (activate), &G_cairo_menu_conf.filemanager);		
	gtk_toggle_button_set_active(gtk,G_cairo_menu_conf.honour_gtk);
	
	gtk_toggle_button_set_active(search,G_cairo_menu_conf.show_search);
	g_signal_connect (G_OBJECT (search), "toggled",G_CALLBACK (_toggle_),&G_cairo_menu_conf.show_search);		
	gtk_toggle_button_set_active(places,G_cairo_menu_conf.show_places);
	g_signal_connect (G_OBJECT (places), "toggled",G_CALLBACK (_toggle_),&G_cairo_menu_conf.show_places);		
	gtk_toggle_button_set_active(release,G_cairo_menu_conf.on_button_release);		
	g_signal_connect (G_OBJECT (release), "toggled",G_CALLBACK (_toggle_),&G_cairo_menu_conf.on_button_release);			
	gtk_toggle_button_set_active(run,G_cairo_menu_conf.show_run);		
	g_signal_connect (G_OBJECT (run), "toggled",G_CALLBACK (_toggle_),&G_cairo_menu_conf.show_run);		
	gtk_toggle_button_set_active(fade_in,G_cairo_menu_conf.do_fade);	
	g_signal_connect (G_OBJECT (fade_in), "toggled",G_CALLBACK (_toggle_),&G_cairo_menu_conf.do_fade);				


	g_signal_connect (G_OBJECT (ok), "button-press-event",G_CALLBACK (_press_ok),prefs_win );	

	gtk_container_add (GTK_CONTAINER (prefs_win), vbox); 

	g_signal_connect (G_OBJECT (gtk), "toggled",G_CALLBACK (_toggle_gtk),gtk_off_section );	
	
	#if 1
	
	gtk_box_pack_start(GTK_CONTAINER (vbox),search,FALSE,FALSE,0);	
	gtk_box_pack_start(GTK_CONTAINER (vbox),places,FALSE,FALSE,0);	
	gtk_box_pack_start(GTK_CONTAINER (vbox),run,FALSE,FALSE,0);		
	gtk_box_pack_start(GTK_CONTAINER (vbox),fade_in,FALSE,FALSE,0);	
	gtk_box_pack_start(GTK_CONTAINER (vbox),release,FALSE,FALSE,0);			

	gtk_box_pack_start(GTK_CONTAINER (vbox),text_table,FALSE,FALSE,0);		
	gtk_table_attach_defaults(text_table,gtk_label_new("Search command"),0,1,0,1);	
	gtk_table_attach_defaults(text_table,search_cmd,1,2,0,1);		
	gtk_table_attach_defaults(text_table,gtk_label_new("Filemanager"),0,1,1,2);	
	gtk_table_attach_defaults(text_table,filemanager,1,2,1,2);		
	
	gtk_box_pack_start(GTK_CONTAINER (vbox),adjust_textlen,FALSE,FALSE,0);			
	gtk_box_pack_start(GTK_CONTAINER (vbox),adjust_textsize,FALSE,FALSE,0);		
	#endif 
	gtk_box_pack_start(GTK_CONTAINER (vbox),gtk,FALSE,FALSE,0);
	
	gtk_box_pack_start(GTK_CONTAINER (vbox),gtk_off_section,FALSE,FALSE,0);
	gtk_box_pack_start(GTK_CONTAINER(gtk_off_section),gtk_off_table,FALSE,FALSE,0);

	gtk_table_attach_defaults(gtk_off_table,normal_label,0,1,0,1);	
	gtk_table_attach_defaults(gtk_off_table,normal_bg,1,2,0,1);	
	gtk_table_attach_defaults(gtk_off_table,normal_fg,2,3,0,1);
	gtk_table_attach_defaults(gtk_off_table,normal_ex,3,4,0,1);			
		
	gtk_table_attach_defaults(gtk_off_table,hover_label,0,1,1,2);	
	gtk_table_attach_defaults(gtk_off_table,hover_bg,1,2,1,2);	
	gtk_table_attach_defaults(gtk_off_table,hover_fg,2,3,1,2);	
	gtk_table_attach_defaults(gtk_off_table,hover_ex,3,4,1,2);		
	gtk_table_attach_defaults(gtk_off_table,gtk_label_new("Gradient Factor"),0,1,2,3);	
	gtk_table_attach_defaults(gtk_off_table,adjust_gradient,1,3,2,3);


	
	gtk_box_pack_start(GTK_CONTAINER (vbox),buttons,FALSE,FALSE,0);
	gtk_box_pack_start(GTK_CONTAINER (buttons),ok,FALSE,FALSE,0);							
	gtk_widget_show_all(prefs_win);	
	if (G_cairo_menu_conf.honour_gtk)
	{
		gtk_widget_hide(gtk_off_section);
	}

}

