/* cairo-menu-applet.c */

#include <gtk/gtk.h>
#include <libawn/libawn.h>
#include "cairo-menu-applet.h"
#include "cairo-menu.h"
#include "cairo-main-icon.h"
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
  
};


static gchar * gnome_run_cmds[] = { "gnome-do","grun","gmrun","gnome-launch-box",
                          "gnome-panel-control --run-dialog",NULL};

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

const gchar *
cairo_menu_applet_get_run_cmd (CairoMenuApplet * applet)
{
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);
  gchar * p;
  gchar **iter;

  if (priv->run_cmd)
  {
    p = g_find_program_in_path (priv->run_cmd);
    if (p)
    {
      g_free (p);
      return priv->run_cmd;
    }
    else 
    {
      g_message ("Cairo Menu (%s): Configured run command (%s) not found",__func__,priv->run_cmd);
    }
  }
  g_message ("Cairo Menu (%s): Searching for run command...",__func__);
  for (iter = gnome_run_cmds; *iter; iter++)
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
  g_message ("No known run dialogs found.  Please configure");
}