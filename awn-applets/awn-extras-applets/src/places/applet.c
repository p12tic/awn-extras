/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
 # Copyright (c) 2007 	Mark Lee           			<avant-wn@lazymalevolence.com>
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

#ifdef  USE_AWN_DESKTOP_AGNOSTIC
#include <libawn/awn-vfs.h>
#else
#include <libgnomevfs/gnome-vfs-utils.h>
#endif

#ifdef  USE_AWN_DESKTOP_AGNOSTIC
#include <libawn/awn-config-client.h>
#include <libawn/awn-vfs.h>
 
#define CONFIG_KEY(key) key
#else
#include <libgnomevfs/gnome-vfs.h>
#include <libgnomevfs/gnome-vfs-utils.h>
 
#include <gconf/gconf-client.h>	

#define GCONF_MENU "/apps/avant-window-navigator/applets/places"

#define CONFIG_KEY(key) GCONF_MENU "/" key
#endif

#define CONFIG_NORMAL_BG     CONFIG_KEY("bg_normal_colour")
#define CONFIG_NORMAL_FG     CONFIG_KEY("text_normal_colour")
#define CONFIG_HOVER_BG      CONFIG_KEY("bg_hover_colour")
#define CONFIG_HOVER_FG      CONFIG_KEY("text_hover_colour")

#define CONFIG_TEXT_SIZE     CONFIG_KEY("text_size")

#define CONFIG_MENU_GRADIENT CONFIG_KEY("menu_item_gradient_factor")

#define CONFIG_FILEMANAGER   CONFIG_KEY("filemanager")
#define CONFIG_APPLET_ICON   CONFIG_KEY("applet_icon")

#define CONFIG_SHOW_TOOLTIPS CONFIG_KEY("show_tooltips")
#define CONFIG_BORDER_COLOUR CONFIG_KEY("border_colour")
#define CONFIG_BORDER_WIDTH  CONFIG_KEY("border_width")

#define CONFIG_HONOUR_GTK    CONFIG_KEY("honour_gtk")

#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <gtk/gtk.h>
#include <glib/gi18n.h>
#include <string.h>


typedef struct
{
	AwnColor	base;
	AwnColor	text;	

}Menu_item_color;

typedef struct
{
	AwnApplet 			*applet	;
	GdkPixbuf 			*icon;	
	GtkWidget			*mainwindow;
	GtkWidget			*vbox;

	Menu_item_color		normal_colours;
	Menu_item_color		hover_colours;
	double				menu_item_gradient_factor;

	gboolean			honour_gtk;
	
	AwnColor			border_colour;
	gint				border_width;	

	gint				text_size;
	gint				max_width;

	
	GSList				*menu_list;	

	gchar				*applet_icon_name;
	gboolean			show_tooltips;

	gchar				*file_manager;

#ifdef USE_AWN_DESKTOP_AGNOSTIC
	AwnConfigClient		*config;
#else
	GConfClient			*config;
#endif;
	
}Places;


typedef struct
{
	gchar 	*text;
	gchar	*exec;
	gchar	*icon;	
	gchar	*comment;

	
	GtkWidget	*widget;
	GtkWidget	*normal;
	GtkWidget	*hover;			
	
	Places		*places;
	
}Menu_Item;

static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event, Places *places);
static gboolean _show_prefs (GtkWidget *widget, GdkEventButton *event, Places * places);

static GSList* get_places(Places * places);
static void render_places(Places * places);
static char * awncolor_to_string(AwnColor * colour);
static void free_menu_list_item(Menu_Item * item,gpointer null);


static char * awncolor_to_string(AwnColor * colour)
{

	return g_strdup_printf("%02x%02x%02x%02x",
								(unsigned int) round((colour->red*255)),
								(unsigned int) round((colour->green*255)),
								(unsigned int) round((colour->blue*255)),
								(unsigned int) round((colour->alpha*255))
								);
}

static AwnColor GdkColor2AwnColor( GdkColor * gdk_color)
{
	AwnColor colour;
	colour.red=gdk_color->red/65535.0;
	colour.green=gdk_color->green/65535.0;    
	colour.blue=gdk_color->blue/65535.0;
	colour.alpha=0.9;  
	return colour;
}

static void free_menu_list_item(Menu_Item * item,gpointer null)
{
	if (item->text)
		g_free(item->text);
	if (item->icon)
		g_free(item->icon);
	if 	(item->exec)
		g_free(item->exec);
	if 	(item->comment)
		g_free(item->comment);
	if (item->widget)
		gtk_widget_destroy(item->widget);
	if (item->normal)
		gtk_widget_destroy(item->normal);
	if (item->hover)		
		gtk_widget_destroy(item->hover);
	item->text=NULL;
	item->icon=NULL;
	item->exec=NULL;	
	item->comment=NULL;		
	item->widget=NULL;
	item->hover=NULL;	
	item->normal=NULL;		

}
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

