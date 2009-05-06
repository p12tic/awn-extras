/* awn-sysmonicon.h */

#ifndef _AWN_SYSMONICON
#define _AWN_SYSMONICON

#include <glib-object.h>
#include <libawn/awn-icon.h>

G_BEGIN_DECLS

#define AWN_TYPE_SYSMONICON awn_sysmonicon_get_type()

#define AWN_SYSMONICON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_SYSMONICON, AwnSysmonicon))

#define AWN_SYSMONICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_SYSMONICON, AwnSysmoniconClass))

#define AWN_IS_SYSMONICON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_SYSMONICON))

#define AWN_IS_SYSMONICON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_SYSMONICON))

#define AWN_SYSMONICON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_SYSMONICON, AwnSysmoniconClass))

typedef struct {
  AwnIcon parent;
} AwnSysmonicon;

typedef struct {
  AwnIconClass parent_class;
} AwnSysmoniconClass;

GType awn_sysmonicon_get_type (void);

GtkWidget* awn_sysmonicon_new (void);

G_END_DECLS

#endif /* _AWN_SYSMONICON */
