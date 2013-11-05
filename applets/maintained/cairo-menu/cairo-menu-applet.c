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
#include "cairo-main-icon.h"
#include "cairo-aux-icon.h"
#include "gnome-menu-builder.h"
#include "config.h"
#include <glib/gi18n-lib.h>

G_DEFINE_TYPE (CairoMenuApplet, cairo_menu_applet, AWN_TYPE_APPLET)

MenuBuildFunc  menu_build;

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_MENU_APPLET, CairoMenuAppletPrivate))

typedef struct _CairoMenuAppletPrivate CairoMenuAppletPrivate;

struct _CairoMenuAppletPrivate {
  DEMenuType   menu_type;
  GtkWidget   * box;
  gchar       * run_cmd;
  gchar       * search_cmd;
  GValueArray * aux_menu_names;
  GValueArray * hidden_names;
  DesktopAgnosticConfigClient *client;
  CairoMainIcon * main_icon;
};


static gchar * gnome_run_cmds[] = { "synapse","gnome-do","kupfer","grun","gmrun","gnome-launch-box",
                          "gnome-panel-control --run-dialog","xfrun4",NULL};

static gchar * gnome_search_cmds[] = { "tracker-search-tool","gnome-do","gnome-search-tool",NULL};

static gboolean _button_clicked_event (CairoMenuApplet *applet, GdkEventButton *event, gpointer null);

enum
{
  PROP_0,
  PROP_AUX_MENU_NAMES,
  PROP_HIDDEN_NAMES,
  PROP_RUN_CMD,
  PROP_SEARCH_CMD
};

static void
cairo_menu_applet_get_property (GObject *object, guint property_id,
                              GValue *value, GParamSpec *pspec)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (object);

  switch (property_id) {
  case PROP_AUX_MENU_NAMES:
    g_value_set_boxed (value,priv->aux_menu_names );
    break;
  case PROP_HIDDEN_NAMES:
    g_value_set_boxed (value,priv->hidden_names );
    break;
  case PROP_RUN_CMD:
    g_value_set_string (value,priv->run_cmd);
    break;
  case PROP_SEARCH_CMD:
    g_value_set_string (value,priv->search_cmd);
    break;
  default:
    G_OBJECT_WARN_INVALID_PROPERTY_ID (object, property_id, pspec);
  }
}

static void
cairo_menu_applet_set_property (GObject *object, guint property_id,
                              const GValue *value, GParamSpec *pspec)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (object);

  switch (property_id) {
  case PROP_AUX_MENU_NAMES:
    if (priv->aux_menu_names)
    {
      g_value_array_free (priv->aux_menu_names);
      priv->aux_menu_names = NULL;
    }
    priv->aux_menu_names = (GValueArray*)g_value_dup_boxed (value);
    break;
  case PROP_HIDDEN_NAMES:
    if (priv->hidden_names)
    {
      g_value_array_free (priv->hidden_names);
      priv->hidden_names = NULL;
    }
    priv->hidden_names = (GValueArray*)g_value_dup_boxed (value);
    break;
  case PROP_RUN_CMD:
    if (priv->run_cmd)
    {
      g_free (priv->run_cmd);
    }
    priv->run_cmd = g_value_dup_string (value);
    break;
  case PROP_SEARCH_CMD:
    if (priv->search_cmd)
    {
      g_free (priv->search_cmd);
    }
    priv->search_cmd = g_value_dup_string (value);
    break;
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
  gint idx;
  /*to when guessing check DESKTOP_SESSION env var. and try loading based on that.
   if env var not set or module fails to load then try to load in the following
   order:  gnome, xfce.
  /*
   TODO fix the various travesties*/
  GList * iter;
  GError * error = NULL;
  gchar * filename = LIBDIR"/awn/applets/cairo-menu/gnome-menu-builder";
  GModule      *module;

  G_OBJECT_CLASS (cairo_menu_applet_parent_class)->constructed (object);
  module = g_module_open (filename,G_MODULE_BIND_LAZY);
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
  priv->client = awn_config_get_default_for_applet (AWN_APPLET (object), NULL);

  /* Connect up the important bits */
  desktop_agnostic_config_client_bind (priv->client,
                                       DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                       "aux_menu_names",
                                       object, "aux_menu_names", FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       NULL);

  desktop_agnostic_config_client_bind (priv->client,
                                       DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                       "hidden_names",
                                       object, "hidden_names", FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       NULL);

  desktop_agnostic_config_client_bind (priv->client,
                                       DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                       "run_cmd",
                                       object, "run_cmd", FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       NULL);

  desktop_agnostic_config_client_bind (priv->client,
                                       DESKTOP_AGNOSTIC_CONFIG_GROUP_DEFAULT,
                                       "search_cmd",
                                       object, "search_cmd", FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       NULL);

  icon = cairo_main_icon_new(AWN_APPLET(object));
  gtk_container_add (GTK_CONTAINER(priv->box),icon);
  priv->main_icon = AWN_CAIRO_MAIN_ICON(icon);

  for (idx = 0; idx < priv->aux_menu_names->n_values; idx++)
  {
    gchar *name;
    GStrv tokens;
    name = g_value_dup_string (g_value_array_get_nth (priv->aux_menu_names, idx));
    tokens = g_strsplit ( name,"###",-1);
    if (g_strv_length (tokens)==3)
    {
      icon = cairo_aux_icon_new (AWN_APPLET(object),tokens[0],tokens[1],tokens[2]);
      gtk_container_add (GTK_CONTAINER(priv->box),icon);
    }
    else
    {
      g_message ("%s: Invalid entry in aux_menu_names",__func__);
    }
    g_strfreev(tokens);
    g_free (name);
  }
/*
  for (iter = priv->aux_menu_names; iter; iter = iter->next)
  {
    gchar * aux_name = iter->data;
    icon = cairo_aux_icon_new (AWN_APPLET(object),aux_name,"","stock_folder");
    gtk_container_add (GTK_CONTAINER(priv->box),icon);
  }*/
}

