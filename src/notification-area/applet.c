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

#define BORDER 3

static GQuark new_quark = 0;
static GQuark del_quark = 0;
static gint   n_rows    = 2;
static gint   n_cols    = 2;
static int    size      = 0;
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
    gdk_cairo_set_source_pixmap (cr, widget->window,
                                 widget->allocation.x,
                                 widget->allocation.y);
    cairo_paint (cr);
  }
}

static gboolean
on_eb_expose (GtkWidget *widget, GdkEventExpose *event, gpointer data)
{
  cairo_t *cr = gdk_cairo_create (widget->window);
  if (use_alpha == FALSE || cr == NULL) return FALSE;

  cairo_set_operator (cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint (cr);

  cairo_set_operator (cr, CAIRO_OPERATOR_OVER);

  GtkWidget* child = gtk_bin_get_child(GTK_BIN(widget));

  // paint the composited children
  if (child)
    gtk_container_foreach (GTK_CONTAINER (child), applet_expose_icon, cr);

  cairo_destroy(cr);

  if (child)
    gtk_container_propagate_expose(GTK_CONTAINER(widget), child,  event);

  return TRUE;
}

static gboolean
applet_expose (GtkWidget *widget, GdkEventExpose *event, gpointer data)
{
  TrayApplet *app = data;
  GtkWidget *table = app->table;

  cairo_t *cr = gdk_cairo_create(widget->window);
  if (!cr) return FALSE;

  // don't clear the background - we already have a transparent background
  //  pixmap if we're running in composited mode

  gint x,y;
  gtk_widget_translate_coordinates(table, widget, 0, 0, &x, &y);

  if (g_list_length(app->icons) > 0)
  {
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER);

    if (use_alpha == FALSE)
    {
      gdk_cairo_set_source_color (cr, &(gtk_widget_get_style(widget)->bg[GTK_STATE_NORMAL]));
    }
    else
    {
      cairo_set_source_rgba(cr, 0.0, 0.0, 0.0, 0.0);
    }

    awn_cairo_rounded_rect (cr, x-BORDER, y-BORDER,
                            table->allocation.width + 2*BORDER,
                            table->allocation.height + 2*BORDER,
                            4.0*BORDER, ROUND_ALL);
    cairo_fill_preserve(cr);

    gdk_cairo_set_source_color (cr, &(gtk_widget_get_style(widget)->bg[GTK_STATE_SELECTED]));
    cairo_set_line_width(cr, 1.5);
    cairo_stroke(cr);
  }

  cairo_destroy(cr);

  GtkWidget* child = gtk_bin_get_child(GTK_BIN(widget));

  if (child)
    gtk_container_propagate_expose(GTK_CONTAINER(widget), child,  event);

  return TRUE;
}

static void
refresh_alignment(GtkAlignment *align, AwnOrientation orient, gint offset)
{
  switch (orient)
  {
    case AWN_ORIENTATION_TOP:
      gtk_alignment_set (align, 0.0, 0.0, 1.0, 0.0);
      gtk_alignment_set_padding (align, offset, 0, BORDER+1, BORDER+1);
      break;
    case AWN_ORIENTATION_BOTTOM:
      gtk_alignment_set (align, 0.0, 1.0, 1.0, 0.0);
      gtk_alignment_set_padding (align, 0, offset, BORDER+1, BORDER+1);
      break;
    case AWN_ORIENTATION_LEFT:
      gtk_alignment_set (align, 0.0, 0.0, 0.0, 1.0);
      gtk_alignment_set_padding (align, BORDER+1, BORDER+1, offset, 0);
      break;
    case AWN_ORIENTATION_RIGHT:
      gtk_alignment_set (align, 1.0, 0.0, 0.0, 1.0);
      gtk_alignment_set_padding (align, BORDER+1, BORDER+1, 0, offset);
      break;
  }
}

static void
offset_changed(AwnApplet *applet, gint offset, gpointer user_data)
{
  GtkAlignment *align = GTK_ALIGNMENT (user_data);

  refresh_alignment(align, orientation, offset);
}

static void
orient_changed(AwnApplet *applet, AwnOrientation orient, gpointer user_data)
{
  TrayApplet *tray_applet = user_data;
  GtkAlignment *align = GTK_ALIGNMENT (tray_applet->align);

  orientation = orient;
  refresh_alignment(align, orient, awn_applet_get_offset(applet));
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

  icon_size = size > 5 ? (size / 2) - 2 : 1;

  // foreach child call set_size_request
  gtk_container_foreach (GTK_CONTAINER (table), resize_icon, NULL);
}

static gboolean
schedule_redraw(gpointer user_data)
{
  GtkWidget *applet = GTK_WIDGET (user_data);
  gtk_widget_queue_draw (applet);

  return FALSE;
}

static gboolean
applet_configured(GtkWidget *applet, GdkEventConfigure *event, TrayApplet *app)
{
  g_idle_add (schedule_redraw, applet);

  return FALSE;
}

AwnApplet*
awn_applet_factory_initp ( gchar* uid, gint orient, gint offset, gint size )
{
  AwnApplet *applet = awn_applet_new( uid, orient, offset, size );
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

  orientation = orient;
  icon_size = size > 5 ? (size / 2) - 2 : 1;
  //gtk_widget_set_size_request (GTK_WIDGET (applet), -1, height* 2 );

  table = gtk_table_new (1, 1, FALSE);
  app->table = table;
  gtk_table_set_col_spacings (GTK_TABLE (table), 1);
  gtk_table_set_row_spacings (GTK_TABLE (table), 1);

  eb = gtk_event_box_new ();
  gtk_event_box_set_visible_window (GTK_EVENT_BOX (eb), TRUE);
  
  align = gtk_alignment_new (0, 1, 1, 0);
  app->align = align;

  refresh_alignment (GTK_ALIGNMENT (align), orient, offset);
  
  gtk_container_add (GTK_CONTAINER (applet), align);
  gtk_container_add (GTK_CONTAINER (align), eb);
  if (gdk_screen_get_rgba_colormap (screen) != NULL)
  {
    gtk_widget_set_colormap (eb, gdk_screen_get_rgba_colormap (screen));
  }
  gtk_container_add (GTK_CONTAINER (eb), table);

  g_signal_connect (applet, "configure-event",
                    G_CALLBACK (applet_configured), app);
  g_signal_connect(applet, "expose-event",
                   G_CALLBACK (applet_expose), app);
  g_signal_connect(applet, "size-changed",
                   G_CALLBACK (size_changed), table);
  g_signal_connect(applet, "orientation-changed",
                   G_CALLBACK (orient_changed), app);
  g_signal_connect(applet, "offset-changed",
                   G_CALLBACK (offset_changed), align);
  g_signal_connect(eb, "expose-event",
                   G_CALLBACK (on_eb_expose), NULL);

  return applet;
}
