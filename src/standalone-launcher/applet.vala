/*
 * Copyright (C) 2008 Rodney Cryderman <rcryderman@gmail.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.
 *
 * Author : R. Cryderman <rcryderman@gmail.com>
 */

using   Gdk;
using   Gtk;
using   Awn;
using   GLib;
using   Wnck;
using   DBus;
using   Cairo;


enum LaunchMode
{
	ANONYMOUS,
	DISCRETE
}

enum TaskMode
{
	SINGLE,
	MULTIPLE
}


static void print_desktop(DesktopItem desktopitem)
{

	stdout.printf("\n\nDesktop item \n");
	stdout.printf("name = %s\n",desktopitem.get_name());
//	stdout.printf("icon = \n",desktopitem.get_icon());
	stdout.printf("exec = %s\n",desktopitem.get_exec());		
	stdout.printf("\n");
}

static int _cmp_ptrs (pointer a, pointer b)
{
	return (int) a - (int) b;
}
static Pixbuf layer_pixbuf_scale(Pixbuf dest,Pixbuf under,Pixbuf over,int width,int height,
								double under_alpha=0.7,double over_alpha=1.0,
								int src_xpos=0,int src_ypos=0,
								double scale_x=1.0, double scale_y=1.0								
								)
{
	if (under!=null)
	{
		under.composite (dest,0, 0, width,height,0,0,1,1, Gdk.InterpType.BILINEAR,255);
	}	
	over.composite (dest,0, 0, width,height,src_xpos,src_ypos,scale_x,scale_y, Gdk.InterpType.BILINEAR,255);
	return dest;
}


static Pixbuf layer_pixbuf(Pixbuf dest,Pixbuf under,Pixbuf over,int width,int height,double under_alpha=0.7,double over_alpha=1.0)
{
	dest=dest.scale_simple (height, height, Gdk.InterpType.BILINEAR );	
	dest.fill(0x00000000);	
	if (under!=null)
		under=over.scale_simple (height, height, Gdk.InterpType.BILINEAR );	
	over=over.scale_simple (height, height, Gdk.InterpType.BILINEAR );	
	return layer_pixbuf_scale(dest,under,over,width,height);
}

static Pixbuf layer_pixbuf_filled(Pixbuf dest,uint pixels,Pixbuf over,int width,int height,double over_alpha=1.0)
{
	dest=dest.scale_simple (height, height, Gdk.InterpType.BILINEAR );	//FIXME
	dest.fill(pixels);
	over=over.scale_simple (height, height, Gdk.InterpType.BILINEAR );	
	return layer_pixbuf_scale(dest,null,over,width,height);
}



class Configuration: GLib.Object
{
	protected			bool				anon_mode   { get; construct; }
	protected			string				uid			{ get; construct; }
	protected			string				subdir;
	protected	weak	Awn.ConfigClient	primary_conf;
	protected			Awn.ConfigClient	default_conf;
	protected			Awn.ConfigClient	dummy;

	
	private				int					_task_mode;
	private				string				_active_image;
//	private				Awn.Color			_active_colour;
	public				int					name_comparision_len;	//FIXME
	private				bool				_override_app_icon;
	public              string              desktop_file_editor;
	
	construct
	{
    	desktop_file_editor=new string();
		if (anon_mode)
		{			
			default_conf=new Awn.ConfigClient.for_applet("standalone-launcher",null);
			primary_conf=default_conf;
			subdir="anonymous/";
		}
		else
		{
			default_conf=new Awn.ConfigClient.for_applet("standalone-launcher",null);
			dummy=new Awn.ConfigClient.for_applet("standalone-launcher",uid);
			primary_conf=dummy;
			subdir="discrete/";			
		}
//		_active_colour=new Awn.Color();
		read_config();

//Don't know why this is crapping out... probably a bindings issue. FIXME later.
//        default_conf.notify_add((CONFIG_CLIENT_DEFAULT_GROUP,"standalone-launcher", _config_changed, null);
		if (!anon_mode)
		{
				
		}

	}
	
	public static void _config_changed(Awn.ConfigClientNotifyEntry entry, pointer data)
	{
	
		stdout.printf("config notifiy fired\n");
	}
	
	Configuration(string uid,bool anon_mode)
	{
		this.uid=uid;
		this.anon_mode=anon_mode;
	}

	private void read_config()
	{   
		string temp;
		_task_mode=get_int(subdir+"task_mode",1);
		_active_image=get_string("active_task_image","emblem-favorite");
		_override_app_icon=get_bool(subdir+"override_app_icon",true);

		name_comparision_len=14;		
        desktop_file_editor="gnome-desktop-item-edit";

		temp=get_string("active_colour","00000000");		
		//cairo_string_to_color(temp,_active_colour);		
	}
	
