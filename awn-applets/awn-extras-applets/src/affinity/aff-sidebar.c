/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*- */
/*
 * Copyright (C) 2007 Neil J. Patel <njpatel@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * Authors: Neil J. Patel <njpatel@gmail.com>
 *
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <gtk/gtk.h>
#include <libgnome/gnome-i18n.h>
#include <libgnomevfs/gnome-vfs.h>
#include <stdio.h>
#include <string.h>

#if !GTK_CHECK_VERSION(2,9,0)
#include <X11/Xlib.h>
#include <X11/extensions/shape.h>
#include <gdk/gdkx.h>
#endif

#include "aff-sidebar.h"

#include "aff-button.h"
#include "aff-settings.h"
#include "aff-utils.h"

#define AFF_SIDEBAR_GET_PRIVATE(obj) (G_TYPE_INSTANCE_GET_PRIVATE ((obj), AFF_TYPE_SIDEBAR, AffSidebarPrivate))

G_DEFINE_TYPE (AffSidebar, aff_sidebar, GTK_TYPE_VBOX);

/* STRUCTS & ENUMS */
struct _AffSidebarPrivate
{
	AffinityApp *app;
	GnomeVFSVolumeMonitor* vfs_monitor;

        GtkWidget *places;
        GtkWidget *places_box;
        GtkWidget *vfs_box;
        GtkWidget *system;	
};

enum {
	ICON_DESKTOP,
	ICON_HOME,
	ICON_DIRECTORY,
	ICON_FILESYSTEM,
	ICON_NETWORK,
	ICON_COMPUTER,
	ICON_PROGRAMS,
	ICON_CONTROL,
	ICON_LOCK,
	ICON_SHUTDOWN,
	N_ICONS	
};

static char *icon_names[] = {
	"gnome-fs-desktop",  
	"gnome-fs-home",
	"gnome-fs-directory",
	"drive-harddisk",
	"gnome-fs-network",
	"computer",
	"system-installer",
	"gnome-control-center",
	"system-lock-screen",
	"system-log-out"
};

#define ICON_SIZE 24

/* FORWARDS */

static void aff_sidebar_class_init(AffSidebarClass *klass);
static void aff_sidebar_init(AffSidebar *sidebar);
static void aff_sidebar_finalize(GObject *obj);

static GtkVBoxClass *parent_class;
static GdkPixbuf *pixbufs[N_ICONS];
static AffinityApp *aff_app = NULL; /* Yuk! */


/* CALLBACKS */

static void
strip_x(char *uri)
{
       int i;
       char c;
       for ( i = 0; i < strlen(uri); i++) {
                c = uri[i];
                
                if ( c == '\n')
                        uri[i] = '\0';
                else
                        ;
        }
}

static void
make_name(GString *name)
{
        int i, space, slash;
        i = space = slash = 0;
        const char *string = name->str;
        
        for ( i = 0; i < name->len; i++) {
                /*
                if (string[i] == ' ') {
                        space = i;
                        break;
                }
                else*/ if (string[i] == '/')
                        slash = i;
                else
                        ;
        }
        
        if (space) {
                g_string_erase(name, 0, space+1);
                return;
        } else {
                g_string_erase(name, 0, slash+1);
        }
}

static void
make_uri(GString *uri)
{
        int i, space;
        const char *string = uri->str;
        i = space = 0;
        
        for ( i = 0; i < uri->len; i++) {
                if (string[i] == ' ') {
                        space = i;
                        break;
                } else
                        ;
        }
        
        if (space) {
                g_string_erase(uri, space, -1);
                return;
        } else 
                ;        
}

static GtkWidget *book_but = NULL;
static GtkWidget *menu = NULL;

static void
bookmark_activate (GtkMenuItem *menuitem, char *u)
{
        char *command;
        command = g_strdup_printf ("%s %s", aff_app->settings->file_manager, u);
        g_spawn_command_line_async (command, NULL);
        g_free (command);
	
	affinity_app_hide (aff_app);      
}

