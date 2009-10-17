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

/* cairo-menu-applet.c */

#include <gtk/gtk.h>
#include <libawn/libawn.h>
#include "cairo-menu-applet.h"
#include "cairo-menu.h"
#include "cairo-main-icon.h"
#include "cairo-aux-icon.h"
#include "gnome-menu-builder.h"
#include "config.h"

G_DEFINE_TYPE (CairoMenuApplet, cairo_menu_applet, AWN_TYPE_APPLET)

MenuBuildFunc  menu_build;

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_MENU_APPLET, CairoMenuAppletPrivate))

typedef struct _CairoMenuAppletPrivate CairoMenuAppletPrivate;

struct _CairoMenuAppletPrivate {
  DEMenuType   menu_type;
  GtkWidget * box;  
  gchar     * run_cmd;
  gchar     * search_cmd;
  GList     * aux_menu_names;
};


static gchar * gnome_run_cmds[] = { "gnome-do","grun","gmrun","gnome-launch-box",
                          "gnome-panel-control --run-dialog",NULL};

static gchar * gnome_search_cmds[] = { "tracker-search-tool","gnome-do",NULL};
  
static gboolean _button_clicked_event (CairoMenuApplet *applet, GdkEventButton *event, gpointer null);


static void
cairo_menu_applet_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_applet_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  switch (property_id) {
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_applet_dispose (GObject *object)
{
  G_OBJECT_CLASS (cairo_menu_applet_parent_class)->dispose (object);
}

static void
cairo_menu_applet_finalize (GObject *object)
{
  G_OBJECT_CLASS (cairo_menu_applet_parent_class)->finalize (object);
}

static void
cairo_menu_applet_constructed (GObject *object)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (object);
  GtkWidget * icon;
  G_OBJECT_CLASS (cairo_menu_applet_parent_class)->constructed (object);

  /*to when guessing check DESKTOP_SESSION env var. and try loading based on that.
   if env var not set or module fails to load then try to load in the following 
   order:  gnome, xfce.   
  /* 
   TODO fix the various travesties*/
  GList * iter;
  GError * error = NULL;
  gchar * filename = APPLETSDIR"/../../../lib/awn/applets/cairo-menu/gnome-menu-builder";
  g_debug ("%s",filename);
  GModule      *module;
  module = g_module_open (filename, 
                          G_MODULE_BIND_LAZY);  
  g_assert (module);
  if (!g_module_symbol (module, "menu_build", (gpointer *)&menu_build))
  {
    if (!g_module_close (module))
      g_warning ("%s: %s", filename, g_module_error ());
    g_assert (FALSE);    
  }
  if (menu_build == NULL)
    {
      if (!g_module_close (module))
        g_warning ("%s: %s", filename, g_module_error ());
      g_assert (FALSE);
    }
  /* call our function in the module */
  icon = cairo_main_icon_new(AWN_APPLET(object));
  gtk_container_add (GTK_CONTAINER(priv->box),icon);

  for (iter = priv->aux_menu_names; iter; iter = iter->next)
  {
    gchar * aux_name = iter->data;
    icon = cairo_aux_icon_new (AWN_APPLET(object),aux_name,"","stock_folder");
    gtk_container_add (GTK_CONTAINER(priv->box),icon);     
  }
}

static void
cairo_menu_applet_class_init (CairoMenuAppletClass *klass)
{
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  g_type_class_add_private (klass, sizeof (CairoMenuAppletPrivate));

  object_class->get_property = cairo_menu_applet_get_property;
  object_class->set_property = cairo_menu_applet_set_property;
  object_class->dispose = cairo_menu_applet_dispose;
  object_class->finalize = cairo_menu_applet_finalize;
  object_class->constructed = cairo_menu_applet_constructed;
}

static void
cairo_menu_applet_init (CairoMenuApplet *self)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (self);

  priv->box = awn_icon_box_new_for_applet (AWN_APPLET (self));
  priv->run_cmd = NULL;
  priv->search_cmd = NULL;
  priv->aux_menu_names = NULL;
//  priv->aux_menu_names = g_list_append (priv->aux_menu_names,g_strdup (":::PLACES"));
  gtk_container_add (GTK_CONTAINER (self), priv->box);
  gtk_widget_show (priv->box);

}

CairoMenuApplet*
cairo_menu_applet_new (const gchar *name,const gchar* uid, gint panel_id)
{
  return g_object_new (AWN_TYPE_CAIRO_MENU_APPLET, 
                        "canonical-name",name,
                        "uid", uid,
                        "panel-id",panel_id,
                        NULL);
}

static const gchar *
cairo_menu_applet_get_cmd (CairoMenuApplet * applet, gchar * def_cmd, gchar **cmd_list)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);
  gchar * p;
  gchar **iter;

  if (def_cmd)
  {
    p = g_find_program_in_path (def_cmd);
    if (p)
    {
      g_free (p);
      return def_cmd;
    }
    else 
    {
      g_message ("Cairo Menu (%s): Configured command (%s) not found",__func__,def_cmd);
    }
  }
  g_message ("Cairo Menu (%s): Searching for command...",__func__);
  for (iter = cmd_list; *iter; iter++)
  {
    p = g_find_program_in_path (*iter);
    if (p)
    {
      g_message ("%s found.",*iter);
      g_free (p);
      return *iter;
    }
    else
    {
      g_message ("%s NOT found.",*iter);
    }
  }
  g_message ("No known command found.  Please configure");
}

const gchar *
cairo_menu_applet_get_run_cmd (CairoMenuApplet * applet)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);
  
  return cairo_menu_applet_get_cmd (applet, priv->run_cmd, gnome_run_cmds);
}

const gchar *
cairo_menu_applet_get_search_cmd (CairoMenuApplet * applet)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);
  
  return cairo_menu_applet_get_cmd (applet, priv->search_cmd, gnome_search_cmds);
}

void
cairo_menu_applet_add_icon (CairoMenuApplet * applet, gchar * menu_name, gchar * display_name, gchar * icon_name)
{
  gchar * str;
  GtkWidget * icon;
  
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);

  g_debug ("%s: %s, %s, %s",__func__,menu_name,display_name,icon_name);
  str = g_strdup_printf("%s###%s###%s",menu_name,display_name,icon_name);
  priv->aux_menu_names = g_list_append (priv->aux_menu_names, str);

  icon = cairo_aux_icon_new (AWN_APPLET(applet),menu_name,display_name,icon_name);
  gtk_widget_show (icon);
  gtk_container_add (GTK_CONTAINER(priv->box),icon);
}