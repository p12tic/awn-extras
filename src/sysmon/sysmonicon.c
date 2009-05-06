/* awn-sysmonicon.c */

#include "sysmonicon.h"

G_DEFINE_TYPE (AwnSysmonicon, awn_sysmonicon, AWN_TYPE_ICON)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_SYSMONICON, AwnSysmoniconPrivate))

typedef struct _AwnSysmoniconPrivate AwnSysmoniconPrivate;

struct _AwnSysmoniconPrivate {
    int dummy;
};

static void
awn_sysmonicon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_sysmonicon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
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
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnSysmoniconPrivate));

  object_class->get_property = awn_sysmonicon_get_property;
  object_class->set_property = awn_sysmonicon_set_property;
  object_class->dispose = awn_sysmonicon_dispose;
  object_class->finalize = awn_sysmonicon_finalize;
}

static void
awn_sysmonicon_init (AwnSysmonicon *self)
{
}

GtkWidget*
awn_sysmonicon_new (void)
{
  return g_object_new (AWN_TYPE_SYSMONICON, NULL);
}

