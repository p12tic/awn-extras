/*
 * Copyright (C) 2007 Neil Jagdish Patel
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

#include <string.h>
#include <stdio.h>
#include <gtk/gtk.h>

#include <cairo.h>
#include <libawn/awn-alignment.h>
#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-defines.h>

#include <math.h>

#include "eggtraymanager.h"

typedef struct {
  AwnApplet      *applet;
  EggTrayManager *manager;
  
  GtkWidget      *align;
  GtkWidget      *table;
  GList          *icons;

} TrayApplet;

#define BORDER 2

static GQuark new_quark = 0;
static GQuark del_quark = 0;
static gint   n_rows    = 2;
static gint   n_cols    = 2;
static int    icon_size;
static AwnOrientation orientation;
static int    use_alpha = FALSE;

static void
tray_icon_added (EggTrayManager *manager, 
                 GtkWidget      *icon,
                 TrayApplet     *applet);

static void
tray_icon_removed (EggTrayManager *manager,
                   GtkWidget      *icon,
                   TrayApplet     *applet);

static void
tray_icon_message_sent (EggTrayManager *manager,
                        GtkWidget      *icon,
                        const char     *text,
                        glong           id,
                        glong           timeout,
                        TrayApplet     *applet);

static void
tray_icon_message_cancelled (EggTrayManager *manager,
                             GtkWidget      *icon,
                             glong           id,
                             TrayApplet     *applet);

static void
applet_expose_icon (GtkWidget *widget,
                    gpointer data);


static void
tray_applet_refresh (TrayApplet *applet)
{
  GList *children; GList *c;
  gint col = 0, row = 0;

  /* First lets go through existing icons, adding or deleting as necessary*/
  children = gtk_container_get_children (GTK_CONTAINER (applet->table));
  for (c = children; c != NULL; c = c->next)
    {
      GtkWidget *icon = GTK_WIDGET (c->data);
      gint del;

      if (!GTK_IS_WIDGET (icon))
        continue;
      del = GPOINTER_TO_INT (g_object_get_qdata (G_OBJECT(icon),del_quark));
      
      if (del)
        {
          gtk_container_remove (GTK_CONTAINER (applet->table), icon);
          continue;
        }
      else
        {
          gtk_container_child_set (GTK_CONTAINER (applet->table),
                                   icon,
                                   "top-attach", row,
                                   "bottom-attach", row+1,
                                   "left-attach", col,
                                   "right-attach", col+1,
                                   NULL);
          switch (orientation)
          {
            case AWN_ORIENTATION_TOP: case AWN_ORIENTATION_BOTTOM:
              if (++row == n_rows)
              {
                row = 0; col++;
              }
              break;
            default:
              if (++col == n_cols)
              {
                col = 0; row++;
              }
              break;
          }
        }
    }
  
  /* now the new icons */
  children = applet->icons;
  for (c = children; c != NULL; c = c->next)
  {
    GtkWidget *icon = GTK_WIDGET (c->data);
    gint new;

    if (!GTK_IS_WIDGET (icon))
      continue;
    new = GPOINTER_TO_INT (g_object_get_qdata (G_OBJECT(icon),new_quark));

    if (!new)
      continue;

    g_object_set_qdata (G_OBJECT (icon), new_quark,  GINT_TO_POINTER (0));
    gtk_table_attach_defaults (GTK_TABLE (applet->table),
                               icon,
                               col, col+1,
                               row, row+1);
    switch (orientation)
    {
      case AWN_ORIENTATION_TOP: case AWN_ORIENTATION_BOTTOM:
        if (++row == n_rows)
        {
          row = 0; col++;
        }
        break;
      default:
        if (++col == n_cols)
        {
          col = 0; row++;
        }
        break;
    }
  }

  guint elements = g_list_length(applet->icons);
  guint num_rows, num_columns;
  guint rows = n_rows, cols = n_cols;
  switch (orientation)
  {
    case AWN_ORIENTATION_TOP: case AWN_ORIENTATION_BOTTOM:
      g_object_get(applet->table, "n-columns", &num_columns, NULL);
      cols = elements % n_rows == 0 ?
        num_columns / n_rows : num_columns / n_rows + 1;
      break;
    default:
      g_object_get(applet->table, "n-rows", &num_rows, NULL);
      rows = elements % n_cols == 0 ?
        num_rows / n_cols : num_rows / n_cols + 1;
      break;
  }
  gtk_table_resize (GTK_TABLE (applet->table), rows ? rows:1, cols ? cols:1);

  gtk_widget_queue_draw (GTK_WIDGET (applet->applet));
}

