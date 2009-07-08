/*
 * Copyright (c) 2007,2008,2009 Rodney Cryderman <rcryderman@gmail.com>
 * Copyright (c) 2007,2008,2009 Mark Lee         <avant-wn@lazymalevolence.com>
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

/* getline() */
#define _GNU_SOURCE
#include <stdio.h>
/* isalpha() */
#include <ctype.h>

#include <gtk/gtk.h>
#include <libdesktop-agnostic/desktop-agnostic.h>
#include <glib/gstdio.h>
#include <glib/gi18n-lib.h>
#include <string.h>

#include <libawn/libawn.h>

#define APPLET_NAME "places"

#define CONFIG_NORMAL_BG     "bg_normal_colour"
#define CONFIG_NORMAL_FG     "text_normal_colour"
#define CONFIG_HOVER_BG      "bg_hover_colour"
#define CONFIG_HOVER_FG      "text_hover_colour"

#define CONFIG_TEXT_SIZE     "text_size"

#define CONFIG_MENU_GRADIENT "menu_item_gradient_factor"

#define CONFIG_FILEMANAGER   "filemanager"
#define CONFIG_APPLET_ICON   "applet_icon"


#define CONFIG_SHOW_TOOLTIPS "show_tooltips"
#define CONFIG_BORDER_COLOUR "border_colour"
#define CONFIG_BORDER_WIDTH  "border_width"

#define CONFIG_HONOUR_GTK    "honour_gtk"

typedef struct
{
  DesktopAgnosticColor *base;
  DesktopAgnosticColor *text;

}Menu_item_color;

typedef struct
{
  GtkWidget  *applet;
  GdkPixbuf    *icon;
  int     applet_icon_height;
  GtkWidget   *mainwindow;
  GtkWidget   *vbox;

  Menu_item_color  normal_colours;
  Menu_item_color  hover_colours;
  double    menu_item_gradient_factor;

  gboolean   honour_gtk;

  DesktopAgnosticColor   *border_colour;
  gint    border_width;

  gint    text_size;
  gint    max_width;


  GSList    *menu_list;

  gchar    *applet_icon_name;
  gboolean   show_tooltips;

  gchar    *file_manager;
  gchar    *desktop_dir;

  DesktopAgnosticConfigClient  *config;

  gchar * uid;
}Places;


typedef struct
{
  gchar  *text;
  gchar *exec;
  gchar *icon;
  gchar *comment;


  GtkWidget *widget;
  GtkWidget *normal;
  GtkWidget *hover;

  Places  *places;

}Menu_Item;


GtkWidget * build_menu_widget(Places * places, Menu_item_color * mic,  char * text, GdkPixbuf *pbuf, GdkPixbuf *pover, int max_width);
static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event, Places *places);
static gboolean _show_prefs(GtkWidget *widget, GdkEventButton *event, Places * places);

static void get_places(Places * places);
static void render_places(Places * places);
static void free_menu_list_item(Menu_Item * item);
static GtkWidget * menu_new(Places *places);
static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event, Places * places);
static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, Places * places);

static void free_menu_list_item(Menu_Item * item)
{
  if (item->text)
    g_free(item->text);

  if (item->icon)
    g_free(item->icon);

  if (item->exec)
    g_free(item->exec);

  if (item->comment)
    g_free(item->comment);

  if (item->widget)
    gtk_widget_destroy(item->widget);

  if (item->normal)
    gtk_widget_destroy(item->normal);

  if (item->hover)
    gtk_widget_destroy(item->hover);

  item->text = NULL;

  item->icon = NULL;

  item->exec = NULL;

  item->comment = NULL;

  item->widget = NULL;

  item->hover = NULL;

  item->normal = NULL;

}

//CONF STUFF

static void config_get_string(DesktopAgnosticConfigClient *client, const gchar *key, gchar **str)
{
  *str = desktop_agnostic_config_client_get_string(client, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, key, NULL);
}

