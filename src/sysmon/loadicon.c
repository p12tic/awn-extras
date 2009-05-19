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
 
 /* awn-loadicon.c */

#include "loadicon.h"

G_DEFINE_TYPE (AwnLoadicon, awn_loadicon, AWN_TYPE_SYSMONICON)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_LOADICON, AwnLoadiconPrivate))

typedef struct _AwnLoadiconPrivate AwnLoadiconPrivate;

struct _AwnLoadiconPrivate {
    int dummy;
};

static void
awn_loadicon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_loadicon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_loadicon_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_loadicon_parent_class)->dispose (object);
}

static void
awn_loadicon_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_loadicon_parent_class)->finalize (object);
}

static void
awn_loadicon_class_init (AwnLoadiconClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnLoadiconPrivate));

  object_class->get_property = awn_loadicon_get_property;
  object_class->set_property = awn_loadicon_set_property;
  object_class->dispose = awn_loadicon_dispose;
  object_class->finalize = awn_loadicon_finalize;
}

static void
awn_loadicon_init (AwnLoadicon *self)
{
}

AwnLoadicon*
awn_loadicon_new (void)
{
  return g_object_new (AWN_TYPE_LOADICON, NULL);
}

