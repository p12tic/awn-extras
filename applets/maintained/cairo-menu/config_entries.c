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

#include <string.h>
#include <stdlib.h>
#include <unistd.h>

#include <glib.h>
#include <libdesktop-agnostic/gtk.h>
#include <libawn/libawn.h>

#include "config_entries.h"
#include "render.h"

Cairo_menu_config G_cairo_menu_conf;

static Cairo_menu_config G_cairo_menu_conf_copy;

static DesktopAgnosticConfigClient *config = NULL;

extern AwnApplet *G_applet;

/* FIXME does not support multiple taskmanagers */
void append_to_launchers(gchar * launcher)
{
  GError *err = NULL;
  DesktopAgnosticConfigClient *taskmanager;
  GValueArray *launchers;

  taskmanager = awn_config_get_default_for_applet_by_info ("taskmanager",
                                                                  "1", &err);
  if (err)
  {
    goto add_to_launchers_error;
  }
  launchers = desktop_agnostic_config_client_get_list (config,
                                                       DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                                       "launcher_paths", &err);
  if (err)
  {
    goto add_to_launchers_error;
  }
  else if (launchers)
  {
    GValue val;

    g_value_init (&val, G_TYPE_STRING);
    g_value_set_string (&val, launcher);
    g_value_array_append(launchers, &val);
    g_value_unset (&val);
    desktop_agnostic_config_client_set_list (config,
                                             DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                             "launcher_paths", launchers, &err);
    g_value_array_free (launchers);
    if (err)
    {
      goto add_to_launchers_error;
    }
  }

add_to_launchers_error:
  if (err)
  {
    g_critical ("Could not add launcher: %s", err->message);
    g_error_free (err);
  }
  return;
}

/* returns a new reference */
static DesktopAgnosticColor*
config_get_color (DesktopAgnosticConfigClient *cfg, const gchar *key,
                  GError **error)
{
  GValue value;
  DesktopAgnosticColor *color;

  value = desktop_agnostic_config_client_get_value (cfg,
                                                    DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                                    key, error);
  if (!G_VALUE_HOLDS_OBJECT (&value) || (error && *error))
  {
    return NULL;
  }
  else
  {
    color = (DesktopAgnosticColor*)g_value_dup_object (&value);
    g_value_unset (&value);
    return color;
  }
}

#define config_get_value(prop, type, key) \
  G_cairo_menu_conf.prop = desktop_agnostic_config_client_get_##type (config, \
                                                                        DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, \
                                                                        key, \
                                                                        &err); \
  if (err) \
  { \
    goto read_config_error; \
  }

