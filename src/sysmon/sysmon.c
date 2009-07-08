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

/* awn-sysmon.c */

#include "sysmon.h"
#include "cpuicon.h"
#include "loadicon.h"



G_DEFINE_TYPE (AwnSysmon, awn_sysmon, AWN_TYPE_APPLET)

#define AWN_SYSMON_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_SYSMON, AwnSysmonPrivate))

typedef struct _AwnSysmonPrivate AwnSysmonPrivate;

struct _AwnSysmonPrivate 
{
  GtkWidget * box;

  /*Made these into properties... 
   
   treating them as pointers for now ...  because I'm not really
   sure of certain behaviours/interactions
   */
  DesktopAgnosticConfigClient * client;
  DesktopAgnosticConfigClient * client_baseconf;
  
  
  GSList    * icon_list;
};

enum
{
  PROP_0,
  PROP_ICON_LIST,
  PROP_CLIENT,
  PROP_BRIDGE,
  PROP_CLIENT_BASECONF,
  PROP_BRIDGE_BASECONF
};

static void
awn_sysmon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  AwnSysmonPrivate * priv = AWN_SYSMON_GET_PRIVATE (object);
  switch (property_id) 
  {
    case PROP_ICON_LIST:
    {
      GValueArray *array;

      array = g_value_array_new (g_slist_length (priv->icon_list));
      for (GSList *node = priv->icon_list; node != NULL; node = node->next)
      {
        GValue val = {0};

        g_value_init (&val, G_TYPE_STRING);
        g_value_set_string (&val, (gchar*)node->data);
        array = g_value_array_append (array, &val);
        g_value_unset (&val);
      }
      g_value_take_boxed (value, array);
      break;
    }
    case PROP_CLIENT:
      g_value_set_object (value,priv->client);
      break;          
    case PROP_CLIENT_BASECONF:
      g_value_set_object (value,priv->client_baseconf);
      break;                
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

/*TODO put this in util functions.*/
static GSList *
free_string_slist (GSList * list)
{
  if (list)
  {
    GSList * iter;
    for (iter=list; iter; iter = g_slist_next(iter) )
    {
      g_free (iter->data);
    }
    g_slist_free (list);
    list = NULL;
  }
  return NULL;
}

static void
awn_sysmon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  AwnSysmonPrivate * priv = AWN_SYSMON_GET_PRIVATE (object);  
  switch (property_id) 
  {
    case PROP_ICON_LIST:
      priv->icon_list = free_string_slist (priv->icon_list);
      priv->icon_list = g_value_get_pointer (value);
      break;
    case PROP_CLIENT:
      g_assert (!priv->client); /*this should not be set more than once!*/
      priv->client = g_value_dup_object (value);
      break;
    case PROP_CLIENT_BASECONF:
      g_assert (!priv->client_baseconf); /*this should not be set more than once!*/
      priv->client_baseconf = g_value_dup_object (value);
      break;
    default:
      G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_sysmon_dispose (GObject *object)
{
  AwnSysmonPrivate * priv = AWN_SYSMON_GET_PRIVATE (object);  

  if (priv->client)
  {
    g_object_unref (priv->client);
  }
  if (priv->client_baseconf)
  {
    g_object_unref (priv->client_baseconf);
  }
  
  G_OBJECT_CLASS (awn_sysmon_parent_class)->dispose (object);
}

static void
awn_sysmon_finalize (GObject *object)
{
  AwnSysmonPrivate * priv = AWN_SYSMON_GET_PRIVATE (object);  
  priv->icon_list = free_string_slist (priv->icon_list);
  
  G_OBJECT_CLASS (awn_sysmon_parent_class)->finalize (object);
}

static void
awn_sysmon_constructed (GObject *object)
{
  gchar * uid;
  GtkWidget *icon;
  AwnSysmon * sysmon = AWN_SYSMON(object);
  AwnSysmonPrivate *priv;
  if (G_OBJECT_CLASS (awn_sysmon_parent_class)->constructed )
  {
    G_OBJECT_CLASS (awn_sysmon_parent_class)->constructed (object);
  }  
  
  priv = AWN_SYSMON_GET_PRIVATE (sysmon);        
  gchar * folder;
  GTimeVal cur_time;

  
  g_object_get (object,
                "uid", &uid,
                NULL);
  /* XXX moonbeam has a good reason that he's doing config this way.
   * DO NOT EMULATE UNLESS YOU HAVE A VERY GOOD REASON.
   */
  folder = g_strdup_printf("%s-%s",APPLET_NAME,uid);
  priv->client = awn_config_get_default_for_applet (AWN_APPLET(object), NULL);
  priv->client_baseconf = awn_config_get_default_for_applet_by_info (APPLET_NAME, NULL, NULL);
  
  g_free (folder);
  desktop_agnostic_config_client_bind (priv->client,
                                       "applet", "icon_list",
                                       G_OBJECT(object), "icon-list", FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_BOTH,
                                       NULL);
  g_get_current_time ( &cur_time);
  desktop_agnostic_config_client_set_int (priv->client,
                                          "applet",
                                          "time_stamp",
                                          cur_time.tv_sec,
                                          NULL);

  if (!priv->icon_list)
  {
    icon = awn_CPUicon_new (AWN_APPLET(sysmon),"default1");
    gtk_container_add (GTK_CONTAINER (priv->box), icon);  
    gtk_widget_show (icon);
  }
  else
  {
    /*TODO error check */
    GSList * iter;
    for (iter = priv->icon_list; iter; iter = g_slist_next(iter) )
    {
      GStrv tokens = g_strsplit (iter->data,"::",-1);
      if ( g_strcmp0 ("CPU",tokens[0])==0)
      {
        icon = awn_CPUicon_new (AWN_APPLET(sysmon),tokens[1]);
        gtk_container_add (GTK_CONTAINER (priv->box), icon);  
        gtk_widget_show (icon);
      }
      else
      {
        g_assert_not_reached();
      }
      g_strfreev(tokens);
    }
  }
  /* 
  icon = awn_CPUicon_new (GRAPH_CIRCLE,AWN_APPLET(sysmon));
  gtk_container_add (GTK_CONTAINER (priv->box), icon);  
  gtk_widget_show (icon);

  icon = awn_CPUicon_new (GRAPH_BAR,AWN_APPLET(sysmon));
  gtk_container_add (GTK_CONTAINER (priv->box), icon);  
  gtk_widget_show (icon);  

  icon = awn_loadicon_new (GRAPH_BAR,AWN_APPLET(sysmon));
  gtk_container_add (GTK_CONTAINER (priv->box), icon); 
  gtk_widget_show (icon);
*/
  
  g_free (uid);
}

static void
awn_sysmon_class_init (AwnSysmonClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);
  GParamSpec   *pspec;  

  object_class->get_property = awn_sysmon_get_property;
  object_class->set_property = awn_sysmon_set_property;
  object_class->dispose = awn_sysmon_dispose;
  object_class->finalize = awn_sysmon_finalize;
  object_class->constructed = awn_sysmon_constructed;

  pspec = g_param_spec_boxed ("icon-list",
                              "Icon list",
                              "The list of icons for this applet instance",
                              G_TYPE_VALUE_ARRAY,
                              G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_ICON_LIST, pspec);   

  pspec = g_param_spec_pointer ("bridge",
                               "bridge",
                               "Config client bridge",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_BRIDGE, pspec);   

  pspec = g_param_spec_pointer ("client",
                               "client",
                               "config client",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_CLIENT, pspec);   

  pspec = g_param_spec_pointer ("client-baseconf",
                               "client baseconf",
                               "config client baseconf",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_CLIENT_BASECONF, pspec);   
  
  g_type_class_add_private (klass, sizeof (AwnSysmonPrivate));
}


static void
awn_sysmon_init (AwnSysmon *sysmon)
{
  AwnSysmonPrivate *priv;
  priv = AWN_SYSMON_GET_PRIVATE (sysmon);
  
  /* Create the icon box */
  priv->box = awn_icon_box_new_for_applet (AWN_APPLET (sysmon));
  gtk_container_add (GTK_CONTAINER (sysmon), priv->box);
  gtk_widget_show (priv->box);

}

AwnSysmon*
awn_sysmon_new (const gchar * name,const gchar *uid,gint panel_id)
{
  return g_object_new (AWN_TYPE_SYSMON,
			    "name", name,
                            "uid", uid,
                            "panel-id", panel_id,
                            NULL);
}

