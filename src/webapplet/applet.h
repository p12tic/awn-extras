/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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
 
 
 #ifndef __WEBAPPLET_APPLET
 
#define __WEBAPPLET_APPLET

#include <libawn/awn-applet.h>
#include <libawn/awn-config-client.h>

typedef struct
{
  AwnApplet         *applet;
  GtkWidget         *mainwindow;
  GdkPixbuf         *icon;  
  GtkWidget         *box;
  GtkWidget         *viewer;
  AwnConfigClient		*instance_config;  
  AwnConfigClient		*default_config;  

  gint            applet_icon_height;
  gchar           *applet_icon_name;
  gchar           *uri;
}WebApplet;

#define APPLET_NAME "webapplet"

#endif 
