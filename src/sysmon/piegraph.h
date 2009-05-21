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

/* awn-piegraph.h */

#ifndef _AWN_PIEGRAPH
#define _AWN_PIEGRAPH

#include <glib-object.h>
#include  "graph.h"

G_BEGIN_DECLS

#define AWN_TYPE_PIEGRAPH awn_piegraph_get_type()

#define AWN_PIEGRAPH(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_PIEGRAPH, AwnPieGraph))

#define AWN_PIEGRAPH_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_PIEGRAPH, AwnPieGraphClass))

#define AWN_IS_PIEGRAPH(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_PIEGRAPH))

#define AWN_IS_PIEGRAPH_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_PIEGRAPH))

#define AWN_PIEGRAPH_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_PIEGRAPH, AwnPieGraphClass))

typedef struct {
  AwnGraph parent;
} AwnPieGraph;

typedef struct {
  AwnGraphClass parent_class;
} AwnPieGraphClass;

GType awn_piegraph_get_type (void);

AwnPieGraph* awn_piegraph_new (void);

G_END_DECLS

#endif /* _AWN_PIEGRAPH */
