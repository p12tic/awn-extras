

#include <glibtop/uptime.h>
#include <glibtop/cpu.h>

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

#include "dashboard.h"

#include <assert.h>





static void draw_main_window(Dashboard *Dashboard);

static gboolean _Dashboard_time_handler (Dashboard *);
static Uptimedata * _Dashboard_syncuptime(Uptimedata * );

static void Dashboard_plugs_construct(gpointer data,gpointer user_data);
static void Dashboard_plugs_destruct(gpointer data,gpointer user_data);

//static gboolean _show_pause_button(GtkWidget ** pwidget,gint interval,void * data);


static gboolean _visibility_notify_event(GtkWidget *widget, GdkEventButton *event, Dashboard * dashboard);
static gboolean _focus_out_event(GtkWidget *widget, GdkEventButton *event, Dashboard * dashboard);

/*FIXME  --- */
static void show_main_window(Dashboard *Dashboard);
static void hide_main_window(Dashboard *Dashboard);


void dashboard_redraw_signal(Dashboard * dashboard)
{
//    gtk_widget_destroy(dashboard->vbox);
    draw_main_window(dashboard);
}
//static const char * freeze_botton_text[2]={"Pause","Update"};

static gboolean _cairo_demo_plug(GtkWidget ** pwidget,gint interval,void * data)
{
    char buf[256];
    Dashboard *Dashboard=data;
    GtkRequisition    maintable_size;
    
//    gtk_widget_get_size_request (Dashboard->maintable, &width, &height);    
//    gtk_widget_size_request (Dashboard->maintable,&maintable_size);

    GdkPixmap*  pixmap=gdk_pixmap_new(NULL,400,65,32);    
    GdkColormap* cmap=gdk_colormap_new(gdk_visual_get_best (),TRUE);    
    gdk_drawable_set_colormap(pixmap,cmap);          
    cairo_t*    cr=gdk_cairo_create(pixmap);
    
	/* Clear the background to transparent */
    
    cairo_set_source_rgba (cr, 1, 0.1, 0.1,0.8);
	cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
	cairo_paint (cr);


    cairo_set_source_rgba (cr, 0.1, 0.1, 0.1,0.6);
	cairo_set_operator (cr, CAIRO_OPERATOR_SOURCE);
    cairo_rectangle(cr,2,2,394,62);
    cairo_stroke (cr);    

	/* Set back to opaque */
	cairo_set_operator (cr, CAIRO_OPERATOR_OVER);
	cairo_set_source_rgb(cr, 1.0, 1.0, 1.0);

	cairo_select_font_face (cr, "Sans", CAIRO_FONT_SLANT_NORMAL, CAIRO_FONT_WEIGHT_NORMAL);
	cairo_set_font_size (cr, 10.0);
	
    cairo_move_to(cr, 10.0, 15.0);
	snprintf(buf,sizeof(buf),"Up Time:%ld:%ld:%ld:%ld",Dashboard->uptimedata.days,
	                        Dashboard->uptimedata.hours,Dashboard->uptimedata.minutes,
	                        Dashboard->uptimedata.seconds);
    cairo_show_text(cr, buf);
    
	cairo_set_font_size (cr, 10.0);    	
    cairo_move_to(cr, 10.0, 30.0);
    snprintf(buf,sizeof(buf),"User:%ld",Dashboard->user);
    cairo_show_text(cr, buf);
    
    cairo_move_to(cr, 10.0, 45.0);
    snprintf(buf,sizeof(buf),"Sys:%ld",Dashboard->sys);
    cairo_show_text(cr, buf);

    cairo_move_to(cr, 10.0, 60.0);
    snprintf(buf,sizeof(buf),"Idle:%ld",Dashboard->idle);
    cairo_show_text(cr, buf);
    
    *pwidget=gtk_image_new_from_pixmap(pixmap,NULL);
    
    g_object_unref (pixmap);
    Dashboard->demo_plug_cr=cr;
	cairo_destroy (cr);
    
    return TRUE;
}

