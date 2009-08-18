/* 
 * Trash applet written in vala.
 *
 * Copyright (C) 2008 Mark Lee <avant-wn@lazymalevolence.com>
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
 * Author : Mark Lee <avant-wn@lazymalevolence.com>
 */

using Cairo;
using GLib;
using Gdk;
using Gtk;
using Awn;
using DesktopAgnostic;

public class GarbageApplet : AppletSimple
{
  private VFS.Implementation vfs;
  public VFS.Trash.Backend trash;
  protected ConfigClient config;
  protected string app_name;
  protected Context ctx;
  protected Surface sfc;
  protected Widget menu;

  /*const TargetEntry[] targets = {
    { "text/uri-list", 0, 0 },
    { "text/plain",    0, 0 },
    { null }
  };*/

  construct
  {
    this.vfs = vfs_get_default ();
    this.trash = (VFS.Trash.Backend)GLib.Object.new (this.vfs.trash_type);
    this.trash.file_count_changed += this.trash_changed;
    this.config = new ConfigClient.for_applet ("garbage", null);
    this.app_name = "Garbage";
    this.map_event += this.on_map_event;
    this.button_press_event += this.on_click;
  }

  public GarbageApplet (string uid, int orient, int height)
  {
    this.uid = uid;
    this.orient = orient;
    this.height = height;
  }

  private bool initialize_dragdrop ()
  {
    TargetEntry[] targets = new TargetEntry[2];
    targets[0].target = "text/uri-list";
    targets[0].flags = 0;
    targets[0].info =  0;
    targets[1].target = "text/plain";
    targets[1].flags = 0;
    targets[1].info =  0;
    drag_source_set (this, ModifierType.BUTTON1_MASK, targets, DragAction.COPY);
    drag_dest_set (this, DestDefaults.ALL, targets, DragAction.COPY);
    this.drag_data_received += this.on_drag_data_received;
    return false;
  }

  private bool on_map_event (GarbageApplet applet, Event evt)
  {
    this.render_icon ();
    Timeout.add (200, this.initialize_dragdrop);
    return true;
  }
  private void render_icon ()
  {
    Surface gdk_sfc;
    IconTheme theme;
    string icon_name;
    Pixbuf icon = null;
    int icon_height, widget_height;
    uint file_count;

    theme = IconTheme.get_default ();
    widget_height = (int)this.get_height ();
    icon_height = (int)(widget_height - 2);
    file_count = this.trash.file_count;
    if (file_count > 0)
    {
      icon_name = "user-trash-full";
    }
    else
    {
      icon_name = "user-trash";
    }
    try
    {
      icon = theme.load_icon (icon_name, icon_height, 0);
    }
    catch (Error e)
    {
      warning ("Could not load icon: %s", e.message);
      return;
    }

    if (this.ctx == null)
    {
      gdk_sfc = cairo_create (this.window).get_target ();
      this.sfc = new Surface.similar (gdk_sfc, Content.COLOR_ALPHA,
                                      widget_height, widget_height);
      this.ctx = new Context (this.sfc);
    }
    // clear context
    this.ctx.set_operator (Operator.SOURCE);
    // draw icon
    cairo_set_source_pixbuf (this.ctx, icon, 0, 0);
    // TODO if requested, draw trash count when count > 0
    try
    {
      if (this.config.get_bool ("DEFAULT", "show_count"))
      {
        // cairo/pango text drawing
      }
    }
    catch (Error e)
    {
      // do nothing
    }
    // finish with the context
    this.ctx.paint ();
    this.set_icon_context (this.ctx);
    // set the title as well
    string plural;
    if (file_count == 1)
    {
      plural = _("item");
    }
    else
    {
      plural = _("items");
    }
    this.set_title ("%s: %u %s".printf (this.app_name, file_count, plural));
  }
  private bool on_click (GarbageApplet widget, EventButton evt)
  {
    switch (evt.button)
    {
      case 1: /* left mouse click */
        try
        {
          //Process.spawn_command_line_async("xdg-open trash:");
          string[] argv = new string[] { "xdg-open", "trash:" };
          spawn_on_screen (widget.get_screen (),
                           null,
                           argv,
                           null,
                           SpawnFlags.SEARCH_PATH,
                           null,
                           0);
        }
        catch (Error e)
        {
          warning ("Could not open the trash folder in your file manager: %s",
                   e.message);
        }
        break;
      case 2: /* middle mouse click */
        break;
      case 3: /* right mouse click */
        weak Menu ctx_menu;
        if (this.menu == null)
        {
          MenuItem item;
          this.menu = this.create_default_menu ();
          item = new MenuItem.with_mnemonic (_("_Empty Trash"));
          item.activate += this.on_menu_empty_activate;
          item.show ();
          ((MenuShell)this.menu).append (item);
        }
        ctx_menu = (Menu)this.menu;
        ctx_menu.set_screen (null);
        ctx_menu.popup (null, null, null, evt.button, evt.time);
        break;
    }
    return true;
  }
  private void on_menu_empty_activate ()
  {
    bool do_empty;
    try
    {
      if (config.get_bool("DEFAULT", "confirm_empty"))
      {
        string msg = _ ("Are you sure you want to empty your trash? It " +
                        "currently contains %u item(s).")
                     .printf (this.trash.file_count);
        MessageDialog dialog = new MessageDialog ((Gtk.Window)this, 0,
                                                  MessageType.QUESTION,
                                                  ButtonsType.YES_NO, msg);
        int response = dialog.run ();
        dialog.destroy ();
        do_empty = (response == ResponseType.YES);
      }
      else
      {
        do_empty = true;
      }
      if (do_empty)
      {
        this.trash.empty ();
      }
    }
    catch (Error ex)
    {
      warning ("Error occurred when trying to retrieve 'confirm_empty' config option: %s",
               ex.message);
      /* show error dialog */
    }
  }
  private void trash_changed ()
  {
    this.render_icon ();
  }
  private void on_drag_data_received (GarbageApplet applet,
                                      DragContext context,
                                      int x,
                                      int y,
                                      SelectionData data,
                                      uint info,
                                      uint time)
  {
    SList<VFS.File.Backend> file_uris;

    try
    {
      file_uris = vfs.files_from_uri_list ((string)data.data);
      foreach (weak VFS.File.Backend file in file_uris)
      {
        if (file.exists)
        {
          this.trash.send_to_trash (file);
        }
      }
    }
    catch (Error err)
    {
      string msg = _ ("Could not send the dragged file(s) to the trash: %s")
        .printf (err.message);
      MessageDialog dialog = new MessageDialog ((Gtk.Window)this, 0,
                                                MessageType.ERROR,
                                                ButtonsType.OK, msg);
      dialog.run ();
      dialog.destroy ();
    }
  }
}

public Applet awn_applet_factory_initp (string uid, int orient, int height)
{
  GarbageApplet applet;

  applet = new GarbageApplet (uid, orient, height);
  applet.set_size_request (height, -1);
  applet.show_all ();
  return applet;
}

// vim: set ft=vala et ts=2 sts=2 sw=2 ai :
