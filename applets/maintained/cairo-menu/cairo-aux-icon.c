/*
 * Copyright (C) 2009 Rodney Cryderman <rcryderman@gmail.com>
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
/* cairo-menu-aux-icon.c */

#include <gtk/gtk.h>
#include <libawn/libawn.h>
#include <libawn/awn-utils.h>
#include "cairo-aux-icon.h"
#include "cairo-menu.h"
#include "cairo-menu-applet.h"
#include "gnome-menu-builder.h"
#include "misc.h"
#include "config.h"

extern MenuBuildFunc  menu_build;

G_DEFINE_TYPE (CairoAuxIcon, cairo_aux_icon, AWN_TYPE_THEMED_ICON)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_AUX_ICON, CairoAuxIconPrivate))

typedef struct _CairoAuxIconPrivate CairoAuxIconPrivate;

struct _CairoAuxIconPrivate {
  DEMenuType   menu_type;
  GtkWidget   *menu;
  GtkWidget   *context_menu;
  AwnApplet   * applet;
  MenuInstance * menu_instance;
  gchar        * menu_name;
  gchar        * display_name;
  gchar        * icon_name;
  guint         autohide_cookie;    
};


enum
{
  PROP_0,
  PROP_APPLET,
  PROP_MENU_NAME,
  PROP_DISPLAY_NAME,
  PROP_ICON_NAME
};

static gboolean _button_clicked_event (CairoAuxIcon *applet, GdkEventButton *event, gpointer null);

static gboolean _deactivate_event (GtkMenuShell *menushell,CairoAuxIcon * icon);

static void
cairo_aux_icon_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (object);
  
  switch (property_id) {
  case PROP_APPLET:
    g_value_set_pointer (value,priv->applet);
    break;
  case PROP_MENU_NAME:
    g_value_set_string (value, priv->menu_name);
    break;
  case PROP_DISPLAY_NAME:
    g_value_set_string (value, priv->display_name);
    break;
  case PROP_ICON_NAME:
    g_value_set_string (value, priv->icon_name);
    break;            
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_aux_icon_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (object);
  
  switch (property_id) {
  case PROP_APPLET:
      priv->applet = g_value_get_pointer (value);
      break;
  case PROP_MENU_NAME:
      priv->menu_name = g_value_dup_string (value);
      break;
  case PROP_DISPLAY_NAME:
      priv->display_name = g_value_dup_string (value);
      break;
  case PROP_ICON_NAME:
      priv->icon_name = g_value_dup_string (value);
      break;      
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_aux_icon_dispose (GObject *object)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (object);

  if (priv->menu)
  {
    gtk_widget_destroy (priv->menu);  
    priv->menu = NULL;
  }
  if (priv->context_menu)
  {
    gtk_widget_destroy (priv->context_menu);
    priv->context_menu = NULL;
  }
  G_OBJECT_CLASS (cairo_aux_icon_parent_class)->dispose (object);
}

static void
cairo_aux_icon_finalize (GObject *object)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (object);

  g_free (priv->menu_name);
  g_free (priv->display_name);
  g_free (priv->menu_instance);
  G_OBJECT_CLASS (cairo_aux_icon_parent_class)->finalize (object);
}

static void
size_changed_cb (CairoAuxIcon * icon,gint size)
{
  g_return_if_fail (AWN_IS_CAIRO_AUX_ICON(icon));
  CairoAuxIconPrivate * priv = GET_PRIVATE (icon);

  awn_themed_icon_set_size (AWN_THEMED_ICON (icon),awn_applet_get_size (priv->applet));
}

static gboolean
queue_menu_build (CairoAuxIcon *icon)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (icon);

  priv->menu = menu_build (priv->menu_instance);
  g_signal_connect(G_OBJECT(priv->menu), "deactivate", G_CALLBACK(_deactivate_event), icon);  
  g_signal_connect(icon, "button-press-event", G_CALLBACK(_button_clicked_event), NULL);
  g_signal_connect_swapped(priv->applet,"size-changed",G_CALLBACK(size_changed_cb),icon);
  return FALSE;
}