static void
add_bookmark ( GdkPixbuf **pixbufs, const char *name, const char *uri, int row)
{
        GtkWidget *item;
        item = gtk_image_menu_item_new_with_label (name);
        
        GtkWidget *image = gtk_image_new_from_pixbuf (pixbufs[ICON_DIRECTORY]);
        gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(item), image);
        
        gtk_menu_attach (GTK_MENU (menu), item, 0,1, row, row+1);
        
        gtk_widget_show_all(menu);
        g_signal_connect(G_OBJECT(item), "activate", G_CALLBACK(bookmark_activate), g_strdup(uri));
}

static void
show_bookmarks (GtkButton *button, AffinityApp *app)
{
        app->lock_focus = TRUE;
        gtk_menu_popup (GTK_MENU(menu),NULL,NULL,NULL,NULL,0,gtk_get_current_event_time());
        
}

static void
selection_done (GtkMenuShell *menushell, AffinityApp *app)
{
	app->lock_focus = FALSE;
	g_print ("Selection done\n");
} 

static void
read_gtk_shortcuts(AffinityApp *app, GdkPixbuf **pixbufs, GtkWidget *box)
{
        if (book_but == NULL) {
                GtkWidget *image = gtk_image_new_from_icon_name("bookmark-new", ICON_SIZE);
                book_but = aff_button_new(app, GTK_IMAGE (image), _("Bookmarks\t"), NULL);
                gtk_box_pack_end(GTK_BOX (box), book_but, FALSE, TRUE, 0);
                
                g_signal_connect(G_OBJECT(book_but), "clicked", G_CALLBACK(show_bookmarks), (gpointer)app);
        }
        if (menu == NULL) {
                menu = gtk_menu_new();
                gtk_menu_attach_to_widget(GTK_MENU(menu), book_but, NULL);
                g_signal_connect(G_OBJECT(menu), "selection-done", G_CALLBACK(selection_done), (gpointer)app);
        }
        
        
        GString *file; /* Bookmarks file */
        file = g_string_new (g_get_home_dir());
        g_string_append(file, "/.gtk-bookmarks");
        
        char line[1024];
        FILE *f;
        f = fopen(file->str, "r");
        
        int count = 0;
        
        if (f != NULL) {
                
                while (fgets(line, 1024, f) != NULL) {
                        count++;
                        GString *name = NULL;
        		GString *uri = NULL;
                        uri = g_string_new(line);
                        make_uri(uri);
                        
                        char *format = gnome_vfs_format_uri_for_display (uri->str);
                        name = g_string_new(format);
                        make_name(name);
                        g_free (format);
                        
                        strip_x(name->str);
                        strip_x(uri->str);
                        add_bookmark(pixbufs, name->str, uri->str, count);
        	        g_string_free(uri, TRUE);
		        g_string_free(name, TRUE);                        
                }
                fclose(f);

        }
        
        if (count)
                gtk_widget_show(book_but);
        else
                gtk_widget_hide(book_but);
        
        g_string_free(file, TRUE);
}

static void 
watch_callback (GnomeVFSMonitorHandle *handle, const gchar *dir,const gchar *file, 
					       GnomeVFSMonitorEventType type,AffinityApp *app)
{
        menu = NULL;
        read_gtk_shortcuts(app, pixbufs, NULL);
        
}

static void
add_shortcut (AffSidebarPrivate *priv, GtkWidget *box, const char *name, GdkPixbuf *icon, const char *uri, gboolean place)
{
        GtkWidget *button, *image;
        image = gtk_image_new_from_pixbuf( icon);
        
        if (place) {
                char *command = g_strdup_printf ("%s %s", priv->app->settings->file_manager, uri);
                button = aff_button_new_with_command (priv->app, GTK_IMAGE (image), name, command);
                g_free (command);
        
        } else
		button = aff_button_new_with_command (priv->app, GTK_IMAGE (image), name, uri);
        
        gtk_box_pack_start(GTK_BOX(box), button, FALSE, TRUE, 0);
//        gtk_widget_set_size_request (button, 120, -1);
        gtk_widget_show_all (button);
}

