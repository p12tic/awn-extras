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

#ifndef __FILEBROWSER_APPLET_H__
#define __FILEBROWSER_APPLET_H__

#include <gtk/gtk.h>
#include <libawn/awn-title.h>

#define FILEBROWSER_TYPE_APPLET (filebrowser_applet_get_type ())
#define FILEBROWSER_APPLET(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), FILEBROWSER_TYPE_APPLET, FileBrowserApplet))
#define FILEBROWSER_APPLET_CLASS(klass) (G_TYPE_CHECK_CLASS_CAST ((klass), FILEBROWSER_TYPE_APPLET, FileBrowserAppletClass))
#define FILEBROWSER_IS_APPLET(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), FILEBROWSER_TYPE_APPLET))
#define FILEBROWSER_IS_APPLET_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE ((klass), FILEBROWSER_TYPE_APPLET))
#define FILEBROWSER_APPLET_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), FILEBROWSER_TYPE_APPLET, FileBrowserAppletClass))

typedef struct _FileBrowserApplet FileBrowserApplet;
typedef struct _FileBrowserAppletClass FileBrowserAppletClass;
typedef struct _FileBrowserAppletPrivate FileBrowserAppletPrivate;

struct _FileBrowserApplet {
	GtkDrawingArea	parent;

    GtkWidget     	*awn_applet;
    GtkWidget     	*context_menu;
    GtkWidget     	*filebrowser;
    
	gchar			*title_text;
};

struct _FileBrowserAppletClass {
    GtkDrawingAreaClass  parent_class;
};

GType filebrowser_applet_get_type(
    void
);

void filebrowser_applet_set_icon(
    FileBrowserApplet *applet,
    GdkPixbuf * icon );

#endif /* __FILEBROWSER_APPLET_H__ */
