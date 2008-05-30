/*
 * Copyright (c) 2007 Rodney Cryderman <rcryderman@gmail.com>

 * Parts Copyright (C) 2004, 2005 Jody Goldberg (jody@gnome.org)
 *       ->cairo -> pixbuf conversion function
 *
 *
 * Original code from abiword (http://www.abisource.com/)  go-image.c
 * Function name:  static void pixbuf_to_cairo (GOImage *image);
 * Copyright (C) 2004, 2005 Jody Goldberg (jody@gnome.org)
 *   void surface_2_pixbuf( GdkPixbuf * pixbuf, cairo_surface_t * surface)
 *
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of version 2 of the GNU General Public
 * License as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301
 * USA
 */


#include <gtk/gtk.h>
#include <gdk/gdk.h>
#include <glib.h>
#include <stdlib.h>
#include <math.h>
#include "gconf-config.h"
//#undef NDEBUG
#include <assert.h>

#include "dashboard_util.h"

typedef struct
{
  void (*notify_color_change)(void *);
  void * arb_data;
  AwnColor *colour;
  GtkColorSelection *colorsel;

}Colour_changer_info;

static rgba_colour g_fg;
static rgba_colour g_bg;
static GConfClient* g_gconf_client = NULL;
static gboolean suppress_hide = FALSE;

static void  _colour_change(GtkColorSelection *colorselection, gpointer p);
static gboolean _cancel_colour_change(GtkWidget *widget, GdkEventButton *event, gpointer *p);


void draw_pie_graph(cairo_t *cr, double x, double y, double radius, double start, double * values, AwnColor * colours, int numel)
{
  int i;
  double end;
  cairo_set_line_width(cr, 1);
#if 0
  cairo_set_source_rgba(cr, 1, 0.2, 0.2, 0.6);
  cairo_move_to(cr, x, y);
  cairo_arc(cr, x, y, radius, start, 2*M_PI*((100 - 90.0) / 100));
  cairo_line_to(cr, x, y);
  cairo_close_path(cr);
// cairo_stroke (cr);

  cairo_fill(cr);
#endif

  for (i = 0;i < numel;i++)
  {
    cairo_set_source_rgba(cr, colours[i].red, colours[i].green, colours[i].blue, colours[i].alpha);
    cairo_move_to(cr, x, y);
    end = start + 2 * M_PI * (values[i] / 100);
    cairo_arc(cr, x, y, radius, start, end);
    start = end;
    cairo_line_to(cr, x, y);
    cairo_close_path(cr);
    cairo_fill(cr);
  }

}


/* Function to open a dialog box displaying the message provided.
straight from http://library.gnome.org/devel/gtk/2.11/GtkDialog.html
*/
void quick_message(gchar *message, GtkWidget * mainwin)
{

  GtkWidget *dialog, *label;

  /* Create the widgets */

  dialog = gtk_dialog_new_with_buttons("Awn System Monitor Message",
                                       mainwin,
                                       GTK_DIALOG_DESTROY_WITH_PARENT,
                                       GTK_STOCK_OK,
                                       GTK_RESPONSE_NONE,
                                       NULL);
  label = gtk_label_new(message);

  /* Ensure that the dialog box is destroyed when the user responds. */

  g_signal_connect_swapped(dialog,
                           "response",
                           G_CALLBACK(gtk_widget_destroy),
                           dialog);

  /* Add the label, and show everything we've added to the dialog. */

  gtk_container_add(GTK_CONTAINER(GTK_DIALOG(dialog)->vbox),
                    label);
  gtk_widget_show_all(dialog);
}

gboolean toggle_boolean_menu(GtkWidget *widget, GdkEventButton *event, gboolean *val)
{
  *val = !(*val);
}

void enable_suppress_hide_main(void)
{
  suppress_hide = TRUE;
}

void disable_suppress_hide_main(void)
{
  suppress_hide = FALSE;
}


gboolean get_suppress_hide_main(void)
{
  return suppress_hide;
}


