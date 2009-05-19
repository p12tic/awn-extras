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
 
 /* awn-loadicon.h */

#ifndef _AWN_LOADICON
#define _AWN_LOADICON

#include <glib-object.h>
#include "sysmonicon.h"
#include "bargraph.h"

G_BEGIN_DECLS

#define AWN_TYPE_LOADICON awn_loadicon_get_type()

#define AWN_LOADICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_LOADICON, AwnLoadicon))

#define AWN_LOADICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_LOADICON, AwnLoadiconClass))

#define AWN_IS_LOADICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_LOADICON))

#define AWN_IS_LOADICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_LOADICON))

#define AWN_LOADICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_LOADICON, AwnLoadiconClass))

typedef struct {
  AwnSysmonicon parent;
} AwnLoadicon;

typedef struct {
  AwnSysmoniconClass parent_class;
} AwnLoadiconClass;

GType awn_loadicon_get_type (void);

GtkWidget* awn_loadicon_new (AwnGraphType graph_type,AwnApplet * applet);

G_END_DECLS

#endif /* _AWN_LOADICON */
