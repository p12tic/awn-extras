/* na-tray-child.c
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

#ifdef HAVE_CONFIG_H
 #include <config.h>
#endif
#include <string.h>

#include "egg-tray-child.h"

#include <glib/gi18n.h>
#include <gdk/gdkx.h>
#include <X11/Xatom.h>

G_DEFINE_TYPE (EggTrayChild, egg_tray_child, GTK_TYPE_SOCKET)

static void
egg_tray_child_finalize (GObject *object)
{
  G_OBJECT_CLASS (egg_tray_child_parent_class)->finalize (object);
}

static void
egg_tray_child_realize (GtkWidget *widget)
{
  EggTrayChild *child = EGG_TRAY_CHILD (widget);
  GdkVisual *visual = gtk_widget_get_visual (widget);
  gboolean visual_has_alpha;

  GTK_WIDGET_CLASS (egg_tray_child_parent_class)->realize (widget);

  /* We have alpha if the visual has something other than red, green, and blue */
  visual_has_alpha = visual->red_prec + visual->blue_prec + visual->green_prec < visual->depth;

  child->fake_transparency = FALSE;

  if (gdk_display_supports_composite (gtk_widget_get_display (widget)))
    {
      if (visual_has_alpha)
        {
          /* We have real transparency with an ARGB visual and the Composite extension.
           */

          /* Set a transparent background */
          GdkColor transparent = { 0, 0, 0, 0 }; /* only pixel=0 matters */
          gdk_window_set_background(widget->window, &transparent);
        }
      else
        {
          child->fake_transparency = TRUE;
        }

      gdk_window_set_composited (widget->window, TRUE);

      child->is_composited = TRUE;
      child->parent_relative_bg = FALSE;
    }
  else if (visual == gdk_window_get_visual (gdk_window_get_parent (widget->window)))
    {
      /* Otherwise, if the visual matches the visual of the parent window, we can
       * use a parent-relative background and fake transparency.
       */
      gdk_window_set_back_pixmap (widget->window, NULL, TRUE);

      child->is_composited = FALSE;
      child->parent_relative_bg = TRUE;
    }
  else
    {
      /* Nothing to do; the icon will sit on top of an ugly gray box */

      child->is_composited = FALSE;
      child->parent_relative_bg = FALSE;
    }

  gtk_widget_set_app_paintable (GTK_WIDGET (child),
				child->parent_relative_bg || child->is_composited);

  /* Double-buffering will interfere with the parent-relative-background fake
   * transparency, since the double-buffer code doesn't know how to fill in the
   * background of the double-buffer correctly.
   */
  gtk_widget_set_double_buffered (GTK_WIDGET (child), child->parent_relative_bg);
}

static void
egg_tray_child_style_set (GtkWidget *widget,
			 GtkStyle  *previous_style)
{
  /* The default handler resets the background according to the new
   * style.  We either use a transparent background or a parent-relative background
   * and ignore the style background. So, just don't chain up.
   */
}

#if 0
/* This is adapted from code that was commented out in na-tray-manager.c; the code
 * in na-tray-manager.c wouldn't have worked reliably, this will. So maybe it can
 * be reenabled. On other hand, things seem to be working fine without it.
 *
 * If reenabling, you need to hook it up in egg_tray_child_class_init().
 */
static void
egg_tray_child_size_request (GtkWidget      *widget,
			    GtkRequisition *request)
{
  GTK_WIDGET_CLASS (egg_tray_child_parent_class)->size_request (widget, request);

  /*
   * Make sure the icons have a meaningful size ..
   */ 
  if ((request->width < 16) || (request->height < 16))
    {
      g_warning (_("tray icon has requested a size of (%i x %i), resizing to (%i x %i)"), 
		 req.width, req.height, nw, nh);
      request->width = nw;
      request->height = nh;
    }
}
#endif