static void config_get_color(DesktopAgnosticConfigClient *client, const gchar *key, DesktopAgnosticColor **color)
{
  GError *error = NULL;
  GValue value = desktop_agnostic_config_client_get_value(client, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, key, &error);

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

void init_config(Places * places)
{
  places->config = awn_config_get_default_for_applet(AWN_APPLET(places->applet), NULL);

  config_get_color(places->config, CONFIG_NORMAL_BG,     &places->normal_colours.base);
  config_get_color(places->config, CONFIG_NORMAL_FG,     &places->normal_colours.text);
  config_get_color(places->config, CONFIG_HOVER_BG,      &places->hover_colours.base);
  config_get_color(places->config, CONFIG_HOVER_FG,      &places->hover_colours.text);
  config_get_color(places->config, CONFIG_BORDER_COLOUR, &places->border_colour);

  places->border_width              = desktop_agnostic_config_client_get_int(places->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, CONFIG_BORDER_WIDTH,  NULL);
  places->text_size                 = desktop_agnostic_config_client_get_int(places->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, CONFIG_TEXT_SIZE,     NULL);
  places->menu_item_gradient_factor = desktop_agnostic_config_client_get_float(places->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, CONFIG_MENU_GRADIENT, NULL);
  places->show_tooltips             = desktop_agnostic_config_client_get_bool(places->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, CONFIG_SHOW_TOOLTIPS, NULL);
  places->honour_gtk                = desktop_agnostic_config_client_get_bool(places->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, CONFIG_HONOUR_GTK,    NULL);
  config_get_string(places->config, CONFIG_FILEMANAGER, &(places->file_manager));
  config_get_string(places->config, CONFIG_APPLET_ICON, &(places->applet_icon_name));

  if (places->honour_gtk)
  {
    GtkWidget *top_win = GTK_WIDGET(places->applet);
    places->normal_colours.base = desktop_agnostic_color_new(&top_win->style->bg[GTK_STATE_NORMAL], G_MAXUSHORT);
    places->normal_colours.text = desktop_agnostic_color_new(&top_win->style->fg[GTK_STATE_ACTIVE], G_MAXUSHORT);
    places->hover_colours.base = desktop_agnostic_color_new(&top_win->style->bg[GTK_STATE_ACTIVE], G_MAXUSHORT);
    places->hover_colours.text = desktop_agnostic_color_new(&top_win->style->fg[GTK_STATE_ACTIVE], G_MAXUSHORT);
    places->border_colour = desktop_agnostic_color_new(&top_win->style->text_aa[0], G_MAXUSHORT);
    places->menu_item_gradient_factor = 1.0;
  }

  places->menu_list = NULL;
}

#define SET_CONFIG_OPTION(type, key, value) desktop_agnostic_config_client_set_##type (places->config, DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, key, value, NULL)
static void set_config_colour(Places *places, const gchar *key, DesktopAgnosticColor *color)
{
  gchar *str;
  str = desktop_agnostic_color_to_string(color);
  SET_CONFIG_OPTION(string, key, str);
  g_free(str);
}

static void save_config(Places * places)
{
  set_config_colour(places, CONFIG_NORMAL_BG,     places->normal_colours.base);
  set_config_colour(places, CONFIG_NORMAL_FG,     places->normal_colours.text);
  set_config_colour(places, CONFIG_HOVER_BG,      places->hover_colours.base);
  set_config_colour(places, CONFIG_HOVER_FG,      places->hover_colours.text);
  SET_CONFIG_OPTION(int,    CONFIG_TEXT_SIZE,     places->text_size);
  SET_CONFIG_OPTION(float,  CONFIG_MENU_GRADIENT, places->menu_item_gradient_factor);
  SET_CONFIG_OPTION(string, CONFIG_FILEMANAGER,   places->file_manager);
  SET_CONFIG_OPTION(string, CONFIG_APPLET_ICON,   places->applet_icon_name);
  SET_CONFIG_OPTION(bool,   CONFIG_HONOUR_GTK,    places->honour_gtk);
  SET_CONFIG_OPTION(bool,   CONFIG_SHOW_TOOLTIPS, places->show_tooltips);
  SET_CONFIG_OPTION(int,    CONFIG_BORDER_WIDTH,  places->border_width);
  set_config_colour(places, CONFIG_BORDER_COLOUR, places->border_colour);
}

static void _do_update_places(Places * places)
{
  g_slist_foreach(places->menu_list, (GFunc)free_menu_list_item, NULL);
  g_slist_free(places->menu_list);
  places->menu_list = NULL;
  gtk_widget_destroy(places->vbox);
  places->mainwindow = menu_new(places);
  places->vbox = gtk_vbox_new(FALSE, 0);
  gtk_container_add(GTK_CONTAINER(places->mainwindow), places->vbox);
  g_signal_connect(G_OBJECT(places->mainwindow), "focus-out-event", G_CALLBACK(_focus_out_event), places);
  g_signal_connect(G_OBJECT(places->mainwindow), "expose-event", G_CALLBACK(_expose_event), places);
  render_places(places); //FIXME

}

static gboolean _do_update_places_wrapper(Places * places)
{
  _do_update_places(places);
  return FALSE;
}


//===========================================================================


static void monitor_places_callback(DesktopAgnosticVFSFileMonitor *monitor,
                                    DesktopAgnosticVFSFileBackend *monitor_path,
                                    DesktopAgnosticVFSFileBackend *event_path,
                                    DesktopAgnosticVFSFileMonitorEvent event,
                                    Places *places)
{
  _do_update_places(places);
}

static void monitor_places(Places *places)
{
  GError *error = NULL;
  DesktopAgnosticVFSFileBackend *file;
  DesktopAgnosticVFSFileMonitor *monitor;

  const gchar *home_dir = g_getenv("HOME");

  if (!home_dir)
  {
    home_dir = g_get_home_dir();
  }

  gchar *filename = g_build_filename(home_dir, ".gtk-bookmarks", NULL);

  file = desktop_agnostic_vfs_file_new_for_path(filename, &error);

  g_free(filename);

  if (error)
  {
    g_critical("Could not create the gtk-bookmarks file object: %s", error->message);
    g_error_free(error);
    return;
  }
  else if (!file)
  {
    g_critical("Could not create the gtk-bookmarks file object.");
    return;
  }


  monitor = desktop_agnostic_vfs_file_backend_monitor(file);
  g_signal_connect(monitor, "changed", G_CALLBACK(monitor_places_callback), places);
}

static void _vfs_changed(DesktopAgnosticVFSVolumeMonitor *monitor,
                         DesktopAgnosticVFSVolumeBackend *volume,
                         Places                          *places)
{
  g_timeout_add(500, (GSourceFunc)_do_update_places_wrapper, places);
}

static void _fillin_connected(DesktopAgnosticVFSVolumeBackend *volume,
                              Places                          *places)
{
  Menu_Item *item;
  DesktopAgnosticVFSFileBackend *uri;
  const gchar *uri_str;

  g_message("Attempting to add %s...", desktop_agnostic_vfs_volume_backend_get_name(volume));

  /* don't use g_return_if_fail because it runs g_critical */
  if (!desktop_agnostic_vfs_volume_backend_is_mounted(volume))
  {
    return;
  }

  item = g_malloc(sizeof(Menu_Item));

  item->places = places;
  item->text = g_strdup(desktop_agnostic_vfs_volume_backend_get_name(volume));
  item->icon = g_strdup(desktop_agnostic_vfs_volume_backend_get_icon(volume));
  uri = desktop_agnostic_vfs_volume_backend_get_uri(volume);
  uri_str = desktop_agnostic_vfs_file_backend_get_uri(uri);
  item->exec = g_strdup_printf("%s %s", places->file_manager, uri_str);
  item->comment = g_strdup_printf("%s\n%s", item->text, uri_str);
  g_object_unref(uri);
  places->menu_list = g_slist_append(places->menu_list, item);
}

static void get_places(Places * places)
{
  DesktopAgnosticVFSImplementation *vfs;
  Menu_Item *item = NULL;
  GError *error = NULL;
  const gchar *desktop_dir = g_get_user_special_dir (G_USER_DIRECTORY_DESKTOP);

  item = g_malloc(sizeof(Menu_Item));
  item->text = g_strdup("Home");
  item->icon = g_strdup("stock_home");
  const gchar *homedir = g_getenv("HOME");

  if (!homedir)
    homedir = g_get_home_dir();

  item->exec = g_strdup_printf("%s %s", places->file_manager, homedir);

  item->comment = g_strdup("Your Home Directory");

  item->places = places;

  places->menu_list = g_slist_append(places->menu_list, item);

  item = g_malloc(sizeof(Menu_Item));

  item->text = g_strdup(_("Desktop"));

  if (desktop_dir)
  {
    places->desktop_dir = g_strdup (desktop_dir);
  }
  else
  {
    if (g_getenv("HOME") )
    {
      places->desktop_dir = g_build_filename(g_getenv("HOME"),"Desktop",NULL);
    }
    else
    {
      places->desktop_dir = g_strdup("Desktop");
    }
  }

  item->icon = g_strdup("desktop");

  item->exec = g_strdup_printf("%s %s", places->file_manager, places->desktop_dir);
  item->comment = g_strdup(item->text);
  item->places = places;
  places->menu_list = g_slist_append(places->menu_list, item);

  item = g_malloc(sizeof(Menu_Item));
  item->text = g_strdup("File System");
  item->icon = g_strdup("system");
  item->exec = g_strdup_printf("%s /", places->file_manager);
  item->comment = g_strdup("Root File System");
  item->places = places;
  places->menu_list = g_slist_append(places->menu_list, item);
  
  vfs = desktop_agnostic_vfs_get_default (&error);
  if (error)
  {
    g_critical("Could not get the VFS implementation: %s", error->message);
    g_error_free(error);
    return;
  }
  else if (!vfs)
  {
    g_critical("Could not get the VFS implementation.");
    return;
  }

  static DesktopAgnosticVFSVolumeMonitor* vol_monitor = NULL;

  if (!vol_monitor)
  {
    /*this is structured like this because get_places() is
    invoked any time there is a change in places... only want perform
    these actions once.*/
    vol_monitor = desktop_agnostic_vfs_implementation_volume_monitor_get_default (vfs);
    g_signal_connect(vol_monitor, "volume-mounted", G_CALLBACK(_vfs_changed), places);
    g_signal_connect(vol_monitor, "volume-unmounted", G_CALLBACK(_vfs_changed), places);

    monitor_places(places); /* monitor bookmark file */
  }

  GList *volumes = desktop_agnostic_vfs_volume_monitor_get_volumes(vol_monitor);

  if (volumes)
  {
    g_message("Number of volumes: %d", g_list_length(volumes));
    g_list_foreach(volumes, (GFunc)_fillin_connected, places);
  }

  g_list_free (volumes);
//bookmarks
  FILE* handle;
  gchar *  filename = g_strdup_printf("%s/.gtk-bookmarks", homedir);
  handle = g_fopen(filename, "r");

  if (handle)
  {
    char * line = NULL;
    size_t  len = 0;

    while (getline(&line, &len, handle) != -1)
    {
      gchar ** tokens;
      tokens = g_strsplit(line, " ", 2);

      if (tokens)
      {
        if (tokens[0])
        {
          gchar * shell_quoted;
          g_strstrip(tokens[0]);
          item = g_malloc(sizeof(Menu_Item));

          if (tokens[1])
          {
            g_strstrip(tokens[1]);
            item->text = g_strdup(tokens[1]);
          }
          else
          {
            item->text = g_uri_unescape_string(g_path_get_basename(tokens[0]), NULL);
          }

          item->icon = g_strdup("stock_folder");

          shell_quoted = g_shell_quote(tokens[0]);
          item->exec = g_strdup_printf("%s %s", places->file_manager, shell_quoted);
          g_free(shell_quoted);
          item->comment = g_uri_unescape_string(g_strdup(tokens[0]), NULL);
          item->places = places;
          places->menu_list = g_slist_append(places->menu_list, item);

        }

      }

      g_strfreev(tokens);

      free(line);

      line = NULL;
    }

    fclose(handle);

    g_free(filename);
  }
  else
  {
    printf("Unable to open bookmark file: %s/.gtk-bookmarks\n", homedir);
  }
}



/* =================================================================

Rendering/events stuff follows

----------------------------------------------------------------*/


GtkWidget * build_menu_widget(Places * places, Menu_item_color * mic,  char * text, GdkPixbuf *pbuf, GdkPixbuf *pover, int max_width)
{
  static cairo_t *cr = NULL;
  GtkWidget * widget;
  GdkScreen* pScreen;
  GdkPixmap * pixmap;
  GdkColormap* cmap;
  cairo_pattern_t *gradient = NULL;
  cairo_text_extents_t    extents;
  gint pixmap_width = max_width;
  gint pixmap_height = places->text_size * 1.6;

  if (pbuf)
  {
    if (gdk_pixbuf_get_height(pbuf) != places->text_size)
    {
      pbuf = gdk_pixbuf_scale_simple(pbuf, places->text_size, places->text_size, GDK_INTERP_HYPER);
    }
    else
    {
      gdk_pixbuf_ref(pbuf);
    }
  }

  if (pover)
  {
    if (gdk_pixbuf_get_height(pover) != places->text_size*0.7)
    {
      pover = gdk_pixbuf_scale_simple(pover, places->text_size * 0.7, places->text_size * 0.7, GDK_INTERP_HYPER);
    }
    else
    {
      gdk_pixbuf_ref(pover);
    }
  }

  pixmap = gdk_pixmap_new(NULL, pixmap_width, places->text_size * 1.6, 32);   //FIXME

  widget = gtk_image_new_from_pixmap(pixmap, NULL);
  pScreen = gtk_widget_get_screen(GTK_WIDGET(places->applet));
  cmap = gdk_screen_get_rgba_colormap(pScreen);

  if (!cmap)
    cmap = gdk_screen_get_rgb_colormap(pScreen);

  gdk_drawable_set_colormap(pixmap, cmap);

  cr = gdk_cairo_create(pixmap);

  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);

  cairo_paint(cr);

  cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);

  gradient = cairo_pattern_create_linear(0, 0, 0, places->text_size * 1.6);

  awn_cairo_pattern_add_color_stop_color_with_alpha_multiplier(gradient, 0, mic->base, places->menu_item_gradient_factor);

  awn_cairo_pattern_add_color_stop_color(gradient, 0.2, mic->base);

  awn_cairo_pattern_add_color_stop_color(gradient, 0.8, mic->base);

  awn_cairo_pattern_add_color_stop_color_with_alpha_multiplier(gradient, 1, mic->base, places->menu_item_gradient_factor);

  cairo_set_source(cr, gradient);

  cairo_paint(cr);

  cairo_set_operator(cr, CAIRO_OPERATOR_OVER);

  if (pbuf)
  {
    gdk_cairo_set_source_pixbuf(cr, pbuf, places->text_size*0.3, places->text_size*0.2);
    cairo_rectangle(cr, 0, 0, places->text_size*1.3, places->text_size*1.2);
    cairo_fill(cr);

    if (pover)
    {
      gdk_cairo_set_source_pixbuf(cr, pover, places->text_size*0.5, places->text_size*0.4);
      cairo_rectangle(cr, 0, 0, places->text_size*1.3, places->text_size*1.2);
      cairo_fill(cr);
    }
  }
  else if (pover)
  {
    gdk_cairo_set_source_pixbuf(cr, pover, places->text_size*0.3, places->text_size*0.2);
    cairo_rectangle(cr, 0, 0, places->text_size*1.3, places->text_size*1.2);
    cairo_fill(cr);
  }

  if (places->border_width > 0)
  {
    awn_cairo_set_source_color(cr, places->border_colour);
    cairo_set_line_width(cr, places->border_width);
    cairo_move_to(cr, places->border_width / 2, 0);
    cairo_line_to(cr, places->border_width / 2, pixmap_height);
    cairo_stroke(cr);
    cairo_move_to(cr, pixmap_width - places->border_width / 2, 0);
    cairo_line_to(cr, pixmap_width - places->border_width / 2, pixmap_height);
    cairo_stroke(cr);
  }

  awn_cairo_set_source_color(cr, mic->text);

  cairo_set_operator(cr, CAIRO_OPERATOR_OVER);
  cairo_move_to(cr, places->text_size*1.4 , places->text_size*1.1);
  cairo_select_font_face(cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
  cairo_set_font_size(cr, places->text_size);

  char * buf;
  int  nul_pos = strlen(text);
  buf = g_malloc(nul_pos + 3);
  strcpy(buf, text);
  cairo_text_extents(cr, buf, &extents);

  while ((nul_pos > 5) && (extents.width +  places->text_size*1.3 > pixmap_width - places->text_size))
  {
    nul_pos--;
    buf[nul_pos] = '\0';
    strcat(buf, "..."); /*good enough*/
    cairo_text_extents(cr, buf, &extents);
  }

  cairo_show_text(cr, buf);

  g_free(buf);
  cairo_destroy(cr);

  if (gradient)
    cairo_pattern_destroy(gradient);

  if (pbuf)
    g_object_unref(pbuf);

  if (pover)
    g_object_unref(pover);

  return widget;
}

