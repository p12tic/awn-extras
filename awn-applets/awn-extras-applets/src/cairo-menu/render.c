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
#include <assert.h> 
#include <gdk/gdk.h>
#include <libawn/awn-cairo-utils.h>
#include <libsexy/sexy-icon-entry.h>

#include "menu.h"
#include "menu_list_item.h"
#include "render.h"

extern Cairo_menu_config G_cairo_menu_conf;

extern AwnApplet *G_applet;
GtkWidget * G_Fixed;
GtkWidget	*	G_toplevel=NULL;
GtkWidget * G_mainwindow;
int G_height,G_y,G_x;
gboolean 	G_repression=FALSE;



typedef struct
{
	GtkWidget *	subwidget;
	GtkWidget * normal;
	GtkWidget * hover;
	GtkWidget * misc;
	GtkWidget * aux;	
}Mouseover_data;
Mouseover_data	* G_Search=NULL;

GtkWidget * build_menu_widget_layer_pixbufs(Menu_item_color * mic, char * text,GdkPixbuf *pbuf_lower,GdkPixbuf *pbuf_upper)
{
    static cairo_t *cr = NULL;   
    GtkWidget * widget;
    GdkScreen* pScreen;        
	GdkPixmap * pixmap; 
	GdkColormap*	cmap;

    pixmap=gdk_pixmap_new(NULL,G_cairo_menu_conf.text_size*G_cairo_menu_conf.menu_item_text_len, G_cairo_menu_conf.text_size*1.4,32);   //FIXME
    widget=gtk_image_new_from_pixmap(pixmap,NULL);        
    pScreen = gtk_widget_get_screen (G_Fixed);
    cmap = gdk_screen_get_rgba_colormap (pScreen);
    if (!cmap)
            cmap = gdk_screen_get_rgb_colormap (pScreen); 
    gdk_drawable_set_colormap(pixmap,cmap);       
    cr=gdk_cairo_create(pixmap);
    cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(cr);
    cairo_set_source_rgba (cr, mic->bg.red,mic->bg.green,mic->bg.blue, mic->bg.alpha);
    cairo_set_operator (cr, CAIRO_OPERATOR_OVER);	
   	cairo_paint(cr);
   	if (pbuf_lower)
   	{
		gdk_cairo_set_source_pixbuf(cr,pbuf_lower,0,0);   	
		cairo_move_to(cr,1,1);
		cairo_paint(cr);
		if (pbuf_upper)
		{
			gdk_cairo_set_source_pixbuf(cr,pbuf_upper,0,0);   	
			cairo_move_to(cr,1,1);
			cairo_paint(cr);
		}					
	}		
    cairo_set_source_rgba (cr, mic->fg.red,mic->fg.green,mic->fg.blue, mic->fg.alpha);
    cairo_set_operator (cr, CAIRO_OPERATOR_OVER);	   	
   	cairo_move_to(cr,G_cairo_menu_conf.text_size*1.3 , G_cairo_menu_conf.text_size);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size (cr,G_cairo_menu_conf.text_size  );          	
   	cairo_show_text(cr,text);    	
	cairo_destroy(cr);
	g_object_unref (pixmap);
	return widget;
}