void read_config(void)
{
  GError *err = NULL;
  GValue *value;
  config = awn_config_get_default_for_applet (G_applet, &err);
  if (err)
  {
    goto read_config_error;
  }

  G_cairo_menu_conf.normal.bg = config_get_color (config, CONF_NORMAL_BG, &err);
  if (err)
  {
    goto read_config_error;
  }

  G_cairo_menu_conf.normal.fg = config_get_color (config, CONF_NORMAL_FG, &err);
  if (err)
  {
    goto read_config_error;
  }

  G_cairo_menu_conf.hover.bg = config_get_color (config, CONF_HOVER_BG, &err);
  if (err)
  {
    goto read_config_error;
  }

  G_cairo_menu_conf.hover.fg = config_get_color (config, CONF_HOVER_FG, &err);
  if (err)
  {
    goto read_config_error;
  }

  config_get_value (text_size, int, CONF_TEXT_SIZE);
  config_get_value (show_search, bool, CONF_SHOW_SEARCH);
  config_get_value (search_cmd, string, CONF_SEARCH_CMD);

  if (!G_cairo_menu_conf.search_cmd ||
      g_strcmp0 (G_cairo_menu_conf.search_cmd, "") == 0)
  {
    gchar *search_cmd;

    search_cmd = g_find_program_in_path("tracker-search-tool");

    if (!search_cmd)
    {
      search_cmd = g_find_program_in_path("beagle-search");
    }

    if (!search_cmd)
    {
      search_cmd = g_strdup("terminal -x locate");
    }

    desktop_agnostic_config_client_set_string (config,
                                               DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                               CONF_SEARCH_CMD, search_cmd, &err);
    if (err)
    {
      g_free (search_cmd);
      goto read_config_error;
    }
    G_cairo_menu_conf.search_cmd = search_cmd;
  }

  config_get_value (menu_item_gradient_factor, float, CONF_MENU_GRADIENT);
  config_get_value (menu_item_text_len, int, CONF_MENU_ITEM_TEXT_LEN);
  config_get_value (show_run, bool, CONF_SHOW_RUN);
  config_get_value (do_fade, bool, CONF_DO_FADE);
  config_get_value (show_places, bool, CONF_SHOW_PLACES);
  config_get_value (filemanager, string, CONF_FILEMANAGER);

  if (!G_cairo_menu_conf.filemanager ||
      g_strcmp0 (G_cairo_menu_conf.filemanager, "") == 0)
  {
    gchar *filemanager;

    filemanager = g_find_program_in_path("xdg-open");

    if (!filemanager)
    {
      filemanager = g_find_program_in_path("nautilus");
    }

    if (!filemanager)
    {
      filemanager = g_find_program_in_path ("thunar");
    }

    if (!filemanager)
    {
      /* give up, they need xdg-open. */
      filemanager = g_strdup ("xdg-open");
    }

    desktop_agnostic_config_client_set_string (config,
                                               DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                               CONF_FILEMANAGER, filemanager,
                                               &err);
    if (err)
    {
      g_free (filemanager);
      goto read_config_error;
    }
    G_cairo_menu_conf.filemanager = filemanager;
  }

  config_get_value (applet_icon, string, CONF_APPLET_ICON);
  config_get_value (on_button_release, bool, CONF_ON_BUTTON_RELEASE);
  config_get_value (show_tooltips, bool, CONF_SHOW_TOOLTIPS);
  config_get_value (logout, string, CONF_LOGOUT);

  if (!G_cairo_menu_conf.logout ||
      g_strcmp0 (G_cairo_menu_conf.logout, "") == 0)
  {
    gchar *logout;

    logout = g_find_program_in_path("closure");

    if (!logout)
    {

      logout = g_find_program_in_path("gnome-session-save");

      if (logout)
      {
        g_free (logout);
        logout = g_strdup("gnome-session-save --kill");
      }
      else
      {
        logout = g_strdup("closure");
      }
    }

    desktop_agnostic_config_client_set_string(config,
                                              DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                              CONF_LOGOUT, logout, &err);
    if (err)
    {
      g_free (logout);
      goto read_config_error;
    }
    G_cairo_menu_conf.logout = logout;
  }

  config_get_value (show_logout, bool, CONF_SHOW_LOGOUT);
  config_get_value (border_width, int, CONF_BORDER_WIDTH);
  G_cairo_menu_conf.border_colour = config_get_color (config, CONF_BORDER_COLOUR, &err);
  if (err)
  {
    goto read_config_error;
  }

  config_get_value (honour_gtk, bool, CONF_HONOUR_GTK);
  if (G_cairo_menu_conf.honour_gtk)
  {
    GtkWidget *top_win = GTK_WIDGET(G_applet);
    gushort alpha = (gushort)(0.9 * G_MAXUSHORT);

    G_cairo_menu_conf.normal.bg = desktop_agnostic_color_new(&top_win->style->bg[GTK_STATE_NORMAL], alpha);

    G_cairo_menu_conf.normal.fg = desktop_agnostic_color_new(&top_win->style->fg[GTK_STATE_ACTIVE], alpha);


    G_cairo_menu_conf.hover.bg = desktop_agnostic_color_new(&top_win->style->bg[GTK_STATE_ACTIVE], alpha);

    G_cairo_menu_conf.hover.fg = desktop_agnostic_color_new(&top_win->style->fg[GTK_STATE_ACTIVE], alpha);

    G_cairo_menu_conf.border_colour = desktop_agnostic_color_new(&top_win->style->text_aa[0], (gushort)(0.4 * G_MAXUSHORT));

    G_cairo_menu_conf.menu_item_gradient_factor = 1.0;
  }

read_config_error:
  if (err)
  {
    g_critical ("Could not read the configuration in its entirety: %s",
                err->message);
    g_error_free (err);
  }
  return;
}

