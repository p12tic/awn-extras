/*
 * Copyright (c) 2007 Rodney Cryderman <rcryderman@gmail.com>
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


#include <glibtop/uptime.h>
#include <glibtop/proclist.h>
#include <glibtop/procstate.h>
#include <glibtop/proctime.h>
#include <glibtop/procuid.h>
#include <glibtop/procmem.h>
#include <glibtop/cpu.h>
#include <glibtop/mem.h>
#include <glibtop/procargs.h>

#define _GNU_SOURCE
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>
#include <signal.h>
#include <sys/types.h>

#include <dirent.h>
#include <libgen.h>

#include "awntop.h"
#include "dashboard.h"
#include "config.h"


#undef NDEBUG
#include <assert.h>


typedef struct
{
    guint64     proctime;
    gboolean    accessed;
}Proctimeinfo;


typedef struct
{
    char    *   name;
    gboolean (*fn) (GtkWidget *, GdkEventButton *, Awntop *);

}Tableheader;


static GtkWidget * get_event_box_label(const char * t, gfloat halign);
static GtkWidget * get_label_ld(const long t);
static GtkWidget * get_label_sz(const char * t, gfloat halign);
static GtkWidget * get_icon_button(Awntop * Awntop,char *name,const gchar *stock_id, GtkIconSize size);
static GtkWidget * get_icon_event_box(Awntop * Awntop,char *name,const gchar *stock_id, GtkIconSize size);
static GtkWidget * get_button_sz(const char * t);

static void build_top_table(Awntop *awntop,GtkWidget *);
static void build_top_table_headings(Awntop *awntop,GtkWidget *);

static Topentry ** fill_topentries(Awntop *awntop,int *numel);
static void free_topentries(Topentry **topentries, int num_top_entries);


static gint proctime_key_compare_func(gconstpointer a,gconstpointer b,   gpointer user_data);
static gboolean proctime_find_inactive(gpointer key,gpointer value,gpointer data);
static void proctimes_remove_inactive(gpointer data,gpointer user_data);
static gboolean proctime_reset_active(gpointer key,gpointer value,gpointer data);

static gint icons_key_compare_func(gconstpointer a,gconstpointer b,   gpointer user_data);


static int cmppid(const void *, const void *);
static int cmpuser(const void *, const void *);
static int cmpvirt(const void *, const void *);
static int cmpres(const void *, const void *);
static int cmpcpu(const void *, const void *);
static int cmpmem(const void *, const void *);
static int cmpcommand(const void *, const void *);

static gboolean _toggle_user_filter (GtkWidget *widget, GdkEventButton *event, Awntop *awntop);
static gboolean _click_pid (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_user (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_virt (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_res (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_cpu (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_mem (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_command (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _time_to_kill(GtkWidget *widget, GdkEventButton *event, long *);
static gboolean _time_to_kill_I_mean_it(GtkWidget *widget, GdkEventButton *event, long * pid);
static gboolean _toggle_display_freeze(GtkWidget *widget, GdkEventButton *event,Awntop *awntop);
static gboolean _change_Awntop_filter_state(GtkWidget *widget, GdkEventButton *event,Awntop *awntop);
static gboolean _increase_awntop_rows (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _decrease_awntop_rows (GtkWidget *widget, GdkEventButton *event, Awntop *);
static gboolean _click_set_term (GtkWidget *widget, GdkEventButton *event, Awntop *awntop);
static gboolean _click_set_kill (GtkWidget *widget, GdkEventButton *event, Awntop *awntop);
static gboolean _click_set_term_kill (GtkWidget *widget, GdkEventButton *event, Awntop *awntop);

static void parse_desktop_entries(Awntop * Awntop);
GtkWidget * lookup_icon(Awntop * Awntop,Topentry **topentries,int i);



Tableheader Global_tableheadings[]=
{
    {   "Process",  _click_pid},
    {   "Username",  _click_user},
    {   "Virtual",  _click_virt},
    {   "Resident",   _click_res},
    {   "%CPU",  _click_cpu},
    {   "%MEM",  _click_mem},
    {   " ",     NULL},
    {   "Command Line",  _click_command}
};

static int _Dummy_DUMMY=0;
static int  G_kill_signal_method=1;

static GdkPixbuf* Stock_Image_Used=(GdkPixbuf* ) (&_Dummy_DUMMY);


static int compmethod=1;

static int     gcomparedir;
static gboolean     top_state;

static void init_Awntop( Awntop * awntop);

static gboolean draw_top(GtkWidget ** pwidget,gint interval,void * data);
static gboolean query_support_multiple(void);

static GtkWidget* attach_right_click_menu(void * data);
static const char* get_component_name(void *);
static const char* get_component_friendly_name(void *d);

static void * plug_fns[MAX_CALLBACK_FN]={
                                        init_Awntop,
                                        NULL,
                                        draw_top,
                                        query_support_multiple,
                                        NULL,
                                        NULL,
                                        NULL,
                                        attach_right_click_menu,
                                        get_component_name,
                                        get_component_friendly_name                                        
                                        };

#define GCONF_AWNTOP_NUM_PROCS GCONF_PATH  "/component_awntop_num_procs"
#define GCONF_AWNTOP_KILL_SIG_METH GCONF_PATH  "/component_awntop_kill_sig_meth"
#define GCONF_AWNTOP_USER_FILTER GCONF_PATH  "/component_awntop_user_filter"

void * awntop_plug_lookup(int fn_id)
{
    assert(fn_id<MAX_CALLBACK_FN);
    return plug_fns[fn_id];
}

static const char* get_component_name(void *d)
{
    const char * name="component_awntop";
    return name;
}    

static const char* get_component_friendly_name(void *d)
{
    const char * name="AWN Top";
    return name;
}    



static GtkWidget* attach_right_click_menu(void * data)
{
    Awntop * awntop=data;
    GtkWidget * menu_items;
    GtkWidget *kill_menu = gtk_menu_new ();    
    
    GtkWidget *menu = gtk_menu_new ();
    
    menu_items = gtk_menu_item_new_with_label ("Increase Entries");
    gtk_menu_shell_append (GTK_MENU_SHELL (menu), menu_items);        
    g_signal_connect(       G_OBJECT (menu_items), 
                            "button-press-event",
                            G_CALLBACK (_increase_awntop_rows), 
                            (gpointer)awntop
                            );
    gtk_widget_show (menu_items);    

    menu_items = gtk_menu_item_new_with_label ("Decrease Entries");
    gtk_menu_shell_append (GTK_MENU_SHELL (menu), menu_items);        
    g_signal_connect(       G_OBJECT (menu_items), 
                            "button-press-event",
                            G_CALLBACK (_decrease_awntop_rows), 
                            (gpointer)awntop
                            );
    gtk_widget_show (menu_items);    
    
    menu_items = gtk_menu_item_new_with_label ("Pause");
    gtk_menu_shell_append (GTK_MENU_SHELL (menu), menu_items);        
    g_signal_connect(       G_OBJECT (menu_items), 
                            "button-press-event",
                            G_CALLBACK (_toggle_display_freeze), 
                            (gpointer)awntop
                            );    
    gtk_widget_show (menu_items);    


    
    dashboard_build_clickable_menu_item(kill_menu, G_CALLBACK(_click_set_term),"SIGTERM",data);
    dashboard_build_clickable_menu_item(kill_menu, G_CALLBACK(_click_set_kill),"SIGKILL",data);
#if 0
    dashboard_build_clickable_menu_item(kill_menu, G_CALLBACK(_click_set_term_kill),"SIGTERM Followed by SIGKILL",data);        
#endif    
    menu_items = gtk_menu_item_new_with_label ("Kill Signal");
    gtk_menu_shell_append (GTK_MENU_SHELL (menu), menu_items);        
    gtk_menu_item_set_submenu(menu_items,kill_menu);      
    gtk_widget_show (menu_items);      
   
    dashboard_build_clickable_menu_item(menu, G_CALLBACK(_toggle_user_filter),"Toggle User filter",data);   
   
    gtk_widget_show (menu_items);   
    
    return menu; 
    
}

static gboolean query_support_multiple(void)
{
    return FALSE;
}



static void init_Awntop( Awntop * awntop)
{
    GConfValue *value;   
    awntop->compar=cmpcpu;

    top_state=TRUE;    
    gcomparedir=-1;    
    compmethod=1;       /*sort by CPU*/
    awntop->updateinterval    =2000; /*FIXME*/
    awntop->accum_interval=0;

    
 //   awntop->redraw_window_fn=redraw_window_fn;
  //  awntop->redraw_window_data=redraw_window_data;    
    
    awntop->displayed_pid_list=NULL;
    awntop->proctimes=g_tree_new_full(proctime_key_compare_func,NULL,g_free,g_free);	
    
    awntop->icons=g_tree_new_full(icons_key_compare_func,NULL,free,free);	
    
    awntop->pixbufs=g_tree_new_full(icons_key_compare_func,NULL,free,free);	    
    awntop->forceupdatefixup=FALSE;
    parse_desktop_entries(awntop);    


    value = gconf_client_get( get_dashboard_gconf(),GCONF_AWNTOP_USER_FILTER, NULL );
    if ( value ) 
    {
        awntop->filterlevel= gconf_client_get_int(get_dashboard_gconf(),GCONF_AWNTOP_USER_FILTER, NULL );
    } 
    else 
    {
        awntop->filterlevel=1;    
    }    



    value = gconf_client_get( get_dashboard_gconf(),GCONF_AWNTOP_KILL_SIG_METH, NULL );
    if ( value ) 
    {
        G_kill_signal_method = gconf_client_get_int(get_dashboard_gconf(),GCONF_AWNTOP_KILL_SIG_METH, NULL );
    } 
    else 
    {
        G_kill_signal_method=2;    
    }    

    value = gconf_client_get( get_dashboard_gconf(), GCONF_AWNTOP_NUM_PROCS, NULL );
    if ( value ) 
    {
        awntop->maxtopentries = gconf_client_get_int(get_dashboard_gconf(),GCONF_AWNTOP_NUM_PROCS, NULL );
    } 
    else 
    {
        awntop->maxtopentries=17;    
    }    
    
    
}    
/*FIXME - changes in other placess have made some of the logic unecessary*/
static gboolean draw_top(GtkWidget ** pwidget,gint interval,void * data)
{

    Awntop * awntop=data;
    static GtkWidget *toptable;    
    const char * states[3]= { "User","!System","All"};            
    GtkWidget *tempwidg    ;
    GSList* removelist;   
    static gboolean firstcall=TRUE;
     
    if (firstcall)
    {
        firstcall=FALSE;
        awntop->accum_interval=awntop->updateinterval - interval;
    }
    else
    {
        awntop->accum_interval=awntop->accum_interval+interval;
        if ( (awntop->accum_interval < awntop->updateinterval) && (!awntop->forceupdatefixup) )
        {
            return FALSE;
        }
    }
    if (!top_state)
    {
        return FALSE;
    }

//    if (top_state)
//    {
        if (awntop->topentries)
        {
                free_topentries(awntop->topentries,awntop->num_top_entries);    
        }
        awntop->topentries=fill_topentries(awntop,&awntop->num_top_entries);         /*call free_topentries when done*/
        qsort(awntop->topentries, (size_t) awntop->num_top_entries ,sizeof(Topentry *),awntop->compar);
        removelist=NULL;
        g_tree_foreach(awntop->proctimes,proctime_find_inactive,&removelist);
        g_slist_foreach(removelist,proctimes_remove_inactive,awntop->proctimes);
        g_slist_free(removelist);
        if (!awntop->displayed_pid_list )                                                            
        {
            awntop->displayed_pid_list=g_malloc(sizeof(long)*awntop->maxtopentries);
        }        
//    }


    
    toptable = gtk_table_new (11, 5, FALSE);    
    gtk_table_set_col_spacings (GTK_TABLE(toptable),5);
    gtk_table_set_row_spacings (GTK_TABLE(toptable),0);                    
    build_top_table_headings(awntop,toptable);
    build_top_table(awntop,toptable);          
                              
                                 
    *pwidget=toptable;
    
    awntop->forceupdatefixup=FALSE;
    awntop->accum_interval=0;        
    return TRUE;
}