/*
At some point in time it might be good to cache cr and gradient.  
At this point it's a bit inefficient on initial startup... but that's the only
time the code is run.
*/
GtkWidget * build_menu_widget(Menu_item_color * mic, char * text,GdkPixbuf *pbuf)
{
    static cairo_t *cr = NULL;   
    GtkWidget * widget;
    GdkScreen* pScreen;        
	GdkPixmap * pixmap; 
	GdkColormap*	cmap;
    cairo_pattern_t *gradient=NULL;
    cairo_text_extents_t    extents;      
    
    pixmap=gdk_pixmap_new(NULL,G_cairo_menu_conf.text_size*G_cairo_menu_conf.menu_item_text_len, 
    					G_cairo_menu_conf.text_size*1.4,32);   //FIXME
    widget=gtk_image_new_from_pixmap(pixmap,NULL);        
    pScreen = gtk_widget_get_screen (G_Fixed);
    cmap = gdk_screen_get_rgba_colormap (pScreen);
    if (!cmap)
            cmap = gdk_screen_get_rgb_colormap (pScreen); 
    gdk_drawable_set_colormap(pixmap,cmap);       
    cr=gdk_cairo_create(pixmap);
    cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(cr);
//    cairo_set_source_rgba (cr, mic->bg.red,mic->bg.green,mic->bg.blue, mic->bg.alpha);
    cairo_set_operator (cr, CAIRO_OPERATOR_OVER);	

    gradient = cairo_pattern_create_linear(0, 0, 0,
            G_cairo_menu_conf.text_size*1.4);
    cairo_pattern_add_color_stop_rgba(gradient, 0,  mic->bg.red,mic->bg.green,mic->bg.blue, 
    						mic->bg.alpha*G_cairo_menu_conf.menu_item_gradient_factor);
    cairo_pattern_add_color_stop_rgba(gradient, 0.5, mic->bg.red,mic->bg.green,mic->bg.blue, 
    									mic->bg.alpha);
    cairo_pattern_add_color_stop_rgba(gradient, 1,mic->bg.red,mic->bg.green,mic->bg.blue, 
    							mic->bg.alpha*G_cairo_menu_conf.menu_item_gradient_factor);
    cairo_set_source(cr, gradient);    
   	cairo_paint(cr);
   	if (pbuf)
   	{
		gdk_cairo_set_source_pixbuf(cr,pbuf,G_cairo_menu_conf.text_size*0.3,G_cairo_menu_conf.text_size*0.2);   	
	
	    cairo_rectangle(cr,0,0,G_cairo_menu_conf.text_size*1.3,
	    						G_cairo_menu_conf.text_size*1.2);
		cairo_fill(cr);
	}		
    cairo_set_source_rgba (cr, mic->fg.red,mic->fg.green,mic->fg.blue, mic->fg.alpha);
    cairo_set_operator (cr, CAIRO_OPERATOR_OVER);	   	
   	cairo_move_to(cr,G_cairo_menu_conf.text_size*1.3 , G_cairo_menu_conf.text_size);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size (cr,G_cairo_menu_conf.text_size  );  
    
    char * buf;
    int  nul_pos=strlen(text);
    buf=g_malloc(nul_pos+3);
    strcpy(buf,text);
	cairo_text_extents(cr,buf,&extents);   
	while  ( ( nul_pos>5) &&
			(extents.width +  G_cairo_menu_conf.text_size*1.3 > 
			G_cairo_menu_conf.text_size*(G_cairo_menu_conf.menu_item_text_len-1))
			)
	{
		nul_pos--;				
		buf[nul_pos]='\0';
		strcat(buf,"...");	/*good enough*/
		cairo_text_extents(cr,buf,&extents);   		
	}			
   	cairo_show_text(cr,buf);    	
   	g_free(buf);
	cairo_destroy(cr);
	cairo_pattern_destroy(gradient);
	return widget;
}

void render_search(Menu_list_item *entry)
{
	GdkPixmap *pixmap;
	GtkIconTheme*  g;  	
	GdkPixbuf *pbuf=NULL;
	GdkPixbuf *tmp;	
//	gtk_image_new_from_stock(GTK_STOCK_EXECUTE,GTK_ICON_SIZE_MENU);  
    g=gtk_icon_theme_get_default();
    
    tmp=gtk_icon_theme_load_icon(g,entry->icon,G_cairo_menu_conf.text_size,0,NULL);
    if (tmp)
    {
		pbuf=gdk_pixbuf_scale_simple(tmp,G_cairo_menu_conf.text_size,G_cairo_menu_conf.text_size,GDK_INTERP_HYPER);    
		g_object_unref(tmp);
	}	
	    
	if (!pbuf)
	{
		tmp=gdk_pixbuf_new_from_file_at_size(entry->icon,-1,G_cairo_menu_conf.text_size,NULL);		
		if (tmp)
		{
			pbuf=gdk_pixbuf_scale_simple(tmp,G_cairo_menu_conf.text_size,G_cairo_menu_conf.text_size,GDK_INTERP_HYPER);    
			g_object_unref(tmp);
		}	
	}		
		
	entry->widget=gtk_event_box_new();
	gtk_event_box_set_visible_window(entry->widget,FALSE);
	gtk_event_box_set_above_child (entry->widget,TRUE);	
	entry->normal=build_menu_widget(&G_cairo_menu_conf.normal,entry->name,pbuf);
	entry->hover=build_menu_widget(&G_cairo_menu_conf.hover,entry->name,pbuf);	
	entry->search_entry=sexy_icon_entry_new();
	sexy_icon_entry_set_icon( (SexyIconEntry *)entry->search_entry,SEXY_ICON_ENTRY_PRIMARY,
							  gtk_image_new_from_pixbuf(pbuf) );
	sexy_icon_entry_add_clear_button((SexyIconEntry *)entry->search_entry);
	g_object_ref(entry->normal);
	gtk_container_add(entry->widget,entry->normal);			
	if (pbuf)
		g_object_unref(pbuf);
}