	public bool get_bool(string key,bool def=false)
	{
		bool value;
		try {
			value = default_conf.get_bool( CONFIG_CLIENT_DEFAULT_GROUP,key);
		}catch (GLib.Error ex){
			value = def;   
		}		
		return value;
	}	

	public int get_int(string key,int def=0)
	{
		int value;
		try {
			value = default_conf.get_int( CONFIG_CLIENT_DEFAULT_GROUP,key);
		}catch (GLib.Error ex){
			value = def;   
		}		
		return value;
	}

	public string get_string(string key,string def="")
	{
		string value;
		try {
			value = default_conf.get_string( CONFIG_CLIENT_DEFAULT_GROUP,key);
		}catch (GLib.Error ex){
			value = def;   
		}		
		return value;
	}

    public bool override_app_icon{
        get { 
			return _override_app_icon;
    	}
    }

	

    public int task_mode {
        get { 
			return _task_mode;
    	}
    }

    public string active_image {
        get { 
			return _active_image;
    	}
    }
	
}

class DesktopFileManagement : GLib.Object
{
	protected   string  directory;
	protected   string  uid { get; construct; }
	
	construct
	{
		directory=Environment.get_home_dir()+"/.config/awn/applets/standalone-launcher/";
		if ( uid.to_double()>0)
		{

            uid=Checksum(uid);
			if (! FileUtils.test(directory,FileTest.EXISTS)  )
			{		
				stdout.printf("creating %s\n",directory);
				if ( DirUtils.create_with_parents(directory,0777) != 0)
				{
					error("Fatal error creating %s\n",directory);
				}
			}
			else if (!FileUtils.test(directory,FileTest.IS_DIR))
			{
				//FIXME... throw an exception... it has to be a dir.
			}
		}
		else
		{
            uid=Checksum(uid);
		}
	}
	
	public void set_name(string name)
	{
            uid=Checksum(name);
	}
	
	private string Checksum(string str)
	{
	    string result=new string();
	    result="anon-";
	    for(int i=0;i<str.len();i++)
	    {
	        string piece = str.substring(i,1);  //FIXME...  easy in C.. not sure of vala.
	        if (
	                    (piece=="%") || (piece==".") || (piece=="?") || (piece=="*") 
	                ||  (piece=="&") || (piece=="~") || (piece=="@") || (piece==";")
	                ||  (piece=="(") || (piece=="\\")|| (piece=="/")
	                ) 
	        {
	            piece="_";
            }	            
	        result=result+piece;
	    }
	    return result;
	}
	
	public DesktopFileManagement(string uid)
	{
		this.uid = uid;
	}
		
	public string Filename()
	{
		return  directory+uid+".desktop";
	}
	
	public bool Exists()
	{
		return FileUtils.test(directory+uid+".desktop", FileTest.EXISTS | FileTest.IS_REGULAR);
		
	}
}


[DBusInterface (name = "org.awnproject.taskmand")]
interface Taskman.TaskmanInterface;


public class DBusComm : GLib.Object 
{
        private		DBus.Connection		conn;
		private		Taskman.TaskmanInterface	taskobj;
		
        construct
        {
                conn = DBus.Bus.get (DBus.BusType.SESSION);
   				taskobj = conn.get_object<Taskman.TaskmanInterface> ("org.awnproject.taskmand", "/org/awnproject/taskmand");
        }

		public void Register(string uid)
		{	
			taskobj.Launcher_Register(uid);
		}
		
		public void Unregister(string uid)
		{
			taskobj.Launcher_Unregister(uid);
		}
		
		public string Inform_Task_Ownership(string uid, string xid, string request)
		{
			string response;
			response=taskobj.Inform_Task_Ownership(uid,xid,request);
			return response;
		}
}

class DiagButton: Gtk.Button
{
	private		Wnck.Window		win				{ get; construct; }
	private		Gtk.Widget		container		{ get; construct; }
	private		int				icon_size		{ get; construct; }     

    
	construct
	{
		weak Gdk.Pixbuf pbuf;
		if (! win.get_icon_is_fallback() )
		{
			weak Gdk.Pixbuf pbuf;
			pbuf=win.get_icon();
			pbuf=pbuf.scale_simple (icon_size-2, icon_size-2, Gdk.InterpType.BILINEAR );
		}	
		if (pbuf==null)
		{
			pbuf=win.get_icon();
		}
		Gtk.Image   image=new Gtk.Image.from_pixbuf(pbuf);
		set_label(win.get_name() );
		set_image(image);
		this.button_press_event += _clicked;	
	}
	