Dashboard_plugs_callbacks* register_Dashboard_plug(      Dashboard * dashboard,    
                                gboolean (*construct_fn)(GtkWidget ** w,gint call_interval,void *data),
                                gboolean (*destruct_fn)(GtkWidget ** w,void *data),
                                int x1, int x2, int y1, int y2,void * arb_data)
{
    Dashboard_plugs_callbacks * node=g_malloc(sizeof(Dashboard_plugs_callbacks));
    node->construct_fn=construct_fn;
    node->destruct_fn=destruct_fn;    
    node->data=arb_data;
    node->x1=x1;
    node->x2=x2;
    node->y1=y1;
    node->y2=y2;            
    node->widget=NULL;
    node->headers_footers=NULL;
    node->widge_wrap=NULL;    
    dashboard->Dashboard_plugs=g_slist_prepend(dashboard->Dashboard_plugs,node);    
   
    return node;
}                                


void register_Dashboard( Dashboard * dashboard,AwnApplet *applet)
{
    /*fequency in updates in seconds.  pull all this crap from gconf eventually...*/	
    dashboard->updateinterval=100;		
    dashboard->force_update=FALSE;

    dashboard->mainwindowvisible=FALSE;    
    dashboard->applet=applet;
    dashboard->Dashboard_plugs=NULL;        /*there are no plugs registered yet*/
    dashboard->box = gtk_alignment_new (0.5, 0.5, 1, 1);
    dashboard->mainwindow = awn_applet_dialog_new (applet);
                       
    gtk_window_set_focus_on_map (GTK_WINDOW (dashboard->mainwindow), TRUE);
    gtk_container_add (GTK_CONTAINER (dashboard->mainwindow), dashboard->box);
            

    gtk_widget_show_all (dashboard->mainwindow);
    gtk_widget_hide (dashboard->mainwindow);
    
    dashboard->vbox = gtk_vbox_new (FALSE, 8);    
    dashboard->maintable = gtk_table_new (35, 10, FALSE);
    gtk_container_add (GTK_CONTAINER (dashboard->box), dashboard->vbox);        
    gtk_table_set_col_spacings (GTK_TABLE(dashboard->maintable),15);    
    gtk_box_pack_end (GTK_BOX (dashboard->vbox), dashboard->maintable, TRUE, TRUE, 0);
    
    g_signal_connect(     G_OBJECT(dashboard->mainwindow), 
                            "focus-out-event", 
                            G_CALLBACK (_focus_out_event), 
                            (gpointer)dashboard
                       );    

    //register_Dashboard_plug(dashboard,_cairo_demo_plug,NULL,0,9,2,3,dashboard);        
    //gtk_table_attach_defaults (GTK_TABLE (Dashboard->table), tempwidg,
     //                    numcols-1, numcols, 1, 2);     
	/*FIXME  - wrap in #ifdef so g_timeout_add_seconds_full is used if gtk version > 2.14.  and do a #define for the intervals*/

	g_timeout_add_full(G_PRIORITY_DEFAULT,dashboard->updateinterval,(GSourceFunc)_Dashboard_time_handler,(gpointer)dashboard,NULL);
/*
	#if GLIB_MAJOR_VERSION == 2 && GLIB_MINOR_VERSION >= 14	
    printf("GLIB_MAJOR_VERSION =%d && GLIB_MINOR_VERSION = %d - Using g_timeout_add_seconds_full\n",
                                                    GLIB_MAJOR_VERSION,GLIB_MINOR_VERSION);	
	g_timeout_add_seconds_full(G_PRIORITY_DEFAULT, 1 ,(GSourceFunc)_Dashboard_time_handler,(gpointer)dashboard,NULL);	
    #else
    printf("GLIB_MAJOR_VERSION =%d && GLIB_MINOR_VERSION = %d - Using g_timeout_add_full\n",
                                                    GLIB_MAJOR_VERSION,GLIB_MINOR_VERSION);	    
	g_timeout_add_full(G_PRIORITY_DEFAULT, 1000 ,(GSourceFunc)_Dashboard_time_handler,(gpointer)dashboard,NULL);
	#endif	*/
}    


void toggle_Dashboard_window(Dashboard *Dashboard)
{
    Dashboard->mainwindowvisible = !Dashboard->mainwindowvisible;
    
    if (Dashboard->mainwindowvisible)
    {
        Dashboard->force_update=TRUE;    
        create_Dashboard_window(Dashboard);
    }
    else
    {
        destroy_Dashboard_window(Dashboard);
    }
}