void render_entry(Menu_Item *entry)
{
  Places * places = entry->places;
  int max_width = places->max_width;
  GtkIconTheme*  g;
  GdkPixbuf *pbuf = NULL;
  gchar * filename;
  g = gtk_icon_theme_get_default();
  pbuf = gtk_icon_theme_load_icon(g, entry->icon, places->text_size, 0, NULL);

  if (!pbuf)
  {
    pbuf = gdk_pixbuf_new_from_file_at_size(entry->icon, -1, places->text_size, NULL);
  }

  if (!pbuf)
  {
    pbuf = gtk_icon_theme_load_icon(g, entry->text, places->text_size, 0, NULL);
  }

  if (!pbuf)
  {
    pbuf = gtk_icon_theme_load_icon(g, entry->exec, places->text_size, 0, NULL);
  }

  if (!pbuf)
  {
    filename = g_strdup_printf("/usr/share/pixmaps/%s", entry->icon);
    pbuf = gdk_pixbuf_new_from_file_at_size(filename, -1, places->text_size, NULL);
    g_free(filename);
  }

  if (!pbuf)
  {
    filename = g_strdup_printf("/usr/share/pixmaps/%s.svg", entry->icon);
    pbuf = gdk_pixbuf_new_from_file_at_size(filename, -1, places->text_size, NULL);
    g_free(filename);
  }

  if (!pbuf)
  {
    filename = g_strdup_printf("/usr/share/pixmaps/%s.png", entry->icon);
    pbuf = gdk_pixbuf_new_from_file_at_size(filename, -1, places->text_size, NULL);
    g_free(filename);
  }

  if (!pbuf)
  {
    filename = g_strdup_printf("/usr/share/pixmaps/%s.xpm", entry->icon);
    pbuf = gdk_pixbuf_new_from_file_at_size(filename, -1, places->text_size, NULL);
    g_free(filename);
  }

  if (!pbuf)
  {
    pbuf = gtk_icon_theme_load_icon(g, "applications-other", places->text_size, 0, NULL);
  }

  if (!pbuf)
  {
    pbuf = gtk_icon_theme_load_icon(g, "application-x-executable", places->text_size, 0, NULL);
  }

  entry->widget = gtk_event_box_new();

  gtk_event_box_set_visible_window(GTK_EVENT_BOX(entry->widget), FALSE);
  gtk_event_box_set_above_child(GTK_EVENT_BOX(entry->widget), TRUE);
  entry->normal = build_menu_widget(places, &places->normal_colours, entry->text, pbuf, NULL, max_width);
  entry->hover = build_menu_widget(places, &places->hover_colours, entry->text, pbuf, NULL, max_width);
  g_object_ref(entry->normal);
  gtk_container_add(GTK_CONTAINER(entry->widget), entry->normal);

  if (pbuf)
    g_object_unref(pbuf);
}