void render_entry(Menu_list_item *entry)
{
	GdkPixmap *pixmap;
	GtkIconTheme*  g;  	
	GdkPixbuf *pbuf=NULL;
	GdkPixbuf *tmp;	
//	gtk_image_new_from_stock(GTK_STOCK_EXECUTE,GTK_ICON_SIZE_MENU);  
    g=gtk_icon_theme_get_default();
    
    tmp=gtk_icon_theme_load_icon(g,entry->icon,G_cairo_menu_conf.text_size,0,NULL);
    if (tmp)
    {
		pbuf=gdk_pixbuf_scale_simple(tmp,G_cairo_menu_conf.text_size,G_cairo_menu_conf.text_size,GDK_INTERP_HYPER);    
		g_object_unref(tmp);
	}	
	    
	if (!pbuf)
	{
		tmp=gdk_pixbuf_new_from_file_at_size(entry->icon,-1,G_cairo_menu_conf.text_size,NULL);		
		if (tmp)
		{
			pbuf=gdk_pixbuf_scale_simple(tmp,G_cairo_menu_conf.text_size,G_cairo_menu_conf.text_size,GDK_INTERP_HYPER);    
			g_object_unref(tmp);
		}	
	}		
	
	
	entry->widget=gtk_event_box_new();
	gtk_event_box_set_visible_window(entry->widget,FALSE);
	gtk_event_box_set_above_child (entry->widget,TRUE);	
	entry->normal=build_menu_widget(&G_cairo_menu_conf.normal,entry->name,pbuf);
	entry->hover=build_menu_widget(&G_cairo_menu_conf.hover,entry->name,pbuf);	
	g_object_ref(entry->normal);
	gtk_container_add(entry->widget,entry->normal);			
	if (pbuf)
		g_object_unref(pbuf);
}


void render_directory(Menu_list_item *directory)
{
	GdkPixmap *pixmap;
	GtkIconTheme*  g;  	
	GdkPixbuf *pbuf1=NULL;
	GdkPixbuf *pbuf2=NULL;
	GdkPixbuf *tmp=NULL;
    g=gtk_icon_theme_get_default();

    tmp=gtk_icon_theme_load_icon(g,"stock_folder",G_cairo_menu_conf.text_size,0,NULL);    
    if (tmp)
    {
		pbuf1=gdk_pixbuf_scale_simple(tmp,G_cairo_menu_conf.text_size,G_cairo_menu_conf.text_size,GDK_INTERP_HYPER);    
		g_object_unref(tmp);
	}		
	if (!pbuf1)
	{
		pbuf1=gdk_pixbuf_new_from_file_at_size("folder",-1,G_cairo_menu_conf.text_size,NULL);
		if (!pbuf1)
		{		
			pbuf1=gdk_pixbuf_new_from_file_at_size("folder_new",-1,G_cairo_menu_conf.text_size,NULL);		
		}			
	}			

    tmp=gtk_icon_theme_load_icon(g,"folder_open",G_cairo_menu_conf.text_size,0,NULL);    
    if (tmp)
    {
		pbuf2=gdk_pixbuf_scale_simple(tmp,G_cairo_menu_conf.text_size,G_cairo_menu_conf.text_size,GDK_INTERP_HYPER);    
		g_object_unref(tmp);
	}		
	if (!pbuf1)
		pbuf1=pbuf2;
	if (!pbuf2)
		pbuf2=pbuf1;		
//	pbuf_over=gtk_icon_theme_load_icon(g,directory->icon,G_cairo_menu_conf.text_size,0,NULL);    	
	directory->widget=gtk_event_box_new();
	gtk_event_box_set_visible_window(directory->widget,FALSE);
	gtk_event_box_set_above_child (directory->widget,TRUE);	
	directory->normal=build_menu_widget(&G_cairo_menu_conf.normal,directory->name,pbuf1);
	directory->hover=build_menu_widget(&G_cairo_menu_conf.hover,directory->name,pbuf2);	
	g_object_ref(directory->normal);
	gtk_container_add(directory->widget,directory->normal);		
	if (pbuf1)
		g_object_unref(pbuf1);
	if (pbuf2)
		g_object_unref(pbuf2);	
}

