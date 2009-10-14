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

#include "config.h"
#include "cairo-menu-applet.h"

#include <gtk/gtk.h>
#include <glib/gi18n.h>

static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event, CairoMenuApplet * applet);

static gboolean _show_prefs(GtkWidget *widget, GdkEventButton *event, CairoMenuApplet * applet)
{

  show_prefs();
  return TRUE;
}


AwnApplet* awn_applet_factory_initp(const gchar *name,
                                    const gchar* uid, gint panel_id)
{

  AwnApplet *applet = AWN_APPLET( cairo_menu_applet_new (name, uid, panel_id) );
  
  g_object_set (applet,
                "display-name","Cairo Menu",
                NULL);
  
  return applet;

}


