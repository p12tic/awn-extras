/* daemon.c - Implementation of the destop notification spec
 *
 * Awn related modifications by Rodney Cryderman <rcryderman@gmail.com>
 *
 * Base gnome-notification-daemon by
 * Copyright (C) 2006 Christian Hammond <chipx86@chipx86.com>
 * Copyright (C) 2005 John (J5) Palmieri <johnp@redhat.com>
 *
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

 
 /*tabsize =4*/
 
#include "config.h"

#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#include <dbus/dbus.h>
#include <dbus/dbus-glib.h>
#include <glib/gi18n.h>
#include <glib.h>
#include <glib-object.h>
#include <gtk/gtk.h>
#include <glib/gprintf.h>

#include <libnotify/notify.h>

#include <glib/gprintf.h>

#include <X11/Xproto.h>

#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/Xatom.h>
#include <gdk/gdkx.h>

#undef NDEBUG
#include <assert.h>

#define WNCK_I_KNOW_THIS_IS_UNSTABLE
#include <libwnck/libwnck.h>

#include <libawn/awn-applet.h>
#include <libawn/awn-applet-simple.h>
#include <libawn/awn-applet-gconf.h>
#include <libawn/awn-applet-dialog.h>


#include "daemon.h"
#include "engines.h"
#include "stack.h"
#include "notificationdaemon-dbus-glue.h"

#define IMAGE_SIZE 48

#define NW_GET_NOTIFY_ID(nw) \
	(GPOINTER_TO_UINT(g_object_get_data(G_OBJECT(nw), "_notify_id")))
#define NW_GET_NOTIFY_SENDER(nw) \
	(g_object_get_data(G_OBJECT(nw), "_notify_sender"))
#define NW_GET_DAEMON(nw) \
	(g_object_get_data(G_OBJECT(nw), "_notify_daemon"))

typedef struct
{
	NotifyStackLocation type;
	const gchar *identifier;

} PopupNotifyStackLocation;

typedef struct
{
  AwnApplet *applet;    
    
}AwnNotificationDaemon;


AwnApplet *G_awn_app=NULL;
int G_awn_app_height=0;
AwnColor G_awn_border;
AwnColor G_awn_bg;
AwnColor G_awn_text;
gchar * G_awn_text_str;
gboolean G_awn_client_pos;
gboolean G_awn_honour_gtk;
int G_awn_override_y;
int G_awn_override_x;
int G_awn_border_width;
float G_awn_gradient_factor;
GdkPixbuf *G_awn_icon;
int 	G_timeout=0;

const PopupNotifyStackLocation popup_stack_locations[] =
{
	{ NOTIFY_STACK_LOCATION_TOP_LEFT,     "top_left"     },
	{ NOTIFY_STACK_LOCATION_TOP_RIGHT,    "top_right"    },
	{ NOTIFY_STACK_LOCATION_BOTTOM_LEFT,  "bottom_left"  },
	{ NOTIFY_STACK_LOCATION_BOTTOM_RIGHT, "bottom_right" },
	{ NOTIFY_STACK_LOCATION_AWN,          "awn-dynamic" },
	{ NOTIFY_STACK_LOCATION_UNKNOWN,      NULL }
};

#define POPUP_STACK_DEFAULT_INDEX 4 /* XXX Hack! */

typedef struct
{
	GTimeVal expiration;
	GTimeVal paused_diff;
	gboolean has_timeout;
	gboolean paused;
	guint id;
	GtkWindow *nw;

} NotifyTimeout;

struct _NotifyDaemonPrivate
{
	guint next_id;
	guint timeout_source;
	GHashTable *notification_hash;
	gboolean url_clicked_lock;
	NotifyStack **stacks;
	gint stacks_size;
};


static GConfClient *gconf_client = NULL;
static DBusConnection *dbus_conn = NULL;

#define CHECK_DBUS_VERSION(major, minor) \
	(DBUS_MAJOR_VER > (major) || \
	 (DBUS_MAJOR_VER == (major) && DBUS_MINOR_VER >= (minor)))


#if !CHECK_DBUS_VERSION(0, 60)
/* This is a hack that will go away in time. For now, it's fairly safe. */
struct _DBusGMethodInvocation
{
	DBusGConnection *connection;
	DBusGMessage *message;
	const DBusGObjectInfo *object;
	const DBusGMethodInfo *method;
};
#endif /* D-BUS < 0.60 */

static void notify_daemon_finalize(GObject *object);
static void _close_notification(NotifyDaemon *daemon, guint id,
								gboolean hide_notification);
static void _emit_closed_signal(GtkWindow *nw);
static void _action_invoked_cb(GtkWindow *nw, const char *key);
static NotifyStackLocation get_stack_location_from_string(const char *slocation);

G_DEFINE_TYPE(NotifyDaemon, notify_daemon, G_TYPE_OBJECT);

static void
notify_daemon_class_init(NotifyDaemonClass *daemon_class)
{
	GObjectClass *object_class = G_OBJECT_CLASS(daemon_class);

	object_class->finalize = notify_daemon_finalize;

	g_type_class_add_private(daemon_class, sizeof(NotifyDaemonPrivate));
}

