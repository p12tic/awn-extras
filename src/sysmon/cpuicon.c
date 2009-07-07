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
 
/*
 TODO
 Per CPU option.
 Config
 
 */

 
 /* awn-CPUicon.c */

#include <glibtop/cpu.h>
#include <libawn/libawn.h>
#include <math.h>

#include "cpuicon.h"
#include "areagraph.h"
#include "circlegraph.h"
#include "bargraph.h"
#include "cpu-dialog.h"

#include "sysmoniconprivate.h"

#include "util.h"


G_DEFINE_TYPE (AwnCPUicon, awn_CPUicon, AWN_TYPE_SYSMONICON)

#define AWN_CPUICON_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CPUICON, AwnCPUiconPrivate))

typedef struct _AwnCPUiconPrivate AwnCPUiconPrivate;

enum
{
  CPU_TOTAL,
  CPU_USED,
  N_CPU_STATES
};

struct _AwnCPUiconPrivate 
{
    AwnCPUDialog  * dialog;
  
    AwnOverlay *text_overlay;
    guint timer_id;
    guint update_timeout;
    guint num_cpus;
    guint now; /*toggle used for the times*/
    guint64 times[2][GLIBTOP_NCPU][N_CPU_STATES];
  
    gdouble   prev_time;
    
};

static AwnGraphSinglePoint awn_CPUicon_get_load(AwnCPUicon *self);


static void
awn_CPUicon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_CPUicon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_CPUicon_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_CPUicon_parent_class)->dispose (object);
}

static void
awn_CPUicon_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_CPUicon_parent_class)->finalize (object);
}

static gboolean 
_awn_CPUicon_update_icon(gpointer object)
{  

  AwnCPUiconPrivate * priv;  
  AwnSysmoniconPrivate * sysmonicon_priv=NULL;  
  AwnCPUicon * icon = object;
  AwnGraphSinglePoint *point;
  GList * list = NULL;
  gchar *text;
  priv = AWN_CPUICON_GET_PRIVATE (object);
  sysmonicon_priv = AWN_SYSMONICON_GET_PRIVATE (object);

  /*FIXME change this to some type of graph_type thing */
  if ( (AWN_IS_AREAGRAPH(sysmonicon_priv->graph)) ||
        (AWN_IS_CIRCLEGRAPH(sysmonicon_priv->graph) ))
  {   
    point = g_new0 (AwnGraphSinglePoint,1);    
    *point = awn_CPUicon_get_load (object);
    text = g_strdup_printf ("CPU: %2.0lf%%",point->value);
    awn_tooltip_set_text (AWN_TOOLTIP(sysmonicon_priv->tooltip),text);
    g_free (text);
    text = g_strdup_printf("%.0lf%%",point->value);  
    g_object_set (priv->text_overlay,
                  "text", text,
                 NULL);  
    g_free (text);
    
    list = g_list_prepend (list,point);
   
    awn_graph_add_data (sysmonicon_priv->graph,list);
    awn_sysmonicon_update_icon (AWN_SYSMONICON (icon));
    g_free (point);
    g_list_free (list);
  }
  else if ( AWN_IS_BARGRAPH(sysmonicon_priv->graph))
  {
    
#undef NOW
#undef LAST
#define LAST (priv->times[priv->now])
#define NOW (priv->times[priv->now ^ 1])
    
    AwnGraphSinglePoint avg_point = awn_CPUicon_get_load (object);      
    gint i;
    GList * iter;    
    glibtop_cpu cpu;
    glibtop_get_cpu(&cpu);
    
    for (i = 0; i < priv->num_cpus; i++)
    {
      gint64 total;
      gint64 total_used;
      gdouble percent_used;
      total = NOW[i][CPU_TOTAL] - LAST[i][CPU_TOTAL];
      total_used = NOW[i][CPU_USED] - LAST[i][CPU_USED];
      percent_used = total_used / (gdouble) total * 100.0;
      point = g_new0 (AwnGraphSinglePoint,1);      
      point->value = percent_used;
      list = g_list_prepend (list,point); 
    }
    text = g_strdup_printf ("CPU: %2.0lf%%",
                            avg_point.value
                            );
    awn_tooltip_set_text (AWN_TOOLTIP(sysmonicon_priv->tooltip),text);
    g_free (text);
    text = g_strdup_printf("%.0lf%%",avg_point.value);
    g_object_set (priv->text_overlay,
                  "text", text,
                 NULL);  
    g_free (text);
    
    awn_graph_add_data (sysmonicon_priv->graph,list);
    awn_sysmonicon_update_icon (AWN_SYSMONICON (icon));
    for (iter = list; iter; iter=g_list_next(iter))
    {
      g_free(iter->data);
    }
    g_list_free (list);    
#undef NOW
#undef LAST
      
  }
  return TRUE;
}


