/*
 * Copyright (C) 2007, 2008, 2009 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, orign
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

/* awn-shiny-switcher.c */

#include "shinyswitcherapplet.h"
#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

G_DEFINE_TYPE (AwnShinySwitcher, awn_shiny_switcher, AWN_TYPE_APPLET)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_SHINY_SWITCHER, AwnShinySwitcherPrivate))

typedef struct _AwnShinySwitcherPrivate AwnShinySwitcherPrivate;


struct _AwnShinySwitcherPrivate 
{

  GdkPixbuf   *icon;
  GtkWidget  *container;
  GtkWidget  **mini_wins;

  GdkPixmap  *wallpaper_active;
  GdkPixmap  *wallpaper_inactive;

  gint    height;
  gint   width;
  gint   padding;
  int    mini_work_width;
  int    mini_work_height;

  gint    rows;
  gint    cols;


  WnckScreen  *wnck_screen;
  int    wnck_token;

  double   wallpaper_alpha_active;
  double   wallpaper_alpha_inactive;
  double   applet_scale;

  int    show_icon_mode;   /* 0...no 1...on inactive workspace onlt 2...all but active win 3..all */
  int    scale_icon_mode;  /* 0...none  1...on all active ws  2...on_active_win 3...all */
  double   scale_icon_factor;
  int    scale_icon_pos;   /*0... centre  1 NW    2 NE   3 SE  4 SW */

  int    win_grab_mode;  /* 0...none 1...all (grab method may override) 2..active ws (and sticky)  3...active win */
  int    win_grab_method; /* 0...gdk */

  GTree   *ws_lookup_ev;
  GTree   *ws_changes;

  GTree   *pixbuf_cache;
  GTree   *surface_cache;

  GTree   *win_menus;

  double   win_active_icon_alpha;
  double   win_inactive_icon_alpha;

  int    active_window_on_workspace_change_method; /* 0... don't change. 1.. top of stack. */

  int    do_queue_freq;
  gint   mousewheel;

  int    cache_expiry;

  gboolean  override_composite_check;

  DesktopAgnosticColor  *applet_border_colour;
  DesktopAgnosticColor  *background_colour;

  int    applet_border_width;
  gboolean  reconfigure;
  gboolean  got_viewport;
  gboolean  show_tooltips;
  gboolean  show_right_click;

  gboolean  grab_wallpaper;
  DesktopAgnosticColor  *desktop_colour;  /* used if grab_wallpaper is FALSE; */


  GdkGC    *gdkgc;
  GdkScreen  *pScreen;
  GdkColormap  *rgb_cmap;
  GdkColormap  *rgba_cmap;
  DesktopAgnosticConfigClient *config;
  DesktopAgnosticConfigClient *dock_config;
	AwnAlignment * align;
	
	GtkPositionType orient;

  gboolean reloading;

};



// -------------------------------------------------------------------
#define CONFIG_ROWS  "rows"
#define CONFIG_COLUMNS  "columns"
#define CONFIG_WALLPAPER_ALPHA_ACTIVE  "background_alpha_active"
#define CONFIG_WALLPAPER_ALPHA_INACTIVE   "background_alpha_inactive"
#define CONFIG_APPLET_SCALE   "applet_scale"
#define CONFIG_SHOW_ICON_MODE "show_icon_mode"
#define CONFIG_SCALE_ICON_MODE "scale_icon_mode"
#define CONFIG_SCALE_ICON_FACTOR "scale_icon_factor"
#define CONFIG_WIN_GRAB_MODE "win_grab_mode"
#define CONFIG_WIN_GRAB_METHOD "win_grab_method"
#define CONFIG_WIN_ACTIVE_ICON_ALPHA "win_active_icon_alpha"
#define CONFIG_WIN_INACTIVE_ICON_ALPHA "win_inactive_icon_alpha"
#define CONFIG_MOUSEWHEEL "mousewheel"
#define CONFIG_CACHE_EXPIRY "cache_expiry"
#define CONFIG_SCALE_ICON_POSITION "scale_icon_position"
#define CONFIG_APPLET_BORDER_WIDTH "applet_border_width"
#define CONFIG_APPLET_BORDER_COLOUR "applet_border_colour"
#define CONFIG_GRAB_WALLPAPER "grab_wallpaper"
#define CONFIG_DESKTOP_COLOUR "desktop_colour"
#define CONFIG_QUEUED_RENDER_FREQ "queued_render_timer"
/* #define CONFIG_SHOW_RIGHT_CLICK "show_right_click" */

#define APPLET_NAME "shinyswitcher"

/*
 * STATIC FUNCTION DEFINITIONS
 */
static void queue_all_render(AwnShinySwitcher *shinyswitcher);

/* Events */
static gboolean _expose_event_window(GtkWidget *widget, GdkEventExpose *expose, gpointer data);
static gboolean _expose_event_outer(GtkWidget *widget, GdkEventExpose *expose, AwnShinySwitcher *shinyswitcher);
static void _offset_changed(AwnShinySwitcher *app, guint offset, AwnShinySwitcher * shinyswitcher);
static void _height_changed(AwnShinySwitcher *app, guint height, AwnShinySwitcher * shinyswitcher);
static void _orient_changed(AwnShinySwitcher *app, GtkPositionType orient, AwnShinySwitcher * shinyswitcher);

static void _workspaces_changed(WnckScreen    *screen, WnckWorkspace *space, AwnShinySwitcher * shinyswitcher);
static gboolean _changed_waited(AwnShinySwitcher *shinyswitcher);
static void _viewports_changed(WnckScreen    *screen, AwnShinySwitcher * shinyswitcher);
static void init_config(AwnShinySwitcher *shinyswitcher);
static gboolean awn_shiny_switcher_setup (AwnShinySwitcher * object);


static void 
config_get_color(DesktopAgnosticConfigClient *client, const gchar *key, DesktopAgnosticColor **color)
{
  GError *error = NULL;
  GValue value = {0,};

  desktop_agnostic_config_client_get_value(client, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, key, &value, &error);

	if (error)
	{
		g_warning("shinyswitcher: error reading config string (%s): %s", key, error->message);
		g_error_free(error);
    *color = desktop_agnostic_color_new_from_string("#000", NULL);
	}
	else
	{
		*color = (DesktopAgnosticColor*)g_value_dup_object(&value);
		g_value_unset(&value);
	}
}

#define GET_VALUE(val,default,type,conf,group,key,err)                    \
  \
  do {            \
    val=desktop_agnostic_config_client_get_##type(conf,group,key,&err);  \
    if (err)                \
    {                       \
      g_warning("Shinyswitcher: error retrieving key (%s). error = %s\n",key,err->message);   \
      g_error_free(err);   \
      err=NULL;            \
      val=default;         \
    }                       \
  }while(0)

static void 
_change_config_cb(const gchar *group, const gchar *key, const GValue *value, gpointer user_data)
{
  AwnShinySwitcher *shinyswitcher = (AwnShinySwitcher *)user_data;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  
  if (!priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
  }
}

static void 
_change_config_ws_cb(const gchar *group, const gchar *key, const GValue *value, gpointer user_data)
{
  AwnShinySwitcher *shinyswitcher = (AwnShinySwitcher *)user_data;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  
  if (!priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
  }
}

static void 
init_config(AwnShinySwitcher *shinyswitcher)
{
  GError  *error = NULL;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  
  if (!priv->config)
  {
    priv->config = awn_config_get_default_for_applet(AWN_APPLET(shinyswitcher), NULL);
    priv->dock_config = awn_config_get_default(AWN_PANEL_ID_DEFAULT, NULL);
    /*this will end up working*/
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "grab_wallpaper",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "applet_border_colour",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);

    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "applet_border_width",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "applet_scale",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "background_alpha_active",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "background_alpha_inactive",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "cache_expiry",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);

    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "columns",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_ws_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "desktop_colour",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "mousewheel",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "queued_render_timer",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "rows",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_ws_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "scale_icon_factor",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "scale_icon_mode",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "scale_icon_position",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "show_icon_mode",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "win_active_icon_alpha",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "win_grab_mode",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);
    desktop_agnostic_config_client_notify_add(priv->config,
                                 DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                 "win_inactive_icon_alpha",
                                 (DesktopAgnosticConfigNotifyFunc)_change_config_cb,
                                 shinyswitcher, NULL);


  }

  GET_VALUE(priv->rows, 2, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_ROWS, error);
  GET_VALUE(priv->cols, 3, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_COLUMNS, error);
  GET_VALUE(priv->wallpaper_alpha_active, 0.9, float, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_WALLPAPER_ALPHA_ACTIVE, error);
  GET_VALUE(priv->wallpaper_alpha_inactive, 0.6, float, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_WALLPAPER_ALPHA_INACTIVE, error);
  GET_VALUE(priv->applet_scale, 0.95, float, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_APPLET_SCALE, error);
  GET_VALUE(priv->scale_icon_mode, 2, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_SCALE_ICON_MODE, error);
  GET_VALUE(priv->scale_icon_factor, 0.8, float, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_SCALE_ICON_FACTOR, error);
  GET_VALUE(priv->show_icon_mode, 3, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_SHOW_ICON_MODE, error);
  GET_VALUE(priv->win_grab_mode, 3, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_WIN_GRAB_MODE, error);
  GET_VALUE(priv->win_grab_method, 0, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_WIN_GRAB_METHOD, error);
  GET_VALUE(priv->win_active_icon_alpha, 0.65, float, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_WIN_ACTIVE_ICON_ALPHA, error);
  GET_VALUE(priv->win_inactive_icon_alpha, 1.0, float, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_WIN_INACTIVE_ICON_ALPHA, error);
  GET_VALUE(priv->mousewheel, 1, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_MOUSEWHEEL, error);
  GET_VALUE(priv->cache_expiry, 7, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_CACHE_EXPIRY, error);
  GET_VALUE(priv->scale_icon_pos, 3, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_SCALE_ICON_POSITION, error);
  GET_VALUE(priv->applet_border_width, 1, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_APPLET_BORDER_WIDTH , error);
  GET_VALUE(priv->grab_wallpaper, TRUE, bool, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_GRAB_WALLPAPER, error);
  GET_VALUE(priv->do_queue_freq, 1000, int, priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
            CONFIG_QUEUED_RENDER_FREQ , error);
  /*  GET_VALUE(priv->show_right_click,FALSE,bool,priv->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, */
  /*            CONFIG_SHOW_RIGHT_CLICK , error); */
  priv->show_right_click = TRUE; /* let's enable by default and see if ther are issues. */
  config_get_color(priv->config, CONFIG_APPLET_BORDER_COLOUR, &priv->applet_border_colour);
  config_get_color(priv->config, CONFIG_DESKTOP_COLOUR,       &priv->desktop_colour);

  priv->active_window_on_workspace_change_method = 1;
  priv->override_composite_check = FALSE;
  priv->show_tooltips = FALSE;    /* buggy at the moment will be a config option eventually */
}

