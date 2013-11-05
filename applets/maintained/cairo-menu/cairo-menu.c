/*
 * Copyright (C) 2009 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
*/
/* cairo-menu.c */

#include "cairo-menu.h"
#include "cairo-menu-item.h"

G_DEFINE_TYPE (CairoMenu, cairo_menu, GTK_TYPE_MENU)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_MENU, CairoMenuPrivate))

typedef struct _CairoMenuPrivate CairoMenuPrivate;

struct _CairoMenuPrivate {
    gboolean cairo_style;
};

static void
cairo_menu_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_dispose (GObject *object)
{
  if (G_OBJECT_CLASS (cairo_menu_parent_class)->dispose)
  {
    G_OBJECT_CLASS (cairo_menu_parent_class)->dispose (object);
  }
}

static void
cairo_menu_finalize (GObject *object)
{
  if (G_OBJECT_CLASS (cairo_menu_parent_class)->finalize)
  {
    G_OBJECT_CLASS (cairo_menu_parent_class)->finalize (object);
  }
}
/*
 From gtkcontainer.c
 */
void
_container_propagate_expose (GtkContainer   *container,
                                GtkWidget      *child,
                                GdkEventExpose *event)
{
  GdkEvent *child_event;

  g_return_if_fail (GTK_IS_CONTAINER (container));
  g_return_if_fail (GTK_IS_WIDGET (child));
  g_return_if_fail (event != NULL);

  g_assert (child->parent == GTK_WIDGET (container));

  if (GTK_WIDGET_DRAWABLE (child) &&
      GTK_WIDGET_NO_WINDOW (child) &&
      (child->window == event->window)&&
      AWN_IS_CAIRO_MENU_ITEM(child))
    {
      child_event = gdk_event_new (GDK_EXPOSE);
      child_event->expose = *event;
      g_object_ref (child_event->expose.window);

      child_event->expose.region = gtk_widget_region_intersect (child, event->region);
      if (!gdk_region_empty (child_event->expose.region))
        {
          gdk_region_get_clipbox (child_event->expose.region, &child_event->expose.area);
          gtk_widget_send_expose (child, child_event);
        }
      gdk_event_free (child_event);
    }
}

/*
 From gtkcontainer.c
 */
static void
_expose_child (GtkWidget *child,gpointer   client_data)
{
  struct {
    GtkWidget *container;
    GdkEventExpose *event;
  } *data = client_data;

  gtk_container_propagate_expose (GTK_CONTAINER (data->container),
                                  child,
                                  data->event);
}

static gboolean
cairo_menu_expose (GtkWidget *widget,GdkEventExpose *event)
{
  struct {
    GtkWidget *container;
    GdkEventExpose *event;
  } data;

  CairoMenuPrivate * priv = GET_PRIVATE(widget);
  data.container = widget;
  data.event = event;

  if (priv->cairo_style)
  {
    double x,y,width,height;

    cairo_t * cr = gdk_cairo_create (widget->window);
    g_debug ("%s:  bit depth = %d",__func__,gdk_drawable_get_depth (widget->window));
    //g_debug ("Region %d,%d: %dx%d",event->area.x, event->area.y,event->area.width, event->area.height);
    x = event->area.x;
    y = event->area.y;
    width = event->area.width;
    height = event->area.height;
    cairo_set_source_rgba (cr,1.0,0.0,0.0,0.5);
    cairo_rectangle (cr, x,y,width,height);
    cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
    cairo_fill (cr);

    gtk_container_forall (GTK_CONTAINER (widget),_expose_child,&data);

    cairo_destroy (cr);
    return TRUE;
  }
  else
  {
    return FALSE;
  }
}

static void
cairo_menu_constructed (GObject *object)
{
  if (G_OBJECT_CLASS (cairo_menu_parent_class)->constructed)
  {
    G_OBJECT_CLASS (cairo_menu_parent_class)->constructed (object);
  }

  g_signal_connect (object,"expose-event",G_CALLBACK(cairo_menu_expose),NULL);
}

static void
cairo_menu_class_init (CairoMenuClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);
  GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);

  g_type_class_add_private (klass, sizeof (CairoMenuPrivate));

  object_class->get_property = cairo_menu_get_property;
  object_class->set_property = cairo_menu_set_property;
  object_class->dispose = cairo_menu_dispose;
  object_class->finalize = cairo_menu_finalize;
  object_class->constructed = cairo_menu_constructed;

//  widget_class->expose_event = cairo_menu_expose;
}

static void
cairo_menu_init (CairoMenu *self)
{
  CairoMenuPrivate * priv = GET_PRIVATE (self);

  priv->cairo_style = FALSE;
  if (priv->cairo_style)
  {
    static GdkScreen   * screen = NULL;
    static GdkColormap * newmap = NULL;
    if (!screen)
    {
      screen = gdk_screen_get_default();
    }
    if (!newmap)
    {
      newmap = gdk_screen_get_rgba_colormap (screen);
    }
    gtk_widget_set_colormap (GTK_WIDGET(self),newmap);
    awn_utils_ensure_transparent_bg (GTK_WIDGET(self));
  }
}

GtkWidget*
cairo_menu_new (void)
{
  return g_object_new (AWN_TYPE_CAIRO_MENU, NULL);
}