static void
egg_tray_child_size_allocate (GtkWidget      *widget,
			     GtkAllocation  *allocation)
{
  EggTrayChild *child = EGG_TRAY_CHILD (widget);

  gboolean moved = allocation->x != widget->allocation.x || allocation->y != widget->allocation.y;
  gboolean resized = allocation->width != widget->allocation.width || allocation->height != widget->allocation.height;

  /* When we are allocating the widget while mapped we need special handling for
   * both real and fake transparency.
   *
   *  Real transparency: we need to invalidate and trigger a redraw of the old
   *   and new areas. (GDK really should handle this for us, but doesn't as of
   *   GTK+-2.14)
   *
   * Fake transparency: if the widget moved, we need to force the contents to be
   *   redrawn with the new offset for the parent-relative background.
   */
  if ((moved || resized) && GTK_WIDGET_MAPPED (widget))
    {
      if (egg_tray_child_is_alpha_capable (child))
	gdk_window_invalidate_rect (gdk_window_get_parent (widget->window),
				    &widget->allocation, FALSE);
    }

  GTK_WIDGET_CLASS (egg_tray_child_parent_class)->size_allocate (widget, allocation);

  if ((moved || resized) && GTK_WIDGET_MAPPED (widget))
    {
      if (egg_tray_child_is_alpha_capable (EGG_TRAY_CHILD (widget)))
	gdk_window_invalidate_rect (gdk_window_get_parent (widget->window),
				    &widget->allocation, FALSE);
      else if (moved && child->parent_relative_bg)
	egg_tray_child_force_redraw (child);
    }
}

/* The plug window should completely occupy the area of the child, so we won't
 * get an expose event. But in case we do (the plug unmaps itself, say), this
 * expose handler draws with real or fake transparency.
 */
static gboolean
egg_tray_child_expose_event (GtkWidget      *widget,
			    GdkEventExpose *event)
{
  EggTrayChild *child = EGG_TRAY_CHILD (widget);

  if (child->is_composited && !child->fake_transparency)
    {
      /* Clear to transparent */
      cairo_t *cr = gdk_cairo_create (widget->window);
      cairo_set_source_rgba (cr, 0, 0, 0, 0);
      cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
      gdk_cairo_region (cr, event->region);
      cairo_fill (cr);
      cairo_destroy (cr);
    }
  else if (child->parent_relative_bg)
    {
      /* Clear to parent-relative pixmap */
      gdk_window_clear_area (widget->window,
			     event->area.x, event->area.y,
			     event->area.width, event->area.height);
    }

  return FALSE;
}

static void
egg_tray_child_init (EggTrayChild *child)
{
}

static void
egg_tray_child_class_init (EggTrayChildClass *klass)
{
  GObjectClass *gobject_class;
  GtkWidgetClass *widget_class;

  gobject_class = (GObjectClass *)klass;
  widget_class = (GtkWidgetClass *)klass;

  gobject_class->finalize = egg_tray_child_finalize;
  widget_class->style_set = egg_tray_child_style_set;
  widget_class->realize = egg_tray_child_realize;
  widget_class->size_allocate = egg_tray_child_size_allocate;
  widget_class->expose_event = egg_tray_child_expose_event;
}

GtkWidget *
egg_tray_child_new (GdkScreen *screen,
		   Window     icon_window)
{
  XWindowAttributes window_attributes;
  Display *xdisplay;
  EggTrayChild *child;
  GdkVisual *visual;
  GdkColormap *colormap;
  gboolean new_colormap;
  int result;

  g_return_val_if_fail (GDK_IS_SCREEN (screen), NULL);
  g_return_val_if_fail (icon_window != None, NULL);

  xdisplay = GDK_SCREEN_XDISPLAY (screen);

  /* We need to determine the visual of the window we are embedding and create
   * the socket in the same visual.
   */

  gdk_error_trap_push ();
  result = XGetWindowAttributes (xdisplay, icon_window,
				 &window_attributes);
  gdk_error_trap_pop ();

  if (!result) /* Window already gone */
    return NULL;

  visual = gdk_x11_screen_lookup_visual (screen,
					 window_attributes.visual->visualid);
  if (!visual) /* Icon window is on another screen? */
    return NULL;

  new_colormap = FALSE;

  if (visual == gdk_screen_get_rgb_visual (screen))
    colormap = gdk_screen_get_rgb_colormap (screen);
  else if (visual == gdk_screen_get_rgba_visual (screen))
    colormap = gdk_screen_get_rgba_colormap (screen);
  else if (visual == gdk_screen_get_system_visual (screen))
    colormap = gdk_screen_get_system_colormap (screen);
  else
    {
      colormap = gdk_colormap_new (visual, FALSE);
      new_colormap = TRUE;
    }

  child = g_object_new (EGG_TYPE_TRAY_CHILD, NULL);
  child->icon_window = icon_window;

  gtk_widget_set_colormap (GTK_WIDGET (child), colormap);

  if (new_colormap)
    g_object_unref (colormap);

  return GTK_WIDGET (child);
}