void _fixup_menus(GtkFixedChild * child,GtkWidget * subwidget)
{
	static int maxheight=600;		/*FIXME*/
	if (!subwidget)
	{
		if (child->widget != G_toplevel)	
		{
			gtk_widget_hide(child->widget);
			return;
		}
	}
	if (child->widget->allocation.height > maxheight)
	{
		maxheight=child->widget->allocation.height;
	}
	if (child->widget != G_toplevel)
	{

//		gtk_fixed_move(G_Fixed,child->widget,child->x,G_Fixed->allocation.height-child->widget->allocation.height);

		if (child->widget != subwidget)
		{
			gboolean found=FALSE;
			void * ptr=g_tree_lookup(G_cairo_menu_conf.submenu_deps,subwidget);
			for(;ptr!=G_toplevel;ptr=g_tree_lookup(G_cairo_menu_conf.submenu_deps,ptr) )
			{
				if (ptr==child->widget)
				{
					found=TRUE;
				}
			}					
			if (!found)
			{
				gtk_widget_hide(child->widget);
			}		
			
		}
		else
		{
			gtk_widget_show_all(subwidget);
			/*NASTY HACK HERE*/
			G_height=child->widget->allocation.height;
			G_y=child->y;
			G_x=child->x;

		}
	}

}

static gboolean _enter_notify_event(GtkWidget *widget,GdkEventCrossing *event,Mouseover_data *data)  
{
	if ( (gtk_bin_get_child(widget)==data->misc) || G_repression)
	{
		return FALSE;	
	}

	GtkWidget * subwidget=data->subwidget;

	g_object_ref(data->hover);
	gtk_container_remove(widget,gtk_bin_get_child(widget));
	gtk_container_add(widget,data->hover);		
	gtk_widget_show_all(data->hover);
	g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,subwidget);		
	gtk_widget_show_all(subwidget);

	gint x,y;

	gdk_window_get_origin (GTK_WIDGET (G_applet)->window,&x, &y);    

	/*Ugly Hack ahead*/
	int widget_ypos=widget->allocation.y;

	if ( G_height >= G_Fixed->allocation.height	)
	{
		gtk_fixed_move(G_Fixed,subwidget,G_x,G_cairo_menu_conf.text_size);
	}
	else if ( !(  (widget_ypos >= G_y) && (widget_ypos <= G_y + subwidget->allocation.height) ))
	{		
		if (G_Fixed->allocation.height-G_height < widget_ypos)
		{
			gtk_fixed_move(G_Fixed,subwidget,G_x,G_Fixed->allocation.height-G_height);
		}
		else if ( widget_ypos + subwidget->allocation.height < G_Fixed->allocation.height)
		{
			gtk_fixed_move(G_Fixed,subwidget,G_x,widget_ypos);
		}				
		else if (widget_ypos + G_cairo_menu_conf.text_size*1.6 - G_height > 0)
		{
			gtk_fixed_move(G_Fixed,subwidget,G_x,widget_ypos + G_cairo_menu_conf.text_size*1.6 - G_height);
		}
		else if ( subwidget->allocation.height > widget_ypos)
		{
			gtk_fixed_move(G_Fixed,subwidget,G_x,0);
		}
		else
		{
			assert(0);
		}
		
	}
    pos_dialog(G_mainwindow);    
	gtk_fixed_move(G_Fixed,G_toplevel,0,G_mainwindow->allocation.height-G_toplevel->allocation.height);		    
	return TRUE;
}

static gboolean _enter_notify_event_entry(GtkWidget *widget,GdkEventCrossing *event,Mouseover_data *data)  
{

	if ( (gtk_bin_get_child(widget)!=data->misc) && ! G_repression)
	{
		GtkWidget * subwidget=data->subwidget;

		g_object_ref(data->hover);
		gtk_container_remove(widget,gtk_bin_get_child(widget) );
		gtk_container_add(widget,data->hover);		
		gtk_widget_show_all(data->hover);
		if (subwidget != G_toplevel)
		{
			g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,subwidget);		
		}		
		else
		{	
			g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL); 	
		}		
		gtk_widget_show_all(subwidget);		
		return TRUE;		
	}		
	return FALSE;
}

