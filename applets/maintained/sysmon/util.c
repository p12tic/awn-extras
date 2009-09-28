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
 
#include <glib.h>
#include "util.h"

gdouble 
get_double_time(void)
{
  GTimeVal  timeval;
  g_get_current_time (&timeval);
  return  timeval.tv_sec + timeval.tv_usec / 1000000.0;
}

gint 
get_conf_value_int ( GObject * object, gchar * prop_name)
{
  gint  i,b;
  gchar * base_prop_name = g_strdup_printf( "%s-base",prop_name);
  
  g_object_get(object,
               prop_name,&i,
               base_prop_name,&b,
               NULL);
  g_free (base_prop_name);
  
  /*CONDITIONAL operator*/
  return i?i:b;
}

void
do_bridge ( AwnApplet * applet,GObject *object,
           gchar * group, gchar * key_name,gchar * prop_name )
{
  DesktopAgnosticConfigClient * client;
  DesktopAgnosticConfigClient * client_baseconf;  
  gchar * base_prop_name = g_strdup_printf( "%s-base",prop_name);
  GError *error = NULL;
  
  g_object_get (applet,
                "client-baseconf", &client_baseconf,
                NULL);
  g_object_get (object,
                "client", &client,
                NULL);
  desktop_agnostic_config_client_bind (client,
                                       group, key_name,
                                       object, prop_name, FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       &error);

  if (error)
  {
    goto do_bridge_error;
  }

  desktop_agnostic_config_client_bind (client_baseconf,
                                       group, key_name,
                                       object, base_prop_name, FALSE,
                                       DESKTOP_AGNOSTIC_CONFIG_BIND_METHOD_INSTANCE,
                                       &error);
do_bridge_error:

  g_free (base_prop_name);

  if (error)
  {
    g_critical ("Config Bridge Error: %s", error->message);
    g_error_free (error);
  }
  
}

void
connect_notify (GObject * object,gchar * prop_name,GCallback cb,gpointer data)
{
  gchar * sig_name;
  
  sig_name = g_strdup_printf( "notify::%s",prop_name);  
  g_signal_connect (object, sig_name,cb,data);
  g_free (sig_name);
  sig_name = g_strdup_printf( "notify::%s-base",prop_name);  
  g_signal_connect (object, sig_name,cb,data);
  g_free(sig_name);
}


static GList * awn_proc_info=NULL;
static guint   awn_proc_timeout_id = 0;
static guint   awn_proc_users = 0;

static gint
_cmp_find_pid (AwnProcInfo *info, gpointer * pid_as_ptr)
{
  return (info->pid - GPOINTER_TO_INT(pid_as_ptr) );
}

gint
cmp_proc_info_percent_ascending (AwnProcInfo *left, AwnProcInfo *right)
{
  if (left->percent_cpu < right->percent_cpu  )
  {
    return -1;
  }
  else if (left->percent_cpu > right->percent_cpu )
  {
    return 1;
  }
  else
  {
    return 0;
  }
}

gint
cmp_proc_info_percent_descending (AwnProcInfo *left, AwnProcInfo *right)
{
  return cmp_proc_info_percent_ascending (right,left);
} 

gint
cmp_proc_state_cmd_ascending (AwnProcInfo *left, AwnProcInfo *right)
{
  return g_strcmp0( left->proc_state.cmd,right->proc_state.cmd);
}

gint
cmp_proc_state_cmd_descending (AwnProcInfo *left, AwnProcInfo *right)
{
  return cmp_proc_state_cmd_ascending (right,left);
}

gint
cmp_pid_ascending (AwnProcInfo *left, AwnProcInfo *right)
{
  return left->pid - right->pid;
}

gint
cmp_pid_descending (AwnProcInfo *left, AwnProcInfo *right)
{
  return cmp_pid_ascending (right,left);
}

GList *
get_process_info (void)
{
 return awn_proc_info; 
}

void
inc_process_info_users(void)
{
  awn_proc_users++;

  if (!awn_proc_timeout_id)
 {
   awn_proc_timeout_id = g_timeout_add_seconds ( 1,(GSourceFunc)update_process_info,NULL);
 }
}

void
dec_process_info_users(void)
{
  awn_proc_users--;
  if (!awn_proc_users)
  {
    g_source_remove (awn_proc_timeout_id);
    awn_proc_timeout_id = 0;
  }
}

void
update_process_info (void)
{
  static guint64 old_total_jiffies = 0;
  
  if (!awn_proc_users)
  {
    g_debug ("%s: no users",__func__);
    return;
  }
  pid_t * p;
  gint y ;
  glibtop_proclist proclist;
  GList * old_awn_proc_info=awn_proc_info;  
  guint64  total_jiffies;
  glibtop_cpu cpu;
  gdouble percent;
  gdouble total_per = 0;

  glibtop_get_cpu (&cpu);
  total_jiffies = cpu.total;
  
  awn_proc_info = NULL;

/*  p = glibtop_get_proclist(&proclist, GLIBTOP_KERN_PROC_RUID, getuid());*/
  p = glibtop_get_proclist(&proclist, GLIBTOP_KERN_PROC_ALL, -1);

//  g_debug ("number of entries = %d",proclist.number);
  for (y = 0;y < proclist.number;y++)
  {
    AwnProcInfo * data = g_malloc (sizeof(AwnProcInfo));
    GList       * search;    

    data->pid = p[y];
    glibtop_get_proc_state(&data->proc_state, p[y]);
    glibtop_get_proc_time(&data->proc_time, p[y]);

    search = g_list_find_custom (old_awn_proc_info,GINT_TO_POINTER(p[y]),
                                 (GCompareFunc)_cmp_find_pid);
    
    if (search)
    {
      AwnProcInfo * search_data = search->data;
      long time_diff;
      double jiffies;      
      
      jiffies = total_jiffies - old_total_jiffies;
//      g_debug ("%d  jiffies = %lf",p[y],jiffies);
      time_diff = (data->proc_time.utime + data->proc_time.stime) - (search_data->proc_time.utime+search_data->proc_time.stime);
//      g_debug ("%d  time diff = %ld",p[y],time_diff);
      percent = time_diff / (jiffies / cpu.frequency) ;
//      g_debug ("percent for %d = %lf",p[y],percent);
    }
    else
    {
      percent = 0;
    }
    data->percent_cpu = percent;
    total_per = total_per + percent;
    awn_proc_info = g_list_prepend (awn_proc_info,data);
  }
  g_list_foreach (old_awn_proc_info,(GFunc)g_free,NULL);  
  g_list_free (old_awn_proc_info);  
  g_free (p);
  old_total_jiffies = total_jiffies;
}

GList *
get_sorted_proc_list (GCompareFunc cmp_func)
{
  return g_list_sort (g_list_copy ( awn_proc_info),cmp_func);
}