static void
cairo_aux_icon_constructed (GObject *object)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (object);
  GdkPixbuf * pbuf;
  gint size = awn_applet_get_size (priv->applet);
  gchar * applet_name = g_strdup_printf("cairo-menu-%s",priv->menu_name);
  gchar * base;
  G_OBJECT_CLASS (cairo_aux_icon_parent_class)->constructed (object);  

  /*
   applet_name can be a path with /'s.  These need to be retained for matching 
   purposes when building the menus... but we need to strip them out for set_info
   */
  base = g_path_get_basename (applet_name);
  awn_themed_icon_set_info_simple (AWN_THEMED_ICON(object),base,awn_applet_get_uid (priv->applet),priv->icon_name);
  g_free (base);
  awn_themed_icon_set_size (AWN_THEMED_ICON (object),size);
  g_free (applet_name);
  
  /* call our function in the module */

  priv->menu_instance = get_menu_instance (priv->applet,
                                        (GetRunCmdFunc)cairo_menu_applet_get_run_cmd,
                                        (GetSearchCmdFunc)cairo_menu_applet_get_search_cmd,
                                        (AddIconFunc) cairo_menu_applet_add_icon,
                                        NULL,
                                        priv->menu_name,
                                        0);
  g_idle_add ((GSourceFunc)queue_menu_build, object);
  awn_icon_set_tooltip_text (AWN_ICON(object),priv->display_name);
}

static void
cairo_aux_icon_class_init (CairoAuxIconClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);
  GParamSpec   *pspec;  

  object_class->get_property = cairo_aux_icon_get_property;
  object_class->set_property = cairo_aux_icon_set_property;
  object_class->dispose = cairo_aux_icon_dispose;
  object_class->finalize = cairo_aux_icon_finalize;
  object_class->constructed = cairo_aux_icon_constructed;

  pspec = g_param_spec_pointer ("applet",
                               "applet",
                               "AwnApplet",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_APPLET, pspec);

  pspec = g_param_spec_string ("menu_name",
                               "menu_name",
                               "Menu Name",
                                "",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_MENU_NAME, pspec);
  
  pspec = g_param_spec_string ("display_name",
                               "display_name",
                               "Display Name",
                                "",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_DISPLAY_NAME, pspec);

  pspec = g_param_spec_string ("icon_name",
                               "icon_name",
                               "Icon Name",
                                "",
                               G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_ICON_NAME, pspec);

  g_type_class_add_private (klass, sizeof (CairoAuxIconPrivate));
}

static void
cairo_aux_icon_init (CairoAuxIcon *self)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (self);

  priv->menu_type = MENU_TYPE_GUESS;
}

GtkWidget*
cairo_aux_icon_new (AwnApplet * applet, gchar * menu_name, gchar * display_name, gchar * icon_name)
{
  return g_object_new (AWN_TYPE_CAIRO_AUX_ICON, 
                        "applet",applet,
                        "menu_name",menu_name,
                        "display_name",display_name,
                        "icon_name",icon_name,
                        NULL);
}

static void
_remove_icon (GtkMenuItem * item, CairoAuxIcon * icon)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (icon);

//  free_menu_instance (priv->menu_instance);
  cairo_menu_applet_remove_icon (AWN_CAIRO_MENU_APPLET(priv->applet),AWN_THEMED_ICON(icon));
}

static void 
_position(GtkMenu *menu, gint *x, gint *y, gboolean *push_in,CairoAuxIcon * icon)
{
  GtkRequisition requisition;
  gint applet_x, applet_y;
  CairoAuxIconPrivate * priv = GET_PRIVATE (icon);
  gint screen_height;
  gint screen_width;
  GdkScreen * def_screen = gdk_screen_get_default ();
  
  screen_height = gdk_screen_get_height (def_screen);
  screen_width = gdk_screen_get_width (def_screen);
  gtk_widget_size_request (GTK_WIDGET(menu),&requisition);
  gdk_window_get_origin(GTK_WIDGET(icon)->window, &applet_x, &applet_y);
  switch (awn_applet_get_pos_type (priv->applet))
  {
    case GTK_POS_BOTTOM:
      *x=applet_x;
      *y=applet_y - requisition.height + awn_applet_get_size (priv->applet);
      break;
    case GTK_POS_TOP:
      *x=applet_x;
      *y=applet_y  + awn_applet_get_size (priv->applet) + awn_applet_get_offset (priv->applet);
      break;
    case GTK_POS_LEFT:
      *x=applet_x + awn_applet_get_size (priv->applet) + awn_applet_get_offset (priv->applet);
      *y=applet_y;
      break;
    case GTK_POS_RIGHT:
      *x=applet_x - requisition.width + awn_applet_get_size (priv->applet);
      *y=applet_y;
      break;
  }
  if (*x + requisition.width > screen_width)
  {
    *x = screen_width - requisition.width;
  }
  if (*y + requisition.height > screen_height)
  {
    *y = screen_height - requisition.height;
  }
//  *push_in = TRUE;  doesn't quite do what I want.
  
}