static void
tray_icon_added (EggTrayManager *manager,
                 GtkWidget      *icon,
                 TrayApplet     *applet)
{
  g_object_set_qdata (G_OBJECT (icon), new_quark, GINT_TO_POINTER (1));
  g_object_set_qdata (G_OBJECT (icon), del_quark, GINT_TO_POINTER (0));

  applet->icons = g_list_append (applet->icons, icon);
  gtk_widget_set_size_request (icon, icon_size, icon_size);

  tray_applet_refresh (applet);
}

static void
tray_icon_removed (EggTrayManager *manager,
                   GtkWidget      *icon,
                   TrayApplet     *applet)
{
  g_object_set_qdata (G_OBJECT (icon), del_quark, GINT_TO_POINTER (1));

  applet->icons = g_list_remove (applet->icons, icon);
  tray_applet_refresh (applet);
}

static void
tray_icon_message_sent (EggTrayManager *manager,
                        GtkWidget      *icon,
                        const char     *text,
                        glong           id,
                        glong           timeout,
                        TrayApplet     *applet)
{
  /* FIXME: er, do somehting useful :-/ */
}

static void
tray_icon_message_cancelled (EggTrayManager *manager,
                             GtkWidget      *icon,
                             glong           id,
                             TrayApplet     *applet)
{
  /* FIXME: Er, cancel the message :-/? */
}

static void
applet_expose_icon (GtkWidget *widget,
                    gpointer data)
{
  cairo_t *cr = data;
  
  if (egg_tray_child_is_composited (EGG_TRAY_CHILD(widget)))
  {
    if (EGG_TRAY_CHILD(widget)->fake_transparency)
    {
      cairo_surface_t *img_srfc;
      int width, height, i, j;

      width = widget->allocation.width;
      height = widget->allocation.height;

      img_srfc = cairo_image_surface_create (CAIRO_FORMAT_ARGB32,
                                             width, height);
      cairo_t *ctx = cairo_create (img_srfc);
      cairo_set_operator (ctx, CAIRO_OPERATOR_SOURCE);
      gdk_cairo_set_source_pixmap (ctx, widget->window, 0, 0);
      cairo_paint (ctx);

      cairo_surface_flush (img_srfc);

      int row_stride = cairo_image_surface_get_stride (img_srfc);
      guchar *pixsrc, *target_pixels;
      
      target_pixels = cairo_image_surface_get_data (img_srfc);

      pixsrc = target_pixels;
      guint32 top_left = *(guint32*)(pixsrc);

      pixsrc = target_pixels + (4 * (width-1));
      guint32 top_right = *(guint32*)(pixsrc);

      pixsrc = target_pixels + (height-1) * row_stride;
      guint32 bottom_left = *(guint32*)(pixsrc);
      
      pixsrc = target_pixels + (height-1) * row_stride + (4 * (width-1));
      guint32 bottom_right = *(guint32*)(pixsrc);

      g_debug ("colors: %08x, %08x, %08x, %08x", top_left, top_right, bottom_left, bottom_right);

      // FIXME: some heuristic to pick the color;
      guint32 background_color = top_left;

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

      cairo_set_source_surface (cr, img_srfc,
                                widget->allocation.x, widget->allocation.y);
      cairo_paint (cr);

      // destroy the temp surface
      cairo_surface_destroy (img_srfc);
    }
    else
    {
      gdk_cairo_set_source_pixmap (cr, widget->window,
                                   widget->allocation.x,
                                   widget->allocation.y);
      cairo_paint (cr);
    }
  }
}