static void 
init_icons( GdkPixbuf **pixbufs, GtkIconTheme *theme )
{
	int i = 0;
	for (i = 0; i < N_ICONS; i++ ) {
		pixbufs[i] = gtk_icon_theme_load_icon (theme,
                                   icon_names[i], /* icon name */
                                   ICON_SIZE, /* size */
                                   0,  /* flags */
                                   NULL);
        }


}

static void 
init_places(AffSidebar *sidebar, GdkPixbuf **pixbufs, GtkWidget *vbox )
{
	AffSidebarPrivate *priv;
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
		
        add_shortcut(priv, vbox, _("Home"), pixbufs[ICON_HOME], g_get_home_dir(), TRUE);
        //add_shortcut(vbox, _("Desktop"), pixbufs[1], "~/Desktop", TRUE);
	add_shortcut(priv, vbox, _("Filesystem"), pixbufs[ICON_FILESYSTEM], "/", TRUE);
	
	const char *comp = priv->app->settings->computer;
	if (strlen (comp) > 3)
		add_shortcut(priv, vbox, _("Computer"), pixbufs[ICON_COMPUTER], comp, TRUE);
	const char *net = priv->app->settings->network;
	if (strlen (net) > 3)
	add_shortcut(priv, vbox, _("Network"), pixbufs[ICON_NETWORK], net, TRUE);
}

static void
init_vfs (AffSidebar *sidebar, GtkWidget *vbox)
{
	AffSidebarPrivate *priv;
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
	
	GList *connected = gnome_vfs_volume_monitor_get_connected_drives (priv->vfs_monitor);
	GList *l;
	
	for (l = connected; l != NULL; l = l->next) {
		GnomeVFSDrive *drive = (GnomeVFSDrive*)l->data;
		GList *volumes = NULL;
		GList *v = NULL;
		
		int res = 0;
				
		volumes = gnome_vfs_drive_get_mounted_volumes (drive);

		for (v = volumes; v != NULL; v = v->next) {
			GnomeVFSVolume *vol = (GnomeVFSVolume*)v->data;
			GdkPixbuf *icon = NULL;
			char *icon_name = NULL;
			char *name = NULL;
			char *uri = NULL;
			char *exec = NULL;
			GtkWidget *button, *image;		
		
			name = gnome_vfs_volume_get_display_name (vol);
			uri = gnome_vfs_volume_get_activation_uri (vol);
			icon_name = gnome_vfs_volume_get_icon (vol);
			icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default(),
                                         		icon_name,
                                         		ICON_SIZE,
                                         		GTK_ICON_LOOKUP_FORCE_SVG,
                                         		NULL);	
						
			image = gtk_image_new_from_pixbuf( icon);		
			button = aff_button_new (priv->app, GTK_IMAGE (image), name, uri);
			
			gtk_box_pack_start (GTK_BOX (vbox), button, FALSE, TRUE, 0);
			
			g_print ("Volume Mounted : %s, %s\n", name, uri);
			
			g_free (name);
			g_free (uri);
			g_free (exec);
			g_free (icon_name);
			
			gnome_vfs_volume_unref (vol);
			res ++;
		}
		
		//gnome_vfs_drive_volume_list_free (volumes);
/*		
		if (!res) {
			GdkPixbuf *icon = NULL;
			char *icon_name = NULL;
			char *name = NULL;
			char *uri = NULL;
			char *exec = NULL;
			GtkWidget *button, *image;		
		
			name = gnome_vfs_drive_get_display_name (drive);
			uri = gnome_vfs_drive_get_device_path (drive);
			exec = g_strdup_printf ("nautilus %s", uri);
			icon_name = gnome_vfs_drive_get_icon (drive);
			icon = gtk_icon_theme_load_icon (gtk_icon_theme_get_default(),
                                         		icon_name,
                                         		GTK_ICON_SIZE_MENU,
                                         		GTK_ICON_LOOKUP_FORCE_SVG,
                                         		NULL);	
						
			image = gtk_image_new_from_pixbuf( icon);		
			button = aff_button_new_with_command (priv->app, GTK_IMAGE (image), name, exec);
			
			gtk_box_pack_start (GTK_BOX (vbox), button, FALSE, TRUE, 0);
			
			g_print ("%s : %s : %s\n", icon_name, name, uri);
			
			g_free (name);
			g_free (uri);
			g_free (exec);
			g_free (icon_name);
			
		}
*/
		gnome_vfs_drive_unref(drive);
	}
	g_list_free (connected);
	
	gtk_widget_show_all (vbox);
}

