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

#ifndef __FILEBROWSER_ICON_H__
#define __FILEBROWSER_ICON_H__

#include <gtk/gtk.h>
#include <libgnomevfs/gnome-vfs.h>
#include <libgnome/gnome-desktop-item.h>

#include "filebrowser-folder.h"

#define FILEBROWSER_TYPE_ICON (filebrowser_icon_get_type ())
#define FILEBROWSER_ICON(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), FILEBROWSER_TYPE_ICON, FileBrowserIcon))
#define FILEBROWSER_ICON_CLASS(class) (G_TYPE_CHECK_CLASS_CAST ((class), FILEBROWSER_TYPE_ICON, FileBrowserIconClass))
#define FILEBROWSER_IS_ICON(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), FILEBROWSER_TYPE_ICON))
#define FILEBROWSER_IS_ICON_CLASS(class) (G_TYPE_CHECK_CLASS_TYPE ((class), FILEBROWSER_TYPE_ICON))
#define FILEBROWSER_ICON_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), FILEBROWSER_TYPE_ICON, FileBrowserIconClass))

typedef struct _FileBrowserIcon FileBrowserIcon;
typedef struct _FileBrowserIconClass FileBrowserIconClass;
typedef struct _FileBrowserIconPrivate FileBrowserIconPrivate;
struct _FileBrowserIcon {
    GtkButton		parent;
    
    GtkWidget      *folder;
    GdkPixbuf      *icon;
    GnomeVFSURI    *uri;
    GnomeDesktopItem *desktop_item;
    gchar          *name;
};

struct _FileBrowserIconClass {
    GtkButtonClass parent_class;
};

GType filebrowser_icon_get_type(
    void );

GtkWidget *filebrowser_icon_new(
    FileBrowserFolder * folder,
    GnomeVFSURI * uri );

#endif /* __FILEBROWSER_ICON_H__ */

