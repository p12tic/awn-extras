/* cairo-menu-applet.h */

#ifndef _CAIRO_AUX_ICON
#define _CAIRO_AUX_ICON

#include <libawn/libawn.h>
#include <glib-object.h>

G_BEGIN_DECLS

#define AWN_TYPE_CAIRO_AUX_ICON cairo_aux_icon_get_type()

#define AWN_CAIRO_AUX_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_AUX_ICON, CairoAuxIcon))

#define AWN_CAIRO_AUX_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_AUX_ICON, CairoMainAuxClass))

#define AWN_IS_CAIRO_AUX_ICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_AUX_ICON))

#define AWN_IS_CAIRO_AUX_ICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_AUX_ICON))

#define AWN_CAIRO_AUX_ICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_AUX_ICON, CairoMainAuxClass))

typedef struct {
  AwnThemedIcon parent;
} CairoAuxIcon;

typedef struct {
  AwnThemedIconClass parent_class;
} CairoAuxIconClass;

GType cairo_aux_icon_get_type (void);

GtkWidget* cairo_aux_icon_new (AwnApplet * applet);

G_END_DECLS

#endif 
