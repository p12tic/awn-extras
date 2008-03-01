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

#include <string.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-config-client.h>
#include <glib/gmacros.h>
#include <glib/gerror.h>

#include <libawn/awn-cairo-utils.h>

#include "filebrowser-gconf.h"
#include "filebrowser-defines.h"

static AwnConfigClient *client = NULL;
static AwnApplet *applet = NULL;

/**
 * Initializes the GConf stuff
 */
void filebrowser_gconf_init(
    AwnApplet * awn_applet, gchar * uid ) {

    if ( !client ) {
        client = awn_config_client_new_for_applet("filebrowser",uid);
    }
    if ( !applet ) {
        applet = awn_applet;
    }
}

/**
 * Should we be creative and composite the applet icon
 */
gboolean filebrowser_gconf_is_composite_applet_icon() {
    gboolean iscomp;

    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_COMPOSITE_APPLET_ICON,
                                   NULL);
    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        iscomp = awn_config_client_get_bool( client, 
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                   FILEBROWSER_GCONFKEY_COMPOSITE_APPLET_ICON,
                                   NULL);
    }
    else
    {
            iscomp = FILEBROWSER_DEFAULT_COMPOSITE_APPLET_ICON;
            awn_config_client_set_bool( client,
                         AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                         FILEBROWSER_GCONFKEY_COMPOSITE_APPLET_ICON,
                         iscomp, NULL );
    }
    return iscomp;
}

gboolean filebrowser_gconf_is_browsing(){
    gboolean browsing;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_ENABLE_BROWSING,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        browsing = awn_config_client_get_bool( client,   AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                            FILEBROWSER_GCONFKEY_ENABLE_BROWSING,
                                            NULL );
    }
    else
    {
        browsing = FILEBROWSER_DEFAULT_ENABLE_BROWSING;
        awn_config_client_set_bool( client,
                     AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                     FILEBROWSER_GCONFKEY_ENABLE_BROWSING,
                     browsing, NULL );
    }
        
    return browsing;
}

gboolean filebrowser_gconf_show_files(){
	
	gboolean show;
    
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_SHOW_FILES,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        show = awn_config_client_get_bool(client,   AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                            FILEBROWSER_GCONFKEY_SHOW_FILES,
                                            NULL );
    }
    else
    {
        show = FILEBROWSER_DEFAULT_SHOW_FILES;
        awn_config_client_set_bool( client,
                     AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                    FILEBROWSER_GCONFKEY_SHOW_FILES,
                     show, NULL );
    }
        
    return show;
}

gboolean filebrowser_gconf_show_hidden_files(){

	gboolean show;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_SHOW_HIDDEN_FILES,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        show = awn_config_client_get_bool(client,   AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                        FILEBROWSER_GCONFKEY_SHOW_HIDDEN_FILES,
                                        NULL );
    }
    else
    {
        show = FILEBROWSER_DEFAULT_SHOW_HIDDEN_FILES;
        awn_config_client_set_bool( client,
                     AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                     FILEBROWSER_GCONFKEY_SHOW_HIDDEN_FILES,
                     show, NULL );
    }
    return show;
}

gboolean filebrowser_gconf_show_folders(){

	gboolean show;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_SHOW_FOLDERS,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        show = awn_config_client_get_bool(client,AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                            FILEBROWSER_GCONFKEY_SHOW_FOLDERS,
                                            NULL );
    }
    else
    {
        show = FILEBROWSER_DEFAULT_SHOW_FOLDERS;
        awn_config_client_set_bool( client,
                         AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                         FILEBROWSER_GCONFKEY_SHOW_FOLDERS,
                         show, NULL );
    }
    return show;
}

gboolean filebrowser_gconf_show_desktop_items(){

	gboolean show;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_SHOW_DESKTOP_ITEMS,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
            
        show = awn_config_client_get_bool(client,AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                            FILEBROWSER_GCONFKEY_SHOW_DESKTOP_ITEMS,
                                            NULL );
    }
    else
    {
            show = FILEBROWSER_DEFAULT_SHOW_DESKTOP_ITEMS;
            awn_config_client_set_bool( client,
                         AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                         FILEBROWSER_GCONFKEY_SHOW_DESKTOP_ITEMS,
                         show, NULL );
    }
    return show;
}

