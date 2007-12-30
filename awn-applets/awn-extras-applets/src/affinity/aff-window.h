/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*- */
/*
 * Copyright (C) 2007 Neil J. Patel <njpatel@gmail.com>
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
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 *
 * Authors: Neil J. Patel <njpatel@gmail.com>
 *
 */

#ifndef _AFF_WINDOW_H_
#define _AFF_WINDOW_H_

#include <gtk/gtkwindow.h>

#include <libawn/awn-applet.h>

#include "affinity.h"

typedef struct _AffWindow      AffWindow;
typedef struct _AffWindowClass AffWindowClass;
typedef struct _AffWindowPrivate  AffWindowPrivate;

#define AFF_TYPE_WINDOW            (aff_window_get_type())
#define AFF_WINDOW(obj)            (G_TYPE_CHECK_INSTANCE_CAST((obj), AFF_TYPE_WINDOW, AffWindow))
#define AFF_WINDOW_CLASS(klass)    (G_TYPE_CHECK_CLASS_CAST((klass), AFF_TYPE_WINDOW, AffWindowClass))
#define AFF_IS_WINDOW(obj)         (G_TYPE_CHECK_INSTANCE_TYPE((obj), AFF_TYPE_WINDOW))
#define AFF_IS_WINDOW_CLASS(klass) (G_TYPE_CHECK_CLASS_TYPE((klass), AFF_TYPE_WINDOW))
#define AFF_WINDOW_GET_CLASS(obj)  (G_TYPE_INSTANCE_GET_CLASS((obj), AFF_TYPE_WINDOW, AffWindowClass))

struct _AffWindow
{
	GtkWindow parent;
	AffWindowPrivate *priv;
};

struct _AffWindowClass
{
	GtkWindowClass parent_class;
};

G_BEGIN_DECLS

GType      aff_window_get_type(void);
GtkWidget *aff_window_new(AffinityApp *app, AwnApplet *applet);
void       aff_window_position_to_widget(AffWindow *tooltip, GtkWidget *widget);
void       aff_window_position_to_rect(AffWindow *tooltip, GdkRectangle *rect, GdkScreen *screen);

void aff_window_enter_button (GtkButton *button, AffWindow *window);
void aff_window_leave_button (GtkButton *button, AffWindow *window);
void aff_window_focus_in_button (GtkWidget *button,  GdkEventFocus *event, AffWindow *window);
void aff_window_focus_out_button (GtkWidget *button,  GdkEventFocus *event, AffWindow *window);

void aff_window_set_pulse (AffWindow *window, gboolean pulse);

G_END_DECLS

#endif
