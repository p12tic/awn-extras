/* cairo-menu-item.c */

#include "cairo-menu-item.h"

G_DEFINE_TYPE (CairoMenuItem, cairo_menu_item, GTK_TYPE_IMAGE_MENU_ITEM)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItemPrivate))

typedef struct _CairoMenuItemPrivate CairoMenuItemPrivate;

struct _CairoMenuItemPrivate {
    gboolean cairo_style;
};

static void
cairo_menu_item_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_item_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_item_dispose (GObject *object)
{
  G_OBJECT_CLASS (cairo_menu_item_parent_class)->dispose (object);
}

static void
cairo_menu_item_finalize (GObject *object)
{
  G_OBJECT_CLASS (cairo_menu_item_parent_class)->finalize (object);
}

static gboolean
cairo_menu_item_expose (GtkWidget *widget,GdkEventExpose *event,gpointer null)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(widget);  

  if (priv->cairo_style)
  {
/*    cairo_t * cr = gdk_cairo_create (widget->window);
    g_debug ("%p",cr);
    cairo_set_source_rgba (cr, 1.0,0.0,0.0,1.0);
    cairo_fill (cr);
    cairo_destroy (cr);*/
    return TRUE;
  }
  else
  {
    return FALSE;
  }
}

static void
cairo_menu_item_constructed (GObject *object)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(object);
  
  if (G_OBJECT_CLASS (cairo_menu_item_parent_class)->constructed)
  {
    G_OBJECT_CLASS (cairo_menu_item_parent_class)->constructed (object);
  }

  g_signal_connect (object,"expose-event",G_CALLBACK(cairo_menu_item_expose),NULL);
}


static void
cairo_menu_item_class_init (CairoMenuItemClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (CairoMenuItemPrivate));

  object_class->get_property = cairo_menu_item_get_property;
  object_class->set_property = cairo_menu_item_set_property;
  object_class->dispose = cairo_menu_item_dispose;
  object_class->finalize = cairo_menu_item_finalize;
  object_class->constructed = cairo_menu_item_constructed;
}

static void
cairo_menu_item_init (CairoMenuItem *self)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(self);
  
  priv->cairo_style = FALSE;
}

GtkWidget*
cairo_menu_item_new (void)
{
  return g_object_new (AWN_TYPE_CAIRO_MENU_ITEM, NULL);
}

