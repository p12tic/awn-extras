/*
 * Copyright (c) 2008   Rodney (moonbeam) Cryderman <rcryderman@gmail.com>
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
#define WNCK_I_KNOW_THIS_IS_UNSTABLE 1

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include <dbus/dbus-glib-bindings.h>
#include <fcntl.h>
#include <glib.h>
#include <glib/gstdio.h>
#include <gtk/gtk.h>
#include <libawn/awn-config-client.h>
#include <libawn-extras/awn-extras.h>
#include <libwnck/libwnck.h>
#include <stdlib.h>
#include <string.h>
#define _GNU_SOURCE
#include <stdio.h>
#include <sys/file.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <time.h>

#include "taskmand.h"
#include "server-bindings.h"

#define CONFIG_KEY(key) key
#define CONFIG_POS_GRAV       CONFIG_KEY("pos_gravity")
#define CONFIG_POS_OFFSET     CONFIG_KEY("pos_offset")

typedef struct
{
    gchar               *path;
    gchar               *desktop_file;
	GList               *queue_new_tasks;
	GList               *uid_list;
	GTree			    *response_list_tree;
	GTree               *grace_period_tree;
	Taskmand            *server;		
	WnckScreen		    *wnck_screen;	
	AwnConfigClient		*config;
	AwnConfigClient		*core_config;	
    int                 applet_list_locking_fd;
    guint               pos_gravity;                //0 for left. 1 for right.
    gint                pos_offset;                 //convert to neg if grav =1
    gchar               *positioner_uid;
}Taskman;

typedef struct
{
    time_t      timestamp;
    int         pid;
}New_Task;

Taskman * taskmanager=NULL;

//========================================================
/*Caution:  Dealing with a Tree of Lists*/
static void remove_from_response_tree(Taskman * taskmanager,ulong xid)
{
    GList * node_data;
    if (node_data=g_tree_lookup(taskmanager->response_list_tree,xid))
    {
        GList * iter;
        for(iter=g_list_first(node_data);iter;iter=g_list_next(iter) )
        {
            g_free(iter->data);
        }
        g_list_free(node_data);
        g_tree_remove(taskmanager->response_list_tree,xid);
    }
}

/*Caution:  Dealing with a Tree of Lists*/
static gboolean add_to_response_list(Taskman * taskmanager,ulong xid,gchar *uid)
{
    GList * response_list;
    response_list=g_tree_lookup(taskmanager->response_list_tree,(gpointer)xid);   
    if (!g_list_find_custom(response_list,uid,strcmp) )
    {
        response_list=g_list_prepend(response_list,g_strdup(uid));
        g_tree_replace(taskmanager->response_list_tree,xid,response_list);
    }
    return ( g_list_length(response_list) == g_list_length(taskmanager->uid_list) );
}

/*Caution:  Dealing with a Tree of Lists*/
static gboolean check_response_list(Taskman * taskmanager,ulong xid)
{
    GList * response_list;
    response_list=g_tree_lookup(taskmanager->response_list_tree,xid);
    printf("response = %d   , uid_list = %d\n",g_list_length(response_list),g_list_length(taskmanager->uid_list) );
    return ( g_list_length(response_list) == g_list_length(taskmanager->uid_list) );
}

//DBUS CRAP GOES HERE *****************************************************************************

G_DEFINE_TYPE(Taskmand, taskmand, G_TYPE_OBJECT);

static void taskmand_class_init(TaskmandClass *class) 
{
}

static void taskmand_init(Taskmand *server) 
{
	GError *error = NULL;
	DBusGProxy *driver_proxy;
	int request_ret;
	server->connection = dbus_g_bus_get(DBUS_BUS_SESSION, &error);
	if (server->connection == NULL)
	{
		g_warning("Unable to connect to dbus: %s", error->message);
		g_error_free(error);
		return;
	}
	dbus_g_object_type_install_info(taskmand_get_type(), &dbus_glib_taskmand_object_info);
	dbus_g_connection_register_g_object(server->connection, "/org/awnproject/taskmand", G_OBJECT(server));
	driver_proxy = dbus_g_proxy_new_for_name(server->connection, DBUS_SERVICE_DBUS, DBUS_PATH_DBUS, DBUS_INTERFACE_DBUS);
	if (!org_freedesktop_DBus_request_name (driver_proxy, "org.awnproject.taskmand", 0, &request_ret, &error)) 
	{
		g_warning("Unable to register service: %s", error->message);
		g_error_free(error);
	}	
	g_object_unref(driver_proxy);
}