void create_Dashboard_window(Dashboard *Dashboard)
{
    draw_main_window(Dashboard);
}

void destroy_Dashboard_window(Dashboard *Dashboard)
{
    Dashboard->mainwindowvisible = FALSE;
    gtk_widget_hide (Dashboard->mainwindow);
//    gtk_widget_destroy(Dashboard->vbox);
}
/*used for plugs linked list */

static void Dashboard_plugs_construct(gpointer data,gpointer user_data)
{
    
    Dashboard_plugs_callbacks * node=data;
    Dashboard *dashboard=user_data;

    int i,j;
    dashboard->need_win_update=FALSE;
    if(node->construct_fn)
    {
        
        if (dashboard->need_win_update=dashboard->need_win_update || node->construct_fn(&node->widget,dashboard->updateinterval,node->data ))
        {
            if (node->widge_wrap)
            {
                gtk_widget_hide (node->widge_wrap);
                gtk_widget_destroy(node->widge_wrap);
            }        
        
            node->widge_wrap = gtk_table_new (3, 3, FALSE);
            gtk_table_set_row_spacings (node->widge_wrap,0);
            gtk_table_set_col_spacings (node->widge_wrap,0);
           

            gtk_table_attach_defaults (GTK_TABLE (node->widge_wrap), node->widget,
                                     0, 3, 1, 2);  
            gtk_table_attach_defaults (GTK_TABLE (dashboard->maintable), node->widge_wrap,
                                     node->x1, node->x2, node->y1, node->y2);  

            if (node->headers_footers)
            {
                for(i=0;i<6;i++)
                {
                    if (node->headers_footers[i])
                    {
                        GtkWidget *head_foot;
                        node->headers_footers[i](&head_foot);
                        gtk_table_attach_defaults (GTK_TABLE (node->widge_wrap),head_foot ,
                                     i % 3, i % 3 +1, (i/3)*3, (i/3)*3+1);  
                     }
                 }
             }
        }      
    }
}

static void Dashboard_plugs_destruct(gpointer data,gpointer user_data)
{
    
    Dashboard_plugs_callbacks * node=data;
    Dashboard *Dashboard=user_data;
    if(node->destruct_fn)
    {
        node->destruct_fn(&node->widget,node->data );
    }      
}


static gboolean _Dashboard_time_handler (Dashboard * Dashboard)
{

    glibtop_cpu         cpu;        
    long tmp;

    
	glibtop_get_cpu( &cpu);     //could as easily do this in render icon.  seems more appropriate here.     FIXME
    
    Dashboard->user=cpu.user-Dashboard->accum_user;
	Dashboard->accum_user=cpu.user;
	Dashboard->sys=cpu.sys - Dashboard->accum_sys ;
	Dashboard->accum_sys=cpu.sys;
    Dashboard->idle=cpu.idle - Dashboard->accum_idle ;	
    Dashboard->accum_idle=cpu.idle;
	Dashboard->uptimedata.seconds=Dashboard->uptimedata.seconds++;
	if (Dashboard->uptimedata.seconds >59)
	{
			_Dashboard_syncuptime(&Dashboard->uptimedata);	/*resync to system uptime every minute.  FIXME*/

	}
    

//    if (Dashboard->uptimedata.seconds % Dashboard->updateinterval == 0)
//    {
        if (Dashboard->mainwindowvisible)
        {
//            gtk_widget_destroy(Dashboard->vbox);      
            draw_main_window(Dashboard);                
        }	
//    }        
	return TRUE;
}


static Uptimedata * _Dashboard_syncuptime(Uptimedata * uptimedata)
{
	glibtop_uptime uptime;
	long tmp;

	glibtop_get_uptime(&uptime);	
	tmp=uptime.uptime;
	uptimedata->seconds=tmp % 60;
	tmp=tmp/60;	//tmp is now minutes
	uptimedata->minutes=tmp%60;
	tmp=tmp / 60;	//tmp now hours
	uptimedata->hours=tmp % 24;
	tmp=tmp / 24;
	uptimedata->days=tmp;
	return uptimedata;
}

