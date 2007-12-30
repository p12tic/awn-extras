/* -*- Mode: C; tab-width: 8; indent-tabs-mode: t; c-basic-offset: 8 -*- */
/*
 * Copyright (C) 2007 Neil J. Patel <njpatel@gmail.com>
 * Copyright (C) 2007 John Stowers <john.stower@gmail.com>
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <gtk/gtk.h>

#if !GTK_CHECK_VERSION(2,9,0)
#include <X11/Xlib.h>
#include <X11/extensions/shape.h>
#include <gdk/gdkx.h>
#endif
#include <libgnome/gnome-i18n.h>

#include <libawn/awn-applet-dialog.h>

#include "aff-window.h"
#include "aff-settings.h"

#define AFF_WINDOW_GET_PRIVATE(obj) (G_TYPE_INSTANCE_GET_PRIVATE ((obj), AFF_TYPE_WINDOW, AffWindowPrivate))

G_DEFINE_TYPE (AffWindow, aff_window, GTK_TYPE_WINDOW);

#define M_PI		3.14159265358979323846 

/* STRUCTS & ENUMS */
struct _AffWindowPrivate
{
	AffinityApp *app;
	
	gboolean have_alpha;
	
	gboolean rounded_corners;
	gfloat corner_radius;
	
	GtkWidget *button;
	
	gboolean pulse;
	gint rings;
	gboolean more;
};


/* FORWARDS */

static void aff_window_class_init(AffWindowClass *klass);
static void aff_window_init(AffWindow *window);
static void aff_window_finalize(GObject *obj); 
static void aff_window_update_input_shape (GtkWidget* window, int width, int height);

static gboolean aff_window_button_press_event(GtkWidget *widget, GdkEventButton *event);
static gboolean aff_window_expose_event(GtkWidget *widget, GdkEventExpose *event);

static GtkWindowClass *parent_class;


static gboolean
_pulse (AffWindow *window)
{
	AffWindowPrivate *priv;
	priv = AFF_WINDOW_GET_PRIVATE (window);
	static gint max_rings = 5;

	if (priv->pulse == FALSE) {
		return FALSE;
	}
	
	if (priv->more) {
		priv->rings++;
	} else {
		priv->rings--;
	}		
	
	if (priv->rings == max_rings)
		priv->more = FALSE;

	else if (priv->rings == 0)
		priv->more = TRUE;
	else
		;
	
	gtk_widget_queue_draw (GTK_WIDGET (window));
	return TRUE;
}


void 
aff_window_set_pulse (AffWindow *window, gboolean pulse)
{
	AffWindowPrivate *priv;
	priv = AFF_WINDOW_GET_PRIVATE (window);
	static guint tag = 0;
	
	if (pulse) {	
		priv->pulse = TRUE;
		tag = g_timeout_add (20, (GSourceFunc)_pulse, (gpointer)window);
	} else {
		g_source_remove (tag);
		priv->pulse = FALSE;
	}
}

void 
aff_window_enter_button (GtkButton *button, AffWindow *window)
{
	AffWindowPrivate *priv;
	priv = AFF_WINDOW_GET_PRIVATE (window);
	
	priv->button = GTK_WIDGET (button);
	gtk_widget_queue_draw (GTK_WIDGET (window));
}

void 
aff_window_leave_button (GtkButton *button, AffWindow *window)
{
	AffWindowPrivate *priv;
	priv = AFF_WINDOW_GET_PRIVATE (window);
	
	priv->button = NULL;
	gtk_widget_queue_draw (GTK_WIDGET (window));		
}

void 
aff_window_focus_in_button (GtkWidget *button,  GdkEventFocus *event, AffWindow *window)
{
	aff_window_enter_button (GTK_BUTTON (button), window);
}