	DiagButton(Wnck.Window win,Gtk.Widget container,int icon_size) 
    {
        this.win = win;
        this.container = container;
        this.icon_size = icon_size;
    }
	
    private bool _clicked(Gtk.Widget widget,Gdk.EventButton event)
    {
		if (win.is_active() )
		{
			win.minimize();
		}
		else
		{
			win.activate(Gtk.get_current_event_time());
		}
		container.hide();
		return true;
	}
}

class LauncherApplet : AppletSimple 
{

    protected	IconTheme				theme;
    protected	Pixbuf					icon;
    protected   Gtk.Window				dialog;
    protected   Gtk.VButtonBox			vbox;
    protected	DesktopItem				desktopitem;
    protected   Configuration			config;
	protected	TargetEntry[]			targets;
	protected	SList<ulong>			XIDs;
	protected	SList<ulong>			PIDs;	
	protected   SList<Wnck.Window>		windows;
	protected   Wnck.Screen				wnck_screen;
	protected   DesktopFileManagement   desktopfile;
	protected   int						launchmode;
	protected   int						taskmode;
	protected   DBusComm				dbusconn;
	protected   ConfigClient			awn_config;
	protected   SList<ulong>			retry_list;	
	protected   Awn.Title               title;
	//protected   Awn.Effects             effects;
	protected   string                  title_string;
	protected   bool                    hidden;
	protected   int                     timer_count;
    protected   Gtk.Menu               right_menu;	

    construct 
    { 
        timer_count=0;
        blank_icon();
		this.realize += _realized;        
		hidden=true;
    }


    private void blank_icon()
    {
        Pixbuf  hidden_icon;       
        set_size_request( height, -1);
        icon=new Pixbuf( Colorspace.RGB,true, 8, height-2,height-2);
        icon.fill( 0x00000066);
        set_icon(icon);
    }


    private void hide_icon()
    {
        if (hidden==false)
        {
            Pixbuf  hidden_icon;      
            stdout.printf("Hiding\n"); 
            set_size_request( 2, 2);
            hidden_icon=new Pixbuf( Colorspace.RGB,true, 8, 2,2);
            hidden_icon.fill( 0x00000000);
            set_icon(hidden_icon);
            hidden=true;
        }            
    }

    private bool _hide_icon()
    {
        hide_icon();
        return false;
    }
    
    private void show_icon()
    {
        if (hidden)
        {
            set_size_request(height, -1);    //not really necessary
            hidden=false;
        }      
        if (icon!=null)              
            set_icon(icon);
    }    

    private bool _initialize()
    {
        stdout.printf("initializing.......................................\n");
		this.button_press_event+=_button_press;

		targets = new TargetEntry[2];
		targets[0].target = "text/uri-list";
		targets[0].flags = 0;
		targets[0].info =  0;
		targets[1].target = "text/plain";
		targets[1].flags = 0;
		targets[1].info =  0;

		drag_dest_set(this, Gtk.DestDefaults.ALL, targets, 2, Gdk.DragAction.COPY);
		//this.drag_drop+=_drag_drop;
		this.drag_data_received+=_drag_data_received;
        this.enter_notify_event+=_enter_notify;
        this.leave_notify_event+=_leave_notify;
		dialog=new AppletDialog(this);
		dialog.set_accept_focus(false);
		dialog.set_app_paintable(true);
		vbox=new VButtonBox();
		dialog.add(vbox);
        build_right_click();

		dbusconn = new DBusComm();
		dbusconn.Register(uid);
		awn_config= new ConfigClient();
				
		wnck_screen = Wnck.Screen.get_default();	
		wnck_screen.force_update();	
        theme = IconTheme.get_default ();        
		icon = theme.load_icon ("stock_stop", height - 2, IconLookupFlags.USE_BUILTIN);
		title_string = new string();
		title = new Awn.Title();
		title = (Awn.Title) Awn.Title.get_default();
		//effects = new Awn.Effects();
		//Effects.init(this,effects);		
       // effects.set_title(title, _get_title);

		if (icon!=null)
			set_icon (icon);   
		if (uid.to_double()>0)
		{				
            desktopfile = new DesktopFileManagement(uid);
			config=new Configuration(uid,false);
			launchmode = LaunchMode.DISCRETE;
			desktopitem = new DesktopItem(desktopfile.Filename() );			
			if (!desktopfile.Exists() )
			{
				desktopitem.set_exec("false");
				desktopitem.set_icon("stock_stop");
				desktopitem.set_item_type("Application");
				desktopitem.set_item_type("None");				
				desktopitem = new DesktopItem(desktopfile.Filename() );
			}
    		title_string = desktopitem.get_name();
		}
		else
		{
			config=new Configuration(uid,true);
			launchmode = LaunchMode.ANONYMOUS;
		    Wnck.Window win=find_win_by_xid(uid.substring(1,128).to_ulong() );

		    if (win!=null)
		    {		    
				string response;
				response=dbusconn.Inform_Task_Ownership(uid,win.get_xid().to_string(),"CLAIM");
				if (response!="MANAGE")
				{
					if (response=="RESET")
					{
						dbusconn.Register(uid);					
						response=dbusconn.Inform_Task_Ownership(uid,win.get_xid().to_string(),"CLAIM");					
					}
					if (response=="HANDSOFF")
					{
						close();
					}			
				}
				set_anon_desktop(win);
                if (desktopitem==null)
                {			               
                    stdout.printf("desktopitme == null. exiting\n");
                    close();
                }
				win.name_changed+=_win_name_change;
				win.state_changed+=_win_state_change;				
                title_string=win.get_name();
				XIDs.prepend(win.get_xid());
				PIDs.prepend(win.get_pid());
				windows.prepend(win);
				icon=win.get_icon();		//the fallback				
				if (icon !=null)
				{
					icon=icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );
					set_icon (icon );   
				}
		    }			
		    else
		    {
				close();
		    }
		}	
		if (desktopitem.exists() )  //we will use a user specified one if it exists.
		{
			if (desktopitem.get_icon(theme)!=null)
			{
				icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
			}		
		}	
		if (icon!=null)
			set_icon (icon );   

