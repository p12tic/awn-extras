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

#ifndef __CONFIGURATION_H
#define __CONFIGURATION_H

#include "applet.h"

#define CONFIG_URI                    "URI"
#define CONFIG_HTML_ENGINE            "HTML_engine"
#define CONFIG_LAST_ACCESS            "last_access"
#define CONFIG_HEIGHT                 "height"
#define CONFIG_WIDTH                  "width"
#define CONFIG_ENABLE_LOCATION_CONFIG "enable_location_dialog"

void init_config (WebApplet *webapplet);

const gchar * config_get_uri(WebApplet *webapplet);
gint  config_get_width(WebApplet *webapplet);
gint  config_get_height(WebApplet *webapplet);
gboolean  config_get_enable_location_dialog(WebApplet *webapplet);

#endif
/* vim: set et ts=2 sts=2 sw=2 : */