void 
aff_window_focus_out_button (GtkWidget *button,  GdkEventFocus *event, AffWindow *window)
{
	aff_window_leave_button (GTK_BUTTON (button), window);
}
/*
static void
aff_window_save_position (AffWindow *window)
{
	GConfClient *client = aff_settings_get_client ();
	gint x, y;
	gtk_window_get_position (GTK_WINDOW (window), &x, &y);
	
	gconf_client_set_int (client, "/apps/affinity/window_xpos", x, NULL);
	gconf_client_set_int (client, "/apps/affinity/window_ypos", y, NULL);
}
*/

/* DRAWING FUNCTIONS */

static void
_rounded_rectangle (AffSettings *s, cairo_t *cr, double x, double y,  double w, double h, double radius)
{
	if (!s->rounded_corners) {
		cairo_rectangle (cr, x, y, w, h);
		return;
	}
	
	double RADIUS_CORNERS = radius;
	cairo_move_to (cr, x+radius, y);
	cairo_arc (cr, x+w-radius, y+radius, radius, M_PI * 1.5, M_PI * 2);
	cairo_arc (cr, x+w-radius, y+h-radius, radius, 0, M_PI * 0.5);
	cairo_arc (cr, x+radius,   y+h-radius, radius, M_PI * 0.5, M_PI);
	cairo_arc (cr, x+radius,   y+radius,   radius, M_PI, M_PI * 1.5);
	
	cairo_move_to (cr, x+RADIUS_CORNERS, y);
	cairo_line_to (cr, x+w-RADIUS_CORNERS, y);
	cairo_move_to (cr, w+x, y+RADIUS_CORNERS);
	cairo_line_to (cr, w+x, h+y-RADIUS_CORNERS);
	cairo_move_to (cr, w+x-RADIUS_CORNERS, h+y);
	cairo_line_to (cr, x+RADIUS_CORNERS, h+y);
	cairo_move_to (cr, x, h+y-RADIUS_CORNERS);
	cairo_line_to (cr, x, y+RADIUS_CORNERS);

}