void init_config(Places * places)
{
#ifdef AWN_USE_DESKTOP_AGNOSTIC
	places->config = awn_config_client_new_for_applet ("places");
#else
	places->config = gconf_client_get_default();
#endif

	config_get_color (places->config, CONFIG_NORMAL_BG,     &places->normal_colours.base);
	config_get_color (places->config, CONFIG_NORMAL_FG,     &places->normal_colours.text);
	config_get_color (places->config, CONFIG_HOVER_BG,      &places->hover_colours.base);
	config_get_color (places->config, CONFIG_HOVER_FG,      &places->hover_colours.text);
	config_get_color (places->config, CONFIG_BORDER_COLOUR, &places->border_colour);

#ifdef AWN_USE_DESKTOP_AGNOSTIC
	places->border_width              = awn_config_client_get_int   (places->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, CONFIG_BORDER_WIDTH,  NULL);
	places->text_size                 = awn_config_client_get_int   (places->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, CONFIG_TEXT_SIZE,     NULL);
	places->menu_item_gradient_factor = awn_config_client_get_float (places->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, CONFIG_MENU_GRADIENT, NULL);
	places->show_tooltips             = awn_config_client_get_bool  (places->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, CONFIG_SHOW_TOOLTIPS, NULL);
	places->honour_gtk                = awn_config_client_get_bool  (places->config, AWN_CONFIG_CLIENT_DEFAULT_GROUP, CONFIG_HONOUR_GTK,    NULL);
#else
	places->border_width              = gconf_client_get_int   (places->config, CONFIG_BORDER_WIDTH,  NULL);
	places->text_size                 = gconf_client_get_int   (places->config, CONFIG_TEXT_SIZE,     NULL);
	places->menu_item_gradient_factor = gconf_client_get_float (places->config, CONFIG_MENU_GRADIENT, NULL);
	places->show_tooltips             = gconf_client_get_bool  (places->config, CONFIG_SHOW_TOOLTIPS, NULL);
	places->honour_gtk                = gconf_client_get_bool  (places->config, CONFIG_HONOUR_GTK,    NULL);
#endif

	config_get_string (places->config, CONFIG_FILEMANAGER, &(places->file_manager));
	config_get_string (places->config, CONFIG_APPLET_ICON, &(places->applet_icon_name));
	if (places->honour_gtk)
	{  	  
		GtkWidget *top_win=GTK_WIDGET(places->applet);
		places->normal_colours.base=GdkColor2AwnColor(&top_win->style->base[0] );
		places->normal_colours.text=GdkColor2AwnColor(&top_win->style->fg[0] );
		places->hover_colours.base=GdkColor2AwnColor(&top_win->style->base[GTK_STATE_PRELIGHT] );
		places->hover_colours.text=GdkColor2AwnColor(&top_win->style->fg[GTK_STATE_PRELIGHT]);
		places->border_colour=GdkColor2AwnColor(&top_win->style->text_aa[0]);
		places->menu_item_gradient_factor=1.0;
	}
}

#ifdef AWN_USE_DESKTOP_AGNOSTIC

static void save_config(Places * places)
{

}

#else

static void save_config(Places * places)
{
	gchar * svalue;
	svalue=awncolor_to_string(&places->normal_colours.base);	
    gconf_client_set_string(places->config, CONFIG_NORMAL_BG,svalue, NULL );
    g_free(svalue);
    svalue = awncolor_to_string(&places->normal_colours.text);
	gconf_client_set_string(places->config, CONFIG_NORMAL_FG, svalue, NULL );
    g_free(svalue);     	
    svalue = awncolor_to_string(&places->hover_colours.base);
	gconf_client_set_string(places->config, CONFIG_HOVER_BG, svalue, NULL );
    g_free(svalue);     	
    svalue = awncolor_to_string(&places->hover_colours.text);
	gconf_client_set_string(places->config, CONFIG_HOVER_FG, svalue, NULL );
    g_free(svalue);     	
    gconf_client_set_int   (places->config, CONFIG_TEXT_SIZE,places->text_size ,NULL);        
    gconf_client_set_float (places->config, CONFIG_MENU_GRADIENT,places->menu_item_gradient_factor,NULL);        
    gconf_client_set_string(places->config, CONFIG_FILEMANAGER, places->file_manager, NULL );
    gconf_client_set_string(places->config, CONFIG_APPLET_ICON,places->applet_icon_name, NULL );
    gconf_client_set_bool  (places->config, CONFIG_HONOUR_GTK,places->honour_gtk,NULL);        
	gconf_client_set_bool  (places->config, CONFIG_SHOW_TOOLTIPS,places->show_tooltips,NULL);    
	gconf_client_set_int   (places->config, CONFIG_BORDER_WIDTH,places->border_width,NULL);    	
    svalue = awncolor_to_string(&places->border_colour);
	gconf_client_set_string(places->config, CONFIG_BORDER_COLOUR, svalue, NULL );
    g_free(svalue);     		
}

#endif

static void _do_update_places(Places * places)
{
	g_slist_foreach (places->menu_list,free_menu_list_item,NULL);	
	g_slist_free(places->menu_list);
	places->menu_list=NULL;
	render_places(places);	//FIXME
	
}

static gboolean _do_update_places_wrapper(Places * places)
{
	_do_update_places(places);
	return FALSE;	
}	


//===========================================================================


#ifdef USE_AWN_DESKTOP_AGNOSTIC
static void monitor_places_callback (AwnVfsMonitor *monitor,
                                     gchar *monitor_path,
                                     gchar *event_path,
                                     AwnVfsMonitorEvent event,
                                     Places *places)
{
	_do_update_places (places);
}

static void monitor_places (Places *places)
{
	AwnVfsMonitor *monitor;

	const gchar *home_dir = g_getenv ("HOME");
	if (!home_dir) {
		home_dir = g_get_home_dir ();
	}
	gchar *filename = g_build_filename (home_dir, ".gtk-bookmarks", NULL);
	monitor = awn_vfs_monitor_add (filename, AWN_VFS_MONITOR_FILE, (AwnVfsMonitorCallback)monitor_places_callback, places);
    if (!monitor) {
        g_warning ("Attempt to monitor '%s' failed!\n", filename);
    }

	g_free (filename);
}

#else

static void monitor_places_callback(GnomeVFSMonitorHandle *handle,
                                 const gchar *monitor_uri,
                                 const gchar *info_uri,
                                 GnomeVFSMonitorEventType event_type,
                                 Places * places)
{
	_do_update_places(places);
}                                 