static gboolean
_awn_cpu_icon_clicked (GtkWidget *widget,
                       GdkEventButton *event,
                       AwnCPUDialog * dialog)
{
  if (GTK_WIDGET_VISIBLE (dialog) )
  {
    gtk_widget_hide (GTK_WIDGET(dialog));
  }
  else
  {
    gtk_widget_show_all (GTK_WIDGET (dialog));
  }
 
  return TRUE;
}

static void
_graph_type_change(GObject *pspec, GParamSpec *gobject, AwnApplet *applet)
{
  AwnGraphType graph_type;  
  static int old_graph = -1;
  AwnGraph  *graph = NULL;
  gint size = awn_applet_get_size (applet);
  
  graph_type = get_conf_value_int(G_OBJECT(pspec),"graph-type");
  
  if (old_graph != graph_type)
  {      
    switch (graph_type)
    {
      default:
        g_warning ("Invalid graph type");
      case GRAPH_DEFAULT:
      case GRAPH_AREA:
        graph = AWN_GRAPH(awn_areagraph_new (size,0.0,100.0));
        break;
      case GRAPH_CIRCLE:
        graph = AWN_GRAPH(awn_circlegraph_new (0.0,100.0));
        break;
      case GRAPH_BAR:
        graph = AWN_GRAPH(awn_bargraph_new (0.0,100.0));
        break;      
    }
    g_object_set (G_OBJECT (pspec),
                  "graph",graph,
                  NULL);
    old_graph = graph_type;
  }  
}

static void
awn_CPUicon_constructed (GObject *object)
{
  /*FIXME*/
  AwnCPUiconPrivate * priv;

  glibtop_cpu cpu;
  int i = 0;
  AwnApplet * applet;
  
  g_assert (G_OBJECT_CLASS ( awn_CPUicon_parent_class) );
  
  if (G_OBJECT_CLASS ( awn_CPUicon_parent_class)->constructed)
  {
    G_OBJECT_CLASS ( awn_CPUicon_parent_class)->constructed(object);
  }
  
  g_object_get (object,
                "applet",&applet,
                NULL);
  g_assert (applet);
  g_assert (AWN_IS_APPLET (applet));
  
  priv = AWN_CPUICON_GET_PRIVATE (object); 
  /*
   this will choose add_seconds in a relatively conservative manner.  Note that
   the timer is assumed to be incorrect and time elapsed is actually measured 
   accurately when the timer fires.  Area graph can be informed that the 
   measurement contains a partial point and it will average things out.
   */
  priv->dialog = awn_cpu_dialog_new_with_applet(GTK_WIDGET(object),applet);
  gtk_window_set_title (GTK_WINDOW (priv->dialog),"CPU");
  g_signal_connect(object, "button-press-event", 
                   G_CALLBACK(_awn_cpu_icon_clicked), 
                   priv->dialog);
  
  if ( (priv->update_timeout > 750) && 
      ( (priv->update_timeout %1000 <25) || (priv->update_timeout %1000 >975)))
  {
    priv->timer_id = g_timeout_add_seconds(priv->update_timeout/ 1000, _awn_CPUicon_update_icon, object);  
  }
  else
  {
    priv->timer_id = g_timeout_add(priv->update_timeout, _awn_CPUicon_update_icon, object);  
  }
  
  priv->num_cpus = 0;
  priv->prev_time = get_double_time();
  glibtop_get_cpu(&cpu);

  while (i < GLIBTOP_NCPU && cpu.xcpu_total[i] != 0)
  {
    priv->num_cpus++;
    i++;
  }
  priv->now = 0;
  
  connect_notify (object, "graph-type",
                    G_CALLBACK (_graph_type_change),applet);
    
  priv->text_overlay = AWN_OVERLAY(awn_overlay_text_new());

  g_object_set (priv->text_overlay,
               "align", AWN_OVERLAY_ALIGN_RIGHT,
               "gravity", GDK_GRAVITY_SOUTH,
                "x-adj", 0.3,
                "y-adj", 0.0,
                "text", "0.0",
               NULL);
  awn_overlayable_add_overlay (AWN_OVERLAYABLE(object), priv->text_overlay);

  /*
  AwnOverlayThemedIcon *icon_overlay = awn_overlay_themed_icon_new(AWN_THEMED_ICON(object),"stock_up","up");
  g_object_set (icon_overlay,
                "gravity", GDK_GRAVITY_NORTH_EAST,
                "scale",0.25,
                NULL);

  awn_effects_add_overlay (effects,icon_overlay);
  */
  
/*  
  GdkPixbuf *pixbuf = gtk_icon_theme_load_icon(gtk_icon_theme_get_default(),
                                  "stock_up",
                                  30 ,
                                  0, NULL);
   
  AwnOverlay * pbuf_overlay = AWN_OVERLAY (awn_overlay_pixbuf_new_with_pixbuf (pixbuf));  
  g_object_set ( pbuf_overlay,
                "gravity",GDK_GRAVITY_SOUTH_EAST,
                "scale", 0.5,
                "alpha", 1.0,
                "apply-effects",FALSE,
                NULL);  
  awn_effects_add_overlay (effects,pbuf_overlay);
  */ 
  
/*
  AwnOverlay * pbuf_overlay = AWN_OVERLAY (awn_overlay_pixbuf_file_new ("/usr/local/share/avant-window-navigator/applets/cairo_main_menu/icons/bbb.svg"));  
  awn_effects_add_overlay (effects,pbuf_overlay);
   */
/*  
  AwnOverlay * throbber_overlay = AWN_OVERLAY (awn_overlay_throbber_new (object));
  g_object_set ( throbber_overlay,
                "active",TRUE,
                "gravity", GDK_GRAVITY_NORTH_WEST,
                NULL);
  awn_effects_add_overlay (effects,throbber_overlay);
  */
  /*
  AwnOverlay * progress_overlay = AWN_OVERLAY (awn_overlay_progress_circle_new ());
  g_object_set (progress_overlay,
                "percent-complete", 25.0,
                NULL);
  
  awn_effects_add_overlay (effects,progress_overlay);  */
}

