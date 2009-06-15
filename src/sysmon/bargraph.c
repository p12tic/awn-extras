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
 
 /* awn-bargraph.c */

#include "graphprivate.h"
#include "bargraph.h"

G_DEFINE_TYPE (AwnBarGraph, awn_bargraph, AWN_TYPE_GRAPH)

#define AWN_BARGRAPH_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_BARGRAPH, AwnBarGraphPrivate))

typedef struct _AwnBarGraphPrivate AwnBarGraphPrivate;

struct _AwnBarGraphPrivate {
  gdouble max_val;
  gdouble min_val;
  gdouble num_vals;
};

enum
{
  PROP_0,
  PROP_MIN_VAL,
  PROP_MAX_VAL
};


static void _awn_bargraph_render_to_context(AwnGraph * graph,cairo_t *cr);
static void _awn_bargraph_add_data(AwnGraph * graph,GList * list);


static void
awn_bargraph_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  AwnBarGraphPrivate * priv;
  priv = AWN_BARGRAPH_GET_PRIVATE (object);
  
  switch (property_id) {
    case PROP_MIN_VAL:
      g_value_set_double (value, priv->min_val); 
      break;           
    case PROP_MAX_VAL:
      g_value_set_double (value, priv->max_val); 
      break;                 
    default:      
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_bargraph_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  AwnBarGraphPrivate * priv;
  priv = AWN_BARGRAPH_GET_PRIVATE (object);
    
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
awn_bargraph_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_bargraph_parent_class)->dispose (object);
}

static void
awn_bargraph_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_bargraph_parent_class)->finalize (object);
}

static void
awn_bargraph_class_init (AwnBarGraphClass *klass)
{
  GParamSpec   *pspec;  
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->get_property = awn_bargraph_get_property;
  object_class->set_property = awn_bargraph_set_property;
  object_class->dispose = awn_bargraph_dispose;
  object_class->finalize = awn_bargraph_finalize;
  
  AWN_GRAPH_CLASS(klass)->render_to_context = _awn_bargraph_render_to_context;
  AWN_GRAPH_CLASS(klass)->add_data = _awn_bargraph_add_data;

  pspec = g_param_spec_double (   "min-val",
                                "MinVal",
                                "Minimum Value",
                                -1000000.0,         /*was using G_MAXDOUBLE, G_MINDOUBLE... but it was not happy*/
                                +1000000.0,
                                0,
                                G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_MIN_VAL, pspec);      
  pspec = g_param_spec_double (   "max-val",
                                "MaxVal",
                                "Maximum Value",
                                -1000000.0,
                                +1000000.0,
                                100.0,
                                G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  
  g_object_class_install_property (object_class, PROP_MAX_VAL, pspec);    
  
  g_type_class_add_private (klass, sizeof (AwnBarGraphPrivate));
  
}

static void _awn_bargraph_render_to_context(AwnGraph * graph,
                                        cairo_t *cr)
{
  AwnGraphPrivate * graph_priv;
  AwnBarGraphPrivate * priv;  
  gdouble bar_width;
  int srfc_height;
  int srfc_width;
  gdouble x = 0;
  int i;
  gdouble * values;

  priv = AWN_BARGRAPH_GET_PRIVATE (graph);  
  graph_priv = AWN_GRAPH_GET_PRIVATE(graph);

  cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint (cr);
  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);  

  srfc_height = cairo_xlib_surface_get_height (cairo_get_target(cr));
  srfc_width = cairo_xlib_surface_get_width (cairo_get_target(cr));  
  values = graph_priv->data;
  cairo_save (cr);
  cairo_scale (cr,srfc_width,srfc_height);
  cairo_set_source_rgba (cr,0.0,0.2,0.9,0.95);
  
  bar_width = 1.0 / (gdouble) priv->num_vals;
  for (i=0; i<priv->num_vals; i++)
  {
    gdouble bar_height =  1.0 * ( values[i] / (priv->max_val-priv->min_val));
    cairo_rectangle (cr, x, 
                         1.0 - bar_height ,
                         bar_width,
                         bar_height);
    cairo_fill (cr);
    x = x + bar_width;
  }
  cairo_restore (cr);
  
}

static void _awn_bargraph_add_data(AwnGraph * graph,
                                        GList * list)
{
  AwnGraphPrivate * graph_priv;
  AwnBarGraphPrivate * priv;  
  GList * iter;  
  gdouble * values;
  
  priv = AWN_BARGRAPH_GET_PRIVATE (graph);  
  graph_priv = AWN_GRAPH_GET_PRIVATE(graph);
  
  if (graph_priv->data)
  {
    g_free (graph_priv->data);
  }

  priv->num_vals = g_list_length (list);
  values = g_new0( gdouble, priv->num_vals);
  graph_priv->data = values;  
  
  for (iter = g_list_first (list); iter; iter = g_list_next (iter) )
  {
    AwnGraphSinglePoint *bar_graph_point = iter->data;    
    *values = bar_graph_point->value;
    values++;
  }
 
}

static void
awn_bargraph_init (AwnBarGraph *self)
{
  AwnGraphPrivate * graph_priv;
  AwnBarGraphPrivate * priv;  
  GList * iter;  
  gint num_items;
}

AwnBarGraph*
awn_bargraph_new (gdouble min_val, gdouble max_val)
{
  AwnBarGraph * result = g_object_new (AWN_TYPE_BARGRAPH,
                         "min-val", min_val,
                         "max-val",max_val,
                       NULL);
  return result;
}


