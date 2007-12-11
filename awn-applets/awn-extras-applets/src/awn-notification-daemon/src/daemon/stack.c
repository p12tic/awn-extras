/* daemon.c - Implementation of the destop notification spec
 *
 * Awn related modifications by Rodney Cryderman <rcryderman@gmail.com>
 *
 * Base gnome-notification-daemon by
 * Copyright (C) 2006 Christian Hammond <chipx86@chipx86.com>
 *
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 */

#include "config.h"
#include "engines.h"
#include "stack.h"

#include <X11/Xproto.h>
#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <gdk/gdkx.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-applet-dialog.h>

struct _NotifyStack
{
	NotifyDaemon *daemon;
	GdkScreen *screen;
	guint monitor;
	NotifyStackLocation location;
	GSList *windows;
};

extern AwnApplet *G_awn_app;
extern int G_awn_app_height;
extern int G_awn_override_y;
extern int G_awn_override_x;

static gboolean
get_work_area(GtkWidget *nw, GdkRectangle *rect)
{
	Atom workarea = XInternAtom(GDK_DISPLAY(), "_NET_WORKAREA", True);
	Atom type;
	Window win;
	int format;
	gulong num, leftovers;
	gulong max_len = 4 * 32;
	guchar *ret_workarea;
	long *workareas;
	int result;
	GdkScreen *screen;
	int disp_screen;

	gtk_widget_realize(nw);
	screen = gdk_drawable_get_screen(GDK_DRAWABLE(nw->window));
	disp_screen = GDK_SCREEN_XNUMBER(screen);

	/* Defaults in case of error */
	rect->x = 0;
	rect->y = 0;
	rect->width = gdk_screen_get_width(screen);
	rect->height = gdk_screen_get_height(screen);

	if (workarea == None)
		return FALSE;

	win = XRootWindow(GDK_DISPLAY(), disp_screen);
	result = XGetWindowProperty(GDK_DISPLAY(), win, workarea, 0,
								max_len, False, AnyPropertyType,
								&type, &format, &num, &leftovers,
								&ret_workarea);

	if (result != Success || type == None || format == 0 || leftovers ||
		num % 4)
	{
		return FALSE;
	}

	workareas = (long *)ret_workarea;
	rect->x      = workareas[disp_screen * 4];
	rect->y      = workareas[disp_screen * 4 + 1];
	rect->width  = workareas[disp_screen * 4 + 2];
	rect->height = workareas[disp_screen * 4 + 3];

	XFree(ret_workarea);

	return TRUE;
}

static void get_origin_awn(gint *x, gint *y,gint width, gint height)
{
        gint ax, ay, aw, ah;
        gint w, h;
        w=width;
        h=height;
        gdk_window_get_origin (GTK_WIDGET (G_awn_app)->window, 
                         &ax, &ay);

	ax=G_awn_override_x>=0?G_awn_override_x:ax;

	
        gtk_widget_get_size_request (GTK_WIDGET (G_awn_app), 
                                     &aw, &ah);
        *x = ax - w/2 + aw/2;
        *y = gdk_screen_get_height (gdk_screen_get_default()) - height - G_awn_app_height*1.5;// + dialog->priv->offset;

	if ( G_awn_override_y>=0)
		*y=G_awn_override_y;
        
        if (*x < 0)
                *x = 2;
        if ((*x+w) > gdk_screen_get_width (gdk_screen_get_default()))
                *x = gdk_screen_get_width (gdk_screen_get_default ()) - w -20;       
}            



static void
get_origin_coordinates(NotifyStackLocation stack_location,
					   GdkRectangle *workarea,
					   gint *x, gint *y, gint *shiftx, gint *shifty,
					   gint width, gint height)
{
	switch (stack_location)
	{
		case NOTIFY_STACK_LOCATION_TOP_LEFT:
		case NOTIFY_STACK_LOCATION_TOP_RIGHT:
		case NOTIFY_STACK_LOCATION_BOTTOM_LEFT:
		case NOTIFY_STACK_LOCATION_BOTTOM_RIGHT:
        case NOTIFY_STACK_LOCATION_AWN:
            get_origin_awn(x,y,width,height);
            break;
		default:
			g_assert_not_reached();
	}
}

