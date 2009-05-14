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
 


/* awn-circlegraph.c */

#include "circlegraph.h"
#include "graphprivate.h"

G_DEFINE_TYPE (AwnCirclegraph, awn_circlegraph, AWN_TYPE_GRAPH)

#define AWN_CIRCLEGRAPH_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CIRCLEGRAPH, AwnCirclegraphPrivate))

typedef struct _AwnCirclegraphPrivate AwnCirclegraphPrivate;

struct _AwnCirclegraphPrivate 
{
  gdouble max_val;
  gdouble min_val;
};

enum
{
  PROP_0,
  PROP_MIN_VAL,
  PROP_MAX_VAL
};

static void _awn_circlegraph_render_to_context(AwnGraph * graph,
                                        cairo_t *ctx);
static void _awn_circlegraph_add_data(AwnGraph * graph,
                                        gpointer data);



static void
awn_circlegraph_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  AwnCirclegraphPrivate * priv;
  priv = AWN_CIRCLEGRAPH_GET_PRIVATE (object);  
  switch (property_id) 
  {
    case PROP_MIN_VAL:
      g_value_set_object (value, &priv->min_val); 
      break;     
    case PROP_MAX_VAL:
      g_value_set_object (value, &priv->max_val); 
      break;               
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_circlegraph_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  AwnCirclegraphPrivate * priv;
  priv = AWN_CIRCLEGRAPH_GET_PRIVATE (object);  

  switch (property_id) 
  {
    case PROP_MIN_VAL:
      priv->min_val = g_value_get_double (value);
      break;     
    case PROP_MAX_VAL:
      priv->max_val = g_value_get_double (value);
      break;               
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_circlegraph_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_circlegraph_parent_class)->dispose (object);
}

static void
awn_circlegraph_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_circlegraph_parent_class)->finalize (object);
}

static void
awn_circlegraph_class_init (AwnCirclegraphClass *klass)
{
  GParamSpec   *pspec;      
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->get_property = awn_circlegraph_get_property;
  object_class->set_property = awn_circlegraph_set_property;
  object_class->dispose = awn_circlegraph_dispose;
  object_class->finalize = awn_circlegraph_finalize;

  AWN_GRAPH_CLASS(klass)->render_to_context = _awn_circlegraph_render_to_context;
  AWN_GRAPH_CLASS(klass)->add_data = _awn_circlegraph_add_data;
  
  pspec = g_param_spec_double (   "min_val",
                                "MinVal",
                                "Minimum Value",
                                -1000000.0,         /*was using G_MAXDOUBLE, G_MINDOUBLE... but it was not happy*/
                                +1000000.0,
                                0,
                                G_PARAM_READWRITE);
  g_object_class_install_property (object_class, PROP_MIN_VAL, pspec);      
  pspec = g_param_spec_double (   "max_val",
                                "MaxVal",
                                "Maximum Value",
                                -1000000.0,
                                +1000000.0,
                                0,
                                G_PARAM_READWRITE);
  g_type_class_add_private (klass, sizeof (AwnCirclegraphPrivate));  
  
}

static void _awn_circlegraph_render_to_context(AwnGraph * graph,
                                        cairo_t *orig_cr)
{
}

static void _awn_circlegraph_add_data(AwnGraph * graph,
                                        gpointer data)
{
}

static void
awn_circlegraph_init (AwnCirclegraph *self)
{
  
  AwnCirclegraphPrivate * priv;
  AwnGraphPrivate * graph_priv;
  
  priv = AWN_CIRCLEGRAPH_GET_PRIVATE (self);
  graph_priv = AWN_GRAPH_GET_PRIVATE (self);

  priv->min_val = 0.0;
  priv->max_val = 100.0;      /*FIXME*/
  
}

AwnCirclegraph*
awn_circlegraph_new (gdouble min_val, gdouble max_val)
{
  return g_object_new (AWN_TYPE_CIRCLEGRAPH, 
                       "min_val", min_val,
                       "max_val", max_val,
                       NULL);
}