/**
 * What is the backend folder of this applet (and is it set)?
 */
gchar *filebrowser_gconf_get_backend_folder() {
	gchar *folder = NULL;
    folder = awn_config_client_get_string(client,AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                                FILEBROWSER_GCONFKEY_BACKEND_FOLDER,
                                                NULL );
    if ( !folder || (strlen(folder)==0) )
    {
        g_free(folder);
        folder = g_strdup_printf( "/home/%s", g_get_user_name(  ) );
        filebrowser_gconf_set_backend_folder( folder );
    }
    printf("folder = %s\n",folder);
    return folder;
}

/**
 * What is the default drag action?
 */
gchar *filebrowser_gconf_get_default_drag_action() {
	gchar *action = NULL;
    action = awn_config_client_get_string(client,AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                                FILEBROWSER_GCONFKEY_DEFAULT_DRAG_ACTION,
                                                NULL );
    if (!action)
    {
         action = g_strdup(FILEBROWSER_DEFAULT_DEFAULT_DRAG_ACTION DRAG_ACTION_LINK);
         awn_config_client_set_string( client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_DEFAULT_DRAG_ACTION,
                                   action, NULL );

    }
    return action;
}

/**
 * Set the backend folder of this applet
 */
void filebrowser_gconf_set_backend_folder(
    const gchar * folder ) {
	
	awn_config_client_set_string (client,
                                    AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                    FILEBROWSER_GCONFKEY_BACKEND_FOLDER,
                                    folder, NULL );  
}

/**
 * Get the icon to use for the applet
 */
gchar          *filebrowser_gconf_get_applet_icon(
) {
	gchar *icon= NULL;
    icon = awn_config_client_get_string(client,AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                        FILEBROWSER_GCONFKEY_APPLET_ICON,
                                        NULL );
    if (!icon)
    {
         icon = g_strdup(FILEBROWSER_DEFAULT_APPLET_ICON);
         awn_config_client_set_string(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_APPLET_ICON,
                                   icon, NULL );

    }
    return icon;
}

/**
 * Get the preferred size of the icons in the filebrowser
 */
guint filebrowser_gconf_get_icon_size(
) {
	guint icon_size;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_ICON_SIZE,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        icon_size = awn_config_client_get_int(client,   AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                            FILEBROWSER_GCONFKEY_ICON_SIZE,
                                            NULL );
    }
    else
    {
        icon_size = FILEBROWSER_DEFAULT_ICON_SIZE;
        awn_config_client_set_int( client,
                     AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                     FILEBROWSER_GCONFKEY_ICON_SIZE,
                     icon_size, NULL );
    }
        
    return icon_size;
}

guint filebrowser_gconf_get_max_rows(){
	guint rows;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                   FILEBROWSER_GCONFKEY_MAX_ROWS,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {

        rows = awn_config_client_get_int(client,AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                            FILEBROWSER_GCONFKEY_MAX_ROWS,
    										NULL );
    }
    else
    {
        rows = FILEBROWSER_DEFAULT_MAX_ROWS;
        awn_config_client_set_int( client,
                     AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                     FILEBROWSER_GCONFKEY_MAX_ROWS,
                     rows, NULL );
    }
    printf("rows = %d\n",rows);
    return rows;

}

guint filebrowser_gconf_get_max_cols(){
	guint cols;
    AwnConfigValueType value = awn_config_client_get_value_type(client,
                                   AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                    FILEBROWSER_GCONFKEY_MAX_COLS,
                                   NULL);    
    if (value!=AWN_CONFIG_VALUE_TYPE_NULL)
    {
        cols = awn_config_client_get_int(client,   AWN_CONFIG_CLIENT_DEFAULT_GROUP, 
                                            FILEBROWSER_GCONFKEY_MAX_COLS,
                                            NULL );
    }
    else
    {
        printf("BOOGER\n");
        cols =  FILEBROWSER_DEFAULT_MAX_COLS;
        awn_config_client_set_int( client,
                     AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                     FILEBROWSER_GCONFKEY_MAX_COLS,
                     cols, NULL );
    }        
    printf("cols = %d\n",cols);
    return cols;
}