char *
egg_tray_child_get_title (EggTrayChild *child)
{
  char *retval = NULL;
  GdkDisplay *display;
  Atom utf8_string, atom, type;
  int result;
  int format;
  gulong nitems;
  gulong bytes_after;
  gchar *val;

  g_return_val_if_fail (EGG_IS_TRAY_CHILD (child), NULL);

  display = gtk_widget_get_display (GTK_WIDGET (child));

  utf8_string = gdk_x11_get_xatom_by_name_for_display (display, "UTF8_STRING");
  atom = gdk_x11_get_xatom_by_name_for_display (display, "_NET_WM_NAME");

  gdk_error_trap_push ();

  result = XGetWindowProperty (GDK_DISPLAY_XDISPLAY (display),
			       child->icon_window,
			       atom,
			       0, G_MAXLONG,
			       False, utf8_string,
			       &type, &format, &nitems,
			       &bytes_after, (guchar **)&val);
 
  if (gdk_error_trap_pop () || result != Success)
    return NULL;

  if (type != utf8_string ||
      format != 8 ||
      nitems == 0)
    {
      if (val)
	XFree (val);
      return NULL;
    }

  if (!g_utf8_validate (val, nitems, NULL))
    {
      XFree (val);
      return NULL;
    }

  retval = g_strndup (val, nitems);

  XFree (val);

  return retval;
}

gboolean
egg_tray_child_is_alpha_capable (EggTrayChild *child)
{
  g_return_val_if_fail (EGG_IS_TRAY_CHILD (child), FALSE);

  return child->is_composited;
}

static int
compare_colors (gconstpointer a, gconstpointer b)
{
  const guint32 *aa = a;
  const guint32 *bb = b;

  // we don't care about the alpha (it's FF anyways)
  return (*aa & 0x00ffffff) - (*bb & 0x00ffffff);
}

/* If we are faking alpha capability, we will provide a method to get cairo
 * image surface with transparent background.
 */
