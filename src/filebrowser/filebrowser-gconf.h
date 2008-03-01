/*
 * Copyright (c) 2007 Timon David Ter Braak
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

#ifndef __FILEBROWSER_GCONF_H__
#define __FILEBROWSER_GCONF_H__

#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>

void filebrowser_gconf_init( AwnApplet * applet, gchar * uid );
    
gboolean filebrowser_gconf_is_composite_applet_icon();
gboolean filebrowser_gconf_is_browsing();
gchar *filebrowser_gconf_get_backend_folder();
gchar *filebrowser_gconf_get_drag_action();

void filebrowser_gconf_set_backend_folder( const gchar * folder );

gchar *filebrowser_gconf_get_applet_icon();
gchar *filebrowser_gconf_get_default_drag_action();

guint filebrowser_gconf_get_icon_size();
guint filebrowser_gconf_get_max_rows();
guint filebrowser_gconf_get_max_cols();

gboolean filebrowser_gconf_show_files();
gboolean filebrowser_gconf_show_hidden_files();
gboolean filebrowser_gconf_show_folders();
gboolean filebrowser_gconf_show_desktop_items();

#endif /* __FILEBROWSER_GCONF_H__ */
