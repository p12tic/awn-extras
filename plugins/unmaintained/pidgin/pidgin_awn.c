/*
 * AWN plugin for GAIM
 * Copyright (C) 2007 Michael (mycroes) Croes <mycroes@gmail.com>
 * Copyright from other people that wrote code with another purpose:
 * Copyright (C) 2002-3 Robert McQueen <robot101@debian.org>
 * Copyright (C) 2003 Herman Bloggs <hermanator12002@yahoo.com>
 *
 * Inspired by a similar plugin by:
 * Robert McQueen <robot101@debian.org>
 * Herman Bloggs <hermanator12002@yahoo.com>
 * Which was in turn inspired by a similar plugin by:
 *  John (J5) Palmieri <johnp@martianrock.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
 * 02111-1307, USA.
 */

#define PURPLE_PLUGINS

/*#include "internal.h"
#include "pidgin.h"*/

//#include "core.h"
#include "conversation.h"
#include "debug.h"
#include "plugin.h"
#include "prefs.h"
#include "signals.h"
#include "sound.h"
#include "version.h"
#include "status.h"

#include "gtkaccount.h"
#include "gtkblist.h"
#include "gtkconv.h"
#include "gtkplugin.h"
#include "gtkprefs.h"
#include "gtksavedstatuses.h"
#include "gtksound.h"
#include "gtkutils.h"
#include "pidginstock.h"
#include "gtkdocklet.h"
#include "gtkdialogs.h"

#include <stdlib.h>
#include <glib.h>
#include <dbus/dbus-glib.h>
#include <dbus/dbus-glib-bindings.h>

#include "pidgin_awn.h"

static AwnStatus status = AWN_STATUS_OFFLINE;

static PurplePluginInfo info = {
	PURPLE_PLUGIN_MAGIC,
	PURPLE_MAJOR_VERSION,
	PURPLE_MINOR_VERSION,
	PURPLE_PLUGIN_STANDARD,
	PIDGIN_PLUGIN_TYPE,
	0,
	NULL,
	PURPLE_PRIORITY_DEFAULT,
	
	"AWN plugin",
	"AWN plugin",
	VERSION,
	
	"Avant Window Navigator plugin",
	"A plugin for Pidgin to show useful information in AWN",
	"Michael Croes <mycroes@gmail.com>",
	"http://code.google.com/p/awn-plugins",
	
	plugin_load,
	plugin_unload,
	NULL,
	
	NULL,
	NULL,
	NULL,
	NULL
};

static void setAwnIcon(char *filename) {
	DBusGConnection *connection;
	DBusGProxy *proxy;
	GError *error;	

	g_type_init();
	
	error = NULL;
	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);
	
	if (connection != NULL)
	{
		proxy = dbus_g_proxy_new_for_name(
				connection,
				"com.google.code.Awn",
				"/com/google/code/Awn",
				"com.google.code.Awn");
		error = NULL;
		dbus_g_proxy_call(proxy, "SetTaskIconByName", &error, G_TYPE_STRING,
				"pidgin", G_TYPE_STRING, filename, G_TYPE_INVALID);
	}
}

static void unsetAwnIcon() {
	DBusGConnection *connection;
	DBusGProxy *proxy;
	GError *error;	
	
	g_type_init();
	
	error = NULL;
	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);
	
	if (connection != NULL)
	{
		proxy = dbus_g_proxy_new_for_name(
				connection,
				"com.google.code.Awn",
				"/com/google/code/Awn",
				"com.google.code.Awn");
		error = NULL;
		dbus_g_proxy_call(proxy, "UnsetTaskIconByName", &error,
				G_TYPE_STRING, "pidgin", G_TYPE_INVALID);
	}
}

static void setAwnInfo(char *info) {
	DBusGConnection *connection;
	DBusGProxy *proxy;
	GError *error;	
	
	g_type_init();
	
	error = NULL;
	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);
	
	if (connection != NULL)
	{
		proxy = dbus_g_proxy_new_for_name(
				connection,
				"com.google.code.Awn",
				"/com/google/code/Awn",
				"com.google.code.Awn");
		error = NULL;
		dbus_g_proxy_call(proxy, "SetInfoByName", &error, G_TYPE_STRING,
				"pidgin", G_TYPE_STRING, info, G_TYPE_INVALID);
	}
}