static void
awn_CPUicon_class_init (AwnCPUiconClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnCPUiconPrivate));

  object_class->get_property = awn_CPUicon_get_property;
  object_class->set_property = awn_CPUicon_set_property;
  object_class->dispose = awn_CPUicon_dispose;
  object_class->finalize = awn_CPUicon_finalize;
  object_class->constructed = awn_CPUicon_constructed;
  
}


static void
awn_CPUicon_init (AwnCPUicon *self)
{ 
  AwnCPUiconPrivate *priv;
  	
  priv = AWN_CPUICON_GET_PRIVATE (self);
  priv->update_timeout = 250;  /*FIXME*/
}

GtkWidget*
awn_CPUicon_new (AwnApplet * applet,gchar * id)
{
  GtkWidget * cpuicon = NULL;
  cpuicon = g_object_new (AWN_TYPE_CPUICON,
                          "applet",applet,
                          "id",id,
                          NULL);
  return cpuicon;
}

static AwnGraphSinglePoint
awn_CPUicon_get_load(AwnCPUicon *self)
{
  guint i;
  glibtop_cpu cpu;
  AwnCPUiconPrivate *priv;
  float  total, used;
  gdouble load;
  AwnGraphSinglePoint point;
  gdouble new_time;
  
  priv = AWN_CPUICON_GET_PRIVATE (self);

  new_time = get_double_time ();
  glibtop_get_cpu(&cpu);

#undef NOW
#undef LAST
#define NOW  (priv->times[priv->now])
#define LAST (priv->times[priv->now ^ 1])

  if (priv->num_cpus == 1)
  {
    NOW[0][CPU_TOTAL] = cpu.total;
    NOW[0][CPU_USED] = cpu.user + cpu.nice + cpu.sys;
  }
  else
  {
    for (i = 0; i < priv->num_cpus; i++)
    {
      NOW[i][CPU_TOTAL] = cpu.xcpu_total[i];
      NOW[i][CPU_USED] = cpu.xcpu_user[i] + cpu.xcpu_nice[i] + cpu.xcpu_sys[i];
    }
  }

  load = total = used = 0.0;

  for (i = 0; i < priv->num_cpus; i++)
  {
    total = total + NOW[i][CPU_TOTAL] - LAST[i][CPU_TOTAL];
    used  = used + NOW[i][CPU_USED]  - LAST[i][CPU_USED];
  }

  load = used / MAX(total, (float)priv->num_cpus * 1.0f);

  point.value = load * 100.0;
  if (point.value>100.0)
  {
    point.value = 100.0;
  }
  point.points = (new_time - priv->prev_time) * 1000.0 / priv->update_timeout; 

  priv->prev_time = new_time;
  // toggle the buffer index.
  priv->now ^= 1;

#undef NOW
#undef LAST
  return point;
}


