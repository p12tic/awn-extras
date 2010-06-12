/*
 * Copyright (c) 2010 Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
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
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
*/

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <gtk/gtk.h>
#include <glib/gi18n-lib.h>
#include <libawn/libawn.h>
#include <libindicator/indicator-object.h>

typedef struct _IndicatorApplet IndicatorApplet;
struct _IndicatorApplet {
  AwnApplet *applet;
  GtkWidget *da;
  GtkWidget *awn_menu;

  IndicatorObject *io;

  GList *images;
  GList *menus;

  gint num;
  gint popup_num;
  gint last_num;
  gint dx;
  gint dy;
};


void
show_about(GtkMenuItem *item, gpointer user_data)
{
  const gchar *license = "This program is free software; you can redistribute \
it and/or modify it under the terms of the GNU General Public License as \
published by the Free Software Foundation; either version 2 of the License, \
or (at your option) any later version.\n\nThis program is distributed in the \
hope that it will be useful, but WITHOUT ANY WARRANTY; without even the \
implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. \
See the GNU General Public License for more details.\n\nYou should have \
received a copy of the GNU General Public License along with this program; \
if not, write to the Free Software Foundation, Inc., 51 Franklin St, Fifth \
Floor, Boston, MA 02110-1301  USA.";
  const gchar *authors[] = {"Sharkbaitbobby <sharkbaitbobby+awn@gmail.com>",
                            NULL};

  GtkWidget *about = gtk_about_dialog_new();

  gtk_about_dialog_set_program_name(GTK_ABOUT_DIALOG(about), "Indicator Applet");
  gtk_about_dialog_set_version(GTK_ABOUT_DIALOG(about), VERSION);
  gtk_about_dialog_set_comments(GTK_ABOUT_DIALOG(about),
                                _("An applet to hold all of the system indicators"));
  gtk_about_dialog_set_copyright(GTK_ABOUT_DIALOG(about),
                                 "Copyright \xc2\xa9 2010 Sharkbaitbobby");
  gtk_about_dialog_set_logo_icon_name(GTK_ABOUT_DIALOG(about), "indicator-applet");
  gtk_about_dialog_set_license(GTK_ABOUT_DIALOG(about), license);
  gtk_about_dialog_set_wrap_license(GTK_ABOUT_DIALOG(about), TRUE);
  gtk_about_dialog_set_authors(GTK_ABOUT_DIALOG(about), authors);
  gtk_about_dialog_set_website(GTK_ABOUT_DIALOG(about),
                               "http://wiki.awn-project.org/Indicator_Applet");
  gtk_about_dialog_set_website_label(GTK_ABOUT_DIALOG(about),
                                     "wiki.awn-project.org");

  gtk_window_set_icon_name(GTK_WINDOW(about), "indicator-applet");

  gtk_dialog_run(GTK_DIALOG(about));
  gtk_widget_destroy(about);
}

static void
resize_da(IndicatorApplet *iapplet)
{
  gint size = awn_applet_get_size(iapplet->applet);
  GtkPositionType pos = awn_applet_get_pos_type(iapplet->applet);
  gint pb_size = 22;
  if (size < 40)
  {
    pb_size = 0.55 * size;
  }

  if (pos == GTK_POS_TOP || pos == GTK_POS_BOTTOM)
  {
    gtk_widget_set_size_request(iapplet->da,
      ((int)(iapplet->num / 2.0) + iapplet->num % 2) * pb_size, -1);
  }
  else
  {
    gtk_widget_set_size_request(iapplet->da, -1,
      ((int)(iapplet->num / 2.0) + iapplet->num % 2) * pb_size);
  }

  gtk_widget_queue_draw(iapplet->da);
}