static void monitor_places(Places * places)
{
	GnomeVFSMonitorHandle * handle;

	const char *homedir = g_getenv ("HOME");
	if (!homedir)
		homedir = g_get_home_dir ();
	gchar *  filename=g_strdup_printf("%s/.gtk-bookmarks",homedir); 			
	if ( gnome_vfs_monitor_add(&handle,filename,GNOME_VFS_MONITOR_FILE,
                               monitor_places_callback,places) != GNOME_VFS_OK)
	{
		printf("attempt to monitor '%s' failed \n",filename);
	}                                                                                          
	g_free(filename);                                                                                                 
}                                                         
#endif

#if !defined(USE_AWN_DESKTOP_AGNOSTIC) || defined(LIBAWN_USE_GNOME)
static void _vfs_changed(GnomeVFSDrive  *drive,GnomeVFSVolume *volume,Places * places)
{
	g_timeout_add(500,_do_update_places_wrapper,places);
}

static void _fillin_connected(GnomeVFSDrive * drive,Places * places)
{
 	
	Menu_Item * item;	
	gchar * dev_path;	
	gchar *	mount_point;
	GnomeVFSVolume* volume;		
	
	volume = gnome_vfs_drive_get_mounted_volume (drive);
	if (!volume)
	{
		return;
	}
	item=g_malloc(sizeof(Menu_Item));	
	
	item->places=places;
	item->text = gnome_vfs_drive_get_display_name (drive);
	item->icon = gnome_vfs_drive_get_icon (drive);
	// FIXME gnome_vfs_drive_get_mounted_volume is deprecated.	
	
	mount_point=gnome_vfs_volume_get_activation_uri(volume);
	item->exec=g_strdup_printf("%s %s",places->file_manager,mount_point);

	dev_path=gnome_vfs_drive_get_device_path(gnome_vfs_volume_get_drive(volume));
	item->comment=g_strdup_printf("%s\n%s\n%s",item->text,mount_point,dev_path ) ;
	places->menu_list=g_slist_append(places->menu_list,item);

	g_free(mount_point);	
	g_free(dev_path);
	gnome_vfs_volume_unref (volume)	;
}	
#elif defined(LIBAWN_USE_XFCE)
static void _vfs_changed (ThunarVfsVolumeManager *volume_manager, ThunarVfsVolume *volume, Places *places)
{
	g_timeout_add (500, _do_update_places_wrapper, places);
}

static void _fillin_connected (ThunarVfsVolume *volume, Places *places)
{
	Menu_Item *item;
	gchar *mount_point;

	if (thunar_vfs_volume_get_status (volume) != THUNAR_VFS_VOLUME_STATUS_MOUNTED) {
		return;
	}

	mount_point = thunar_vfs_path_dup_string (thunar_vfs_volume_get_mount_point (volume));
	item = g_malloc (sizeof (Menu_Item));
	item->places = places;
	item->text = g_strdup (thunar_vfs_volume_get_name (volume));
	item->icon = g_strdup (thunar_vfs_volume_lookup_icon_name (volume, gtk_icon_theme_get_default ()));
	item->exec = g_strdup_printf ("%s %s", places->file_manager, mount_point);
	item->comment = g_strdup_printf ("%s\n%s", item->text, mount_point);
	places->menu_list = g_slist_append (places->menu_list, item);
	g_free (mount_point);
}
#else
static void _vfs_volume_changed (GVolumeMonitor *monitor, GVolume *volume, Places *places)
{
	g_timeout_add (500, _do_update_places_wrapper, places);
}

static void _vfs_drive_changed (GVolumeMonitor *monitor, GDrive *drive, Places *places)
{
	g_timeout_add (500, _do_update_places_wrapper, places);
}

static void _fillin_connected (GVolume *volume, Places *places)
{
	Menu_Item *item;
	GIcon *icon;
	gchar *mount_point = g_file_get_path (g_volume_get_root (volume));
	item = g_malloc (sizeof (Menu_Item));
	item->places = places;
	item->text = g_volume_get_name (volume);
	icon = g_volume_get_icon (icon);
	if (G_IS_THEMED_ICON (icon)) {
		const gchar * const *icon_names = g_themed_icon_get_names (G_THEMED_ICON (icon));
		if (g_strv_length (icon_names) > 0) {
			item->icon = g_strdup (icon_names[0]);
		}
		g_strfreev (icon_names);
	} else if (G_IS_FILE_ICON (icon)) {
		item->icon = g_file_get_path (g_file_icon_get_file (G_FILE_ICON (icon)));
	} else {
		g_warning ("The GIcon implementation returned by g_volume_get_icon() is unsupported!");
	}
	g_free (icon);
	item->exec = g_strdup_printf ("%s %s", places->file_manager, mount_point);
	item->comment = g_strdup_printf ("%s\n%s", item->text, mount_point);
	places->menu_list = g_slist_append (places->menu_list, item);

	g_free (mount_point);
}
#endif

