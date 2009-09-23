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
    guint update_timeout[NUM_CONF_STATES];
    guint num_cpus;
    guint now; /*toggle used for the times*/
    guint64 times[2][GLIBTOP_NCPU][N_CPU_STATES];
  
    gdouble   prev_time;
    GtkWidget   *context_menu;
};


enum
{
  PROP_0,
  PROP_UPDATE_TIMEOUT,
  PROP_UPDATE_TIMEOUT_DEFAULT  
};

static AwnGraphSinglePoint awn_CPUicon_get_load(AwnCPUicon *self);

static void awn_CPUicon_show_context_menu(AwnCPUicon *self);

static void set_timeout (AwnCPUicon * object);

static void
awn_CPUicon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  AwnCPUiconPrivate * priv;  
  priv = AWN_CPUICON_GET_PRIVATE (object);

  switch (property_id) {
    case PROP_UPDATE_TIMEOUT:
      g_value_set_int (value, priv->update_timeout[CONF_STATE_INSTANCE]); 
      break;    
    case PROP_UPDATE_TIMEOUT_DEFAULT:
      g_value_set_int (value, priv->update_timeout[CONF_STATE_BASE]);
      break;        
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_CPUicon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  AwnCPUiconPrivate * priv;  
  priv = AWN_CPUICON_GET_PRIVATE (object);
  
  switch (property_id) {
    case PROP_UPDATE_TIMEOUT:
      priv->update_timeout[CONF_STATE_INSTANCE] = g_value_get_int (value);
      break;
    case PROP_UPDATE_TIMEOUT_DEFAULT:
      priv->update_timeout[CONF_STATE_BASE] = g_value_get_int (value);
      break;      
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
  switch (event->button)
  {
    case 1:
      if (GTK_WIDGET_VISIBLE (dialog) )
      {
        dec_process_info_users ();
        gtk_widget_hide (GTK_WIDGET(dialog));
      }
      else
      {
        inc_process_info_users ();
        gtk_widget_show_all (GTK_WIDGET (dialog));
      }
      break;
    case 2:
      break;
    case 3:
      awn_CPUicon_show_context_menu(AWN_CPUICON(widget));
      break;
  }
  return TRUE;
}

static void
_graph_type_change(GObject *object, GParamSpec *pspec, AwnApplet *applet)
{
  AwnGraphType graph_type;  
  static int old_graph = -1;
  AwnGraph  *graph = NULL;
  gint size = awn_applet_get_size (applet);
  
  graph_type = get_conf_value_int(G_OBJECT(object),"graph-type");
  
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
    g_object_set (G_OBJECT (object),
                  "graph",graph,
                  NULL);
    old_graph = graph_type;
  }  
}

static void
set_timeout (AwnCPUicon * object)
{
  AwnCPUiconPrivate * priv;  
  gint update_timeout = get_conf_value_int ( G_OBJECT(object), "update-timeout");

  priv = AWN_CPUICON_GET_PRIVATE (object);   
  if (priv->timer_id)
  {
    g_source_remove (priv->timer_id);
  }
  
  if ( (update_timeout > 750) && 
      ( (update_timeout %1000 <25) || (update_timeout %1000 >975)))
  {
    priv->timer_id = g_timeout_add_seconds(update_timeout/ 1000, _awn_CPUicon_update_icon, object);  
  }
  else
  {
    priv->timer_id = g_timeout_add(update_timeout, _awn_CPUicon_update_icon, object);  
  }
}

static void
_update_timeout_change(GObject *object, GParamSpec *pspec, AwnApplet *applet)
{
  set_timeout(AWN_CPUICON(object));
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
  connect_notify (object, "update-timeout",
                    G_CALLBACK (_update_timeout_change),object);
  
  set_timeout (AWN_CPUICON(object));
  priv->text_overlay = AWN_OVERLAY(awn_overlay_text_new());

  g_object_set (priv->text_overlay,
               "align", AWN_OVERLAY_ALIGN_RIGHT,
               "gravity", GDK_GRAVITY_SOUTH,
                "x-adj", 0.3,
                "y-adj", 0.0,
                "text", "0.0",
               NULL);
  awn_overlayable_add_overlay (AWN_OVERLAYABLE(object), priv->text_overlay);

  do_bridge ( applet,object,
             "icon","update_timeout","update-timeout");

}