static void
_notify_timeout_destroy(NotifyTimeout *nt)
{
	gtk_widget_destroy(GTK_WIDGET(nt->nw));
	g_free(nt);
}

static void
notify_daemon_init(NotifyDaemon *daemon)
{
	NotifyStackLocation location;
	GConfClient *client = get_gconf_client();
	GdkDisplay *display;
	GdkScreen *screen;
	gchar *slocation;
	gint i;

	daemon->priv = G_TYPE_INSTANCE_GET_PRIVATE(daemon, NOTIFY_TYPE_DAEMON,
											   NotifyDaemonPrivate);

	daemon->priv->next_id = 1;
	daemon->priv->timeout_source = 0;

	slocation = gconf_client_get_string(client, GCONF_KEY_POPUP_LOCATION,
										NULL);
	location = get_stack_location_from_string(slocation);
	g_free(slocation);

	display = gdk_display_get_default();
	screen = gdk_display_get_default_screen(display);
	daemon->priv->stacks_size = gdk_screen_get_n_monitors(screen);
	daemon->priv->stacks = g_new0(NotifyStack *, daemon->priv->stacks_size);

	for (i = 0; i < daemon->priv->stacks_size; i++)
	{
		daemon->priv->stacks[i] = notify_stack_new(daemon, screen,
												   i, location);
	}

	daemon->priv->notification_hash =
		g_hash_table_new_full(g_int_hash, g_int_equal, g_free,
							  (GDestroyNotify)_notify_timeout_destroy);
							  
							  
    /*awn daemon specific initialization follows*/							  
}

static void
notify_daemon_finalize(GObject *object)
{
	NotifyDaemon *daemon       = NOTIFY_DAEMON(object);
	GObjectClass *parent_class = G_OBJECT_CLASS(notify_daemon_parent_class);

	g_hash_table_destroy(daemon->priv->notification_hash);
	g_free(daemon->priv);

	if (parent_class->finalize != NULL)
		parent_class->finalize(object);
}

static NotifyStackLocation
get_stack_location_from_string(const char *slocation)
{
	NotifyStackLocation stack_location = NOTIFY_STACK_LOCATION_DEFAULT;

	if (slocation == NULL || *slocation == '\0')
		return NOTIFY_STACK_LOCATION_DEFAULT;
	else
	{
		const PopupNotifyStackLocation *l;

		for (l = popup_stack_locations;
			 l->type != NOTIFY_STACK_LOCATION_UNKNOWN;
			 l++)
		{
			if (!strcmp(slocation, l->identifier))
				stack_location = l->type;
		}
	}

	return stack_location;
}

static DBusMessage *
create_signal(GtkWindow *nw, const char *signal_name)
{
	guint id = NW_GET_NOTIFY_ID(nw);
	gchar *dest = NW_GET_NOTIFY_SENDER(nw);
	DBusMessage *message;

	g_assert(dest != NULL);

	message = dbus_message_new_signal("/org/freedesktop/Notifications",
									  "org.freedesktop.Notifications",
									  signal_name);

	dbus_message_set_destination(message, dest);
	dbus_message_append_args(message,
							 DBUS_TYPE_UINT32, &id,
							 DBUS_TYPE_INVALID);

	return message;
}

static void
_action_invoked_cb(GtkWindow *nw, const char *key)
{
	NotifyDaemon *daemon = NW_GET_DAEMON(nw);
	guint id = NW_GET_NOTIFY_ID(nw);
	DBusMessage *message;

	message = create_signal(nw, "ActionInvoked");
	dbus_message_append_args(message,
							 DBUS_TYPE_STRING, &key,
							 DBUS_TYPE_INVALID);

	dbus_connection_send(dbus_conn, message, NULL);
	dbus_message_unref(message);

	_close_notification(daemon, id, TRUE);
}

static void
_emit_closed_signal(GtkWindow *nw)
{
	DBusMessage *message = create_signal(nw, "NotificationClosed");
	dbus_connection_send(dbus_conn, message, NULL);
	dbus_message_unref(message);
}

static void
_close_notification(NotifyDaemon *daemon, guint id, gboolean bhide_notification)
{
	NotifyDaemonPrivate *priv = daemon->priv;
	NotifyTimeout *nt;

	nt = (NotifyTimeout *)g_hash_table_lookup(priv->notification_hash, &id);

	if (nt != NULL)
	{
		_emit_closed_signal(nt->nw);

		if (bhide_notification)
			hide_notification(nt->nw);

		g_hash_table_remove(priv->notification_hash, &id);
	}
}

static void
_notification_destroyed_cb(GtkWindow *nw, NotifyDaemon *daemon)
{
	_close_notification(daemon, NW_GET_NOTIFY_ID(nw), FALSE);
}

static void
_mouse_entered_cb(GtkWindow *nw, GdkEventCrossing *event, NotifyDaemon *daemon)
{
	NotifyTimeout *nt;
	guint id;
	GTimeVal now;

	if (event->detail == GDK_NOTIFY_INFERIOR)
		return;

	id = NW_GET_NOTIFY_ID(nw);
	nt = (NotifyTimeout *)g_hash_table_lookup(daemon->priv->notification_hash,
											  &id);

	nt->paused = TRUE;
	g_get_current_time(&now);

	nt->paused_diff.tv_usec = nt->expiration.tv_usec - now.tv_usec;
	nt->paused_diff.tv_sec  = nt->expiration.tv_sec  - now.tv_sec;

	if (nt->paused_diff.tv_usec < 0)
	{
		nt->paused_diff.tv_usec += G_USEC_PER_SEC;
		nt->paused_diff.tv_sec--;
	}
}