static GSList* get_places(Places * places)
{
	
	Menu_Item	*item=NULL;
		
	item=g_malloc(sizeof(Menu_Item));	
	item->text=g_strdup("Home");
	item->icon=g_strdup("stock_home");
	const gchar *homedir = g_getenv ("HOME");
	if (!homedir)
 		homedir = g_get_home_dir ();
	item->exec=g_strdup_printf("%s %s",places->file_manager,homedir);			
	item->comment=g_strdup("Your Home Directory");	
	item->places=places;
	places->menu_list=g_slist_append(places->menu_list,item);
	
	item=g_malloc(sizeof(Menu_Item));	
	item->text=g_strdup("File System");
	item->icon=g_strdup("stock_folder");
	item->exec=g_strdup_printf("%s /",places->file_manager);			
	item->comment=g_strdup("Root File System");
	item->places=places;	
	places->menu_list=g_slist_append(places->menu_list,item);

#if !defined(AWN_USE_DESKTOP_AGNOSTIC) || defined(LIBAWN_USE_GNOME)
	static GnomeVFSVolumeMonitor* vfsvolumes=NULL;
	if (!vfsvolumes)
	{	
	/*this is structured like this because get_places() is
	invoked any time there is a change in places... only want perform
	these actions once.*/
		vfsvolumes=gnome_vfs_get_volume_monitor(); 
		g_signal_connect (G_OBJECT(vfsvolumes),"volume-mounted",G_CALLBACK (_vfs_changed),places);
		g_signal_connect (G_OBJECT(vfsvolumes),"volume-unmounted",G_CALLBACK (_vfs_changed),places);
		g_signal_connect (G_OBJECT(vfsvolumes),"drive-disconnected" ,G_CALLBACK (_vfs_changed),places);
		g_signal_connect (G_OBJECT(vfsvolumes),"drive-connected",G_CALLBACK (_vfs_changed),places);		
		
		monitor_places(places);	//Monitor bookmark file
	}		
	GList *connected=gnome_vfs_volume_monitor_get_connected_drives(vfsvolumes);	
	if (connected)
		g_list_foreach(connected,_fillin_connected,places);
	g_list_free(connected);
#elif defined(LIBAWN_USE_XFCE)
	/* monitor volumes */
	static ThunarVfsVolumeManager *volume_manager=NULL;
	
	if (!volume_manager)
	{
		volume_manager = thunar_vfs_volume_manager_get_default ();
		g_signal_connect (G_OBJECT (volume_manager), "volume-mounted",   G_CALLBACK (_vfs_changed), places);
		g_signal_connect (G_OBJECT (volume_manager), "volume-unmounted", G_CALLBACK (_vfs_changed), places);
		g_signal_connect (G_OBJECT (volume_manager), "volume-added",     G_CALLBACK (_vfs_changed), places);
		g_signal_connect (G_OBJECT (volume_manager), "volume-removed",   G_CALLBACK (_vfs_changed), places);
		monitor_places (places); /* monitor bookmark file */
	}		
	GList *volumes = thunar_vfs_volume_manager_get_volumes (volume_manager);
	if (volumes) {
		g_list_foreach (volumes, _fillin_connected, places);
	}
	/* thunar-vfs docs say: "The returned list is owned by manager and should therefore considered constant in the caller." */	
#else
	/* monitor volumes */
	static GVolumeMonitor volume_monitor=NULL;
	
	if (!volume_manager)
	{	
		volume_monitor = g_volume_monitor_get ();
		g_signal_connect (G_OBJECT (volume_monitor), "volume-mounted",     G_CALLBACK (_vfs_volume_changed),places);
		g_signal_connect (G_OBJECT (volume_monitor), "volume-unmounted",   G_CALLBACK (_vfs_volume_changed),places);
		g_signal_connect (G_OBJECT (volume_monitor), "drive-disconnected", G_CALLBACK (_vfs_drive_changed),places);
		g_signal_connect (G_OBJECT (volume_monitor), "drive-connected",    G_CALLBACK (_vfs_drive_changed),places);
		monitor_places (places);		
	}		
	GList *volumes = g_volume_monitor_get_mounted_volumes (volume_monitor);
	if (volumes) {
		g_list_foreach (volumes, _fillin_connected, places);
	}
	g_list_free (volumes);

#endif
//bookmarks	
	FILE*	handle;
	gchar *  filename=g_strdup_printf("%s/.gtk-bookmarks",homedir);
	handle=g_fopen(filename,"r");
	if (handle)
	{
		char *	line=NULL;
		char *  len=0;
		while ( getline(&line,&len,handle) != -1)	
		{
				char *p;
				p=line+strlen(line);
				if (p!=line)
				{
					while ( !isalpha(*p) && (p!=line))
					{
						*p='\0';
						p--;
					}							
					while( (*p!='/') && (p!=line) )
						p--;
					if (p!=line)
					{
						char * tmp;
						p++;
						item=g_malloc(sizeof(Menu_Item));	

						for(tmp=p; *tmp && (*tmp!=' ');tmp++);
						if (*tmp==' ')
						{
							*tmp='\0';
							p=tmp+1;
						}
						item->text=g_strdup(p);
						item->icon=g_strdup("stock_folder");
						item->exec=g_strdup_printf("%s %s",places->file_manager,line);			
						item->comment=g_strdup(line);
						item->places=places;						
						places->menu_list=g_slist_append(places->menu_list,item);						
					}												
				}
				free(line);
				line=NULL;
		}
		fclose(handle);
		g_free(filename);
	}		
	else
	{
		printf("Unable to open bookmark file: %s/.gtk-bookmarks\n",homedir);
	}	
}



/* =================================================================

Rendering/events stuff follows

----------------------------------------------------------------*/


