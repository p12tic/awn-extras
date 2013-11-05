/*
 * Copyright (C) 2007, 2008, 2009 Rodney Cryderman <rcryderman@gmail.com>
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

/* shiny-switcher.h */

/* awn-shiny-switcher.h */

#ifndef _AWN_SHINY_SWITCHER
#define _AWN_SHINY_SWITCHER

#include <glib-object.h>
#include <time.h>
#include <glib.h>
#define WNCK_I_KNOW_THIS_IS_UNSTABLE 1
#include <libwnck/libwnck.h>
#include <gdk/gdk.h>
#include <gtk/gtk.h>
#include <gdk/gdkx.h>
#include <X11/Xlib.h>
#include <X11/extensions/Xcomposite.h>
#include <X11/extensions/Xrender.h>
#include <X11/extensions/Xfixes.h>
#include <math.h>

#include <libdesktop-agnostic/desktop-agnostic.h>
#include <libawn/libawn.h>
#include <libawn/awn-utils.h>


G_BEGIN_DECLS

enum
{
  CENTRE,
  NW,
  NE,
  SE,
  SW
};

enum
{
  IMAGE_CACHE_PIXBUF,
  IMAGE_CACHE_SURFACE
};


typedef struct
{
  gpointer data;
  gint  width;
  gint  height;
  time_t  time_stamp;
  int   img_type;
}Image_cache_item;


typedef struct
{
  GtkWidget     *min_win;
  WnckWindow    *wnck_window;
  AwnApplet     *shinyswitcher;

}Window_info;

typedef struct
{
  WnckWorkspace    *space;

  AwnApplet  *shinyswitcher;
  GtkWidget    *wallpaper_ev;
  int      mini_win_index;
  GList     *event_boxes;
}Workplace_info;


typedef struct
{
  WnckWindow    *wnck_window;
  AwnApplet   *shinyswitcher;
}Win_press_data;


#define AWN_TYPE_SHINY_SWITCHER awn_shiny_switcher_get_type()

#define AWN_SHINY_SWITCHER(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_SHINY_SWITCHER, AwnShinySwitcher))

#define AWN_SHINY_SWITCHER_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_SHINY_SWITCHER, AwnShinySwitcherClass))

#define AWN_IS_SHINY_SWITCHER(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_SHINY_SWITCHER))

#define AWN_IS_SHINY_SWITCHER_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_SHINY_SWITCHER))

#define AWN_SHINY_SWITCHER_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_SHINY_SWITCHER, AwnShinySwitcherClass))

typedef struct {
  AwnApplet parent;
} AwnShinySwitcher;

typedef struct {
  AwnAppletClass parent_class;
} AwnShinySwitcherClass;

GType awn_shiny_switcher_get_type (void);

AwnShinySwitcher* awn_shiny_switcher_new (const gchar *name, const gchar *uid,
                                          gint panel_id);

G_END_DECLS

#endif /* _AWN_SHINY_SWITCHER */