static void
_mouse_exitted_cb(GtkWindow *nw, GdkEventCrossing *event,
				  NotifyDaemon *daemon)
{
	NotifyTimeout *nt;
	guint id;

	if (event->detail == GDK_NOTIFY_INFERIOR)
		return;

	id = NW_GET_NOTIFY_ID(nw);
	nt = (NotifyTimeout *)g_hash_table_lookup(daemon->priv->notification_hash,
											  &id);

	nt->paused = FALSE;
}

static gboolean
_is_expired(gpointer key, gpointer value, gpointer data)
{
	NotifyTimeout *nt = (NotifyTimeout *)value;
	gboolean *phas_more_timeouts = (gboolean *)data;
	time_t now_time;
	time_t expiration_time;
	GTimeVal now;

	if (!nt->has_timeout)
		return FALSE;

	g_get_current_time(&now);

	expiration_time = (nt->expiration.tv_sec * 1000) +
	                  (nt->expiration.tv_usec / 1000);
	now_time = (now.tv_sec * 1000) + (now.tv_usec / 1000);

	if (now_time > expiration_time)
	{
		notification_tick(nt->nw, 0);
		_emit_closed_signal(nt->nw);
		return TRUE;
	}
	else if (nt->paused)
	{
		nt->expiration.tv_usec = nt->paused_diff.tv_usec + now.tv_usec;
		nt->expiration.tv_sec  = nt->paused_diff.tv_sec  + now.tv_sec;

		if (nt->expiration.tv_usec >= G_USEC_PER_SEC)
		{
			nt->expiration.tv_usec -= G_USEC_PER_SEC;
			nt->expiration.tv_sec++;
		}
	}
	else
	{
		notification_tick(nt->nw, expiration_time - now_time);
	}

	*phas_more_timeouts = TRUE;

	return FALSE;
}

static gboolean
_check_expiration(gpointer data)
{
	NotifyDaemon *daemon = (NotifyDaemon *)data;
	gboolean has_more_timeouts = FALSE;

	g_hash_table_foreach_remove(daemon->priv->notification_hash,
								_is_expired, (gpointer)&has_more_timeouts);

	if (!has_more_timeouts)
		daemon->priv->timeout_source = 0;

	return has_more_timeouts;
}

static void
_calculate_timeout(NotifyDaemon *daemon, NotifyTimeout *nt, int timeout)
{
	if (timeout == 0)
		nt->has_timeout = FALSE;
	else
	{
		glong usec;
		if (G_timeout>0)
			timeout=G_timeout;
		nt->has_timeout = TRUE;

		if (timeout == -1)
			timeout = NOTIFY_DAEMON_DEFAULT_TIMEOUT;

		set_notification_timeout(nt->nw, timeout);

		usec = timeout * 1000;	/* convert from msec to usec */

		/*
		 * If it's less than 0, wrap around back to MAXLONG.
		 * g_time_val_add() requires a glong, and anything larger than
		 * MAXLONG will be treated as a negative value.
		 */
		if (usec < 0)
			usec = G_MAXLONG;

		g_get_current_time(&nt->expiration);
		g_time_val_add(&nt->expiration, usec);

		if (daemon->priv->timeout_source == 0)
		{
			daemon->priv->timeout_source =
				g_timeout_add(100, _check_expiration, daemon);
		}
	}
}

static guint
_store_notification(NotifyDaemon *daemon, GtkWindow *nw, int timeout)
{
	NotifyDaemonPrivate *priv = daemon->priv;
	NotifyTimeout *nt;
	guint id = 0;

	do
	{
		id = priv->next_id;

		if (id != UINT_MAX)
			priv->next_id++;
		else
			priv->next_id = 1;

		if (g_hash_table_lookup(priv->notification_hash, &id) != NULL)
			id = 0;

	} while (id == 0);

	nt = g_new0(NotifyTimeout, 1);
	nt->id = id;
	nt->nw = nw;

	_calculate_timeout(daemon, nt, timeout);

	g_hash_table_insert(priv->notification_hash,
						g_memdup(&id, sizeof(guint)), nt);

	return id;
}

