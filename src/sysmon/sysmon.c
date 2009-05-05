/* awn-sysmon.c */

#include "sysmon.h"

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
awn_sysmon_class_init (AwnSysmonClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnSysmonPrivate));

  object_class->get_property = awn_sysmon_get_property;
  object_class->set_property = awn_sysmon_set_property;
  object_class->dispose = awn_sysmon_dispose;
  object_class->finalize = awn_sysmon_finalize;
}

static void
awn_sysmon_init (AwnSysmon *sysmon)
{
  AwnSysmonPrivate *priv;
  GtkWidget *icon;
  GdkPixbuf * pixbuf;
        
  priv = AWN_SYSMON_GET_PRIVATE (sysmon);
  
  /* Create the icon box */
  priv->box = awn_icon_box_new_for_applet (AWN_APPLET (sysmon));
  gtk_container_add (GTK_CONTAINER (sysmon), priv->box);
  gtk_widget_show (priv->box);
  icon = awn_icon_new ();
  pixbuf = gtk_icon_theme_load_icon (gtk_icon_theme_get_default (), 
                                     "gnome-system-monitor",
                                     40, 
                                     GTK_ICON_LOOKUP_FORCE_SVG, NULL);
  g_assert (pixbuf);
  g_debug ("SIZE = %u \n",awn_applet_get_size (AWN_APPLET(sysmon)));
  awn_icon_set_from_pixbuf (AWN_ICON(icon),pixbuf);
  gtk_container_add (GTK_CONTAINER (priv->box), icon);
  gtk_widget_show (icon);
  
  
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

