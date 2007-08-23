/*
 * Copyright (c) 2007 Timon David Ter Braak
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
#include <libawn/awn-applet.h>

#include "stack-applet.h"

AwnApplet *awn_applet_factory_initp(
    gchar * uid,
    gint orient,
    gint height ) {

	GtkWidget *applet = awn_applet_new( uid, orient, height );
    GtkWidget *stack = stack_applet_new( AWN_APPLET( applet ) );
    
    gtk_container_add( GTK_CONTAINER( applet ), stack );

    gtk_widget_set_size_request( applet, height, height );

    gtk_widget_show( applet );

    return AWN_APPLET( applet );
}
