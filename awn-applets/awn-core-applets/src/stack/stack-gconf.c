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
#include <gconf/gconf-client.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-gconf.h>
#include <libawn/awn-cairo-utils.h>

#include "stack-gconf.h"
#include "stack-defines.h"

static GConfClient *client = NULL;
static AwnApplet *applet = NULL;

/**
 * Initializes the GConf stuff
 */
void stack_gconf_init(
    AwnApplet * awn_applet ) {

    if ( !client ) {
        client = gconf_client_get_default(  );
    }
    if ( !applet ) {
        applet = awn_applet;
    }

    awn_applet_add_preferences( awn_applet, "/schemas/apps/awn-stack/prefs", NULL );
}

/**
 * Should we be creative and composite the applet icon
 */
gboolean stack_gconf_is_composite_applet_icon(
) {

    gboolean iscomp;
    GConfValue *value = awn_applet_gconf_get_value( applet,
                            STACK_GCONFKEY_COMPOSITE_APPLET_ICON,
                            NULL );

    if ( value ) {
        iscomp = awn_applet_gconf_get_bool( applet, STACK_GCONFKEY_COMPOSITE_APPLET_ICON, NULL );
    } else {
        iscomp = STACK_DEFAULT_COMPOSITE_APPLET_ICON;
        awn_applet_gconf_set_bool( applet,
                                   STACK_GCONFKEY_COMPOSITE_APPLET_ICON,
                                   STACK_DEFAULT_COMPOSITE_APPLET_ICON, NULL );
    }

    return iscomp;
}

gboolean stack_gconf_is_browsing(){
    gboolean browsing;
    GConfValue *value = awn_applet_gconf_get_value( applet,
                            STACK_GCONFKEY_ENABLE_BROWSING,
                            NULL );

    if ( value ) {
        browsing = awn_applet_gconf_get_bool( applet, STACK_GCONFKEY_ENABLE_BROWSING, NULL );
    } else {
        browsing = STACK_DEFAULT_ENABLE_BROWSING;
        awn_applet_gconf_set_bool( applet,
                                   STACK_GCONFKEY_ENABLE_BROWSING,
                                   STACK_DEFAULT_ENABLE_BROWSING, NULL );
    }

    return browsing;
}

gboolean stack_gconf_show_files(){
	
	gboolean show;
    GConfValue *value = awn_applet_gconf_get_value( applet,
                            STACK_GCONFKEY_SHOW_FILES,
                            NULL );

    if ( value ) {
        show = awn_applet_gconf_get_bool( applet, STACK_GCONFKEY_SHOW_FILES, NULL );
    } else {
        show = STACK_DEFAULT_SHOW_FILES;
        awn_applet_gconf_set_bool( applet,
                                   STACK_GCONFKEY_SHOW_FILES,
                                   STACK_DEFAULT_SHOW_FILES, NULL );
    }

    return show;
}

gboolean stack_gconf_show_hidden_files(){

	gboolean show;
    GConfValue *value = awn_applet_gconf_get_value( applet,
                            STACK_GCONFKEY_SHOW_HIDDEN_FILES,
                            NULL );

    if ( value ) {
        show = awn_applet_gconf_get_bool( applet, STACK_GCONFKEY_SHOW_HIDDEN_FILES, NULL );
    } else {
        show = STACK_DEFAULT_SHOW_HIDDEN_FILES;
        awn_applet_gconf_set_bool( applet,
                                   STACK_GCONFKEY_SHOW_HIDDEN_FILES,
                                   STACK_DEFAULT_SHOW_HIDDEN_FILES, NULL );
    }

    return show;
}

gboolean stack_gconf_show_folders(){

	gboolean show;
    GConfValue *value = awn_applet_gconf_get_value( applet,
                            STACK_GCONFKEY_SHOW_FOLDERS,
                            NULL );

    if ( value ) {
        show = awn_applet_gconf_get_bool( applet, STACK_GCONFKEY_SHOW_FOLDERS, NULL );
    } else {
        show = STACK_DEFAULT_SHOW_FOLDERS;
        awn_applet_gconf_set_bool( applet,
                                   STACK_GCONFKEY_SHOW_FOLDERS,
                                   STACK_DEFAULT_SHOW_FOLDERS, NULL );
    }

    return show;
}

gboolean stack_gconf_show_desktop_items(){

	gboolean show;
    GConfValue *value = awn_applet_gconf_get_value( applet,
                            STACK_GCONFKEY_SHOW_DESKTOP_ITEMS,
                            NULL );

    if ( value ) {
        show = awn_applet_gconf_get_bool( applet, STACK_GCONFKEY_SHOW_DESKTOP_ITEMS, NULL );
    } else {
        show = STACK_DEFAULT_SHOW_DESKTOP_ITEMS;
        awn_applet_gconf_set_bool( applet,
                                   STACK_GCONFKEY_SHOW_DESKTOP_ITEMS,
                                   STACK_DEFAULT_SHOW_DESKTOP_ITEMS, NULL );
    }

    return show;
}