GtkWidget * build_menu_widget(Places * places,Menu_item_color * mic,  char * text,GdkPixbuf *pbuf,GdkPixbuf *pover,int max_width)
{
    static cairo_t *cr = NULL;   
    GtkWidget * widget;
    GdkScreen* pScreen;        
	GdkPixmap * pixmap; 
	GdkColormap*	cmap;
    cairo_pattern_t *gradient=NULL;
    cairo_text_extents_t    extents;      
    gint pixmap_width=max_width;
    gint pixmap_height=places->text_size*1.6;
    if (pbuf)
    	if(gdk_pixbuf_get_height(pbuf) !=places->text_size)
    	{
	    	pbuf=gdk_pixbuf_scale_simple(pbuf,places->text_size,places->text_size,GDK_INTERP_HYPER);  
		}	    	
		else
		{	
			gdk_pixbuf_ref(pbuf);
		}
	if (pover)	    
    	if(gdk_pixbuf_get_height(pover) !=places->text_size*0.7)
    	{
		    pover=gdk_pixbuf_scale_simple(pover,places->text_size*0.7,places->text_size*0.7,GDK_INTERP_HYPER);  
		}
		else
		{
			gdk_pixbuf_ref(pover);		
		}
    pixmap=gdk_pixmap_new(NULL, pixmap_width,places->text_size*1.6,32);   //FIXME
    widget=gtk_image_new_from_pixmap(pixmap,NULL);      
    pScreen = gtk_widget_get_screen ( GTK_WIDGET(places->applet) );
    cmap = gdk_screen_get_rgba_colormap (pScreen);
    if (!cmap)
            cmap = gdk_screen_get_rgb_colormap (pScreen); 
    gdk_drawable_set_colormap(pixmap,cmap);       
    cr=gdk_cairo_create(pixmap);
    cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(cr);
	cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);	
	gradient = cairo_pattern_create_linear(0, 0, 0,places->text_size*1.6);            
	cairo_pattern_add_color_stop_rgba(gradient, 0,  mic->base.red,mic->base.green,mic->base.blue, 
							mic->base.alpha*places->menu_item_gradient_factor);
	cairo_pattern_add_color_stop_rgba(gradient, 0.2, mic->base.red,mic->base.green,mic->base.blue, 
										mic->base.alpha);
	cairo_pattern_add_color_stop_rgba(gradient, 0.8, mic->base.red,mic->base.green,mic->base.blue, 
										mic->base.alpha);											
	cairo_pattern_add_color_stop_rgba(gradient, 1,mic->base.red,mic->base.green,mic->base.blue, 
								mic->base.alpha*places->menu_item_gradient_factor);
	cairo_set_source(cr, gradient);    
   	cairo_paint(cr);
	cairo_set_operator (cr, CAIRO_OPERATOR_OVER);	   	
   	if (pbuf)
   	{
		gdk_cairo_set_source_pixbuf(cr,pbuf,places->text_size*0.3,places->text_size*0.2);   		
	    cairo_rectangle(cr,0,0,places->text_size*1.3,places->text_size*1.2);	    						
		cairo_fill(cr);
		if (pover)
		{
			gdk_cairo_set_source_pixbuf(cr,pover,places->text_size*0.5,places->text_size*0.4);   		
			cairo_rectangle(cr,0,0,places->text_size*1.3,places->text_size*1.2);	    						
			cairo_fill(cr);		
		}
	}	
	else if (pover)
	{
		gdk_cairo_set_source_pixbuf(cr,pover,places->text_size*0.3,places->text_size*0.2);   		
		cairo_rectangle(cr,0,0,places->text_size*1.3,places->text_size*1.2);	    						
		cairo_fill(cr);		
	}		
	if (places->border_width>0 )
	{
	    cairo_set_source_rgba (cr, places->border_colour.red,  places->border_colour.green,
	    						   places->border_colour.blue, places->border_colour.alpha);		
		cairo_set_line_width(cr,places->border_width);   		    							
   		cairo_move_to(cr,places->border_width/2,0);
   		cairo_line_to(cr,places->border_width/2,pixmap_height);   		
   		cairo_stroke(cr);
   		cairo_move_to(cr,pixmap_width-places->border_width/2,0);
   		cairo_line_to(cr,pixmap_width-places->border_width/2,pixmap_height);   		
   		cairo_stroke(cr);   		
	}
    cairo_set_source_rgba (cr, mic->text.red,mic->text.green,mic->text.blue, mic->text.alpha);
    cairo_set_operator (cr, CAIRO_OPERATOR_OVER);	   	
   	cairo_move_to(cr,places->text_size*1.4 , places->text_size*1.1);
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size (cr,places->text_size  );  
    
    char * buf;
    int  nul_pos=strlen(text);
    buf=g_malloc(nul_pos+3);
    strcpy(buf,text);
	cairo_text_extents(cr,buf,&extents);   
	while ((nul_pos>5) && (extents.width +  places->text_size*1.3 > pixmap_width-places->text_size) )
	{
		nul_pos--;				
		buf[nul_pos]='\0';
		strcat(buf,"...");	/*good enough*/
		cairo_text_extents(cr,buf,&extents);   		
	}			
   	cairo_show_text(cr,buf);    	
   	g_free(buf);
	cairo_destroy(cr);
	if (gradient)
		cairo_pattern_destroy(gradient);
	if (pbuf)
		g_object_unref(pbuf);	
	if (pover)
		g_object_unref(pover);
	return widget;
}

void render_entry(Menu_Item *entry )
{
	Places * places=entry->places;
	int max_width=places->max_width;
	GtkIconTheme*  g;  	
	GdkPixbuf *pbuf=NULL;
	gchar * filename;	
    g=gtk_icon_theme_get_default();
    pbuf=gtk_icon_theme_load_icon(g,entry->icon,places->text_size,0,NULL);
	if (!pbuf)
	{
		pbuf=gdk_pixbuf_new_from_file_at_size(entry->icon,-1,places->text_size,NULL);		
	}		
	if (!pbuf)
	{
		pbuf=gtk_icon_theme_load_icon(g,entry->text,places->text_size,0,NULL);	
	}		
	if (!pbuf)
	{
		pbuf=gtk_icon_theme_load_icon(g,entry->exec,places->text_size,0,NULL);		
	}			
	if (!pbuf)
	{
		filename=g_strdup_printf("/usr/share/pixmaps/%s",entry->icon);
		pbuf=gdk_pixbuf_new_from_file_at_size(filename,-1,places->text_size,NULL);		
		g_free(filename);
	}		
	if (!pbuf)
	{
		filename=g_strdup_printf("/usr/share/pixmaps/%s.svg",entry->icon);
		pbuf=gdk_pixbuf_new_from_file_at_size(filename,-1,places->text_size,NULL);		
		g_free(filename);
	}	
	if (!pbuf)
	{
		filename=g_strdup_printf("/usr/share/pixmaps/%s.png",entry->icon);
		pbuf=gdk_pixbuf_new_from_file_at_size(filename,-1,places->text_size,NULL);		
		g_free(filename);
	}	
	if (!pbuf)
	{
		filename=g_strdup_printf("/usr/share/pixmaps/%s.xpm",entry->icon);
		pbuf=gdk_pixbuf_new_from_file_at_size(filename,-1,places->text_size,NULL);		
		g_free(filename);
	}		
	if (!pbuf)
	{
		pbuf=gtk_icon_theme_load_icon(g,"applications-other",places->text_size,0,NULL);		
	}	
	if (!pbuf)
	{
		pbuf=gtk_icon_theme_load_icon(g,"application-x-executable",places->text_size,0,NULL);		
	}			
	entry->widget=gtk_event_box_new();
	gtk_event_box_set_visible_window(entry->widget,FALSE);
	gtk_event_box_set_above_child (entry->widget,TRUE);	
	entry->normal=build_menu_widget(places,&places->normal_colours,entry->text,pbuf,NULL,max_width);
	entry->hover=build_menu_widget(places,&places->hover_colours,entry->text,pbuf,NULL,max_width);	
	g_object_ref(entry->normal);
	gtk_container_add(entry->widget,entry->normal);			
	if (pbuf)
		g_object_unref(pbuf);
}