GtkWidget * get_blank(Places * places)
{
  int max_width = places->max_width;
  static cairo_t *cr = NULL;
  GdkScreen* pScreen;
  GdkPixmap * pixmap;
  GdkColormap* cmap;
  GtkWidget * widget;

  if (places->border_width > 0)
  {
    pixmap = gdk_pixmap_new(NULL, max_width, places->border_width, 32);
  }
  else
  {
    pixmap = gdk_pixmap_new(NULL, max_width, 1, 32);
  }

  widget = gtk_image_new_from_pixmap(pixmap, NULL);

  pScreen = gtk_widget_get_screen(GTK_WIDGET(places->applet));
  cmap = gdk_screen_get_rgba_colormap(pScreen);

  if (!cmap)
    cmap = gdk_screen_get_rgb_colormap(pScreen);

  gdk_drawable_set_colormap(pixmap, cmap);

  cr = gdk_cairo_create(pixmap);

  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);

  cairo_paint(cr);

  if (places->border_width > 0)
  {
    awn_cairo_set_source_color(cr, places->border_colour);
    cairo_set_operator(cr, CAIRO_OPERATOR_SOURCE);
  }
  else
  {

    awn_cairo_set_source_color_with_alpha_multiplier(cr, places->border_colour, 0);
  }

  cairo_paint(cr);

  cairo_destroy(cr);
  g_object_unref(pixmap);
  return widget;
}

