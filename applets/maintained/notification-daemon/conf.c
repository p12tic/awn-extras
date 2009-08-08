/* daemon.c - Implementation of the destop notification spec
 *
 * Awn related modifications by Rodney Cryderman <rcryderman@gmail.com>
 *
 * Base gnome-notification-daemon by
 * Copyright (C) 2006 Christian Hammond <chipx86@chipx86.com>
 * Copyright (C) 2005 John (J5) Palmieri <johnp@redhat.com>
 *
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 */


/*tabsize =4*/

#include "config.h"

#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include <dbus/dbus.h>
#include <dbus/dbus-glib.h>
#include <glib/gi18n.h>
#include <glib.h>
#include <glib-object.h>
#include <gtk/gtk.h>
#include <glib/gprintf.h>

#include <libnotify/notify.h>

#include <glib/gprintf.h>

#include <X11/Xproto.h>

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <gdk/gdkx.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-gconf.h>
#include <libawn/awn-dialog.h>
#include <libawn/awn-applet-simple.h>


#include "daemon.h"
#include "conf.h"

void
popup_location_changed_cb(GConfClient *client, guint cnxn_id,
                          GConfEntry *entry, gpointer user_data);

extern AwnApplet *G_awn_app;
extern int G_awn_app_height;
extern DesktopAgnosticColor *G_awn_border;
extern DesktopAgnosticColor *G_awn_bg;
extern DesktopAgnosticColor *G_awn_text;
extern gchar * G_awn_text_str;
extern gboolean G_awn_client_pos;
extern gboolean G_awn_honour_gtk;
extern int G_awn_override_y;
extern int G_awn_override_x;
extern int G_awn_border_width;
extern float G_awn_gradient_factor;
extern GdkPixbuf *G_awn_icon;
extern GConfClient *gconf_client;

void read_configuration(NotifyDaemon *daemon)
{
  GConfValue*  value;
  gchar * svalue;


  gconf_client = gconf_client_get_default();
  gconf_client_add_dir(gconf_client, GCONF_KEY_DAEMON,
                       GCONF_CLIENT_PRELOAD_NONE, NULL);

#if 1
  gconf_client_notify_add(gconf_client, GCONF_KEY_POPUP_LOCATION,
                          popup_location_changed_cb, daemon,
                          NULL, NULL);

  /* Emit signal to verify/set current key */
  gconf_client_notify(gconf_client, GCONF_KEY_POPUP_LOCATION);
#endif

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_KILL_ND,
                           NULL);

  if (value)
  {
    if (gconf_client_get_bool(gconf_client, GCONF_KEY_AWN_KILL_ND , NULL))
    {
      if (system("pgrep notification-daemon && killall notification-daemon") == -1)
      {
        printf("Failed to execute killall command: disable kill notication daemon and configure to kill daemon before loading applet\n");
      }
      else
      {
        system("pgrep notification-daemon &&  killall -9 notification-daemon");
      }
    }
  }
  else
  {
    gconf_client_set_bool(gconf_client, GCONF_KEY_AWN_KILL_ND, TRUE , NULL);

    if (system("pgrep notification-daemon && killall notification-daemon") == -1)
    {
      printf("Failed to execute killall command: disable kill notication daemon and configure to kill daemon before loading applet\n");
    }
    else
    {
      system("pgrep notification-daemon && killall -9 notification-daemon");
    }

  }

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_CLIENT_POS,

                           NULL);

  if (value)
  {
    G_awn_client_pos = gconf_client_get_bool(gconf_client, GCONF_KEY_AWN_CLIENT_POS , NULL);
  }
  else
  {
    G_awn_client_pos = TRUE;
    gconf_client_set_bool(gconf_client, GCONF_KEY_AWN_CLIENT_POS, G_awn_client_pos, NULL);
  }

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_HONOUR_GTK,

                           NULL);

  if (value)
  {
    G_awn_honour_gtk = gconf_client_get_bool(gconf_client, GCONF_KEY_AWN_HONOUR_GTK , NULL);
  }
  else
  {
    G_awn_honour_gtk = TRUE;
    gconf_client_set_bool(gconf_client, GCONF_KEY_AWN_HONOUR_GTK, G_awn_honour_gtk, NULL);
  }

  svalue = gconf_client_get_string(gconf_client, GCONF_KEY_AWN_BG, NULL);

  if (!svalue)
  {
    gconf_client_set_string(gconf_client , GCONF_KEY_AWN_BG, svalue = g_strdup("#0a0a0abb"), NULL);
  }

  G_awn_bg = desktop_agnostic_color_new_from_string(svalue, NULL);

  g_free(svalue);

  svalue = gconf_client_get_string(gconf_client, GCONF_KEY_AWN_TEXT_COLOUR, NULL);

  if (!svalue)
  {
    gconf_client_set_string(gconf_client , GCONF_KEY_AWN_TEXT_COLOUR, svalue = g_strdup("#eeeeeebb"), NULL);
  }

  G_awn_text = desktop_agnostic_color_new_from_string(svalue, NULL);

  G_awn_text_str = g_strdup(svalue);

  if (strlen(G_awn_text_str) > 6)
    G_awn_text_str[6] = '\0';

  g_free(svalue);

  svalue = gconf_client_get_string(gconf_client, GCONF_KEY_AWN_BORDER, NULL);

  if (!svalue)
  {
    gconf_client_set_string(gconf_client , GCONF_KEY_AWN_BORDER, svalue = g_strdup("#ffffffaa"), NULL);
  }

  G_awn_border = desktop_agnostic_color_new_from_string(svalue, NULL);

  g_free(svalue);

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_BORDER_WIDTH, NULL);

  if (value)
  {
    G_awn_border_width = gconf_client_get_int(gconf_client, GCONF_KEY_AWN_BORDER_WIDTH, NULL) ;
  }
  else
  {
    G_awn_border_width = 3;
    gconf_client_set_int(gconf_client, GCONF_KEY_AWN_BORDER_WIDTH, G_awn_border_width , NULL);
  }

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_GRADIENT_FACTOR, NULL);

  if (value)
  {
    G_awn_gradient_factor = gconf_client_get_float(gconf_client, GCONF_KEY_AWN_GRADIENT_FACTOR, NULL) ;
  }
  else
  {
    G_awn_gradient_factor = 0.75;
    gconf_client_set_float(gconf_client, GCONF_KEY_AWN_GRADIENT_FACTOR, G_awn_gradient_factor , NULL);
  }

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_OVERRIDE_X, NULL);

  if (value)
  {
    G_awn_override_x = gconf_client_get_int(gconf_client, GCONF_KEY_AWN_OVERRIDE_X, NULL) ;
  }
  else
  {
    G_awn_override_x = -1;
    gconf_client_set_int(gconf_client, GCONF_KEY_AWN_OVERRIDE_X, G_awn_override_x , NULL);
  }

  value = gconf_client_get(gconf_client, GCONF_KEY_AWN_OVERRIDE_Y, NULL);

  if (value)
  {
    G_awn_override_y = gconf_client_get_int(gconf_client, GCONF_KEY_AWN_OVERRIDE_Y, NULL) ;
  }
  else
  {
    G_awn_override_y = -1;
    gconf_client_set_int(gconf_client, GCONF_KEY_AWN_OVERRIDE_Y, G_awn_override_y , NULL);
  }

}
