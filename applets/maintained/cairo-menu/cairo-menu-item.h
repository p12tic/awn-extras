/* cairo-menu-item.h */

#ifndef _CAIRO_MENU_ITEM
#define _CAIRO_MENU_ITEM

#include <gtk/gtk.h>

G_BEGIN_DECLS

#define AWN_TYPE_CAIRO_MENU_ITEM cairo_menu_item_get_type()

#define AWN_CAIRO_MENU_ITEM(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItem))

#define AWN_CAIRO_MENU_ITEM_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItemClass))

#define AWN_IS_CAIRO_MENU_ITEM(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_CAIRO_MENU_ITEM))

#define AWN_IS_CAIRO_MENU_ITEM_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_CAIRO_MENU_ITEM))

#define AWN_CAIRO_MENU_ITEM_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_CAIRO_MENU_ITEM, CairoMenuItemClass))

typedef struct {
  GtkImageMenuItem parent;
} CairoMenuItem;

typedef struct {
  GtkImageMenuItemClass parent_class;
} CairoMenuItemClass;

GType cairo_menu_item_get_type (void);

GtkWidget* cairo_menu_item_new (void);

G_END_DECLS

#endif /* _CAIRO_MENU_ITEM */
