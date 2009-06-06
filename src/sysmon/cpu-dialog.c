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

/* cpu-dialog.c */

#include "cpu-dialog.h"

G_DEFINE_TYPE (AwnCPUDialog, awn_cpu_dialog, AWN_TYPE_DIALOG)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CPU_DIALOG, AwnCPUDialogPrivate))

typedef struct _AwnCPUDialogPrivate AwnCPUDialogPrivate;

struct _AwnCPUDialogPrivate {
    int dummy;
};

static void
awn_cpu_dialog_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_cpu_dialog_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_cpu_dialog_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_cpu_dialog_parent_class)->dispose (object);
}

static void
awn_cpu_dialog_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_cpu_dialog_parent_class)->finalize (object);
}

static void
awn_cpu_dialog_class_init (AwnCPUDialogClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnCPUDialogPrivate));

  object_class->get_property = awn_cpu_dialog_get_property;
  object_class->set_property = awn_cpu_dialog_set_property;
  object_class->dispose = awn_cpu_dialog_dispose;
  object_class->finalize = awn_cpu_dialog_finalize;
}

static void
awn_cpu_dialog_init (AwnCPUDialog *self)
{
}

AwnCPUDialog*
awn_cpu_dialog_new (void)
{
  return g_object_new (AWN_TYPE_CPU_DIALOG, NULL);
}