/*used for binary tree of icons and binary tree of pixbufs*/
static gint icons_key_compare_func(gconstpointer a,gconstpointer b,   gpointer user_data)
{
/*Returns : 	negative value if a < b; zero if a = b; positive value if a > b.*/
    const char *p1, *p2;
    p1=a;
    p2=b;
    return (strcmp(p1,p2) );    
}
    
/*used for binary tree of proctime*/
static gint proctime_key_compare_func(gconstpointer a,gconstpointer b,   gpointer user_data)
{
/*Returns : 	negative value if a < b; zero if a = b; positive value if a > b.*/
    const int *p1, *p2;
    p1=a;
    p2=b;
    return (*p1- *p2);    
}

static gboolean proctime_find_inactive(gpointer key,gpointer value,gpointer data)
{
    Proctimeinfo * p=value;
    GSList** removelist=data;    

    if ( ! p->accessed )
    {
//        printf("dummy=%d\n",p->dummy);
        *removelist=g_slist_prepend(*removelist,key);
    }
    return FALSE;
}

static gboolean proctime_reset_active(gpointer key,gpointer value,gpointer data)
{
    Proctimeinfo * p;
    
    p=value;
    p->accessed=FALSE;
    return FALSE;
}

static void proctimes_remove_inactive(gpointer data,gpointer user_data)
{
    int *p=data;
    GTree *tree=user_data;
    g_tree_remove(tree,p);

}