cairo_surface_t *
egg_tray_child_get_image_surface (EggTrayChild *child)
{
  g_return_val_if_fail (EGG_IS_TRAY_CHILD (child), NULL);

  GtkWidget *widget = (GtkWidget*)child;

  if (child->fake_transparency)
  {
    GArray *array;
    cairo_surface_t *img_srfc, *similar;
    int width, height, i, j;

    width = widget->allocation.width;
    height = widget->allocation.height;

    /* 
     * If GDK wasn't bugged on intrepid, we wouldn't have to use
     * an extra surface.
     */
    cairo_t *cr = gdk_cairo_create (widget->window);
    similar = cairo_surface_create_similar (cairo_get_target (cr),
                                            CAIRO_CONTENT_COLOR_ALPHA,
                                            width, height);
    cairo_t *ctx = cairo_create (similar);
    cairo_set_operator (ctx, CAIRO_OPERATOR_SOURCE);
    gdk_cairo_set_source_pixmap (ctx, widget->window, 0.0, 0.0);
    cairo_paint (ctx);

    cairo_destroy (ctx);
    cairo_destroy (cr);

    img_srfc = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                           width, height);
    ctx = cairo_create (img_srfc);
    cairo_set_operator (ctx, CAIRO_OPERATOR_SOURCE);
    cairo_set_source_surface (ctx, similar, 0.0, 0.0);
    cairo_paint (ctx);

    cairo_surface_flush (img_srfc);

    int row_stride = cairo_image_surface_get_stride (img_srfc);
    guchar *pixsrc, *target_pixels;

    target_pixels = cairo_image_surface_get_data (img_srfc);

    array = g_array_sized_new (FALSE, FALSE, sizeof (guint32), 4);

    // would this work fine on big endian?
    pixsrc = target_pixels;
    g_array_append_val (array, *(guint32*)(pixsrc)); // top left

    pixsrc = target_pixels + (4 * (width-1));
    g_array_append_val (array, *(guint32*)(pixsrc)); // top right
    g_array_append_val (array, *(guint32*)(pixsrc)); // top right

    pixsrc = target_pixels + (height-1) * row_stride;
    g_array_append_val (array, *(guint32*)(pixsrc)); // bottom left

    pixsrc = target_pixels + (height-1) * row_stride + (4 * (width-1));
    g_array_append_val (array, *(guint32*)(pixsrc)); // bottom right

    g_array_sort (array, compare_colors);

    // pick the color with a simple rule - most occurrences 
    //  (plus we use increased weight for the top right pixel)
    // if corner pixels are all different then we'll pick the "middle" one
    //  (black, gray, white -> gray)
    guint32 background_color = g_array_index (array, guint32, 2);

    g_array_free (array, TRUE);

    // replace the background color with transparent
    for (i = 0; i < height; i++)
    {
      pixsrc = target_pixels + i * row_stride;

      for (j = 0; j < width; j++)
      {
        guint32 pixel_color = *(guint32*)(pixsrc);
        if (pixel_color == background_color)
        {
          *(guint32*)(pixsrc) = 0;
        }
        pixsrc += 4;
      }
    }

    cairo_surface_mark_dirty (img_srfc);
    cairo_destroy (ctx);

    // destroy the temp surface
    cairo_surface_destroy (similar);

    return img_srfc;
  }
  else if (child->is_composited)
  {
    cairo_surface_t *img_srfc;
    int width, height;

    width = widget->allocation.width;
    height = widget->allocation.height;

    img_srfc = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                           width, height);
    cairo_t *ctx = cairo_create (img_srfc);
    cairo_set_operator (ctx, CAIRO_OPERATOR_SOURCE);
    gdk_cairo_set_source_pixmap (ctx, widget->window, 0.0, 0.0);
    cairo_paint (ctx);

    cairo_surface_flush (img_srfc);

    cairo_destroy (ctx);

    return img_srfc;
  }

  // FIXME: what if the display doesn't support composite extension?
  //   could we do the same as we're doing with fake_transparency?
  return NULL;
}

/* If we are faking transparency with a window-relative background, force a
 * redraw of the icon. This should be called if the background changes or if
 * the child is shifed with respect to the background.
 */
void
egg_tray_child_force_redraw (EggTrayChild *child)
{
  GtkWidget *widget = GTK_WIDGET (child);

  if (GTK_WIDGET_MAPPED (child) && child->parent_relative_bg)
    {
#if 1
      /* Sending an ExposeEvent might cause redraw problems if the
       * icon is expecting the server to clear-to-background before
       * the redraw. It should be ok for GtkStatusIcon or EggTrayIcon.
       */
      Display *xdisplay = GDK_DISPLAY_XDISPLAY (gtk_widget_get_display (widget));
      XEvent xev;

      xev.xexpose.type = Expose;
      xev.xexpose.window = GDK_WINDOW_XWINDOW (GTK_SOCKET (child)->plug_window);
      xev.xexpose.x = 0;
      xev.xexpose.y = 0;
      xev.xexpose.width = widget->allocation.width;
      xev.xexpose.height = widget->allocation.height;
      xev.xexpose.count = 0;

      gdk_error_trap_push ();
      XSendEvent (GDK_DISPLAY_XDISPLAY (gtk_widget_get_display (widget)),
		  xev.xexpose.window,
		  False, ExposureMask,
		  &xev);
     /* We have to sync to reliably catch errors from the XSendEvent(),
       * since that is asynchronous.
       */
      XSync (xdisplay, False);
      gdk_error_trap_pop ();
#else
      /* Hiding and showing is the safe way to do it, but can result in more
       * flickering.
       */
      gdk_window_hide (widget->window);
      gdk_window_show (widget->window);
#endif
    }
}