static void setAwnInfoByXid(gint xid, char *info) {
	DBusGConnection *connection;
	DBusGProxy *proxy;
	GError *error;	
	
	g_type_init();
	
	error = NULL;
	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);
	
	if (connection != NULL)
	{
		proxy = dbus_g_proxy_new_for_name(
				connection,
				"com.google.code.Awn",
				"/com/google/code/Awn",
				"com.google.code.Awn");
		error = NULL;
		dbus_g_proxy_call(proxy, "SetInfoByXid", &error, G_TYPE_INT,
				xid, G_TYPE_STRING, info, G_TYPE_INVALID);
	}
}

static void unsetAwnInfo() {
	DBusGConnection *connection;
	DBusGProxy *proxy;
	GError *error;	
	
	g_type_init();
	
	error = NULL;
	connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);
	
	if (connection != NULL)
	{
		proxy = dbus_g_proxy_new_for_name(
				connection,
				"com.google.code.Awn",
				"/com/google/code/Awn",
				"com.google.code.Awn");
		error = NULL;
		dbus_g_proxy_call(proxy, "UnsetInfoByName", &error, G_TYPE_STRING,
				"pidgin", G_TYPE_INVALID);
	}
}

/****************************
 * helper functions
 ****************************/

static void update_icon(AwnStatus newStatus) {
	switch (newStatus) {
		case AWN_STATUS_OFFLINE:
			setAwnIcon(PATH_IMG_OFFLINE);
			break;
		case AWN_STATUS_ONLINE:
			setAwnIcon(PATH_IMG_ONLINE);
			break;
		case AWN_STATUS_BUSY:
			setAwnIcon(PATH_IMG_BUSY);
			break;
		case AWN_STATUS_EXTENDED_AWAY:
			setAwnIcon(PATH_IMG_EXTENDED_AWAY);
			break;
		case AWN_STATUS_AWAY:
			setAwnIcon(PATH_IMG_AWAY);
			break;
		case AWN_STATUS_INVISIBLE:
			setAwnIcon(PATH_IMG_INVISIBLE);
			break;
		case AWN_STATUS_NEW_IM:
			setAwnIcon(PATH_IMG_NEW_IM);
			break;
		default:
			setAwnIcon(PATH_IMG_CONNECTING);
	}
}

static GList * get_pending_list()
{
	GList *l_im = NULL;
	GList *l_chat = NULL;
	
	l_im = pidgin_conversations_find_unseen_list(PURPLE_CONV_TYPE_IM,
			PIDGIN_UNSEEN_TEXT, FALSE, 0);
	
	l_chat = pidgin_conversations_find_unseen_list(PURPLE_CONV_TYPE_CHAT,
			PIDGIN_UNSEEN_NICK, FALSE, 0);
	
	if (l_im != NULL && l_chat != NULL)
		return g_list_concat(l_im, l_chat);
	else if (l_im != NULL)
		return l_im;
	else
		return l_chat;
}

/****************************
 * the real work
 ****************************/

static gboolean awn_update_status()
{
	GList *convs, *l;
	int count;
	AwnStatus newstatus = AWN_STATUS_CONNECTING;
	gboolean pending = FALSE;
	char awn_info[5];
	
	/* unseen messages */ /* no need to limit for awn :) */
	convs = get_pending_list(); /* DOCKLET_TOOLTIP_LINE_LIMIT */
	
	if (convs != NULL) {
		pending = TRUE;
		/* set tooltip if messages are pending */
		if (1) { /* if (showInfo/Tooltip) */
			for (l = convs, count = 0; l != NULL; l = l->next, count++) {
				if (PIDGIN_IS_PIDGIN_CONVERSATION(l->data)) {
					/* conv to count */
					PurpleConversation *conv = (PurpleConversation *)l->data;
					PidginConversation *gtkconv = PIDGIN_CONVERSATION(conv);
					/*Following lines get buddy list xid */
					/*PidginWindow *conv_window = pidgin_conv_get_window(gtkconv);
					GtkWidget *gtk_window = conv_window->window;*/
					
					sprintf(awn_info, "%u", (gint)gtkconv->unseen_count);
					setAwnInfo(awn_info);
					newstatus = AWN_STATUS_NEW_IM;
				}
			}
		}
		
		g_list_free(convs);
	} else {
		unsetAwnInfo();
	}
	
	for (l = purple_accounts_get_all(); l != NULL; l = l->next) {
		AwnStatus tmpstatus = AWN_STATUS_CONNECTING;
		
		PurpleAccount *account = (PurpleAccount *)l->data;
		PurpleStatus *account_status;
		

		if (!purple_account_get_enabled(account, PIDGIN_UI))
			continue;
		
		if (purple_account_is_disconnected(account))
			continue;
		
		account_status = purple_account_get_active_status(account);
		
		if (purple_account_is_connecting(account)) {
			tmpstatus = AWN_STATUS_CONNECTING;
		} else if (purple_status_is_online(account_status)) {
			switch (purple_status_type_get_primitive(purple_status_get_type(account_status))) {
				case PURPLE_STATUS_AWAY:
					tmpstatus = AWN_STATUS_AWAY;
					break;

				case PURPLE_STATUS_EXTENDED_AWAY:
					tmpstatus = AWN_STATUS_EXTENDED_AWAY;
					break;

				case PURPLE_STATUS_UNAVAILABLE:
					tmpstatus = AWN_STATUS_BUSY;
					break;

				case PURPLE_STATUS_OFFLINE:
					tmpstatus = AWN_STATUS_ONLINE;
					break;

				case PURPLE_STATUS_INVISIBLE:
					tmpstatus = AWN_STATUS_INVISIBLE;
					break;

				default:
					tmpstatus = AWN_STATUS_ONLINE;
					break;

			}
		}
		
		if (tmpstatus > newstatus)
			newstatus = tmpstatus;
		
	}
	
	if (status != newstatus) {
		status = newstatus;
		
		update_icon(status);
	}
	
	return FALSE;
}
			
		