static double 
vp_vscale(AwnShinySwitcher *shinyswitcher)
{
  static double cached = 1;
  double result = cached;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  WnckWorkspace * space =  wnck_screen_get_active_workspace(priv->wnck_screen);

  if (space)
  {
    result = (double)wnck_screen_get_height(priv->wnck_screen) / (double)wnck_workspace_get_height(space);
    cached = result;
  }

  return result;
}

static double 
vp_hscale(AwnShinySwitcher *shinyswitcher)
{
  static double cached = 1;
  double result = cached;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  WnckWorkspace * space = wnck_screen_get_active_workspace(priv->wnck_screen);

  if (space)
  {
    result = (double)wnck_screen_get_width(priv->wnck_screen) / (double)wnck_workspace_get_width(space);
    cached = result;
  }

  return result;

}

static void 
calc_dimensions(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  /* FIXME this is no longer screen width/height  it's workspace */
  int wnck_ws_width = wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen));
  int wnck_ws_height = wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen));
  int wnck_scr_width = wnck_screen_get_width(priv->wnck_screen);
  int wnck_scr_height = wnck_screen_get_height(priv->wnck_screen);

  double ws_ratio, scr_ratio;

  ws_ratio = wnck_ws_width / (double)wnck_ws_height;
  scr_ratio = wnck_scr_width / (double)wnck_scr_height;

  switch (priv->orient)
  {

    case GTK_POS_BOTTOM:
    
    case GTK_POS_TOP:
      priv->mini_work_height = priv->height * priv->applet_scale / priv->rows;
      priv->mini_work_width = priv->mini_work_height * priv->applet_scale * scr_ratio *
                                       (double)wnck_ws_width / (double)wnck_scr_width * vp_vscale(shinyswitcher);
      break;

    case GTK_POS_LEFT:

    case GTK_POS_RIGHT:
      priv->mini_work_width = priv->height * priv->applet_scale / priv->cols;    
      priv->mini_work_height = priv->mini_work_width * priv->applet_scale * (1.0/scr_ratio )
                                       *(
                                         ((double)wnck_ws_height / (double)wnck_scr_height)
                                        /((double) wnck_ws_width / (double) wnck_scr_width)
                                        );
      priv->height = priv->mini_work_height * priv->rows;
      break;
  }

  priv->width = priv->mini_work_width * priv->cols;

  g_assert(priv->mini_work_height);
  g_assert(priv->mini_work_width);
  g_assert(priv->width);
}


static GdkPixmap * 
copy_pixmap(AwnShinySwitcher *shinyswitcher, GdkPixmap * src)
{
  GdkPixmap * copy;
  int  w, h;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  
  g_return_val_if_fail(src,NULL);
  gdk_drawable_get_size(src, &w, &h);
  if (!w || !h)
  {
    return NULL;
  }
  copy = gdk_pixmap_new(src, w, h, 32);   /* FIXME */
  gdk_draw_drawable(copy, priv->gdkgc, src, 0, 0, 0, 0, -1, -1);
  return copy;
}

/* grabs the wallpaper as a gdkpixmap. */
/* FIXME This needs a cleanup */
static void 
grab_wallpaper(AwnShinySwitcher *shinyswitcher)
{
  int w, h;
  GtkWidget * widget;
  static GdkPixmap* wallpaper = NULL;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  
  static gulong old_xid = -1;
  gulong wallpaper_xid = wnck_screen_get_background_pixmap(priv->wnck_screen);
  if (!wallpaper || (old_xid != wallpaper_xid))
  {
    wallpaper = gdk_pixmap_foreign_new(wallpaper_xid);
  }

  old_xid = wallpaper_xid;
  if (!wallpaper)
  {
    return;
  }

  gdk_drawable_set_colormap(wallpaper, priv->rgb_cmap);

  priv->wallpaper_inactive = gdk_pixmap_new(NULL, priv->mini_work_width * vp_hscale(shinyswitcher), priv->mini_work_height * vp_vscale(shinyswitcher), 32);   /* FIXME */
  widget = gtk_image_new_from_pixmap(priv->wallpaper_inactive, NULL);
  gtk_widget_set_app_paintable(widget, TRUE);
  gdk_drawable_set_colormap(priv->wallpaper_inactive, priv->rgba_cmap);
  cairo_t * destcr = gdk_cairo_create(priv->wallpaper_inactive);

  if (destcr)
  {
    cairo_set_operator(destcr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(destcr);
    gdk_drawable_get_size(wallpaper, &w, &h);
    cairo_scale(destcr, priv->mini_work_width / (double)w*vp_hscale(shinyswitcher), priv->mini_work_height / (double)h*vp_vscale(shinyswitcher));
    gdk_cairo_set_source_pixmap(destcr, wallpaper, 0, 0);
    cairo_set_operator(destcr, CAIRO_OPERATOR_OVER);
    cairo_paint_with_alpha(destcr, priv->wallpaper_alpha_inactive);
  }

  gtk_widget_destroy(widget);

  priv->wallpaper_active = gdk_pixmap_new(NULL, priv->mini_work_width * vp_hscale(shinyswitcher), priv->mini_work_height * vp_vscale(shinyswitcher), 32);   /* FIXME */
  widget = gtk_image_new_from_pixmap(priv->wallpaper_active, NULL);
  gtk_widget_set_app_paintable(widget, TRUE);
  gdk_drawable_set_colormap(priv->wallpaper_active, priv->rgba_cmap);
  destcr = gdk_cairo_create(priv->wallpaper_active);

  if (destcr)
  {
    cairo_set_operator(destcr, CAIRO_OPERATOR_CLEAR);
    cairo_paint(destcr);
    cairo_scale(destcr, priv->mini_work_width / (double)w*vp_hscale(shinyswitcher), priv->mini_work_height / (double)h*vp_vscale(shinyswitcher));
    gdk_cairo_set_source_pixmap(destcr, wallpaper, 0, 0);
    cairo_set_operator(destcr, CAIRO_OPERATOR_OVER);
    cairo_paint_with_alpha(destcr, priv->wallpaper_alpha_active);
    cairo_destroy(destcr);
  }

  gtk_widget_destroy(widget);
}

static void 
set_background(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  if (priv->grab_wallpaper)
  {
    grab_wallpaper(shinyswitcher);
  }
  else
  {
    cairo_t  *cr;
    GtkWidget  *widget;
    priv->wallpaper_inactive = gdk_pixmap_new(NULL, priv->mini_work_width * vp_hscale(shinyswitcher), priv->mini_work_height * vp_vscale(shinyswitcher), 32);   /* FIXME */
    gdk_drawable_set_colormap(priv->wallpaper_inactive, priv->rgba_cmap);
    widget = gtk_image_new_from_pixmap(priv->wallpaper_inactive, NULL);
    gtk_widget_set_app_paintable(widget, TRUE);
    cr = gdk_cairo_create(priv->wallpaper_inactive);

    if (cr)
    {
      cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
      cairo_paint(cr);
      cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
      awn_cairo_set_source_color(cr, priv->desktop_colour);
      cairo_paint_with_alpha(cr, priv->wallpaper_alpha_inactive);
      gtk_widget_destroy(widget);
      cairo_destroy(cr);
    }

    priv->wallpaper_active = gdk_pixmap_new(NULL, priv->mini_work_width * vp_hscale(shinyswitcher), priv->mini_work_height * vp_vscale(shinyswitcher), 32);   /* FIXME */

    gdk_drawable_set_colormap(priv->wallpaper_active, priv->rgba_cmap);
    widget = gtk_image_new_from_pixmap(priv->wallpaper_active, NULL);
    gtk_widget_set_app_paintable(widget, TRUE);
    cr = gdk_cairo_create(priv->wallpaper_active);

    if (cr)
    {
      cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
      cairo_paint(cr);
      cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
      awn_cairo_set_source_color(cr, priv->desktop_colour);
      cairo_paint_with_alpha(cr, priv->wallpaper_alpha_active);
      cairo_destroy(cr);
    }

    gtk_widget_destroy(widget);
  }
}

static gboolean
_start_applet_prefs(GtkMenuItem *menuitem, gpointer null)
{
  GError *err = NULL;
  g_spawn_command_line_async("python " APPLETSDIR G_DIR_SEPARATOR_S APPLET_NAME
                             G_DIR_SEPARATOR_S "shiny-prefs.py", &err);
  if (err)
  {
    g_warning("Failed to start shinyswitcher prefs dialog: %s\n", err->message);
    g_error_free(err);
  }

  return TRUE;
}

static gboolean 
_button_workspace(GtkWidget *widget, GdkEventButton *event, Workplace_info * ws)
{

  AwnShinySwitcher *shinyswitcher = AWN_SHINY_SWITCHER  (ws->shinyswitcher);
  static GtkWidget *menu = NULL;
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);

  if (event->button == 1)
  {
    if (priv->got_viewport)
    {
      int vp_pos_col = 1.0 / vp_hscale(shinyswitcher) * (event->x / (double)priv->mini_work_width);
      int vp_pos_row = 1.0 / vp_vscale(shinyswitcher) * (event->y / (double)priv->mini_work_height);
      wnck_screen_move_viewport(priv->wnck_screen,
                                vp_pos_col*wnck_screen_get_width(priv->wnck_screen),
                                vp_pos_row*wnck_screen_get_height(priv->wnck_screen));
    }

    wnck_workspace_activate(ws->space, event->time);
  }
  else if (event->button == 3)
  {
    if (!menu)
    {
      GtkWidget *item;
      menu = awn_applet_create_default_menu(AWN_APPLET(shinyswitcher));
      gtk_menu_set_screen(GTK_MENU(menu), NULL);
      item = gtk_image_menu_item_new_with_label("Applet Preferences");
      gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(item),
                                    gtk_image_new_from_stock(GTK_STOCK_PREFERENCES,
                                                             GTK_ICON_SIZE_MENU));
      gtk_widget_show_all(item);
      g_signal_connect(G_OBJECT(item), "activate",
                       G_CALLBACK(_start_applet_prefs), NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

      item = awn_applet_create_about_item (AWN_APPLET(shinyswitcher),
             "Copyright 2007,2008 Rodney Cryderman <rcryderman@gmail.com>",
             AWN_APPLET_LICENSE_GPLV2,
             NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);
    }

    if (menu)
    {
      gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL,
                     event->button, event->time);
    }
  }
  return FALSE;
}

