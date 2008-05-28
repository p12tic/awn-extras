/*
 * Copyright (C) 2008 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */

#include <gtk/gtk.h>
#include "awn-extras.h" 

static gboolean _start_applet_prefs(GtkWidget *widget, GdkEventButton *event, void * null)
{
	GError *err=NULL; 
    g_spawn_command_line_async("gconf-editor",&err);//FIXME
    if (err)
    {
        g_error_free (err);
    }
    
    return TRUE;
}

static gboolean _start_awn_manager(GtkWidget *widget, GdkEventButton *event, void * null)
{
	GError *err=NULL; 
    g_spawn_command_line_async("awn-manager",&err);
    if (err)
    {
        g_error_free (err);
    }
    return TRUE;
}

static gboolean _close_awn(GtkWidget *widget, GdkEventButton *event, void * null)
{
	GError *err=NULL;
    g_spawn_command_line_async("killall awn",&err);//FIXME
    if (err)
    {
        g_error_free (err);
    }
    return TRUE;
}

GtkWidget * create_applet_menu(GtkWidget * menu, guint features)
{
    GtkWidget *item;  
    if (!menu)
    {
        menu = gtk_menu_new (); 
        gtk_menu_set_screen (GTK_MENU (menu), NULL);   
    }
    if ( features  & AWN_MENU_APPLET_PREFS_ENABLE)
    {
        if ( share_config_bool ( SHR_KEY_GENERIC_PREFS ) )
        {
            item = create_applet_menu_item(AWN_MENU_ITEM_APPLET_PREFS);
            gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);
        }
        else
        {
            g_warning("Generic Preferences Requested but support is not enabled in configuration\n");
        }
    }
    if ( ! (features  & AWN_MENU_MANAGER_DISABLE) )
    {
        item = create_applet_menu_item(AWN_MENU_ITEM_MANAGER);
        gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);      
    }
    if ( ! (features  & AWN_MENU_CLOSE_DISABLE) )
    {
        item = create_applet_menu_item(AWN_MENU_ITEM_CLOSE);
        gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);          
    }
    return menu;
}

GtkWidget * create_applet_menu_item(AwnMenuItem menu_item_type)
{
    GtkWidget * item=NULL;
    switch (menu_item_type)
    {
        case AWN_MENU_ITEM_MANAGER:
            item = gtk_image_menu_item_new_with_label ("Awn Preferences");
            g_signal_connect (G_OBJECT (item), "button-press-event",
                        G_CALLBACK (_start_awn_manager), NULL);
            break;
        case AWN_MENU_ITEM_CLOSE:
            item = gtk_image_menu_item_new_with_label ("Close");
            g_signal_connect (G_OBJECT (item), "button-press-event",
                        G_CALLBACK (_close_awn), NULL);
            break;
        case AWN_MENU_ITEM_APPLET_PREFS:
            item = gtk_image_menu_item_new_with_label ("Applet Preferences");        
            g_signal_connect (G_OBJECT (item), "button-press-event",
                        G_CALLBACK (_start_applet_prefs), NULL);
            break;
    }  
    gtk_widget_show_all(item);
    return item;
}
