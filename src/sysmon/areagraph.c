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


/* awn-areagraph.c */

#include "areagraph.h"

G_DEFINE_TYPE (Awn_Areagraph, awn_areagraph, AWN_TYPE_GRAPH)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_AREAGRAPH, Awn_AreagraphPrivate))

typedef struct _Awn_AreagraphPrivate Awn_AreagraphPrivate;

struct _Awn_AreagraphPrivate {
    int dummy;
};

static void
awn_areagraph_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_areagraph_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_areagraph_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_areagraph_parent_class)->dispose (object);
}

static void
awn_areagraph_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_areagraph_parent_class)->finalize (object);
}

static void
awn_areagraph_class_init (Awn_AreagraphClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (Awn_AreagraphPrivate));

  object_class->get_property = awn_areagraph_get_property;
  object_class->set_property = awn_areagraph_set_property;
  object_class->dispose = awn_areagraph_dispose;
  object_class->finalize = awn_areagraph_finalize;
}

static void
awn_areagraph_init (Awn_Areagraph *self)
{
}

Awn_Areagraph*
awn_areagraph_new (void)
{
  return g_object_new (AWN_TYPE_AREAGRAPH, NULL);
}

