/*
 * Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
 *
 * This is a CPU Load Applet for the Avant Window Navigator.  This module contains
 * #define's for the GConf keys.
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

/* The GConf path */
#define GCONF_PATH "/apps/avant-window-navigator/applets/cpumeter"

/* The color of the graph */
#define GCONF_GRAPH_COLOR GCONF_PATH "/graph_color"
#define GCONF_DEFAULT_GRAPH_COLOR "B39AE6FF"

/* the color of the border */
#define GCONF_BORDER_COLOR GCONF_PATH "/border_color"
#define GCONF_DEFAULT_BORDER_COLOR "FFFFFFFF"

/* the color of the background */
#define GCONF_BG_COLOR GCONF_PATH "/bg_color"
#define GCONF_DEFAULT_BG_COLOR "FFFFFF10"

/* Width of the border */
#define GCONF_BORDER_WIDTH GCONF_PATH "/border_width"
#define GCONF_DEFAULT_BORDER_WIDTH 2.0

/* Set to nonzero if you want the gradient overlay */
#define GCONF_DO_GRADIENT GCONF_PATH "/do_gradient"
#define GCONF_DEFAULT_DO_GRADIENT 1

/* Set to nonzero if you want the text "CPU - nn%" below the graph */
#define GCONF_DO_SUBTITLE GCONF_PATH "/do_subtitle"
#define GCONF_DEFAULT_DO_SUBTITLE 1

/* Update frequency in milliseconds */
#define GCONF_UPDATE_FREQ GCONF_PATH "/update_frequency"
#define GCONF_DEFAULT_UPDATE_FREQ 1000
