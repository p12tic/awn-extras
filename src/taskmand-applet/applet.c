/*
 * Copyright (c) 2008   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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

#include <gtk/gtk.h>
#include <libawn/awn-applet-simple.h>


AwnApplet* awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
	GdkPixbuf *icon;
    
    AwnApplet *applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
    if (!icon)
    {
        icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,height-2,height-2);
        gdk_pixbuf_fill(icon,0x11881133);
    }    
    gtk_widget_set_size_request (GTK_WIDGET (applet), 2, 2);
    awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),icon);    
    return applet;
}

