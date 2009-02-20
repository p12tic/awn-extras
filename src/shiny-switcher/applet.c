/*
 * Copyright (C) 2007, 2008, 2009 Rodney Cryderman <rcryderman@gmail.com>
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

#include <libawn/awn-applet.h>
#include <libawn/awn-utils.h>
#include "config.h"

#include "shinyswitcherapplet.h"



AwnApplet*
awn_applet_factory_initp(gchar* uid, gint orient, gint height)
{
  AwnApplet *applet;
  Shiny_switcher*shiny_switcher;
  applet = awn_applet_new(uid, orient, height*0.5);
  shiny_switcher = applet_new(applet, orient, height , height);
  shiny_switcher->orient = orient;

  return applet;
}