static gboolean
determine_position(IndicatorApplet *iapplet, gint x, gint y)
{
  AwnApplet *applet = iapplet->applet;
  GtkPositionType pos = awn_applet_get_pos_type(applet);
  gint size = awn_applet_get_size(applet);
  gint offset = awn_applet_get_offset(applet);
  gint width = iapplet->da->allocation.width;
  gint height = iapplet->da->allocation.height;

  gint pb_size = 22;
  if (size < 40)
  {
    pb_size = 0.55 * size;
  }

  gint col = -1, row = -1, num = -1, dx = -1, dy = -1;

  switch (pos)
  {
    case GTK_POS_BOTTOM:
      if (y > height - offset - pb_size * 2 && y < height - offset - pb_size)
      {
        // Top row
        row = 1;
        dy = y - height + offset + pb_size * 2;
      }
      else if (y > height - offset - pb_size && y < height - offset)
      {
        // Bottom row
        row = 0;
        dy = y - height + offset + pb_size;
      }

      col = (gint)(x / pb_size);
      dx = x - col * pb_size;
      num = col * 2 + row;
      break;

    case GTK_POS_TOP:
      if (y > offset && y < offset + pb_size)
      {
        // Top row
        row = 0;
        dy = y - offset;
      }
      else if (y > offset + pb_size && y < offset + pb_size * 2)
      {
        // Bottom row
        row = 1;
        dy = y - offset - pb_size; 
      }

      col = (gint)(x / pb_size);
      dx = x - col * pb_size;
      num = col * 2 + row;
      break;

    case GTK_POS_LEFT:
      if (x > offset && x < offset + pb_size)
      {
        // Left column
        col = 0;
        dx = x - offset;
      }
      else if (x > offset + pb_size && x < offset + pb_size * 2)
      {
        // Right column
        col = 1;
        dx = x - offset - pb_size;
      }

      row = (gint)(y / pb_size);
      dy = y - row * pb_size;
      num = row * 2 + col;
      break;

    default:
      if (x < width - offset && x > width - offset - pb_size)
      {
        // Right column
        col = 0;
        dx = x - width + offset + pb_size;
      }
      else if (x < width - offset - pb_size && x > width - offset - pb_size * 2)
      {
        // Left column
        col = 1;
        dx = x - width + offset + pb_size * 2;
      }

      row = (gint)(y / pb_size);
      dy = y - row * pb_size;
      num = row * 2 + col;
      break;
  }

  if (row == -1 || col == -1 || num == -1 || num >= g_list_length(iapplet->menus))
  {
    return FALSE;
  }

  iapplet->popup_num = num;
  iapplet->dx = dx;
  iapplet->dy = dy;

  return TRUE;
}

static void
expose_event(GtkWidget *da, GdkEventExpose *event, IndicatorApplet *iapplet)
{
  AwnApplet *applet = AWN_APPLET(iapplet->applet);

  cairo_t *cr = gdk_cairo_create(da->window);

  cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
  cairo_set_source_rgba(cr, 0.0, 0.0, 0.0, 0.0);
  cairo_paint(cr);

  cairo_set_operator(cr, CAIRO_OPERATOR_OVER);

  GtkPositionType pos = awn_applet_get_pos_type(applet);
  gint offset = awn_applet_get_offset(applet);
  gint size = awn_applet_get_size(applet);
  gint w = da->allocation.width;
  gint h = da->allocation.height;
  gfloat x = 0.0, y = 0.0;
  gint pb_size = 22;

  if (size < 40)
  {
    pb_size = 0.55 * size;
  }

  GdkPixbuf *pb;

  gint i;
  for (i = 0; i < g_list_length(iapplet->images); i++)
  {
    cairo_save(cr);

    switch (pos)
    {
      case GTK_POS_BOTTOM:
        x = (i - i % 2) * pb_size / 2;
        y = h - pb_size * (1 + i % 2) - offset;
        break;

      case GTK_POS_TOP:
        x = (i - i % 2) * pb_size / 2;
        y = pb_size * (i % 2) + offset;
        break;

      case GTK_POS_LEFT:
        x = pb_size * (i % 2) + offset;
        y = (i - i % 2) * pb_size / 2;
        break;

      default:
        x = w - pb_size * (1 + i % 2) - offset;
        y = (i - i % 2) * pb_size / 2;
        break;
    }

    cairo_rectangle(cr, x, y, pb_size, pb_size);
    cairo_clip(cr);
    cairo_translate(cr, x, y);
    pb = gtk_image_get_pixbuf(GTK_IMAGE(g_list_nth_data(iapplet->images, i)));

    if (size < 40)
    {
      pb = gdk_pixbuf_scale_simple(pb, pb_size, pb_size, GDK_INTERP_BILINEAR);
    }

    gdk_cairo_set_source_pixbuf(cr, pb, 0.0, 0.0);
    cairo_paint(cr);

    cairo_restore(cr);

    if (size < 40)
    {
      g_object_unref(pb);
    }
  }
}

