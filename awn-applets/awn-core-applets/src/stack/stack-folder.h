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

#ifndef __STACK_FOLDER_H__
#define __STACK_FOLDER_H__

#include <gtk/gtk.h>
#include <libawn/awn-applet-dialog.h>
#include <libgnomevfs/gnome-vfs.h>

#include "stack-dialog.h"

#define STACK_TYPE_FOLDER (stack_folder_get_type ())
#define STACK_FOLDER(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), STACK_TYPE_FOLDER, StackFolder))
#define STACK_FOLDER_CLASS(class) (G_TYPE_CHECK_CLASS_CAST ((class), STACK_TYPE_FOLDER, StackFolderClass))
#define STACK_IS_FOLDER(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), STACK_TYPE_FOLDER))
#define STACK_IS_FOLDER_CLASS(class) (G_TYPE_CHECK_CLASS_TYPE ((class), STACK_TYPE_FOLDER))
#define STACK_FOLDER_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), STACK_TYPE_FOLDER, StackFolderClass))

typedef struct _StackFolder StackFolder;
typedef struct _StackFolderClass StackFolderClass;

struct _StackFolder {
    GtkViewport        parent;

    StackDialog    *dialog;
    GtkWidget		*table;

    const gchar    *name;
    GnomeVFSURI    *uri;
    GnomeVFSMonitorHandle *monitor;

    GList          *icon_list;
    gint            page;
    gint			pages;
    
    GdkPixbuf      *applet_icon;
};

struct _StackFolderClass {
    GtkViewportClass   parent_class;
};

GType stack_folder_get_type(
    void );

GtkWidget *stack_folder_new(
    StackDialog * dialog,
    GnomeVFSURI * uri );

gboolean is_directory(
    GnomeVFSURI * uri );

gboolean stack_folder_has_next_page(
    StackFolder * folder );
    
gboolean stack_folder_has_prev_page(
    StackFolder * folder );

void stack_folder_do_next_page(
    StackFolder * folder );
    
void stack_folder_do_prev_page(
    StackFolder * folder );
    
gboolean stack_folder_has_parent_folder(
    StackFolder * folder );

#endif /* __STACK_FOLDER_H__ */

