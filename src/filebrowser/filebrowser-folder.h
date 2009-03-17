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

#ifndef __FILEBROWSER_FOLDER_H__
#define __FILEBROWSER_FOLDER_H__

#include <gtk/gtk.h>
#include <libawn/awn-dialog.h>
#include <libgnomevfs/gnome-vfs.h>

#include "filebrowser-dialog.h"

#define FILEBROWSER_TYPE_FOLDER (filebrowser_folder_get_type ())
#define FILEBROWSER_FOLDER(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), FILEBROWSER_TYPE_FOLDER, FileBrowserFolder))
#define FILEBROWSER_FOLDER_CLASS(class) (G_TYPE_CHECK_CLASS_CAST ((class), FILEBROWSER_TYPE_FOLDER, FileBrowserFolderClass))
#define FILEBROWSER_IS_FOLDER(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), FILEBROWSER_TYPE_FOLDER))
#define FILEBROWSER_IS_FOLDER_CLASS(class) (G_TYPE_CHECK_CLASS_TYPE ((class), FILEBROWSER_TYPE_FOLDER))
#define FILEBROWSER_FOLDER_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), FILEBROWSER_TYPE_FOLDER, FileBrowserFolderClass))

typedef struct _FileBrowserFolder FileBrowserFolder;
typedef struct _FileBrowserFolderClass FileBrowserFolderClass;

struct _FileBrowserFolder {
    GtkEventBox			parent;

    FileBrowserDialog			*dialog;

    const gchar			*name;
    GnomeVFSURI			*uri;
    GnomeVFSMonitorHandle *monitor;

    GtkListStore        *store;    
    GdkPixbuf      		*applet_icon;
    gint                offset;
    gint                total;
};

struct _FileBrowserFolderClass {
    GtkEventBoxClass   parent_class;
};

GType filebrowser_folder_get_type(
    void );

GtkWidget *filebrowser_folder_new(
    FileBrowserDialog * dialog,
    GnomeVFSURI * uri );

gboolean filebrowser_folder_has_next_page(
    FileBrowserFolder * folder );
    
gboolean filebrowser_folder_has_prev_page(
    FileBrowserFolder * folder );

void filebrowser_folder_do_next_page(
    FileBrowserFolder * folder );
    
void filebrowser_folder_do_prev_page(
    FileBrowserFolder * folder );
    
gboolean filebrowser_folder_has_parent_folder(
    FileBrowserFolder * folder );

void filebrowser_folder_layout(FileBrowserFolder *folder, gint offset);

#endif /* __FILEBROWSER_FOLDER_H__ */