static gboolean _leave_notify_event(GtkWidget *widget,GdkEventCrossing *event,Mouseover_data *data)  
{
	if ( (gtk_bin_get_child(widget)!=data->misc) && ! G_repression)
	{
		gtk_widget_show(data->subwidget);
		g_object_ref(data->normal);
		gtk_container_remove(widget,gtk_bin_get_child(widget));
		gtk_container_add(widget,data->normal);		
		gtk_widget_show_all(data->normal);
		return TRUE;		
	}
	return FALSE;
}

static gboolean _leave_notify_event_entry(GtkWidget *widget,GdkEventCrossing *event,Mouseover_data *data)  
{
	if ((gtk_bin_get_child(widget)!=data->misc) &&! G_repression)
	{
		gtk_widget_show(data->subwidget);
		g_object_ref(data->normal);
		gtk_container_remove(widget,gtk_bin_get_child(widget));
		gtk_container_add(widget,data->normal);		
		gtk_widget_show_all(data->normal);
		return TRUE;		
	}
	return FALSE;
}
 
static gboolean _button_clicked_event(GtkWidget *widget,GdkEventButton *event,Menu_list_item * menu_item) 
{
	GError *err=NULL;
	g_spawn_command_line_async(menu_item->exec,&err);
	gtk_widget_hide(G_Fixed->parent);
	return TRUE;
}          

static gboolean _button_clicked_event_search(GtkWidget *widget,GdkEventButton *event,Mouseover_data *data) 
{
	g_list_foreach(GTK_FIXED(G_Fixed)->children,_fixup_menus,NULL); 
	gtk_widget_show(data->misc);
	g_object_ref(gtk_bin_get_child(widget));
	gtk_container_remove(widget,gtk_bin_get_child(widget));
	gtk_container_add(widget,data->misc);		
	gtk_widget_show_all(data->misc);
	G_repression=TRUE;
	gtk_widget_grab_focus(data->misc);
	return TRUE;
}    

void hide_search(void)
{
	if (G_Search)
	{
		if (gtk_bin_get_child(G_Search->aux) == G_Search->misc)
		{
			g_object_ref(gtk_bin_get_child(G_Search->aux));
			gtk_container_remove(G_Search->aux,gtk_bin_get_child(G_Search->aux));
			gtk_container_add(G_Search->aux,G_Search->normal);		
			gtk_widget_show_all(G_Search->normal);			
		}			
	}
}
 

static gboolean _focus_out_search(GtkWidget *widget, GdkEventButton *event, Mouseover_data *data)
{
	printf("_focus_out_search\n");
	hide_search();
	G_repression=FALSE;
    return FALSE;
}



int activate_search(GtkWidget *w,Menu_list_item * menu_item)
{
	GError *err=NULL;
	char  *cmd;

	G_repression=FALSE;
	cmd=g_malloc(strlen(G_cairo_menu_conf.search_cmd) + strlen(gtk_entry_get_text (w)) +4 );
	strcpy(cmd,G_cairo_menu_conf.search_cmd);
	strcat(cmd," '");	
	strcat(cmd,gtk_entry_get_text (w) );
	strcat(cmd,"'");		
	gtk_widget_hide(G_Fixed->parent);
	g_spawn_command_line_async(cmd,&err);    
	g_free(cmd);	
	return FALSE;
}
static gboolean _button_clicked_ignore(GtkWidget *widget,GdkEventButton *event,Menu_list_item * menu_item) 
{
	G_repression=FALSE;
	return TRUE;
}          