static gboolean _click_set_term (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    G_kill_signal_method=1;    
    gconf_client_set_int(get_dashboard_gconf(),GCONF_AWNTOP_KILL_SIG_METH,G_kill_signal_method, NULL );                            
    return TRUE;
}

static gboolean _click_set_kill (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    G_kill_signal_method=2;    
    gconf_client_set_int(get_dashboard_gconf(),GCONF_AWNTOP_KILL_SIG_METH,G_kill_signal_method, NULL );                                
    return TRUE;
}

static gboolean _click_set_term_kill (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    G_kill_signal_method=3;    
    gconf_client_set_int(get_dashboard_gconf(),GCONF_AWNTOP_KILL_SIG_METH,G_kill_signal_method, NULL );                                
    return TRUE;
}

static gboolean _click_pid (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmppid)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmppid;
        gcomparedir=1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
static gboolean _click_user (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmpuser)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmpuser;
        gcomparedir=1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
static gboolean _click_virt (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmpvirt)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmpvirt;
        gcomparedir=-1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
static gboolean _click_res (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmpres)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmpres;
        gcomparedir=-1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
static gboolean _click_cpu (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmpcpu)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmpcpu;
        gcomparedir=-1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
static gboolean _click_mem (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmpmem)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmpmem;
        gcomparedir=-1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
static gboolean _click_command (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    top_state=1;
    if (awntop->compar == cmpcommand)
    {
        gcomparedir=gcomparedir *-1;
    }
    else
    {   
        awntop->compar = cmpcommand;
        gcomparedir=1;
    }    
    awntop->forceupdatefixup=TRUE;    
    return TRUE;
}
#if 0
static gboolean _time_to_kill_I_mean_it(GtkWidget *widget, GdkEventButton *event, long * pid)
{

    kill(*pid,SIGKILL);    /*I'd don't really care about detecting the result at the moment...  FIXME??*/
    return TRUE;
}
#endif