static gboolean 
_button_clicked_event (CairoAuxIcon *icon, GdkEventButton *event, gpointer null)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;
  CairoAuxIconPrivate * priv = GET_PRIVATE (icon);
  
  if (event->button == 1)
  {
    gtk_menu_popup(GTK_MENU(priv->menu), NULL, NULL, (GtkMenuPositionFunc)_position,icon,
                          event->button, event->time);   
    if (!priv->autohide_cookie)
    {     
      priv->autohide_cookie = awn_applet_inhibit_autohide (AWN_APPLET(priv->applet),"CairoMenu" );
    }                
    g_object_set(awn_overlayable_get_effects (AWN_OVERLAYABLE(icon)), "depressed", FALSE,NULL);    
  }
  else if (event->button == 3)
  {
    GtkWidget * item;

    if (!priv->context_menu)
    {
      priv->context_menu = awn_applet_create_default_menu (AWN_APPLET(priv->applet));
      gtk_menu_set_screen(GTK_MENU(priv->context_menu), NULL);
      
      item = awn_themed_icon_create_remove_custom_icon_item (AWN_THEMED_ICON(icon),NULL);
      gtk_menu_shell_append (GTK_MENU_SHELL(priv->context_menu), item);
/*      
      item = gtk_image_menu_item_new_with_label("Applet Preferences");
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM(item), 
                                     gtk_image_new_from_stock (GTK_STOCK_PREFERENCES,GTK_ICON_SIZE_MENU));
      gtk_widget_show(item);
      gtk_menu_shell_append(GTK_MENU_SHELL(priv->context_menu), item);*/
      gtk_menu_set_screen(GTK_MENU(priv->context_menu), NULL);
      item = gtk_image_menu_item_new_with_label("Remove Icon");
      gtk_image_menu_item_set_image (GTK_IMAGE_MENU_ITEM(item), 
                                     gtk_image_new_from_stock (GTK_STOCK_REMOVE,GTK_ICON_SIZE_MENU));

      gtk_widget_show(item);
      gtk_menu_shell_append(GTK_MENU_SHELL(priv->context_menu), item);
      g_signal_connect (G_OBJECT(item),"activate",G_CALLBACK(_remove_icon),icon);
      
//      g_signal_connect(G_OBJECT(item), "button-press-event", G_CALLBACK(_show_prefs), NULL);
      item=awn_applet_create_about_item_simple(AWN_APPLET(priv->applet),
                                               "Copyright 2007,2008, 2009 Rodney Cryderman <rcryderman@gmail.com>",
                                               AWN_APPLET_LICENSE_GPLV2,
                                               VERSION);
      gtk_menu_shell_append(GTK_MENU_SHELL(priv->context_menu), item);
      g_signal_connect(G_OBJECT(priv->context_menu), "deactivate", G_CALLBACK(_deactivate_event), icon);
      awn_utils_show_menu_images (GTK_MENU (priv->context_menu));
    }
    if (!priv->autohide_cookie)
    {     
      priv->autohide_cookie = awn_applet_inhibit_autohide (AWN_APPLET(priv->applet),"CairoMenu" );
    }        
    gtk_menu_popup(GTK_MENU(priv->context_menu), NULL, NULL, NULL, NULL,event_button->button, event_button->time);
    g_object_set(awn_overlayable_get_effects (AWN_OVERLAYABLE(icon)), "depressed", FALSE,NULL);    
  }
  else
  {
    return TRUE;
  }
  awn_icon_set_is_active (AWN_ICON(icon), TRUE);  
  return TRUE;
}

static gboolean 
_deactivate_event (GtkMenuShell *menushell,CairoAuxIcon * icon)
{
  CairoAuxIconPrivate * priv = GET_PRIVATE (icon);
  
  if (priv->autohide_cookie)
  {     
    awn_applet_uninhibit_autohide (AWN_APPLET(priv->applet),priv->autohide_cookie);
    priv->autohide_cookie = 0;
  }
  awn_icon_set_is_active (AWN_ICON(icon), FALSE);
}