		wnck_screen.window_closed+=_window_closed;
		wnck_screen.window_opened+=_window_opened;		
		wnck_screen.application_closed+=_application_closed;
		wnck_screen.application_opened+=_application_opened;	
		wnck_screen.active_window_changed+=	_active_window_changed;

		taskmode=TaskMode.MULTIPLE;
        show_icon();        
        desktopitem.set_string ("Type","Application");        
		return false;
    }

    
    public LauncherApplet(string uid, int orient, int height) 
    {
        this.uid = uid;
        this.orient = orient;
        this.height = height;
    }

    private string _get_title()
    {
        stdout.printf("In get_title() \n");
        return title_string;
    }    

    private void set_anon_desktop(Wnck.Window win)
    {
        string  temp=new string();
		string  exec=new string();    
		Wnck.Application app=win.get_application();	
		if (app.get_name()!=null)
		{
		    temp=app.get_name();
            desktopfile = new DesktopFileManagement(temp);
			desktopfile.set_name(temp);		
		}
		else
		{
		    temp=win.get_name();
		    desktopfile = new DesktopFileManagement(temp);		
			desktopfile.set_name(temp);
		}		
		stdout.printf("creating desktop = %s, %s\n",temp,desktopfile.Filename());
		desktopitem = new DesktopItem(desktopfile.Filename() );
        desktopitem.set_string ("Type","Application");		 		
        desktopitem.save(desktopfile.Filename());
//        desktopitem = new DesktopItem(desktopfile.Filename() );        
		desktopitem.set_name(temp);
		if (! desktopitem.exists() )		
		{
			desktopitem.set_icon("none");
			desktopitem.set_item_type("Application");
			desktopitem.set_exec("false");			
		}

        
		string filename=new string();
		if (win.get_pid() != 0)
		{
		    bool result;
		    filename="/proc/"+(win.get_pid()).to_string()+"/cmdline";
		    try{
                result=FileUtils.get_contents(filename,out exec);
            }catch (GLib.FileError ex){
                result=false;
            }    		    
        	if (result)
        	{
        		desktopitem.set_exec(exec);
        		try{
            		desktopitem.save(desktopfile.Filename() );
            	}catch(GLib.Error ex){
            	    stdout.printf("error writing file %s\n",desktopfile.Filename());
            	}
        		if (desktopitem.get_icon(theme)=="none")
        		{
        			desktopitem.set_icon(GLib.Path.get_basename(exec));			
        		}		
    		}    	
        }
        else
        {
        
        }
        try{
    		desktopitem.save(desktopfile.Filename() );	
    	}catch(GLib.Error ex){
    	    stdout.printf("error writing file %s\n",desktopfile.Filename());
    	}
        desktopitem.set_string ("Type","Application");		    	
//        desktopitem.save(desktopfile.Filename());    	
//		desktopitem = new DesktopItem(desktopfile.Filename() );						
    }
        
    private void close()
    {
		string needle;
		stdout.printf("Closing uid = %s\n",uid);
		weak SList<string> applet_list;
		int fd_lock=Awn.ConfigClient.key_lock_open(Awn.CONFIG_CLIENT_DEFAULT_GROUP,"applets_list");
		if (fd_lock!=-1)
		{
			Awn.ConfigClient.key_lock(fd_lock,1);
		    dbusconn.Unregister(uid);
			applet_list = awn_config.get_list (Awn.CONFIG_CLIENT_DEFAULT_GROUP,"applets_list", Awn.ConfigListType.STRING) ;
			needle="standalone-launcher.desktop::"+uid;

		    for ( int i = 0; i < applet_list.length(); i++) 
		    {
				if( applet_list.nth_data(i).str(needle) !=null)
				{
		            applet_list.delete_link(applet_list.nth(i) );
		            i=0;
				}
		    }
			awn_config.set_list(Awn.CONFIG_CLIENT_DEFAULT_GROUP,"applets_list", Awn.ConfigListType.STRING,applet_list);
			Awn.ConfigClient.key_lock_close(fd_lock);
		}						
		Thread.exit(null);
		assert_not_reached ();
    }

    private bool _drag_drop(Gtk.Widget widget,Gdk.DragContext context,int x,int y,uint time)
    {
        stdout.printf("Drag_ drop \n");
		return true;
    }  

    private void _drag_data_received(Gtk.Widget widget,Gdk.DragContext context,int x,int y,Gtk.SelectionData selectdata,uint info,uint time)
    {    
		weak SList <string>	fileURIs;
		string  cmd;  
		bool status=false;
		stdout.printf("Drag and drop received \n");
		fileURIs=vfs_get_pathlist_from_string(selectdata.data);
		foreach (string str in fileURIs) 
		{
			print_desktop(desktopitem);			
			if (uid.to_double()>0)
			{

				DesktopItem		tempdesk;
				tempdesk = new DesktopItem(Filename.from_uri(str));
				if (tempdesk.exists() )
				{
					if ( (tempdesk.get_exec() != null) && (tempdesk.get_name()!=null) )
					{
                        try{
    						tempdesk.save(desktopfile.Filename());//FIXME - throws
                    	}catch(GLib.Error ex){
                    	    stdout.printf("error writing file %s\n",desktopfile.Filename());
                    	}
						
						desktopitem = tempdesk;//new DesktopItem(desktopfile.Filename() );				
						if (desktopitem.get_icon(theme) != null)
						{
							icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
						}
						else
						{
							icon = theme.load_icon ("stock_stop", height - 2, IconLookupFlags.USE_BUILTIN);
						}		
                        if (icon!=null)              
                            set_icon(icon);
				        while( XIDs.length()>0 ) 
				        {
				    		int val = XIDs.nth_data(0);
							XIDs.remove_all(val);	
				        }
						status=true;				        
					}	        
				}
			}		
			print_desktop(desktopitem);						
			Pixbuf temp_icon;
			temp_icon=new Pixbuf.from_file_at_scale( Filename.from_uri(str) ,height-2,height-2,true );
			if (temp_icon !=null)
			{

				icon=temp_icon;
				if (launchmode == LaunchMode.ANONYMOUS)
				{	
					Wnck.Window  win;		
					if (XIDs.length() > 0 )
					{		
						ulong xid=XIDs.nth_data(0);
						win=find_win_by_xid(xid);
					}
					else
						break;
//					if ( wnck_screen.get_workspaces().find(win) !=null)
					{
//						set_anon_desktop(win);
						desktopitem.set_icon(Filename.from_uri(str) );							
					}			
				}			
				else
				{
					desktopitem.set_icon(Filename.from_uri(str) );					
				}			
				try {
    				desktopitem.save(desktopfile.Filename() );				
            	}catch(GLib.Error ex){
            	    stdout.printf("error writing file %s\n",desktopfile.Filename());
            	}
				
                if (icon!=null)              
                    set_icon(icon);
				status=true;
			}
		}		
		drag_finish (context, status, false, time);		

    }  

    private Wnck.Window  find_win_by_xid(ulong xid)
    {
		weak	GLib.List	<Wnck.Window>	wins;
		wins=wnck_screen.get_windows();
		foreach (Wnck.Window win in wins)
		{
			if (win.get_xid() == xid)
			{
				return win;
			}		
		}
		return null;
    }

    
    private Wnck.Window  find_win_by_pid(ulong pid)
    {
		weak	GLib.List	<Wnck.Window>	windows;
		windows=wnck_screen.get_windows();
		foreach (Wnck.Window win in windows)
		{
			if (win.get_pid() == pid)
			{
				return win;
			}		
		}
		return null;
    }
    
	private static bool _toggle_win(Wnck.Window win)
	{
	
		return true;
	}
    
    private void button_dialog()
    {
		if (dialog.visible )
		{
			dialog.hide();
		}
		else
		{
			vbox.destroy();
			vbox = new VButtonBox();
			vbox.set_app_paintable(true);

			dialog.add(vbox);
			foreach (Wnck.Window win in windows)
			{

				DiagButton  button = new DiagButton(win,dialog,height);//win.get_name() 				
				vbox.add(button);
			}
			dialog.show_all();
		}		
    }
    
    private bool single_left_click()
    {
		ulong		xid;
		Wnck.Window  win;
		if (XIDs.length() == 1 )
		{		
			dialog.hide();
			xid=XIDs.nth_data(0);
			win=find_win_by_xid(xid);
            if (win==null)
            {
                if (PIDs.length()>0)
                {
                    stdout.printf("win = null. curious. trying pid.\n");
                    ulong   pid=PIDs.nth_data(0);
                    win=find_win_by_pid(pid);
                }
            }
			if (win!=null)
			{
				if (win.is_active() )
				{
					win.minimize();
				}
				else
				{
					win.activate(Gtk.get_current_event_time());
				}
			}
			return (win!=null);			
		}		
		else
		{
			button_dialog();
		}
		return true;
    }
    
    private bool _click_right_menu(Gtk.Widget widget,Gdk.EventButton event)
    {
    
        Process.spawn_command_line_async(config.desktop_file_editor+" "+desktopfile.Filename() );
        return false;
    }
    private void build_right_click()
    {
        Gtk.MenuItem   menu_item;
        right_menu=new Menu();
        menu_item=new MenuItem.with_label ("Edit Launcher");
        
        right_menu.append(menu_item);
        menu_item.show();
        menu_item.button_press_event+=_click_right_menu;
    }
    
    private void right_click(Gdk.EventButton event)
    {
        right_menu.popup(null, null, null, null,
			  event.button, event.time);
            
    }
     
    private bool _button_press(Gtk.Widget widget,Gdk.EventButton event)
    {
		ulong	pid;
		int		xid;

        bool	launch_new=false;
		SList<string>	documents;
		switch (event.button) 
		{
			case 1:
				launch_new=true;	
				if (XIDs.length() > 0 )
				{
					launch_new=!single_left_click();
				}
                else if (PIDs.length()>0)
                {
                    stdout.printf("This should not be happening!!!!!!!!!!!!!!!\n");
                    pid=PIDs.nth_data(0);
                    Wnck.Window win=find_win_by_pid(pid);
                }
			case 2:
				launch_new=true;
            case 3:
                launch_new=false;
                right_click(event);
			default:
				break;
		}
						
		if ( launch_new && (desktopitem!=null) )
		{
			pid=desktopitem.launch(documents);
			if (pid>0)
			{
				stdout.printf("launched: pid = %d\n",pid);
				PIDs.append(pid);
			}
			else if (pid==-1)
			{
				Process.spawn_command_line_async(desktopitem.get_exec());
			}
		}
		return false;
    }
    
    
    
	private void _realized()
	{

        Timeout.add(200,_initialize,this);
	}

    private bool _leave_notify(Gtk.Widget widget,Gdk.EventCrossing event)
    {
        title.hide(this );
        return false;   
    }

    
    private bool _enter_notify(Gtk.Widget widget,Gdk.EventCrossing event)
    {
        title.show(this,title_string );
        return false;   
    }
    
	private void _window_closed(Wnck.Screen screen,Wnck.Window window)
	{ 
		dialog.hide();
		
//		if (windows.find(window) !=null)
		{		
    		XIDs.remove(window.get_xid() );
        }    		
        
		if ( (XIDs.length() == 0) &&  (windows.find(window)!=null) )
		{
			if (launchmode == LaunchMode.ANONYMOUS)
			{
				Timeout.add(500,_hide_icon,this);	
				timer_count++;		
				Timeout.add(30000,_timed_closed,this);
			}				
		}

		if (windows.find(window) !=null)
		{
			Pixbuf new_icon=null;
			
    		windows.remove(window);			
			if (config.override_app_icon )
			{
				if (desktopitem.get_icon(theme) != null)
				{			
					new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
				}
			}			
			else if (!window.get_icon_is_fallback() && !config.override_app_icon )
			{
				new_icon=window.get_icon();
			}
			if (XIDs.length() >0)
			{
				ulong xid;
				Wnck.Window win;
				xid=XIDs.nth_data(0);
				win=find_win_by_xid(xid);
				if (config.override_app_icon )
				{
					if ( desktopitem.get_icon(theme) != null)
					{
						new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
					}			
				}				
				else if (!win.get_icon_is_fallback())
				{
					new_icon=win.get_icon();
				}			
			}
			if (new_icon !=null)
			{
				new_icon=new_icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );
			}
			if (new_icon == null)
				if ( desktopitem.get_icon(theme) != null )
				{
					new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws			
				}		
			if (new_icon !=null)
			{
				icon=new_icon;
				set_icon (icon ); 
			}
		}
	}
	
	private bool _timed_closed()
	{
	    timer_count--;
	    if (timer_count <=0)
	    {
        	if (XIDs.length() == 0)
        	{
        		close();
            }        		
		}	
		return false;
	}
	
	private bool _try_again()
	{
		foreach( ulong xid in retry_list)
		{
			string response;
			response=dbusconn.Inform_Task_Ownership(uid,xid.to_string(),"ACCEPT");
			if (response=="MANAGE")
			{
				Pixbuf new_icon;
				Wnck.Window win=find_win_by_xid(xid);
				if (win!=null)          
					windows.prepend(win);
                else
                    continue;					
				XIDs.prepend(xid);
				retry_list.remove(xid);

				if (launchmode == LaunchMode.ANONYMOUS)
				{
					Wnck.Application app=win.get_application();
					desktopfile.set_name(app.get_name());
				}
			
				if (config.override_app_icon )
				{
					if (desktopitem.get_icon(theme) != null)
					{
						new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME 
					}
				}
				else if (! win.get_icon_is_fallback() ||  (desktopitem.get_icon(theme) == null) )
				{
					new_icon=win.get_icon();
					new_icon=new_icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );
				}
				else
				{
					new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
				}
				icon=new_icon;
				win.name_changed+=_win_name_change;
				win.state_changed+=_win_state_change;				
                title_string=win.get_name();
                show_icon();                
			}
			else if (response=="HANDSOFF")
			{
				retry_list.remove(xid);
			}
			else if (response=="RESET")
			{
				dbusconn.Register(uid);										
			}		
		}		
		return (retry_list.length() != 0 );
	}
	
	private void _window_opened(Wnck.Screen screen,Wnck.Window window)
	{ 
		string response;
		int pid;
		ulong xid;
		bool	accepted=false;		
		xid=window.get_xid();
		
		if ( (XIDs.length()>0) && (config.task_mode==TaskMode.SINGLE) )
		{
			string response;
			do
			{
			    response=dbusconn.Inform_Task_Ownership(uid,xid.to_string(),"DENY");
                if (response=="RESET")  
					dbusconn.Register(uid);													    
            }while(response=="RESET");			    
			return;
		}

		if ( (XIDs.find(window.get_xid()) != null) || (windows.find(window)!=null) )
		{
		    return;     
		}

        if (window.is_skip_tasklist())
        {
            return;
        }

        string exec = new string();
        string filename=new string();
/*        	
        filename="/proc/"+(window.get_pid()).to_string()+"/cmdline";
        if ( FileUtils.get_contents(filename,out exec)==false)
        {
            exec=".";
        }
        */
        string desk_name=desktopitem.get_name();
        if (desk_name == null)
        {
            desk_name=".";
        }
        if ( (PIDs.find(window.get_pid() ) !=null))
        {
            do
            {
                response=dbusconn.Inform_Task_Ownership(uid,xid.to_string(),"CLAIM");
                if (response=="MANAGE")
                {
                    Pixbuf  new_icon;
                    windows.prepend(window);
                    XIDs.prepend(xid);
                    if (launchmode == LaunchMode.ANONYMOUS)
                    {	
                        Wnck.Application app=window.get_application();	
                        desktopfile.set_name(app.get_name());		
                    }		
                    if (desktopitem.get_icon(theme) != null)
                    {
                        new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
                    }
                    else
                    {
                        new_icon=window.get_icon();
                        new_icon=new_icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );							
                    }		
                    icon=new_icon;
                    show_icon();  
                    title_string=window.get_name();
                    window.name_changed+=_win_name_change;
                    window.state_changed+=_win_state_change;
                }
                else if (response=="RESET")
                    dbusconn.Register(uid);										
            }while (response=="RESET");
        }
        else
        {
            string  window_name = new string();
            window_name=window.get_name();
            int cmp_len=config.name_comparision_len>0?config.name_comparision_len:(desk_name.len()>window_name.len()?window_name.len():desk_name.len() );                		    			
            stdout.printf("window open: '%s', '%s'\n",window_name,desk_name);			                		
            if (desk_name.substring(0,cmp_len)==window_name.substring(0,cmp_len) ) //FIXME strncmp
            {
                accepted=true;                    
            }
            else
            {
                foreach(Wnck.Window win in windows)	 //does the new window match up with any of the existing ones.
                {
                    bool is_it_good=false;
                    is_it_good=(window.get_name()==win.get_name() ) ;
                    if (!is_it_good)
                        if ( (win.get_session_id ()!=null ) && (window.get_session_id () !=null))
                            is_it_good=(window.get_session_id () == win.get_session_id ());
                    if (is_it_good)
                    {
                        accepted=true;
                        break;
                    }
                }					
            }
        }
        if (accepted)
        {
            do
            {
                response=dbusconn.Inform_Task_Ownership(uid,xid.to_string(),"ACCEPT");
                if (response=="MANAGE")
                {
                    Pixbuf new_icon;
                    windows.prepend(window);
                    XIDs.prepend(xid);				
                    if (config.override_app_icon )
                    {
                        if (desktopitem.get_icon(theme) != null)
                        {				
                            new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME 
                        }			
                    }								
                    else if (! window.get_icon_is_fallback() ||  (desktopitem.get_icon(theme) == null) )
                    {
                        new_icon=window.get_icon();
                        new_icon=new_icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );							
                    }		
                    else
                    {
                        new_icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
                    }
                    icon=new_icon;
                    show_icon();
                    title_string=window.get_name();
                    window.name_changed+=_win_name_change;
                    window.state_changed+=_win_state_change;    
                }						
                else if (response=="RESET")
                    dbusconn.Register(uid);										
            }while (response=="RESET");							
        }
        else
        {
            response=dbusconn.Inform_Task_Ownership(uid,xid.to_string(),"DENY");
            if (response=="RESET")
                    dbusconn.Register(uid);	
        }					

		if (response=="WAIT")
		{
			retry_list.prepend(xid);
			if (retry_list.length()<2)
			{
				Timeout.add(100,_try_again,this);
			}		
		}
	}
    
    private void _win_name_change(Wnck.Window  window)
    {
        title_string=window.get_name();            
    }
    
    private void _win_state_change(Wnck.Window window,Wnck.WindowState changed_mask,Wnck.WindowState new_state)
    {
        stdout.printf("window state changed\n");
        if ( (Wnck.WindowState.DEMANDS_ATTENTION & new_state) == Wnck.WindowState.DEMANDS_ATTENTION )
        {
            stdout.printf("demanding attention\n");
  //          effect_start (effects, Effect.ATTENTION);
        }
    }    
    
	private void _application_closed(Wnck.Screen screen,Wnck.Application app)
	{ 
		PIDs.remove(app.get_pid() );	
	}
	
	private void _application_opened(Wnck.Screen screen,Wnck.Application app)
	{ 
		if (PIDs.find(app.get_pid() ) !=null)
		{
			desktopfile.set_name(app.get_name());	
//			desktopitem = new DesktopItem(desktopfile.Filename() );
			PIDs.append(app.get_pid() );		
		}		
	}

	private void _active_window_changed(Wnck.Screen screen,Wnck.Window prev)
	{
		Pixbuf  temp;
		bool	icon_changed=false;
	    bool    scale_icon=false;
	    
		Wnck.Window active=screen.get_active_window();//active can be null
		
		if (prev !=null)
		{
    		if (windows.find(prev) != null)
    		{
    			if (config.override_app_icon )
    			{
    				if (desktopitem.get_icon(theme) != null)
    				{				
    					icon_changed=true;			
    					icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
    				}			
    			}
    			else if (!prev.get_icon_is_fallback() )
    			{
    				icon_changed=true;				
    				icon=prev.get_icon();
                    scale_icon=true;
    			}		
    			
    		} 			
		}
		if (active !=null)
		{
    		if (windows.find(active) != null)
    		{
               // effect_stop (effects, Effect.ATTENTION);
                title_string=active.get_name();
                if (config.override_app_icon )
    			{
    				if (desktopitem.get_icon(theme) != null)
    				{
    					icon_changed=true;			
    					icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
    				}
    				else if (!active.get_icon_is_fallback() )
    				{
    					icon_changed=true;				
    					icon=active.get_icon();
                        scale_icon=true;
    				}
    			}
    			else if (!active.get_icon_is_fallback() )
    			{
    				icon_changed=true;				
    				icon=active.get_icon();
                    scale_icon=true;    				
    			}
    		}
        }    		
		if (icon_changed)	 
		{
		    if (scale_icon)
		    {
    			icon=icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );		
    		}
			if (icon !=null)
			{
				set_icon(icon);
			}			
		}	 
	}
}
 
public Applet awn_applet_factory_initp (string uid, int orient, int height) 
{
	LauncherApplet applet;
	Wnck.set_client_type (Wnck.ClientType.PAGER);
	applet = new LauncherApplet (uid, orient, height);
	applet.set_size_request (height, -1);
	applet.show_all ();
	return applet;
}

/* vim: set ft=cs noet ts=4 sts=4 sw=4 : */
