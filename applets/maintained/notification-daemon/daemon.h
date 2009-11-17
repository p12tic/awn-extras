/*
 * daemon.h - Implementation of the destop notification spec
 *
 * Copyright (C) 2006 Christian Hammond <chipx86@chipx86.com>
 * Copyright (C) 2005 John (J5) Palmieri <johnp@redhat.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2, or (at your option)
 * any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 */
#ifndef NOTIFY_DAEMON_H
#define NOTIFY_DAEMON_H

#include <libawn/libawn.h>
#include <glib.h>
#include <glib-object.h>

#include <dbus/dbus-glib.h>
#include <dbus/dbus-glib-lowlevel.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <glib/gmacros.h>
#include <glib/gerror.h>
#include <gconf/gconf-value.h>

#include <libawn/awn-dialog.h>
#include <libawn/awn-cairo-utils.h>

#define APPLET_NAME "awn-notification-daemon"

#define GCONF_KEY_DAEMON         "/apps/notification-daemon"
#define GCONF_KEY_THEME          GCONF_KEY_DAEMON "/theme"
#define GCONF_KEY_POPUP_LOCATION GCONF_KEY_DAEMON "/popup_location"
#define GCONF_KEY_SOUND_ENABLED  GCONF_KEY_DAEMON "/sound_enabled"
#define GCONF_KEY_DEFAULT_SOUND  GCONF_KEY_DAEMON "/default_sound"

#define GCONF_AWN ""
#define GCONF_KEY_AWN_KILL_ND GCONF_AWN "kill_standard_daemon"
#define GCONF_KEY_AWN_BG GCONF_AWN "bg_colour"
#define GCONF_KEY_AWN_BORDER GCONF_AWN "border_colour"
#define GCONF_KEY_AWN_BORDER_WIDTH GCONF_AWN "border_width"
#define GCONF_KEY_AWN_GRADIENT_FACTOR GCONF_AWN "gradient_factor"
#define GCONF_KEY_AWN_TEXT_COLOUR  GCONF_AWN "text_colour"
#define GCONF_KEY_AWN_CLIENT_POS  GCONF_AWN "honour_client_posxy"
#define GCONF_KEY_AWN_HONOUR_GTK  GCONF_AWN "honour_gtk"
#define GCONF_KEY_AWN_OVERRIDE_X  GCONF_AWN "override_x"
#define GCONF_KEY_AWN_OVERRIDE_Y  GCONF_AWN "override_y"
#define GCONF_KEY_AWN_TIMEOUT  GCONF_AWN "override_override_timeout"
#define GCONF_KEY_AWN_BOLD_BODY  GCONF_AWN "bold_text_body"
#define GCONF_KEY_AWN_SHOW_ICON GCONF_AWN "show_icon"
#define GCONF_KEY_AWN_HIDE_OPACITY GCONF_AWN "hide_opacity"

#define NOTIFY_TYPE_DAEMON (notify_daemon_get_type())
#define NOTIFY_DAEMON(obj) \
  (G_TYPE_CHECK_INSTANCE_CAST ((obj), NOTIFY_TYPE_DAEMON, NotifyDaemon))
#define NOTIFY_DAEMON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_CAST ((klass), NOTIFY_TYPE_DAEMON, NotifyDaemonClass))
#define NOTIFY_IS_DAEMON(obj) \
  (G_TYPE_CHECK_INSTANCE_TYPE ((obj), NOTIFY_TYPE_DAEMON))
#define NOTIFY_IS_DAEMON_CLASS(klass) \
  (G_TYPE_CHECK_CLASS_TYPE ((klass), NOTIFY_TYPE_DAEMON))
#define NOTIFY_DAEMON_GET_CLASS(obj) \
  (G_TYPE_INSTANCE_GET_CLASS((obj), NOTIFY_TYPE_DAEMON, NotifyDaemonClass))

#define NOTIFY_DAEMON_DEFAULT_TIMEOUT 7000

enum
{
  URGENCY_LOW,
  URGENCY_NORMAL,
  URGENCY_CRITICAL
};

typedef enum
{
  NOTIFYD_CLOSED_EXPIRED = 1,
  NOTIFYD_CLOSED_USER = 2,
  NOTIFYD_CLOSED_API = 3,
  NOTIFYD_CLOSED_RESERVED = 4

} NotifydClosedReason;

typedef struct _NotifyDaemon        NotifyDaemon;

typedef struct _NotifyDaemonClass   NotifyDaemonClass;

typedef struct _NotifyDaemonPrivate NotifyDaemonPrivate;

struct _NotifyDaemon
{
  GObject parent;

  /*< private > */
  NotifyDaemonPrivate *priv;
};

struct _NotifyDaemonClass
{
  GObjectClass parent_class;
};

G_BEGIN_DECLS

GType notify_daemon_get_type(void);

GQuark notify_daemon_error_quark(void);

gboolean notify_daemon_notify_handler(NotifyDaemon *daemon,
                                      const gchar *app_name,
                                      guint id,
                                      const gchar *icon,
                                      const gchar *summary,
                                      const gchar *body,
                                      gchar **actions,
                                      GHashTable *hints,
                                      int timeout,
                                      DBusGMethodInvocation *context);

gboolean notify_daemon_close_notification_handler(NotifyDaemon *daemon,
    guint id, GError **error);

gboolean notify_daemon_get_capabilities(NotifyDaemon *daemon,
                                        char ***out_caps);

gboolean notify_daemon_get_server_information(NotifyDaemon *daemon,
    char **out_name,
    char **out_vendor,
    char **out_version,
    char **out_spec_ver);

DesktopAgnosticConfigClient  *get_conf_client(void);

typedef struct
{
  AwnApplet *awn_app;  //NULL
  int awn_app_height;  //0
  DesktopAgnosticColor *awn_border;
  DesktopAgnosticColor *awn_bg;
  DesktopAgnosticColor *awn_text;
  gchar * awn_text_str;
  gboolean awn_client_pos;
  gboolean awn_honour_gtk;
  int awn_override_y;
  int awn_override_x;
  int awn_border_width;
  float awn_gradient_factor;
  GdkPixbuf *awn_icon;
  int  timeout;   //0
  gboolean bold_text_body;
  gboolean    show_icon;
  gboolean    show_status;
  float hide_opacity;
}Notification_Daemon;

G_END_DECLS

#endif /* NOTIFY_DAEMON_H */
