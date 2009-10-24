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
/* cairo-menu-item.c */

#include "cairo-menu-item.h"

G_DEFINE_TYPE (CairoMenuItem, cairo_menu_item, GTK_TYPE_IMAGE_MENU_ITEM)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItemPrivate))

typedef struct _CairoMenuItemPrivate CairoMenuItemPrivate;

struct _CairoMenuItemPrivate {
  gboolean cairo_style;
  gchar * drag_source_data;
#if !GTK_CHECK_VERSION (2,16,0)  
  gchar * label;
#endif
};

enum
{
  PROP_0,
#if !GTK_CHECK_VERSION (2,16,0)    
  PROP_LABEL
#endif    
};
static void
cairo_menu_item_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(object);
  
  switch (property_id) {
#if !GTK_CHECK_VERSION (2,16,0)    
  case PROP_LABEL:
      g_value_set_string (value,priv->label);
      break;
#endif
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_item_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(object);
  
  switch (property_id) {
#if !GTK_CHECK_VERSION (2,16,0)    
  case PROP_LABEL:
    if (priv->label)
    {
      g_free (priv->label);
    }
    priv->label = g_value_dup_string (value);
    break;
#endif
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_item_dispose (GObject *object)
{
  if (G_OBJECT_CLASS (cairo_menu_item_parent_class)->dispose)
  {
    G_OBJECT_CLASS (cairo_menu_item_parent_class)->dispose (object);
  }
}

static void
cairo_menu_item_finalize (GObject *object)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(object);  
  if (priv->drag_source_data)
  {
 //   g_free(priv->drag_source_data);
    priv->drag_source_data = NULL;
  }
#if !GTK_CHECK_VERSION (2,16,0)  
  g_free (priv->label);
#endif
  if (G_OBJECT_CLASS (cairo_menu_item_parent_class)->finalize)
  {
    G_OBJECT_CLASS (cairo_menu_item_parent_class)->finalize (object);
  }
}

static gboolean
cairo_menu_item_expose (GtkWidget *widget,GdkEventExpose *event)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(widget);  

  if (priv->cairo_style)
  {
    cairo_t * cr = gdk_cairo_create (widget->window);
    cairo_set_source_rgba (cr, 0.0,0.0,0.4,0.0);
    cairo_paint (cr);
    cairo_destroy (cr);
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
#if !GTK_CHECK_VERSION (2,16,0)
  GtkWidget *label = gtk_label_new (priv->label);
  gtk_misc_set_alignment (GTK_MISC (label),0.0,0.5);
  gtk_container_add (GTK_CONTAINER(object),label);
#endif

  g_signal_connect (object,"expose-event",G_CALLBACK(cairo_menu_item_expose),NULL);
}


static void
cairo_menu_item_class_init (CairoMenuItemClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);
  GtkWidgetClass *widget_class = GTK_WIDGET_CLASS (klass);
  
  object_class->get_property = cairo_menu_item_get_property;
  object_class->set_property = cairo_menu_item_set_property;
  object_class->dispose = cairo_menu_item_dispose;
  object_class->finalize = cairo_menu_item_finalize;
  object_class->constructed = cairo_menu_item_constructed;

//  widget_class->expose_event = cairo_menu_item_expose;

#if !GTK_CHECK_VERSION (2,16,0)
  GParamSpec   *pspec;    
  pspec = g_param_spec_string ("label",
                               "label",
                               "Text Label String",
                                "",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_LABEL, pspec);
#endif
  
  g_type_class_add_private (klass, sizeof (CairoMenuItemPrivate));


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
  return g_object_new (AWN_TYPE_CAIRO_MENU_ITEM,
#if GTK_CHECK_VERSION (2,16,0)
                      "always-show-image",TRUE,
#endif
                      NULL);
}

GtkWidget*
cairo_menu_item_new_with_label (const gchar * label)
{
  return g_object_new (AWN_TYPE_CAIRO_MENU_ITEM,
                        "label",label,
#if GTK_CHECK_VERSION (2,16,0)                       
                        "always-show-image",TRUE,
#endif
                        NULL);
}

/*
 Drag and drop 
 */
static const GtkTargetEntry drop_types[] = 
{
  { (gchar*)"STRING", 0, 0 },
  { (gchar*)"text/plain", 0,  },
  { (gchar*)"text/uri-list", 0, 0 }
};

static void
_get_data (GtkWidget *widget,GdkDragContext   *drag_context,
           GtkSelectionData *data,guint info,guint time,gpointer null)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(widget);
  gtk_selection_data_set_text (data,priv->drag_source_data,-1);
}

void
cairo_menu_item_set_source (CairoMenuItem *item, gchar * drag_data)
{
  CairoMenuItemPrivate * priv = GET_PRIVATE(item);
  GtkWidget * image;

  if (priv->drag_source_data)
  {
    g_free(priv->drag_source_data);
    priv->drag_source_data = NULL;
  }
  g_object_get (item,
                "image",&image,
                NULL);
  priv->drag_source_data = g_strdup (drag_data);
  gtk_drag_source_set (GTK_WIDGET(item),GDK_BUTTON1_MASK,drop_types,3,GDK_ACTION_COPY);
  if (image)
  {
    if ( gtk_image_get_storage_type (GTK_IMAGE(image))==GTK_IMAGE_PIXBUF)
    {
      GdkPixbuf * pbuf = gtk_image_get_pixbuf (GTK_IMAGE(image));
      if (pbuf)
      {
        gtk_drag_source_set_icon_pixbuf (GTK_WIDGET(item),pbuf);
      }
    }
    else if (gtk_image_get_storage_type (GTK_IMAGE(image))==GTK_IMAGE_ICON_NAME)
    {
      gchar * icon_name;
      g_object_get (image,
                    "icon_name",&icon_name,
                    NULL);
      gtk_drag_source_set_icon_name (GTK_WIDGET(item),icon_name);
      g_free (icon_name);
    }
  }
  g_signal_connect (item,"drag-data-get",G_CALLBACK(_get_data),NULL);
}
