/*
 * Copyright (c) 2007 Mike Desjardins
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

#ifndef CPUMETERAPPLET_H_
#define CPUMETERAPPLET_H_

#include <libawn/awn-applet.h>
#include <glib/gtypes.h>
#include <glibtop/cpu.h>

/* Stuff to store the CPU measurements */
#define NUM_POINTS 200


enum {
	CPU_TOTAL,
	CPU_USED,
	N_CPU_STATES
};

typedef struct {
	guint num_cpus;
	gfloat data[NUM_POINTS];
	guint index;
  guint64 times[2][GLIBTOP_NCPU][N_CPU_STATES];
  gboolean initialized;
  guint now;
} LoadGraph;

/* Graphing constants */
#define PAD 8
#define SIZE 40
#define ARC 8

/* Applet struct */
typedef struct
{
	AwnApplet *applet;
  LoadGraph *loadgraph;

	guint size;
	guint new_size;
	GtkOrientation orient;

	GtkTooltips *tooltips;
	GdkPixbuf *icon;

	/* Effect stuff */
	guint height;
	gint y_offset;

}CpuMeter;

// Applet
CpuMeter* cpumeter_applet_new (AwnApplet *applet);

#endif /*CPUMETERAPPLET_H_*/