/**
 * What is the backend folder of this applet (and is it set)?
 */
gchar *stack_gconf_get_backend_folder(
) {

    gchar *folder = awn_applet_gconf_get_string( applet,
                             STACK_GCONFKEY_BACKEND_FOLDER,
                             NULL );

    if ( strlen( folder ) < 1 ) {
        folder = g_strdup_printf( "/home/%s", g_get_user_name(  ) );
        stack_gconf_set_backend_folder( folder );
    }

    return folder;
}

/**
 * What is the default drag action?
 */
gchar *stack_gconf_get_default_drag_action() {

    gchar *action = awn_applet_gconf_get_string( applet,
                             STACK_GCONFKEY_DEFAULT_DRAG_ACTION,
                             NULL );

    if ( strlen( action ) < 1 ) {
		awn_applet_gconf_set_string( applet,
                                     STACK_GCONFKEY_DEFAULT_DRAG_ACTION, STACK_DEFAULT_DEFAULT_DRAG_ACTION, NULL );
        action = STACK_DEFAULT_DEFAULT_DRAG_ACTION;
    }

    return action;
}

/**
 * Set the backend folder of this applet
 */
void stack_gconf_set_backend_folder(
    const gchar * folder ) {

    awn_applet_gconf_set_string( applet, STACK_GCONFKEY_BACKEND_FOLDER, folder, NULL );
}

/**
 * Get the icon to use for the applet
 */
gchar          *stack_gconf_get_applet_icon(
) {

    gchar          *icon = awn_applet_gconf_get_string( applet,
                           STACK_GCONFKEY_APPLET_ICON,
                           NULL );

    if ( !icon ) {
        awn_applet_gconf_set_string( applet,
                                     STACK_GCONFKEY_APPLET_ICON, STACK_DEFAULT_APPLET_ICON, NULL );
        icon = STACK_DEFAULT_APPLET_ICON;
    }

    return icon;
}

/**
 * Get the preferred size of the icons in the stack
 */
guint stack_gconf_get_icon_size(
) {

    guint icon_size = awn_applet_gconf_get_int( applet,
                                STACK_GCONFKEY_ICON_SIZE, NULL );

    if ( !( icon_size > 0 ) ) {
        awn_applet_gconf_set_int( applet, STACK_GCONFKEY_ICON_SIZE, STACK_DEFAULT_ICON_SIZE, NULL );
        icon_size = STACK_DEFAULT_ICON_SIZE;
    }

    return icon_size;
}

guint stack_gconf_get_max_rows(){

    guint rows = awn_applet_gconf_get_int( applet,
                                STACK_GCONFKEY_MAX_ROWS, NULL );

    if ( !( rows > 0 ) ) {
        awn_applet_gconf_set_int( applet, STACK_GCONFKEY_MAX_ROWS, STACK_DEFAULT_MAX_ROWS, NULL );
        rows = STACK_DEFAULT_MAX_ROWS;
    }

    return rows;
}

guint stack_gconf_get_max_cols(){

    guint cols = awn_applet_gconf_get_int( applet,
                                STACK_GCONFKEY_MAX_COLS, NULL );

    if ( !( cols > 0 ) ) {
        awn_applet_gconf_set_int( applet, STACK_GCONFKEY_MAX_COLS, STACK_DEFAULT_MAX_COLS, NULL );
        cols = STACK_DEFAULT_MAX_COLS;
    }

    return cols;
}


/**
 * Get a color from a GConf key
 */
static void stack_gconf_get_color(
    AwnColor * color,
    const gchar * key,
    const gchar * def ) {

    gchar *value = awn_applet_gconf_get_string( applet, key, NULL );

    if ( !value ) {
        awn_applet_gconf_set_string( applet, key, def, NULL );
        value = g_strdup( def );
    }

	awn_cairo_string_to_color( value, color );
}

/**
 * Get the color for the borders (lines)
 */
void stack_gconf_get_border_color (AwnColor *color){

	stack_gconf_get_color (color, STACK_GCONFKEY_BORDER_COLOR,
	  STACK_DEFAULT_BORDER_COLOR);
}

/**
 * Get the color for the background
 */
void stack_gconf_get_background_color (AwnColor *color){

	stack_gconf_get_color (color, STACK_GCONFKEY_BACKGROUND_COLOR,
      STACK_DEFAULT_BACKGROUND_COLOR);
}

/**
 * Get the color for the icons text
 */
void stack_gconf_get_icontext_color (AwnColor *color){

   stack_gconf_get_color (color, STACK_GCONFKEY_ICONTEXT_COLOR,
   STACK_DEFAULT_ICONTEXT_COLOR);
}

