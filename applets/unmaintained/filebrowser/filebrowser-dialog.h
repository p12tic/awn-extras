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

#ifndef __FILEBROWSER_DIALOG_H__
#define __FILEBROWSER_DIALOG_H__

#include <gtk/gtk.h>
#include <libawn/awn-dialog.h>

#include "filebrowser-applet.h"

#define FILEBROWSER_TYPE_DIALOG (filebrowser_dialog_get_type ())
#define FILEBROWSER_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), FILEBROWSER_TYPE_DIALOG, FileBrowserDialog))
#define FILEBROWSER_DIALOG_CLASS(class) (G_TYPE_CHECK_CLASS_CAST ((class), FILEBROWSER_TYPE_DIALOG, FileBrowserDialogClass))
#define FILEBROWSER_IS_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), FILEBROWSER_TYPE_DIALOG))
#define FILEBROWSER_IS_DIALOG_CLASS(class) (G_TYPE_CHECK_CLASS_TYPE ((class), FILEBROWSER_TYPE_DIALOG))
#define FILEBROWSER_DIALOG_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), FILEBROWSER_TYPE_DIALOG, FileBrowserDialogClass))

typedef struct _FileBrowserDialog FileBrowserDialog;
typedef struct _FileBrowserDialogClass FileBrowserDialogClass;
typedef struct _FileBrowserDialogPrivate FileBrowserDialogPrivate;

struct _FileBrowserDialog {
	GtkVBox			parent;

    GtkWidget		*awn_dialog;
    FileBrowserApplet		*applet;

    gboolean        active;

  GtkWidget *hscroll;
  GtkAdjustment *adj;
  gint last_page;

	GtkWidget		*viewport;
};

struct _FileBrowserDialogClass {
    GtkVBoxClass parent_class;
};

GType filebrowser_dialog_get_type(
    void );
    
GtkWidget *filebrowser_dialog_new(
    FileBrowserApplet * applet );

void filebrowser_dialog_toggle_visiblity(
    GtkWidget * widget );

void filebrowser_dialog_set_folder(
    FileBrowserDialog * dialog,
    GnomeVFSURI * uri,
    gint page );

#endif /* __FILEBROWSER_DIALOG_H__ */

