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

#ifndef __STACK_ICON_H__
#define __STACK_ICON_H__

#include <gtk/gtk.h>
#include <libgnomevfs/gnome-vfs.h>
#include <libgnome/gnome-desktop-item.h>

#include "stack-folder.h"

#define STACK_TYPE_ICON (stack_icon_get_type ())
#define STACK_ICON(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), STACK_TYPE_ICON, StackIcon))
#define STACK_ICON_CLASS(class) (G_TYPE_CHECK_CLASS_CAST ((class), STACK_TYPE_ICON, StackIconClass))
#define STACK_IS_ICON(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), STACK_TYPE_ICON))
#define STACK_IS_ICON_CLASS(class) (G_TYPE_CHECK_CLASS_TYPE ((class), STACK_TYPE_ICON))
#define STACK_ICON_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), STACK_TYPE_ICON, StackIconClass))

typedef struct _StackIcon StackIcon;
typedef struct _StackIconClass StackIconClass;
typedef struct _StackIconPrivate StackIconPrivate;
struct _StackIcon {
    GtkButton		parent;
    
    GtkWidget      *folder;
    GdkPixbuf      *icon;
    GnomeVFSURI    *uri;
    GnomeDesktopItem *desktop_item;
    gchar          *name;
};

struct _StackIconClass {
    GtkButtonClass parent_class;
};

GType stack_icon_get_type(
    void );

GtkWidget *stack_icon_new(
    StackFolder * folder,
    GnomeVFSURI * uri );

#endif /* __STACK_ICON_H__ */

