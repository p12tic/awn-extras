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
 
#ifndef _AWN_SYSMON_UTIL
#define _AWN_SYSMON_UTIL



#include <gtk/gtk.h>
#include <libawn/libawn.h>

#include <glibtop/proclist.h>
#include <glibtop/procstate.h>
#include <glibtop/proctime.h>

#include "defines.h"

typedef struct
{
  pid_t   pid;
  gdouble percent_cpu;
  glibtop_proc_state  proc_state;
  glibtop_proc_time  proc_time;
}AwnProcInfo;


gdouble get_double_time (void);

gint get_conf_value_int (GObject * object, gchar * prop_name);

void do_bridge ( AwnApplet * applet,GObject *object,
           gchar * instance_group,gchar * key_name,gchar * prop_name );

void connect_notify (GObject * object,gchar * prop_name,GCallback cb,gpointer data);

void update_process_info (void);

GList * get_process_info (void);

void  inc_process_info_users(void);

void dec_process_info_users(void);

#endif