static gboolean
_notify_daemon_process_icon_data(NotifyDaemon *daemon, GtkWindow *nw,
								 GValue *icon_data)
{
	const guchar *data = NULL;
	gboolean has_alpha;
	int bits_per_sample;
	int width;
	int height;
	int rowstride;
	int n_channels;
	gsize expected_len;
	GdkPixbuf *pixbuf;
	GValueArray *image_struct;
	GValue *value;
	GArray *tmp_array;
#if CHECK_DBUS_VERSION(0, 61)
	GType struct_type;

	struct_type = dbus_g_type_get_struct(
		"GValueArray",
		G_TYPE_INT,
		G_TYPE_INT,
		G_TYPE_INT,
		G_TYPE_BOOLEAN,
		G_TYPE_INT,
		G_TYPE_INT,
		dbus_g_type_get_collection("GArray", G_TYPE_UCHAR),
		G_TYPE_INVALID);

	if (!G_VALUE_HOLDS(icon_data, struct_type))
	{
		g_warning("_notify_daemon_process_icon_data expected a "
				  "GValue of type GValueArray");
		return FALSE;
	}
#endif /* D-BUS >= 0.61 */

	image_struct = (GValueArray *)g_value_get_boxed(icon_data);
	value = g_value_array_get_nth(image_struct, 0);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected position "
				  "0 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value, G_TYPE_INT))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 0 of the GValueArray to be of type int");
		return FALSE;
	}

	width = g_value_get_int(value);
	value = g_value_array_get_nth(image_struct, 1);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 1 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value, G_TYPE_INT))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 1 of the GValueArray to be of type int");
		return FALSE;
	}

	height = g_value_get_int(value);
	value = g_value_array_get_nth(image_struct, 2);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 2 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value, G_TYPE_INT))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 2 of the GValueArray to be of type int");
		return FALSE;
	}

	rowstride = g_value_get_int(value);
	value = g_value_array_get_nth(image_struct, 3);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 3 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value, G_TYPE_BOOLEAN))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 3 of the GValueArray to be of type gboolean");
		return FALSE;
	}

	has_alpha = g_value_get_boolean(value);
	value = g_value_array_get_nth(image_struct, 4);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 4 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value, G_TYPE_INT))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 4 of the GValueArray to be of type int");
		return FALSE;
	}

	bits_per_sample = g_value_get_int(value);
	value = g_value_array_get_nth(image_struct, 5);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 5 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value, G_TYPE_INT))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 5 of the GValueArray to be of type int");
		return FALSE;
	}

	n_channels = g_value_get_int(value);
	value = g_value_array_get_nth(image_struct, 6);

	if (value == NULL)
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 6 of the GValueArray to exist");
		return FALSE;
	}

	if (!G_VALUE_HOLDS(value,
					   dbus_g_type_get_collection("GArray", G_TYPE_UCHAR)))
	{
		g_warning("_notify_daemon_process_icon_data expected "
				  "position 6 of the GValueArray to be of type GArray");
		return FALSE;
	}

	tmp_array = (GArray *)g_value_get_boxed(value);
	expected_len = (height - 1) * rowstride + width *
	               ((n_channels * bits_per_sample + 7) / 8);

	if (expected_len != tmp_array->len)
	{
		g_warning("_notify_daemon_process_icon_data expected image "
				  "data to be of length %i but got a length of %i",
				  expected_len, tmp_array->len);
		return FALSE;
	}

	data = (guchar *)g_memdup(tmp_array->data, tmp_array->len);
	pixbuf = gdk_pixbuf_new_from_data(data, GDK_COLORSPACE_RGB, has_alpha,
									  bits_per_sample, width, height,
									  rowstride,
									  (GdkPixbufDestroyNotify)g_free,
									  NULL);
	set_notification_icon(nw, pixbuf);
	g_object_unref(G_OBJECT(pixbuf));

	return TRUE;
}

static void
window_clicked_cb(GtkWindow *nw, GdkEventButton *button, NotifyDaemon *daemon)
{
	if (daemon->priv->url_clicked_lock)
	{
		daemon->priv->url_clicked_lock = FALSE;
		return;
	}

	_action_invoked_cb(nw, "default");
	_close_notification(daemon, NW_GET_NOTIFY_ID(nw), TRUE);
}

static void
popup_location_changed_cb(GConfClient *client, guint cnxn_id,
						  GConfEntry *entry, gpointer user_data)
{
	NotifyDaemon *daemon = (NotifyDaemon*)user_data;
	NotifyStackLocation stack_location;
	const char *slocation;
	GConfValue *value;
	gint i;

	if (daemon == NULL)
		return;

	value = gconf_entry_get_value(entry);
	slocation = (value != NULL ? gconf_value_get_string(value) : NULL);

	if (slocation != NULL && *slocation != '\0')
	{
		stack_location = get_stack_location_from_string(slocation);
	}
	else
	{
		gconf_client_set_string(get_gconf_client(),
			"/apps/notification-daemon/popup_location",
			popup_stack_locations[POPUP_STACK_DEFAULT_INDEX].identifier,
			NULL);

		stack_location = NOTIFY_STACK_LOCATION_DEFAULT;
	}

	for (i = 0; i < daemon->priv->stacks_size; i++)
		notify_stack_set_location(daemon->priv->stacks[i], stack_location);
}

static void
url_clicked_cb(GtkWindow *nw, const char *url)
{
	NotifyDaemon *daemon = NW_GET_DAEMON(nw);
	char *escaped_url;
	char *cmd = NULL;

	/* Somewhat of a hack.. */
	daemon->priv->url_clicked_lock = TRUE;

	escaped_url = g_shell_quote(url);
	/*
	 * We can't actually check for GNOME_DESKTOP_SESSION_ID, because it's
	 * not in the environment for this program :(
	 */
	if (
		g_find_program_in_path("gnome-open") != NULL)
	{
		cmd = g_strdup_printf("gnome-open %s", escaped_url);
	}
	else if (g_find_program_in_path("mozilla-firefox") != NULL)
	{
		cmd = g_strdup_printf("mozilla-firefox %s", escaped_url);
	}
	else if (g_find_program_in_path("firefox") != NULL)
	{
		cmd = g_strdup_printf("firefox %s", escaped_url);
	}
	else if (g_find_program_in_path("mozilla") != NULL)
	{
		cmd = g_strdup_printf("mozilla %s", escaped_url);
	}
	else
	{
		g_warning("Unable to find a browser.");
	}

	g_free(escaped_url);

	if (cmd != NULL)
	{
		g_spawn_command_line_async(cmd, NULL);
		g_free(cmd);
	}
}

