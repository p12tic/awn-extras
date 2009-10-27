/*
 * Copyright (C) 2008 Rodney Cryderman <rcryderman@gmail.com>
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

#include <glib.h>
#include <glib/gi18n.h>
#include <gtk/gtk.h>
#include <gdk/gdkkeysyms.h>

#include <libawn/libawn.h>

#include "engine_html.h"
#include "applet.h"
#include "configuration.h"

#define ICON_NAME "applications-internet"

typedef struct
{
  WebApplet *webapplet;
  gchar *url;
  gchar *icon;
  gchar *name;
  gint width;
  gint height;
} WebSite;

static void
set_title(WebApplet *webapplet, const gchar *uri)
{
  gchar *title = NULL;

  if (g_str_has_prefix(uri, "http://"))
    title = g_strdup(uri + 7);

  else if (g_str_has_prefix(uri, "https://"))
    title = g_strdup(uri + 8);

  else
    title = g_strdup(uri);

  /* Truncate at any '/' */
  title[strcspn(title, "/")] = '\0';

  awn_applet_simple_set_tooltip_text(AWN_APPLET_SIMPLE(webapplet->applet),
                                     title);

  g_free(title);
}

static void
go_to_url(WebApplet *webapplet, gchar *url)
{
  html_web_view_open(webapplet->viewer, url);

  gtk_widget_show(webapplet->viewer);

  if (GTK_IS_WIDGET(webapplet->start))
    gtk_widget_destroy(webapplet->start);

  gtk_widget_set_size_request(GTK_WIDGET(webapplet->box),
                              config_get_width(webapplet),
                              config_get_height(webapplet));

  set_title(webapplet, (const gchar*)url);
}

static void
site_clicked(GtkButton *button, WebSite *site)
{
  go_to_url(site->webapplet, site->url);

  gint size = awn_applet_get_size(site->webapplet->applet);

  gchar *path = g_strdup_printf(APPLETSDIR"/webapplet/icons/%s", site->icon);
  GdkPixbuf *pixbuf = gdk_pixbuf_new_from_file_at_size(path, size, size, NULL);
  awn_applet_simple_set_icon_pixbuf(AWN_APPLET_SIMPLE(site->webapplet->applet), pixbuf);

  if (site->width && site->height)
  {
    gtk_widget_set_size_request(GTK_WIDGET(site->webapplet->box),
                                site->width, site->height);
  }

  /* Set as new home page if this is either in the main menu, or 
   * in the dialog with 'set as new home page' checked */
  if (!GTK_IS_WIDGET(site->webapplet->check_home) ||
      gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(site->webapplet->check_home)))
  {
    config_set_uri(site->webapplet, site->url);
    config_set_site(site->webapplet, site->name);

    if (GTK_IS_WIDGET(site->webapplet->location_dialog))
      gtk_widget_destroy(site->webapplet->location_dialog);
  }

  if (GTK_IS_WIDGET(site->webapplet->location_dialog))
    gtk_widget_destroy(site->webapplet->location_dialog);

  else
    config_set_first_start(site->webapplet, FALSE);

  /* Set the title to the name of the website */
  awn_applet_simple_set_tooltip_text(AWN_APPLET_SIMPLE(site->webapplet->applet),
                                     site->name);

  g_free(path);
}

static WebSite *
get_site(WebApplet *webapplet, gchar *name)
{
  WebSite *site = g_new0(WebSite, 1);
  site->url = g_strdup(g_key_file_get_string(webapplet->sites_file,
                       name, "URL", NULL));
  site->name = g_strdup(g_key_file_get_string(webapplet->sites_file,
                        name, "Name", NULL));
  site->webapplet = webapplet;

  /* Width specific for this website */
  if (g_key_file_has_key(webapplet->sites_file, name, "Width", NULL))
  {
    site->width = g_key_file_get_integer(webapplet->sites_file,
                                         name, "Width", NULL);
  }

  /* Height specific for this website */
  if (g_key_file_has_key(webapplet->sites_file, name, "Height", NULL))
  {
    site->height = g_key_file_get_integer(webapplet->sites_file,
                                          name, "Height", NULL);
  }

  /* Icon, usually at least 48x48, or scalable */
  if (g_key_file_has_key(webapplet->sites_file, name, "Icon-svg", NULL))
  {
    site->icon = g_strdup(g_key_file_get_string(webapplet->sites_file,
                          name, "Icon-svg", NULL));
  }

  /* Icon over Icon-48 because Icon could be 64px */
  else if (g_key_file_has_key(webapplet->sites_file, name, "Icon", NULL))
  {
    site->icon = g_strdup(g_key_file_get_string(webapplet->sites_file,
                          name, "Icon", NULL));
  }

  else if (g_key_file_has_key(webapplet->sites_file, name, "Icon-48", NULL))
  {
    site->icon = g_strdup(g_key_file_get_string(webapplet->sites_file,
                          name, "Icon-48", NULL));
  }

  return site;
}