gboolean taskmand_launcher_register(Taskmand *obj, gchar *uid, GError **error)
{
    g_message("Register %s\n",uid);
    GList * node=g_list_find_custom(taskmanager->uid_list,uid,strcmp);    
    if (!node)
        taskmanager->uid_list=g_list_append(taskmanager->uid_list,g_strdup(uid));    
	return TRUE;
}

gboolean taskmand_inform_task_ownership(Taskmand *obj, gchar *uid,gchar *id, gchar *request,gchar ** response,GError **error)
{
    gulong id_as_long=strtoul(id,NULL,10);	
    if( g_list_find_custom(taskmanager->uid_list,uid,strcmp))
    {
        gboolean all_responded=add_to_response_list(taskmanager,id_as_long,uid);
	    if (strcmp(request,"CLAIM")==0 )
	    {
	        if ( g_list_find(taskmanager->queue_new_tasks,id_as_long) )
	        {
	            taskmanager->queue_new_tasks=g_list_remove(taskmanager->queue_new_tasks,id_as_long);
	            g_message("taskmand: launcher claimed, uid=%s, id=%s\n",uid,id);
                *response=g_strdup("MANAGE");
                remove_from_response_tree(taskmanager,id_as_long);
                g_tree_remove(taskmanager->grace_period_tree,id_as_long);
	        }
	        else
	        {
                *response=g_strdup("HANDSOFF");	        //normally should not happen
	        }
        }
        else if (strcmp(request,"ACCEPT")==0 )
        {
	        if ( g_list_find(taskmanager->queue_new_tasks,id_as_long) ) 
	        {
	            if (all_responded || (g_tree_lookup(taskmanager->grace_period_tree,id_as_long)==1) )
	            {
	                g_message("taskmand: launcher accepted, uid=%s, id=%s\n",uid,id);
	                taskmanager->queue_new_tasks=g_list_remove(taskmanager->queue_new_tasks,id_as_long);
                    remove_from_response_tree(taskmanager,id_as_long);	
                    g_tree_remove(taskmanager->grace_period_tree,id_as_long);                                    
                    *response=g_strdup("MANAGE");                
                }                    
                else
                {
                    *response=g_strdup("WAIT");
                }
	        }
	        else
	        {
                *response=g_strdup("HANDSOFF");	
	        }        
        }                                        
        else
        {
            *response=g_strdup("HANDSOFF");
        }
    }
    else
        *response=g_strdup("RESET");                
	return TRUE;
}

gboolean taskmand_launcher_unregister(Taskmand *obj, gchar *uid, GError **error)
{
    GList * node=g_list_find_custom(taskmanager->uid_list,uid,strcmp);
    if (node)
    {
        g_message("Unregister:  uid=%s\n",uid);
        g_free(node->data);
        taskmanager->uid_list=g_list_delete_link(taskmanager->uid_list,node);
    }
	return TRUE;
}

gboolean taskmand_launcher_position(Taskmand *obj, gchar *uid, GError **error)
{
	g_message("received launcher position\n");
    g_free(taskmanager->positioner_uid);
    taskmanager->positioner_uid=g_strdup(uid);
	*error=NULL;
	return TRUE;
}

//END OF DBUS CRAP ***********************************************************************

static void config_get_string (AwnConfigClient *client, const gchar *key, gchar **str)
{
	*str = awn_config_client_get_string (client, AWN_CONFIG_CLIENT_DEFAULT_GROUP, key, NULL);
}

void init_config(Taskman * taskmanager)
{
	taskmanager->config = awn_config_client_new_for_applet ("taskmand", NULL);
	taskmanager->core_config = awn_config_client_new ();	
	taskmanager->applet_list_locking_fd=awn_config_client_key_lock_open( AWN_CONFIG_CLIENT_DEFAULT_GROUP  ,"applets_list");	
	g_assert(taskmanager->applet_list_locking_fd != -1);
    taskmanager->desktop_file=g_strdup("standalone-launcher.desktop");
    taskmanager->path=NULL;
    taskmanager->pos_gravity=1 & 1; 
//    taskmanager->pos_offset= ABS(6) * (1 - taskmanager->pos_gravity*2);
    taskmanager->pos_offset= ABS(0) * (1 - taskmanager->pos_gravity*2);
    
	taskmanager->pos_gravity=awn_config_client_get_int(taskmanager->config,AWN_CONFIG_CLIENT_DEFAULT_GROUP,CONFIG_POS_GRAV, NULL)&1;    
	taskmanager->pos_offset =awn_config_client_get_int(taskmanager->config,AWN_CONFIG_CLIENT_DEFAULT_GROUP,CONFIG_POS_OFFSET, NULL)
	                                            * (1 - taskmanager->pos_gravity*2);
    taskmanager->positioner_uid=NULL;
}

