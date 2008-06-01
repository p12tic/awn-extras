/*
 * Copyright (c) 2007 Nicolas de BONFILS
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
#include "config.h"

#include "wobblyziniapplet.h"

static gboolean
_button_clicked_event (GtkWidget      *widget,
                       GdkEventButton *event,
                       AwnApplet *applet)
{
  static GtkWidget *menu=NULL;
  if (event->button == 3)
  {
    if (!menu)
    {
      menu = awn_applet_create_default_menu (applet);
    }
    gtk_menu_set_screen (GTK_MENU (menu), NULL);
    gtk_menu_popup (GTK_MENU (menu), NULL, NULL, NULL, NULL,
                    event->button, event->time);
  }
  return TRUE;
}

AwnApplet*
awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
	AwnApplet *applet;
	WobblyZini *wobblyzini;

	/*printf ("avant init\n");*/
	applet = awn_applet_new( uid, orient, height );
	gtk_widget_set_size_request (GTK_WIDGET (applet), awn_applet_get_height (applet) * 2, awn_applet_get_height (applet) );
	wobblyzini = wobblyzini_applet_new(applet);
	/*printf ("apres init\n");*/
  g_signal_connect (G_OBJECT (applet), "button-press-event",
                    G_CALLBACK (_button_clicked_event), applet); 
	return applet;
}

