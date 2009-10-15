/* cairo-menu-applet.h */

#ifndef _CAIRO_MENU_APPLET
#define _CAIRO_MENU_APPLET

#include <libawn/awn-applet.h>
#include <glib-object.h>

G_BEGIN_DECLS

typedef const gchar * (*GetRunCmdFunc )(AwnApplet * applet);
typedef GtkWidget * (* MenuBuildFunc) (AwnApplet *,GetRunCmdFunc);


typedef enum 
{
  MENU_TYPE_GUESS,
  MENU_TYPE_GNOME,
  MENU_TYPE_XFCE
}DEMenuType;

#define AWN_TYPE_CAIRO_MENU_APPLET cairo_menu_applet_get_type()

#define AWN_CAIRO_MENU_APPLET(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_MENU_APPLET, CairoMenuApplet))

#define AWN_CAIRO_MENU_APPLET_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_MENU_APPLET, CairoMenuAppletClass))

#define AWN_IS_CAIRO_MENU_APPLET(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_MENU_APPLET))

#define AWN_IS_CAIRO_MENU_APPLET_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_MENU_APPLET))

#define AWN_CAIRO_MENU_APPLET_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_MENU_APPLET, CairoMenuAppletClass))

typedef struct {
  AwnApplet parent;
} CairoMenuApplet;

typedef struct {
  AwnAppletClass parent_class;
} CairoMenuAppletClass;

GType cairo_menu_applet_get_type (void);

CairoMenuApplet* cairo_menu_applet_new (const gchar *name,const gchar* uid, gint panel_id);

const gchar * cairo_menu_applet_get_run_cmd (CairoMenuApplet * applet);

G_END_DECLS

#endif /* _CAIRO_MENU_APPLET */
