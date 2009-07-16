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


#include "applet.h"
#include "configuration.h"

static gchar *
get_string (WebApplet *webapplet, const gchar *key)
{
  return desktop_agnostic_config_client_get_string (webapplet->config,
                                                    DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                                    key, NULL);
}

static void
set_string(WebApplet *webapplet, const gchar *key, gchar *val)
{
  desktop_agnostic_config_client_set_string (webapplet->config,
                                             DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                             key, val, NULL);
}

static gboolean
get_bool (WebApplet *webapplet, const gchar *key)
{
  return desktop_agnostic_config_client_get_bool (webapplet->config,
                                                  DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                                  key, NULL);
}

static void
set_bool(WebApplet *webapplet, const gchar *key, gboolean val)
{
  desktop_agnostic_config_client_set_bool (webapplet->config,
                                           DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                           key, val, NULL);
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

void
config_set_uri(WebApplet *webapplet, gchar *uri)
{
  set_string(webapplet, CONFIG_URI, uri);
}

const gchar *
config_get_site(WebApplet *webapplet)
{
  static gchar *str = NULL;
  if (str)
    g_free(str);

  str = get_string(webapplet, CONFIG_SITE);

  return str;
}

void
config_set_site(WebApplet *webapplet, gchar *site)
{
  set_string(webapplet, CONFIG_SITE, site);
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

gboolean
config_get_first_start(WebApplet *webapplet)
{
  return get_bool(webapplet, CONFIG_FIRST_START);
}

void
config_set_first_start(WebApplet *webapplet, gboolean val)
{
  set_bool(webapplet, CONFIG_FIRST_START, val);
}

void
init_config(WebApplet *webapplet)
{
  GTimeVal time_val;
  g_get_current_time (&time_val);
  gchar* date_time = g_time_val_to_iso8601 (&time_val);
  webapplet->config = awn_config_get_default_for_applet (webapplet->applet,
                                                         NULL);

  desktop_agnostic_config_client_set_string(webapplet->config,
                                            DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                            CONFIG_LAST_ACCESS, date_time, NULL);
  g_free (date_time);
}
/* vim: set et ts=2 sts=2 sw=2 : */