GtkWidget * dashboard_build_clickable_menu_item(GtkWidget * menu, GCallback fn, char * mess, void *data)
{
  GtkWidget * menu_items;
  menu_items = gtk_menu_item_new_with_label(mess);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menu_items);
  g_signal_connect(G_OBJECT(menu_items),
                   "button-press-event",
                   G_CALLBACK(fn),
                   data
                  );
  gtk_widget_show(menu_items);
  return menu_items;
}

GtkWidget * dashboard_build_clickable_check_menu_item(GtkWidget * menu, GCallback fn, char * mess, void *data, gboolean state)
{
  GtkWidget * menu_items;
  menu_items = gtk_check_menu_item_new_with_label(mess);
  gtk_menu_shell_append(GTK_MENU_SHELL(menu), menu_items);
  g_signal_connect(G_OBJECT(menu_items),
                   "button-press-event",
                   G_CALLBACK(fn),
                   data
                  );
  gtk_check_menu_item_set_active(menu_items, state);
  gtk_widget_show(menu_items);
  return menu_items;
}

char * dashboard_cairo_colour_to_string(AwnColor * colour)
{
  char * str = malloc(128);
  char * tmp = malloc(32);

  snprintf(tmp, 32, "%04x", (unsigned int) round((colour->red*255)));
  strcpy(str, tmp + 2);
  snprintf(tmp, 32, "%04x", (unsigned int) round((colour->green*255)));
  strcat(str, tmp + 2);
  snprintf(tmp, 32, "%04x", (unsigned int) round((colour->blue*255)));
  strcat(str, tmp + 2);
  snprintf(tmp, 32, "%04x", (unsigned int) round((colour->alpha*255)));
  strcat(str, tmp + 2);
  free(tmp);
  return str;
}


void pick_awn_color(AwnColor * awncolour, const char *mess, void * arb_data, void (*notify_color_change)(void *))
{
  GtkColorSelectionDialog* dialog;
  GdkColor c;
  Colour_changer_info colour_change_data;
  enable_suppress_hide_main();
  dialog = gtk_color_selection_dialog_new(mess);
  gtk_color_selection_set_has_opacity_control(dialog->colorsel, TRUE);

  gtk_color_selection_set_current_alpha(dialog->colorsel,
                                        65535*awncolour->alpha);
  c.red = 65535 * awncolour->red;
  c.blue = 65535 * awncolour->blue;
  c.green = 65535 * awncolour->green;
  gtk_color_selection_set_current_color(dialog->colorsel, &c);
  colour_change_data.colour = awncolour;
  colour_change_data.arb_data = arb_data;
  colour_change_data.notify_color_change = notify_color_change;
  colour_change_data.colorsel = dialog->colorsel;

  g_signal_connect(G_OBJECT(dialog->colorsel),
                   "color-changed",
                   G_CALLBACK(_colour_change),
                   &colour_change_data
                  );
  g_signal_connect(G_OBJECT(dialog->cancel_button),
                   "button-press-event",
                   G_CALLBACK(_cancel_colour_change),
                   &colour_change_data
                  );

  gtk_dialog_run(GTK_DIALOG(dialog));
  enable_suppress_hide_main();
  gtk_widget_destroy(dialog);
  enable_suppress_hide_main();
}

static gboolean _cancel_colour_change(GtkWidget *widget, GdkEventButton *event, gpointer *p)
{
  Colour_changer_info * data = p;
  GdkColor c;
  void (*fn)(void *);

  fn = data->notify_color_change;
  data->colour->alpha = gtk_color_selection_get_previous_alpha(data->colorsel) / 65535.0;
  gtk_color_selection_get_previous_color(data->colorsel, &c);
  data->colour->red = c.red / 65535.0;
  data->colour->green = c.green / 65535.0;
  data->colour->blue = c.blue / 65535.0;

  if (fn)
    fn(data->arb_data);

  return FALSE;
}

