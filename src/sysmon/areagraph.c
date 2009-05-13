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
#include <math.h>

#include "areagraph.h"
#include "graphprivate.h"

G_DEFINE_TYPE (Awn_Areagraph, awn_areagraph, AWN_TYPE_GRAPH)

#define AWN_AREAGRAPH_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_AREAGRAPH, AwnAreagraphPrivate))

typedef struct _Awn_AreagraphPrivate AwnAreagraphPrivate;

struct _Awn_AreagraphPrivate 
{
  gdouble max_val;
  gdouble min_val;
  guint num_points;
  gdouble cur_point;
  
};

enum
{
  PROP_0,
  PROP_NUM_POINTS,
  PROP_MIN_VAL,
  PROP_MAX_VAL
};

static void _awn_areagraph_render_to_context(AwnGraph * graph,
                                        cairo_t *ctx);
static void _awn_areagraph_add_data(AwnGraph * graph,
                                        gpointer data);

static void
awn_areagraph_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  AwnAreagraphPrivate * priv;
  priv = AWN_AREAGRAPH_GET_PRIVATE (object);
  
  switch (property_id) 
  {
    case PROP_NUM_POINTS:
      g_value_set_object (value, &priv->num_points); 
      break;     
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
awn_areagraph_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  AwnAreagraphPrivate * priv;
  priv = AWN_AREAGRAPH_GET_PRIVATE (object);
  
  switch (property_id) 
  {
    case PROP_NUM_POINTS:
      priv->num_points = g_value_get_uint (value);
      break;     
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
  GParamSpec   *pspec;    
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->get_property = awn_areagraph_get_property;
  object_class->set_property = awn_areagraph_set_property;
  object_class->dispose = awn_areagraph_dispose;
  object_class->finalize = awn_areagraph_finalize;
  
  AWN_GRAPH_CLASS(klass)->render_to_context = _awn_areagraph_render_to_context;
  AWN_GRAPH_CLASS(klass)->add_data = _awn_areagraph_add_data;
  
  pspec = g_param_spec_uint (   "num_points",
                                "NumPoints",
                                "Number of points on graph",
                                1,
                                G_MAXUINT,
                                48,
                                G_PARAM_READWRITE);
  g_object_class_install_property (object_class, PROP_NUM_POINTS, pspec);      
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
  
  g_object_class_install_property (object_class, PROP_MAX_VAL, pspec);    

  
  g_type_class_add_private (klass, sizeof (AwnAreagraphPrivate));
  
}

static void _awn_areagraph_render_to_context(AwnGraph * graph,
                                        cairo_t *cr)
{
  /*Can be optimized.  FIXME
   */
  AwnAreagraphPrivate * priv;
  AwnGraphPrivate * graph_priv;  
  gint  srfc_height;
  gint  srfc_width;
  gint  i;
  gint  end_point;
  gint  x=0;
  gdouble * values = NULL;
  
  priv = AWN_AREAGRAPH_GET_PRIVATE (graph);
  graph_priv = AWN_GRAPH_GET_PRIVATE (graph);
  values = graph_priv->data;
  
  cairo_save (cr);
  cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint (cr);
  
  srfc_height = cairo_xlib_surface_get_height (cairo_get_target(cr));
  srfc_width = cairo_xlib_surface_get_width (cairo_get_target(cr));
  
  cairo_scale (cr,1.0, 0.5);//srfc_height / (double) (priv->max_val - priv->min_val));
  cairo_set_source_rgba (cr, 0.8, 0.0, 0.6, 0.6);

  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);

  if ( (gint) priv->cur_point)
  {
    end_point = ( (gint)priv->cur_point) -1 ;
  }
  else
  {
    end_point = ((gint) priv->cur_point) ;
  }
    
  for (i=priv->cur_point; x < priv->num_points;i++)
  {
    cairo_move_to (cr, x,priv->max_val - priv->min_val);
    cairo_line_to (cr, x, priv->max_val - priv->min_val - values[i]);
    cairo_stroke (cr);
    if (i >= priv->num_points )
    {
      i = -1;
    }    
    x++;    
  }
  cairo_restore (cr);
}

static void _awn_areagraph_add_data(AwnGraph * graph,
                                        gpointer data)
{
  /*deal with partial later FIXME */
  AwnGraphPrivate * graph_priv;
  AwnAreagraphPrivate * priv;
  gdouble * values;
  gint i;
  glong count;
  const Awn_AreagraphPoint *area_graph_point = data;
  
  priv = AWN_AREAGRAPH_GET_PRIVATE (graph);  
  graph_priv = AWN_GRAPH_GET_PRIVATE(graph);
  
  values = graph_priv->data;
  i=priv->cur_point;
  count = lround ( area_graph_point->points);
  
  if (count)
  {
    while (count)
    {
      values[i] = area_graph_point->value;
      i++;
      count--;
      if (i >= priv->num_points)
      {
        i = 0;
      }
    }
  }
  priv->cur_point = i +1;
  
}

static void
awn_areagraph_init (Awn_Areagraph *self)
{
  AwnAreagraphPrivate * priv;
  AwnGraphPrivate * graph_priv;
  
  priv = AWN_AREAGRAPH_GET_PRIVATE (self);
  graph_priv = AWN_GRAPH_GET_PRIVATE (self);

  priv->min_val = 0.0;
  priv->max_val = 100.0;      /*FIXME*/
  priv->num_points = 48;
  priv->cur_point = 0;
  
  graph_priv->data =g_new0(gdouble, priv->num_points);
  
}

GtkWidget*
awn_areagraph_new (guint num_points, gdouble min_val, gdouble max_val)
{
  return g_object_new (AWN_TYPE_AREAGRAPH, 
                       "num_points",num_points,
                       "min_val", min_val,
                       "max_val", max_val,
                       NULL);
}

void 
awn_areagraph_clear (Awn_Areagraph *self, gdouble val)
{
  int i;
  AwnGraphPrivate * graph_priv;
  AwnAreagraphPrivate * priv;

  graph_priv = AWN_GRAPH_GET_PRIVATE (self);
  priv = AWN_AREAGRAPH_GET_PRIVATE (self);  
  graph_priv->data =g_new0(gdouble, priv->num_points);
  
  for (i=0; i<priv->num_points;i++)
  {
    ((gdouble *)graph_priv->data)[i]=val;
  }
}