static void
draw (GtkWidget *window, cairo_t *cr)
{
	AffWindowPrivate *priv;
    	AffSettings *s;
    	double width, height;
	GtkStyle *style;
	GdkColor step1;

	priv = AFF_WINDOW_GET_PRIVATE (window);
	s = priv->app->settings;
	width = window->allocation.width;
	height = window->allocation.height;
	
	aff_window_update_input_shape (window, width, height);

	style = gtk_widget_get_style (window);
	step1 = style->base[GTK_STATE_NORMAL];	

	/* clear window to fully transparent */
	cairo_set_source_rgba (cr, 1.0f, 1.0f, 1.0f, 0.0f);
	cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
	cairo_paint (cr);
	
	cairo_move_to(cr, 0, 0);
	cairo_set_line_width(cr, 1.0);
	
	cairo_pattern_t *pat;
	cairo_set_operator (cr, CAIRO_OPERATOR_OVER);


	/* main gradient */
	pat = cairo_pattern_create_linear (0.0, 0.0, 0.0, height);
	cairo_pattern_add_color_stop_rgba (pat, 0.0, s->back_step_1.red, 
						     s->back_step_1.green,
						     s->back_step_1.blue,	
						     s->back_step_1.alpha);
	cairo_pattern_add_color_stop_rgba (pat, 1.0, s->back_step_2.red, 
						     s->back_step_2.green,
						     s->back_step_2.blue,	
						     s->back_step_2.alpha);
	_rounded_rectangle (s, cr, 0, 0, width, height, 10);
	cairo_set_source(cr, pat);
	cairo_fill(cr);
	cairo_pattern_destroy(pat);

	/* internal hi-lightborder */
	cairo_set_source_rgba (cr, s->highlight.red, 
				   s->highlight.green,
				   s->highlight.blue,	
				   s->highlight.alpha);
	_rounded_rectangle (s, cr, 1.5, 1.5, width-3, height-3, 10);
	cairo_stroke(cr);
	
	/* border */
	cairo_set_source_rgba (	cr,s->border.red, 
				   s->border.green,
				   s->border.blue,	
				   s->border.alpha);
	_rounded_rectangle (s, cr, 0.5, 0.5, width-1, height-1, 10);
	cairo_stroke(cr);
	
	/* Entry border */
	GtkWidget *entry = priv->app->entry;
	double x, y, w, h;
	x = entry->allocation.x;
	y = entry->allocation.y;
	w = entry->allocation.width;
	h = entry->allocation.height;
	
	cairo_set_source_rgba (	cr, step1.red/65535.0,
				    step1.green/65535.0,
				    step1.blue/65535.0, 1.0);
	_rounded_rectangle (s, cr, x-1.5, y-0.5, w+2, h, 4);
	cairo_fill_preserve (cr);	
	cairo_set_source_rgba (	cr, s->widget_border.red, 
				    s->widget_border.green,
				    s->widget_border.blue,	
				    s->widget_border.alpha);
	cairo_stroke (cr);

	cairo_set_source_rgba (cr,  s->widget_highlight.red, 
				    s->widget_highlight.green,
				    s->widget_highlight.blue,	
				    s->widget_highlight.alpha);
	_rounded_rectangle (s, cr, x-2.5, y-1.5, w+4, h+2, 4);
	cairo_stroke (cr);			

	/* Progress */
	if (priv->pulse) {
		int i = 0;
		for (i =0; i < priv->rings; i++) {
			
			cairo_set_source_rgba (cr, s->widget_highlight.red, 
				    		   s->widget_highlight.green,
				    	           s->widget_highlight.blue,	
				    		   s->widget_highlight.alpha - (0.2 * i));
			
			_rounded_rectangle (s, cr, x-2.5-i, y-1.5-i, w+4+(2*i), h+2+(2*i), 4);
			
			cairo_stroke (cr);
		}	
	}
	/* Main hilight gradient */
	pat = cairo_pattern_create_linear (0.0, 0.0, 0.0, height);
	cairo_pattern_add_color_stop_rgba (pat, 0.0, s->hi_step_1.red, 
						     s->hi_step_1.green,
						     s->hi_step_1.blue,	
						     s->hi_step_1.alpha);
	cairo_pattern_add_color_stop_rgba (pat, 1.0, s->hi_step_2.red, 
						     s->hi_step_2.green,
						     s->hi_step_2.blue,	
						     s->hi_step_2.alpha);
	
	_rounded_rectangle (s, cr, 1.5, 1.5, width-2, y+(h/2), 10);
	cairo_set_source(cr, pat);
	cairo_fill(cr);
	cairo_pattern_destroy(pat);
	
	if (priv->button) {
		x = priv->button->allocation.x;
		y = priv->button->allocation.y;
		w = priv->button->allocation.width;
		h = priv->button->allocation.height;

		cairo_set_source_rgba (	cr, s->widget_border.red, 
					    s->widget_border.green,
					    s->widget_border.blue,		
					    s->widget_border.alpha);
		_rounded_rectangle (s, cr, x-0.5, y-0.5, w, h, 4);
		cairo_fill (cr);
	
		cairo_set_source_rgba (cr,  s->widget_highlight.red, 
					    s->widget_highlight.green,
					    s->widget_highlight.blue,		
					    s->widget_highlight.alpha);
		_rounded_rectangle (s, cr, x-1.5, y-1.5, w+2, h+2, 4);
		cairo_stroke (cr);
	}	

	/* Treeview border */
	if (!priv->app->searching)
		return;
	GtkWidget *treeview = priv->app->treeview;
	x = treeview->allocation.x;
	y = treeview->allocation.y;
	w = treeview->allocation.width;
	h = treeview->allocation.height;
	
	cairo_set_source_rgba (	cr, step1.red/65535.0,
				    step1.green/65535.0,
				    step1.blue/65535.0, 1.0);
	_rounded_rectangle (s, cr, x-0.5, y-0.5, w+1, h+1, 3);
	cairo_fill_preserve (cr);	
	cairo_set_source_rgba (	cr, s->widget_border.red, 
				    s->widget_border.green,
				    s->widget_border.blue,	
				    s->widget_border.alpha);
	cairo_stroke (cr);
	
	cairo_set_source_rgba (	cr, s->widget_highlight.red, 
				    s->widget_highlight.green,
				    s->widget_highlight.blue,	
				    s->widget_highlight.alpha);
	_rounded_rectangle (s, cr, x-1.5, y-1.5, w+3, h+3, 3); 
	cairo_stroke (cr);			
}

