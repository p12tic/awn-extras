/*
 * Copyright (C) 2007, 2008 Rodney Cryderman <rcryderman@gmail.com>
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


#ifndef __CAIRO_MENU_CONFIG_
#define __CAIRO_MENU_CONFIG_

#include <libdesktop-agnostic/desktop-agnostic.h>

#define CONF_NORMAL_BG "bg_normal_colour"
#define CONF_NORMAL_FG "text_normal_colour"
#define CONF_HOVER_BG "bg_hover_colour"
#define CONF_HOVER_FG "text_hover_colour"

#define CONF_TEXT_SIZE "text_size"

#define CONF_SEARCH_CMD "search_cmd"
#define CONF_SHOW_SEARCH "search_show"
#define CONF_SHOW_RUN "run_show"

#define CONF_DO_FADE "fade_in"

#define CONF_MENU_GRADIENT "menu_item_gradient_factor"
#define CONF_MENU_ITEM_TEXT_LEN "menu_item_text_len"

#define CONF_SHOW_PLACES "places_show"

#define CONF_FILEMANAGER "filemanager"
#define CONF_APPLET_ICON "applet_icon"

#define CONF_ON_BUTTON_RELEASE "activate_on_release"
#define CONF_SHOW_TOOLTIPS "show_tooltips"

#define CONF_SHOW_LOGOUT "show_logout"
#define CONF_LOGOUT "logout"

#define CONF_BORDER_COLOUR "border_colour"
#define CONF_BORDER_WIDTH "border_width"

#define CONF_HONOUR_GTK "honour_gtk"

typedef struct
{
  DesktopAgnosticColor *bg;
  DesktopAgnosticColor *fg;

}Menu_item_color;

typedef struct
{
  Menu_item_color normal;
  Menu_item_color hover;
  Menu_item_color selected;
  DesktopAgnosticColor *border_colour;
  int   border_width;
  int   text_size;
  GTree *  submenu_deps;
  gboolean show_search;
  gchar  *search_cmd;
  gboolean show_logout;
  gchar  *logout;

  gboolean show_run;
  gboolean do_fade;
  gboolean show_places;
  gchar   *filemanager;
  gchar  *applet_icon;
  int   menu_item_text_len;
  double   menu_item_gradient_factor;
  gboolean honour_gtk;
  gboolean  on_button_release;
  gboolean show_tooltips;
}Cairo_menu_config;

void read_config(void);
void show_prefs(void);
void append_to_launchers(gchar * launcher);

#endif