static gboolean
_reload_vfs (AffSidebar *sidebar)
{
	AffSidebarPrivate *priv;
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
	
	init_vfs (sidebar, priv->vfs_box);
	
	return FALSE;
}  

static void        
aff_sidebar_volume_mounted (GnomeVFSVolumeMonitor *volume_monitor,
                            GnomeVFSVolume        *volume,
                            AffSidebar            *sidebar)
{
	AffSidebarPrivate *priv;
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
	
	gtk_widget_destroy (priv->vfs_box);
	priv->vfs_box = gtk_vbox_new (FALSE, 0);
	g_timeout_add (1000, (GSourceFunc)_reload_vfs, (gpointer)sidebar);
	
	gtk_box_pack_start (GTK_BOX (priv->places_box), priv->vfs_box, FALSE, FALSE, 0); 
}

static void        
aff_sidebar_volume_unmounted (GnomeVFSVolumeMonitor *volume_monitor,
                            GnomeVFSVolume        *volume,
                            AffSidebar            *sidebar)
{
	AffSidebarPrivate *priv;
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
	
	gtk_widget_destroy (priv->vfs_box);
	priv->vfs_box = gtk_vbox_new (FALSE, 0);
	g_timeout_add (1000, (GSourceFunc)_reload_vfs, (gpointer)sidebar);
	
	gtk_box_pack_start (GTK_BOX (priv->places_box), priv->vfs_box, FALSE, FALSE, 0); 
}  

static void 
init_system(AffSidebar *sidebar, GdkPixbuf **pixbufs, GtkWidget *vbox )
{
 	AffSidebarPrivate *priv;
 	AffSettings *s;
 	
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
	s = priv->app->settings;
	
	if (strlen (s->config_software) > 2)
		add_shortcut(priv,vbox, _("Manage Software"), pixbufs[ICON_PROGRAMS], s->config_software, FALSE);
        
        if (strlen (s->control_panel) > 2)
	        add_shortcut(priv,vbox, _("Control Panel"), pixbufs[ICON_CONTROL], s->control_panel, FALSE);
	
	if (strlen (s->lock_screen) > 2)
	add_shortcut(priv,vbox, _("Lock Screen"), pixbufs[ICON_LOCK], s->lock_screen, FALSE);
	
	if (strlen (s->log_out) > 2)
	add_shortcut(priv,vbox, _("Log Out"), pixbufs[ICON_SHUTDOWN], s->log_out, FALSE);
}

/*  GOBJECT INIT CODE */
static void
aff_sidebar_class_init(AffSidebarClass *klass)
{
	GObjectClass *gobject_class;
	
	parent_class = g_type_class_peek_parent(klass);

	gobject_class = G_OBJECT_CLASS(klass);
	g_type_class_add_private (gobject_class, sizeof (AffSidebarPrivate));
	gobject_class->finalize = aff_sidebar_finalize;
}

static void
aff_sidebar_init(AffSidebar *sidebar)
{
	AffSidebarPrivate *priv;
		
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);
	
        init_icons(pixbufs, gtk_icon_theme_get_default());
	
}



static void
aff_sidebar_finalize(GObject *obj)
{
	AffSidebar *sidebar;
	
	g_return_if_fail(obj != NULL);
	g_return_if_fail(AFF_IS_SIDEBAR(obj));

	sidebar = AFF_SIDEBAR(obj);
	
	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(obj);
}

