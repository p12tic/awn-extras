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

G_DEFINE_TYPE (AwnSysmon, awn_sysmon, AWN_TYPE_APPLET)

#define AWN_SYSMON_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_SYSMON, AwnSysmonPrivate))

typedef struct _AwnSysmonPrivate AwnSysmonPrivate;

struct _AwnSysmonPrivate {
    GtkWidget * box;
};

static void
awn_sysmon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_sysmon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_sysmon_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_sysmon_parent_class)->dispose (object);
}

static void
awn_sysmon_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_sysmon_parent_class)->finalize (object);
}

static void
awn_sysmon_constructed (GObject *object)
{
  GtkWidget *icon;
  AwnSysmon * sysmon = AWN_SYSMON(object);
  AwnSysmonPrivate *priv;
  priv = AWN_SYSMON_GET_PRIVATE (sysmon);        
  
  icon = awn_CPUicon_new (GRAPH_DEFAULT,AWN_APPLET(sysmon));
  gtk_container_add (GTK_CONTAINER (priv->box), icon);  
  gtk_widget_show (icon);

  icon = awn_CPUicon_new (GRAPH_CIRCLE,AWN_APPLET(sysmon));
  gtk_container_add (GTK_CONTAINER (priv->box), icon);  
  gtk_widget_show (icon);
  
}

static void
awn_sysmon_class_init (AwnSysmonClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnSysmonPrivate));

  object_class->get_property = awn_sysmon_get_property;
  object_class->set_property = awn_sysmon_set_property;
  object_class->dispose = awn_sysmon_dispose;
  object_class->finalize = awn_sysmon_finalize;
  object_class->constructed = awn_sysmon_constructed;
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
awn_sysmon_new (const gchar *uid,
                  gint         orient,
                  gint         offset,
                  gint         size)
{
  return g_object_new (AWN_TYPE_SYSMON,
                            "uid", uid,
                            "orient", orient,
                            "offset", offset,
                            "size", size,
                            NULL);
}