static GtkWidget *
website_buttons(WebApplet *webapplet)
{
  GtkWidget *table = gtk_table_new(1, 3, TRUE);

  if (webapplet->sites_file)
  {
    GtkWidget *button;
    GdkPixbuf *pixbuf;
    WebSite *site;
    gchar **groups, *path = NULL;
    gint i, y;

    GKeyFile *file = webapplet->sites_file;

    table = gtk_table_new(1, 3, TRUE);

    groups = g_key_file_get_groups(file, NULL);

    for (i = 0; groups[i]; i++)
    {
      button = gtk_button_new_with_label(g_key_file_get_string(file,
                                         groups[i], "Name", NULL));

      if (g_key_file_has_key(file, groups[i], "Icon-22", NULL))
      {
        path = g_strdup_printf(APPLETSDIR"/webapplet/icons/%s",
                               g_key_file_get_string(file, groups[i], "Icon-22", NULL));
      }

      else if (g_key_file_has_key(file, groups[i], "Icon-svg", NULL))
      {
        path = g_strdup_printf(APPLETSDIR"/webapplet/icons/%s",
                               g_key_file_get_string(file, groups[i], "Icon-svg", NULL));
      }

      else if (g_key_file_has_key(file, groups[i], "Icon-48", NULL))
      {
        path = g_strdup_printf(APPLETSDIR"/webapplet/icons/%s",
                               g_key_file_get_string(file, groups[i], "Icon-48", NULL));
      }

      else if (g_key_file_has_key(file, groups[i], "Icon", NULL))
      {
        path = g_strdup_printf(APPLETSDIR"/webapplet/icons/%s",
                               g_key_file_get_string(file, groups[i], "Icon", NULL));
      }

      if (path)
      {
        pixbuf = gdk_pixbuf_new_from_file_at_size(path, 22, 22, NULL);
        gtk_button_set_image(GTK_BUTTON(button),
                             gtk_image_new_from_pixbuf(pixbuf));

        g_free(path);
      }

      y = (gint)((gdouble)i / 4.0);

      gtk_table_attach(GTK_TABLE(table), button,
                       i % 4, (i % 4) + 1,
                       y, y + 1, GTK_FILL|GTK_EXPAND, 0, 3, 3);

      site = get_site(webapplet, groups[i]);

      g_signal_connect(G_OBJECT(button), "clicked",
                       G_CALLBACK(site_clicked), (gpointer)site);
    }
  }

  return table;
}

static void
_send_dialog_response(GtkEntry *entry, GtkDialog *dialog)
{
  gtk_dialog_response(dialog, GTK_RESPONSE_OK);
}

static gboolean
_show_location_dialog(GtkMenuItem *menuitem, WebApplet *webapplet)
{
  GtkWidget *dialog, *entry, *hbox, *vbox, *home_img, *home_box;
  gint response;

  /* Make the dialog */
  dialog = gtk_dialog_new_with_buttons(_("Open Location"),
                                       GTK_WINDOW(webapplet->mainwindow),
                                       GTK_DIALOG_DESTROY_WITH_PARENT,
                                       GTK_STOCK_CANCEL, GTK_RESPONSE_CANCEL,
                                       GTK_STOCK_OPEN, GTK_RESPONSE_OK,
                                       NULL);
  webapplet->location_dialog = dialog;

  /* Entry and "URL:" label */
  entry = gtk_entry_new();
  g_signal_connect(G_OBJECT(entry), "activate",
                   G_CALLBACK(_send_dialog_response), dialog);

  hbox = gtk_hbox_new(FALSE, 6);
  gtk_box_pack_start(GTK_BOX(hbox), gtk_label_new(_("URL:")), FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(hbox), entry, TRUE, TRUE, 0);

  /* Checkbox: Set as _home page, with nice little Home icon */
  home_img = gtk_image_new_from_stock(GTK_STOCK_HOME, GTK_ICON_SIZE_MENU);
  webapplet->check_home = gtk_check_button_new_with_mnemonic(_("Set as new _Home Page"));

  home_box = gtk_hbox_new(FALSE, 3);
  gtk_box_pack_start(GTK_BOX(home_box), home_img, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(home_box), webapplet->check_home, FALSE, FALSE, 0);

  /* Put everything together */
  vbox = gtk_vbox_new(FALSE, 6);
  gtk_box_pack_start(GTK_BOX(vbox), hbox, FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), website_buttons(webapplet), FALSE, FALSE, 0);
  gtk_box_pack_start(GTK_BOX(vbox), home_box, FALSE, FALSE, 0);
  gtk_container_set_border_width(GTK_CONTAINER(vbox), 6);
  gtk_widget_show_all(vbox);

  gtk_box_pack_start(GTK_BOX(GTK_DIALOG(dialog)->vbox), vbox, TRUE, TRUE, 0);

  response = gtk_dialog_run(GTK_DIALOG(dialog));

  if (response == GTK_RESPONSE_OK)
  {
    gchar *url = (gchar*)gtk_entry_get_text(GTK_ENTRY(entry));

    /* Open the page */
    go_to_url(webapplet, url);

    set_title(webapplet, url);

    /* User entered a URL, didn't choose a site */
    awn_applet_simple_set_icon_name(AWN_APPLET_SIMPLE(webapplet->applet),
                                    ICON_NAME);
    config_set_site(webapplet, "");
  }

  gtk_widget_destroy(dialog);

  return TRUE;
}

