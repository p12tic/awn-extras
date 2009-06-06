/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */

/* cpu-dialog.h */

#ifndef _AWN_CPU_DIALOG
#define _AWN_CPU_DIALOG

#include <glib-object.h>
#include <libawn/awn-dialog.h>

G_BEGIN_DECLS

#define AWN_TYPE_CPU_DIALOG awn_cpu_dialog_get_type()

#define AWN_CPU_DIALOG(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CPU_DIALOG, AwnCPUDialog))

#define AWN_CPU_DIALOG_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CPU_DIALOG, AwnCPUDialogClass))

#define AWN_IS_CPU_DIALOG(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CPU_DIALOG))

#define AWN_IS_CPU_DIALOG_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CPU_DIALOG))

#define AWN_CPU_DIALOG_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CPU_DIALOG, AwnCPUDialogClass))

typedef struct {
  AwnDialog parent;
} AwnCPUDialog;

typedef struct {
  AwnDialogClass parent_class;
} AwnCPUDialogClass;

GType awn_cpu_dialog_get_type (void);

AwnCPUDialog* awn_cpu_dialog_new (void);

G_END_DECLS

#endif /* _AWN_CPU_DIALOG */