static void
config_set_color (DesktopAgnosticConfigClient *cfg, const gchar *key,
                  DesktopAgnosticColor *color, GError **error)
{
  GValue value = { 0, };

  g_value_init (&value, DESKTOP_AGNOSTIC_TYPE_COLOR);
  g_value_set_object (&value, color);

  desktop_agnostic_config_client_set_value (cfg,
                                            DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                            key, &value, error);
  g_value_unset (&value);
}

#define config_set_value(prop, type, key) \
  desktop_agnostic_config_client_set_##type (config, \
                                             DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT, \
                                             key, G_cairo_menu_conf.prop, \
                                             &err); \
  if (err) \
  { \
    goto _save_config_error; \
  }

static void _save_config(void)
{
  GError *err = NULL;

  config_set_color (config, CONF_NORMAL_BG, G_cairo_menu_conf.normal.bg, &err);
  if (err)
  {
    goto _save_config_error;
  }

  config_set_color (config, CONF_NORMAL_FG, G_cairo_menu_conf.normal.fg, &err);
  if (err)
  {
    goto _save_config_error;
  }

  config_set_color (config, CONF_HOVER_BG, G_cairo_menu_conf.hover.bg, &err);
  if (err)
  {
    goto _save_config_error;
  }

  config_set_color (config, CONF_HOVER_FG, G_cairo_menu_conf.hover.fg, &err);
  if (err)
  {
    goto _save_config_error;
  }

  config_set_value (text_size, int, CONF_TEXT_SIZE);

  config_set_value (show_search, bool, CONF_SHOW_SEARCH);

  config_set_value (search_cmd, string, CONF_SEARCH_CMD);

  config_set_value (menu_item_gradient_factor, float, CONF_MENU_GRADIENT);

  config_set_value (menu_item_text_len, int, CONF_MENU_ITEM_TEXT_LEN);

  config_set_value (show_run, bool, CONF_SHOW_RUN);

  config_set_value (do_fade, bool, CONF_DO_FADE);

  config_set_value (show_places, bool, CONF_SHOW_PLACES);

  config_set_value (filemanager, string, CONF_FILEMANAGER);

  config_set_value (applet_icon, string, CONF_APPLET_ICON);

  config_set_value (on_button_release, bool, CONF_ON_BUTTON_RELEASE);

  config_set_value (honour_gtk, bool, CONF_HONOUR_GTK);

  config_set_value (show_tooltips, bool, CONF_SHOW_TOOLTIPS);

  config_set_value (show_logout, bool, CONF_SHOW_LOGOUT);

  config_set_value (logout, string, CONF_LOGOUT);

  config_set_value (border_width, int, CONF_BORDER_WIDTH);

  config_set_color (config, CONF_BORDER_COLOUR, G_cairo_menu_conf.border_colour,
                    &err);
  if (err)
  {
    goto _save_config_error;
  }

_save_config_error:
  if (err)
  {
    g_critical ("Could not save the configuration in its entirety: %s",
                err->message);
    g_error_free (err);
  }
}

