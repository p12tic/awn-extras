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
 
 /* awn-areagraph.h */

#ifndef _AWN_AREAGRAPH
#define _AWN_AREAGRAPH

#include <glib-object.h>
#include "graph.h"

G_BEGIN_DECLS

#define AWN_TYPE_AREAGRAPH awn_areagraph_get_type()

#define AWN_AREAGRAPH(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_AREAGRAPH, Awn_Areagraph))

#define AWN_AREAGRAPH_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_AREAGRAPH, Awn_AreagraphClass))

#define AWN_IS_AREAGRAPH(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_AREAGRAPH))

#define AWN_IS_AREAGRAPH_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_AREAGRAPH))

#define AWN_AREAGRAPH_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_AREAGRAPH, Awn_AreagraphClass))

typedef struct 
{
  AwnGraph parent;
} Awn_Areagraph;

typedef struct 
{
  AwnGraphClass parent_class;
} Awn_AreagraphClass;


GType awn_areagraph_get_type (void);

GtkWidget* awn_areagraph_new (gint num_points, gdouble min_val, gdouble max_val);

void awn_areagraph_clear (Awn_Areagraph *self,gdouble val);

G_END_DECLS

#endif /* _AWN_AREAGRAPH */