static gboolean
on_eb_expose (GtkWidget *widget, GdkEventExpose *event, gpointer data)
{
  GtkWidget* child = gtk_bin_get_child (GTK_BIN (widget));

  cairo_t *cr = gdk_cairo_create (widget->window);
  g_return_val_if_fail(cr, FALSE);

  if (use_alpha)
  {
    cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
    cairo_paint (cr);

    // FIXME: clip the paint area

    cairo_set_operator (cr, CAIRO_OPERATOR_OVER);

    // paint the composited children
    if (child)
      gtk_container_foreach (GTK_CONTAINER (child), applet_expose_icon, cr);
  }
  else
  {
    gdk_cairo_set_source_color (cr, &(gtk_widget_get_style(widget)->bg[GTK_STATE_NORMAL]));
    cairo_paint (cr);
  }

  cairo_destroy(cr);

  if (child)
    gtk_container_propagate_expose (GTK_CONTAINER (widget), child,  event);

  return TRUE;
}

static gboolean
applet_expose (GtkWidget *widget, GdkEventExpose *event, gpointer data)
{
  cairo_t *cr = gdk_cairo_create(widget->window);
  if (!cr) return FALSE;

  /* background is already cleared by AwnApplet */

  gint x, y, w, h;
  x = widget->allocation.x;
  y = widget->allocation.y;
  w = widget->allocation.width;
  h = widget->allocation.height;

  gdk_cairo_region (cr, event->region);
  cairo_clip (cr);

  cairo_set_operator(cr, CAIRO_OPERATOR_OVER);

  if (use_alpha == FALSE)
  {
    gdk_cairo_set_source_color (cr, &(gtk_widget_get_style(widget)->bg[GTK_STATE_NORMAL]));
  }
  else
  {
    cairo_set_source_rgba(cr, 0.0, 0.0, 0.0, 0.0);
  }

  cairo_set_line_width (cr, 1.0);

  awn_cairo_rounded_rect (cr, x+0.5, y+0.5, w-1.0, h-1.0,
                          2.0*BORDER, ROUND_ALL);
  cairo_fill_preserve(cr);

  GdkColor c = gtk_widget_get_style(widget)->dark[GTK_STATE_SELECTED];

  cairo_set_source_rgba (cr, c.red / 65535.0, c.green / 65535.0,
                         c.blue / 65535.0, 0.625);

  cairo_set_operator (cr, CAIRO_OPERATOR_DEST_OUT);
  cairo_set_line_width (cr, 1.5);

  cairo_stroke_preserve(cr);

  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);
  cairo_set_line_width (cr, 1.0);

  cairo_stroke(cr);

  cairo_destroy(cr);

  return FALSE;
}

static void
orient_changed(AwnApplet *applet, AwnOrientation orient, gpointer user_data)
{
  TrayApplet *tray_applet = user_data;

  orientation = orient;
  tray_applet_refresh(tray_applet);
}

static void
resize_icon(GtkWidget *widget, gpointer user_data)
{
  gtk_widget_set_size_request(widget, icon_size, icon_size);
}

static void
size_changed(AwnApplet *applet, guint size, gpointer user_data)
{
  GtkTable *table = GTK_TABLE (user_data);

  /*
   * " /2 " because we always have 2 rows/cols
   * " -1 " spacing in the table
   * "size % 2" compensates the table spacing
   */
  icon_size = size > 5 ? (size / 2) - 1 + (size % 2) : 1;

  // foreach child call set_size_request
  gtk_container_foreach (GTK_CONTAINER (table), resize_icon, NULL);

  gtk_widget_queue_draw (GTK_WIDGET (applet));
}

