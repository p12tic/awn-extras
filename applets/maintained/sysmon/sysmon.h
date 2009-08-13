/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Library General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor Boston, MA 02110-1301,  USA
 */
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

AwnSysmon* awn_sysmon_new (const gchar * name,const gchar *uid,gint panel_id);

G_END_DECLS

#endif /* _AWN_SYSMON */
