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
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>

#include "config.h"
#include "gconf-config.h"
#include "awnsystemmonitor.h"

AwnApplet* awn_applet_factory_initp(gchar* uid, gint orient, gint height)
{
  AwnApplet *applet = AWN_APPLET(awn_applet_simple_new(uid, orient, height));
  CpuMeter *cpumeter;

  gtk_widget_set_size_request(GTK_WIDGET(applet), height*1.25, -1);


  GdkPixbuf *icon;
#if 0
  icon = gtk_icon_theme_load_icon(gtk_icon_theme_get_default(),
                                  "gnome-main-menu",
                                  height - 2,
                                  0, NULL);
  awn_applet_simple_set_temp_icon(AWN_APPLET_SIMPLE(applet), icon);
#endif
  /*setting to a transparent pixbuf to begin with... awn-effects (I think)
  does not seem to deal well with having the icon set overly late*/

#if 1
  icon = gdk_pixbuf_new(GDK_COLORSPACE_RGB, TRUE, 8, height, height);
  gdk_pixbuf_fill(icon, 0x00000000);
  awn_applet_simple_set_icon_pixbuf(AWN_APPLET_SIMPLE(applet), icon);
#endif
  cpumeter = cpumeter_applet_new(applet);
  cpumeter->height = height;
  /*gtk_widget_show_all(GTK_WIDGET(applet));*/
  return applet;
}

