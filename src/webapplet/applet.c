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

#include <libawn/awn-cairo-utils.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-dialog.h>
#include <gtk/gtk.h>
#include <glib.h>
#include <glib/gi18n.h>

#include <libawn-extras/awn-extras.h>

#include "engine_html.h"
#include "applet.h"
#include "configuration.h"


static void
_send_dialog_response (GtkEntry *entry, GtkDialog *dialog)
{
  gtk_dialog_response (dialog, GTK_RESPONSE_OK);
}

static gboolean
_show_location_dialog (GtkMenuItem *menuitem,WebApplet *webapplet)
{
  static gboolean done_once = FALSE;
  static GtkWidget *location_dialog;
  static GtkWidget *entry;
  gint response;
  if (!done_once)
  {
    location_dialog = gtk_dialog_new_with_buttons (_("Open Location"),
                                                     GTK_WINDOW (webapplet->mainwindow),
                                                     GTK_DIALOG_DESTROY_WITH_PARENT,
                                                     GTK_STOCK_CANCEL,
                                                     GTK_RESPONSE_CANCEL,
                                                     GTK_STOCK_OPEN,
                                                     GTK_RESPONSE_OK,
                                                     NULL);
    GtkWidget *hbox = gtk_hbox_new (FALSE, 5);
    gtk_container_add (GTK_CONTAINER (hbox), gtk_label_new (_("URI:")));
    entry = gtk_entry_new ();
    g_signal_connect (G_OBJECT (entry), "activate",
                      G_CALLBACK (_send_dialog_response),
                      location_dialog);
    gtk_container_add (GTK_CONTAINER (hbox), entry);
    gtk_widget_show_all (hbox);
    gtk_container_add (GTK_CONTAINER (GTK_DIALOG (location_dialog)->vbox),
                       hbox);
    done_once = TRUE;
  }
  response = gtk_dialog_run (GTK_DIALOG (location_dialog));
  gtk_widget_hide (location_dialog);
  if (response == GTK_RESPONSE_OK)
  {
    html_web_view_open (webapplet->viewer,
                        gtk_entry_get_text (GTK_ENTRY (entry)));
  }
  gchar * title = g_strdup_printf("%30s",gtk_entry_get_text (GTK_ENTRY (entry)));  //FIXME put the URL or page title in here...
  awn_applet_simple_set_tooltip_text(AWN_APPLET_SIMPLE(webapplet->applet),title);
  g_free(title);
  
  return TRUE;
}

static void
awn_html_dialog_new (WebApplet *webapplet)
{
  /* create viewer */
  webapplet->mainwindow = awn_dialog_new_for_widget (webapplet->applet);
  webapplet->box = gtk_vbox_new (FALSE, 1);
  gtk_widget_set_size_request (GTK_WIDGET (webapplet->box), config_get_width(webapplet),
                               config_get_height(webapplet) );
  webapplet->viewer = html_web_view_new ();
  gtk_container_add (GTK_CONTAINER (webapplet->box),webapplet->viewer);
  gtk_container_add (GTK_CONTAINER (webapplet->mainwindow), webapplet->box);
  html_web_view_open (webapplet->viewer, config_get_uri(webapplet));
}


static gboolean
_button_clicked_event (GtkWidget      *widget,
                       GdkEventButton *event,
                       WebApplet      *webapplet)
{
  static GtkWidget *menu=NULL;
  GdkEventButton *event_button;
  event_button = (GdkEventButton *)event;
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
      item = awn_applet_create_preferences(webapplet->uid,APPLET_NAME,APPLET_NAME);
      if (item) //generic preferences is enabled
      {
        gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);          
      }        
      item = awn_applet_simple_create_about_item("2008 Rodney Cryderman <rcryderman@gmail.com>\n2008 Mark Lee <avant-wn@lazymalevolence.com>\n",
                                                 AWN_APPLET_LICENSE_GPLV2,
                                                 "WebApplet",
                                                 NULL);
      gtk_menu_shell_append (GTK_MENU_SHELL (menu), item);                
    }
    gtk_menu_popup (GTK_MENU (menu), NULL, NULL, NULL, NULL,
                    event_button->button, event_button->time);
  }
  return TRUE;
}

static gboolean
_focus_out_event(GtkWidget *widget, GdkEventButton *event, void * null)
{
//  gtk_widget_hide(webapplet->mainwindow);
  return TRUE;
}


static void
_bloody_thing_has_style (GtkWidget *widget,WebApplet *webapplet)
{

  gchar * title = g_strdup_printf("%30s",config_get_uri(webapplet));  //FIXME put the URL or page title in here...
  awn_applet_simple_set_tooltip_text(AWN_APPLET_SIMPLE(webapplet->applet),title);
  g_free(title);
  g_signal_connect (G_OBJECT (webapplet->applet), "button-press-event",
                    G_CALLBACK (_button_clicked_event), webapplet);
  g_signal_connect (G_OBJECT (webapplet->mainwindow), "focus-out-event",
                    G_CALLBACK (_focus_out_event), webapplet);
}

AwnApplet *
awn_applet_factory_initp (const gchar *name, gchar* uid, gint panel_id)
{
  g_on_error_stack_trace (NULL);
  html_init ();
  WebApplet *webapplet = g_malloc (sizeof (WebApplet));
  webapplet->uid=g_strdup(uid);
  init_config (webapplet, uid);
  webapplet->applet = AWN_APPLET (awn_applet_simple_new (name, uid, panel_id));
  gint height = awn_applet_get_size(webapplet->applet);
  gtk_widget_set_size_request (GTK_WIDGET (webapplet->applet), height, -1);

  webapplet->applet_icon_name = g_strdup ("apple-green");  

  awn_applet_simple_set_icon_name(AWN_APPLET_SIMPLE(webapplet->applet),
                                    APPLET_NAME,
                                    webapplet->applet_icon_name)  ;
 
  /*gtk_widget_show_all (GTK_WIDGET (webapplet->applet));*/
  awn_html_dialog_new (webapplet);
  gtk_window_set_focus_on_map (GTK_WINDOW (webapplet->mainwindow), TRUE);
  g_signal_connect_after (G_OBJECT (webapplet->applet), "realize",
                          G_CALLBACK (_bloody_thing_has_style), webapplet);
  return webapplet->applet;
}
/* vim: set et ts=2 sts=2 sw=2 : */
