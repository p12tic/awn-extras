/*
 * Copyright (c) 2007 Mike (mosburger) Desjardins <desjardinsmike@gmail.com>
 *
 * This is a CPU Load Applet for the Avant Window Navigator.  It
 * borrows heavily from the Gnome system monitor, so kudos go to
 * the authors of that program:
 *
 * Kevin Vandersloot <kfv101@psu.edu>
 * Erik Johnsson <zaphod@linux.nu> - icon support
 * Jorgen Scheibengruber
 * Benoît Dejean <benoit@placenet.org> - maintainer
 * Paolo Borelli <pborelli@katamail.com>
 * Baptiste Mille-Mathias - artwork
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

// This is all stuff that needs to move to gconf to be user-configurable.  Someday.  *sigh*

/* The red component of the color of the graph */
#define GRAPH_COLOR_R 0.7

/* The green component of the color of the graph */
#define GRAPH_COLOR_G 0.6

/* The blue component of the color of the graph */
#define GRAPH_COLOR_B 0.9

/* The red component of the border of the graph */
#define BORDER_COLOR_R 1.0

/* The green component of the color of the graph */
#define BORDER_COLOR_G 1.0

/* The blue component of the color of the graph */
#define BORDER_COLOR_B 1.0

/* Width of the border */
#define BORDER_WIDTH 2.0

/* Set to nonzero if you want the gradient overlay */
#define DO_GRADIENT 1

/* Update frequency in milliseconds */
#define UPDATE_FREQ 1000