static gboolean _scroll_event(GtkWidget *widget,GdkEventMotion *event,GtkWidget * box) 
{
	GtkBoxChild *boxchild;
	if (event->type == GDK_SCROLL)
	{

	 	if (event->state & GDK_SHIFT_MASK)
		{
			boxchild=g_list_first(GTK_BOX(box)->children)->data;
			assert(boxchild);
			GTK_IS_WIDGET (boxchild->widget);			
			gtk_box_reorder_child (GTK_BOX(box),boxchild->widget,-1);
		}
		else
		{
			boxchild=g_list_last(GTK_BOX(box)->children)->data;
			assert(boxchild);
			GTK_IS_WIDGET (boxchild->widget);
			gtk_box_reorder_child (GTK_BOX(box),boxchild->widget,0);			
		}
		gtk_widget_show_all(widget);
	}
	return TRUE;
}     

                                              
void render_menu_widgets(Menu_list_item * menu_item,GtkWidget * box)
{
	static Xpos=0;
//	gtk_widget_show_all(box);
	switch (menu_item->item_type)
	{
		case MENU_ITEM_DIRECTORY:
			{
				GtkWidget *newbox;
				render_directory(menu_item);
//				gtk_widget_set_tooltip_markup(menu_item->widget,menu_item->comment);				
				newbox=gtk_vbox_new(FALSE,0);
				gtk_widget_set_app_paintable(newbox ,TRUE);
				Xpos=Xpos+G_cairo_menu_conf.text_size*G_cairo_menu_conf.menu_item_text_len*4/5;//FIXME
				gtk_fixed_put(G_Fixed,newbox,Xpos,0);
//				gtk_widget_show_all(newbox);   						
				g_slist_foreach(menu_item->sublist,render_menu_widgets,newbox);				

				Mouseover_data	*data;				
				data=g_malloc(sizeof(Mouseover_data));
				data->subwidget=newbox;
				data->normal=menu_item->normal;
				data->hover=menu_item->hover;
				data->misc=NULL;
				g_signal_connect(menu_item->widget, "enter-notify-event", G_CALLBACK (_enter_notify_event), data);
				g_signal_connect(menu_item->widget, "leave-notify-event", G_CALLBACK (_leave_notify_event), data);
				g_signal_connect(newbox, "scroll-event" , G_CALLBACK (_scroll_event),newbox);
				g_signal_connect(menu_item->widget, "button-press-event",G_CALLBACK (_button_clicked_ignore),data);				
				g_tree_insert(G_cairo_menu_conf.submenu_deps,newbox,box);				
				Xpos=Xpos-G_cairo_menu_conf.text_size*G_cairo_menu_conf.menu_item_text_len*4/5;//FIXME
			}				
			break;
		case MENU_ITEM_ENTRY:
			{
				render_entry(menu_item);
				gtk_widget_set_tooltip_markup(menu_item->widget,menu_item->comment);
				Mouseover_data	*data;				
				data=g_malloc(sizeof(Mouseover_data));
				data->subwidget=box;
				data->normal=menu_item->normal;
				data->hover=menu_item->hover;
				data->misc=NULL;
				g_signal_connect(menu_item->widget, "enter-notify-event", G_CALLBACK (_enter_notify_event_entry), data);
				g_signal_connect(menu_item->widget, "leave-notify-event", G_CALLBACK (_leave_notify_event_entry), data);
			
				g_signal_connect (G_OBJECT (menu_item->widget), "button-press-event",G_CALLBACK (_button_clicked_event), menu_item);
			}				
			break;			
		case MENU_ITEM_SEARCH:
			{
				render_search(menu_item);
				Mouseover_data	*data;				
				data=g_malloc(sizeof(Mouseover_data));
				data->subwidget=box;
				data->normal=menu_item->normal;
				data->hover=menu_item->hover;
				data->misc=menu_item->search_entry;
				data->aux=menu_item->widget;				
				G_Search=data;
				g_signal_connect(menu_item->widget, "enter-notify-event", G_CALLBACK (_enter_notify_event_entry), data);
				g_signal_connect(menu_item->widget, "leave-notify-event", G_CALLBACK (_leave_notify_event_entry), data);
				g_signal_connect (G_OBJECT(menu_item->widget), "button-press-event",G_CALLBACK (_button_clicked_event_search),data);
				g_signal_connect (G_OBJECT(data->misc), "focus-out-event",G_CALLBACK (_focus_out_search),data);
 				g_signal_connect (G_OBJECT(data->misc), "activate",G_CALLBACK (activate_search), menu_item);				
 				
			}	
			break;				
		case MENU_ITEM_BLANK:
			{
			
			}
		default:
			menu_item->widget=NULL;							
	}	
	if (menu_item->widget)
	{	
		gtk_box_pack_start(box,menu_item->widget,FALSE,FALSE,0);
	}
}