static gboolean _time_to_kill(GtkWidget *widget, GdkEventButton *event, long * pid)
{
    assert( (G_kill_signal_method >0 ) && (G_kill_signal_method<4) );
    
    if (G_kill_signal_method==1 )
    {
        kill(*pid,SIGTERM);    /*I'd don't really care about detecting the result at the moment...  FIXME??*/        

#if 0
        if (G_kill_signal_method & 2)
        {
            kill(*pid,SIGKILL);    /*I'd don't really care about detecting the result at the moment...  FIXME??*/        
        }
#endif        
    }
    else if (G_kill_signal_method ==2 )
    {
        printf("kill %d \n",(int) *pid);
            kill(*pid,SIGKILL);    /*I'd don't really care about detecting the result at the moment...  FIXME??*/        
    }
    top_state=1;
    return TRUE;
}

static gboolean _toggle_display_freeze(GtkWidget *widget, GdkEventButton *event,Awntop *awntop)
{
    top_state=!top_state;
    awntop->forceupdatefixup=TRUE;    
//    gtk_widget_destroy(awntop->vbox);      
//    draw_main_window(Awntop);         
    /*FIXME write up some callback code in dashboard to trigger an immediate redraw*/
    return TRUE;
}

static gboolean _toggle_user_filter (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    awntop->filterlevel= !awntop->filterlevel;
    gconf_client_set_int(get_dashboard_gconf(),GCONF_AWNTOP_USER_FILTER,awntop->filterlevel, NULL );                                        
    return TRUE;
}

#if 0
static gboolean _change_Awntop_filter_state(GtkWidget *widget, GdkEventButton *event,Awntop *awntop)
{

    
    if (awntop->filterlevel==3)         /*FIXME*/
    {
        awntop->filterlevel=0;
    }
    awntop->forceupdatefixup=TRUE;       
    return TRUE;

}
#endif

static gboolean _increase_awntop_rows (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    awntop->forceupdatefixup=TRUE;
    awntop->maxtopentries++;  /*possible FIXME - race? */
    gconf_client_set_int(get_dashboard_gconf(),GCONF_AWNTOP_NUM_PROCS,awntop->maxtopentries, NULL );                        
    return TRUE;    
}
static gboolean _decrease_awntop_rows (GtkWidget *widget, GdkEventButton *event, Awntop *awntop)
{
    awntop->forceupdatefixup=TRUE;
    awntop->maxtopentries--;
    gconf_client_set_int(get_dashboard_gconf(),GCONF_AWNTOP_NUM_PROCS,awntop->maxtopentries, NULL );                            
    return TRUE;    
}


/************Section:  qsort compare functions-------------*/
static int cmppid(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return ( (*l)->pid -(*r)->pid) * gcomparedir;
}

/*FIXME ???  currently sort on uid not user name */
static int cmpuser(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return ( (*l)->uid -(*r)->uid) * gcomparedir;
}

static int cmpvirt(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return ( (*l)->virt -(*r)->virt) * gcomparedir;
}
static int cmpres(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return ( (*l)->res -(*r)->res) * gcomparedir;
}
static int cmpcpu(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return ( (*l)->cpu -(*r)->cpu) * gcomparedir;
}
static int cmpmem(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return ( (*l)->mem -(*r)->mem) * gcomparedir;
}
static int cmpcommand(const void * p1 , const void * p2)
{
    int result=0;
    Topentry ** l = (Topentry **) p1;
    Topentry ** r = (Topentry **) p2;
    
    return strcmp((*l)->cmd,(*r)->cmd) * gcomparedir;
}




