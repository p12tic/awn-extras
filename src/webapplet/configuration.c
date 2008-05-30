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
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
 */


#include <libawn/awn-config-client.h>

#include "applet.h"
#include "configuration.h"

static gchar *
get_string (WebApplet *webapplet, const gchar *key)
{
  gchar *str=NULL;
  if (awn_config_client_entry_exists (webapplet->instance_config,
                                      AWN_CONFIG_CLIENT_DEFAULT_GROUP,key) )
  {        
    str = awn_config_client_get_string (webapplet->instance_config,
                                      AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                      key, NULL);
  }    
  if (!str)
  {
    str = awn_config_client_get_string (webapplet->default_config,
                                        AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                        key, NULL);
  }
  return str;
}

static gboolean
get_bool (WebApplet *webapplet, const gchar *key)
{
  gboolean value;
  if (awn_config_client_entry_exists (webapplet->instance_config,
                                      AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                      key)) {
    value = awn_config_client_get_bool (webapplet->instance_config,
                                        AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                        key, NULL);
  }
  else
  {
    value = awn_config_client_get_bool (webapplet->default_config,
                                        AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                        key, NULL);
  }
  return value;
}

gint
get_width (WebApplet *webapplet)
{
  gchar *str = get_string (webapplet, CONFIG_WIDTH);
  gint width;
  if (g_strrstr (str, "%"))
  {
    gint screen_width;
    double percent;
    screen_width = gdk_screen_get_width (gdk_screen_get_default ());
    percent = g_strtod (str, NULL);
    width = (gint)(screen_width * percent / 100.0);
  }
  else
  {
    width = (gint)g_strtod (str, NULL);
  }
  g_free (str);
  return width;
}

gint
get_height (WebApplet *webapplet)
{
  gchar *str = get_string (webapplet, CONFIG_HEIGHT);
  gint height;
  if (g_strrstr (str, "%"))
  {
    gint screen_height;
    double percent;
    screen_height = gdk_screen_get_height (gdk_screen_get_default ());
    percent = g_strtod (str, NULL);
    height = (gint)(screen_height * percent / 100.0);
  }
  else
  {
    height = (gint)g_strtod (str, NULL);
  }
  g_free (str);
  return height;
}

const gchar * 
config_get_uri(WebApplet *webapplet)
{
    static gchar * str=NULL;
    if (str)
    {
        g_free(str);
    }
    str=get_string (webapplet, CONFIG_URI);
    return str;
}  

gint 
config_get_width(WebApplet *webapplet)
{
  return get_width (webapplet);
}  

gint 
config_get_height(WebApplet *webapplet)
{
  return get_height (webapplet);
}

gboolean 
config_get_enable_location_dialog(WebApplet *webapplet)
{
  return get_bool (webapplet, CONFIG_ENABLE_LOCATION_CONFIG);
}  

void
init_config(WebApplet *webapplet, gchar *uid)
{
  GTimeVal time_val;
  g_get_current_time (&time_val);
  gchar* date_time = g_time_val_to_iso8601 (&time_val);
  webapplet->default_config = awn_config_client_new_for_applet (APPLET_NAME,
                                                                NULL);
  webapplet->instance_config = awn_config_client_new_for_applet (APPLET_NAME,
                                                                 uid);

  awn_config_client_set_string(webapplet->instance_config,
                               AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                               CONFIG_LAST_ACCESS, date_time, NULL);
  g_free (date_time);
}
/* vim: set et ts=2 sts=2 sw=2 : */