static void 
_menu_selection_done(GtkMenuShell *menushell, AwnShinySwitcher *shinyswitcher)
{
  queue_all_render(shinyswitcher);
}


static gboolean  
_button_win(GtkWidget *widget, GdkEventButton *event, Win_press_data * data)
{
  WnckWindow*  wnck_win = data->wnck_window;
  GtkWidget *menu = NULL;
  GtkWidget *item = NULL;
  AwnShinySwitcher * shinyswitcher = AWN_SHINY_SWITCHER(data->shinyswitcher);
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  
  if (! WNCK_IS_WINDOW(wnck_win))
  {
    return TRUE;
  }

  if (event->button == 1)
  {
    WnckWorkspace* space = wnck_window_get_workspace(wnck_win);
    if (priv->got_viewport)
    {
      int x,y,w,h;
      int ws_x,ws_y;
      
      wnck_window_get_geometry (wnck_win, &x,&y,&w,&h);
      x = x +   wnck_workspace_get_viewport_x (space);
      y = y +   wnck_workspace_get_viewport_y (space);

      ws_x = x / wnck_screen_get_width(priv->wnck_screen);
      ws_y = y / wnck_screen_get_height(priv->wnck_screen);
      wnck_screen_move_viewport(priv->wnck_screen,
                                ws_x*wnck_screen_get_width(priv->wnck_screen),
                                ws_y*wnck_screen_get_height(priv->wnck_screen));
      
    }
    if (space)
    {
       wnck_workspace_activate(space, event->time);
    }
    wnck_window_activate(wnck_win, event->time);
    return TRUE;
  }
  else if (event->button == 3)
  {
    AwnShinySwitcher *shinyswitcher = g_tree_lookup(priv->win_menus, wnck_win);

    if (WNCK_IS_WINDOW(wnck_win) && shinyswitcher)
    {
      menu = wnck_action_menu_new(wnck_win);
      item = gtk_separator_menu_item_new();
      gtk_widget_show_all(item);
      gtk_menu_shell_prepend(GTK_MENU_SHELL(menu), item);

      item = awn_applet_create_pref_item();
      gtk_menu_shell_prepend(GTK_MENU_SHELL(menu), item);

      item = gtk_separator_menu_item_new();
      gtk_widget_show(item);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

      item = gtk_image_menu_item_new_with_label("Applet Preferences");
      gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(item),
                                    gtk_image_new_from_stock(GTK_STOCK_PREFERENCES,
                                                             GTK_ICON_SIZE_MENU));
      gtk_widget_show_all(item);
      g_signal_connect(G_OBJECT(item), "activate",
                       G_CALLBACK(_start_applet_prefs), NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

      item = awn_applet_create_about_item (AWN_APPLET(shinyswitcher),
             "Copyright 2007,2008 Rodney Cryderman <rcryderman@gmail.com>",
             AWN_APPLET_LICENSE_GPLV2,
             NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);

      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

      gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL, event->button, event->time);
      g_signal_connect(G_OBJECT(menu), "selection-done", G_CALLBACK(_menu_selection_done), shinyswitcher);
    }
    else
    {
      menu = g_tree_lookup(priv->win_menus, wnck_win);

      if (menu)
      {
        gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL, event->button, event->time);
      }
    }

    return TRUE;
  }

  return FALSE;
}


static gboolean 
_scroll_event(GtkWidget *widget, GdkEventMotion *event, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  WnckWorkspace *cur_space = wnck_screen_get_active_workspace(priv->wnck_screen);
  WnckWorkspace *new_space;

  if (cur_space)
  {
    if (event->type == GDK_SCROLL)
    {
      WnckMotionDirection direction1, direction2;

      switch (priv->mousewheel)
      {

        case 1:

        case 3:
          direction1 =  WNCK_MOTION_LEFT;
          direction2 =  WNCK_MOTION_RIGHT;
          break;

        case 2:

        case 4:

        default:
          direction1 =  WNCK_MOTION_RIGHT;
          direction2 =  WNCK_MOTION_LEFT;

      }

      if (event->state & GDK_SHIFT_MASK)
      {
        new_space = wnck_workspace_get_neighbor(cur_space, WNCK_MOTION_RIGHT);
      }
      else
      {
        new_space = wnck_workspace_get_neighbor(cur_space, WNCK_MOTION_LEFT);

      }
    }

    if (new_space)
    {
      wnck_workspace_activate(new_space, event->time); /* FIXME */
    }
  }

  return TRUE;
}

static void 
create_containers(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);
  int  num_workspaces = priv->rows * priv->cols;
  GList*  wnck_spaces;
  GList * iter;
  int  win_num;
  cairo_t  *cr;
  int   y_offset, x_offset;

  priv->mini_wins = g_malloc(sizeof(GtkWidget*) * num_workspaces);
  priv->container = gtk_fixed_new();
  awn_utils_ensure_transparent_bg (priv->container);
  gtk_widget_set_app_paintable(priv->container, TRUE);

  GdkPixmap *border = gdk_pixmap_new(NULL,
                                     priv->width + priv->applet_border_width * 2,
                                     (priv->height + priv->applet_border_width * 2) * priv->applet_scale ,
                                     32);   /* FIXME */
  GtkWidget *border_widget = gtk_image_new_from_pixmap(border, NULL);
  gtk_widget_set_app_paintable(border_widget, TRUE);
  gdk_drawable_set_colormap(border, priv->rgba_cmap);
  cr = gdk_cairo_create(border);
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint(cr);
  cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
  awn_cairo_set_source_color(cr, priv->applet_border_colour);

  cairo_paint(cr);
  cairo_destroy(cr);
  g_object_unref(border);

  y_offset = (priv->height - (priv->mini_work_height * priv->rows)) / 2;

  gtk_fixed_put(GTK_FIXED(priv->container), border_widget, 0, y_offset);
  gtk_widget_show(border_widget);
  y_offset = y_offset + priv->applet_border_width;
  x_offset = priv->applet_border_width;
  wnck_spaces = wnck_screen_get_workspaces(priv->wnck_screen);

  for (iter = g_list_first(wnck_spaces);iter;iter = g_list_next(iter))
  {
    GtkWidget * ev;
    Workplace_info * ws;
    win_num = wnck_workspace_get_number(iter->data);
    priv->mini_wins[win_num] = gtk_fixed_new();
    awn_utils_ensure_transparent_bg (priv->mini_wins[win_num]);
    
    gtk_widget_set_app_paintable(priv->mini_wins[win_num], TRUE);
    GdkPixmap *copy;

    if (priv->got_viewport)
    {
      int viewports_cols;
      int viewports_rows;
      viewports_cols = wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen)) /
                       wnck_screen_get_width(priv->wnck_screen) ;
      viewports_rows = wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen)) /
                       wnck_screen_get_height(priv->wnck_screen) ;
      ev = gtk_event_box_new();
      gtk_widget_set_app_paintable(ev, TRUE);

      if (iter->data == wnck_screen_get_active_workspace(priv->wnck_screen))
      {
        copy = priv->wallpaper_active;
      }
      else
      {
        copy = priv->wallpaper_inactive;
      }

      copy = copy_pixmap(shinyswitcher, copy);
      if (copy)
      {
        gtk_container_add(GTK_CONTAINER(ev), gtk_image_new_from_pixmap(copy, NULL));
        g_object_unref(copy);
      }
    }
    else
    {
      ev = gtk_event_box_new();
      gtk_widget_set_app_paintable(ev, TRUE);

      if (iter->data == wnck_screen_get_active_workspace(priv->wnck_screen))
      {
        copy = priv->wallpaper_active;
      }
      else
      {
        copy = priv->wallpaper_inactive;
      }

      copy = copy_pixmap(shinyswitcher, copy);
      if (copy)
      {
        gtk_container_add(GTK_CONTAINER(ev), gtk_image_new_from_pixmap(copy, NULL));
        g_object_unref(copy);
      }
    }

    gtk_fixed_put(GTK_FIXED(priv->mini_wins[win_num]), ev, 0, 0);

    gtk_fixed_put(GTK_FIXED(priv->container), priv->mini_wins[win_num],
                  priv->mini_work_width*wnck_workspace_get_layout_column(iter->data) + x_offset,
                  priv->mini_work_height*wnck_workspace_get_layout_row(iter->data)
                  + y_offset);
    ws = g_malloc(sizeof(Workplace_info));
    ws->shinyswitcher = AWN_APPLET(shinyswitcher);
    ws->space = iter->data;
    ws->wallpaper_ev = ev;
    ws->mini_win_index = win_num;
    ws->event_boxes = NULL;
    g_tree_insert(priv->ws_lookup_ev, iter->data, ws);
    g_signal_connect(G_OBJECT(ev), "button-press-event", G_CALLBACK(_button_workspace), ws);
    g_signal_connect(G_OBJECT(ev), "expose_event", G_CALLBACK(_expose_event_window), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->mini_wins[win_num]), "expose_event", G_CALLBACK(_expose_event_window), NULL);
  }

  awn_utils_ensure_transparent_bg (priv->container);
  gtk_container_add(GTK_CONTAINER(priv->align), priv->container);

  g_signal_connect(GTK_WIDGET(shinyswitcher), "scroll-event" , G_CALLBACK(_scroll_event), shinyswitcher);
}