static gboolean
screensaver_active(GtkWidget *nw)
{
	GdkDisplay *display = gdk_drawable_get_display(GDK_DRAWABLE(nw->window));
	Atom type;
	int format;
	unsigned long nitems, bytes_after;
	unsigned char *temp_data;
	gboolean active = FALSE;
	Atom XA_BLANK = gdk_x11_get_xatom_by_name_for_display(display, "BLANK");
	Atom XA_LOCK = gdk_x11_get_xatom_by_name_for_display(display, "LOCK");

	/* Check for a screensaver first. */
	if (XGetWindowProperty(
		GDK_DISPLAY_XDISPLAY(display),
		GDK_ROOT_WINDOW(),
		gdk_x11_get_xatom_by_name_for_display(display, "_SCREENSAVER_STATUS"),
		0, G_MAXLONG, False, XA_INTEGER, &type, &format, &nitems,
		&bytes_after, &temp_data) == Success &&
		type && temp_data != NULL)
	{
		CARD32 *data = (CARD32 *)temp_data;

		active = (type == XA_INTEGER && nitems >= 3 &&
				  (time_t)data[1] > (time_t)666000000L &&
				  (data[0] == XA_BLANK || data[0] == XA_LOCK));
	}

	if (temp_data != NULL)
		free(temp_data);

	return active;
}

static gboolean
fullscreen_window_exists(GtkWidget *nw)
{
	WnckScreen *wnck_screen;
	GList *l;

	wnck_screen = wnck_screen_get(GDK_SCREEN_XNUMBER(
		gdk_drawable_get_screen(GDK_DRAWABLE(GTK_WIDGET(nw)->window))));
	wnck_screen_force_update(wnck_screen);

	for (l = wnck_screen_get_windows_stacked(wnck_screen);
		 l != NULL;
		 l = l->next)
	{
		WnckWindow *wnck_win = (WnckWindow *)l->data;

		if (wnck_window_is_fullscreen(wnck_win))
		{
			/*
			 * Sanity check if the window is _really_ fullscreen to
			 * work around a bug in libwnck that doesn't get all
			 * unfullscreen events.
			 */
			int sw = wnck_screen_get_width(wnck_screen);
			int sh = wnck_screen_get_height(wnck_screen);
			int x, y, w, h;

			wnck_window_get_geometry(wnck_win, &x, &y, &w, &h);

			if (sw == w && sh == h)
				return TRUE;
		}
	}

	return FALSE;
}

