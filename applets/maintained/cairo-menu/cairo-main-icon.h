/* cairo-menu-applet.h */

#ifndef _CAIRO_MAIN_ICON
#define _CAIRO_MAIN_ICON

#include <libawn/libawn.h>
#include <glib-object.h>

G_BEGIN_DECLS

#define AWN_TYPE_CAIRO_MAIN_ICON cairo_main_icon_get_type()

#define AWN_CAIRO_MAIN_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_MAIN_ICON, CairoMainIcon))

#define AWN_CAIRO_MAIN_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_MAIN_ICON, CairoMainIconClass))

#define AWN_IS_CAIRO_MAIN_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_MAIN_ICON))

#define AWN_IS_CAIRO_MAIN_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_MAIN_ICON))

#define AWN_CAIRO_MAIN_ICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_MAIN_ICON, CairoMainIconClass))

typedef struct {
  AwnThemedIcon parent;
} CairoMainIcon;

typedef struct {
  AwnThemedIconClass parent_class;
} CairoMainIconClass;

GType cairo_main_icon_get_type (void);

GtkWidget* cairo_main_icon_new (AwnApplet * applet);

G_END_DECLS

#endif /* _CAIRO_MENU_APPLET */
