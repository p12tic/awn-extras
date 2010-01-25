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

/* awn-graph.c */

#include "graph.h"

G_DEFINE_TYPE (AwnGraph, awn_graph, G_TYPE_OBJECT)

#include "graphprivate.h"

static void _awn_graph_render_to_context (AwnGraph * graph,
                                          cairo_t *ctx,
                                          gint width, gint height);
static void _awn_graph_add_data          (AwnGraph * graph,
                                          GList * data);

static void
awn_graph_get_property (GObject *object, guint property_id,
                        GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_graph_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_graph_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_graph_parent_class)->dispose (object);
}

static void
awn_graph_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_graph_parent_class)->finalize (object);
}

static void
awn_graph_class_init (AwnGraphClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnGraphPrivate));

  object_class->get_property = awn_graph_get_property;
  object_class->set_property = awn_graph_set_property;
  object_class->dispose = awn_graph_dispose;
  object_class->finalize = awn_graph_finalize;
  
  klass->render_to_context = _awn_graph_render_to_context;
  klass->add_data = _awn_graph_add_data;
}

static void
awn_graph_init (AwnGraph *self)
{
}

AwnGraph*
awn_graph_new (void)
{
  return g_object_new (AWN_TYPE_GRAPH, NULL);
}

static void _awn_graph_render_to_context (AwnGraph * graph,
                                          cairo_t *cr,
                                          gint width, gint height)
{
  AwnGraphPrivate * priv;
  
  priv = AWN_GRAPH_GET_PRIVATE(graph);
  
  cairo_set_source_rgba(cr, 0.3, 0.4, 0.1, 0.4);
  cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
  cairo_paint(cr);
     
}

static void _awn_graph_add_data(AwnGraph * graph,
                                        GList * data)
{
  AwnGraphPrivate * priv;
  
  priv = AWN_GRAPH_GET_PRIVATE(graph);
}

void awn_graph_render_to_context (AwnGraph * graph, cairo_t *ctx,
                                  gint width, gint height)
{
  AwnGraphClass *klass;

  klass = AWN_GRAPH_GET_CLASS (graph);

  return klass->render_to_context (graph, ctx, width, height);
}

void awn_graph_add_data (AwnGraph * graph, GList * data)
{
  AwnGraphClass *klass;

  klass = AWN_GRAPH_GET_CLASS (graph);
  g_return_if_fail (klass->add_data);
  g_return_if_fail (data);
  return klass->add_data (graph, data);
}
