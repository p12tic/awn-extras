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

#include <glibtop/loadavg.h>

#include "loadicon.h"
#include "sysmoniconprivate.h"
#include "defines.h"
#include "bargraph.h"

G_DEFINE_TYPE (AwnLoadicon, awn_loadicon, AWN_TYPE_SYSMONICON)

#define AWN_LOADICON_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_LOADICON, AwnLoadiconPrivate))

typedef struct _AwnLoadiconPrivate AwnLoadiconPrivate;

struct _AwnLoadiconPrivate {
    guint timer_id;
    guint update_timeout;
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

static gboolean 
_awn_loadicon_update_icon(gpointer object)
{  
  AwnLoadiconPrivate * priv;  
  AwnSysmoniconPrivate * sysmonicon_priv=NULL;  
  AwnLoadicon * icon = AWN_LOADICON(object);
  glibtop_loadavg load;  
  GList * list = NULL;
  int i;
  
  priv = AWN_LOADICON_GET_PRIVATE (object);
  sysmonicon_priv = AWN_SYSMONICON_GET_PRIVATE (object);

  glibtop_get_loadavg(&load);
  
  for (i =0; i<3;i++)
  {
    AwnGraphSinglePoint *point = g_new0 (AwnGraphSinglePoint,1);
    point->value = load.loadavg[i];
    point->points = 1.0;  /*ignored by bargraph*/
    list = g_list_append (list,point);
  }
  awn_graph_add_data (sysmonicon_priv->graph,list);
  awn_sysmonicon_update_icon (AWN_SYSMONICON (icon));
  return TRUE;
  
}

static void
awn_loadicon_constructed (GObject *object)
{
  AwnLoadiconPrivate * priv;
  AwnSysmoniconPrivate * sysmonicon_priv=NULL;  
  gint size;
  AwnGraphType graph_type;

  g_assert (G_OBJECT_CLASS ( awn_loadicon_parent_class) );
  G_OBJECT_CLASS ( awn_loadicon_parent_class)->constructed(object);
  
  priv = AWN_LOADICON_GET_PRIVATE (object); 
  sysmonicon_priv = AWN_SYSMONICON_GET_PRIVATE (object);  
  
  if ( (priv->update_timeout > 750) && 
      ( (priv->update_timeout %1000 <25) || (priv->update_timeout %1000 >975)))
  {
    priv->timer_id = g_timeout_add_seconds(priv->update_timeout/ 1000, 
                                           _awn_loadicon_update_icon, 
                                           object);  
  }
  else
  {
    priv->timer_id = g_timeout_add(priv->update_timeout, _awn_loadicon_update_icon, object);  
  }
  size = awn_applet_get_size (sysmonicon_priv->applet);

  /*CONDITIONAL*/
  graph_type = sysmonicon_priv->graph_type[CONF_STATE_INSTANCE];
  /*FIXME add in default fallback */
  
  switch (graph_type)
  {
    case GRAPH_DEFAULT:
    case GRAPH_BAR:    
      sysmonicon_priv->graph = AWN_GRAPH(awn_bargraph_new (0.0,10.0));      
      break;
    case GRAPH_CIRCLE:
    case GRAPH_AREA:      
    default:
      g_assert_not_reached();
  }
  
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
  object_class->constructed = awn_loadicon_constructed;  
}

static void
awn_loadicon_init (AwnLoadicon *self)
{
  AwnLoadiconPrivate *priv;
  	
  priv = AWN_LOADICON_GET_PRIVATE (self);
  priv->update_timeout = 1000;  /*FIXME*/
  
}

GtkWidget*
awn_loadicon_new (AwnGraphType graph_type,AwnApplet * applet)
{
  return g_object_new (AWN_TYPE_LOADICON, 
                          "graph_type",graph_type,                          
                          "applet",applet,
                          NULL);  
}

