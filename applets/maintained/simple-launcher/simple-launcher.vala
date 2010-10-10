/*
 * Copyright (C) 2010 Michal Hruby <michal.mhr@gmail.com>
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
 * Author : Michal Hruby <michal.mhr@gmail.com>
 */

using Awn;
using DesktopAgnostic;
//using Zeitgeist;

class SimpleLauncher : Applet
{
  static const string DESKTOP_ENTRY = "desktop-entry-object";

  //private Zeitgeist.Log zg_log = new Zeitgeist.Log ();
  private IconBox icon_box;
  private Awn.ThemedIcon add_icon;
  private Gtk.Menu menu;
  private Gtk.MenuItem remove_menu_item;
  private Gtk.MenuItem edit_menu_item;
  private DesktopAgnostic.Config.Client client;
  private string config_dir;
  private GenericArray<Awn.ThemedIcon> launchers;
  private uint timer_id = 0;

  private ValueArray _launcher_list = new ValueArray (4);
  public ValueArray launcher_list
  {
    get
    {
      return _launcher_list;
    }
    set
    {
      _launcher_list = value.copy ();
    }
  }

  const Gtk.TargetEntry[] targets = {
    { "text/uri-list", 0, 0 },
    { "text/plain",    0, 0 }
  };

  public SimpleLauncher (string canonical_name, string uid, int panel_id)
  {
    Object (canonical_name: canonical_name, uid: uid, panel_id: panel_id);

    init_widgets ();

    this.notify["launcher-list"].connect (this.launchers_changed);
    launchers_changed ();
  }

  private void init_widgets ()
  {
    menu = this.create_default_menu () as Gtk.Menu;
    menu.append (new Gtk.SeparatorMenuItem ());
    edit_menu_item = new Gtk.MenuItem.with_label ("Edit Launcher");
    edit_menu_item.activate.connect (this.edit_clicked);
    menu.append (edit_menu_item);
    remove_menu_item = new Gtk.MenuItem.with_label ("Remove Launcher");
    remove_menu_item.activate.connect (this.remove_clicked);
    menu.append (remove_menu_item);
    menu.show_all ();

    icon_box = new IconBox.for_applet (this);

    add_icon = new Awn.ThemedIcon ();
    add_icon.drag_and_drop = false;
    add_icon.set_size (this.size);
    Gtk.drag_dest_set (add_icon,
                       Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP,
                       targets,
                       Gdk.DragAction.COPY);
    (add_icon as Gtk.Widget).drag_data_received.connect (this.uri_received);
    add_icon.set_info_simple (canonical_name, uid, "add");
    add_icon.set_tooltip_text ("Drop launcher here");
    add_icon.show ();

    icon_box.add (add_icon);
    icon_box.set_child_packing (add_icon, false, false, 0, Gtk.PackType.END);
    icon_box.show ();

    this.add (icon_box);
  }

