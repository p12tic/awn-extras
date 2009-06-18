/*
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
 
#include <glib.h>
#include "util.h"

gdouble 
get_double_time(void)
{
  GTimeVal  timeval;
  g_get_current_time (&timeval);
  return  timeval.tv_sec + timeval.tv_usec / 1000000.0;
}

gint 
get_conf_value_int ( GObject * object, gchar * prop_name)
{
  gint  i,b;
  gchar * base_prop_name = g_strdup_printf( "%s-base",prop_name);
  
  g_object_get(object,
               prop_name,&i,
               base_prop_name,&b,
               NULL);
  g_free (base_prop_name);
  
  /*CONDITIONAL operator*/
  return i?i:b;
}

void
do_bridge ( AwnApplet * applet,GObject *object,
           gchar * instance_group,gchar * base_group,
           gchar * key_name,gchar * prop_name )
{
  AwnConfigClient * client;
  AwnConfigBridge * bridge;
  AwnConfigClient * client_baseconf;  
  gchar * base_prop_name = g_strdup_printf( "%s-base",prop_name);  
  
  g_object_get (applet,
                "client", &client,
                "bridge", &bridge,
                "client-baseconf", &client_baseconf,
                NULL);              

  awn_config_bridge_bind (bridge, client,
                          instance_group, key_name,
                          G_OBJECT(object), prop_name);
  
  awn_config_bridge_bind (bridge, client_baseconf,
                          base_group, key_name,
                          G_OBJECT(object),base_prop_name);
  
  g_free (base_prop_name);
}