void measure_width(Menu_Item * menu_item)
{
  static cairo_t *cr = NULL;
  static cairo_surface_t*  surface;
  cairo_text_extents_t    extents;
  Places * places = menu_item->places;

  if (!cr)
  {
    surface = cairo_image_surface_create(CAIRO_FORMAT_ARGB32, places->text_size * 40, places->text_size * 1.6);
    cr = cairo_create(surface);
  }

  cairo_select_font_face(cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);

  cairo_set_font_size(cr, places->text_size);
  cairo_text_extents(cr, menu_item->text, &extents);

  if (extents.width + places->text_size*2.5 > places->max_width)
  {
    places->max_width = extents.width + places->text_size * 2.5;
  }
}


static gboolean _enter_notify_event_entry(GtkWidget *widget, GdkEventCrossing *event, Menu_Item * item)
{
  g_object_ref(item->hover);
  gtk_container_remove(GTK_CONTAINER(widget), gtk_bin_get_child(GTK_BIN(widget)));
  gtk_container_add(GTK_CONTAINER(widget), item->hover);
  gtk_widget_show_all(item->hover);
  gtk_widget_show_all(widget);
  return TRUE;
}

static gboolean _leave_notify_event_entry(GtkWidget *widget, GdkEventCrossing *event, Menu_Item * item)
{
  g_object_ref(item->normal);
  gtk_container_remove(GTK_CONTAINER(widget), gtk_bin_get_child(GTK_BIN(widget)));
  gtk_container_add(GTK_CONTAINER(widget), item->normal);
  gtk_widget_show_all(item->normal);
  gtk_widget_show_all(widget);
  return TRUE;
}

static gboolean _button_do_event(GtkWidget *widget, GdkEventButton *event, Menu_Item * item)
{
  GError *err = NULL;
  g_spawn_command_line_async(item->exec, &err);
  gtk_widget_hide(item->places->mainwindow);
  return TRUE;
}

static void render_menu_widgets(Menu_Item * item, Places * places)
{
  render_entry(item);
#if GTK_CHECK_VERSION(2,12,0)

  if (places->show_tooltips)
    if (item->comment)
      gtk_widget_set_tooltip_text(item->widget, item->comment);

#endif
  g_signal_connect(G_OBJECT(item->widget), "enter-notify-event", G_CALLBACK(_enter_notify_event_entry), item);

  g_signal_connect(G_OBJECT(item->widget), "leave-notify-event", G_CALLBACK(_leave_notify_event_entry), item);

  g_signal_connect(G_OBJECT(item->widget), "button-release-event", G_CALLBACK(_button_do_event), item);

  gtk_box_pack_start(GTK_BOX(places->vbox), item->widget, FALSE, FALSE, 0);
}

static void render_places(Places * places)
{
  get_places(places);
  places->max_width = 0;
  g_slist_foreach(places->menu_list, (GFunc)measure_width, places);
  gtk_box_pack_start(GTK_BOX(places->vbox), get_blank(places), FALSE, FALSE, 0);
  g_slist_foreach(places->menu_list, (GFunc)render_menu_widgets, places);
  gtk_box_pack_end(GTK_BOX(places->vbox), get_blank(places), FALSE, FALSE, 0);
}



//****************************************************************************************************

//FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME FIXME



typedef struct
{
  GtkWidget *gtk_off_table;
  GtkWidget * hover_ex;
  GtkWidget * normal_ex;
  GtkWidget * prefs_win;
  GdkColormap *colormap;
  GdkScreen *screen;
  gchar * tmp;
  GtkWidget* vbox;
  GtkWidget * gtk;
  GtkWidget * tooltips;
  GtkWidget* gtk_off_section;
  GtkWidget *normal_label;
  GdkColor  colr;
  GtkWidget *normal_bg;
  GtkWidget *normal_fg;
  Places  *places;
  GtkWidget *hover_bg;
  GtkWidget *hover_fg;
  GtkWidget *hover_label;
  GtkWidget *border_label;
  GtkWidget *border_colour;
  GtkWidget * text_table;
  GtkWidget * filemanager;
  GtkWidget * adjust_gradient;

  GtkWidget * adjust_textsize;
  GtkWidget * adjust_borderwidth;

  GtkWidget* buttons;
  GtkWidget* ok;
  Menu_item_color mic;
}Pref_menu;


Pref_menu  *pref_menu = NULL;

static gboolean _press_ok(GtkWidget *widget, GdkEventButton *event, GtkWidget * win)
{
  save_config(pref_menu->places);
  gtk_widget_destroy(win);
  _do_update_places(pref_menu->places);
  g_free(pref_menu);
  return FALSE;
}


static gboolean _toggle_(GtkWidget *widget, gboolean * value)
{
  *value = !*value;

  return FALSE;
}

static gboolean _toggle_gtk(GtkWidget *widget, GtkWidget * gtk_off_section)
{
// gtk_toggle_button_set_active(widget,G_cairo_menu_conf.honour_gtk);
  pref_menu->places->honour_gtk = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));

  if (pref_menu->places->honour_gtk)
  {
    gtk_widget_hide(pref_menu->gtk_off_section);
  }
  else
  {
    gtk_widget_show_all(pref_menu->gtk_off_section);
  }

  return TRUE;
}

