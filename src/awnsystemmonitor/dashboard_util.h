/*
 * Copyright (c) 2007 Rodney Cryderman <rcryderman@gmail.com>
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


#ifndef DASHBOARD_UTIL_H_
#define DASHBOARD_UTIL_H_

#include <libawn/awn-applet.h>
#include <libawn/awn-cairo-utils.h>
//#include <libawn/awn-title.h>
#include <libawn/awn-tooltip.h>
#include <stdlib.h>

#include <gconf/gconf-client.h>
#define NDEBUG
enum { DASHBOARD_FONT_TINY, DASHBOARD_FONT_SMALL, DASHBOARD_FONT_MEDIUM, DASHBOARD_FONT_LARGE };


typedef struct
{
  float red;
  float green;
  float blue;
}rgb_colour;

typedef struct
{
  float red;
  float green;
  float blue;
  float alpha;
}rgba_colour;

typedef struct
{
  GdkPixmap *pixmap;
  cairo_t *cr;
  GdkColormap* cmap;

}dashboard_cairo_widget;

void draw_pie_graph(cairo_t *cr, double x, double y, double radius, double start, double * values, AwnColor * colours, int numel);

void pick_awn_color(AwnColor * awncolour, const char *mess, void * arb_data, void (*notify_color_change)(void *));

void set_dashboard_gconf(GConfClient* p);
GConfClient* get_dashboard_gconf(void);

void set_fg_rbg(GdkColor *);
void set_bg_rbg(GdkColor *);

void get_fg_rgb_colour(rgb_colour *);
void get_fg_rgba_colour(rgba_colour *);
void get_bg_rgb_colour(rgb_colour *);
void get_bg_rgba_colour(rgba_colour *);

void use_bg_rgb_colour(cairo_t * cr);
void use_bg_rgba_colour(cairo_t * cr);
void use_fg_rgb_colour(cairo_t * cr);
void use_fg_rgba_colour(cairo_t * cr);

GtkWidget * get_cairo_widget(dashboard_cairo_widget *, int width, int height);

void del_cairo_widget(dashboard_cairo_widget * d);

float dashboard_get_font_size(int size);

char * dashboard_cairo_colour_to_string(AwnColor * colour);

GtkWidget * dashboard_build_clickable_menu_item(GtkWidget * menu, GCallback fn, char * mess, void *data);
GtkWidget * dashboard_build_clickable_check_menu_item(GtkWidget * menu, GCallback fn, char * mess, void *data, gboolean state);

void enable_suppress_hide_main(void);
void disable_suppress_hide_main(void);
gboolean get_hide_main(void);

gboolean toggle_boolean_menu(GtkWidget *widget, GdkEventButton *event, gboolean *p);

void quick_message(gchar *message, GtkWidget * mainwin);

/*void set_tiles_x(int x);
void set_tiles_y(int y);
int get_tiles_x(void);
int get_tiles_y(void);
float get_tile_size_x(void);
float get_tile_size_y(void);
*/


#endif