gboolean
notify_daemon_notify_handler(NotifyDaemon *daemon,
							 const gchar *app_name,
							 guint id,
							 const gchar *icon,
							 const gchar *summary,
							 const gchar *body,
							 gchar **actions,
							 GHashTable *hints,
							 int timeout, DBusGMethodInvocation *context)
{
	NotifyDaemonPrivate *priv = daemon->priv;
	NotifyTimeout *nt = NULL;
	GtkWindow *nw = NULL;
	GValue *data;
	gboolean use_pos_data = FALSE;
	gboolean new_notification = FALSE;
	gint x = 0;
	gint y = 0;
	guint return_id;
	gchar *sender;
	gint i;

	if (id > 0)
	{
		nt = (NotifyTimeout *)g_hash_table_lookup(priv->notification_hash,
												  &id);

		if (nt != NULL)
			nw = nt->nw;
		else
			id = 0;
	}

	if (nw == NULL)
	{
		nw = create_notification(url_clicked_cb);
		g_object_set_data(G_OBJECT(nw), "_notify_daemon", daemon);
		gtk_widget_realize(GTK_WIDGET(nw));
		new_notification = TRUE;

		g_signal_connect(G_OBJECT(nw), "button-release-event",
						 G_CALLBACK(window_clicked_cb), daemon);
		g_signal_connect(G_OBJECT(nw), "destroy",
						 G_CALLBACK(_notification_destroyed_cb), daemon);
		g_signal_connect(G_OBJECT(nw), "enter-notify-event",
						 G_CALLBACK(_mouse_entered_cb), daemon);
		g_signal_connect(G_OBJECT(nw), "leave-notify-event",
						 G_CALLBACK(_mouse_exitted_cb), daemon);
	}
	else
	{
		clear_notification_actions(nw);
	}

	set_notification_text(nw, summary, body);
	set_notification_hints(nw, hints);

	/*
	 *XXX This needs to handle file URIs and all that.
	 */

	/* deal with x, and y hints */
	if ((data = (GValue *)g_hash_table_lookup(hints, "x")) != NULL)
	{
		x = g_value_get_int(data);

		if ((data = (GValue *)g_hash_table_lookup(hints, "y")) != NULL)
		{
			y = g_value_get_int(data);
			use_pos_data = TRUE;
		}
	}

	/* set up action buttons */
	for (i = 0; actions[i] != NULL; i += 2)
	{
		gchar *l = actions[i + 1];

		if (l == NULL)
		{
			g_warning("Label not found for action %s. "
					  "The protocol specifies that a label must "
					  "follow an action in the actions array", actions[i]);

			break;
		}

		if (strcasecmp(actions[i], "default"))
		{
			add_notification_action(nw, l, actions[i],
										  G_CALLBACK(_action_invoked_cb));
		}
	}

	/* check for icon_data if icon == "" */
	if (*icon == '\0')
	{
		data = (GValue *)g_hash_table_lookup(hints, "icon_data");

		if (data)
			_notify_daemon_process_icon_data(daemon, nw, data);
	}
	else
	{
		GdkPixbuf *pixbuf = NULL;

		if (!strncmp(icon, "file://", 7) || *icon == '/')
		{
			if (!strncmp(icon, "file://", 7))
				icon += 7;

			/* Load file */
			pixbuf = gdk_pixbuf_new_from_file(icon, NULL);
		}
		else
		{
			/* Load icon theme icon */
			GtkIconTheme *theme = gtk_icon_theme_get_default();
			GtkIconInfo *icon_info =
				gtk_icon_theme_lookup_icon(theme, icon, IMAGE_SIZE,
										   GTK_ICON_LOOKUP_USE_BUILTIN);

			if (icon_info != NULL)
			{
				gint icon_size = MIN(IMAGE_SIZE,
									 gtk_icon_info_get_base_size(icon_info));

				if (icon_size == 0)
					icon_size = IMAGE_SIZE;

				pixbuf = gtk_icon_theme_load_icon(theme, icon, icon_size,
												  GTK_ICON_LOOKUP_USE_BUILTIN,
												  NULL);

				gtk_icon_info_free(icon_info);
			}

			if (pixbuf == NULL)
			{
				/* Well... maybe this is a file afterall. */
				pixbuf = gdk_pixbuf_new_from_file(icon, NULL);
			}
		}

		if (pixbuf != NULL)
		{
			set_notification_icon(nw, pixbuf);
			g_object_unref(G_OBJECT(pixbuf));
		}
	}

	if ( (use_pos_data)  && G_awn_client_pos) 
	{
		/*
		 * Typically, the theme engine will set its own position based on
		 * the arrow X, Y hints. However, in case, move the notification to
		 * that position.
		 */
		set_notification_arrow(nw, TRUE, x, y);
		move_notification(nw, x, y);
	}
	else
	{
		gint monitor;
		GdkScreen *screen;
		gint x, y;

		set_notification_arrow(nw, FALSE, 0, 0);

		gdk_display_get_pointer(gdk_display_get_default(),
								&screen, &x, &y, NULL);
		monitor = gdk_screen_get_monitor_at_point(screen, x, y);
		g_assert(monitor >= 0 && monitor < priv->stacks_size);

		notify_stack_add_window(priv->stacks[monitor], nw, new_notification);
	}

	if (!screensaver_active(GTK_WIDGET(nw)) &&
		!fullscreen_window_exists(GTK_WIDGET(nw)))
	{
		show_notification(nw);
	}

	return_id = (id == 0 ? _store_notification(daemon, nw, timeout) : id);

#if CHECK_DBUS_VERSION(0, 60)
	sender = dbus_g_method_get_sender(context);
#else
	sender = g_strdup(dbus_message_get_sender(
		dbus_g_message_get_message(context->message)));
#endif

	g_object_set_data(G_OBJECT(nw), "_notify_id",
					  GUINT_TO_POINTER(return_id));
	g_object_set_data_full(G_OBJECT(nw), "_notify_sender", sender,
						   (GDestroyNotify)g_free);

	if (nt)
		_calculate_timeout(daemon, nt, timeout);

	dbus_g_method_return(context, return_id);

	return TRUE;
}

gboolean
notify_daemon_close_notification_handler(NotifyDaemon *daemon,
										 guint id, GError **error)
{
	_close_notification(daemon, id, TRUE);

	return TRUE;
}

gboolean
notify_daemon_get_capabilities(NotifyDaemon *daemon, char ***caps)
{
	*caps = g_new0(char *, 6);

	(*caps)[0] = g_strdup("actions");
	(*caps)[1] = g_strdup("body");
	(*caps)[2] = g_strdup("body-hyperlinks");
	(*caps)[3] = g_strdup("body-markup");
	(*caps)[4] = g_strdup("icon-static");
	(*caps)[5] = NULL;

	return TRUE;
}

gboolean
notify_daemon_get_server_information(NotifyDaemon *daemon,
									 char **out_name,
									 char **out_vendor,
									 char **out_version,
									 char **out_spec_ver)
{
	*out_name     = g_strdup("Notification Daemon");
	*out_vendor   = g_strdup("Galago Project");
	*out_version  = g_strdup(VERSION);
	*out_spec_ver = g_strdup("0.9");

	return TRUE;
}

GConfClient *
get_gconf_client(void)
{
	return gconf_client;
}