static gint 
_cmp_ptrs(gconstpointer a, gconstpointer b)
{
  return a -b;
}

static void 
prepare_to_render_workspace(AwnShinySwitcher *shinyswitcher, WnckWorkspace * space)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  GdkPixmap * copy;
  Workplace_info * ws2;
  ws2 = g_tree_lookup(priv->ws_lookup_ev, space);
//  g_assert(ws2);
  if (!ws2)
  {
    return;
  }

  if (priv->got_viewport)
  {
    int viewports_cols;
    int viewports_rows;
    int i, j;
    viewports_cols = wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen)) /
                     wnck_screen_get_width(priv->wnck_screen) ;
    viewports_rows = wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen)) /
                     wnck_screen_get_height(priv->wnck_screen) ;
    copy = gdk_pixmap_new(NULL, priv->mini_work_width, priv->mini_work_height, 32);
    gdk_drawable_set_colormap(copy, priv->rgba_cmap);

    gdk_draw_rectangle(copy, priv->gdkgc, TRUE, 0, 0, priv->mini_work_width, priv->mini_work_height);
    int vp_active_x = lround (1.0 / vp_hscale(shinyswitcher) *
                      wnck_workspace_get_viewport_x(wnck_screen_get_active_workspace(priv->wnck_screen)) /
                      wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen)));
    int vp_active_y = lround (1.0 / vp_vscale(shinyswitcher) *
                      wnck_workspace_get_viewport_y(wnck_screen_get_active_workspace(priv->wnck_screen)) /
                      wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen)));

    for (i = 0;i < viewports_rows;i++)
    {
      for (j = 0;j < viewports_cols;j++)
      {
        GdkPixmap * to_copy;
        to_copy = ((i == vp_active_y) && (j == vp_active_x)) ? priv->wallpaper_active : priv->wallpaper_inactive;
        gdk_draw_drawable(copy, priv->gdkgc, to_copy, 0, 0,
                          j*priv->mini_work_width*vp_hscale(shinyswitcher),
                          i*priv->mini_work_height*vp_vscale(shinyswitcher),
                          -1, -1);
      }
    }
  }
  else
  {
    if (wnck_screen_get_active_workspace(priv->wnck_screen) == space)
    {
      copy = copy_pixmap(shinyswitcher, priv->wallpaper_active);
    }
    else
    {
      copy = copy_pixmap(shinyswitcher, priv->wallpaper_inactive);
    }
  }

  if (copy)
  {
    GtkWidget *new_pixmap;
    gtk_widget_destroy(gtk_bin_get_child(GTK_BIN(ws2->wallpaper_ev)));
    new_pixmap = gtk_image_new_from_pixmap(copy, NULL);
    gtk_widget_set_app_paintable(new_pixmap, TRUE);
    gtk_container_add(GTK_CONTAINER(ws2->wallpaper_ev), new_pixmap);
    g_object_unref(copy);
    gtk_widget_show_all(ws2->wallpaper_ev);
  }

  if (ws2->event_boxes)
  {
    GList * ev_iter;

    for (ev_iter = g_list_first(ws2->event_boxes);ev_iter;ev_iter = g_list_next(ev_iter))
    {
      gtk_widget_hide(ev_iter->data);
      gtk_widget_destroy(ev_iter->data);
    }

    g_list_free(ws2->event_boxes);

    ws2->event_boxes = NULL;
  }
}

static void 
image_cache_insert_pixbuf(GTree*  cache, gpointer key,  GdkPixbuf * pbuf)
{
  int w, h;
  Image_cache_item * leaf;
  g_assert(!g_tree_lookup(cache, pbuf));
  leaf = g_malloc(sizeof(Image_cache_item));
  h = gdk_pixbuf_get_height(pbuf);
  w = gdk_pixbuf_get_width(pbuf);
  leaf->data = pbuf;
  leaf->width = w;
  leaf->height = h;
  leaf->time_stamp = time(NULL);
  leaf->img_type = IMAGE_CACHE_PIXBUF;
  g_tree_insert(cache, key, leaf);
}

static void 
image_cache_insert_surface(GTree*  cache, gpointer key,  cairo_surface_t *surface)
{
  int w, h;
  Image_cache_item * leaf;
  g_assert(!g_tree_lookup(cache, surface));
  leaf = g_malloc(sizeof(Image_cache_item));

  h = cairo_image_surface_get_height(surface);
  w = cairo_image_surface_get_width(surface);
  leaf->data = surface;
  leaf->width = w;
  leaf->height = h;
  leaf->time_stamp = time(NULL);
  leaf->img_type = IMAGE_CACHE_SURFACE;
  g_tree_insert(cache, key, leaf);
}

static void 
image_cache_unref_data(Image_cache_item * leaf)
{
  switch (leaf->img_type)
  {

    case IMAGE_CACHE_SURFACE:
      cairo_surface_destroy(leaf->data);
      break;

    case IMAGE_CACHE_PIXBUF:

    default:
      g_assert((G_OBJECT(leaf->data))->ref_count == 1);
      g_object_unref(G_OBJECT(leaf->data));
      break;
  }
}

static gpointer 
image_cache_lookup_key_width_height(AwnShinySwitcher *shinyswitcher, GTree*  cache,
    gpointer key, gint width, gint height, gboolean allow_time_expire)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  Image_cache_item * leaf;
  leaf = g_tree_lookup(cache, key);

  if (leaf)
  {
    if ((leaf->height == height)  && (leaf->width == width))
    {
      if ((time(NULL) - priv->cache_expiry  < leaf->time_stamp) || !allow_time_expire)
      {
        return leaf->data;
      }
    }
    else
    {

    }

    /* if the leaf cached drawable is not a perfect match we get rid of it... */
    image_cache_unref_data(leaf);

    g_tree_remove(cache, key);

    g_free(leaf);
  }

  return NULL;
}

static void 
image_cache_remove(GTree*  cache, gpointer key)
{
  Image_cache_item * leaf;
  leaf = g_tree_lookup(cache, key);

  if (leaf)
  {
    image_cache_unref_data(leaf);
    g_tree_remove(cache, key);
    g_free(leaf);
  }
}

static void 
image_cache_expire(AwnShinySwitcher *shinyswitcher, GTree*  cache, gpointer key)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  Image_cache_item * leaf;
  leaf = g_tree_lookup(cache, key);

  if (leaf)
  {
    leaf->time_stamp = leaf->time_stamp - priv->cache_expiry;
  }
}

static void 
grab_window_xrender_meth(AwnShinySwitcher *shinyswitcher, cairo_t *destcr, WnckWindow *win, double scaled_x, double scaled_y,
                              double scaled_width, double scaled_height, int x, int y, int width, int height, gboolean allow_update)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  int event_base, error_base;
  gboolean  hasNamePixmap = FALSE;
  gulong    Xid = wnck_window_get_xid(win);

  Display* dpy = gdk_x11_get_default_xdisplay();

  if (XCompositeQueryExtension(dpy, &event_base, &error_base))
  {
    /* If we get here the server supports the extension */

    int major = 0, minor = 2; /* The highest version we support */
    XCompositeQueryVersion(dpy, &major, &minor);

    /* major and minor will now contain the highest version the server supports. */
    /* The protocol specifies that the returned version will never be higher */
    /* then the one requested. Version 0.2 is the first version to have the */
    /* XCompositeNameWindowPixmap() request. */

    if (major > 0 || minor >= 2)
      hasNamePixmap = TRUE;
  }

  XWindowAttributes attr;

  if (XGetWindowAttributes(dpy, Xid, &attr))
  {

    XRenderPictFormat *format = XRenderFindVisualFormat(dpy, attr.visual);
    int x                     = attr.x;
    int y                     = attr.y;

    /* Create a Render picture so we can reference the window contents. */
    /* We need to set the subwindow mode to IncludeInferiors, otherwise child widgets */
    /* in the window won't be included when we draw it, which is not what we want. */
    XRenderPictureAttributes pa;
    pa.subwindow_mode = IncludeInferiors; /* Don't clip child widgets */

    Picture picture = XRenderCreatePicture(dpy, Xid, format, CPSubwindowMode, &pa);

    /* Create a copy of the bounding region for the window */
    XserverRegion region = XFixesCreateRegionFromWindow(dpy, Xid, WindowRegionBounding);

    /* The region is relative to the screen, not the window, so we need to offset */
    /* it with the windows position */
    XFixesTranslateRegion(dpy, region, -x, -y);
    XFixesSetPictureClipRegion(dpy, picture, 0, 0, region);
    XFixesDestroyRegion(dpy, region);

    /* [Fill the destination widget/pixmap with whatever you want to use as a background here] */

    /* XRenderComposite( dpy, hasAlpha ? PictOpOver : PictOpSrc, picture, None, */
    /*  dest.x11RenderHandle(), 0, 0, 0, 0, destX, destY, width, height ); */


    printf("xrender good\n");
  }
  else
  {
    printf("xrender bad\n");
  }

}

