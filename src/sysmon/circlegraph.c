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

#include <math.h>
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
  gdouble prev_val;
  gdouble current_val;
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
                                G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_MIN_VAL, pspec);      
  pspec = g_param_spec_double (   "max_val",
                                "MaxVal",
                                "Maximum Value",
                                -1000000.0,
                                +1000000.0,
                                0,
                                G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_MAX_VAL, pspec);        
  g_type_class_add_private (klass, sizeof (AwnCirclegraphPrivate));  
  
}

static void _awn_circlegraph_render_to_context(AwnGraph * graph,
                                        cairo_t *orig_cr)
{
  AwnCirclegraphPrivate * priv;  
  cairo_pattern_t *pat;
//  cairo_t * cr = orig_cr;
  cairo_t * cr = cairo_create (cairo_get_target(orig_cr) ); /* FIXME This should not be necessary*/
  gint srfc_width;
  gint srfc_height;
  gdouble usage;
  
  priv = AWN_CIRCLEGRAPH_GET_PRIVATE (graph);    
  
  cairo_save (cr);
  srfc_height = cairo_xlib_surface_get_height (cairo_get_target(cr));
  srfc_width = cairo_xlib_surface_get_width (cairo_get_target(cr));

  cairo_scale (cr, srfc_width / 256.0, srfc_height / 256.0);
  
  
/*  pat = cairo_pattern_create_linear (0.0, 0.0,  0.0, 256.0);
  cairo_pattern_add_color_stop_rgba (pat, 1, 0, 0, 0, 1);
  cairo_pattern_add_color_stop_rgba (pat, 0, 1, 1, 1, 1);
  cairo_rectangle (cr, 0, 0, 256, 256);
  cairo_set_source (cr, pat);
  cairo_fill (cr);
  cairo_pattern_destroy (pat);
*/
  g_debug ("cpu = %lf\n",priv->current_val);
  usage = (priv->current_val + priv->prev_val) / 200.0;
  pat = cairo_pattern_create_radial (125.2, 130.4, 2,
                                     102.4,  102.4, 128.0);
  cairo_pattern_add_color_stop_rgba (pat, 0, 1*usage, 0, 0, 1);
  cairo_pattern_add_color_stop_rgba (pat, 1, 0, 1 *(1-usage), 0, 1);
  cairo_set_source (cr, pat);
  cairo_arc (cr, 128.0, 128.0, 120, 0, 2 * M_PI);
  cairo_fill (cr);
  cairo_pattern_destroy (pat);
  
  cairo_restore (cr);
}

static void _awn_circlegraph_add_data(AwnGraph * graph,
                                        gpointer data)
{
  AwnGraphPrivate * graph_priv;
  AwnCirclegraphPrivate * priv;

  const AwnGraphSinglePoint *area_graph_point = data;

  priv = AWN_CIRCLEGRAPH_GET_PRIVATE (graph);  
  graph_priv = AWN_GRAPH_GET_PRIVATE(graph);
  
  priv->prev_val = priv->current_val;
  priv->current_val = area_graph_point->value;
  
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
  priv->prev_val = 0;
  priv->current_val = 0;
}

AwnCirclegraph*
awn_circlegraph_new (gdouble min_val, gdouble max_val)
{
  return g_object_new (AWN_TYPE_CIRCLEGRAPH, 
                       "min_val", min_val,
                       "max_val", max_val,
                       NULL);
}