GtkWidget * get_blank(Places * places)
{
	int max_width=places->max_width;
	GtkIconTheme*  g;  	
    static cairo_t *cr = NULL;   
    GdkScreen* pScreen;        
	GdkPixmap * pixmap; 
	GdkColormap*	cmap;
	GtkWidget * widget;	
	if (places->border_width>0)
	{
		pixmap=gdk_pixmap_new(NULL,max_width,places->border_width,32);  
	}
	else
	{
		pixmap=gdk_pixmap_new(NULL,max_width,1,32); 
	}							
    widget=gtk_image_new_from_pixmap(pixmap,NULL);        
    pScreen = gtk_widget_get_screen (GTK_WIDGET(places->applet));
    cmap = gdk_screen_get_rgba_colormap (pScreen);
    if (!cmap)
            cmap = gdk_screen_get_rgb_colormap (pScreen); 
    gdk_drawable_set_colormap(pixmap,cmap);       
    cr=gdk_cairo_create(pixmap);
	if (places->border_width>0)
	{    
	    cairo_set_source_rgba (cr, places->border_colour.red, places->border_colour.green,
	    						   places->border_colour.blue,places->border_colour.alpha);		
	}
	else
	{
	    cairo_set_source_rgba (cr, places->normal_colours.base.red, places->normal_colours.base.green,
	    						   places->normal_colours.base.blue,places->normal_colours.base.alpha);			
	}	    							
    cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
    cairo_paint(cr);
    cairo_destroy(cr);
    g_object_unref(pixmap);
	return widget;        
}

void measure_width(Menu_Item * menu_item)
{
    static cairo_t *cr = NULL;   
    static cairo_surface_t*  surface;
    cairo_text_extents_t    extents;    
	Places * places=menu_item->places;
    if (!cr)
    {
		surface=cairo_image_surface_create (CAIRO_FORMAT_ARGB32,places->text_size*40,places->text_size*1.6);   
		cr=cairo_create(surface);
    }
    cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
    cairo_set_font_size (cr,places->text_size  );  
	cairo_text_extents(cr,menu_item->text,&extents);   
	if ( extents.width+places->text_size*1.5 > places->max_width)
	{
		if (extents.width+places->text_size*1.5 >places->text_size*40)
		{
			places->max_width=places->text_size*40;
		}
		else
		{
			places->max_width=extents.width+places->text_size*2.5;
		}			
	}
}


static gboolean _enter_notify_event_entry(GtkWidget *widget,GdkEventCrossing *event,Menu_Item * item)  
{
	g_object_ref(item->hover);
	gtk_container_remove(widget,gtk_bin_get_child(widget) );
	gtk_container_add(widget,item->hover);		
	gtk_widget_show_all(item->hover);
	gtk_widget_show_all(widget);		
	return TRUE;		
}

static gboolean _leave_notify_event_entry(GtkWidget *widget,GdkEventCrossing *event,Menu_Item * item)  
{
	g_object_ref(item->normal);
	gtk_container_remove(widget,gtk_bin_get_child(widget));
	gtk_container_add(widget,item->normal);		
	gtk_widget_show_all(item->normal);
	gtk_widget_show_all(widget);			
	return TRUE;		
}

static gboolean _button_do_event(GtkWidget *widget,GdkEventButton *event,Menu_Item * item) 
{
	GError *err=NULL;
	g_spawn_command_line_async(item->exec,&err);
	gtk_widget_hide(item->places->mainwindow);
	return TRUE;
}    

static void render_menu_widgets(Menu_Item * item, Places * places)
{
	render_entry(item );
	g_signal_connect(G_OBJECT(item->widget), "enter-notify-event", G_CALLBACK (_enter_notify_event_entry), item);
	g_signal_connect(G_OBJECT(item->widget), "leave-notify-event", G_CALLBACK (_leave_notify_event_entry), item);
	g_signal_connect (G_OBJECT(item->widget), "button-release-event",G_CALLBACK (_button_do_event), item);	
	gtk_box_pack_start(places->vbox,item->widget,FALSE,FALSE,0);
}

static void render_places(Places * places)
{
	get_places(places);
	places->max_width=0;
	g_slist_foreach(places->menu_list,measure_width,places);
	gtk_box_pack_start(places->vbox,get_blank(places),FALSE,FALSE,0);	
	g_slist_foreach(places->menu_list,render_menu_widgets,places);	
	gtk_box_pack_end(places->vbox,get_blank(places),FALSE,FALSE,0);	
}