/*filles up topentries with pointers to struct vars(did this way to make qsort faster).
numel is number of elements
*/
static Topentry ** fill_topentries(Awntop *awntop,int *numel)
{    
    glibtop_proclist proclist;                           
    glibtop_proc_state proc_state;
    glibtop_proc_time  proc_time;
    glibtop_proc_uid   proc_uid;
    glibtop_proc_mem   proc_mem;
    guint64 tmp;
    unsigned * p;    
    long percent;   
    int i;     
    Topentry **topentries;
    Proctimeinfo *value;
    int *ptmp;
        
    glibtop_get_mem(&awntop->libtop_mem);
    switch (awntop->filterlevel)
    {
        case 0:
                p=glibtop_get_proclist(&proclist,GLIBTOP_KERN_PROC_RUID, getuid());
                break;
        case 1:
                p=glibtop_get_proclist(&proclist,GLIBTOP_KERN_PROC_ALL, -1);        
                break;
    }
                    


    *numel=proclist.number;

    topentries=g_malloc(sizeof(Topentry*)*proclist.number);    
    g_tree_foreach(awntop->proctimes,proctime_reset_active,NULL);            
    for(i=0;i<proclist.number;i++)
    {        
        topentries[i]=g_malloc(sizeof(Topentry));
        topentries[i]->pid=p[i];
        glibtop_get_proc_state ( &proc_state, p[i]);
        strncpy(topentries[i]->cmd,proc_state.cmd,sizeof(topentries[i]->cmd));

/*  Leave this here - gets full command line.
{
        glibtop_proc_args buf;
        char *a=glibtop_get_proc_args(&buf,p[i],256 );
        printf("%s\n",a);

}*/
        glibtop_get_proc_time (&proc_time, p[i]);        
        value=g_tree_lookup(awntop->proctimes,&p[i]);     
        assert(awntop->accum_interval);        
        if (value)
        {
            if (awntop->forceupdatefixup)
            {
                topentries[i]->cpu=percent/(awntop->accum_interval/1000.0) ;            
            }
            else
            {
                topentries[i]->cpu=percent/(awntop->updateinterval/1000.0) ;
            }
            percent =  (proc_time.utime+proc_time.stime) - value->proctime;    
            value->proctime=proc_time.utime+proc_time.stime;                            
            if (percent>100)    /*FIXME this really should not happen...  */
            {
                percent=0;  
                
            }
        }
        else
        {
            ptmp=g_malloc(sizeof(guint64));
            *ptmp=p[i];
            value=g_malloc(sizeof(Proctimeinfo) );
            topentries[i]->cpu=value->proctime=proc_time.utime+proc_time.stime;
            g_tree_insert(awntop->proctimes,ptmp,value);
            percent=0;
        }
        value->accessed=TRUE;   
        if (awntop->forceupdatefixup)
        {
            topentries[i]->cpu=percent/(awntop->accum_interval/1000.0) ;                    
        }
        else
        {
            topentries[i]->cpu=percent/(awntop->updateinterval/1000.0) ;     
        }
        glibtop_get_proc_uid( &proc_uid,p[i]);
        topentries[i]->uid=proc_uid.uid ;    
        topentries[i]->nice=proc_uid.nice ;                     
        glibtop_get_proc_mem(&proc_mem,p[i]);
        topentries[i]->mem=proc_mem.resident*100/awntop->libtop_mem.total  ;        
        topentries[i]->res=proc_mem.resident ;    
        topentries[i]->virt=proc_mem.vsize ;           
    }     

    
    g_free(p);    
    return topentries;                   
}

static void free_topentries(Topentry **topentries, int num_top_entries)
{
    int i;
    for(i=0;i<num_top_entries;i++)
    {
        g_free(topentries[i]);
    }    
    g_free(topentries);
}


static void build_top_table_headings(Awntop *awntop,GtkWidget * table)
{
    GtkWidget * label;
    GtkWidget * button;
    int i;
    char *markup;        
    for(i=0;i<8;i++)       /*FIXME*/
    {
        label = gtk_label_new (NULL);
        markup = g_markup_printf_escaped ("<span style=\"italic\">%s</span>", Global_tableheadings[i].name);
        gtk_label_set_markup (GTK_LABEL (label), markup);        
        g_free (markup);    
        if (Global_tableheadings[i].fn)
        {
            button = gtk_button_new ();
            g_signal_connect (G_OBJECT (button), "button-press-event",G_CALLBACK (Global_tableheadings[i].fn), (gpointer)awntop);
            gtk_button_set_relief (GTK_BUTTON (button), GTK_RELIEF_NONE);                        
            gtk_container_add (GTK_CONTAINER (button),label);        
            gtk_table_attach_defaults (GTK_TABLE (table), button,
                                 i, i+1, 0, 1);
        }
        else
        {
            gtk_table_attach_defaults (GTK_TABLE (table), label,
                                 i, i+1, 0, 1);        
        }
    }
}   