GtkWidget *
aff_sidebar_new(AffinityApp *app)
{
	AffSidebarPrivate *priv;
	GtkWidget *box, *frame, *alignment;
	GtkWidget *label;
	gchar *markup;	
	GtkWidget *sidebar = g_object_new(AFF_TYPE_SIDEBAR, 
					 "homogeneous", FALSE,
					 "spacing", 8,
					 NULL);
	priv = AFF_SIDEBAR_GET_PRIVATE (sidebar);					 
	priv->app = app;
	aff_app = app;
	
	frame = gtk_frame_new(" ");
	priv->places = frame;
	gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_NONE);
	
	label = gtk_label_new (" ");
	markup = g_strdup_printf ("<span foreground='%s' size='larger' weight='bold'>%s</span>", 
				  app->settings->text_color, 
				  _("Places"));
				  
	gtk_label_set_markup (GTK_LABEL (label), markup);
	g_free (markup);
	gtk_frame_set_label_widget (GTK_FRAME (frame), label);
	
        alignment = gtk_alignment_new (0.0, 0.0, 1.0, 0.0);
        gtk_alignment_set_padding(GTK_ALIGNMENT (alignment), 5, 0, 15, 0);
        gtk_container_add(GTK_CONTAINER (frame), alignment);	
       
        box = gtk_vbox_new(FALSE, 0 );
        priv->places_box = box;
        gtk_container_add (GTK_CONTAINER (alignment), box); 
        init_places (AFF_SIDEBAR (sidebar), pixbufs, box);
        
        /* VFS */
        box = gtk_vbox_new(FALSE, 0 );
        priv->vfs_box = box;
        priv->vfs_monitor = gnome_vfs_get_volume_monitor ();
        init_vfs (AFF_SIDEBAR (sidebar), priv->vfs_box);
        
        g_signal_connect (G_OBJECT (priv->vfs_monitor), "volume-mounted",
        		  G_CALLBACK (aff_sidebar_volume_mounted), (gpointer)sidebar);
        g_signal_connect (G_OBJECT (priv->vfs_monitor), "volume-unmounted",
        		  G_CALLBACK (aff_sidebar_volume_unmounted), (gpointer)sidebar);
        
	/* System */
	frame = gtk_frame_new(" ");
        priv->system = frame;
	gtk_frame_set_shadow_type (GTK_FRAME (frame), GTK_SHADOW_NONE);

	label = gtk_label_new (" ");
	markup = g_strdup_printf ("<span foreground='%s' size='larger' weight='bold'>%s</span>", 
				  app->settings->text_color, 
				  _("System"));
				  
	gtk_label_set_markup (GTK_LABEL (label), markup);
	g_free (markup);
	gtk_frame_set_label_widget (GTK_FRAME (frame), label);	

        alignment = gtk_alignment_new (0.0, 0.0, 1.0, 0.0);
        gtk_alignment_set_padding(GTK_ALIGNMENT(alignment), 5, 0, 15, 0);
        gtk_container_add(GTK_CONTAINER(frame), alignment);	

	box = gtk_vbox_new(FALSE, 0 );
        gtk_container_add (GTK_CONTAINER(alignment), box);         
        init_system (AFF_SIDEBAR (sidebar), pixbufs,box);
	        
//	gtk_widget_set_size_request (GTK_WIDGET (sidebar), 150, 100);	

        /* Bookmarks */
	read_gtk_shortcuts(app, pixbufs, priv->places_box);

        GnomeVFSMonitorHandle *handle;
        GnomeVFSResult result;
        GString *file; /* Bookmarks file */
        file = g_string_new (g_get_home_dir());
        g_string_append(file, "/.gtk-bookmarks");
        result = gnome_vfs_monitor_add (&handle, file->str , GNOME_VFS_MONITOR_FILE, 
        				(GnomeVFSMonitorCallback)watch_callback, (gpointer)app);
        if(! result == GNOME_VFS_OK)
                g_print("VFS ERROR : %s", gnome_vfs_result_to_string (result));
        
        g_string_free(file, TRUE);	
        
        gtk_box_pack_start (GTK_BOX (sidebar), priv->places, TRUE, TRUE, 0);
        gtk_box_pack_start (GTK_BOX (priv->places_box), priv->vfs_box, TRUE, TRUE, 0);
        gtk_box_pack_end (GTK_BOX (sidebar), priv->system, FALSE, TRUE, 0);            
		
	return GTK_WIDGET(sidebar);
}

