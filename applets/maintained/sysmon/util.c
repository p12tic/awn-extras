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
           gchar * group, gchar * key_name,gchar * prop_name )
{
  DesktopAgnosticConfigClient * client;
  DesktopAgnosticConfigClient * client_baseconf;  
  gchar * base_prop_name = g_strdup_printf( "%s-base",prop_name);
  GError *error = NULL;
  
  g_object_get (applet,
                "client-baseconf", &client_baseconf,
                NULL);
  g_object_get (object,
                "client", &client,
                NULL);
  desktop_agnostic_config_client_bind (client,
                                       group, key_name,
                                       object, prop_name, FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       &error);

  if (error)
  {
    goto do_bridge_error;
  }

  desktop_agnostic_config_client_bind (client_baseconf,
                                       group, key_name,
                                       object, base_prop_name, FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       &error);
do_bridge_error:

  g_free (base_prop_name);

  if (error)
  {
    g_critical ("Config Bridge Error: %s", error->message);
    g_error_free (error);
  }
  
}

void
connect_notify (GObject * object,gchar * prop_name,GCallback cb,gpointer data)
{
  gchar * sig_name;
  
  sig_name = g_strdup_printf( "notify::%s",prop_name);  
  g_signal_connect (object, sig_name,cb,data);
  g_free (sig_name);
  sig_name = g_strdup_printf( "notify::%s-base",prop_name);  
  g_signal_connect (object, sig_name,cb,data);
  g_free(sig_name);
}
