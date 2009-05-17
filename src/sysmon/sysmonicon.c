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

/* awn-sysmonicon.c */

#include "sysmonicon.h"
#include "graph.h"

G_DEFINE_TYPE (AwnSysmonicon, awn_sysmonicon, AWN_TYPE_ICON)

#include "sysmoniconprivate.h"
enum
{
  PROP_0,
  PROP_APPLET,
  PROP_GRAPHTYPE
};

static void create_surface (AwnSysmonicon * sysmonicon);


static void
awn_sysmonicon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  AwnSysmoniconPrivate * priv;
  AwnSysmonicon * sysmonicon = AWN_SYSMONICON(object);
  priv = AWN_SYSMONICON_GET_PRIVATE (sysmonicon);
  switch (property_id) {
    case PROP_APPLET:
      g_value_set_object (value, priv->applet); 
      break;    
    case PROP_GRAPHTYPE:
      g_value_set_int (value, priv->graph_type); 
      break;    
    default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_sysmonicon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  AwnSysmoniconPrivate * priv;
  AwnSysmonicon * sysmonicon = AWN_SYSMONICON(object);
  priv = AWN_SYSMONICON_GET_PRIVATE (sysmonicon);
  switch (property_id) {
    case PROP_APPLET:
      priv->applet = g_value_get_object (value);
      break;    
    case PROP_GRAPHTYPE:
      priv->graph_type = g_value_get_int (value);
      break;          
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_sysmonicon_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_sysmonicon_parent_class)->dispose (object);
}

static void
awn_sysmonicon_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_sysmonicon_parent_class)->finalize (object);
}

static void
awn_sysmonicon_class_init (AwnSysmoniconClass *klass)
{
  GParamSpec   *pspec;  
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->get_property = awn_sysmonicon_get_property;
  object_class->set_property = awn_sysmonicon_set_property;
  object_class->dispose = awn_sysmonicon_dispose;
  object_class->finalize = awn_sysmonicon_finalize;
  
  pspec = g_param_spec_object ("applet",
                               "Applet",
                               "AwnApplet",
                               AWN_TYPE_APPLET,
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_APPLET, pspec);  
  
  pspec = g_param_spec_int ("graph_type",
                               "Graph_type",
                               "Graph Type",
                               GRAPH_DEFAULT,
                               GRAPH_LAST,
                               GRAPH_DEFAULT,
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_GRAPHTYPE, pspec);  
  
  g_type_class_add_private (object_class, sizeof (AwnSysmoniconPrivate));
  
}

static gboolean _expose(GtkWidget *self,
                        GdkEventExpose *event,
                        gpointer null)
{
  AwnSysmoniconPrivate * priv;
  priv = AWN_SYSMONICON_GET_PRIVATE (self);
  
  if (!priv->graph_cr)
  {
    create_surface (AWN_SYSMONICON(self));
    awn_graph_render_to_context (priv->graph,priv->graph_cr);
    awn_icon_set_from_context (AWN_ICON(self),priv->graph_cr);
  }  
  return TRUE;
}

static void
awn_sysmonicon_init (AwnSysmonicon *self)
{
  AwnSysmoniconPrivate * priv;
  priv = AWN_SYSMONICON_GET_PRIVATE (self);

  priv->graph = NULL;
  priv->graph_cr = NULL;
  g_signal_connect_after (G_OBJECT(self), "expose-event", G_CALLBACK(_expose), NULL);       
}

GtkWidget*
awn_sysmonicon_new (AwnApplet *applet)
{
  return g_object_new (AWN_TYPE_SYSMONICON, 
                       "Applet",applet,
                       NULL);
}

AwnGraph *
awn_sysmonicon_get_graph(AwnSysmonicon * self)
{
  AwnSysmoniconPrivate * priv;
  priv = AWN_SYSMONICON_GET_PRIVATE (self);
  return priv->graph;
}

static void
create_surface (AwnSysmonicon * sysmonicon)
{
  
  cairo_t * temp_cr =NULL;
  AwnSysmoniconPrivate * priv;
  gint size;
  
  priv = AWN_SYSMONICON_GET_PRIVATE (sysmonicon);
  
  size = awn_applet_get_size (AWN_APPLET(priv->applet));
  
  if (priv->graph_cr)
  {
    cairo_destroy(priv->graph_cr);
    priv->graph_cr = NULL;
  }

  if (priv->surface)
  {
    cairo_surface_destroy(priv->surface);
    priv->surface = NULL;
  }

  temp_cr = gdk_cairo_create(GTK_WIDGET(priv->applet)->window);
  priv->surface = cairo_surface_create_similar (cairo_get_target(temp_cr),CAIRO_CONTENT_COLOR_ALPHA, size,size);
  cairo_destroy(temp_cr);
  priv->graph_cr = cairo_create(priv->surface);
  cairo_scale(priv->graph_cr,(double)size/48.0,(double)size/48.0);

}

void
awn_sysmonicon_update_icon (AwnSysmonicon * icon)
{
  AwnSysmoniconPrivate * priv;
  priv = AWN_SYSMONICON_GET_PRIVATE (icon);
  g_return_if_fail (priv->graph_cr);
  awn_graph_render_to_context (priv->graph,priv->graph_cr);
  /*FIXME
   Have a background, rendered graph, and foregrond and slap them together.
   */

  awn_icon_set_from_context (AWN_ICON(icon),priv->graph_cr); 
}