static void 
grab_window_gdk_meth(AwnShinySwitcher *shinyswitcher, cairo_t *destcr, WnckWindow *win, double scaled_x, double scaled_y,
                          double scaled_width, double scaled_height, int x, int y, int width, int height, gboolean allow_update)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  int    w, h;
  GdkColormap  *cmap;
  /* printf("BEGIN:     grab_window_gdk_meth\n"); */

  gint    err_code;
  cairo_surface_t* cached_srfc = NULL;
  cairo_surface_t* srfc = NULL;
  cairo_t   *cr;

  if (! WNCK_IS_WINDOW(win))
  {
    goto error_out ;
  }

  cached_srfc = image_cache_lookup_key_width_height(shinyswitcher, priv->surface_cache, win, scaled_width, scaled_height, allow_update);

  /* printf("xid=%ld\n",Xid); */

  if (cached_srfc)
  {
    /*  printf("Surface cache HIT\n"); */
  }
  else if (allow_update)
  {
    /*  printf("Surface cache MISS\n"); */
    gulong    Xid = wnck_window_get_xid(win);
    gdk_error_trap_push();
    GdkPixmap * pmap = gdk_pixmap_foreign_new(Xid);

    if (!pmap)
    {
      /* ok... our window is no longer here.  we can bail safely. */
      printf("Shinyswitcher Message: window gone!.  bailing oout of grab_window_gdk_meth\n");
      goto error_out;
    }

    if (!GDK_IS_PIXMAP(pmap))
    {
      printf("Shinyswitcher Message: not a gdkpixmap!.  bailing oout of grab_window_gdk_meth\n");
      g_object_unref(pmap);
      goto error_out;
    }

    /*FIXME... suspecing that we have a race that causes occasional crash. this is to minimize chance of this happening*/

    gdk_drawable_get_size(pmap, &w, &h);

    if ((h < 5) || (w < 5))
    {
      printf("Shinyswitcher Message: pixmpap too small or non-existent.  bailing oout of grab_window_gdk_meth\n");
      g_object_unref(pmap);
      goto error_out;
    }

    g_assert(pmap);

    if (gdk_drawable_get_depth(pmap) == 32)
    {
      cmap = priv->rgba_cmap;
    }
    else if (gdk_drawable_get_depth(pmap) >= 15)
    {
      cmap = priv->rgb_cmap;
    }
    else
    {
      printf("Shinyswitcher Message: dunno what's up with the pixmaps depth.  bailing oout of grab_window_gdk_meth\n");
      g_object_unref(pmap);
      goto error_out;
    }

    gdk_drawable_set_colormap(pmap, cmap);

    /* adjusting for the fact the pixmap does not have the wm frame... */
    double cairo_scaling_y = scaled_height / (double)h;
    double cairo_scaling_x = scaled_width  / (double)w;

    srfc = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, width, height);
    cairo_t *src = cairo_create(srfc);
    cairo_set_operator(src, CAIRO_OPERATOR_SOURCE);
    gdk_cairo_set_source_pixmap(src, pmap, (width - w) / 2.0, (height - h) / 2.0);
    cairo_rectangle(src, (width - w) / 2.0, (height - h) / 2.0, w, h);
    cairo_fill(src);
    cairo_destroy(src);

    cached_srfc = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, scaled_width, scaled_height);
    cr = cairo_create(cached_srfc);
    cairo_scale(cr, cairo_scaling_x, cairo_scaling_y);
    cairo_set_source_surface(cr, srfc, 0, 0);
    cairo_set_operator(cr, CAIRO_OPERATOR_OVER);
    cairo_rectangle(cr, 0, 0, width, height);
    cairo_fill(cr);

    cairo_destroy(cr);
    g_object_unref(pmap);
    image_cache_insert_surface(priv->surface_cache, win, cached_srfc);
    cairo_surface_destroy(srfc);
  }
  else
  {
    return; /* we  got nothing... */
  }

  cairo_set_source_surface(destcr, cached_srfc, scaled_x, scaled_y);

  cairo_set_operator(destcr, CAIRO_OPERATOR_OVER);
  cairo_rectangle(destcr, scaled_x, scaled_y, scaled_width, scaled_height);
  cairo_fill(destcr);

  return;
  /* cairo_surface_destroy(cached_srfc); */

error_out:
  /* gdk_flush(); */
  err_code = gdk_error_trap_pop();

  if (err_code)
  {
    printf("Shinyswitcher Message:  A (trapped) X error occured in grab_window_gdk_meth: %d\n", err_code);
  }
}

static void 
do_win_grabs(AwnShinySwitcher *shinyswitcher, cairo_t *destcr, WnckWindow *win, double scaled_x, double scaled_y,
                  double scaled_width, double scaled_height, int x, int y, int width, int height, gboolean on_active_space)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  if (! WNCK_IS_WINDOW(win))
  {
    return ;
  }

  /* Do we grab the window in this particular circumstance? */
  if ((priv->win_grab_mode == 1) || ((priv->win_grab_mode == 2) &&  on_active_space)
      || ((priv->win_grab_mode == 3) && wnck_window_is_active(win)))
  {
    /*window grab method 0... on xfwm only works for active space unless win sticky - so specified behaviour
    in mode may be overriden.  FIXME  cache pixmaps for inactive workspaces.
    */
    switch (priv->win_grab_method)
    {

      case 0:
        /*    if ( on_active_space || wnck_window_is_pinned(win)) */
      {
        grab_window_gdk_meth(shinyswitcher, destcr, win, scaled_x, scaled_y,
                             scaled_width, scaled_height, x, y, width, height,
                             on_active_space || wnck_window_is_pinned(win));
      }

      break;

      case 1:
        grab_window_xrender_meth(shinyswitcher, destcr, win, scaled_x, scaled_y,
                                 scaled_width, scaled_height, x, y, width, height,
                                 on_active_space || wnck_window_is_pinned(win));
        break;

      default:
        printf("INVALID CONFIG OPTION: window grab method\n");
        break;
    }
  }
}


static void 
do_icon_overlays(AwnShinySwitcher *shinyswitcher, cairo_t *destcr, WnckWindow *win, double scaled_x, double scaled_y,
                      double scaled_width, double scaled_height, int x, int y, int width, int height, gboolean on_active_space)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  if (! WNCK_IS_WINDOW(win))
  {
    return ;
  }

  double scale = scaled_width > scaled_height ? scaled_height : scaled_width;

  if (((priv->show_icon_mode == 1) && !on_active_space) || ((priv->show_icon_mode == 2) && !wnck_window_is_active(win))
      || (priv->show_icon_mode == 3))
  {
    GdkPixbuf *pbuf = NULL;
    double icon_scaling = 1.0;

    if ((priv->scale_icon_mode == 3) || (wnck_window_is_active(win) && (priv->scale_icon_mode == 2))
        || (on_active_space && (priv->scale_icon_mode == 1)))
    {
      icon_scaling = priv->scale_icon_factor;
    }

    if (scale*icon_scaling < 1.2)
    {
      return;
    }

    pbuf = image_cache_lookup_key_width_height(shinyswitcher, priv->pixbuf_cache, win, scale * icon_scaling, scale * icon_scaling, TRUE);

    if (!pbuf)
    {
      pbuf = wnck_window_get_icon(win);
      g_assert(pbuf);

      if (!GDK_IS_PIXBUF(pbuf))
      {
        pbuf = wnck_window_get_mini_icon(win);
      }

      if (!GDK_IS_PIXBUF(pbuf))
      {
        pbuf = gdk_pixbuf_new(GDK_COLORSPACE_RGB, TRUE, 8, scaled_width, scaled_height);
        gdk_pixbuf_fill(pbuf, 0x00A00022);
        printf("Bad pixbuf \n");
      }

      pbuf = gdk_pixbuf_scale_simple(pbuf, scale * icon_scaling, scale * icon_scaling, GDK_INTERP_BILINEAR);

      image_cache_insert_pixbuf(priv->pixbuf_cache, win, pbuf);
    }

    cairo_set_operator(destcr, CAIRO_OPERATOR_OVER);

    double alpha = 1.0;

    if (icon_scaling > 0.999)
    {
      gdk_cairo_set_source_pixbuf(destcr, pbuf, scaled_x + (scaled_width - scale) / 2.0, scaled_y + (scaled_height - scale) / 2.0);
      cairo_rectangle(destcr, scaled_x + (scaled_width - scale) / 2.0, scaled_y + (scaled_height - scale) / 2.0, scale, scale);
    }
    else
    {
      switch (priv->scale_icon_pos)
      {

        case NW:
          gdk_cairo_set_source_pixbuf(destcr, pbuf, scaled_x, scaled_y);
          cairo_rectangle(destcr, scaled_x, scaled_y, scale*icon_scaling, scale*icon_scaling);
          break;

        case NE:
          gdk_cairo_set_source_pixbuf(destcr, pbuf, scaled_x + scaled_width - scale*icon_scaling, scaled_y);
          cairo_rectangle(destcr, scaled_x + scaled_width - scale*icon_scaling, scaled_y,
                          scale*icon_scaling, scale*icon_scaling);
          break;

        case SE:
          gdk_cairo_set_source_pixbuf(destcr, pbuf, scaled_x + scaled_width - scale*icon_scaling,
                                      scaled_y + scaled_height - scale*icon_scaling);
          cairo_rectangle(destcr, scaled_x + scaled_width - scale*icon_scaling, scaled_y + scaled_height - scale*icon_scaling,
                          scale*icon_scaling, scale*icon_scaling);
          break;

        case SW:
          gdk_cairo_set_source_pixbuf(destcr, pbuf, scaled_x,
                                      scaled_y + scaled_height - scale*icon_scaling);
          cairo_rectangle(destcr, scaled_x, scaled_y + scaled_height - scale*icon_scaling,
                          scale*icon_scaling, scale*icon_scaling);
          break;

        case CENTRE:

        default:
          gdk_cairo_set_source_pixbuf(destcr, pbuf, scaled_x + (scaled_width - scale*icon_scaling) / 2.0,
                                      scaled_y + (scaled_height - scale*icon_scaling) / 2.0);
          cairo_rectangle(destcr, scaled_x + (scaled_width - scale*icon_scaling) / 2.0,
                          scaled_y + (scaled_height - scale*icon_scaling) / 2.0, scale, scale);
          break;
      }
    }

    if (wnck_window_is_active(win))
    {
      alpha = priv->win_active_icon_alpha;
    }
    else
    {
      alpha = priv->win_inactive_icon_alpha;
    }

    cairo_paint_with_alpha(destcr, alpha);
  }
}


