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
#include "config.h"

#include "shinyswitcherapplet.h"

static gboolean
_make_transparent (GtkWidget *widget, gpointer data)
{
  /*
   * Cribbed from awn-icon.c
   */
  if (gtk_widget_is_composited(widget)) // FIXME: is is_composited correct here?
  {
    static GdkPixmap *pixmap = NULL;
    if (pixmap == NULL)
    {
      pixmap = gdk_pixmap_new(widget->window, 1, 1, -1);
      cairo_t *cr = gdk_cairo_create(pixmap);
      cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
      cairo_paint(cr);
      cairo_destroy(cr);
    }
    gdk_window_set_back_pixmap(widget->window, pixmap, FALSE);

  }
   
  return FALSE;
}


AwnApplet*
awn_applet_factory_initp(gchar* uid, gint orient, gint height)
{
  AwnApplet *applet;
  Shiny_switcher*shiny_switcher;
  applet = awn_applet_new(uid, orient, height*0.5);
  shiny_switcher = applet_new(applet, orient, height , height);
  shiny_switcher->orient = orient;
  gtk_widget_add_events (GTK_WIDGET (applet), GDK_ALL_EVENTS_MASK);

  g_signal_connect_after(G_OBJECT(applet), "realize",
                         G_CALLBACK(_make_transparent), NULL);  
  return applet;
}