static gboolean _press_ok(GtkWidget *widget, GdkEventButton *event, GtkWidget * win)
{
  _save_config();
  gtk_widget_destroy(win);
  GError *err = NULL;
  GtkWidget *dialog, *label;

  dialog = gtk_dialog_new_with_buttons("Cairo Menu Message",
                                       NULL,
                                       GTK_DIALOG_DESTROY_WITH_PARENT,
                                       GTK_STOCK_OK,
                                       GTK_RESPONSE_NONE,
                                       NULL);
  label = gtk_label_new("About to restart Cairo Menu.  Please shutdown any instances of awn-manager");

  /* Ensure that the dialog box is destroyed when the user responds. */

  g_signal_connect_swapped(dialog,
                           "response",
                           G_CALLBACK(gtk_widget_destroy),
                           dialog);
  gtk_container_add(GTK_CONTAINER(GTK_DIALOG(dialog)->vbox),
                    label);
  gtk_widget_show_all(dialog);
  gtk_dialog_run(GTK_DIALOG(dialog));
  g_spawn_command_line_async("/bin/sh -c 'export T_STAMP=`date +\"%s\"`&& export AWN_G_ORIG=`gconftool-2 -g /apps/avant-window-navigator/panel/applet_list | sed -e \"s/cairo_main_menu\\.desktop::[0-9]*/cairo_main_menu\\.desktop::$T_STAMP/\"` && export AWN_G_MOD=`echo $AWN_G_ORIG |sed -e \"s/[^,^\[]*cairo_main_menu\\.desktop::[0-9]*,?//\"` && gconftool-2 --type list --list-type=string -s /apps/avant-window-navigator/panel/applet_list \"$AWN_G_MOD\" && sleep 2 && gconftool-2 --type list --list-type=string -s /apps/avant-window-navigator/panel/applet_list \"$AWN_G_ORIG\"'", &err);
  exit(0);
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
  G_cairo_menu_conf.honour_gtk = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));

  if (G_cairo_menu_conf.honour_gtk)
  {
    gtk_widget_hide(gtk_off_section);
  }
  else
  {
    gtk_widget_show_all(gtk_off_section);
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

/*I'm lazy.. and I do not like doing pref dialogs....*/
GtkTable *gtk_off_table;
GtkWidget * hover_ex;
GtkWidget * normal_ex;

void _mod_colour(GtkColorButton *widget, DesktopAgnosticColor **color)
{
  DesktopAgnosticGTKColorButton *button;

  button = DESKTOP_AGNOSTIC_GTK_COLOR_BUTTON (widget);

  *color = g_object_ref (desktop_agnostic_gtk_color_button_get_da_color (button));
  gtk_widget_destroy(hover_ex);
  gtk_widget_destroy(normal_ex);
  hover_ex = build_menu_widget(&G_cairo_menu_conf.hover, "Hover", NULL, NULL, 200);
  normal_ex = build_menu_widget(&G_cairo_menu_conf.normal, "Normal", NULL, NULL, 200);

  gtk_table_attach_defaults(gtk_off_table, normal_ex, 3, 4, 0, 1);
  gtk_table_attach_defaults(gtk_off_table, hover_ex, 3, 4, 1, 2);
  gtk_widget_show(hover_ex);
  gtk_widget_show(normal_ex);
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
  tmp = gtk_file_chooser_get_filename(GTK_FILE_CHOOSER(filechooserbutton));

  if (tmp)
  {
    g_free(svalue);
    svalue = g_filename_to_utf8(tmp, -1, NULL, NULL, NULL) ;
    g_free(tmp);
    *p = svalue;
  }
}

void show_prefs(void)
{
  G_cairo_menu_conf_copy = G_cairo_menu_conf;

  GtkWidget * prefs_win = gtk_window_new(GTK_WINDOW_TOPLEVEL);
  GdkColormap *colormap;
  GdkScreen *screen;
  gchar * tmp;

  screen = gtk_window_get_screen(GTK_WINDOW(prefs_win));
  colormap = gdk_screen_get_rgba_colormap(screen);

  if (colormap != NULL && gdk_screen_is_composited(screen))
  {
    gtk_widget_set_colormap(prefs_win, colormap);
  }

  gtk_window_set_title(GTK_WINDOW(prefs_win), "Cairo Menu Preferences");

  GtkWidget* vbox = gtk_vbox_new(FALSE, 0);
  GtkWidget * gtk = gtk_check_button_new_with_label("Use Gtk");
  GtkWidget * places = gtk_check_button_new_with_label("Show Places");
  GtkWidget * search = gtk_check_button_new_with_label("Show Search");
  GtkWidget * run = gtk_check_button_new_with_label("Show Run");
  GtkWidget * logout = gtk_check_button_new_with_label("Show Logout");
  GtkWidget * fade_in = gtk_check_button_new_with_label("Fade in menu");
  GtkWidget * release = gtk_check_button_new_with_label("Activate On Release");
  GtkWidget * tooltips = gtk_check_button_new_with_label("Show tooltips");


  GtkWidget* gtk_off_section = gtk_vbox_new(FALSE, 0);
  gtk_off_table = GTK_TABLE(gtk_table_new(2, 4, FALSE));

  GtkWidget *normal_label = gtk_label_new("Normal");

  GtkWidget *normal_bg = GTK_WIDGET (desktop_agnostic_gtk_color_button_new_with_color(G_cairo_menu_conf.normal.bg));
  g_signal_connect(G_OBJECT(normal_bg), "color-set", G_CALLBACK(_mod_colour), &G_cairo_menu_conf.normal.bg);

  GtkWidget *normal_fg = GTK_WIDGET (desktop_agnostic_gtk_color_button_new_with_color(G_cairo_menu_conf.normal.fg));
  g_signal_connect(G_OBJECT(normal_fg), "color-set", G_CALLBACK(_mod_colour), &G_cairo_menu_conf.normal.fg);

  GtkWidget *hover_label = gtk_label_new("Hover");
// GtkWidget *hover_bg=gtk_button_new_with_label("Background");

  GtkWidget *hover_bg = GTK_WIDGET (desktop_agnostic_gtk_color_button_new_with_color(G_cairo_menu_conf.hover.bg));
  g_signal_connect(G_OBJECT(hover_bg), "color-set", G_CALLBACK(_mod_colour), &G_cairo_menu_conf.hover.bg);

// GtkWidget *hover_fg=gtk_button_new_with_label("Foreground");
  GtkWidget *hover_fg = GTK_WIDGET (desktop_agnostic_gtk_color_button_new_with_color(G_cairo_menu_conf.hover.fg));
  g_signal_connect(G_OBJECT(hover_fg), "color-set", G_CALLBACK(_mod_colour), &G_cairo_menu_conf.hover.fg);


  GtkWidget *border_label = gtk_label_new("Border");

  GtkWidget *border_colour = GTK_WIDGET (desktop_agnostic_gtk_color_button_new_with_color(G_cairo_menu_conf.border_colour));
  g_signal_connect(G_OBJECT(border_colour), "color-set", G_CALLBACK(_mod_colour), &G_cairo_menu_conf.border_colour);


  GtkTable * text_table = GTK_TABLE(gtk_table_new(2, 4, FALSE));
// GtkWidget * search_cmd=gtk_entry_new();
  GtkWidget * search_cmd = gtk_file_chooser_button_new("Search Util", GTK_FILE_CHOOSER_ACTION_OPEN);
// GtkWidget * filemanager=gtk_entry_new();
  GtkWidget * filemanager = gtk_file_chooser_button_new("File Manager", GTK_FILE_CHOOSER_ACTION_OPEN);
// gtk_file_chooser_set_current_folder (GTK_FILE_CHOOSER (filemanager),"/usr/bin");

  tmp = g_filename_from_utf8(G_cairo_menu_conf.filemanager, -1, NULL, NULL, NULL) ;
  gtk_file_chooser_set_filename(GTK_FILE_CHOOSER(filemanager), tmp);
  g_free(tmp);

  tmp = g_filename_from_utf8(G_cairo_menu_conf.search_cmd, -1, NULL, NULL, NULL) ;
  gtk_file_chooser_set_filename(GTK_FILE_CHOOSER(search_cmd), tmp);
  g_free(tmp);


  GtkWidget * adjust_gradient = gtk_spin_button_new_with_range(0.0, 1.0, 0.01);

  GtkWidget * adjust_textlen = gtk_spin_button_new_with_range(5, 30, 1);
  GtkWidget * adjust_textsize = gtk_spin_button_new_with_range(4, 40, 1);
  GtkWidget * adjust_borderwidth = gtk_spin_button_new_with_range(0, 10, 1);

  GtkWidget* buttons = gtk_hbox_new(FALSE, 0);
  GtkWidget* ok = gtk_button_new_with_label("Ok");

  Menu_item_color mic;
  mic.bg = G_cairo_menu_conf.normal.bg;
  mic.fg = G_cairo_menu_conf.normal.fg;
  normal_ex = build_menu_widget(&mic, "Normal", NULL, NULL, 200);

  mic.bg = G_cairo_menu_conf.hover.bg;
  mic.fg = G_cairo_menu_conf.hover.fg;
  hover_ex = build_menu_widget(&mic, "Hover", NULL, NULL, 200);


  gtk_window_set_keep_above(GTK_WINDOW(prefs_win), TRUE);
  gtk_window_set_accept_focus(GTK_WINDOW(prefs_win), TRUE);
  gtk_window_set_focus_on_map(GTK_WINDOW(prefs_win), TRUE);

  gtk_spin_button_set_value(GTK_SPIN_BUTTON(adjust_gradient), G_cairo_menu_conf.menu_item_gradient_factor);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(adjust_textlen), G_cairo_menu_conf.menu_item_text_len);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(adjust_textsize), G_cairo_menu_conf.text_size);
  gtk_spin_button_set_value(GTK_SPIN_BUTTON(adjust_borderwidth), G_cairo_menu_conf.border_width);
  g_signal_connect(G_OBJECT(adjust_gradient), "value-changed", G_CALLBACK(spin_change),
                   &G_cairo_menu_conf.menu_item_gradient_factor);
  g_signal_connect(G_OBJECT(adjust_textlen), "value-changed", G_CALLBACK(spin_int_change),
                   &G_cairo_menu_conf.menu_item_text_len);
  g_signal_connect(G_OBJECT(adjust_textsize), "value-changed", G_CALLBACK(spin_int_change),
                   &G_cairo_menu_conf.text_size);
  g_signal_connect(G_OBJECT(adjust_borderwidth), "value-changed", G_CALLBACK(spin_int_change),
                   &G_cairo_menu_conf.border_width);

  g_signal_connect(G_OBJECT(search_cmd), "file-set", G_CALLBACK(_file_set), &G_cairo_menu_conf.search_cmd);
  g_signal_connect(G_OBJECT(filemanager), "file-set", G_CALLBACK(_file_set), &G_cairo_menu_conf.filemanager);

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(gtk), G_cairo_menu_conf.honour_gtk);

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(search), G_cairo_menu_conf.show_search);
  g_signal_connect(G_OBJECT(search), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.show_search);
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(places), G_cairo_menu_conf.show_places);
  g_signal_connect(G_OBJECT(places), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.show_places);
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(release), G_cairo_menu_conf.on_button_release);
  g_signal_connect(G_OBJECT(release), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.on_button_release);
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(tooltips), G_cairo_menu_conf.show_tooltips);
  g_signal_connect(G_OBJECT(tooltips), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.show_tooltips);

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(run), G_cairo_menu_conf.show_run);
  g_signal_connect(G_OBJECT(run), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.show_run);
  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(logout), G_cairo_menu_conf.show_logout);
  g_signal_connect(G_OBJECT(logout), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.show_logout);

  gtk_toggle_button_set_active(GTK_TOGGLE_BUTTON(fade_in), G_cairo_menu_conf.do_fade);
  g_signal_connect(G_OBJECT(fade_in), "toggled", G_CALLBACK(_toggle_), &G_cairo_menu_conf.do_fade);


  g_signal_connect(G_OBJECT(ok), "button-press-event", G_CALLBACK(_press_ok), prefs_win);

  gtk_container_add(GTK_CONTAINER(prefs_win), vbox);

  g_signal_connect(G_OBJECT(gtk), "toggled", G_CALLBACK(_toggle_gtk), gtk_off_section);

  gtk_box_pack_start(GTK_BOX(vbox), search, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), places, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), run, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), logout, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), fade_in, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), release, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), tooltips, FALSE, FALSE, 0);

  gtk_box_pack_start(GTK_BOX(vbox), GTK_WIDGET(text_table), FALSE, FALSE, 0);
  gtk_table_attach_defaults(text_table, gtk_label_new("Search command"), 0, 1, 0, 1);
  gtk_table_attach_defaults(text_table, search_cmd, 1, 2, 0, 1);
  gtk_table_attach_defaults(text_table, gtk_label_new("File Manager"), 0, 1, 1, 2);
  gtk_table_attach_defaults(text_table, filemanager, 1, 2, 1, 2);
  gtk_table_attach_defaults(text_table, gtk_label_new("Approx. Max Chars (worst case)"), 0, 1, 2, 3);
  gtk_table_attach_defaults(text_table, adjust_textlen, 1, 2, 2, 3);
  gtk_table_attach_defaults(text_table, gtk_label_new("Font Size"), 0, 1, 3, 4);
  gtk_table_attach_defaults(text_table, adjust_textsize, 1, 2, 3, 4);
  gtk_table_attach_defaults(text_table, gtk_label_new("Border Width"), 0, 1, 4, 5);
  gtk_table_attach_defaults(text_table, adjust_borderwidth, 1, 2, 4, 5);

  gtk_box_pack_start(GTK_BOX(vbox), gtk, FALSE, FALSE, 0);

  gtk_box_pack_start(GTK_BOX(vbox), gtk_off_section, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(gtk_off_section), GTK_WIDGET(gtk_off_table), FALSE, FALSE, 0);

  gtk_table_attach_defaults(gtk_off_table, normal_label, 0, 1, 0, 1);
  gtk_table_attach_defaults(gtk_off_table, normal_bg, 1, 2, 0, 1);
  gtk_table_attach_defaults(gtk_off_table, normal_fg, 2, 3, 0, 1);
  gtk_table_attach_defaults(gtk_off_table, normal_ex, 3, 4, 0, 1);

  gtk_table_attach_defaults(gtk_off_table, hover_label, 0, 1, 1, 2);
  gtk_table_attach_defaults(gtk_off_table, hover_bg, 1, 2, 1, 2);
  gtk_table_attach_defaults(gtk_off_table, hover_fg, 2, 3, 1, 2);
  gtk_table_attach_defaults(gtk_off_table, hover_ex, 3, 4, 1, 2);

  gtk_table_attach_defaults(gtk_off_table, border_label, 0, 1, 2, 3);
  gtk_table_attach_defaults(gtk_off_table, border_colour, 2, 3, 2, 3);

  gtk_table_attach_defaults(gtk_off_table, gtk_label_new("Gradient Factor"), 0, 1, 3, 4);
  gtk_table_attach_defaults(gtk_off_table, adjust_gradient, 2, 3, 3, 4);



  gtk_box_pack_start(GTK_BOX(vbox), buttons, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(buttons), ok, FALSE, FALSE, 0);
  gtk_widget_show_all(prefs_win);

  if (G_cairo_menu_conf.honour_gtk)
  {
    gtk_widget_hide(gtk_off_section);
  }

}

// vim:ts=2:sts=2:sw=2:et:ai:cindent