int activate(GtkWidget *w, gchar **p)
{
  gchar * svalue = *p;
  g_free(svalue);
  svalue = g_filename_to_utf8(gtk_entry_get_text(GTK_ENTRY(w)) , -1, NULL, NULL, NULL);
  *p = svalue;
  return FALSE;
}

void _mod_colour(GtkColorButton *widget, DesktopAgnosticColor * user_data)
{
  GdkColor *color;
  gtk_color_button_get_color(widget, color);
  desktop_agnostic_color_set_color(user_data, color);
  user_data->alpha = gtk_color_button_get_alpha(widget);
  gtk_widget_destroy(pref_menu->hover_ex);
  gtk_widget_destroy(pref_menu->normal_ex);
  pref_menu->hover_ex = build_menu_widget(pref_menu->places, &pref_menu->places->hover_colours, "Hover", NULL, NULL, 200);
  pref_menu->normal_ex = build_menu_widget(pref_menu->places, &pref_menu->places->normal_colours, "Normal", NULL, NULL, 200);

  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->normal_ex, 3, 4, 0, 1);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->hover_ex, 3, 4, 1, 2);
  gtk_widget_show(pref_menu->hover_ex);
  gtk_widget_show(pref_menu->normal_ex);
}

void spin_change(GtkSpinButton *spinbutton, double * val)
{
  *val = gtk_spin_button_get_value(spinbutton);
}

void spin_int_change(GtkSpinButton *spinbutton, int * val)
{
  *val = gtk_spin_button_get_value(spinbutton);
}


void _file_set(GtkFileChooserButton *filechooserbutton, gchar **p)
{
  gchar * svalue = *p;
  gchar * tmp;
  g_free(svalue);
  tmp = gtk_file_chooser_get_filename(GTK_FILE_CHOOSER(filechooserbutton));
  svalue = g_filename_to_utf8(tmp, -1, NULL, NULL, NULL) ;
  g_free(tmp);
  *p = svalue;

}