static void
go_clicked(GtkButton *button, WebApplet *webapplet)
{
  go_to_url(webapplet, (gchar*)gtk_entry_get_text(GTK_ENTRY(webapplet->entry)));

  config_set_first_start(webapplet, FALSE);
}

static void
entry_key_release(GtkWidget *entry, GdkEventKey *event, WebApplet *webapplet)
{
  if (event->keyval == GDK_Return || event->keyval == GDK_KP_Enter)
    go_clicked(NULL, webapplet);
}

static GtkWidget *
first_start(WebApplet *webapplet)
{
  GtkWidget *image, *button, *hbox, *buttons;

  /* Main VBox */
  webapplet->start = gtk_vbox_new(FALSE, 6);

  webapplet->entry = gtk_entry_new();
  gtk_entry_set_text(GTK_ENTRY(webapplet->entry), config_get_uri(webapplet));
  g_signal_connect(G_OBJECT(webapplet->entry), "key-release-event",
                   G_CALLBACK(entry_key_release), (gpointer)webapplet);

  image = gtk_image_new_from_stock(GTK_STOCK_GO_FORWARD, GTK_ICON_SIZE_BUTTON);
  button = gtk_button_new();
  gtk_button_set_image(GTK_BUTTON(button), image);
  g_signal_connect(G_OBJECT(button), "clicked",
                   G_CALLBACK(go_clicked), (gpointer)webapplet);

  hbox = gtk_hbox_new(FALSE, 3);
  gtk_box_pack_start(GTK_BOX(hbox), webapplet->entry, TRUE, TRUE, 0);
  gtk_box_pack_start(GTK_BOX(hbox), button, FALSE, FALSE, 0);

  gtk_box_pack_start(GTK_BOX(webapplet->start), hbox, FALSE, FALSE, 0);

  buttons = website_buttons(webapplet);
  gtk_box_pack_start(GTK_BOX(webapplet->start), buttons, FALSE, FALSE, 0);

  return webapplet->start;
}