static void
menu_position(GtkMenu *menu, gint *x, gint *y, gboolean *move, IndicatorApplet *iapplet)
{
  AwnApplet *applet = AWN_APPLET(iapplet->applet);
  GtkPositionType pos = awn_applet_get_pos_type(applet);
  gint size = awn_applet_get_size(applet);
  gint offset = awn_applet_get_offset(applet);
  gint mwidth = GTK_WIDGET(menu)->requisition.width;
  gint mheight = GTK_WIDGET(menu)->requisition.height;

  gint pb_size = 22;
  if (size < 40)
  {
    pb_size = 0.55 * size;
  }

  switch (pos)
  {
    case GTK_POS_BOTTOM:
      *x -= iapplet->dx;
      *y -= iapplet->dy + mheight;
      break;
    case GTK_POS_TOP:
      *x -= iapplet->dx;
      *y += pb_size - iapplet->dy;
      break;
    case GTK_POS_LEFT:
      *x += pb_size - iapplet->dx;
      *y -= iapplet->dy;
      break;
    default:
      *x -= iapplet->dx + mwidth;
      *y -= iapplet->dy;
      break;
  }

  *move = TRUE;
}

static gboolean
button_press(GtkWidget *widget, GdkEventButton *event, IndicatorApplet *iapplet)
{
  AwnApplet *applet = AWN_APPLET(iapplet->applet);
  if (event->button == 3)
  {
    if (!iapplet->awn_menu)
    {
      iapplet->awn_menu = awn_applet_create_default_menu(applet);

      GtkWidget *about_item = gtk_image_menu_item_new_from_stock(GTK_STOCK_ABOUT, NULL);
      g_signal_connect(G_OBJECT(about_item), "activate", G_CALLBACK(show_about), NULL);

      gtk_menu_shell_append(GTK_MENU_SHELL(iapplet->awn_menu), GTK_WIDGET(about_item));

      gtk_widget_show_all(iapplet->awn_menu);
    }
    gtk_menu_popup(GTK_MENU(iapplet->awn_menu), NULL, NULL, NULL, NULL,
                   event->button, event->time);

    return FALSE;
  }

  if (!determine_position(iapplet, (gint)event->x, (gint)event->y))
  {
    return FALSE;
  }

  gtk_menu_popup(GTK_MENU(g_list_nth_data(iapplet->menus, iapplet->popup_num)), NULL, NULL,
    (GtkMenuPositionFunc)menu_position, (gpointer)iapplet, event->button, event->time);

  return FALSE;
}

static gboolean
pixbuf_changed(GObject *image, GParamSpec *spec, IndicatorApplet *iapplet)
{
  gtk_widget_queue_draw(iapplet->da);

  return FALSE;
}

static void
entry_added(IndicatorObject *io, IndicatorObjectEntry *entry, IndicatorApplet *iapplet)
{
  if (entry->image == NULL || entry->menu == NULL)
  {
    /* If either of these is NULL, there will likely be problems when
     * the entry is removed */
    return;
  }

  g_object_set_data(G_OBJECT(entry->image), "indicator", io);
  iapplet->images = g_list_append(iapplet->images, entry->image);
  iapplet->menus = g_list_append(iapplet->menus, entry->menu);
  iapplet->num++;

  gint handler = g_signal_connect(G_OBJECT(entry->image), "notify::pixbuf",
                                  G_CALLBACK(pixbuf_changed), (gpointer)iapplet);
  g_object_set_data(G_OBJECT(entry->image), "pixbufhandler", (gpointer)handler);

  gtk_widget_hide(GTK_WIDGET(entry->menu));

  resize_da(iapplet);

  return;
}

static void 
entry_removed(IndicatorObject *io, IndicatorObjectEntry *entry, IndicatorApplet *iapplet)
{
  iapplet->images = g_list_remove(iapplet->images, entry->image);
  iapplet->menus = g_list_remove(iapplet->menus, entry->menu);
  iapplet->num--;

  gint handler = (gint)g_object_get_data(G_OBJECT(entry->image), "pixbufhandler");

  if (g_signal_handler_is_connected(G_OBJECT(entry->image), handler))
  {
    g_signal_handler_disconnect(G_OBJECT(entry->image), handler);
  }

  resize_da(iapplet);
}

static gboolean
size_changed(AwnApplet *applet, gint size, IndicatorApplet *iapplet)
{
  resize_da(iapplet);

  return FALSE;
}

