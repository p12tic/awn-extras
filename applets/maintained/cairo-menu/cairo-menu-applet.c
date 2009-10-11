/* cairo-menu-applet.c */

#include <gtk/gtk.h>
#include "cairo-menu-applet.h"
#include "cairo-menu.h"
#include "gnome-menu-builder.h"
#include "config.h"

typedef GtkWidget * (* MenuBuildFunc) (void);

G_DEFINE_TYPE (CairoMenuApplet, cairo_menu_applet, AWN_TYPE_APPLET_SIMPLE)

#define GET_PRIVATE(o) \
  (G_TYPE_INSTANCE_GET_PRIVATE ((o), AWN_TYPE_CAIRO_MENU_APPLET, CairoMenuAppletPrivate))

typedef struct _CairoMenuAppletPrivate CairoMenuAppletPrivate;

struct _CairoMenuAppletPrivate {
  GtkWidget   *menu;
};


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
  G_OBJECT_CLASS (cairo_menu_applet_parent_class)->constructed (object);

/* 
   TODO fix the various travesties*/
  GError * error = NULL;
  gchar * filename = APPLETSDIR"/../../../lib/awn/applets/cairo-menu/gnome-menu-builder";
  g_debug ("%s",filename);
  MenuBuildFunc  menu_build;
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
  priv->menu = menu_build ();
  gtk_widget_show_all (priv->menu);
  g_signal_connect(object, "button-press-event", G_CALLBACK(_button_clicked_event), NULL);

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
_button_clicked_event (CairoMenuApplet *applet, GdkEventButton *event, gpointer null)
{
  GdkEventButton *event_button;
  event_button = (GdkEventButton *) event;
  CairoMenuAppletPrivate * priv = GET_PRIVATE (applet);
  
  if (event->button == 1)
  {
    gtk_menu_popup(GTK_MENU(priv->menu), NULL, NULL, NULL, NULL,
                            event_button->button, event_button->time);    
  }
  else if (event->button == 3)
  {
    static GtkWidget * menu=NULL;
    static GtkWidget * item;

    if (!menu)
    {
      menu = awn_applet_create_default_menu (AWN_APPLET(applet));
      item = gtk_menu_item_new_with_label("Preferences");
      
      gtk_widget_show(item);
      gtk_menu_set_screen(GTK_MENU(menu), NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);
//      g_signal_connect(G_OBJECT(item), "button-press-event", G_CALLBACK(_show_prefs), NULL);
      item=awn_applet_create_about_item_simple(AWN_APPLET(applet),
                                               "Copyright 2007,2008, 2009 Rodney Cryderman <rcryderman@gmail.com>",
                                               AWN_APPLET_LICENSE_GPLV2,
                                               NULL);
      gtk_menu_shell_append(GTK_MENU_SHELL(menu), item);      
      
    }

    gtk_menu_popup(GTK_MENU(menu), NULL, NULL, NULL, NULL,event_button->button, event_button->time);
  }
  return TRUE;
}