static void
cairo_menu_applet_class_init (CairoMenuAppletClass *klass)
{
  GParamSpec     *pspec;
  GObjectClass *object_class = G_OBJECT_CLASS (klass);

  object_class->get_property = cairo_menu_applet_get_property;
  object_class->set_property = cairo_menu_applet_set_property;
  object_class->dispose = cairo_menu_applet_dispose;
  object_class->finalize = cairo_menu_applet_finalize;
  object_class->constructed = cairo_menu_applet_constructed;

  pspec = g_param_spec_boxed ("aux_menu_names",
                              "aux_menu_names",
                              "List of aux menus",
                              G_TYPE_VALUE_ARRAY,
                              G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_AUX_MENU_NAMES, pspec);

  pspec = g_param_spec_boxed ("hidden_names",
                              "hidden_names",
                              "List of hidden menus",
                              G_TYPE_VALUE_ARRAY,
                              G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_HIDDEN_NAMES, pspec);

  pspec = g_param_spec_string ("run_cmd",
                              "run_cmd",
                              "Run Command",
                              NULL,
                              G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_RUN_CMD, pspec);

  pspec = g_param_spec_string ("search_cmd",
                              "search_cmd",
                              "Search Command",
                              NULL,
                              G_PARAM_READWRITE | G_PARAM_CONSTRUCT);
  g_object_class_install_property (object_class, PROP_SEARCH_CMD, pspec);

  g_type_class_add_private (klass, sizeof (CairoMenuAppletPrivate));

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

  bindtextdomain (GETTEXT_PACKAGE, LOCALEDIR);
  textdomain (GETTEXT_PACKAGE);
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

static gboolean
cmd_found (gchar *cmd)
{
  gchar * p;
  gchar **split = NULL;

  if (strlen (cmd) == 0)
  {
    return FALSE;
  }

  /* Split into executable and arguments */
  split = g_strsplit (cmd, " ", 2);
  p = g_find_program_in_path (split[0]);
  if (p)
  {
    if (p!=split[0])
    {
      g_free (p);
    }
    g_strfreev (split);
    return TRUE;
  }
  g_strfreev (split);
  return FALSE;
}

static const gchar *
cairo_menu_applet_get_cmd (CairoMenuApplet * applet, gchar * def_cmd, gchar **cmd_list)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);
  gchar **iter;

  if (def_cmd)
  {
    if (cmd_found (def_cmd))
    {
      g_message ("Cairo Menu default command found '%s'",def_cmd);
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
    g_debug ("%s",*iter);
    if (cmd_found (*iter))
    {
      g_message ("%s found.",*iter);
      return *iter;
    }
    else
    {
      g_message ("%s NOT found.",*iter);
    }
  }
  g_message ("No known command found.  Please configure");
  return NULL;
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
cairo_menu_applet_append_hidden_menu (CairoMenuApplet * applet, gchar * menu_name)
{
  GValueArray * names;
  GValue val = {0,};
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);

  g_object_get (G_OBJECT (applet), "hidden_names", &names, NULL);
  g_value_init (&val, G_TYPE_STRING);
  g_value_set_string (&val, menu_name);
  names = g_value_array_append (names, &val);
  g_object_set (G_OBJECT (applet), "hidden_names", names, NULL);
  g_value_unset (&val);
  g_value_array_free (names);

}

