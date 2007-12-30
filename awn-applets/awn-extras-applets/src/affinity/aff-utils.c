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

#include "aff-utils.h"

#include <gnome.h>
#include <libgnome/gnome-i18n.h>
#include <libgnomevfs/gnome-vfs-utils.h>
#include <libgnome/gnome-desktop-item.h>

#define METADATA_IMAGE_WIDTH	48
#define METADATA_IMAGE_HEIGHT	48

GdkPixbuf *
aff_utils_get_icon (const char *uri)
{
	gchar *icon_name = NULL;
	gchar *thumb_name = NULL;
	GdkPixbuf *temp = NULL;
	gchar *local_uri = gnome_vfs_get_local_path_from_uri (uri);
	GtkIconTheme *theme = gtk_icon_theme_get_default ();
	
	thumb_name = gnome_thumbnail_path_for_uri (uri, GNOME_THUMBNAIL_SIZE_NORMAL);
	temp = gdk_pixbuf_new_from_file_at_scale (thumb_name, METADATA_IMAGE_WIDTH, METADATA_IMAGE_HEIGHT, TRUE, NULL);
	if (temp) {
		g_free (thumb_name);
		g_free (local_uri);
		return temp;
	}
	icon_name = gnome_icon_lookup_sync  (theme, 
                                             NULL,
                                             local_uri,
                                             NULL,
                                             GNOME_ICON_LOOKUP_FLAGS_SHOW_SMALL_IMAGES_AS_THEMSELVES |
                                             		GNOME_ICON_LOOKUP_FLAGS_ALLOW_SVG_AS_THEMSELVES,
                                             0);                                       
	temp = gtk_icon_theme_load_icon (theme,
                                         icon_name,
                                         METADATA_IMAGE_HEIGHT,
                                         GTK_ICON_LOOKUP_FORCE_SVG,
                                         NULL);
	g_free (icon_name);
	g_free (thumb_name);
	g_free (local_uri);
	
	return temp;	
}

GdkPixbuf *
aff_utils_get_icon_sized (const char *uri, gint width, gint height)
{
	gchar *icon_name = NULL;
	gchar *thumb_name = NULL;
	GdkPixbuf *temp = NULL;
	gchar *local_uri = gnome_vfs_get_local_path_from_uri (uri);
	GtkIconTheme *theme = gtk_icon_theme_get_default ();
	
	thumb_name = gnome_thumbnail_path_for_uri (uri, GNOME_THUMBNAIL_SIZE_NORMAL);
	temp = gdk_pixbuf_new_from_file_at_scale (thumb_name, width, height, TRUE, NULL);
	if (temp) {
		g_free (thumb_name);
		g_free (local_uri);
		return temp;
	}
	
	if (temp == NULL) {
		temp = gtk_icon_theme_load_icon (theme,
                                         	uri,
                                         	width,
                                         	GTK_ICON_LOOKUP_FORCE_SVG,
                                         	NULL);	
	}
	
	icon_name = gnome_icon_lookup_sync  (theme, 
                                             NULL,
                                             local_uri,
                                             NULL,
                                             GNOME_ICON_LOOKUP_FLAGS_SHOW_SMALL_IMAGES_AS_THEMSELVES |
                                             		GNOME_ICON_LOOKUP_FLAGS_ALLOW_SVG_AS_THEMSELVES,
                                             0);                                       
	temp = gtk_icon_theme_load_icon (theme,
                                         icon_name,
                                         width,
                                         GTK_ICON_LOOKUP_FORCE_SVG,
                                         NULL);
	g_free (icon_name);
	g_free (thumb_name);
	g_free (local_uri);
	
	return temp;	
}