void show_prefs(Places * places)
{
  pref_menu = g_malloc(sizeof(Pref_menu));

  pref_menu->places = places;
  pref_menu->prefs_win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  pref_menu->screen = gtk_window_get_screen(GTK_WINDOW(pref_menu->prefs_win));
  pref_menu->colormap = gdk_screen_get_rgba_colormap(pref_menu->screen);

  if (pref_menu->colormap != NULL && gdk_screen_is_composited(pref_menu->screen))
  {
    gtk_widget_set_colormap(pref_menu->prefs_win, pref_menu->colormap);
  }

  gtk_window_set_title(GTK_WINDOW(pref_menu->prefs_win), "Places Preferences");

  pref_menu->vbox = gtk_vbox_new(FALSE, 0);
  pref_menu->gtk = gtk_check_button_new_with_label("Use Gtk");
  pref_menu->tooltips = gtk_check_button_new_with_label("Show tooltips");

  pref_menu->gtk_off_section = gtk_vbox_new(FALSE, 0);
  pref_menu->gtk_off_table = gtk_table_new(2, 4, FALSE);

  pref_menu->normal_label = gtk_label_new("Normal");

  desktop_agnostic_color_get_color(places->normal_colours.base, &pref_menu->colr);
  pref_menu->normal_bg = gtk_color_button_new_with_color(&pref_menu->colr);
  gtk_color_button_set_use_alpha(GTK_COLOR_BUTTON(pref_menu->normal_bg), TRUE);
  gtk_color_button_set_alpha(GTK_COLOR_BUTTON(pref_menu->normal_bg), places->normal_colours.base->alpha);
  g_signal_connect(G_OBJECT(pref_menu->normal_bg), "color-set", G_CALLBACK(_mod_colour), &places->normal_colours.base);
  desktop_agnostic_color_get_color(places->normal_colours.text, &pref_menu->colr);
  pref_menu->normal_fg = gtk_color_button_new_with_color(&pref_menu->colr);
  gtk_color_button_set_use_alpha(GTK_COLOR_BUTTON(pref_menu->normal_fg), TRUE);
  gtk_color_button_set_alpha(GTK_COLOR_BUTTON(pref_menu->normal_fg), places->normal_colours.text->alpha);
  g_signal_connect(G_OBJECT(pref_menu->normal_fg), "color-set", G_CALLBACK(_mod_colour), &places->normal_colours.text);

  pref_menu->hover_label = gtk_label_new("Hover");
  desktop_agnostic_color_get_color(places->hover_colours.base, &pref_menu->colr);
  pref_menu->hover_bg = gtk_color_button_new_with_color(&pref_menu->colr);
  gtk_color_button_set_use_alpha(GTK_COLOR_BUTTON(pref_menu->hover_bg), TRUE);
  gtk_color_button_set_alpha(GTK_COLOR_BUTTON(pref_menu->hover_bg), places->hover_colours.base->alpha);
  g_signal_connect(G_OBJECT(pref_menu->hover_bg), "color-set", G_CALLBACK(_mod_colour), &places->hover_colours.base);

  desktop_agnostic_color_get_color(places->hover_colours.text, &pref_menu->colr);
  pref_menu->hover_fg = gtk_color_button_new_with_color(&pref_menu->colr);
  gtk_color_button_set_use_alpha(GTK_COLOR_BUTTON(pref_menu->hover_fg), TRUE);
  gtk_color_button_set_alpha(GTK_COLOR_BUTTON(pref_menu->hover_fg), places->hover_colours.text->alpha);
  g_signal_connect(G_OBJECT(pref_menu->hover_fg), "color-set", G_CALLBACK(_mod_colour), &places->hover_colours.text);

  pref_menu->border_label = gtk_label_new("Border");

  desktop_agnostic_color_get_color(places->border_colour, &pref_menu->colr);
  pref_menu->border_colour = gtk_color_button_new_with_color(&pref_menu->colr);
  gtk_color_button_set_use_alpha(GTK_COLOR_BUTTON(pref_menu->border_colour), TRUE);
  gtk_color_button_set_alpha(GTK_COLOR_BUTTON(pref_menu->border_colour), places->border_colour->alpha);
  g_signal_connect(G_OBJECT(pref_menu->border_colour), "color-set", G_CALLBACK(_mod_colour), &places->border_colour);


  pref_menu->text_table = gtk_table_new(2, 4, FALSE);
  pref_menu->filemanager = gtk_file_chooser_button_new("File Manager", GTK_FILE_CHOOSER_ACTION_OPEN);
  pref_menu->tmp = g_filename_from_utf8(places->file_manager, -1, NULL, NULL, NULL) ;
  gtk_file_chooser_set_filename(GTK_FILE_CHOOSER(pref_menu->filemanager), pref_menu->tmp);
  g_free(pref_menu->tmp);

  pref_menu->adjust_gradient = gtk_spin_button_new_with_range(0.0, 1.0, 0.01);

  pref_menu->adjust_textsize = gtk_spin_button_new_with_range(4, 40, 1);
  pref_menu->adjust_borderwidth = gtk_spin_button_new_with_range(0, 10, 1);

  pref_menu->buttons = gtk_hbox_new(FALSE, 0);
  pref_menu->ok = gtk_button_new_with_label("Ok");

  pref_menu->mic.base = places->normal_colours.base;
  pref_menu->mic.text = places->normal_colours.text;
  pref_menu->normal_ex = build_menu_widget(places, &pref_menu->mic, "Normal", NULL, NULL, 200);

  pref_menu->mic.base = places->hover_colours.base;
  pref_menu->mic.text = places->hover_colours.text;
  pref_menu->hover_ex = build_menu_widget(places, &pref_menu->mic, "Hover", NULL, NULL, 200);

  gtk_window_set_keep_above(GTK_WINDOW(pref_menu->prefs_win), TRUE);
  gtk_window_set_accept_focus(GTK_WINDOW(pref_menu->prefs_win), TRUE);
  gtk_window_set_focus_on_map(GTK_WINDOW(pref_menu->prefs_win), TRUE);

  gtk_spin_button_set_value(GTK_SPIN_BUTTON(pref_menu->adjust_gradient), places->menu_item_gradient_factor);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(pref_menu->adjust_textsize), places->text_size);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(pref_menu->adjust_borderwidth), places->border_width);
  g_signal_connect(G_OBJECT(pref_menu->adjust_gradient), "value-changed", G_CALLBACK(spin_change),
                   &places->menu_item_gradient_factor);
  g_signal_connect(G_OBJECT(pref_menu->adjust_textsize), "value-changed", G_CALLBACK(spin_int_change),
                   &places->text_size);
  g_signal_connect(G_OBJECT(pref_menu->adjust_borderwidth), "value-changed", G_CALLBACK(spin_int_change),
                   &places->border_width);

  g_signal_connect(G_OBJECT(pref_menu->filemanager), "file-set", G_CALLBACK(_file_set), &places->file_manager);

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(pref_menu->gtk), places->honour_gtk);

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(pref_menu->tooltips), places->show_tooltips);
  g_signal_connect(G_OBJECT(pref_menu->tooltips), "toggled", G_CALLBACK(_toggle_), &places->show_tooltips);

  g_signal_connect(G_OBJECT(pref_menu->ok), "button-press-event", G_CALLBACK(_press_ok), pref_menu->prefs_win);

  gtk_container_add(GTK_CONTAINER(pref_menu->prefs_win), pref_menu->vbox);

  g_signal_connect(G_OBJECT(pref_menu->gtk), "toggled", G_CALLBACK(_toggle_gtk), pref_menu->gtk_off_section);

  gtk_box_pack_start(GTK_BOX(pref_menu->vbox), pref_menu->tooltips,   FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(pref_menu->vbox), pref_menu->text_table, FALSE, FALSE, 0);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->text_table), gtk_label_new("File Manager"),   0, 1, 1, 2);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->text_table), pref_menu->filemanager,          1, 2, 1, 2);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->text_table), gtk_label_new("Font Size (px)"), 0, 1, 3, 4);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->text_table), pref_menu->adjust_textsize,      1, 2, 3, 4);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->text_table), gtk_label_new("Border Width"),   0, 1, 4, 5);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->text_table), pref_menu->adjust_borderwidth,   1, 2, 4, 5);

  gtk_box_pack_start(GTK_BOX(pref_menu->vbox), pref_menu->gtk, FALSE, FALSE, 0);

  gtk_box_pack_start(GTK_BOX(pref_menu->vbox),            pref_menu->gtk_off_section, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(pref_menu->gtk_off_section), pref_menu->gtk_off_table,   FALSE, FALSE, 0);

  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->normal_label, 0, 1, 0, 1);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->normal_bg,    1, 2, 0, 1);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->normal_fg,    2, 3, 0, 1);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->normal_ex,    3, 4, 0, 1);

  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->hover_label, 0, 1, 1, 2);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->hover_bg,    1, 2, 1, 2);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->hover_fg,    2, 3, 1, 2);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->hover_ex,    3, 4, 1, 2);

  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->border_label,  0, 1, 2, 3);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->border_colour, 2, 3, 2, 3);

  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), gtk_label_new("Gradient Factor"), 0, 1, 3, 4);
  gtk_table_attach_defaults(GTK_TABLE(pref_menu->gtk_off_table), pref_menu->adjust_gradient,       2, 3, 3, 4);

  gtk_box_pack_start(GTK_BOX(pref_menu->vbox),    pref_menu->buttons, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(pref_menu->buttons), pref_menu->ok,      FALSE, FALSE, 0);
  gtk_widget_show_all(pref_menu->prefs_win);

  if (places->honour_gtk)
  {
    gtk_widget_hide(pref_menu->gtk_off_section);
  }
}




static gboolean _show_prefs(GtkWidget *widget, GdkEventButton *event, Places * places)
{
  show_prefs(places);
  return TRUE;
}

//****************************************************************************************************
//-------------------------------------------------------------------------


