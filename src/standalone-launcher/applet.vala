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
	
	construct
	{
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
	}
	
	public void set_name(string name)
	{
		uid=name;		
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
	
    construct 
    { 
		dialog=new AppletDialog(this);
		dialog.set_accept_focus(false);
		dialog.set_app_paintable(true);
		vbox=new VButtonBox();
		dialog.add(vbox);
		dbusconn = new DBusComm();
		dbusconn.Register(uid);
		awn_config= new ConfigClient();
		desktopfile = new DesktopFileManagement(uid);		
		wnck_screen = Wnck.Screen.get_default();	
		wnck_screen.force_update();	
        theme = IconTheme.get_default ();        
		icon = theme.load_icon ("stock_stop", height - 2, IconLookupFlags.USE_BUILTIN);
		if (icon!=null)
			set_icon (icon);   
		if (uid.to_double()>0)
		{				
			config=new Configuration(uid,false);
			launchmode = LaunchMode.DISCRETE;
			desktopitem = new DesktopItem(desktopfile.Filename() );			
			if (!desktopfile.Exists() )
			{
				desktopitem.set_exec("false");
				desktopitem.set_icon("stock_stop");
				desktopitem.set_item_type("Application");			
				desktopitem = new DesktopItem(desktopfile.Filename() );
			}
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
				XIDs.append(win.get_xid());
				PIDs.append(win.get_pid());
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
		
		targets = new TargetEntry[2];
		targets[0].target = "STRING";
		targets[0].flags = 0;
		targets[0].info =  0;
		targets[1].target = "text/uri-list";
		targets[1].flags = 0;
		targets[1].info =  0;

		wnck_screen.window_closed+=_window_closed;
		wnck_screen.window_opened+=_window_opened;		
		wnck_screen.application_closed+=_application_closed;
		wnck_screen.application_opened+=_application_opened;	
		wnck_screen.active_window_changed+=	_active_window_changed;


		this.realize += _realized;
		taskmode=TaskMode.MULTIPLE;
    }
    
    public LauncherApplet(string uid, int orient, int height) 
    {
        this.uid = uid;
        this.orient = orient;
        this.height = height;
    }
    

    private void set_anon_desktop(Wnck.Window win)
    {
		string  exec=new string();    
		Wnck.Application app=win.get_application();	
		if (app.get_name()!=null)
		{
			desktopfile.set_name(app.get_name());		
		}
		else
		{
			desktopfile.set_name(win.get_name());				
		}		
		desktopitem = new DesktopItem(desktopfile.Filename() );
				
		if (! desktopitem.exists() )		
		{
			desktopitem.set_icon("none");
			desktopitem.set_item_type("Application");
			desktopitem.set_exec("false");			
		}

		string filename=new string();
		filename="/proc/"+(win.get_pid()).to_string()+"/cmdline";
		if (FileUtils.get_contents(filename,out exec)==true )
		{
			desktopitem.set_exec(exec);
			desktopitem.save(desktopfile.Filename() );
			if (desktopitem.get_icon(theme)=="none")
			{
				desktopitem.set_icon(GLib.Path.get_basename(exec));			
			}		
		}    	
		desktopitem.save(desktopfile.Filename() );					
    }
        
    private void close()
    {
		string needle;
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
		return true;
    }  

    private void _drag_data_received(Gtk.Widget widget,Gdk.DragContext context,int x,int y,Gtk.SelectionData selectdata,uint info,uint time)
    {
		weak SList <string>	fileURIs;
		string  cmd;  
		bool status=false;
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
						tempdesk.save(desktopfile.Filename());//FIXME - throws
						desktopitem = tempdesk;//new DesktopItem(desktopfile.Filename() );				
						if (desktopitem.get_icon(theme) != null)
						{
							icon = new Pixbuf.from_file_at_scale(desktopitem.get_icon(theme),height-2,-1,true );//FIXME - throws
						}
						else
						{
							icon = theme.load_icon ("stock_stop", height - 2, IconLookupFlags.USE_BUILTIN);
						}		
						set_icon (icon );   
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
				desktopitem.save(desktopfile.Filename() );				
				set_icon(icon);	
				status=true;
			}
		}		
		drag_finish (context, status, false, time);		

    }  

    private Wnck.Window  find_win_by_xid(ulong xid)
    {
		weak	GLib.List	<Wnck.Window>	windows;
		windows=wnck_screen.get_windows();
		foreach (Wnck.Window win in windows)
		{
			if (win.get_xid() == xid)
			{
				return win;
			}		
		}
		return null;
    }

    
    private Wnck.Window  find_win_by_pid(int pid)
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
     
    private bool _button_press(Gtk.Widget widget,Gdk.EventButton event)
    {
		int		pid;
		int		xid;
		bool	launch_new=false;
		SList<string>	documents;
		stdout.printf("In button press \n");
		stdout.printf("exec = %s\n",desktopitem.get_exec() );
		switch (event.button) 
		{
			case 1:
				launch_new=true;			
				if (XIDs.length() > 0 )
				{
					launch_new=!single_left_click();
				}
			case 2:
				launch_new=true;
			default:
				break;
		}
						
		if ( launch_new && (desktopitem!=null) )
		{
			stdout.printf("Launching...\n");
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
		this.button_press_event+=_button_press;
		drag_dest_set(this, Gtk.DestDefaults.ALL, targets, 2, Gdk.DragAction.COPY);
		this.drag_drop+=_drag_drop;
		this.drag_data_received+=_drag_data_received;
	}
 
	private void _window_closed(Wnck.Screen screen,Wnck.Window window)
	{ 
		dialog.hide();
		windows.remove(window);
		XIDs.remove(window.get_xid() );
		if (XIDs.length() == 0)
		{
			if (launchmode == LaunchMode.ANONYMOUS)
			{
				Timeout.add(500,_timed_closed,this);
			}				
		}

		if (windows.find(window) !=null)
		{
			Pixbuf new_icon=null;
			
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
		if (XIDs.length() == 0)
		{
			close();
		}	
		return false;
	}
	
	private bool _try_again()
	{
		ulong xid;

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
				XIDs.prepend(xid);
				retry_list.remove(xid);

				if (launchmode == LaunchMode.ANONYMOUS)
				{	
					Wnck.Application app=win.get_application();	
					desktopfile.set_name(app.get_name());		
				}		
//				desktopitem = new DesktopItem(desktopfile.Filename() );
				
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
				set_icon (icon );   		
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
		xid=window.get_xid();
		if ( (XIDs.length()>0) && (config.task_mode==TaskMode.SINGLE) )
		{
			return;
		}
		if (XIDs.find(window.get_xid() )==null)
		{
			string window_name=window.get_name();
			string desk_name=desktopitem.get_name();
			int cmp_len=config.name_comparision_len>0?config.name_comparision_len:(desk_name.len()>window_name.len()?window_name.len():desk_name.len() );
			if ( 
				(PIDs.find(window.get_pid() ) !=null)
				||
				(  desk_name.substring(0,cmp_len) == window_name.substring(0,cmp_len) ) //FIXME strncmp
			)
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
//						desktopitem = new DesktopItem(desktopfile.Filename() );
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
						set_icon (icon );   					
					}
					else if (response=="RESET")
						dbusconn.Register(uid);										
				}while (response=="RESET");
			}
			else
			{
				bool	accepted=false;
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
						if (launchmode == LaunchMode.ANONYMOUS)
						{	
							Wnck.Application app=window.get_application();	
							desktopfile.set_name(app.get_name());		
						}		
//						desktopitem = new DesktopItem(desktopfile.Filename() );						
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
								set_icon (icon );   
							}						
							else if (response=="RESET")
								dbusconn.Register(uid);										
						}while (response=="RESET");							
					}
				}
				if (!accepted)
				{
					response=dbusconn.Inform_Task_Ownership(uid,xid.to_string(),"DENY");
					if (response=="RESET")
							dbusconn.Register(uid);	
				}					
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
	
		Wnck.Window active=screen.get_active_window();		
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
			}		
			
		} 	
		if (windows.find(active) != null)
		{
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
				}
			}
			else if (!active.get_icon_is_fallback() )
			{
				icon_changed=true;				
				icon=active.get_icon();
			}		
		}
		if (icon_changed)	 
		{
			icon=icon.scale_simple (height-2, height-2, Gdk.InterpType.BILINEAR );		
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