/****************************
 * callbacks
 ****************************/

static void awn_update_status_cb(void *data)
{
	awn_update_status();
}

static void awn_conv_updated_cb(PidginConversation *conv, PurpleConvUpdateType type)
{
	if (type == PURPLE_CONV_UPDATE_UNSEEN)
		awn_update_status();
}

static void awn_signon_cb(PurpleConnection *gc)
{
	awn_update_status();
}

static void awn_signoff_cb(PurpleConnection *gc)
{
	awn_update_status();
}

static void buddy_signon_cb(PurpleBuddy *buddy) {
	
}

static void buddy_signoff_cb(PurpleBuddy *buddy) {
	
}

static void buddy_status_changed_cb(PurpleBuddy *buddy, PurpleStatus *old, PurpleStatus *new) {

}

static gboolean plugin_load(PurplePlugin *plugin) {
	void *blist_handle = purple_blist_get_handle(); /* unused by pidgin systray */
	void *conn_handle = purple_connections_get_handle();
	void *conv_handle = purple_conversations_get_handle();
	void *accounts_handle = purple_accounts_get_handle();
	
	purple_signal_connect(conn_handle, "signed-on", plugin,
			PURPLE_CALLBACK(awn_signon_cb), NULL);
	purple_signal_connect(conn_handle, "signed-off", plugin,
			PURPLE_CALLBACK(awn_signoff_cb), NULL);
	purple_signal_connect(accounts_handle, "account-status-changed", plugin,
			PURPLE_CALLBACK(awn_update_status_cb), NULL);
	purple_signal_connect(accounts_handle, "account-connecting", plugin,
			PURPLE_CALLBACK(awn_update_status_cb), NULL);
	purple_signal_connect(conv_handle, "received-im-msg", plugin,
			PURPLE_CALLBACK(awn_update_status_cb), NULL);
	purple_signal_connect(conv_handle, "conversation-created", plugin,
			PURPLE_CALLBACK(awn_update_status_cb), NULL);
	purple_signal_connect(conv_handle, "deleting-conversation", plugin,
			PURPLE_CALLBACK(awn_update_status_cb), NULL);
	purple_signal_connect(conv_handle, "conversation-updated", plugin,
			PURPLE_CALLBACK(awn_conv_updated_cb), NULL);
	purple_signal_connect(blist_handle, "buddy-signed-on", plugin,
			PURPLE_CALLBACK(buddy_signon_cb), NULL);
	purple_signal_connect(blist_handle, "buddy-signed-off", plugin,
			PURPLE_CALLBACK(buddy_signoff_cb), NULL);
	purple_signal_connect(blist_handle, "buddy-status-changed", plugin,
			PURPLE_CALLBACK(buddy_status_changed_cb), NULL);
	
	awn_update_status();
	update_icon(status);
	return TRUE;
}

static gboolean plugin_unload(PurplePlugin *plugin) {
	unsetAwnIcon();
	unsetAwnInfo();
	return TRUE;
}	

static void init_plugin(PurplePlugin *plugin) {
}

PURPLE_INIT_PLUGIN(pidgin_awn, init_plugin, info)