static gboolean _expose_event(GtkWidget *widget, GdkEventExpose *expose, Places * places)
{
  cairo_t *cr;
  GdkEvent *evt;

  cr = gdk_cairo_create(widget->window);
  cairo_set_operator(cr, CAIRO_OPERATOR_CLEAR);
  cairo_paint(cr);
  evt = g_malloc(sizeof(GdkEvent));
  evt->expose = *expose;
  gtk_widget_send_expose(places->vbox, evt);
  g_free(evt);
  cairo_destroy(cr);
  return TRUE;
}


void pos_dialog(GtkWidget * window, Places *places)
{
  gint x, y;
  gdk_window_get_origin(GTK_WIDGET(places->applet)->window, &x, &y);
  gtk_window_move(GTK_WINDOW(window), x, y - window->allocation.height + GTK_WIDGET(places->applet)->allocation.height / 3);

}


static GtkWidget * menu_new(Places *places)
{
  GdkColormap *colormap;
  GdkScreen *screen;
  GtkWidget *win = gtk_window_new(GTK_WINDOW_TOPLEVEL);

  gtk_window_set_type_hint(GTK_WINDOW(win), GDK_WINDOW_TYPE_HINT_DIALOG);
  gtk_window_set_skip_taskbar_hint(GTK_WINDOW(win), TRUE);

  gtk_window_set_decorated(GTK_WINDOW(win), FALSE);
  gtk_window_set_accept_focus(GTK_WINDOW(win), TRUE);
  gtk_window_set_focus_on_map(GTK_WINDOW(win), TRUE);
  gtk_window_set_keep_above(GTK_WINDOW(win), TRUE);
  gtk_window_set_skip_pager_hint(GTK_WINDOW(win), TRUE);
  gtk_window_stick(GTK_WINDOW(win));

// gtk_window_set_opacity(GTK_WINDOW (win),0.0);
  screen = gtk_window_get_screen(GTK_WINDOW(win));
  colormap = gdk_screen_get_rgba_colormap(screen);

  if (colormap != NULL && gdk_screen_is_composited(screen))
  {
    gtk_widget_set_colormap(win, colormap);
  }

  gtk_widget_set_events(win, GDK_BUTTON_PRESS_MASK | GDK_BUTTON_RELEASE_MASK | GDK_FOCUS_CHANGE_MASK | GDK_POINTER_MOTION_MASK);

  gtk_widget_set_app_paintable(win, TRUE);


  return win;

}




static gboolean _button_clicked_event(GtkWidget *widget, GdkEventButton *event, Places * places)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;

  if (event->button == 1)
  {
    /*the gtk_window_set_opacity is a hack because the mainwindow window flickers,
       visibly, briefly on the screen sometimes without it*/
    if (GTK_WIDGET_VISIBLE(places->mainwindow))
    {
      gtk_widget_hide(places->mainwindow);
    }
    else
    {
      gtk_widget_show_all(places->mainwindow);
      pos_dialog(places->mainwindow, places);
//      awn_applet_simple_set_title_visibility(AWN_APPLET_SIMPLE(places->applet),FALSE);
    }
  }
  else if (event->button == 3)
  {
    static GtkWidget * menu = NULL;
    static GtkWidget * item;

    if (!menu)
    {
      menu = awn_applet_create_default_menu(AWN_APPLET(places->applet));
      item = gtk_menu_item_new_with_label("Preferences");
      gtk_widget_show(item);
      gtk_menu_set_screen(GTK_MENU(menu), NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);
      g_signal_connect(G_OBJECT(item), "button-press-event", G_CALLBACK(_show_prefs), places);
      item = awn_applet_create_about_item_simple (AWN_APPLET(places->applet),
                                                  "Copyright 2007,2008 Rodney Cryderman <rcryderman@gmail.com>\n"
                                                  "Copyright 2007,2008 Mark Lee <avant-wn@lazymalevolence.com>\n",
                                                  AWN_APPLET_LICENSE_GPLV2,
                                                  NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);
    }

    gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL, event_button->button, event_button->time);
  }

  return TRUE;
}

static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event, Places * places)
{

  DesktopAgnosticConfigClient *client = awn_config_get_default(AWN_PANEL_ID_DEFAULT, NULL);
  if (desktop_agnostic_config_client_get_bool(client, "shared", "dialog_focus_loss_behavior", NULL))
  {
    gtk_widget_hide(places->mainwindow);
  }

  return TRUE;
}

static void _bloody_thing_has_style(GtkWidget *widget, Places *places)
{
  init_config(places);

  //The EASY way to use awn icons.
  awn_applet_simple_set_icon_name(AWN_APPLET_SIMPLE(places->applet),
                                  places->applet_icon_name)  ;
  awn_applet_simple_set_tooltip_text(AWN_APPLET_SIMPLE(places->applet), "Places");

  render_places(places);
  g_signal_connect(G_OBJECT(places->applet), "button-press-event", G_CALLBACK(_button_clicked_event), places);
  g_signal_connect(G_OBJECT(places->mainwindow), "focus-out-event", G_CALLBACK(_focus_out_event), places);
  g_signal_connect(G_OBJECT(places->mainwindow), "expose-event", G_CALLBACK(_expose_event), places);
}

AwnApplet* awn_applet_factory_initp(const gchar *name,
                                    const gchar *uid, gint panel_id)
{
  g_on_error_stack_trace(NULL);
  Places * places = g_malloc(sizeof(Places));
  GtkWidget *applet = places->applet = awn_applet_simple_new(name, uid, panel_id);
  g_object_set (applet,
                "display-name","Places",
                NULL);
  gtk_widget_set_size_request(GTK_WIDGET(applet), awn_applet_get_size(AWN_APPLET(applet)), -1);

  places->applet_icon_height = awn_applet_get_size(AWN_APPLET(applet)) - 2;


  /* gtk_widget_show_all(GTK_WIDGET(applet));*/
  places->mainwindow = menu_new(places);
  gtk_window_set_focus_on_map(GTK_WINDOW(places->mainwindow), TRUE);
  places->vbox = gtk_vbox_new(FALSE, 0);
  gtk_container_add(GTK_CONTAINER(places->mainwindow), places->vbox);
  g_signal_connect_after(G_OBJECT(places->applet), "map", G_CALLBACK(_bloody_thing_has_style), places);

  places->uid = g_strdup(uid);
  return AWN_APPLET(applet);

}