  construct
  {
    this.config_dir = Path.build_filename (Environment.get_user_config_dir (),
                                           "awn", "applets", "simple-launcher",
                                           null);
    DirUtils.create_with_parents (config_dir, 0755);

    launchers = new GenericArray<Awn.ThemedIcon> ();

    this.client = Awn.Config.get_default_for_applet (this);

    try
    {
      this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "launcher_list",
                        this, "launcher-list",
                        false, DesktopAgnostic.Config.BindMethod.FALLBACK);
    }
    catch (DesktopAgnostic.Config.Error err)
    {
      critical ("Config Error: %s", err.message);
    }
  }

  private void uri_received (Gdk.DragContext context,
                             int x, int y,
                             Gtk.SelectionData data,
                             uint info,
                             uint time_)
  {
    if (data == null || data.get_length () == 0)
    {
      Gtk.drag_finish (context, false, false, time_);
      return;
    }

    SList<VFS.File> files = VFS.files_from_uri_list ((string) data.data);
    process_uri (files.data);

    Gtk.drag_finish (context, true, false, time_);
  }

  private void process_uri (VFS.File file)
  {
    string uri = file.uri;
    debug ("received %s", uri);

    var df = get_new_desktop_file ();

    if (uri.has_suffix (".desktop"))
    {
      FDO.DesktopEntry de = FDO.desktop_entry_new_for_file (file);
      de.save (df);
    }
    else
    {
      FDO.DesktopEntry link_entry = FDO.desktop_entry_new ();
      link_entry.entry_type = FDO.DesktopEntryType.LINK;
      link_entry.name = Uri.unescape_string (Path.get_basename (uri));
      link_entry.set_string ("URL", uri);
      // TODO: link_entry.icon = "";
      link_entry.save (df);
    }

    var path = df.path;
    Value v = path;
    _launcher_list.append (v);
    this.notify_property ("launcher-list");
  }

  private VFS.File get_new_desktop_file ()
  {
    VFS.File? f = null;
    int counter = 1;
    do
    {
      string path = Path.build_filename (
        config_dir,
        "launcher-%d.desktop".printf (counter++),
        null);
      f = VFS.file_new_for_path (path);
    } while (f.exists ());

    return f;
  }

  private void launchers_changed ()
  {
    int i;
    // mark all icons as untouched
    for (i=0; i<launchers.length; i++)
    {
      launchers[i].set_data ("untouched", 1);
    }

    // create new launchers
    int index = 0;
    foreach (Value v in _launcher_list)
    {
      string de_path = v.get_string ();
      bool found = false;
      for (i=0; i<launchers.length; i++)
      {
        FDO.DesktopEntry? de = launchers[i].get_data (DESKTOP_ENTRY);
        if (de != null && de.file.path == de_path)
        {
          launchers[i].set_data ("untouched", 0);
          found = true;

          icon_box.reorder_child (launchers[i], index);
          break;
        }
      }

      if (!found)
      {
        var icon = create_launcher (de_path);
        icon_box.reorder_child (icon, index);
      }

      index++;
    }

    // destroy removed launchers
    List<unowned Awn.ThemedIcon> l = new List<unowned Awn.ThemedIcon> ();
    for (i=0; i<launchers.length; i++)
    {
      if (launchers[i].get_data<int> ("untouched") != 0)
      {
        l.append (launchers[i]);
      }
    }

    foreach (unowned Awn.ThemedIcon ti in l)
    {
      remove_launcher (ti);
    }

    if (launchers.length > 0) add_icon.hide ();
    else add_icon.show ();
  }

  private Awn.ThemedIcon? create_launcher (string path)
  {
    var f = VFS.file_new_for_path (path);
    var de = FDO.desktop_entry_new_for_file (f);

    var icon = new Awn.ThemedIcon ();
    icon.drag_and_drop = false;
    icon.set_data (DESKTOP_ENTRY, de);
    icon.set_size (this.size);

    string icon_name = "image-missing";
    if (de.key_exists ("Icon"))
    {
      icon_name = de.get_string ("Icon");
      // FIXME: what if there's full path?
    }
    icon.set_info_simple (this.canonical_name,
                          this.uid,
                          icon_name);
    icon.set_tooltip_text (de.get_localestring ("Name", null));

    icon.clicked.connect (this.on_launcher_clicked);
    icon.context_menu_popup.connect (this.on_launcher_ctx_menu);
    icon_box.add (icon);
    icon.show ();

    Gtk.drag_dest_set (icon, 0, null, Gdk.DragAction.PRIVATE);
    icon.drag_motion.connect (this.on_launcher_drag_motion);

    launchers.add (icon);

    return icon;
  }

  private void remove_launcher (Awn.ThemedIcon launcher)
  {
    FDO.DesktopEntry de = launcher.steal_data (DESKTOP_ENTRY);
    if (de.file.path.has_prefix (config_dir))
    {
      de.file.remove ();
    }
    this.launchers.remove (launcher);
    launcher.destroy (); // removes the launcher from IconBox
  }

  private bool on_launcher_drag_motion ()
  {
    if (timer_id != 0)
    {
      Source.remove (timer_id);
    }
    timer_id = Timeout.add (2500,
                            () => { this.add_icon.hide (); return false; });
    add_icon.show ();
    return false;
  }

  private void on_launcher_clicked (Awn.Icon launcher)
  {
    FDO.DesktopEntry de = launcher.get_data (DESKTOP_ENTRY);
    return_if_fail (de != null);

    de.launch (0, null);
    launcher.get_effects ().start_ex (Awn.Effect.LAUNCHING, 1, false, false);
  }

  private void on_launcher_ctx_menu (Awn.Icon launcher, Gdk.EventButton event)
  {
    FDO.DesktopEntry de = launcher.get_data (DESKTOP_ENTRY);

    remove_menu_item.set_data (DESKTOP_ENTRY, launcher);
    edit_menu_item.set_sensitive (de.entry_type == FDO.DesktopEntryType.APPLICATION);
    edit_menu_item.set_data (DESKTOP_ENTRY, launcher);

    launcher.popup_gtk_menu (menu, event.button, event.time);
  }

  private void remove_clicked ()
  {
    Awn.ThemedIcon ti = remove_menu_item.get_data (DESKTOP_ENTRY);
    FDO.DesktopEntry de = ti.get_data (DESKTOP_ENTRY);

    uint index = 0;
    foreach (Value v in _launcher_list)
    {
      if (v.get_string () == de.file.path) break;
      index++;
    }

    if (index < _launcher_list.n_values) _launcher_list.remove (index);

    this.notify_property ("launcher-list");
  }

  private void edit_clicked ()
  {
    Awn.ThemedIcon ti = remove_menu_item.get_data (DESKTOP_ENTRY);
    FDO.DesktopEntry de = ti.get_data (DESKTOP_ENTRY);

    //var d = new UI.LauncherEditorDialog (de.file, null, false);
    var d = Object.@new (typeof (UI.LauncherEditorDialog),
                         "file", de.file, "output", null, null) as Gtk.Dialog;
    d.show_all ();
    d.run ();
    d.destroy ();
  }
}

public Applet?
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  return new SimpleLauncher (canonical_name, uid, panel_id);
}

