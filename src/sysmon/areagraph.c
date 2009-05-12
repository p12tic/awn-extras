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

#define AWN_AREAGRAPH_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_AREAGRAPH, AwnAreagraphPrivate))

typedef struct _Awn_AreagraphPrivate AwnAreagraphPrivate;

struct _Awn_AreagraphPrivate 
{
  gdouble max_val;
  gdouble min_val;
  gdouble num_points;
  gdouble cur_point;
  gdouble * values;
  
};


static void _awn_areagraph_render_to_context(AwnGraph * graph,
                                        cairo_t *ctx);
static void _awn_areagraph_add_data(AwnGraph * graph,
                                        gpointer data);

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

  g_type_class_add_private (klass, sizeof (AwnAreagraphPrivate));

  object_class->get_property = awn_areagraph_get_property;
  object_class->set_property = awn_areagraph_set_property;
  object_class->dispose = awn_areagraph_dispose;
  object_class->finalize = awn_areagraph_finalize;
  
  AWN_GRAPH_CLASS(klass)->render_to_context = _awn_areagraph_render_to_context;
  AWN_GRAPH_CLASS(klass)->add_data = _awn_areagraph_add_data;
  
}

static void _awn_areagraph_render_to_context(AwnGraph * graph,
                                        cairo_t *cr)
{
  AwnAreagraphPrivate * priv;
  
  g_debug ("area graph render! \n");
  priv = AWN_AREAGRAPH_GET_PRIVATE(graph);
  
  cairo_set_source_rgba(cr, 0.3, 0.4, 0.1, 0.4);
  cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
  cairo_paint(cr);
     
}

static void _awn_areagraph_add_data(AwnGraph * graph,
                                        gpointer data)
{
  AwnAreagraphPrivate * priv;
  
  priv = AWN_AREAGRAPH_GET_PRIVATE(graph);
}

static void
awn_areagraph_init (Awn_Areagraph *self)
{
  AwnAreagraphPrivate * priv;
  
  priv = AWN_AREAGRAPH_GET_PRIVATE(self);

  priv->min_val = 0.0;
  priv->max_val = 100.0;
  priv->num_points = 48;
  priv->cur_point = 0;
  priv->values =g_new0(gdouble, priv->num_points);
  
}

Awn_Areagraph*
awn_areagraph_new (void)
{
  return g_object_new (AWN_TYPE_AREAGRAPH, NULL);
}

