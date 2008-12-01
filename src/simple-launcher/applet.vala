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

class Configuration: GLib.Object
{
  public  string    uid   { get;
                            construct;
                          }
  protected   Awn.ConfigClient default_conf;
  private             string              _desktop_file_editor;

  construct
  {

    default_conf = new Awn.ConfigClient.for_applet("simple-launcher", null);
    read_config();
    default_conf.notify_add(CONFIG_CLIENT_DEFAULT_GROUP, "desktop_file_editor", this._config_changed);
  }

  private void _config_changed(Awn.ConfigClientNotifyEntry entry)
  {
    this.read_config_dynamic();
    stdout.printf("config notify fired\n");
  }

  Configuration(string uid)
  {
    this.uid = uid;
  }

  //config options that are monitored and can be dynamically changed
  private void read_config_dynamic()
  {
    _desktop_file_editor = get_string("desktop_file_editor", "awn-launcher-editor");
  }

  private void read_config()
  {
    read_config_dynamic();
  }

  public bool get_bool(string key, bool def = false)
  {
    bool value;

    try
    {
      value = default_conf.get_bool(CONFIG_CLIENT_DEFAULT_GROUP, key);
    }
    catch (GLib.Error ex)
    {
      value = def;
    }

    return value;
  }

  public float get_float(string key, float def = 0)
  {
    float value;

    try
    {
      value = default_conf.get_float(CONFIG_CLIENT_DEFAULT_GROUP, key);
    }
    catch (GLib.Error ex)
    {
      value = def;
    }

    return value;
  }

  public int get_int(string key, int def = 0)
  {
    int value;

    try
    {
      value = default_conf.get_int(CONFIG_CLIENT_DEFAULT_GROUP, key);
    }
    catch (GLib.Error ex)
    {
      value = def;
    }

    return value;
  }

  public string get_string(string key, string def = "")
  {
    string value;

    try
    {
      value = default_conf.get_string(CONFIG_CLIENT_DEFAULT_GROUP, key);
    }
    catch (GLib.Error ex)
    {
      value = def;
    }

    return value;
  }

  public string desktop_file_editor
  {
    get {
      return _desktop_file_editor;
    }
  }
}

//------------------------------------------------------------------------------

class LauncherApplet : AppletSimple
{
//    protected IconTheme    theme;
//    protected Pixbuf     icon;
  protected DesktopItem    desktopitem;//primary item
  protected   Configuration   config;
  protected TargetEntry[]   targets;
  protected   Awn.Title               title;
  protected   weak Awn.Effects        effects;
  protected   string                  title_string;
  protected   Gtk.Menu                right_menu;
  protected   string                  directory;

  construct
  {
    stdout.printf("construct\n");
    set_awn_icon("simple-launcher","stock_stop");    
    this.realize += _realized;
  }


  private bool _initialize()
  {
    stdout.printf("initialize\n");
    this.button_press_event += _button_press;
    targets = new TargetEntry[2];
    targets[0].target = "text/uri-list";
    targets[0].flags = 0;
    targets[0].info =  0;
    targets[1].target = "text/plain";
    targets[1].flags = 0;
    targets[1].info =  0;

    drag_source_set(this, Gdk.ModifierType.BUTTON1_MASK, targets, Gdk.DragAction.COPY);
    drag_dest_set(this, Gtk.DestDefaults.ALL, targets, Gdk.DragAction.COPY);
    this.drag_data_received += _drag_data_received;
    this.drag_data_get += _drag_data_get;
    build_right_click();

    //FIXME
    stdout.printf("create dir\n");
    directory = Environment.get_home_dir() + "/.config/awn/applets/simple-launcher/";

    if (! FileUtils.test(directory, FileTest.EXISTS))
    {
      if (DirUtils.create_with_parents(directory, 0777) != 0)
      {
        stdout.printf("Fatal error creating %s\n", directory);
      }
    }

    stdout.printf("finish create\n");

    stdout.printf("config\n");
    config = new Configuration(uid);
    stdout.printf("finish config\n");

    if (!FileUtils.test(directory + config.uid + ".desktop", FileTest.EXISTS))
    {
      stdout.printf("file does not exist\n");
      desktopitem = new DesktopItem(directory + config.uid + ".desktop");
      desktopitem.set_exec("false");
      desktopitem.set_icon("stock_stop");
      desktopitem.set_item_type("Application");
      desktopitem.set_name("None");
    }
    else
    {
      desktopitem = new DesktopItem(directory + config.uid + ".desktop");
    }

    if (desktopitem != null)
    {
      set_awn_icon("simple-launcher",desktopitem.get_string("Icon"));
    }
    effects = get_effects();
    effects.start_ex( Effect.LAUNCHING, null, null, 1);
    desktopitem.set_string("Type", "Application");
    return false;
  }

  public LauncherApplet(string uid, int orient, int height)
  {
    this.uid = uid;
    this.orient = orient;
    this.height = height;
  }

  private bool _drag_drop(Gtk.Widget widget, Gdk.DragContext context, int x, int y, uint time)
  {
    return true;
  }