/*FIXME  - clean this function up*/
GtkWidget * lookup_icon(Awntop * awntop,Topentry **topentries,int i)
{
    GtkIconTheme*  g;      
    GtkIconInfo*  iconinfo;
    GdkPixbuf* pbuf=NULL;
    char* parg;  
    glibtop_proc_args     procargs;
    char *ptmp;
    GtkWidget *image;        
    char *pvalue=NULL;
    char *p;
    
    parg=glibtop_get_proc_args(&procargs,topentries[i]->pid,256);        
    ptmp=strchr(parg,' ');
    if (ptmp)
        *ptmp='\0';
        
    pbuf=g_tree_lookup(awntop->pixbufs,parg);

    if (pbuf)
    {
        if (pbuf==Stock_Image_Used)
        {
            image=gtk_image_new_from_stock(GTK_STOCK_EXECUTE,GTK_ICON_SIZE_MENU);        
        }
        else
        {
            image=gtk_image_new_from_pixbuf(pbuf);
        }
        g_free(parg);       
        return image;        
    }
    
            
    if (!parg && !(*parg) )
    {
        pvalue=g_tree_lookup(awntop->icons,topentries[i]->cmd);
        if (!pvalue)
        {
            pvalue=g_tree_lookup(awntop->icons,basename(topentries[i]->cmd));
        }
    }
    else
    {

        pvalue=g_tree_lookup(awntop->icons,parg);  
        if (!pvalue)
        {
            pvalue=g_tree_lookup(awntop->icons,basename(parg));
        }
        
    }

    if (pvalue)     
    {
        g=gtk_icon_theme_get_default();
        pbuf=gtk_icon_theme_load_icon(g,pvalue,16,0,NULL);     
        if (!pbuf)
        {

            p=malloc(strlen("/usr/share/pixmaps/")+strlen(basename(pvalue))+1);
            strcpy(p,"/usr/share/pixmaps/");
            strcat(p,basename(pvalue));
            pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
            free(p); 
            if (!pbuf)
            {
                p=malloc(strlen("/usr/local/share/pixmaps/")+strlen(basename(pvalue))+1);
                strcpy(p,"/usr/local/share/pixmaps/");
                strcat(p,basename(pvalue));
                pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
                free(p);                                     
            }
        }
        
    
     }
     else
     {
        p=malloc(strlen("/usr/share/pixmaps/")+strlen(basename(parg))+1+strlen(".png"));
        strcpy(p,"/usr/share/pixmaps/");
        strcat(p,basename(parg));
        strcat(p,".png");
        pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
        free(p); 
        if (!pbuf)
        {
            p=malloc(strlen("/usr/local/share/pixmaps/")+strlen(basename(parg))+1+strlen(".png"));
            strcpy(p,"/usr/local/share/pixmaps/");
            strcat(p,basename(parg));
            strcat(p,".png");
            pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
            free(p); 
            if (!pbuf)
            {
                p=malloc(strlen("/usr/share/pixmaps/")+strlen(basename(parg))+1+strlen(".xpm"));
                strcpy(p,"/usr/share/pixmaps/");
                strcat(p,basename(parg));
                strcat(p,".xpm");
                pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
                free(p); 
                if (!pbuf)
                {
                    p=malloc(strlen("/usr/local/share/pixmaps/")+strlen(basename(parg))+1+strlen(".xpm"));
                    strcpy(p,"/usr/local/share/pixmaps/");
                    strcat(p,basename(parg));
                    strcat(p,".xpm");
                    pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
                    free(p); 
                }
            }        
        }        
    }
    if (!pbuf)   
    {
        image=gtk_image_new_from_stock(GTK_STOCK_EXECUTE,GTK_ICON_SIZE_MENU);
    }
    else
    {
        image=gtk_image_new_from_pixbuf(pbuf);
        g_tree_insert(awntop->pixbufs,strdup(parg),pbuf);                                     
//        g_object_unref (pbuf);
    }
    g_free(parg);       
    return image;

}

static void build_top_table(Awntop *awntop,GtkWidget * table )
{
    GtkWidget *tempwidg;	
    int i;
    GtkWidget *image;        
    Topentry **topentries=awntop->topentries;
    int num_top_entries=awntop->num_top_entries;
    
    
    g_free(awntop->displayed_pid_list);
    awntop->displayed_pid_list=g_malloc(sizeof(long)*awntop->maxtopentries);        

    for(i=0;(i<num_top_entries) && (i<awntop->maxtopentries);i++)
    {    
        char buf[100];
        struct passwd * userinfo;
        long tmp;
        assert(i <= awntop->maxtopentries);        
        awntop->displayed_pid_list[i]=topentries[i]->pid; /*array of pids that show in top.  Used for kill events*/
        
                    
        gtk_table_attach_defaults (GTK_TABLE (table),get_label_ld(topentries[i]->pid),
                                 0, 1, i+2, i+3);
            
        userinfo=getpwuid(topentries[i]->uid);
        tempwidg= (userinfo) ? get_label_sz(userinfo->pw_name,0): get_label_ld(topentries[i]->uid);
        gtk_table_attach_defaults (GTK_TABLE (table), tempwidg,
                                 1, 2, i+2, i+3);
                                                        
        tmp=topentries[i]->virt/1024;               /*FIXME?? consider as a fn*/
        if (tmp >=10000)                            
        {
            tmp=tmp/1024;       //convert K into M
            snprintf(buf,sizeof(buf),"%dM",tmp);              
        }
        else
        {
            snprintf(buf,sizeof(buf),"%d",tmp);              
        }
        gtk_table_attach_defaults (GTK_TABLE (table), get_label_sz(buf,1),
                                 2, 3, i+2, i+3);
         
        tmp=topentries[i]->res/1024;                    /*FIXME?? consider as a fn*/
        if (tmp >=10000)
        {
            tmp=tmp/1024;       //convert K into M
            snprintf(buf,sizeof(buf),"%dM",tmp);              
        }
        else
        {
            snprintf(buf,sizeof(buf),"%d",tmp);              
        }                                 
        gtk_table_attach_defaults (GTK_TABLE (table), get_label_sz(buf,1),
                                 3, 4, i+2, i+3);

        gtk_table_attach_defaults (GTK_TABLE (table), get_label_ld(topentries[i]->cpu),
                                 4, 5, i+2, i+3);        

        gtk_table_attach_defaults (GTK_TABLE (table), get_label_ld(topentries[i]->mem),
                                 5, 6, i+2, i+3);
           
        
        gtk_table_attach_defaults (GTK_TABLE (table), lookup_icon(awntop,topentries,i),
                         6, 7, i+2, i+3);  
        char trunc[32];
        snprintf(trunc,12,"%s",topentries[i]->cmd);
        tempwidg=get_event_box_label(trunc,0); 
        gtk_table_attach_defaults (GTK_TABLE (table),tempwidg ,
                                 7, 8, i+2, i+3);
        
        tempwidg= get_icon_event_box(awntop,"xkill",GTK_STOCK_CLOSE,GTK_ICON_SIZE_MENU);
        g_signal_connect (G_OBJECT (tempwidg), "button-press-event",
                                    G_CALLBACK (_time_to_kill), 
                                    (gpointer)&awntop->displayed_pid_list[i]);                              
        gtk_table_attach_defaults (GTK_TABLE (table),tempwidg,
                                 8, 9, i+2, i+3);

#if 0
        tempwidg= get_event_box_label("-9",0);
        g_signal_connect (G_OBJECT (tempwidg), "button-press-event",
                                    G_CALLBACK (_time_to_kill_I_mean_it), 
                                    (gpointer)&awntop->displayed_pid_list[i]);
        gtk_table_attach_defaults (GTK_TABLE (table), tempwidg,
                                 9, 10, i+2, i+3);                 
#endif                                 
    }    
}