static void
_height_changed (AwnApplet *app, guint height, gpointer *data)
{
}

gboolean send_startup_message(gpointer data)
{
	NotifyNotification *notify;	
	gchar *summary = "Awn Notification Daemon Message";
	gchar *body = "Awn Notification Daemon has loaded Successfully.\nClick <a href=\"http://wiki.awn-project.org/index.php?title=Awn_Notification-Daemon\">Here</a> for online documentation.";
	gchar *type = NULL;
	gchar *icon_str = NULL;
	glong expire_timeout = NOTIFY_EXPIRES_DEFAULT;
    NotifyUrgency urgency = NOTIFY_URGENCY_NORMAL;
    GError *error = NULL;    
	
	if ( fork()==0 )
	{
        notify_init("notify-send");
    	notify = notify_notification_new(summary, body, icon_str, NULL);
    	notify_notification_set_category(notify, type);
    	notify_notification_set_urgency(notify, urgency);
    	notify_notification_set_timeout(notify, expire_timeout);    
        notify_notification_show(notify, NULL);

    	g_object_unref(G_OBJECT(notify));
    	notify_uninit();
    	exit(0);
    }    	
    return FALSE;
}

gboolean hide_icon(gpointer data)
{
    gtk_widget_set_size_request (GTK_WIDGET (G_awn_app), 1, 1);

    G_awn_icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,1,1);
    gdk_pixbuf_fill(G_awn_icon,0x00000000);  
    awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (G_awn_app),G_awn_icon);  
	G_awn_icon=NULL;
	return FALSE;
}