static gboolean
position_changed(AwnApplet *applet, GtkPositionType pos, IndicatorApplet *iapplet)
{
  resize_da(iapplet);

  return FALSE;
}

static gboolean
scroll(GtkWidget *da, GdkEventScroll *event, IndicatorApplet *iapplet)
{
  if (!determine_position(iapplet, (gint)event->x, (gint)event->y))
  {
    return FALSE;
  }

  GtkWidget *image = g_list_nth_data(iapplet->images, iapplet->popup_num);
  IndicatorObject *io = g_object_get_data(G_OBJECT(image), "indicator");
  g_signal_emit_by_name(io, "scroll", 1, event->direction);

  return FALSE;
}

static gboolean
load_module(const gchar * name, IndicatorApplet *iapplet)
{
  g_return_val_if_fail(name != NULL, FALSE);

  if (!g_str_has_suffix(name, G_MODULE_SUFFIX))
  {
    return FALSE;
  }

  gchar *fullpath = g_build_filename(INDICATOR_DIR, name, NULL);
  IndicatorObject *io = iapplet->io = indicator_object_new_from_file(fullpath);
  g_free(fullpath);

  g_signal_connect(G_OBJECT(io), INDICATOR_OBJECT_SIGNAL_ENTRY_ADDED,
    G_CALLBACK(entry_added), iapplet);
  g_signal_connect(G_OBJECT(io), INDICATOR_OBJECT_SIGNAL_ENTRY_REMOVED,
    G_CALLBACK(entry_removed), iapplet);

  GList *entries = indicator_object_get_entries(io);
  GList *entry = NULL;

  for (entry = entries; entry != NULL; entry = g_list_next(entry))
  {
    entry_added(io, (IndicatorObjectEntry*)entry->data, iapplet);
  }

  g_list_free(entries);

  return TRUE;
}

AwnApplet*
awn_applet_factory_initp(const gchar *name, const gchar *uid, gint panel_id)
{
  AwnApplet *applet = awn_applet_new(name, uid, panel_id);
  GtkWidget *da = gtk_drawing_area_new();
  gtk_widget_add_events(da, GDK_BUTTON_PRESS_MASK);

  IndicatorApplet* iapplet = g_new0(IndicatorApplet, 1);
  iapplet->da = da;
  iapplet->num = 0;
  iapplet->applet = applet;
  iapplet->images = NULL;
  iapplet->menus = NULL;
  iapplet->popup_num = -1;
  iapplet->last_num = -1;

  g_signal_connect(G_OBJECT(applet), "position-changed",
                   G_CALLBACK(position_changed), (gpointer)iapplet);
  g_signal_connect(G_OBJECT(applet), "size-changed",
                   G_CALLBACK(size_changed), (gpointer)iapplet);

  g_signal_connect(G_OBJECT(da), "button-press-event",
                   G_CALLBACK(button_press), (gpointer)iapplet);
  g_signal_connect(G_OBJECT(da), "expose-event",
                   G_CALLBACK(expose_event), (gpointer)iapplet);
  g_signal_connect(G_OBJECT(da), "scroll-event",
                   G_CALLBACK(scroll), (gpointer)iapplet);

  /* Code (mostly) from gnome-panel's indicator-applet-0.3.6/src/applet-main.c */
  if (g_file_test(INDICATOR_DIR, (G_FILE_TEST_EXISTS | G_FILE_TEST_IS_DIR)))
  {
    GDir *dir = g_dir_open(INDICATOR_DIR, 0, NULL);

    const gchar *name;
    while ((name = g_dir_read_name(dir)) != NULL)
    {
      if (!g_strcmp0(name, "libsession.so"))
      {
        continue;
      }
      if (!g_strcmp0(name, "libme.so"))
      {
        continue;
      }
      load_module(name, iapplet);
    }
    g_dir_close (dir);
  }
  /* End... */

  gtk_container_add(GTK_CONTAINER(applet), da);

  gtk_widget_show_all(da);

  GtkPositionType pos = awn_applet_get_pos_type(applet);
  if (pos == GTK_POS_TOP || pos == GTK_POS_BOTTOM)
  {
    gtk_widget_set_size_request(da, 1, -1);
  }
  else
  {
    gtk_widget_set_size_request(da, -1, 1);
  }

  return applet;
}