/************Section:  main window events-------------*/

static gboolean
_button_clicked_test_event (GtkWidget *widget, GdkEventButton *event, Dashboard * dashboard)
{
    printf("button_clicked_test_event\n");        
	return TRUE;
}

static gboolean
_visibility_notify_event(GtkWidget *widget, GdkEventButton *event, Dashboard * dashboard)
{
//    hide_main_window(dashboard);
    return TRUE;
}

static gboolean
_focus_out_event(GtkWidget *widget, GdkEventButton *event, Dashboard * dashboard)
{
//    hide_main_window(dashboard);
    destroy_Dashboard_window(dashboard);
    return TRUE;
}

/*
static void draw_main_window(Dashboard *dashboard)

-draws the main window.
-interates though the list of dashboard plugs and they draw their widgets.

*/
static void draw_main_window(Dashboard *dashboard)
{

	GtkWidget *label;
	GtkWidget *button;	
    GtkWidget *tempwidg;	
    int i;
    int numcols;

//    dashboard->vbox = gtk_vbox_new (FALSE, 8);    
//    dashboard->maintable = gtk_table_new (35, 10, FALSE);
    
    /*have dashboard plugs that have registered draw their widgets*/
    g_slist_foreach(dashboard->Dashboard_plugs,Dashboard_plugs_construct,dashboard);    
       
    /*we're done laying out the damn thing - let's show it*/


    if (dashboard->need_win_update || dashboard->force_update)
    {
        dashboard->force_update=FALSE;
        awn_applet_dialog_position_reset (AWN_APPLET_DIALOG (dashboard->mainwindow));    
        gtk_widget_show_all (dashboard->mainwindow);    
    }
}



static void show_main_window(Dashboard *dashboard)
{
//    gtk_widget_hide (Dashboard->mainwindow);
}

static void hide_main_window(Dashboard *dashboard)
{

    gtk_widget_hide (dashboard->mainwindow);
//    gtk_widget_destroy(dashboard->vbox);
}


/*
    */

/* Gets the pixbuf from a desktop file's icon name. Based on the same function
 * from matchbox-desktop
 */
 /*
static GdkPixbuf *
get_icon (const gchar *name, gint size)
{
  static GtkIconTheme *theme = NULL;
  GdkPixbuf *pixbuf = NULL;
  GError *error = NULL;
  gchar *stripped = NULL;
  gint width, height;

  if (theme == NULL)
    theme = gtk_icon_theme_get_default ();

  if (name == NULL)
  {
    g_warning ("No icon name found");
    return NULL;
  }

  if (g_path_is_absolute (name))
  {
    if (g_file_test (name, G_FILE_TEST_EXISTS))
    {
      pixbuf = gdk_pixbuf_new_from_file_at_scale (name, size, size, 
                                                  TRUE, &error);
      if (error)
      {
        g_warning ("Error loading icon: %s\n", error->message);
        g_error_free (error);
        error = NULL;
      }
      return pixbuf;
    } 
  }

  stripped = strip_extension (name);
  
  pixbuf = gtk_icon_theme_load_icon (theme,
                                     stripped,
                                     size,
                                     0, &error);
  if (error)
  {   
    g_warning ("Error loading icon: %s\n", error->message);
    g_error_free (error);
    error = NULL;
  }

  width = gdk_pixbuf_get_width (pixbuf);
  height = gdk_pixbuf_get_height (pixbuf);

  if (width != size || height != size)
  {
    GdkPixbuf *temp = pixbuf;
    pixbuf = gdk_pixbuf_scale_simple (temp, 
                                      size,
                                      size,
                                      GDK_INTERP_HYPER);
    g_object_unref (temp);
  }

  g_free (stripped);
  return pixbuf;
}


typedef enum
{
  GTK_ICON_SIZE_INVALID,
  GTK_ICON_SIZE_MENU,
  GTK_ICON_SIZE_SMALL_TOOLBAR,
  GTK_ICON_SIZE_LARGE_TOOLBAR,
  GTK_ICON_SIZE_BUTTON,
  GTK_ICON_SIZE_DND,
  GTK_ICON_SIZE_DIALOG
} GtkIconSize;

*/
