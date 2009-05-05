/* Awn-sysmonicon.h */

#ifndef _AWN_SYSMONICON
#define _AWN_SYSMONICON

#include <glib-object.h>

G_BEGIN_DECLS

#define AWN_TYPE_sysmonicon Awn_sysmonicon_get_type()

#define AWN_sysmonicon(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_sysmonicon, AwnSysmonicon))

#define AWN_sysmonicon_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_sysmonicon, AwnSysmoniconClass))

#define AWN_IS_sysmonicon(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_sysmonicon))

#define AWN_IS_sysmonicon_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_sysmonicon))

#define AWN_sysmonicon_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_sysmonicon, AwnSysmoniconClass))

typedef struct {
  AwnIcon parent;
} AwnSysmonicon;

typedef struct {
  AwnIconClass parent_class;
} AwnSysmoniconClass;

GType Awn_sysmonicon_get_type (void);

AwnSysmonicon* Awn_sysmonicon_new (void);

G_END_DECLS

#endif /* _AWN_SYSMONICON */