void show_prefs(Places * places)
{	
#if 0
	GtkWidget * prefs_win=gtk_window_new (GTK_WINDOW_TOPLEVEL);	
	GdkColormap *colormap;
	GdkScreen *screen;
	gchar * tmp;
		
	screen = gtk_window_get_screen(GTK_WINDOW(prefs_win));
	colormap = gdk_screen_get_rgba_colormap(screen);
	if (colormap != NULL && gdk_screen_is_composited(screen))
	{
		gtk_widget_set_colormap(prefs_win, colormap);
	}	    	
	gtk_window_set_title (prefs_win,"Places Preferences");
	GtkWidget* vbox=gtk_vbox_new(FALSE,0);
	GtkWidget * gtk=gtk_check_button_new_with_label("Use Gtk");
	GtkWidget * tooltips=gtk_check_button_new_with_label("Show tooltips");	

		
	GtkWidget* gtk_off_section=gtk_vbox_new(FALSE,0);	
	gtk_off_table=gtk_table_new(2,4,FALSE);
	
	GtkWidget *normal_label=gtk_label_new("Normal");
	GdkColor 	colr;

	colr.red=places->normal_colours.base.red*65535;
	colr.green=places->normal_colours.base.green*65535;	
	colr.blue=places->normal_colours.base.blue*65535;	
	GtkWidget *normal_bg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (normal_bg,TRUE);
	gtk_color_button_set_alpha (normal_bg,places->normal_colours.base.alpha*65535);
	g_signal_connect (G_OBJECT (normal_bg), "color-set",G_CALLBACK (_mod_colour),&places->normal_colours.base);		

	colr.red=places->normal_colours.text.red*65535;
	colr.green=places->normal_colours.text.green*65535;	
	colr.blue=places->normal_colours.text.blue*65535;	
	GtkWidget *normal_fg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (normal_fg,TRUE);
	gtk_color_button_set_alpha (normal_fg,places->normal_colours.text.alpha*65535);
	g_signal_connect (G_OBJECT (normal_fg), "color-set",G_CALLBACK (_mod_colour),&places->normal_colours.text);		
	
	GtkWidget *hover_label=gtk_label_new("Hover");

	colr.red=places->hover_colours.base.red*65535;
	colr.green=places->hover_colours.base.green*65535;	
	colr.blue=places->hover_colours.base.blue*65535;	
	GtkWidget *hover_bg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (hover_bg,TRUE);
	gtk_color_button_set_alpha (hover_bg,places->hover_colours.base.alpha*65535);
	g_signal_connect (G_OBJECT (hover_bg), "color-set",G_CALLBACK (_mod_colour),&places->hover_colours.base);		
	
	colr.red=places->hover_colours.text.red*65535;
	colr.green=places->hover_colours.text.green*65535;	
	colr.blue=places->hover_colours.text.blue*65535;	
	GtkWidget *hover_fg=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (hover_fg,TRUE);
	gtk_color_button_set_alpha (hover_fg,places->hover_colours.text.alpha*65535);	
	g_signal_connect (G_OBJECT (hover_fg), "color-set",G_CALLBACK (_mod_colour),&places->hover_colours.text);		


	GtkWidget *border_label=gtk_label_new("Border");

	colr.red=places->border_colour.red*65535;
	colr.green=places->border_colour.green*65535;	
	colr.blue=places->border_colour.blue*65535;	
	GtkWidget *border_colour=gtk_color_button_new_with_color(&colr);
	gtk_color_button_set_use_alpha (border_colour,TRUE);
	gtk_color_button_set_alpha (border_colour,places->border_colour.alpha*65535);
	g_signal_connect (G_OBJECT (border_colour), "color-set",G_CALLBACK (_mod_colour),&places->border_colour);		


	GtkWidget * text_table=gtk_table_new(2,4,FALSE);
	GtkWidget * filemanager=gtk_file_chooser_button_new("File Manager",GTK_FILE_CHOOSER_ACTION_OPEN);	

	tmp=g_filename_from_utf8(places->filemanager,-1, NULL, NULL, NULL) ;
	gtk_file_chooser_set_filename(GTK_FILE_CHOOSER (filemanager),tmp);
	g_free(tmp);
	
	GtkWidget * adjust_gradient=gtk_spin_button_new_with_range(0.0,1.0,0.01);

	GtkWidget * adjust_textsize=gtk_spin_button_new_with_range(4,40,1);
	GtkWidget * adjust_borderwidth=gtk_spin_button_new_with_range(0,10,1);			
	
	GtkWidget* buttons=gtk_hbox_new(FALSE,0);	
	GtkWidget* ok=gtk_button_new_with_label("Ok");
	
	Menu_item_color mic;
	mic.bg=places->normal_colours.base;
	mic.fg=places->normal_colours.text;
	normal_ex=build_menu_widget(&mic,"Normal",NULL,NULL,200,MENU_WIDGET_NORMAL);

	mic.bg=places->hover_colours.base;
	mic.fg=places->hover_colours.text;
	hover_ex=build_menu_widget(&mic,"Hover",NULL,NULL,200,MENU_WIDGET_NORMAL);

    gtk_window_set_keep_above (GTK_WINDOW (prefs_win),TRUE);
    gtk_window_set_accept_focus(GTK_WINDOW (prefs_win),TRUE);
	gtk_window_set_focus_on_map (GTK_WINDOW (prefs_win),TRUE);	

	gtk_spin_button_set_value(adjust_gradient,places->menu_item_gradient_factor);
	gtk_spin_button_set_value(adjust_textsize,places->text_size);			
	gtk_spin_button_set_value(adjust_borderwidth,places->border_width);	
	g_signal_connect (G_OBJECT (adjust_gradient), "value-changed",G_CALLBACK (spin_change),
									&places->menu_item_gradient_factor);	
	g_signal_connect (G_OBJECT (adjust_textsize), "value-changed",G_CALLBACK (spin_int_change),
									&places->text_size);	
	g_signal_connect (G_OBJECT (adjust_borderwidth), "value-changed",G_CALLBACK (spin_int_change),
								&places->border_width);	
	
	g_signal_connect (G_OBJECT(filemanager), "file-set",G_CALLBACK (_file_set), &places->filemanager);		

	gtk_toggle_button_set_active(gtk,places->honour_gtk);
	
	gtk_toggle_button_set_active(tooltips,places->show_tooltips);		
	g_signal_connect (G_OBJECT (tooltips), "toggled",G_CALLBACK (_toggle_),&places->show_tooltips);			
	
	g_signal_connect (G_OBJECT (ok), "button-press-event",G_CALLBACK (_press_ok),prefs_win );	

	gtk_container_add (GTK_CONTAINER (prefs_win), vbox); 

	g_signal_connect (G_OBJECT (gtk), "toggled",G_CALLBACK (_toggle_gtk),gtk_off_section );	

	gtk_box_pack_start(GTK_CONTAINER (vbox),tooltips,FALSE,FALSE,0);			

	gtk_box_pack_start(GTK_CONTAINER (vbox),text_table,FALSE,FALSE,0);		
	gtk_table_attach_defaults(text_table,gtk_label_new("File Manager"),0,1,1,2);	
	gtk_table_attach_defaults(text_table,filemanager,1,2,1,2);
	gtk_table_attach_defaults(text_table,gtk_label_new("Font Size (px)"),0,1,3,4);			
	gtk_table_attach_defaults(text_table,adjust_textsize,1,2,3,4);				
	gtk_table_attach_defaults(text_table,gtk_label_new("Border Width"),0,1,4,5);			
	gtk_table_attach_defaults(text_table,adjust_borderwidth,1,2,4,5);	
		
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
	
	gtk_table_attach_defaults(gtk_off_table,border_label,0,1,2,3);		
	gtk_table_attach_defaults(gtk_off_table,border_colour,2,3,2,3);

	gtk_table_attach_defaults(gtk_off_table,gtk_label_new("Gradient Factor"),0,1,3,4);	
	gtk_table_attach_defaults(gtk_off_table,adjust_gradient,2,3,3,4);


	
	gtk_box_pack_start(GTK_CONTAINER (vbox),buttons,FALSE,FALSE,0);
	gtk_box_pack_start(GTK_CONTAINER (buttons),ok,FALSE,FALSE,0);							
	gtk_widget_show_all(prefs_win);	
	if (places->honour_gtk)
	{
		gtk_widget_hide(gtk_off_section);
	}
#endif
}




