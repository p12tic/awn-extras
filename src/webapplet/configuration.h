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

#define CONFIG_KEY(key) key
#define CONFIG_URI              CONFIG_KEY("URI")
#define CONFIG_HTML_ENGINE      CONFIG_KEY("HTML_engine")
#define CONFIG_LAST_ACCESS      CONFIG_KEY("last_access")
#define CONFIG_HEIGHT           CONFIG_KEY("height")
#define CONFIG_WIDTH            CONFIG_KEY("width")

void init_config(WebApplet * webapplet, gchar * uid);

#endif