static GtkWidget * get_icon_button(Awntop * awntop,char *name,const gchar *stock_id, GtkIconSize size)
{
    GtkIconTheme*  g;      
    GdkPixbuf* pbuf;
    GtkWidget *image=NULL;  
    GtkWidget *button;  
    
    pbuf=g_tree_lookup(awntop->pixbufs,name);
    if (!pbuf)
    {    
        g=gtk_icon_theme_get_default();
        pbuf=gtk_icon_theme_load_icon(g,name,16,0,NULL);     
        if (!pbuf)
        {         
            image=gtk_image_new_from_stock(stock_id,size);     /* pbuf could be NULL after this*/
            g_tree_insert(awntop->pixbufs,strdup(name),Stock_Image_Used);             
                                                       
        }
/*        if (image)
        {

            pbuf=gtk_image_get_pixbuf(image);           //doesn't work if it's  GTK_IMAGE_STOCK

        }*/
        if (pbuf)
        {
            g_object_ref(pbuf);            
            g_tree_insert(awntop->pixbufs,strdup(name),pbuf); 
        }
        
    }
//    assert(pbuf);
    if (!image)
    {
        if (pbuf==Stock_Image_Used)
        {
            image=gtk_image_new_from_stock(stock_id,size);
        }
        else
        {
            image=gtk_image_new_from_pixbuf(pbuf);
        }
    }    
    
    button=gtk_button_new();
    gtk_button_set_image(button,image);
    return button; 
}


static GtkWidget * get_icon_event_box(Awntop * awntop,char *name,const gchar *stock_id, GtkIconSize size)
{
    GtkIconTheme*  g;      
    GdkPixbuf* pbuf;
    GtkWidget *image=NULL;  
    GtkWidget *eventbox;  
    char *p;
    
    pbuf=g_tree_lookup(awntop->pixbufs,name);
    if (!pbuf)
    {
        g=gtk_icon_theme_get_default();
        pbuf=gtk_icon_theme_load_icon(g,name,16,0,NULL);     
        if (!pbuf)
        {         
            p=malloc(strlen("/usr/share/pixmaps/")+strlen(name)+1+strlen(".png"));
            strcpy(p,"/usr/share/pixmaps/");
            strcat(p,name);
            strcat(p,".png");
            pbuf=gdk_pixbuf_new_from_file_at_scale(p,16,16,FALSE,NULL);               
            free(p); 
            if (!pbuf)
            {
                image=gtk_image_new_from_stock(stock_id,size);  
                assert(image);
                g_tree_insert(awntop->pixbufs,strdup(name),Stock_Image_Used);                             
                
                 //doesn't work if it's  GTK_IMAGE_STOCK
/*                pbuf=gtk_image_get_pixbuf(image);       
                g_object_ref(pbuf);    */
            }
        }
        if (pbuf)
        {
            g_tree_insert(awntop->pixbufs,strdup(name),pbuf); 
        }
    } 
    
    if (!image)
    {
        if (pbuf==Stock_Image_Used)
        {
            image=gtk_image_new_from_stock(stock_id,size);
        }
        else
        {
            image=gtk_image_new_from_pixbuf(pbuf);
        }    
    }    
    eventbox = gtk_event_box_new (); 
    gtk_event_box_set_visible_window( GTK_EVENT_BOX(eventbox),FALSE);
    gtk_container_add (GTK_CONTAINER (eventbox),image);        
    
    return eventbox; 
}

 
static GtkWidget * get_event_box_label(const char * t, gfloat halign)
{
	GtkWidget *label;
	GtkWidget *eventbox;	
     
    label = gtk_label_new (t);
    gtk_misc_set_alignment((GtkMisc *)label,halign,0.5);    
    eventbox = gtk_event_box_new (); 
    gtk_event_box_set_visible_window( GTK_EVENT_BOX(eventbox),FALSE);
    gtk_container_add (GTK_CONTAINER (eventbox),label);        
    return eventbox;
}