static void
translate_coordinates(NotifyStackLocation stack_location,
					  GdkRectangle *workarea,
					  gint *x, gint *y, gint *shiftx, gint *shifty,
					  gint width, gint height, gint index)
{
	gint 	stacking_direction=1;	//stack updward.
    gint 	tmp;
	switch (stack_location)
	{
		case NOTIFY_STACK_LOCATION_TOP_LEFT:
		case NOTIFY_STACK_LOCATION_TOP_RIGHT:
		case NOTIFY_STACK_LOCATION_BOTTOM_LEFT:
		case NOTIFY_STACK_LOCATION_BOTTOM_RIGHT:
        	case NOTIFY_STACK_LOCATION_AWN:
			tmp=*y;
			get_origin_awn(x,y,width,height);
			if (y<gdk_screen_get_height (gdk_screen_get_default() )/2 )
			{
				stacking_direction=-1; //stacking down
			}
			*y=tmp-height*0.95*stacking_direction;               
            break;
		default:
			g_assert_not_reached();
	}
}

NotifyStack *
notify_stack_new(NotifyDaemon *daemon,
				 GdkScreen *screen,
				 guint monitor,
				 NotifyStackLocation location)
{
	NotifyStack *stack;

	g_assert(daemon != NULL);
	g_assert(screen != NULL && GDK_IS_SCREEN(screen));
	g_assert(monitor < gdk_screen_get_n_monitors(screen));
	g_assert(location != NOTIFY_STACK_LOCATION_UNKNOWN);

	stack = g_new0(NotifyStack, 1);
	stack->daemon   = daemon;
	stack->screen   = screen;
	stack->monitor  = monitor;
	stack->location = location;

	return stack;
}

void
notify_stack_destroy(NotifyStack *stack)
{
	g_assert(stack != NULL);

	g_slist_free(stack->windows);
	g_free(stack);
}

void
notify_stack_set_location(NotifyStack *stack,
						  NotifyStackLocation location)
{
	stack->location = location;
}

static void
notify_stack_shift_notifications(NotifyStack *stack,
								 GtkWindow *nw,
								 GSList **nw_l,
								 gint init_width,
								 gint init_height,
								 gint *nw_x,
								 gint *nw_y)
{
	GdkRectangle workarea;
	GSList *l;
	gint x, y, shiftx = 0, shifty = 0, index = 1;

	get_work_area(GTK_WIDGET(nw), &workarea);
	get_origin_coordinates(stack->location, &workarea, &x, &y,
						   &shiftx, &shifty, init_width, init_height);

	if (nw_x != NULL)
		*nw_x = x;

	if (nw_y != NULL)
		*nw_y = y;

	for (l = stack->windows; l != NULL; l = l->next)
	{
		GtkWindow *nw2 = GTK_WINDOW(l->data);
		GtkRequisition req;

		if (nw2 != nw)
		{
			gtk_widget_size_request(GTK_WIDGET(nw2), &req);

			translate_coordinates(stack->location, &workarea, &x, &y,
								  &shiftx, &shifty, req.width, GTK_WIDGET(nw2)->allocation.height,
								  index++);
        //    printf("notify_stack_shift_notifications: %d, %d\n",x,y);								  
			move_notification(nw2, x, y);         /*AWN*/
		}
		else if (nw_l != NULL)
		{
			*nw_l = l;
		}
	}
}

void
notify_stack_add_window(NotifyStack *stack,
						GtkWindow *nw,
						gboolean new_notification)
{
	GtkRequisition req;
	gint x, y;

	gtk_widget_size_request(GTK_WIDGET(nw), &req);
#if 0
	notify_stack_shift_notifications(stack, nw, NULL,
									 req.width, req.height, &x, &y);
#else
    gtk_widget_show(nw);
		notify_stack_shift_notifications(stack, nw, NULL,
  									 req.width, GTK_WIDGET(nw)->allocation.height, &x, &y);
//	    gtk_widget_hide(nw);							 
#endif		
//    printf("notify_stack_add_window: %d, %d\n",x,y);				 
	move_notification(nw, x, y);

	if (new_notification)
	{
		g_signal_connect_swapped(G_OBJECT(nw), "destroy",
								 G_CALLBACK(notify_stack_remove_window),
								 stack);
		stack->windows = g_slist_prepend(stack->windows, nw);
	}
}

void
notify_stack_remove_window(NotifyStack *stack,
						   GtkWindow *nw)
{
	GSList *remove_l = NULL;

	notify_stack_shift_notifications(stack, nw, &remove_l, 0, 0, NULL, NULL);

	if (remove_l != NULL)
		stack->windows = g_slist_delete_link(stack->windows, remove_l);

	if (GTK_WIDGET_REALIZED(GTK_WIDGET(nw)))
		gtk_widget_unrealize(GTK_WIDGET(nw));
}