static void 
draw_pixmap (GtkWidget *window, cairo_t *cr)
{
	double width, height;
	width = window->allocation.width;
	height = window->allocation.height;

	/* clear window to fully transparent */
	cairo_set_source_rgba (cr, 1.0f, 1.0f, 1.0f, 1.0f);
	cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
	cairo_paint (cr);

	cairo_move_to(cr, 0, 0);
	cairo_set_line_width(cr, 1.0);

	/* fill */
	cairo_set_source_rgba (	cr, 0, 0, 0, 1);
	cairo_rectangle (cr,0, 0, width, height);
	cairo_stroke(cr);
}

/*  CALLBACKS */


static gboolean
aff_window_button_press_event(GtkWidget *widget, GdkEventButton *event)
{
	switch (event->button) {
	
		case 1:
			gtk_window_begin_move_drag (GTK_WINDOW(widget),
						    event->button,
						    event->x_root,
						    event->y_root,
						    event->time);
			break;
		case 3:
			g_print("Popup a user-settable menu\n");
			break;
		default:
			break;
	}
	return FALSE;
}

static gboolean
aff_window_expose_event(GtkWidget *widget, GdkEventExpose *event)
{
	cairo_t *cr;
	cr = gdk_cairo_create (widget->window);
	draw (widget, cr);
	cairo_destroy (cr);
	
	return GTK_WIDGET_CLASS(parent_class)->expose_event(widget, event);
}

#if !GTK_CHECK_VERSION(2,9,0)
/* this is piece by piece taken from gtk+ 2.9.0 (CVS-head with a patch applied
regarding XShape's input-masks) so people without gtk+ >= 2.9.0 can compile and
run input_shape_test.c */
static void 
aff_window_do_shape_combine_mask (GdkWindow* window, GdkBitmap* mask, gint x, gint y)
{
	Pixmap pixmap;
	int ignore;
	int maj;
	int min;

	if (!XShapeQueryExtension (GDK_WINDOW_XDISPLAY (window), &ignore, &ignore))
		return;

	if (!XShapeQueryVersion (GDK_WINDOW_XDISPLAY (window), &maj, &min))
		return;

	/* for shaped input we need at least XShape 1.1 */
	if (maj != 1 && min < 1)
		return;

	if (mask)
		pixmap = GDK_DRAWABLE_XID (mask);
	else
	{
		x = 0;
		y = 0;
		pixmap = None;
	}

	XShapeCombineMask (GDK_WINDOW_XDISPLAY (window),
					   GDK_DRAWABLE_XID (window),
					   ShapeInput,
					   x,
					   y,
					   pixmap,
					   ShapeSet);
}
#endif

static void 
aff_window_update_input_shape (GtkWidget* window, int width, int height)
{
	AffWindowPrivate *priv;
	static GdkBitmap* shape_bitmap = NULL;
	static cairo_t* cr = NULL;

	priv = AFF_WINDOW_GET_PRIVATE (AFF_WINDOW (window));

	shape_bitmap = (GdkBitmap*) gdk_pixmap_new (NULL, width, height, 1);
	if (shape_bitmap)
	{
		cr = gdk_cairo_create (shape_bitmap);
		if (cairo_status (cr) == CAIRO_STATUS_SUCCESS)
		{
			draw_pixmap (window, cr);
			cairo_destroy (cr);

#if !GTK_CHECK_VERSION(2,9,0)
			aff_window_do_shape_combine_mask (window->window, NULL, 0, 0);
			aff_window_do_shape_combine_mask (window->window, shape_bitmap, 0, 0);
#else
			gtk_widget_input_shape_combine_mask (window, NULL, 0, 0);
			gtk_widget_input_shape_combine_mask (window, shape_bitmap, 0, 0);
#endif
		}
		g_object_unref ((gpointer) shape_bitmap);
	}
	//aff_window_save_position (AFF_WINDOW (window));
}