static void 
_unrealize_window_ev(GtkWidget *widget, Win_press_data * data)
{
  g_free(data);
}


static void 
do_event_boxes(AwnShinySwitcher *shinyswitcher, WnckWindow *win, Workplace_info *ws, double scaled_x, double scaled_y,
                    double scaled_width, double scaled_height)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  if (! WNCK_IS_WINDOW(win))
  {
    return ;
  }

  if ((priv->active_window_on_workspace_change_method) && (scaled_height > 1.0) && (scaled_width > 1.0))
  {
    GtkWidget *ev = gtk_event_box_new();
    gtk_widget_set_app_paintable(ev, TRUE);
    gtk_event_box_set_visible_window(GTK_EVENT_BOX(ev), FALSE);
    gtk_widget_set_size_request(ev, scaled_width, scaled_height);
    gtk_fixed_put(GTK_FIXED(ws->wallpaper_ev->parent), ev, scaled_x, scaled_y);

    ws->event_boxes = g_list_append(ws->event_boxes, ev);
    gtk_widget_show(ev);
#if GTK_CHECK_VERSION(2,12,0)

    if (priv->show_tooltips)
      if (wnck_window_has_name(win))
        gtk_widget_set_tooltip_text(ev, wnck_window_get_name(win));

#endif
    Win_press_data * data = g_malloc(sizeof(Win_press_data));

    if (data)
    {
      data->wnck_window = win;
      data->shinyswitcher = AWN_APPLET(shinyswitcher);
      g_signal_connect(G_OBJECT(ev), "button-press-event", G_CALLBACK(_button_win), data);
      g_signal_connect(G_OBJECT(ev), "unrealize", G_CALLBACK(_unrealize_window_ev), data);
    }
  }
}


static void 
remove_queued_render(AwnShinySwitcher *shinyswitcher, WnckWorkspace *space)
{  
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  if (space)
  {
    if (g_tree_lookup(priv->ws_changes, space))
    {
      g_tree_remove(priv->ws_changes, space);
    }
  }
}

static void 
render_windows_to_wallpaper(AwnShinySwitcher *shinyswitcher,  WnckWorkspace * space)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  GList* wnck_spaces = wnck_screen_get_workspaces(priv->wnck_screen);
  GList * iter;
  WnckWindow * top_win = NULL;
  Workplace_info * ws = NULL;


  for (iter = g_list_first(wnck_spaces);iter;iter = g_list_next(iter))
  {
    if ((!space) || (space == iter->data))
    {
      int workspace_num;
      GList*  wnck_windows;
      GList* win_iter;
      remove_queued_render(shinyswitcher, iter->data);
      prepare_to_render_workspace(shinyswitcher, iter->data);
      workspace_num = wnck_workspace_get_number(iter->data);
      wnck_windows = wnck_screen_get_windows_stacked(priv->wnck_screen);

      for (win_iter = g_list_first(wnck_windows);win_iter;win_iter = g_list_next(win_iter))
      {

        if (wnck_window_is_visible_on_workspace(win_iter->data, iter->data))
        {
          if (!wnck_window_is_skip_pager(win_iter->data))
          {
            top_win = iter->data;
            gboolean on_active_space = (wnck_screen_get_active_workspace(priv->wnck_screen) == iter->data);

            int x, y, width, height;
            wnck_window_get_geometry(win_iter->data, &x, &y, &width, &height);
            double scaled_width = (double)priv->mini_work_width * (double)width /
                                  (double)wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen));
            double scaled_height = (double)priv->mini_work_height * (double) height /
                                   (double)wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen));
            double scaled_x, scaled_y;

            scaled_x = (double)x * (double)priv->mini_work_width /
                       (double)wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen))
                       +
                       wnck_workspace_get_viewport_x(iter->data) * (double)priv->mini_work_width /
                       (double)wnck_workspace_get_width(wnck_screen_get_active_workspace(priv->wnck_screen))
                       ;
            scaled_y = (double)y * (double)priv->mini_work_height /
                       (double)wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen))
                       +
                       wnck_workspace_get_viewport_y(iter->data) * (double)priv->mini_work_height /
                       (double)wnck_workspace_get_height(wnck_screen_get_active_workspace(priv->wnck_screen))
                       ;
            ws = g_tree_lookup(priv->ws_lookup_ev, iter->data);
            if (!ws)
              break;
            GdkPixmap *pixmap;
            gtk_image_get_pixmap(GTK_IMAGE(gtk_bin_get_child(GTK_BIN(ws->wallpaper_ev))), &pixmap, NULL);
            cairo_t * destcr = NULL;
            if (pixmap && GDK_IS_PIXMAP (pixmap) )
            {
              destcr = gdk_cairo_create(pixmap);
            }
            if (!destcr)
            {
              continue;
            }
            cairo_set_operator(destcr, CAIRO_OPERATOR_CLEAR);
            cairo_fill(destcr);

            if (1)/* FIXME */
            {
              cairo_set_operator(destcr, CAIRO_OPERATOR_OVER);
              cairo_rectangle(destcr, scaled_x, scaled_y, scaled_width, scaled_height);
              cairo_set_source_rgba(destcr, 1.0f, 1.0f, 1.0f, 0.2f);  /* FIXME ... pref. */
              cairo_fill(destcr);
            }

            if ((scaled_height > 8) && (scaled_width > 8))  /* FIME */
            {
              do_win_grabs(shinyswitcher, destcr, win_iter->data, scaled_x, scaled_y, scaled_width, scaled_height,
                           x, y, width, height, on_active_space);
            }

            if ((scaled_height > 4) && (scaled_width > 4))  /* FIME */
            {

              do_icon_overlays(shinyswitcher, destcr, win_iter->data, scaled_x, scaled_y, scaled_width, scaled_height,
                               x, y, width, height, on_active_space);
            }

            cairo_destroy(destcr);

            do_event_boxes(shinyswitcher, win_iter->data, ws, scaled_x, scaled_y, scaled_width, scaled_height);
          }
        }
      }

      /* printf("\n"); */
    }

    if (!space)
    {
      if (ws)
      {
        GtkWidget * container = ws->wallpaper_ev->parent;
        gtk_widget_hide(container);
        gtk_widget_show(container);
      }
    }
  }

  if (space)
  {
    if (top_win && ws)
    {
      GtkWidget * container = ws->wallpaper_ev->parent;
      gtk_widget_hide(container);
      gtk_widget_show(container);
    }
  }
}

static gboolean 
do_queued_renders(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  GList* wnck_spaces = wnck_screen_get_workspaces(priv->wnck_screen);
  GList * iter;

  if (priv->reloading)
  {
    return TRUE;
  }
  
  for (iter = g_list_first(wnck_spaces);iter;iter = g_list_next(iter))
  {
    if (g_tree_lookup(priv->ws_changes, iter->data))
    {
      g_tree_remove(priv->ws_changes, iter->data);
      render_windows_to_wallpaper(shinyswitcher, iter->data);
    }
  }

  return TRUE;
}

static void 
queue_render(AwnShinySwitcher *shinyswitcher, WnckWorkspace *space)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);
  if (space)
  {
    if (! g_tree_lookup(priv->ws_changes, space))
    {
      g_tree_insert(priv->ws_changes, space, space);
    }
  }
}

static void 
queue_all_render(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);
  GList* wnck_spaces = wnck_screen_get_workspaces(priv->wnck_screen);
  GList * iter;

  for (iter = g_list_first(wnck_spaces);iter;iter = g_list_next(iter))
  {
    queue_render(shinyswitcher, iter->data);
  }
}

static void 
_activewin_change(WnckScreen *screen, WnckWindow *previously_active_window, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  WnckWorkspace *prev_space = NULL;
  WnckWindow * act_win = NULL;
  WnckWorkspace * act_space = NULL;

  if (priv->reloading)
  {
    return;
  }
  act_space = wnck_screen_get_active_workspace(priv->wnck_screen) ;

  if (previously_active_window)
  {
    if (! WNCK_IS_WINDOW(previously_active_window))
    {
      return ;
    }

    prev_space = wnck_window_get_workspace(previously_active_window);
  }

  if (!act_space)
  {
    act_win = wnck_screen_get_active_window(priv->wnck_screen);

    if (act_win)
    {
      act_space = wnck_window_get_workspace(act_win);
    }
  }

  if (prev_space == act_space)
  {
    render_windows_to_wallpaper(shinyswitcher, act_space);
  }
  else
  {
    if (act_space && prev_space)
    {
      render_windows_to_wallpaper(shinyswitcher, act_space);
      queue_render(shinyswitcher, prev_space);
    }
    else if (act_space)
    {
      queue_all_render(shinyswitcher);
      render_windows_to_wallpaper(shinyswitcher, act_space);/* this will remove act_space from queue. */
    }
    else
    {
      render_windows_to_wallpaper(shinyswitcher, NULL);
    }
  }

  if (act_win)
  {
    image_cache_expire(shinyswitcher, priv->surface_cache, act_win);
  }
}


