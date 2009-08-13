/*
 * Copyright (c) 2007 Rodney Cryderman <rcryderman@gmail.com>
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

#ifndef Awntop_H_
#define Awntop_H_

#include <libawn/awn-applet.h>
#include "cairo-utils.h"
//#include <libawn/awn-title.h>
#include <libawn/awn-tooltip.h>

#include <glib.h>
#include <gtk/gtk.h>


typedef struct
{
  long     pid;
  int     uid;
  int     pri;
  int     nice;
  long    virt;
  long    res;
  long    shr;
  long     cpu;
  long     mem;
  long    time;
  char    cmd[40];
}Topentry;



typedef struct
{
  guint updateinterval;
  gboolean   forceupdatefixup;
  guint    accum_interval;
  int maxtopentries;
  int (*compar)(const void *, const void *);
  long    *   displayed_pid_list;
  GTree*  proctimes;
  GTree*  icons;
  GTree*  pixbufs;
  Topentry **topentries;
  int num_top_entries;
  int filterlevel;
  glibtop_mem libtop_mem;

  void (*redraw_window_fn)(void *);
  void * redraw_window_data;
}Awntop;

void * awntop_plug_lookup(int fn_id);

#endif
