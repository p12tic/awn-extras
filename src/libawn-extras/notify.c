/*
 * Copyright (c) 2007   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
 *
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place - Suite 330,
 * Boston, MA 02111-1307, USA.
 */


#include <glib.h>
#include <libnotify/notify.h>
#include <sys/types.h>
#include <sys/wait.h>

#include "awn-extras.h" 

static gboolean _do_wait(gpointer null)
{
	return (waitpid(-1, NULL,  WNOHANG) <= 0 ) ;
}

gboolean notify_message(gchar * summary, gchar * body,gchar * icon_str,glong timeout)
{
	NotifyNotification *notify;	
	gchar *type = NULL;
	gboolean  	success=FALSE;
	glong expire_timeout = NOTIFY_EXPIRES_DEFAULT;
	if (timeout>0)
	{
		expire_timeout=timeout;
	}			
    NotifyUrgency urgency = NOTIFY_URGENCY_NORMAL;
    GError *error = NULL;    
    notify_init("notify-send");
	notify = notify_notification_new(summary, body, icon_str, NULL);
	if (notify)
	{
		notify_notification_set_category(notify, type);
		notify_notification_set_urgency(notify, urgency);
		notify_notification_set_timeout(notify, expire_timeout);    
		notify_notification_show(notify, NULL);
		g_object_unref(G_OBJECT(notify));
		success=TRUE;
	}	
	else
	{
		g_warning("libawn-extras: notify_message().  Failed to send notification\n");
	}	
	notify_uninit(); 
	return success; 	
}


void notify_message_async(gchar * summary, gchar * body,gchar * icon_str,glong timeout)
{	
	if ( fork()==0 )
	{
		notify_message(summary,body,icon_str,timeout);
    	exit(0);
    }      
	g_timeout_add(3000, (GSourceFunc*)_do_wait,NULL);     
}



