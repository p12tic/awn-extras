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

#ifndef __STACK_APPLET_H__
#define __STACK_APPLET_H__

/*
 * INCLUDES
 */
#include <gtk/gtk.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-title.h>

#define STACK_TYPE_APPLET (stack_applet_get_type ())
#define STACK_APPLET(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), STACK_TYPE_APPLET, StackApplet))
#define STACK_APPLET_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST ((klass), STACK_TYPE_APPLET, StackAppletClass))
#define STACK_IS_APPLET(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), STACK_TYPE_APPLET))
#define STACK_IS_APPLET_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE ((klass), STACK_TYPE_APPLET))
#define STACK_APPLET_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), STACK_TYPE_APPLET, StackAppletClass))

typedef struct _StackApplet StackApplet;
typedef struct _StackAppletClass StackAppletClass;
typedef struct _StackAppletPrivate StackAppletPrivate;

struct _StackApplet {
	GtkDrawingArea	parent;

    AwnApplet     	*awn_applet;
    GtkWidget     	*context_menu;
    GtkWidget     	*stack;
    
	AwnTitle		*title;
	gchar			*title_text;

    GdkPixbuf     	*icon;
    GdkPixbuf     	*composite_icon;
    GdkPixbuf     	*reflect_icon;

    gboolean        drag_hover;

    guint           size;
    guint           new_size;
    gint            y_offset;
    gint            dir;
};

struct _StackAppletClass {
    GtkDrawingAreaClass  parent_class;
};

GType stack_applet_get_type(
    void
);

gboolean _bounce_baby(
    StackApplet * applet );

void stack_applet_set_icon(
    StackApplet * applet,
    GdkPixbuf * icon );

#endif /* __STACK_APPLET_H__ */
