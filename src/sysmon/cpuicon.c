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
 
 
 /* awn-CPUicon.c */

#include "cpuicon.h"

G_DEFINE_TYPE (AwnCPUicon, awn_CPUicon, AWN_TYPE_SYSMONICON)

#define AWN_CPUICON_GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CPUICON, AwnCPUiconPrivate))

typedef struct _AwnCPUiconPrivate AwnCPUiconPrivate;

struct _AwnCPUiconPrivate {
    guint timer_id;
    guint update_timeout;
};

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
_awn_CPUicon_update_icon(gpointer icon)
{
  g_debug ("Fire!\n");
  return TRUE;
}

static void
awn_CPUicon_constructed (GObject *object)
{
  AwnCPUiconPrivate * priv;
  priv = AWN_CPUICON_GET_PRIVATE (object);
  priv->timer_id = g_timeout_add(priv->update_timeout, _awn_CPUicon_update_icon, object);  
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
  GdkPixbuf * pixbuf;  
  AwnCPUiconPrivate *priv;
  	
  priv = AWN_CPUICON_GET_PRIVATE (self);
  priv->update_timeout = 1000;
}

GtkWidget*
awn_CPUicon_new (AwnApplet * applet)
{
  GtkWidget * cpuicon = NULL;
  cpuicon = g_object_new (AWN_TYPE_CPUICON,
                          "applet",applet,
                          NULL);
  return cpuicon;
}