GdkPixbuf *
aff_utils_get_app_icon (const char *name)
{
        GdkPixbuf *icon = NULL;
        GdkScreen *screen = gdk_screen_get_default();
        GtkIconTheme *theme = NULL;
        theme = gtk_icon_theme_get_for_screen (screen);

        gint width, height;
        width = height = METADATA_IMAGE_HEIGHT;

        if (!name)
                return NULL;
        
        GtkIconInfo *icon_info = gtk_icon_theme_lookup_icon (theme, name, width, 0);

	if (icon_info != NULL) {
		icon = gdk_pixbuf_new_from_file_at_size (
				      gtk_icon_info_get_filename (icon_info),
                                      width, -1, NULL);
		gtk_icon_info_free(icon_info);
	}
	  
        /* first we try gtkicontheme */
        if (icon == NULL)
        	icon = gtk_icon_theme_load_icon( theme, name, width, GTK_ICON_LOOKUP_FORCE_SVG, NULL);
	
        if (icon == NULL) {
                /* lets try and load directly from file */
                GString *str;
                
                if ( strstr(name, "/") != NULL )
                        str = g_string_new(name);
                else {
                        str = g_string_new("/usr/share/pixmaps/");
                        g_string_append(str, name);
                }
                
                icon = gdk_pixbuf_new_from_file_at_scale(str->str, 
                                                         width,
                                                         height,
                                                         TRUE, NULL);
                g_string_free(str, TRUE);
        }
        
        if (icon == NULL) {
                /* lets try and load directly from file */
                GString *str;
                
                if ( strstr(name, "/") != NULL )
                        str = g_string_new(name);
                else {
                        str = g_string_new("/usr/local/share/pixmaps/");
                        g_string_append(str, name);
                }
                
                icon = gdk_pixbuf_new_from_file_at_scale(str->str, 
                                                         width,
                                                         -1,
                                                         TRUE, NULL);
                g_string_free(str, TRUE);
        }
        
        if (icon == NULL) {
                GString *str;
                
                str = g_string_new("/usr/share/");
                g_string_append(str, name);
                g_string_erase(str, (str->len - 4), -1 );
                g_string_append(str, "/");
		g_string_append(str, "pixmaps/");
		g_string_append(str, name);
		
		icon = gdk_pixbuf_new_from_file_at_scale
       		                             (str->str,
                                             width,
                                             -1,
                                             TRUE,
                                             NULL);
                g_string_free(str, TRUE);
        }
        
        if (icon == NULL) {
                GString *str = NULL;
                str = g_string_new (name);
                if (str->len > 4) 
	                str = g_string_erase (str, str->len-4, -1);
                icon = gtk_icon_theme_load_icon( theme, str->str, width, GTK_ICON_LOOKUP_FORCE_SVG, NULL);
        	g_string_free (str, TRUE);
        }        
        return icon;

}

GdkPixbuf *
aff_utils_get_app_icon_sized (const char *name, gint width, gint height)
{
        GdkPixbuf *icon = NULL;
        GdkScreen *screen = gdk_screen_get_default();
        GtkIconTheme *theme = NULL;
        theme = gtk_icon_theme_get_for_screen (screen);

        if (!name)
                return NULL;
        
        GtkIconInfo *icon_info = gtk_icon_theme_lookup_icon (theme, name, width, 0);

	if (icon_info != NULL) {
		icon = gdk_pixbuf_new_from_file_at_size (
				      gtk_icon_info_get_filename (icon_info),
                                      width, -1, NULL);
		gtk_icon_info_free(icon_info);
	}
	  
        /* first we try gtkicontheme */
        if (icon == NULL)
        	icon = gtk_icon_theme_load_icon( theme, name, width, GTK_ICON_LOOKUP_FORCE_SVG, NULL);
	
        if (icon == NULL) {
                /* lets try and load directly from file */
                GString *str;
                
                if ( strstr(name, "/") != NULL )
                        str = g_string_new(name);
                else {
                        str = g_string_new("/usr/share/pixmaps/");
                        g_string_append(str, name);
                }
                
                icon = gdk_pixbuf_new_from_file_at_scale(str->str, 
                                                         width,
                                                         height,
                                                         TRUE, NULL);
                g_string_free(str, TRUE);
        }
        
        if (icon == NULL) {
                /* lets try and load directly from file */
                GString *str;
                
                if ( strstr(name, "/") != NULL )
                        str = g_string_new(name);
                else {
                        str = g_string_new("/usr/local/share/pixmaps/");
                        g_string_append(str, name);
                }
                
                icon = gdk_pixbuf_new_from_file_at_scale(str->str, 
                                                         width,
                                                         -1,
                                                         TRUE, NULL);
                g_string_free(str, TRUE);
        }
        
        if (icon == NULL) {
                GString *str;
                
                str = g_string_new("/usr/share/");
                g_string_append(str, name);
                g_string_erase(str, (str->len - 4), -1 );
                g_string_append(str, "/");
		g_string_append(str, "pixmaps/");
		g_string_append(str, name);
		
		icon = gdk_pixbuf_new_from_file_at_scale
       		                             (str->str,
                                             width,
                                             -1,
                                             TRUE,
                                             NULL);
                g_string_free(str, TRUE);
        }
        
        if (icon == NULL) {
                GString *str = NULL;
                str = g_string_new (name);
                if (str->len > 4) 
	                str = g_string_erase (str, str->len-4, -1);
                icon = gtk_icon_theme_load_icon( theme, str->str, width, GTK_ICON_LOOKUP_FORCE_SVG, NULL);
        	g_string_free (str, TRUE);
        }        
        return icon;

}


