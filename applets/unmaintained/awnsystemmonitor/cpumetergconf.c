/*
 * Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
 *
 * This is a CPU Load Applet for the Avant Window Navigator.  This module is
 * for managing the gconf settings.
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
#include <glib.h>
#include <gconf/gconf-value.h>

#include <libawn/awn-applet.h>
#include <gconf/gconf-value.h>

#include "cairo-utils.h"

#include "awnsystemmonitor.h"
#include "config.h"
#include "gconf-config.h"
void cpumeter_gconf_event(GConfClient* client, guint cxnid, GConfEntry* entry, gpointer user_data);
void cpumeter_gconf_get_color(GConfClient* client, AwnColor* color, gchar* key, gchar* def);
gfloat cpumeter_gconf_get_border_width(GConfClient* client);
gboolean cpumeter_gconf_use_gradient(GConfClient* client);
gboolean cpumeter_gconf_do_subtitle(GConfClient* client);
guint cpumeter_gconf_get_update_frequency(GConfClient* client);

/**
 * Initializes the GConf stuff
 */
void cpumeter_gconf_init(CpuMeter* cpumeter)
{
  cpumeter->client = gconf_client_get_default();
  // TODO - Add Callback for updates
  gconf_client_add_dir(cpumeter->client, GCONF_PATH, GCONF_CLIENT_PRELOAD_NONE, NULL);
  gconf_client_notify_add(cpumeter->client, GCONF_PATH, cpumeter_gconf_event, cpumeter, NULL, NULL);
}

/**
 * GConf callback, receives notifications of configuration changes.
 */
void cpumeter_gconf_event(GConfClient* client, guint cxnid, GConfEntry* entry, gpointer user_data)
{
  CpuMeter* cpumeter = (CpuMeter*)user_data;

  // Re-read everything instead of trying to figure out what changed.
  cpumeter_gconf_get_color(client, &cpumeter->bg, GCONF_BG_COLOR, GCONF_DEFAULT_BG_COLOR);
  cpumeter_gconf_get_color(client, &cpumeter->graph, GCONF_GRAPH_COLOR, GCONF_DEFAULT_GRAPH_COLOR);
  cpumeter_gconf_get_color(client, &cpumeter->border, GCONF_BORDER_COLOR, GCONF_DEFAULT_BORDER_COLOR);
  cpumeter->border_width = cpumeter_gconf_get_border_width(client);
  cpumeter->do_gradient = cpumeter_gconf_use_gradient(client);
  cpumeter->do_subtitle = cpumeter_gconf_do_subtitle(client);
  cpumeter->update_freq = cpumeter_gconf_get_update_frequency(client);

#if 0
  /*this is causing strange issues with the render function - removing */

  if (cpumeter->timer_id != -1)
  {
    g_source_remove(cpumeter->timer_id);
  }

  cpumeter->timer_id = g_timeout_add(cpumeter->update_freq, (GSourceFunc*)cpu_meter_render, cpumeter);

#endif
}

/**
 * Gets a color component from gconf
 */
void cpumeter_gconf_get_color(GConfClient* client, AwnColor* color, gchar* key, gchar* def)
{
  gchar *value = gconf_client_get_string(client, key, NULL);

  if (!value)
  {
    gconf_client_set_string(client, key, def, NULL);
    value = g_strdup(def);
  }

  awn_cairo_string_to_color(value, color);
}

/**
 * Gets the border width
 */
gfloat cpumeter_gconf_get_border_width(GConfClient* client)
{
  gfloat width;
  GConfValue *value = gconf_client_get(client, GCONF_BORDER_WIDTH, NULL);

  if (value)
  {
    width = gconf_client_get_float(client, GCONF_BORDER_WIDTH, NULL);
  }
  else
  {
    width = GCONF_DEFAULT_BORDER_WIDTH;
    gconf_client_set_float(client, GCONF_BORDER_WIDTH, GCONF_DEFAULT_BORDER_WIDTH, NULL);
  }

  return width;
}


/**
 * Should we do the pretty gradient on the graph.
 */
gboolean cpumeter_gconf_use_gradient(GConfClient* client)
{
  gboolean do_gradient;
  GConfValue *value = gconf_client_get(client, GCONF_DO_GRADIENT, NULL);

  if (value)
  {
    do_gradient = gconf_client_get_bool(client, GCONF_DO_GRADIENT, NULL);
  }
  else
  {
    do_gradient = GCONF_DEFAULT_DO_GRADIENT;
    gconf_client_set_bool(client, GCONF_DO_GRADIENT, GCONF_DEFAULT_DO_GRADIENT, NULL);
  }

  return do_gradient;
}


/**
 * Should we do the CPU - nn% subtitle?
 */
gboolean cpumeter_gconf_do_subtitle(GConfClient* client)
{
  gboolean do_subtitle;
  GConfValue *value = gconf_client_get(client, GCONF_DO_SUBTITLE, NULL);

  if (value)
  {
    do_subtitle = gconf_client_get_bool(client, GCONF_DO_SUBTITLE, NULL);
  }
  else
  {
    do_subtitle = GCONF_DEFAULT_DO_SUBTITLE;
    gconf_client_set_bool(client, GCONF_DO_SUBTITLE, GCONF_DEFAULT_DO_SUBTITLE, NULL);
  }

  return do_subtitle;
}


/**
 * Get the graph update frequency.
 */
guint cpumeter_gconf_get_update_frequency(GConfClient* client)
{
  guint update_freq;
  GConfValue *value = gconf_client_get(client, GCONF_UPDATE_FREQ, NULL);

  if (value)
  {
    update_freq = gconf_client_get_int(client, GCONF_UPDATE_FREQ, NULL);
  }
  else
  {
    update_freq = GCONF_DEFAULT_UPDATE_FREQ;
    gconf_client_set_int(client, GCONF_UPDATE_FREQ, GCONF_DEFAULT_UPDATE_FREQ, NULL);
  }

  return update_freq;
}
