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

#include <string.h>

#include <libawn/awn-desktop-item.h>
#include <libawn/awn-vfs.h>

#ifdef LIBAWN_USE_GNOME
#include <libgnomeui/gnome-icon-lookup.h>
#include <libgnomeui/gnome-thumbnail.h>
#else
#include "egg-pixbuf-thumbnail.h"
#ifdef LIBAWN_USE_XFCE
#include <thunar-vfs/thunar-vfs.h>
#else
#include <gio/gio.h>
#endif
#endif

#include "aff-utils.h"

#define METADATA_IMAGE_SIZE	48

GdkPixbuf *
aff_utils_get_icon (const char *uri)
{
    return aff_utils_get_icon_sized (uri, METADATA_IMAGE_SIZE, METADATA_IMAGE_SIZE);
}

GdkPixbuf *
aff_utils_get_icon_sized (const char *uri, gint width, gint height)
{
	gchar *icon_name = NULL;
	gchar *thumb_name = NULL;
	GdkPixbuf *temp = NULL;
	gchar *local_uri = NULL;
	GtkIconTheme *theme = gtk_icon_theme_get_default ();
	
#ifdef LIBAWN_USE_GNOME
    local_uri = gnome_vfs_get_local_path_from_uri (uri);
	thumb_name = gnome_thumbnail_path_for_uri (uri, GNOME_THUMBNAIL_SIZE_NORMAL);
	temp = gdk_pixbuf_new_from_file_at_scale (thumb_name, width, height, TRUE, NULL);
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
#else
#ifdef LIBAWN_USE_XFCE
    ThunarVfsPath *path = thunar_vfs_path_new (uri, NULL);
    local_uri = thunar_vfs_path_dup_string (path);
    thunar_vfs_path_unref (path);
#else
    GFile *file = g_file_new_for_uri (uri);
    local_uri = g_file_get_path (file);
    g_free (file);
#endif
    temp = egg_pixbuf_get_thumbnail_for_file_at_size (local_uri, height, NULL);
    if (temp) {
        g_free (local_uri);
        return temp;
    }
#ifdef LIBAWN_USE_XFCE
    ThunarVfsMimeDatabase *mime_db = thunar_vfs_mime_database_get_default ();
    ThunarVfsMimeInfo *mime_info = thunar_vfs_mime_database_get_info_for_file (mime_db, local_uri, NULL);
    icon_name = thunar_vfs_mime_info_lookup_icon_name (mime_info, theme);
    thunar_vfs_mime_info_unref (mime_info);
#else
    GIcon *icon;
    // not using g_content_type_get_icon because it's not implemented as of glib 2.15.4
    gchar *content_type = g_content_type_guess (local_uri, NULL, 0, NULL);
    icon = g_content_type_get_icon (content_type);
    if (!icon) {
        GAppInfo *app_info = g_app_info_get_default_for_type (g_content_type_guess (local_uri, NULL, 0, NULL), FALSE);
        icon = g_app_info_get_icon (app_info);
        g_free (app_info);
    }
    if (G_IS_FILE_ICON (icon)) {
        temp = egg_pixbuf_get_thumbnail_for_file_at_size ((gchar*)g_file_icon_get_file (G_FILE_ICON(icon)), height, NULL);
        if (temp) {
            g_free (icon);
            g_free (local_uri);
            return temp;
        }
    } else if (G_IS_THEMED_ICON (icon)) {
        icon_name = (gchar*)(g_themed_icon_get_names (G_THEMED_ICON (icon))[0]);
    }
    g_free (icon);
#endif
#endif
	temp = gtk_icon_theme_load_icon (theme,
                                         icon_name,
                                         height,
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
    return aff_utils_get_app_icon_sized (name, METADATA_IMAGE_SIZE, METADATA_IMAGE_SIZE);
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