static void
awn_CPUicon_class_init (AwnCPUiconClass *klass)
{
  GParamSpec   *pspec;   
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->get_property = awn_CPUicon_get_property;
  object_class->set_property = awn_CPUicon_set_property;
  object_class->dispose = awn_CPUicon_dispose;
  object_class->finalize = awn_CPUicon_finalize;
  object_class->constructed = awn_CPUicon_constructed;
  
  
  pspec = g_param_spec_int ("update-timeout",
                               "update_timeout",
                               "how often to update`",
                               100,
                               100000,
                               1000,
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_UPDATE_TIMEOUT, pspec);  

  pspec = g_param_spec_int ("update-timeout-base",
                               "update_timeout base",
                               "how often to update`",
                               100,
                               100000,
                               1000,
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_UPDATE_TIMEOUT_DEFAULT, pspec);  
  
  g_type_class_add_private (klass, sizeof (AwnCPUiconPrivate));
}


static void
awn_CPUicon_init (AwnCPUicon *self)
{ 
  AwnCPUiconPrivate *priv;
  	
  priv = AWN_CPUICON_GET_PRIVATE (self);
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
  point.points = (new_time - priv->prev_time) * 1000.0 / 
    get_conf_value_int (G_OBJECT(self), "update-timeout"); 

  priv->prev_time = new_time;
  // toggle the buffer index.
  priv->now ^= 1;

#undef NOW
#undef LAST
  return point;
}

static void
change_to_area (AwnCPUicon *self)
{
  g_object_set (self,
                "graph-type",GRAPH_AREA,
                NULL);
}

static void
change_to_circle (AwnCPUicon *self)
{
  g_object_set (self,
                "graph-type",GRAPH_CIRCLE,
                NULL);  
}

static void
change_to_bars (AwnCPUicon *self)
{
  g_object_set (self,
                "graph-type",GRAPH_BAR,
                NULL);
}

static void 
awn_CPUicon_show_context_menu(AwnCPUicon *self)
{
  AwnCPUiconPrivate *priv;
  AwnApplet         *applet;
  GtkWidget         *item;
  GtkWidget         *submenu;
  	
  priv = AWN_CPUICON_GET_PRIVATE (self);
  if (priv->context_menu)
  {
    gtk_widget_destroy (priv->context_menu);
  }
  g_object_get (self,
                "applet",&applet,
                NULL);
  
  priv->context_menu = awn_applet_create_default_menu(applet);
  item = gtk_menu_item_new_with_label ("Graph Type");
  gtk_menu_shell_append(GTK_MENU_SHELL(priv->context_menu), item);
  
  submenu = gtk_menu_new ();
  gtk_menu_item_set_submenu (GTK_MENU_ITEM(item),submenu);
  
  item = gtk_menu_item_new_with_label ("Area");
  gtk_menu_shell_append(GTK_MENU_SHELL(submenu), item);
  g_signal_connect_swapped (item, "activate", G_CALLBACK(change_to_area), self);
  item = gtk_menu_item_new_with_label ("Circle");
  gtk_menu_shell_append(GTK_MENU_SHELL(submenu), item);
  g_signal_connect_swapped (item, "activate", G_CALLBACK(change_to_circle), self);  
  item = gtk_menu_item_new_with_label ("Bars");
  gtk_menu_shell_append(GTK_MENU_SHELL(submenu), item);
  g_signal_connect_swapped (item, "activate", G_CALLBACK(change_to_bars), self);  
  
  item = awn_applet_create_about_item_simple (applet,
                                              "Copyright 2009 Rodney Cryderman <rcryderman@gmail.com>\n",
                                              AWN_APPLET_LICENSE_GPLV2,
                                              NULL);
  gtk_menu_shell_append(GTK_MENU_SHELL(priv->context_menu), item);
  
  gtk_widget_show_all (priv->context_menu);
  
  gtk_menu_popup(GTK_MENU(priv->context_menu), NULL, NULL, NULL, NULL, 0, gtk_get_current_event_time() );  
  
}