static void
awn_html_dialog_new(WebApplet *webapplet)
{
  /* create viewer */
  webapplet->mainwindow = awn_dialog_new_for_widget (GTK_WIDGET(webapplet->applet));
  webapplet->box = gtk_vbox_new (FALSE, 1);

  webapplet->viewer = html_web_view_new ();

  /* Load the .ini file for websites */
  GError *err = NULL;
  webapplet->sites_file = g_key_file_new();

  g_key_file_load_from_file(webapplet->sites_file,
                            APPLETSDIR"/webapplet/webapplet-websites.ini",
                            0, &err);

  if (err)
  {
    printf("Error loading websites: %s\n", err->message);
    g_error_free(err);
    g_key_file_free(webapplet->sites_file);
    webapplet->sites_file = NULL;
  }

  /* If first time using this, hide WebView, show location entry/website buttons */
  if (config_get_first_start(webapplet))
  {
    gtk_widget_set_no_show_all(webapplet->viewer, TRUE);

    gtk_box_pack_start(GTK_BOX(webapplet->box), first_start(webapplet),
                       FALSE, FALSE, 0);

    awn_applet_simple_set_tooltip_text(AWN_APPLET_SIMPLE(webapplet->applet),
                                       _("Web Applet"));
  }

  else
  {
    go_to_url(webapplet, (gchar*)config_get_uri(webapplet));

    if (webapplet->sites_file)
    {
      const gchar *name = config_get_site(webapplet);

      if (name && strcmp(name, "") != 0)
      {
        gint size = awn_applet_get_size(webapplet->applet);

        WebSite *site = get_site(webapplet, (gchar*)name);
        gchar *path = g_strdup_printf(APPLETSDIR"/webapplet/icons/%s", site->icon);
        GdkPixbuf *pixbuf = gdk_pixbuf_new_from_file_at_size(path, size, size, NULL);
        awn_applet_simple_set_icon_pixbuf(AWN_APPLET_SIMPLE(site->webapplet->applet), pixbuf);

        if (site->width && site->height)
        {
          gtk_widget_set_size_request(GTK_WIDGET(site->webapplet->box),
                                      site->width, site->height);
        }
      }
    }
  }

  gtk_box_pack_start(GTK_BOX(webapplet->box), webapplet->viewer, TRUE, TRUE, 0);
  gtk_container_add(GTK_CONTAINER(webapplet->mainwindow), webapplet->box);
}


static gboolean
_button_clicked_event (GtkWidget      *widget,
                       GdkEventButton *event,
                       WebApplet      *webapplet)
{
  static GtkWidget *menu=NULL;

  if (event->button == 1)
  {
    if (GTK_WIDGET_VISIBLE (webapplet->mainwindow))
    {
      gtk_widget_hide (webapplet->mainwindow);
    }
    else
    {
      gtk_widget_show_all (webapplet->mainwindow);
    }
  }
  else if (event->button == 3)
  {
    if (!menu)
    {
      GtkWidget *item;
      menu = awn_applet_create_default_menu (webapplet->applet);
      gtk_menu_set_screen (GTK_MENU (menu), NULL);
      if (config_get_enable_location_dialog(webapplet))
      {
        item = gtk_image_menu_item_new_with_label (_("Open Location"));
        gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM (item),
                                       gtk_image_new_from_stock (GTK_STOCK_OPEN,
                                                          GTK_ICON_SIZE_MENU));
        gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);
        gtk_widget_show_all (item);
        g_signal_connect (G_OBJECT (item), "activate",
                          G_CALLBACK (_show_location_dialog), webapplet);
      }           
      item = awn_applet_create_about_item_simple(webapplet->applet,
                                                 "2008 Rodney Cryderman <rcryderman@gmail.com>\n"
                                                 "2008 Mark Lee <avant-wn@lazymalevolence.com>\n",
                                                 AWN_APPLET_LICENSE_GPLV2,
                                                 NULL);
      gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);
    }
    gtk_menu_popup (GTK_MENU (menu), NULL, NULL, NULL, NULL,
                    event->button, event->time);
  }
  return TRUE;
}

static void
_bloody_thing_has_style (GtkWidget *widget,WebApplet *webapplet)
{
  g_signal_connect (G_OBJECT (webapplet->applet), "button-press-event",
                    G_CALLBACK (_button_clicked_event), webapplet);
  //g_object_set (G_OBJECT (webapplet->mainwindow), "hide-on-unfocus", TRUE,
  //              NULL);
}

AwnApplet *
awn_applet_factory_initp (const gchar *name, gchar* uid, gint panel_id)
{
  g_on_error_stack_trace (NULL);
  html_init ();
  WebApplet *webapplet = g_malloc (sizeof (WebApplet));
  webapplet->uid=g_strdup(uid);
  init_config (webapplet);
  webapplet->check_home = NULL;
  webapplet->location_dialog = NULL;
  webapplet->start = NULL;
  webapplet->applet = AWN_APPLET (awn_applet_simple_new (name, uid, panel_id));
  gint height = awn_applet_get_size(webapplet->applet);

  awn_applet_simple_set_icon_name(AWN_APPLET_SIMPLE(webapplet->applet),
                                  ICON_NAME);
 
  /*gtk_widget_show_all (GTK_WIDGET (webapplet->applet));*/
  awn_html_dialog_new (webapplet);
  gtk_window_set_focus_on_map (GTK_WINDOW (webapplet->mainwindow), TRUE);
  g_signal_connect_after (G_OBJECT (webapplet->applet), "realize",
                          G_CALLBACK (_bloody_thing_has_style), webapplet);
  return webapplet->applet;
}
/* vim: set et ts=2 sts=2 sw=2 : */
