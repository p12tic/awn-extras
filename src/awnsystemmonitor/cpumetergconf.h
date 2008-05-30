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

#ifndef __CPUMETER_GCONF_H__
#define __CPUMETER_GCONF_H__


#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>

void cpumeter_gconf_init(CpuMeter* cpumeter);
void cpumeter_gconf_get_color(AwnApplet* applet, AwnColor* color, gchar* key, gchar* def);
gfloat cpumeter_gconf_get_border_width(AwnApplet* applet);
gboolean cpumeter_gconf_use_gradient(AwnApplet* applet);
gboolean cpumeter_gconf_do_subtitle(CpuMeter* cpumeter);
guint cpumeter_gconf_get_update_frequency(AwnApplet* applet);

#endif  /* __CPUMETER_GCONF_H__ */