//==================================================

gboolean launch_anonymous_launcher(gulong xid)
{
    static time_t timer=-1;
    if (time(NULL)-timer < 2)
        g_usleep(G_USEC_PER_SEC * 0.50);    //awn tends to brain fart if applets_list changes multiple times in a short period
    timer=time(NULL);                               
    if ( ! check_response_list(taskmanager,xid) )
    {
        g_message("taskmand: A LAUNCHER TIMED OUT !!!!!!!!!!!!!!!!!! or awn-core still hasn't been fixed\n");
    }
    remove_from_response_tree(taskmanager,xid);	
    while( awn_config_client_key_lock(taskmanager->applet_list_locking_fd, LOCK_EX))
        g_warning("taskmand: failed to acquire lock\n");
    GSList *applet_list=awn_config_client_get_list(taskmanager->core_config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                            "applets_list", AWN_CONFIG_CLIENT_LIST_TYPE_STRING,NULL);
    char * applet_location=g_strdup_printf("%s::-%lu+%ld",taskmanager->path,xid,(long)time(NULL));
//    applet_list=g_list_append(applet_list,applet_location);
    
    
    GSList * insert_point=NULL;
    GSList * iter;
    for(iter=applet_list;iter;iter=g_slist_next(iter) ) //FIXME.. this is a quick hack. Do not leave this way. Not as bad as core though :-)
    {
        if ( g_strrstr_len(iter->data,strlen(iter->data) ,taskmanager->positioner_uid) )
        {
            insert_point=iter;
            break;
        }
    }
    if (!insert_point)
        insert_point=g_slist_nth(applet_list,g_list_length(applet_list)*taskmanager->pos_gravity+taskmanager->pos_offset );
    applet_list=g_slist_insert_before(applet_list,insert_point,applet_location);
    awn_config_client_set_list(taskmanager->core_config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                   "applets_list",AWN_CONFIG_CLIENT_LIST_TYPE_STRING,applet_list,NULL);
    awn_config_client_key_lock(taskmanager->applet_list_locking_fd, LOCK_UN  );
    return TRUE;
}

void clean_applet_list(void)
{
    while ( awn_config_client_key_lock(taskmanager->applet_list_locking_fd, LOCK_EX  ) )
        g_warning("taskmand: failed to acquire lock\n");
    GSList *applet_list=awn_config_client_get_list(taskmanager->core_config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                            "applets_list", AWN_CONFIG_CLIENT_LIST_TYPE_STRING,NULL);
    GSList * iter;
    for (iter=applet_list;iter;iter=g_slist_next(iter)) 
    {
        if (strstr(iter->data,"::-") )
        {
            applet_list=g_slist_remove(applet_list,iter->data);
            iter=applet_list;
            if (!iter)
            {
                break;
            }
        }
    }
    awn_config_client_set_list(taskmanager->core_config, AWN_CONFIG_CLIENT_DEFAULT_GROUP,
                                            "applets_list", AWN_CONFIG_CLIENT_LIST_TYPE_STRING,applet_list,NULL);
    awn_config_client_key_lock(taskmanager->applet_list_locking_fd, LOCK_UN  );
}

//Timers

gboolean _launcher_response_timeout(gpointer * xid_as_pointer)
{
    ulong xid = (ulong) xid_as_pointer;
    if (g_tree_lookup(taskmanager->grace_period_tree,xid)==-1)
    {
        g_tree_replace(taskmanager->grace_period_tree,xid,1);
        return TRUE;
    }
    g_tree_remove(taskmanager->grace_period_tree,xid); 
    if ( g_list_find(taskmanager->queue_new_tasks,xid) )
    {
        g_warning("taskmand: not claimed, xid=%lu, starting anonymous launcher\n",xid);
        launch_anonymous_launcher(xid);        
    }
	return FALSE;
}

//wnck crap

