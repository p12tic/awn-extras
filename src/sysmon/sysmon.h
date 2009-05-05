/* awn-sysmon.h */

#ifndef _AWN_SYSMON
#define _AWN_SYSMON

#include <glib-object.h>
#include <libawn/libawn.h>

G_BEGIN_DECLS

#define AWN_TYPE_SYSMON awn_sysmon_get_type()

#define AWN_SYSMON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), AWN_TYPE_SYSMON, AwnSysmon))

#define AWN_SYSMON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), AWN_TYPE_SYSMON, AwnSysmonClass))

#define AWN_IS_SYSMON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), AWN_TYPE_SYSMON))

#define AWN_IS_SYSMON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), AWN_TYPE_SYSMON))

#define AWN_SYSMON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS ((obj), AWN_TYPE_SYSMON, AwnSysmonClass))

typedef struct {
  AwnApplet parent;
} AwnSysmon;

typedef struct {
  AwnAppletClass parent_class;
} AwnSysmonClass;

GType awn_sysmon_get_type (void);

AwnSysmon* awn_sysmon_new (const gchar *uid,gint orient,gint offset,gint size);

G_END_DECLS

#endif /* _AWN_SYSMON */
