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
 
 /* awn-graph.h */

#ifndef _AWN_GRAPH
#define _AWN_GRAPH

#include <glib-object.h>
#include <cairo.h>
#include <gtk/gtk.h>

G_BEGIN_DECLS

#define AWN_TYPE_GRAPH awn_graph_get_type()

#define AWN_GRAPH(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_GRAPH, AwnGraph))

#define AWN_GRAPH_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_GRAPH, AwnGraphClass))

#define AWN_IS_GRAPH(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_GRAPH))

#define AWN_IS_GRAPH_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_GRAPH))

#define AWN_GRAPH_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_GRAPH, AwnGraphClass))

typedef struct {
  GObject parent;
} AwnGraph;

typedef struct {
  GObjectClass parent_class;
  void (*render_to_context) (AwnGraph * graph,cairo_t * ctx);
  void (*add_data) (AwnGraph * graph, gpointer data);
} AwnGraphClass;

GType awn_graph_get_type (void);

AwnGraph* awn_graph_new (void);

void awn_graph_render_to_context (AwnGraph * graph, cairo_t *ctx);
void awn_graph_add_data (AwnGraph * graph, gpointer data);

G_END_DECLS

#endif /* _AWN_GRAPH */