AwnApplet* awn_applet_factory_initp ( gchar* uid, gint orient, gint height )
{
	NotifyDaemon *daemon;
	DBusGConnection *connection;
	DBusGProxy *bus_proxy;
	GError *error;
	guint request_name_result;
	AwnApplet *applet;
    GConfValue*	 value;
    gchar * svalue;

    G_awn_app_height=height;

    G_awn_app = applet = AWN_APPLET (awn_applet_simple_new (uid, orient, height));
    
    g_signal_connect (G_OBJECT (applet), "height-changed", G_CALLBACK (_height_changed), (gpointer)applet);    
    gtk_widget_set_size_request (GTK_WIDGET (applet), height, height);

    G_awn_icon=gdk_pixbuf_new(GDK_COLORSPACE_RGB,TRUE,8,height,height);
    gdk_pixbuf_fill(G_awn_icon,0x00000033);  
    awn_applet_simple_set_temp_icon (AWN_APPLET_SIMPLE (applet),G_awn_icon);  
	G_awn_icon=NULL;

    gtk_widget_show_all (GTK_WIDGET (applet));


	g_log_set_always_fatal(G_LOG_LEVEL_ERROR | G_LOG_LEVEL_CRITICAL);

	gconf_client = gconf_client_get_default();
	gconf_client_add_dir(gconf_client, GCONF_KEY_DAEMON,
						 GCONF_CLIENT_PRELOAD_NONE, NULL);



	error = NULL;

	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);

	while (connection == NULL)
	{
		printf("Failed to open connection to bus: %s. sleeping 5 s.\n",
				   error->message);
		g_error_free(error);
    	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);		
        sleep(5);
	}

	dbus_conn = dbus_g_connection_get_connection(connection);
    assert(dbus_conn);
    
	dbus_g_object_type_install_info(NOTIFY_TYPE_DAEMON,
									&dbus_glib_notification_daemon_object_info);

	bus_proxy = dbus_g_proxy_new_for_name(connection,
										  "org.freedesktop.DBus",
										  "/org/freedesktop/DBus",
										  "org.freedesktop.DBus");
    assert(bus_proxy);
	while (!dbus_g_proxy_call(bus_proxy, "RequestName", &error,
						   G_TYPE_STRING, "org.freedesktop.Notifications",
						   G_TYPE_UINT, 0,
						   G_TYPE_INVALID,
						   G_TYPE_UINT, &request_name_result,
						   G_TYPE_INVALID))
	{
		printf("Could not aquire name: %s. sleeping 2 seconds", error->message);
		sleep(2);
	}

	daemon = g_object_new(NOTIFY_TYPE_DAEMON, NULL);
    assert(daemon);
    
	gconf_client_notify_add(gconf_client, GCONF_KEY_POPUP_LOCATION,
							popup_location_changed_cb, daemon,
							NULL, NULL);

	/* Emit signal to verify/set current key */
	gconf_client_notify(gconf_client, GCONF_KEY_POPUP_LOCATION);
	
    value=gconf_client_get(gconf_client, GCONF_KEY_AWN_KILL_ND,
										NULL);		
										
    if (value)
    {																		
        if (gconf_client_get_bool(gconf_client,GCONF_KEY_AWN_KILL_ND ,NULL) )
        {
            if ( system("pgrep notification-daemon && killall notification-daemon") == -1)
            {            
                printf("Failed to execute killall command: disable kill notication daemon and configure to kill daemon before loading applet\n");                
            }
            else
            {
                system("pgrep notification-daemon &&  killall -9 notification-daemon");
            }
        }        										     										
    }	
    else
    {
        gconf_client_set_bool (gconf_client,GCONF_KEY_AWN_KILL_ND,TRUE ,NULL);
        if ( system("pgrep notification-daemon && killall notification-daemon") == -1)
        {
            printf("Failed to execute killall command: disable kill notication daemon and configure to kill daemon before loading applet\n");                
        }        
        else
        {
            system("pgrep notification-daemon && killall -9 notification-daemon");
        }
        
    }		
    value=gconf_client_get(gconf_client, GCONF_KEY_AWN_CLIENT_POS,
										NULL);		
    if (value)
    {																		
        G_awn_client_pos=gconf_client_get_bool(gconf_client,GCONF_KEY_AWN_CLIENT_POS ,NULL);
    }
    else
    {
        G_awn_client_pos=TRUE;
        gconf_client_set_bool (gconf_client,GCONF_KEY_AWN_CLIENT_POS,G_awn_client_pos,NULL);
    }        
    
    value=gconf_client_get(gconf_client, GCONF_KEY_AWN_HONOUR_GTK,
										NULL);		
    if (value)
    {																		
        G_awn_honour_gtk=gconf_client_get_bool(gconf_client,GCONF_KEY_AWN_HONOUR_GTK ,NULL);
    }
    else
    {
        G_awn_honour_gtk=TRUE;
        gconf_client_set_bool (gconf_client,GCONF_KEY_AWN_HONOUR_GTK,G_awn_honour_gtk,NULL);
    }  
    
    svalue = gconf_client_get_string(gconf_client,GCONF_KEY_AWN_BG, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_KEY_AWN_BG, svalue=g_strdup("0a0a0abb"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_awn_bg );    
    g_free(svalue);
 
    svalue = gconf_client_get_string(gconf_client,GCONF_KEY_AWN_TEXT_COLOUR, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_KEY_AWN_TEXT_COLOUR, svalue=g_strdup("eeeeeebb"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_awn_text );    
    G_awn_text_str=g_strdup(svalue);
    if (strlen(G_awn_text_str)>6)
        G_awn_text_str[6]='\0';
    g_free(svalue);
            	
    svalue = gconf_client_get_string(gconf_client,GCONF_KEY_AWN_BORDER, NULL );
    if ( !svalue ) 
    {
        gconf_client_set_string(gconf_client , GCONF_KEY_AWN_BORDER, svalue=g_strdup("ffffffaa"), NULL );
    }
    awn_cairo_string_to_color( svalue,&G_awn_border );    
    g_free(svalue);     
    
    value=gconf_client_get(gconf_client,GCONF_KEY_AWN_BORDER_WIDTH,NULL);		
    if (value)
    {																		
        G_awn_border_width=gconf_client_get_int(gconf_client,GCONF_KEY_AWN_BORDER_WIDTH,NULL) ;
    }
    else             							
    {
        G_awn_border_width=3;
        gconf_client_set_int(gconf_client,GCONF_KEY_AWN_BORDER_WIDTH,G_awn_border_width ,NULL);        
    }

    value=gconf_client_get(gconf_client,GCONF_KEY_AWN_GRADIENT_FACTOR,NULL);		
    if (value)
    {																		
        G_awn_gradient_factor=gconf_client_get_float(gconf_client,GCONF_KEY_AWN_GRADIENT_FACTOR,NULL) ;
    }
    else             							
    {
        G_awn_gradient_factor=0.75;
        gconf_client_set_float (gconf_client,GCONF_KEY_AWN_GRADIENT_FACTOR,G_awn_gradient_factor ,NULL);        
    }
 
    value=gconf_client_get(gconf_client,GCONF_KEY_AWN_OVERRIDE_X,NULL);		
    if (value)
    {
        G_awn_override_x=gconf_client_get_int(gconf_client,GCONF_KEY_AWN_OVERRIDE_X,NULL) ;
    }
    else             							
    {
        G_awn_override_x=-1;
        gconf_client_set_int (gconf_client,GCONF_KEY_AWN_OVERRIDE_X,G_awn_override_x ,NULL);        
    }
    
    value=gconf_client_get(gconf_client,GCONF_KEY_AWN_OVERRIDE_Y,NULL);		
    if (value)
    {																		
        G_awn_override_y=gconf_client_get_int(gconf_client,GCONF_KEY_AWN_OVERRIDE_Y,NULL) ;
    }
    else             							
    {
        G_awn_override_y=-1;
        gconf_client_set_int (gconf_client,GCONF_KEY_AWN_OVERRIDE_Y,G_awn_override_y ,NULL);        
    }


    value=gconf_client_get(gconf_client,GCONF_KEY_AWN_TIMEOUT,NULL);		
    if (value)
    {																		
        G_timeout=gconf_client_get_int(gconf_client,GCONF_KEY_AWN_TIMEOUT,NULL) ;
    }
    else             							
    {
        G_timeout=-1;
        gconf_client_set_int (gconf_client,GCONF_KEY_AWN_TIMEOUT,G_timeout ,NULL);        
    }
  
	dbus_g_connection_register_g_object(connection,"/org/freedesktop/Notifications",G_OBJECT(daemon));
    
    g_timeout_add(5000, (GSourceFunc*)send_startup_message,NULL); 
    g_timeout_add(3000, (GSourceFunc*)hide_icon,NULL); 
    return applet;

}