static void 
_workspace_change(WnckScreen *screen, WnckWorkspace *previously_active_space, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  WnckWorkspace *act_space = wnck_screen_get_active_workspace(priv->wnck_screen);

  if (priv->reloading)
  {
    return;
  }
  if (act_space && previously_active_space)
  {
    render_windows_to_wallpaper(shinyswitcher, act_space);
    
    if (act_space != previously_active_space)
    {
      if (priv->got_viewport)
      {
        queue_render(shinyswitcher, previously_active_space);
      }
      else
      {
        queue_all_render(shinyswitcher);
      }
    }
  }
  else if (act_space)
  {
    queue_all_render(shinyswitcher);
    render_windows_to_wallpaper(shinyswitcher, act_space);/* this will remove act_space from queue. */
  }
  else
  {
    render_windows_to_wallpaper(shinyswitcher, NULL);
  }
}


static void 
_window_stacking_change(WnckScreen *screen, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  WnckWorkspace *space = wnck_screen_get_active_workspace(priv->wnck_screen);
  if (priv->reloading)
  {
    return;
  }
  if (space)
  {
    render_windows_to_wallpaper(shinyswitcher, space);
  }
  else
  {
    render_windows_to_wallpaper(shinyswitcher, NULL);
  }
}

static void 
_win_geom_change(WnckWindow *window, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  if (priv->reloading)
  {
    return;
  }
  if (! WNCK_IS_WINDOW(window))
  {
    return ;
  }


  WnckWorkspace *space = wnck_window_get_workspace(window);

  if (!space)
  {
    space = wnck_screen_get_active_workspace(priv->wnck_screen);
  }

  if (space)
  {
    if (priv->got_viewport)
    {
      queue_render(shinyswitcher, space);
    }
    else
    {
      queue_all_render(shinyswitcher);
    }
  }
  else
  {
    queue_all_render(shinyswitcher);
  }
}

static void 
_win_state_change(WnckWindow *window, WnckWindowState changed_mask, WnckWindowState new_state, AwnShinySwitcher *shinyswitcher)
{
  _win_geom_change(window, shinyswitcher);
}

static void 
_win_ws_change(WnckWindow *window, AwnShinySwitcher *shinyswitcher)
{
  queue_all_render(shinyswitcher);
}

static gboolean 
create_windows(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  GList* wnck_spaces = wnck_screen_get_workspaces(priv->wnck_screen);
  GList * iter;

  render_windows_to_wallpaper(shinyswitcher, NULL);

  for (iter = g_list_first(wnck_spaces);iter;iter = g_list_next(iter))
  {
    GList*  wnck_windows = wnck_screen_get_windows_stacked(priv->wnck_screen);
    GList* win_iter;

    for (win_iter = g_list_first(wnck_windows);win_iter;win_iter = g_list_next(win_iter))
    {

      if (!wnck_window_is_skip_pager(win_iter->data))
      {
        g_signal_connect(G_OBJECT(win_iter->data), "state-changed", G_CALLBACK(_win_state_change), shinyswitcher);
        g_signal_connect(G_OBJECT(win_iter->data), "geometry-changed", G_CALLBACK(_win_geom_change), shinyswitcher);
        g_signal_connect(G_OBJECT(win_iter->data), "workspace-changed", G_CALLBACK(_win_ws_change), shinyswitcher);

        if (priv->show_right_click && WNCK_IS_WINDOW(win_iter->data))
        {
          g_tree_insert(priv->win_menus, G_OBJECT(win_iter->data), shinyswitcher);
        }
        else if (!priv->show_right_click && WNCK_IS_WINDOW(win_iter->data))
        {
          GtkWidget * menu;
          GtkWidget *item;
          menu = awn_applet_create_default_menu(AWN_APPLET(shinyswitcher));
          gtk_menu_set_screen(GTK_MENU(menu), NULL);
          item = gtk_image_menu_item_new_with_label("Applet Preferences");
          gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(item),
                                        gtk_image_new_from_stock(GTK_STOCK_PREFERENCES,
                                                                 GTK_ICON_SIZE_MENU));
          gtk_widget_show_all(item);
          g_signal_connect(G_OBJECT(item), "activate",
                           G_CALLBACK(_start_applet_prefs), NULL);
          gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

          item = awn_applet_create_about_item (AWN_APPLET(shinyswitcher),
             "Copyright 2007,2008 Rodney Cryderman <rcryderman@gmail.com>",
             AWN_APPLET_LICENSE_GPLV2,
             NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);

          gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

          g_tree_insert(priv->win_menus, G_OBJECT(win_iter->data), menu);
        }
      }
    }
  }

  return FALSE;
}

static void 
_wallpaper_change(WnckScreen *screen, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  if (priv->reloading)
  {
    return;
  }
  g_object_unref(priv->wallpaper_inactive);
  g_object_unref(priv->wallpaper_active);
  set_background(shinyswitcher);
  queue_all_render(shinyswitcher);
}

static void 
_window_opened(WnckScreen *screen, WnckWindow *window, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);
  if (priv->reloading)
  {
    return;
  }
  if (! WNCK_IS_WINDOW(window))
  {
    return ;
  }

  g_signal_connect(G_OBJECT(window), "state-changed", G_CALLBACK(_win_state_change), shinyswitcher);

  g_signal_connect(G_OBJECT(window), "geometry-changed", G_CALLBACK(_win_geom_change), shinyswitcher);
  g_signal_connect(G_OBJECT(window), "workspace-changed", G_CALLBACK(_win_ws_change), shinyswitcher);

  if (priv->show_right_click && WNCK_IS_WINDOW(window))
  {
    g_tree_insert(priv->win_menus, G_OBJECT(window), shinyswitcher);
  }
  else if (!priv->show_right_click && WNCK_IS_WINDOW(window))
  {
    GtkWidget * menu;
    GtkWidget *item;
    menu = awn_applet_create_default_menu(AWN_APPLET(shinyswitcher));
    gtk_menu_set_screen(GTK_MENU(menu), NULL);
    item = gtk_image_menu_item_new_with_label("Applet Preferences");
    gtk_image_menu_item_set_image(GTK_IMAGE_MENU_ITEM(item),
                                  gtk_image_new_from_stock(GTK_STOCK_PREFERENCES,
                                                           GTK_ICON_SIZE_MENU));
    gtk_widget_show_all(item);
    g_signal_connect(G_OBJECT(item), "activate",
                     G_CALLBACK(_start_applet_prefs), NULL);
    gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);

    item = awn_applet_create_about_item (AWN_APPLET(shinyswitcher),
             "Copyright 2007,2008 Rodney Cryderman <rcryderman@gmail.com>",
             AWN_APPLET_LICENSE_GPLV2,
             NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);

    gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);
    g_tree_insert(priv->win_menus, G_OBJECT(window), menu);
  }
}

static void 
_window_closed(WnckScreen *screen, WnckWindow *window, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  if (priv->reloading)
  {
    return;
  }  
  image_cache_remove(priv->pixbuf_cache, window);
  image_cache_remove(priv->surface_cache, window);

  if (priv->show_right_click)
    g_tree_remove(priv->win_menus, window);

  if (!priv->got_viewport)
  {
    queue_all_render(shinyswitcher);
  }

  g_signal_handlers_disconnect_by_func(G_OBJECT(window), G_CALLBACK(_win_state_change), shinyswitcher);

  g_signal_handlers_disconnect_by_func(G_OBJECT(window), G_CALLBACK(_win_geom_change), shinyswitcher);
  g_signal_handlers_disconnect_by_func(G_OBJECT(window), G_CALLBACK(_win_ws_change), shinyswitcher);
}

static void 
_composited_changed(GdkScreen *screen, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  screen = gtk_widget_get_screen(GTK_WIDGET(shinyswitcher));

  if (gdk_screen_is_composited(screen))
  {
//    printf("screen is now composited... maybe we should do something\n");
  }
  else
  {
//    printf("screen is now not composited... maybe we should do something\n");
  }
  if (!priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
  }  
}

static void  
_wm_changed(WnckScreen *screen, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);    
//  g_debug(" Window Manager Changed: %s",  wnck_screen_get_window_manager_name(screen));

  /*
    Can't detect compiz here...
   */
  if (wnck_screen_get_window_manager_name (screen) && !priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
//    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
    /*we need to exit from this signal handler before calling some of the 
     functions in _setup*/
    g_idle_add ( (GSourceFunc)awn_shiny_switcher_setup,shinyswitcher);
  }
}


static void 
_screen_size_changed(WnckScreen *screen, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);
  calc_dimensions(shinyswitcher);
}


static gboolean 
do_queue_act_ws(AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);  
  WnckWorkspace *space;
  space = wnck_screen_get_active_workspace(priv->wnck_screen);

  if (space)
  {
    queue_render(shinyswitcher, space);
  }

  return TRUE;
}


static gboolean 
_waited(AwnShinySwitcher *shinyswitcher)
{
  static gboolean done_once = FALSE;
  
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);
  priv->pScreen = gtk_widget_get_screen(GTK_WIDGET(AWN_APPLET(shinyswitcher)));
  wnck_screen_force_update(priv->wnck_screen);
  priv->rows = wnck_workspace_get_layout_row(wnck_screen_get_workspace(priv->wnck_screen,
                        wnck_screen_get_workspace_count(priv->wnck_screen) - 1)
                                                     ) + 1;
  priv->cols = wnck_workspace_get_layout_column(wnck_screen_get_workspace(priv->wnck_screen,
                        wnck_screen_get_workspace_count(priv->wnck_screen) - 1)
                                                        ) + 1 ;

  priv->gdkgc = gdk_gc_new(GTK_WIDGET(AWN_APPLET(shinyswitcher))->window);
  priv->rgba_cmap = gdk_screen_get_rgba_colormap(priv->pScreen);
  priv->rgb_cmap = gdk_screen_get_rgb_colormap(priv->pScreen);
  calc_dimensions(shinyswitcher);
  set_background(shinyswitcher);
  create_containers(shinyswitcher);
  create_windows(shinyswitcher);

  if (!done_once)
  {
    g_signal_connect(G_OBJECT(priv->wnck_screen), "active-workspace-changed", G_CALLBACK(_workspace_change), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->wnck_screen), "active-window-changed", G_CALLBACK(_activewin_change), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->wnck_screen), "background-changed", G_CALLBACK(_wallpaper_change), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->wnck_screen), "window-stacking-changed", G_CALLBACK(_window_stacking_change), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->wnck_screen), "window-closed", G_CALLBACK(_window_closed), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->wnck_screen), "window-opened", G_CALLBACK(_window_opened), shinyswitcher);
    g_signal_connect(G_OBJECT(priv->wnck_screen), "window-manager-changed", G_CALLBACK(_wm_changed), shinyswitcher);
    