static gboolean 
aff_window_configure_event (GtkWidget* window, GdkEventConfigure* event)
{
	gint new_width = event->width;
	gint new_height = event->height;

	aff_window_update_input_shape (window, new_width, new_height);
	return FALSE;
}

static void 
aff_window_screen_changed (GtkWidget* widget, GdkScreen* old_screen)
{                       
	AffWindow *window;
	AffWindowPrivate *priv;
	GdkScreen* new_screen;
	GdkColormap* colormap;
	
	window = AFF_WINDOW(widget);
	priv = AFF_WINDOW_GET_PRIVATE (window);
	new_screen = gtk_widget_get_screen (widget);
	colormap = gdk_screen_get_rgba_colormap (new_screen);
      
	if (!colormap) {
		colormap = gdk_screen_get_rgb_colormap (new_screen);
		priv->have_alpha = FALSE;
	} else
		priv->have_alpha = TRUE;
	
	gtk_widget_set_colormap (widget, colormap);
}


/*  GOBJECT INIT CODE */
static void
aff_window_class_init(AffWindowClass *klass)
{
	GObjectClass *gobject_class;
	GtkWidgetClass *widget_class;

	parent_class = g_type_class_peek_parent(klass);

	gobject_class = G_OBJECT_CLASS(klass);
	g_type_class_add_private (gobject_class, sizeof (AffWindowPrivate));
	gobject_class->finalize = aff_window_finalize;
	
	widget_class = GTK_WIDGET_CLASS(klass);
	widget_class->button_press_event = aff_window_button_press_event;
	widget_class->expose_event = aff_window_expose_event;
	widget_class->screen_changed = aff_window_screen_changed;
	//widget_class->configure_event = aff_window_configure_event;
}

static void
aff_window_init(AffWindow *window)
{
	AffWindowPrivate *priv;
	
	priv = AFF_WINDOW_GET_PRIVATE (window);
	
	priv->rounded_corners = TRUE;
	priv->corner_radius = 10;
	priv->button = NULL;
	
	aff_window_screen_changed (GTK_WIDGET(window), NULL);
	gtk_widget_set_app_paintable (GTK_WIDGET(window), TRUE);
	gtk_widget_add_events(GTK_WIDGET(window), GDK_ALL_EVENTS_MASK);
	
}



static void
aff_window_finalize(GObject *obj)
{
	AffWindow *window;
	
	g_return_if_fail(obj != NULL);
	g_return_if_fail(AFF_IS_WINDOW(obj));

	window = AFF_WINDOW(obj);
	
	if (G_OBJECT_CLASS(parent_class)->finalize)
		G_OBJECT_CLASS(parent_class)->finalize(obj);
}

GtkWidget *
aff_window_new(AffinityApp *app, AwnApplet *applet)
{
	AffWindowPrivate *priv;
	
	AwnAppletDialog *window = NULL;
    window = g_object_new(AFF_TYPE_WINDOW, 
					 "type", GTK_WINDOW_POPUP,
					 "decorated", FALSE,
					 "default-height", 500,
					 "default-width", 600,
					 "icon-name", "search",
					 "focus-on-map", TRUE,
					 "title", _("Affinity Search Window"),
  					 "window_position", GTK_WIN_POS_NONE,
					 "modal", FALSE,
					 "destroy_with_parent", TRUE,
					 "gravity", GDK_GRAVITY_NORTH_WEST,
					 NULL);

	gtk_window_set_type_hint (GTK_WINDOW (window), GDK_WINDOW_TYPE_HINT_MENU);

	priv = AFF_WINDOW_GET_PRIVATE (window);					 
	priv->app = app;
			 			   
	return GTK_WIDGET(window);
}