static gboolean _show_prefs (GtkWidget *widget, GdkEventButton *event, Places * places)
{
//	show_prefs(places);
	return TRUE;
}

//-------------------------------------------------------------------------


static gboolean _expose_event (GtkWidget *widget, GdkEventExpose *expose, Places * places)
{
    cairo_t *cr;
    cr=gdk_cairo_create(widget->window);    
    cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);        
    cairo_paint(cr);                  
	gtk_widget_send_expose(places->vbox,expose);        
    cairo_destroy(cr);                        
    return TRUE;
}

static gboolean _button_clicked_event (GtkWidget *widget, GdkEventButton *event, Places * places)
{
    GdkEventButton *event_button;
    event_button = (GdkEventButton *) event; 
    if (event->button == 1)
    {
    	/*the gtk_window_set_opacity is a hack because the mainwindow window flickers, 
    	  	visibly, briefly on the screen sometimes without it*/
		if (GTK_WIDGET_VISIBLE(places->mainwindow) )
		{
			gtk_widget_hide(places->mainwindow);
		}
		else
		{
			gtk_widget_show_all(places->mainwindow);		
		}    
    }
    else if (event->button == 3)    
    {
    	static gboolean done_once=FALSE;
    	static GtkWidget * menu;
    	static GtkWidget * item;
    	if (!done_once)
    	{
			menu=gtk_menu_new ();
			item=gtk_menu_item_new_with_label("Preferences");
			gtk_widget_show(item);
			gtk_menu_set_screen(menu,NULL);    	
			gtk_menu_shell_append(menu,item);
			g_signal_connect (G_OBJECT (item), "button-press-event",G_CALLBACK (_show_prefs), NULL);
    		done_once=TRUE;
    	}
    	gtk_menu_popup (menu, NULL, NULL, NULL, NULL, 
			  event_button->button, event_button->time);
    }
 	return TRUE;
}

static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event, Places * places)
{
    if (  gdk_window_get_window_type (event->window) !=GDK_WINDOW_TEMP)
    {        
        gtk_widget_hide(places->mainwindow);
    }
    return TRUE;
}


static void _bloody_thing_has_style(GtkWidget *widget,Places *places)
{
	init_config(places);	
	render_places(places);
}

AwnApplet* awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
	GdkPixbuf *icon;
	Places * places = g_malloc(sizeof(Places) );	
  	AwnApplet *applet = places->applet= AWN_APPLET (awn_applet_simple_new (uid, orient, height));
	gtk_widget_set_size_request (GTK_WIDGET (applet), height, -1);
	icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (), "stock_folder",height-2, 0, NULL);	
	if (!icon)
	{			                       
    	icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,height-2,height-2);
	    gdk_pixbuf_fill(icon,0x11881133);  
	}	    
	places->icon=icon;
	awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),icon);                                   	
	gtk_widget_show_all (GTK_WIDGET (applet));		
	places->mainwindow = awn_applet_dialog_new (applet);			
	places->vbox=gtk_vbox_new(FALSE,0);	
	gtk_container_add (GTK_CONTAINER (places->mainwindow),places->vbox);    
	g_signal_connect (G_OBJECT (places->applet), "button-press-event",G_CALLBACK (_button_clicked_event), places);		
	g_signal_connect(G_OBJECT(places->mainwindow),"focus-out-event",G_CALLBACK (_focus_out_event),places);    
	g_signal_connect (G_OBJECT (places->mainwindow),"expose-event", G_CALLBACK (_expose_event), places);		
	g_signal_connect_after(G_OBJECT (places->applet), "realize", _bloody_thing_has_style, places);
	return applet;

}