static GtkWidget * get_label_ld(const long t)
{
	GtkWidget *label;
    char    buf[32];
     
    snprintf(buf,sizeof(buf),"%ld",t);   
    label = gtk_label_new (buf);  
    gtk_misc_set_alignment((GtkMisc *)label,1.0,0.5);
    return label;
}
            
static GtkWidget * get_label_sz(const char * t, gfloat halign)
{
	GtkWidget *label;
    label = gtk_label_new (t);  
    gtk_misc_set_alignment((GtkMisc *)label,halign,0.5);
    return label;
}

static GtkWidget * get_button_sz(const char * t)
{
	GtkWidget *button;
    button=gtk_button_new_with_label(t);
    gtk_button_set_relief (GTK_BUTTON (button), GTK_RELIEF_NONE);    
    return button;
}

static void parse_desktop_entries(Awntop * awntop)
{
    struct dirent **namelist;
    int n;        
    char * pXDG_desktop_dir;
    char * pXDG_desktop_dir_home;
    char * pXDG_alldirs;
    char * ptmp;
    char * tok;
    GKeyFile*   keyfile;
    char *pvalue;

    pXDG_desktop_dir=strdup( ptmp=getenv("XDG_DATA_DIRS")?ptmp:"/usr/share");   /*FIXME if strdup return NULL...  I guess it could happen*/

    pXDG_desktop_dir_home=strdup(ptmp=getenv("XDG_DATA_HOME")?ptmp:"/usr/local/share");
    
    pXDG_alldirs=malloc(strlen(pXDG_desktop_dir)+strlen(pXDG_desktop_dir_home)+2);
    if (pXDG_alldirs)
    {
        strcpy(pXDG_alldirs,pXDG_desktop_dir_home);
        strcat(pXDG_alldirs,":");
        strcat(pXDG_alldirs,pXDG_desktop_dir);
        
//        printf("pXDG_desktop_dir = %s\n",pXDG_alldirs);
        for(tok=strtok(pXDG_alldirs,":");tok;tok=strtok(NULL,":"))      /*FIXME - hard coded token*/
        {
            char * pdirname;
            pdirname=malloc(strlen(tok)+strlen("/applications")+1);      /*FIXME*/
            strcpy(pdirname,tok);
            strcat(pdirname,"/applications");
//            printf("%s\n",pdirname);
            
            n = scandir(pdirname, &namelist, 0, alphasort);
            if (n < 0)
                perror("error opening desktop files");
            else 
            {
               while (n--) 
               {
                    char *fullpath;
                    fullpath=malloc(strlen(pdirname) + strlen(namelist[n]->d_name) +2);                
                    if (fullpath)
                    {
                        strcpy(fullpath,pdirname);              /*FIXME -need to look into the variations on g_key_file_load_from_file*/
                        strcat(fullpath,"/");
                        strcat(fullpath,namelist[n]->d_name);   
                        keyfile=g_key_file_new(); 
                                 
                        if (g_key_file_load_from_file(keyfile,fullpath,0,NULL) )
                        {
                            char *iconname;
                            if (iconname=g_key_file_get_string(keyfile,"Desktop Entry","Icon",NULL) )
                            {
                                char * execname;
                                if (execname=g_key_file_get_string(keyfile,"Desktop Entry","Exec",NULL) )
                                {
                                    ptmp=strchr(execname,' ');
                                    if (ptmp)
                                        *ptmp='\0';
                                    pvalue=g_tree_lookup(awntop->icons,execname);     
                                    if (!pvalue)
                                    {                                        
                                        g_tree_insert(awntop->icons,execname,strdup(iconname) );  /*FIXME*/
                                    }
                                    else
                                    {
                                        g_free(execname);
                                    }
                                }
                                g_free(iconname);
                            }
                            else
                            {
  //                              printf("key not found \n");
                            }
                            
                       }
                       else
                       {
//                            printf("Failed to load keyfile: %s\n",fullpath);
                       }
                       g_key_file_free(keyfile);
                       free(namelist[n]);
                       free(fullpath);
                    }
               }
               free(namelist);
            }
            free(pdirname);
        }   
    }    
    free(pXDG_alldirs);     
    
    /*FIXME --- below - obviously*/
    if (!g_tree_lookup(awntop->icons,"firefox-bin"))
    {          
        g_tree_insert(awntop->icons,"firefox-bin",strdup("firefox-icon.png"));  
    }
    if (!g_tree_lookup(awntop->icons,"bash"))
    {
        g_tree_insert(awntop->icons,"bash",strdup("terminal")); 
    }
    if (!g_tree_lookup(awntop->icons,"sh"))
    {
        g_tree_insert(awntop->icons,"sh",strdup("terminal"));  
    }
    if (!g_tree_lookup(awntop->icons,"dash"))
    {
        g_tree_insert(awntop->icons,"dash",strdup("terminal"));
    }    
    if (!g_tree_lookup(awntop->icons,"ash"))
    {
        g_tree_insert(awntop->icons,"ash",strdup("terminal")); 
    }   
    if (!g_tree_lookup(awntop->icons,"csh"))
    {
        g_tree_insert(awntop->icons,"csh",strdup("terminal")); 
    }     

//    free(ptmp);            
}