#if GLIB_CHECK_VERSION(2,14,0)

    if (priv->do_queue_freq % 1000 == 0)
    {
      g_timeout_add_seconds(priv->do_queue_freq / 1000, (GSourceFunc)do_queued_renders, shinyswitcher);
      g_timeout_add_seconds((priv->do_queue_freq + 1000) / 1000, (GSourceFunc)do_queue_act_ws, shinyswitcher); /* FIXME */
    }
    else
    {
      g_timeout_add(priv->do_queue_freq, (GSourceFunc)do_queued_renders, shinyswitcher);
      g_timeout_add(priv->do_queue_freq + 1000, (GSourceFunc)do_queue_act_ws, shinyswitcher); /* FIXME */
    }

#else
    g_timeout_add(priv->do_queue_freq, (GSourceFunc)do_queued_renders, shinyswitcher);

    g_timeout_add(priv->do_queue_freq + 1000, (GSourceFunc)do_queue_act_ws, shinyswitcher); /* FIXME */

#endif
    g_signal_connect(G_OBJECT(shinyswitcher), "size-changed", G_CALLBACK(_height_changed), (gpointer)shinyswitcher);

    g_signal_connect(G_OBJECT(shinyswitcher), "position-changed", G_CALLBACK(_orient_changed), (gpointer)shinyswitcher);

    g_signal_connect(G_OBJECT(shinyswitcher), "offset-changed", G_CALLBACK(_offset_changed), shinyswitcher);
  }

  gtk_widget_show_all(priv->container);

  gtk_widget_show_all(GTK_WIDGET(shinyswitcher));

  if (!done_once)
  {
    g_signal_connect(G_OBJECT(priv->pScreen), "composited-changed", G_CALLBACK(_composited_changed), shinyswitcher);

    g_signal_connect(G_OBJECT(priv->pScreen), "size-changed", G_CALLBACK(_screen_size_changed), shinyswitcher);

    g_signal_connect(G_OBJECT(shinyswitcher), "expose_event", G_CALLBACK(_expose_event_outer), shinyswitcher);

    g_signal_connect(G_OBJECT(priv->wnck_screen), "workspace-created", G_CALLBACK(_workspaces_changed), shinyswitcher);

    g_signal_connect(G_OBJECT(priv->wnck_screen), "workspace-destroyed", G_CALLBACK(_workspaces_changed), shinyswitcher);

    g_signal_connect(G_OBJECT(priv->wnck_screen), "viewports-changed", G_CALLBACK(_viewports_changed), shinyswitcher);
  }
  done_once = TRUE;
  priv->reloading = FALSE;

  return FALSE;
}

static gboolean 
_expose_event_window(GtkWidget *widget, GdkEventExpose *expose, gpointer data)
{
  return FALSE;
}


static gboolean 
_expose_event_outer(GtkWidget *widget, GdkEventExpose *expose, AwnShinySwitcher *shinyswitcher)
{

  return FALSE;

}

static void
_height_changed(AwnShinySwitcher *app, guint height, AwnShinySwitcher *shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  /* doing this as a tree right now..  cause it's easy and I think I'll need a complex data structure eventually. */
  priv->height = height;
  if (!priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
  }
}


static void 
_offset_changed(AwnShinySwitcher *app, guint offset, AwnShinySwitcher * shinyswitcher)
{
}

static void
_orient_changed(AwnShinySwitcher *app, GtkPositionType orient,
                AwnShinySwitcher * shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE (shinyswitcher);  
  priv->orient = orient;
  if (!priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
  }
}

static void
_workspaces_changed(WnckScreen    *screen, WnckWorkspace *space, AwnShinySwitcher * shinyswitcher)
{
  AwnShinySwitcherPrivate * priv = GET_PRIVATE(shinyswitcher);      
  if (!priv->reloading)
  {
    priv->reloading = TRUE;
    gtk_widget_destroy (GTK_WIDGET(priv->align));
//    awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));
    g_idle_add ((GSourceFunc)awn_shiny_switcher_setup,shinyswitcher);
  }  
//  gtk_widget_destroy (GTK_WIDGET(priv->align));
//  awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (shinyswitcher));  
}

static void
_viewports_changed(WnckScreen    *screen, AwnShinySwitcher * shinyswitcher)
{
/*  g_debug("viewports_changed\n");
  _changed(priv->applet, shinyswitcher);
  _changed_waited(shinyswitcher);*/
}
//******************************************************************************






static void
awn_shiny_switcher_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_shiny_switcher_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
awn_shiny_switcher_dispose (GObject *object)
{
  G_OBJECT_CLASS (awn_shiny_switcher_parent_class)->dispose (object);
}

static void
awn_shiny_switcher_finalize (GObject *object)
{
  G_OBJECT_CLASS (awn_shiny_switcher_parent_class)->finalize (object);
}

static gboolean
awn_shiny_switcher_setup (AwnShinySwitcher * object)
{
  AwnShinySwitcherPrivate * priv;
  GdkScreen *screen;

  priv = GET_PRIVATE (object);
  g_return_val_if_fail (priv->reloading,TRUE);
  priv->padding = awn_applet_get_offset(AWN_APPLET(object));;
  priv->orient = awn_applet_get_pos_type(AWN_APPLET(object));
  priv->align  = AWN_ALIGNMENT(awn_alignment_new_for_applet(AWN_APPLET(object)));
  gtk_container_add(GTK_CONTAINER(object), GTK_WIDGET(priv->align));
  priv->config = NULL;
  priv->wallpaper_active = NULL;
  priv->wallpaper_inactive = NULL;

  priv->height = awn_applet_get_size(AWN_APPLET(object));
  priv->wnck_screen = wnck_screen_get_default();
  wnck_screen_force_update(priv->wnck_screen);
  priv->got_viewport = wnck_workspace_is_virtual(wnck_screen_get_active_workspace(priv->wnck_screen));

  init_config(AWN_SHINY_SWITCHER(object));

  priv->reconfigure = !priv->got_viewport;  /* for the moment... will be a config option eventually */

  screen = gtk_widget_get_screen(GTK_WIDGET(object));

  if (priv->reconfigure)
  {
    wnck_screen_change_workspace_count(priv->wnck_screen, priv->cols*priv->rows);
    wnck_screen_force_update(priv->wnck_screen);

    if (!priv->wnck_token)
    {
      priv->wnck_token = wnck_screen_try_set_workspace_layout(priv->wnck_screen, 0,  priv->rows, 0);
    }
    else
    {
      priv->wnck_token = wnck_screen_try_set_workspace_layout(priv->wnck_screen, priv->wnck_token, priv->rows, 0);
    }

    if (!priv->wnck_token)
    {
      printf("Failed to acquire ownership of workspace layout\n");
      priv->reconfigure = FALSE;
    }
  }
  else
  {
    printf("ShinySwitcher Message:  viewport/compiz detected.. using existing workspace config\n");
  }
  if (priv->wnck_token)
  {
    wnck_screen_release_workspace_layout(priv->wnck_screen,priv->wnck_token);
    priv->wnck_token = 0;
  }

  if (!priv->pScreen || !wnck_screen_get_window_manager_name(priv->wnck_screen))
  {
    g_idle_add((GSourceFunc)_waited, object); /* don't need to do this as seconds... happens once. */
  }
  else
  {
    g_idle_add((GSourceFunc)_waited, object); /* don't need to do this as seconds... happens once. */    
//    _waited (object);
  }
  return FALSE;
}

static void
awn_shiny_switcher_constructed (GObject *object)
{
  AwnShinySwitcherPrivate * priv;
  priv = GET_PRIVATE (object);
  
  G_OBJECT_CLASS (awn_shiny_switcher_parent_class)->constructed (object);

  priv->pScreen = NULL;
  priv->reloading = TRUE;
  priv->ws_lookup_ev = g_tree_new(_cmp_ptrs);

  /* doing this as a tree right now..  cause it's easy and I think I'll need a complex data structure eventually. */
  priv->ws_changes = g_tree_new(_cmp_ptrs);
  priv->pixbuf_cache = g_tree_new(_cmp_ptrs);
  priv->surface_cache = g_tree_new(_cmp_ptrs);
  priv->win_menus = g_tree_new(_cmp_ptrs);
  
  awn_shiny_switcher_setup (AWN_SHINY_SWITCHER (object));
}

static void
awn_shiny_switcher_class_init (AwnShinySwitcherClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (AwnShinySwitcherPrivate));

  object_class->get_property = awn_shiny_switcher_get_property;
  object_class->set_property = awn_shiny_switcher_set_property;
  object_class->dispose = awn_shiny_switcher_dispose;
  object_class->finalize = awn_shiny_switcher_finalize;
  object_class->constructed = awn_shiny_switcher_constructed;
}


static void
awn_shiny_switcher_init (AwnShinySwitcher *self)
{
}

AwnShinySwitcher*
awn_shiny_switcher_new (const gchar *name, const gchar *uid, gint panel_id)
{
  return g_object_new (AWN_TYPE_SHINY_SWITCHER,
                       "canonical-name",name,
                       "uid",uid,
                       "panel-id",panel_id,
                       NULL);
}

