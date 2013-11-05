/* na-tray-child.h
 * Copyright (C) 2002 Anders Carlsson <andersca@gnu.org>
 * Copyright (C) 2003-2006 Vincent Untz
 * Copyright (C) 2008 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */

#ifndef __EGG_TRAY_CHILD_H__
#define __EGG_TRAY_CHILD_H__

#include <gtk/gtk.h>
#include <gdk/gdkx.h>

G_BEGIN_DECLS

#define EGG_TRAY_TYPE_CHILD			(egg_tray_child_get_type ())
#define EGG_TRAY_CHILD(obj)			(G_TYPE_CHECK_INSTANCE_CAST ((obj), EGG_TRAY_TYPE_CHILD, EggTrayChild))
#define EGG_TRAY_CHILD_CLASS(klass)		(G_TYPE_CHECK_CLASS_CAST ((klass), EGG_TRAY_TYPE_CHILD, EggTrayChildClass))
#define EGG_IS_TRAY_CHILD(obj)			(G_TYPE_CHECK_INSTANCE_TYPE ((obj), EGG_TRAY_TYPE_CHILD))
#define EGG_IS_TRAY_CHILD_CLASS(klass)		(G_TYPE_CHECK_CLASS_TYPE ((klass), EGG_TRAY_TYPE_CHILD))
#define EGG_TRAY_CHILD_GET_CLASS(obj)		(G_TYPE_INSTANCE_GET_CLASS ((obj), EGG_TRAY_TYPE_CHILD, EggTrayChildClass))

typedef struct _EggTrayChild	    EggTrayChild;
typedef struct _EggTrayChildClass  EggTrayChildClass;

struct _EggTrayChild
{
  GtkSocket parent_instance;
  Window icon_window;
  guint is_composited : 1;
  guint parent_relative_bg : 1;
  guint fake_transparency : 1;
};

struct _EggTrayChildClass
{
  GtkSocketClass parent_class;
};

GType            egg_tray_child_get_type          (void);

GtkWidget       *egg_tray_child_new               (GdkScreen    *screen,
                                                   Window        icon_window);
char            *egg_tray_child_get_title         (EggTrayChild *child);
gboolean         egg_tray_child_is_alpha_capable  (EggTrayChild *child);
cairo_surface_t *egg_tray_child_get_image_surface (EggTrayChild *child);

void             egg_tray_child_force_redraw      (EggTrayChild *child);

G_END_DECLS

#endif /* __EGG_TRAY_CHILD_H__ */