static void _application_closed(WnckScreen *screen,WnckApplication *app,Taskman * taskmanager)
{
    if (strcmp(wnck_application_get_name(app),"avant-window-navigator")==0)
    {
        g_message("taskmand:  avant-window-navigator closed.... taskmand exiting\n");
        clean_applet_list();        
        exit(0);
    }
}


static void _window_opened(WnckScreen *screen,WnckWindow *window,Taskman * taskmanager)
{
    if ( !wnck_window_is_skip_tasklist(window) )
    {
        ulong xid=wnck_window_get_xid(window);
        taskmanager->queue_new_tasks=g_list_append(taskmanager->queue_new_tasks,xid);
        g_timeout_add(425,(GSourceFunc)_launcher_response_timeout,xid);	            
        g_tree_replace(taskmanager->grace_period_tree,xid,-1);
    }        
}

static void _window_closed(WnckScreen *screen,WnckWindow *window,Taskman * taskmanager)
{
    ulong xid=wnck_window_get_xid(window);    
    remove_from_response_tree(taskmanager,xid);
    taskmanager->queue_new_tasks=g_list_remove(taskmanager->queue_new_tasks,xid);
} 

static gint _cmp_ptrs(gconstpointer a,gconstpointer b)
{
	return a-b;
}

void set_path(Taskman * taskmanager,char * bin_name)
{
    if (!taskmanager->path)
    {
        char *bin_path=g_find_program_in_path (bin_name);    
        char *prefix=g_path_get_dirname(bin_path);
        taskmanager->path=g_strdup_printf("%s/../lib/awn/applets/%s",prefix,taskmanager->desktop_file);
        if (!g_file_test(taskmanager->path,G_FILE_TEST_EXISTS) )
        {
            g_free(taskmanager->path);
            taskmanager->path=g_strdup_printf("%s/../lib64/awn/applets/%s",prefix,taskmanager->desktop_file);        
        }
        g_free(bin_path);
        g_free(prefix);
    }        
}

//-------------------------------------------------------------------------

static gboolean show_version = FALSE;

static GOptionEntry entries[] = 
{
  { "version", 'v', 0, G_OPTION_ARG_NONE, &show_version, "Version", NULL },
  { NULL }
};

int main (int argc, char *argv[])
{
    GError *error = NULL;
    GOptionContext *context;
    context = g_option_context_new ("- taskmand... an alternate awn task manager");
    g_option_context_add_main_entries (context, entries, GETTEXT_PACKAGE);
    g_option_context_add_group (context, gtk_get_option_group (TRUE));
    g_option_context_parse (context, &argc, &argv, &error);    
    if (show_version)
    {
        printf("taskmand version: %s","Not Implemented");
        exit(0);
    }
    GMainLoop *main_loop;
    taskmanager = g_malloc(sizeof(Taskman) );    
    g_type_init();
    init_config(taskmanager);
    set_path(taskmanager,argv[0]);
    g_message("taskmand... starting:%s\n",taskmanager->path);	
	taskmanager->response_list_tree=g_tree_new(_cmp_ptrs);
    taskmanager->grace_period_tree=g_tree_new(_cmp_ptrs);
	taskmanager->queue_new_tasks=NULL;
	taskmanager->uid_list=NULL;
    GdkDisplayManager*  disp_man=gdk_display_manager_get();
    g_assert(disp_man);
    GdkDisplay* disp=gdk_display_open(g_getenv("DISPLAY"));          //FIXME
    g_assert(disp);
    gdk_display_manager_set_default_display(disp_man,disp);    
    GdkScreen* screen=gdk_display_get_default_screen(disp);
    g_assert(screen);
    clean_applet_list();
    sleep(2);    
	wnck_set_client_type(WNCK_CLIENT_TYPE_PAGER )	;
	taskmanager->wnck_screen=wnck_screen_get_default();
	taskmanager->server = g_object_new(taskmand_get_type(), NULL);
    main_loop = g_main_loop_new(NULL, FALSE);
	g_signal_connect(G_OBJECT(taskmanager->wnck_screen),"window-closed",G_CALLBACK (_window_closed),taskmanager);  
	g_signal_connect(G_OBJECT(taskmanager->wnck_screen),"window-opened",G_CALLBACK (_window_opened),taskmanager);
	g_signal_connect(G_OBJECT(taskmanager->wnck_screen),"application-closed",G_CALLBACK (_application_closed),taskmanager);	  	  
    g_main_loop_run(main_loop);
	return 0;
}