gboolean
cairo_menu_applet_check_hidden_menu (CairoMenuApplet * applet, gchar * menu_name)
{
  GValueArray * names;
  gint idx;
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);

  g_object_get (applet,"hidden_names",&names,NULL);
  if (names)
  {
    for (idx = 0; idx < names->n_values; idx++)
    {
      gchar *name;
      name = g_value_dup_string (g_value_array_get_nth (names, idx));
      if (g_strcmp0 (name,menu_name)==0)
      {
        g_free (name);
        g_value_array_free (names);
        return TRUE;
      }
      g_free (name);
    }
    g_value_array_free (names);
  }
  return FALSE;
}

void
cairo_menu_applet_remove_hidden_menu (CairoMenuApplet * applet, gchar * menu_name)
{
  GValueArray * names;
  gint idx;

  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);

  g_object_get (applet,"hidden_names",&names,NULL);
  if (names)
  {
    for (idx = 0; idx < names->n_values; idx++)
    {
      gchar *name;
      name = g_value_dup_string (g_value_array_get_nth (names, idx));
      if (g_strcmp0 (name,menu_name)==0)
      {
        GValueArray* s = g_value_array_remove (names, idx);
//        g_value_array_free (s);
        g_object_set (applet,"hidden_names",names,NULL);
        break;
      }
      g_free (name);
    }
  }
  g_value_array_free (names);
}

void
cairo_menu_applet_remove_icon (CairoMenuApplet * applet, AwnThemedIcon * icon)
{
  gchar * menu_name;
  gchar * display_name;
  gchar * icon_name;
  gchar * str;
  GList * s;
  gint  idx;
  GValueArray * names;
  GList * iter;

  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);

  g_object_get (icon,
                "menu_name",&menu_name,
                "display_name",&display_name,
                "icon_name",&icon_name,
                NULL);

  str = g_strdup_printf("%s###%s###%s",menu_name,display_name,icon_name);

  g_object_get (applet,"aux_menu_names",&names,NULL);
  if (names)
  {
    for (idx = 0; idx < names->n_values; idx++)
    {
      gchar *name;
      name = g_value_dup_string (g_value_array_get_nth (names, idx));
      if (g_strcmp0 (name,str)==0)
      {
        GValueArray* s = g_value_array_remove (names, idx);
//        g_value_array_free (s);
        g_object_set (applet,"aux_menu_names",names,NULL);
        break;
      }
      g_free (name);
    }
  }
  g_value_array_free (names);
  gtk_container_remove (GTK_CONTAINER(priv->box), GTK_WIDGET(icon));

  cairo_menu_applet_remove_hidden_menu (applet,menu_name);
  cairo_main_icon_refresh_menu (priv->main_icon);

  g_free (menu_name);
  g_free (display_name);
  g_free (icon_name);
  g_free (str);

}

void
cairo_menu_applet_add_icon (CairoMenuApplet * applet, gchar * menu_name, gchar * display_name, gchar * icon_name)
{
  gchar * str;
  GtkWidget * icon;
//  gchar * base;
  GValue val = {0,};
  GValueArray * names;
  GList * iter;

  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);

  str = g_strdup_printf("%s###%s###%s",menu_name,display_name,icon_name);
  cairo_menu_applet_append_hidden_menu (applet,menu_name);

  g_object_get (G_OBJECT (applet), "aux_menu_names", &names, NULL);
  g_value_init (&val, G_TYPE_STRING);
  g_value_set_string (&val, str);
  names = g_value_array_append (names, &val);
  g_object_set (G_OBJECT (applet), "aux_menu_names", names, NULL);
  g_value_unset (&val);
  g_value_array_free (names);

  icon = cairo_aux_icon_new (AWN_APPLET(applet),menu_name,display_name,icon_name);
  gtk_widget_show (icon);
  gtk_container_add (GTK_CONTAINER(priv->box),icon);

  cairo_main_icon_refresh_menu (priv->main_icon);
}