AwnApplet*
awn_applet_factory_initp (gchar *name, gchar* uid, gint panel_id)
{
  AwnApplet *applet = awn_applet_new (name, uid, panel_id);
  TrayApplet *app = g_new0 (TrayApplet, 1);
  GdkScreen  *screen;
  GtkWidget  *align, *table, *eb;

  /* Check if we're using => 2.15.0 */
  if ((gtk_major_version == 2 && gtk_minor_version >= 15) ||
      gtk_major_version > 2)
  {
    use_alpha = TRUE;
  }
  
  /* Er, why did I have to do this again ? */
  GtkWidget *widget = GTK_WIDGET (applet);
  while (widget->parent)
        widget = widget->parent;
  screen = gtk_widget_get_screen (GTK_WIDGET (widget));

  if (egg_tray_manager_check_running(screen))
  {
    const gchar *msg = "There is already another notification area "
                       "running on this screen!";

    GtkWidget *dialog = gtk_message_dialog_new (NULL, 
        GTK_DIALOG_MODAL, GTK_MESSAGE_ERROR, GTK_BUTTONS_CLOSE, "%s", msg);

    gtk_message_dialog_format_secondary_text (GTK_MESSAGE_DIALOG (dialog),
        "%s", "Please remove the existing notification area and then "
        "restart the applet.");

    gtk_dialog_run (GTK_DIALOG (dialog));
    gtk_widget_destroy (dialog);

    g_error ("%s\n", msg);
    return NULL;
  }

  new_quark = g_quark_from_string ("awn-na-icon-new");
  del_quark = g_quark_from_string ("awn-na-icon-del");

  app->applet = applet;
  app->manager = egg_tray_manager_new ();
  app->icons = NULL;

  if (!egg_tray_manager_manage_screen (app->manager, screen))
      g_warning ("The notification area could not manage the screen \n");

  g_signal_connect (app->manager, "tray_icon_added",
                    G_CALLBACK (tray_icon_added), app);
  g_signal_connect (app->manager, "tray_icon_removed",
                    G_CALLBACK (tray_icon_removed), app);
  g_signal_connect (app->manager, "message_sent",
                    G_CALLBACK (tray_icon_message_sent), app);
  g_signal_connect (app->manager, "message_cancelled",
                    G_CALLBACK (tray_icon_message_cancelled), app);

  orientation = awn_applet_get_orientation (applet);
  gint size = awn_applet_get_size (applet);
  icon_size = size > 5 ? (size / 2) - 1 + (size % 2) : 1;
  //gtk_widget_set_size_request (GTK_WIDGET (applet), -1, height* 2 );

  table = gtk_table_new (1, 1, FALSE);
  app->table = table;
  gtk_table_set_col_spacings (GTK_TABLE (table), 1);
  gtk_table_set_row_spacings (GTK_TABLE (table), 1);

  eb = gtk_event_box_new ();
  /* FIXME: connect only when use_alpha == FALSE ? */
  g_signal_connect_swapped (eb, "size-allocate",
                            G_CALLBACK (gtk_widget_queue_draw), applet);

  align = awn_alignment_new_for_applet (applet);
  awn_alignment_set_offset_modifier (AWN_ALIGNMENT (align), -BORDER);
  app->align = gtk_alignment_new (0.0, 0.0, 1.0, 1.0);
  gtk_alignment_set_padding (GTK_ALIGNMENT (app->align),
                             BORDER, BORDER, BORDER, BORDER);

  gtk_container_add (GTK_CONTAINER (applet), align);
  gtk_container_add (GTK_CONTAINER (align), app->align);
  gtk_container_add (GTK_CONTAINER (app->align), eb);
  if (gdk_screen_get_rgba_colormap (screen) != NULL)
  {
    gtk_widget_set_colormap (eb, gdk_screen_get_rgba_colormap (screen));
  }
  gtk_container_add (GTK_CONTAINER (eb), table);

  g_signal_connect(app->align, "expose-event",
                   G_CALLBACK (applet_expose), app);
  g_signal_connect(applet, "size-changed",
                   G_CALLBACK (size_changed), table);
  g_signal_connect(applet, "orientation-changed",
                   G_CALLBACK (orient_changed), app);
  g_signal_connect(eb, "expose-event",
                   G_CALLBACK (on_eb_expose), NULL);

  return applet;
}