static void  _colour_change(GtkColorSelection *colorselection, gpointer p)
{
  Colour_changer_info * data = p;
  GdkColor color;
  void (*fn)(void *);

  fn = data->notify_color_change;
  gtk_color_selection_get_current_color(colorselection, &color);
  data->colour->red = color.red / 65535.0;
  data->colour->green = color.green / 65535.0;
  data->colour->blue = color.blue / 65535.0;
  data->colour->alpha = gtk_color_selection_get_current_alpha(colorselection) / 65535.0;

  if (fn)
    fn(data->arb_data);

  enable_suppress_hide_main();
}

void set_dashboard_gconf(GConfClient* p)
{
  assert(p);
  g_gconf_client = p;
}

GConfClient* get_dashboard_gconf(void)
{
  assert(g_gconf_client);
  return g_gconf_client;
}


void set_fg_rbg(GdkColor *d)
{
  g_fg.red = ((float)(d->red)) / 65535.0 ;
  g_fg.blue = ((float)(d->blue)) / 65535.0;
  g_fg.green = ((float)(d->green)) / 65535.0;
}


void set_bg_rbg(GdkColor *d)
{
  g_bg.red = ((float)(d->red)) / 65535.0 ;
  g_bg.blue = ((float)(d->blue)) / 65535.0;
  g_bg.green = ((float)(d->green)) / 65535.0;
}

void get_fg_rgb_colour(rgb_colour *d)
{
  d->red = g_fg.red;
  d->green = g_fg.green;
  d->blue = g_fg.blue;

}


void get_fg_rgba_colour(rgba_colour *d)
{
  d->red = g_fg.red;
  d->green = g_fg.green;
  d->blue = g_fg.blue;
  d->alpha = 0.9;
}

void get_bg_rgb_colour(rgb_colour *d)
{
  d->red = g_bg.red;
  d->green = g_bg.green;
  d->blue = g_bg.blue;

}

void get_bg_rgba_colour(rgba_colour *d)
{
  d->red = g_bg.red;
  d->green = g_bg.green;
  d->blue = g_bg.blue;
  d->alpha = 0.90;
}


GtkWidget * get_cairo_widget(dashboard_cairo_widget * d, int width, int height)
{

  GtkWidget * widget;
  GdkScreen* pScreen;

  d->pixmap = gdk_pixmap_new(NULL, width, height, 32);       /*FIXME*/
  widget = gtk_image_new_from_pixmap(d->pixmap, NULL);
  pScreen = gtk_widget_get_screen(widget);
  d->cmap = gdk_screen_get_rgba_colormap(pScreen);

  if (!d->cmap)
    d->cmap = gdk_screen_get_rgb_colormap(pScreen);

  gdk_drawable_set_colormap(d->pixmap, d->cmap);

  d->cr = gdk_cairo_create(d->pixmap);

  rgb_colour bg;

  get_bg_rgb_colour(&bg);

  cairo_set_source_rgb(d->cr, bg.red, bg.green, bg.blue);

  cairo_set_operator(d->cr, CAIRO_OPERATOR_SOURCE);

  cairo_paint(d->cr);

  return widget;
}


void del_cairo_widget(dashboard_cairo_widget * d)
{
  g_object_unref(d->pixmap);
  cairo_destroy(d->cr);
}

float dashboard_get_font_size(int size)
{
  return 6.0 + 3.0*size;
}

void use_bg_rgb_colour(cairo_t * cr)
{
  rgb_colour c;
  get_bg_rgb_colour(&c);
  cairo_set_source_rgb(cr, c.red, c.green, c.blue);

}

void use_bg_rgba_colour(cairo_t * cr)
{
  rgba_colour c;
  get_bg_rgba_colour(&c);
  cairo_set_source_rgba(cr, c.red, c.green, c.blue, c.alpha);
}

void use_fg_rgb_colour(cairo_t * cr)
{
  rgb_colour c;
  get_fg_rgb_colour(&c);
  cairo_set_source_rgb(cr, c.red, c.green, c.blue);
}

void use_fg_rgba_colour(cairo_t * cr)
{
  rgba_colour c;
  get_fg_rgba_colour(&c);
  cairo_set_source_rgba(cr, c.red, c.green, c.blue, c.alpha);
}
