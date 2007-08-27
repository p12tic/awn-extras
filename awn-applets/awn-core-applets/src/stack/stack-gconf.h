/*
 * Copyright (c) 2007 Timon David Ter Braak
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

#ifndef __STACK_GCONF_H__
#define __STACK_GCONF_H__

#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>

void stack_gconf_init(
    AwnApplet * applet );
    
gboolean stack_gconf_is_composite_applet_icon();
gboolean stack_gconf_is_browsing();
gchar *stack_gconf_get_backend_folder();
gchar *stack_gconf_get_drag_action();

void stack_gconf_set_backend_folder( gchar * folder );

gchar *stack_gconf_get_applet_icon();
gchar *stack_gconf_get_default_drag_action();

guint stack_gconf_get_icon_size();
guint stack_gconf_get_max_rows();
guint stack_gconf_get_max_cols();

gboolean stack_gconf_show_files();
gboolean stack_gconf_show_hidden_files();
gboolean stack_gconf_show_folders();
gboolean stack_gconf_show_desktop_items();

void stack_gconf_get_border_color (AwnColor *color);
void stack_gconf_get_background_color (AwnColor *color);
void stack_gconf_get_icontext_color (AwnColor *color);

#endif /* __STACK_GCONF_H__ */
