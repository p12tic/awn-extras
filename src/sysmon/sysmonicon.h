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

/* awn-sysmonicon.h */

#ifndef _AWN_SYSMONICON
#define _AWN_SYSMONICON

#include <gtk/gtk.h>
#include <glib-object.h>
#include <libawn/libawn.h>

#include "graph.h"
G_BEGIN_DECLS

#define AWN_TYPE_SYSMONICON awn_sysmonicon_get_type()

#define AWN_SYSMONICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_SYSMONICON, AwnSysmonicon))

#define AWN_SYSMONICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_SYSMONICON, AwnSysmoniconClass))

#define AWN_IS_SYSMONICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_SYSMONICON))

#define AWN_IS_SYSMONICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_SYSMONICON))

#define AWN_SYSMONICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_SYSMONICON, AwnSysmoniconClass))

typedef struct {
  AwnThemedIcon parent;
} AwnSysmonicon;

typedef struct {
  AwnThemedIconClass parent_class;

  /*< vtable >*/
  void          (*set_applet)         (AwnApplet * applet);

} AwnSysmoniconClass;

GType awn_sysmonicon_get_type (void);

GtkWidget* awn_sysmonicon_new (AwnApplet *);

AwnGraph * awn_sysmonicon_get_graph(AwnSysmonicon * icon);

void awn_sysmonicon_update_icon (AwnSysmonicon * icon);

G_END_DECLS

#endif /* _AWN_SYSMONICON */
