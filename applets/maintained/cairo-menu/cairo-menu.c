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

static gboolean
cairo_menu_expose (GtkWidget *widget,GdkEventExpose *event,gpointer null)
{
  CairoMenuPrivate * priv = GET_PRIVATE(widget);  

  if (priv->cairo_style)
  {
    /*looks like I'm going to need look in the gtk_menu/gtk_menu_shell/etc expose functions and 
     borrow some code*/
    cairo_t * cr = gdk_cairo_create (widget->window);
    cairo_set_source_rgba (cr, 0.0,0.0,1.0,0.7);
    cairo_paint (cr);    
    cairo_destroy (cr);
    gtk_container_foreach (GTK_CONTAINER (widget),(GtkCallback)gtk_widget_queue_draw,NULL);    
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

  g_type_class_add_private (klass, sizeof (CairoMenuPrivate));

  object_class->get_property = cairo_menu_get_property;
  object_class->set_property = cairo_menu_set_property;
  object_class->dispose = cairo_menu_dispose;
  object_class->finalize = cairo_menu_finalize;
  object_class->constructed = cairo_menu_constructed;
}

static void
cairo_menu_init (CairoMenu *self)
{
  CairoMenuPrivate * priv = GET_PRIVATE (self);
  
  priv->cairo_style = FALSE;
}

GtkWidget*
cairo_menu_new (void)
{
  return g_object_new (AWN_TYPE_CAIRO_MENU, NULL);
}