  private void _drag_data_get(Gtk.Widget widget, Gdk.DragContext context, Gtk.SelectionData selection_data, uint info, uint time_)
  {
    stdout.printf("_drag_data_get\n");
    selection_data.set_text("test data\n", -1);
  }

  private void _drag_data_received(Gtk.Widget widget, Gdk.DragContext context, int x, int y, Gtk.SelectionData selectdata, uint info, uint time)
  {
    stdout.printf("drag data received\n");
    weak SList <string> fileURIs = null;
    string  cmd;
    bool status = false;

    try
    {
      fileURIs = vfs_get_pathlist_from_string((string)(selectdata.data));
    }
    catch (Error ex)
    {
      warning("Could not parse drag data.");
    }

    foreach(string str in fileURIs)

    {
      DesktopItem  tempdesk;
      string filename;

      try
      {
        filename = Filename.from_uri(str);
      }
      catch (ConvertError ex)
      {
        filename = "";
      }

      if (filename.has_suffix("desktop") )
      {
        tempdesk = new Awn.DesktopItem(filename);

        if (tempdesk.exists())
        {
          try
          {
            tempdesk.save("file://" + directory + config.uid + ".desktop");
          }
          catch (GLib.Error ex)
          {
            stderr.printf("error writing file %s\n", directory + config.uid + ".desktop");
          }

          desktopitem = new DesktopItem(directory + config.uid + ".desktop");

          if (desktopitem != null)
          {
            set_awn_icon("simple-launcher",desktopitem.get_string("Icon"));
          }
          else
          {
            set_awn_icon("simple-launcher","stock_stop");
          }        
          
          status = true;
        }
      }
    }
    drag_finish(context, status, false, time);
  }

  private bool _reread_config(Gtk.Widget widget, Gdk.EventButton event)
  {
    desktopitem = new DesktopItem(directory + config.uid + ".desktop");

    if (desktopitem != null)
    {
      set_awn_icon("simple-launcher",desktopitem.get_string("Icon"));
    }
    else
    {
      set_awn_icon("simple-launcher","stock_stop");
    }       
    return false;
  }

  private bool _desktop_edit(Gtk.Widget widget, Gdk.EventButton event)
  {
    try
    {
      Process.spawn_command_line_async(config.desktop_file_editor + " " + directory + config.uid + ".desktop");
    }
    catch (SpawnError ex)
    {
      stderr.printf("Failed to spawn '%s' \n", config.desktop_file_editor + " " + desktopitem.get_filename());
    }

    return false;
  }

  private void build_right_click()
  {
    Gtk.MenuItem   menu_item;
    right_menu = (Gtk.Menu) create_default_menu();  //FIXME typecast bad.

    menu_item = new MenuItem.with_label("Edit Launcher");
    right_menu.append(menu_item);
    menu_item.show();
    menu_item.button_press_event += _desktop_edit;

    menu_item = new MenuItem.with_label("Reread Configuration");
    right_menu.append(menu_item);
    menu_item.show();
    menu_item.button_press_event += _reread_config;

  }

  private void right_click(Gdk.EventButton event)
  {
    right_menu.popup(null, null, null, event.button, event.time);
  }

  private bool _button_press(Gtk.Widget widget, Gdk.EventButton event)
  {
    ulong pid = -1;
    int  xid;

    bool launch_new = false;
    SList<string> documents = null;
    uint multi_count = 0;

    effects.stop( Effect.ATTENTION); //effect off

    switch (event.button)
    {

      case 1:
        launch_new = true;       //yes we will launch.
        break;

      case 2:
        break;

      case 3:
        launch_new = false;
        right_click(event);
        break;

      default:
        break;
    }

    if (launch_new && (desktopitem != null))
    {
      effects.start_ex( Effect.LAUNCHING, null, null, 3);

      try
      {
        pid = desktopitem.launch(documents);
      }
      catch (Error ex)
      {
        warning("Launch error: %s", ex.message);
      }

      if (pid > 0)
      {
        stdout.printf("launched: pid = %lu\n", pid);
      }
      else if (pid == -1)
      {
        try
        {
          Process.spawn_command_line_async(desktopitem.get_exec());
        }
        catch (SpawnError ex)
        {
          stderr.printf("failed to spawn '%s'\n", desktopitem.get_exec());
        }
      }
    }

    return false;
  }

  private void _realized()
  {
    stdout.printf("realized\n");
    this.window.set_back_pixmap(null, false);
    this.show();
    Timeout.add(200, _initialize);
  }

  private bool _leave_notify(Gtk.Widget widget, Gdk.EventCrossing event)
  {
    title.hide(this);
    return false;
  }


  private bool _enter_notify(Gtk.Widget widget, Gdk.EventCrossing event)
  {

    title_string = desktopitem.get_name();
    title.show(this, title_string);
    return false;
  }

}

public Applet awn_applet_factory_initp(string uid, int orient, int height)
{
  LauncherApplet applet;
  applet = new LauncherApplet(uid, orient, height);
  applet.set_size_request(height, -1);
  applet.show_all();
  return applet;
}

/* vim: set ft=cs noet ts=4 sts=4 sw=4 : */
