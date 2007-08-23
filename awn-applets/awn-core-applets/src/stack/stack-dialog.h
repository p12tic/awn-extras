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

#ifndef __STACK_DIALOG_H__
#define __STACK_DIALOG_H__

#include <gtk/gtk.h>
#include <libawn/awn-applet-dialog.h>

#include "stack-applet.h"

#define STACK_TYPE_DIALOG (stack_dialog_get_type ())
#define STACK_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_CAST ((obj), STACK_TYPE_DIALOG, StackDialog))
#define STACK_DIALOG_CLASS(class) (G_TYPE_CHECK_CLASS_CAST ((class), STACK_TYPE_DIALOG, StackDialogClass))
#define STACK_IS_DIALOG(obj) (G_TYPE_CHECK_INSTANCE_TYPE ((obj), STACK_TYPE_DIALOG))
#define STACK_IS_DIALOG_CLASS(class) (G_TYPE_CHECK_CLASS_TYPE ((class), STACK_TYPE_DIALOG))
#define STACK_DIALOG_GET_CLASS(obj) (G_TYPE_INSTANCE_GET_CLASS ((obj), STACK_TYPE_DIALOG, StackDialogClass))

typedef struct _StackDialog StackDialog;
typedef struct _StackDialogClass StackDialogClass;
typedef struct _StackDialogPrivate StackDialogPrivate;

struct _StackDialog {
	GtkFixed parent;

    GtkWidget *awn_dialog;
    StackApplet    *applet;
    GtkWidget      *fixed;

    gboolean        active;
    gdouble         anim_time;

    GtkWidget      *fm_box;
    GtkAllocation   fm_alloc;

    GtkWidget      *fup_box;
    GtkAllocation   fup_alloc;

    GtkWidget      *flt_box;
    GtkAllocation   flt_alloc;

    GtkWidget      *frt_box;
    GtkAllocation   frt_alloc;
};

struct _StackDialogClass {
    GtkFixedClass parent_class;
};

GType stack_dialog_get_type(
    void );
    
GtkWidget *stack_dialog_new(
    StackApplet * applet );

GnomeVFSURI *stack_dialog_get_backend_folder(
);

void stack_dialog_toggle_visiblity(
    GtkWidget * widget );

void stack_dialog_open_uri(
    StackDialog * dialog,
    GnomeVFSURI * uri );

void stack_dialog_set_folder(
    StackDialog * dialog,
    GtkWidget * folder,
    gint page );

#endif /* __STACK_DIALOG_H__ */

