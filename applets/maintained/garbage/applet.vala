/*
 * Trash applet written in Vala.
 *
 * Copyright (C) 2008, 2009 Mark Lee <avant-wn@lazymalevolence.com>
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
using Gdk;
using Gtk;
using Awn;
using DesktopAgnostic;
using DesktopAgnostic.Config;

// only here so that config.h is before gi18n-lib.h
private const string not_used = Build.APPLETSDIR;

public class GarbageApplet : AppletSimple
{
  public VFS.Trash trash;
  private Client config;
  private Menu menu;
  private MenuItem empty_menu_item;
  private GarbagePrefs? prefs;
  private OverlayText? text_overlay;
  private OverlayThrobber? throbber_overlay;
  private OverlayProgress? progress_overlay;
  private bool highlighted;

  public bool show_count { get; set; }
  public bool confirm_empty { get; set; }

  const TargetEntry[] targets = {
    { "text/uri-list", 0, 0 },
    { "text/plain",    0, 0 }
  };

  construct
  {
    this.trash = VFS.trash_get_default ();
    this.trash.file_count_changed.connect (this.trash_changed);
    this.display_name = Gettext._ ("Garbage");
    this.map_event.connect (this.on_map_event);
    this.clicked.connect (this.on_clicked);
    this.context_menu_popup.connect (this.on_context_menu_popup);
    this.text_overlay = null;
    this.throbber_overlay = null;
    this.progress_overlay = null;
    this.highlighted = false;
  }

  public GarbageApplet (string canonical_name, string uid, int panel_id)
  {
    this.canonical_name = canonical_name;
    this.uid = uid;
    this.panel_id = panel_id;
    (this.get_icon () as Awn.ThemedIcon).set ("drag-and-drop", false);
    this.config = Awn.Config.get_default_for_applet (this);
    try
    {
      this.config.bind (GROUP_DEFAULT, "show_count", this, "show-count",
                        false, BindMethod.FALLBACK);
      this.config.bind (GROUP_DEFAULT, "confirm_empty", this, "confirm-empty",
                        false, BindMethod.FALLBACK);
      this.notify["show-count"].connect (this.on_prop_changed);
      this.render_applet_icon ();
    }
    catch (DesktopAgnostic.Config.Error err)
    {
      critical ("Config Error: %s", err.message);
    }
  }

  private void
  on_prop_changed (ParamSpec pspec)
  {
    this.render_applet_icon ();
  }

  private bool
  on_map_event (Event evt)
  {
    unowned Gtk.Widget icon = this.get_icon ();

    drag_dest_set (icon, DestDefaults.DROP | DestDefaults.MOTION,
                   targets, DragAction.MOVE);
    icon.drag_motion.connect (this.on_drag_motion);
    icon.drag_leave.connect (this.on_drag_leave);
    icon.drag_data_received.connect (this.on_drag_data_received);
    return true;
  }

  private void
  show_error_message (string msg)
  {
    // FIXME use libnotify?
    MessageDialog dialog;

    dialog = new MessageDialog (this, DialogFlags.MODAL, MessageType.ERROR,
                                ButtonsType.OK, msg);
    dialog.run ();
    dialog.destroy ();
  }

  private void
  render_applet_icon ()
  {
    uint file_count;
    string plural;

    file_count = this.trash.file_count;
    if (file_count > 0)
    {
      icon_name = "user-trash-full";
      if (this.empty_menu_item != null && !this.empty_menu_item.sensitive)
      {
        this.empty_menu_item.sensitive = true;
      }
    }
    else
    {
      icon_name = "user-trash";
      if (this.empty_menu_item != null && this.empty_menu_item.sensitive)
      {
        this.empty_menu_item.sensitive = false;
      }
    }
    // set icon
    this.set_icon_name (icon_name);
    // if requested, draw trash count when count > 0
    if (this.show_count && file_count > 0)
    {
      if (this.text_overlay == null)
      {
        unowned Overlayable overlayable;

        // moonbeam says get_icon generally returns Awn.ThemedIcon
        overlayable = this.get_icon () as Overlayable;
        this.text_overlay = new OverlayText ();
        overlayable.add_overlay (this.text_overlay);
      }

      if (!this.text_overlay.active)
      {
        this.text_overlay.active = true;
      }

      this.text_overlay.text = "%u".printf (file_count);
    }
    else if (this.text_overlay != null)
    {
      if (this.text_overlay.active)
      {
        this.text_overlay.active = false;
      }
    }
    // set the title as well
    // $display_name: $count item(s)
    plural = Gettext.ngettext ("%s: %u item", "%s: %u items", file_count);
    this.set_tooltip_text (plural.printf (this.display_name, file_count));
  }
  private void
  on_clicked ()
  {
    try
    {
      string[] argv = new string[] { "xdg-open", "trash:" };
      spawn_on_screen (this.get_screen (),
                       null,
                       argv,
                       null,
                       SpawnFlags.SEARCH_PATH,
                       null,
                       null);
    }
    catch (GLib.Error err)
    {
      string msg;
      msg = Gettext._ ("Could not open the trash folder with your file manager: %s")
            .printf (err.message);
    }
  }
  private void
  on_context_menu_popup (EventButton evt)
  {
    weak Menu ctx_menu;
    if (this.menu == null)
    {
      ImageMenuItem prefs_item;
      Widget about_item;

      this.menu = this.create_default_menu () as Menu;
      this.empty_menu_item =
        new MenuItem.with_mnemonic (Gettext._ ("_Empty Trash"));
      this.empty_menu_item.activate.connect (this.on_menu_empty_activate);
      this.empty_menu_item.set_sensitive (this.trash.file_count > 0);
      this.empty_menu_item.show ();
      this.menu.append (this.empty_menu_item);
      prefs_item = new ImageMenuItem.from_stock (STOCK_PREFERENCES, null);
      prefs_item.activate.connect (this.on_menu_prefs_activate);
      prefs_item.show ();
      this.menu.append (prefs_item);
      about_item = this.create_about_item_simple ("Copyright © 2009 Mark Lee <avant-wn@lazymalevolence.com>",
                                                  AppletLicense.GPLV2,
                                                  Build.VERSION);
      about_item.show ();
      this.menu.append (about_item as MenuItem);
    }
    ctx_menu = (Menu)this.menu;
    ctx_menu.set_screen (null);
    ctx_menu.popup (null, null, null, evt.button, evt.time);
  }
  private void
  on_menu_empty_activate ()
  {
    bool do_empty;

    if (this.confirm_empty)
    {
      string msg = Gettext._ ("Are you sure you want to empty your trash? It currently contains %u item(s).")
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
      if (this.throbber_overlay == null)
      {
        unowned Widget widget;
        unowned Overlayable overlayable;

        widget = this.get_icon ();
        // moonbeam says get_icon generally returns Awn.ThemedIcon
        overlayable = widget as Overlayable;
        this.throbber_overlay = new OverlayThrobber ();
        overlayable.add_overlay (this.throbber_overlay);
      }
      this.throbber_overlay.active = true;
      this.trash.empty ();
      this.throbber_overlay.active = false;
    }
  }
  private void
  on_menu_prefs_activate ()
  {
    if (this.prefs == null)
    {
      this.prefs = new GarbagePrefs (this);
    }
    this.prefs.show_all ();
  }
  private void
  trash_changed ()
  {
    this.render_applet_icon ();
  }

  private bool
  on_drag_motion (DragContext context, int x, int y, uint time)
  {
    if (!this.highlighted)
    {
      this.get_icon ().get_effects ().start (Effect.LAUNCHING);
      this.highlighted = true;
    }
    return true;
  }

  private void
  on_drag_leave (DragContext context, uint time)
  {
    if (this.highlighted)
    {
      this.get_icon ().get_effects ().stop (Effect.LAUNCHING);
      this.highlighted = false;
    }
  }

  private void
  on_drag_data_received (DragContext context, int x, int y, SelectionData data,
                         uint info, uint time)
  {
    SList<VFS.File> file_uris;

    if (data == null || data.get_length () == 0)
    {
      drag_finish (context, false, false, time);
      return;
    }

    if (this.progress_overlay == null)
    {
      unowned Overlayable overlayable;

      // moonbeam says get_icon generally returns Awn.ThemedIcon
      overlayable = this.get_icon () as Overlayable;
      this.progress_overlay = new OverlayProgressCircle ();
      overlayable.add_overlay (this.progress_overlay);
    }
    this.progress_overlay.percent_complete = 0.0;
    this.progress_overlay.active = true;

    try
    {
      double total;
      uint pos = 0;

      file_uris = VFS.files_from_uri_list ((string)data.data);
      total = (double)file_uris.length ();
      foreach (unowned VFS.File file in file_uris)
      {
        if (file.exists ())
        {
          this.trash.send_to_trash (file);
        }
        this.progress_overlay.percent_complete = (++pos) / total;
      }
    }
    catch (GLib.Error err)
    {
      string msg = Gettext._ ("Could not send the dragged file(s) to the trash: %s")
                   .printf (err.message);
      this.show_error_message (msg);
    }

    this.progress_overlay.active = false;
    drag_finish (context, true, true, time);
  }
}

public Applet
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  Intl.setlocale (LocaleCategory.ALL, "");
  Gettext.bindtextdomain (Build.GETTEXT_PACKAGE, Build.LOCALEDIR);
  Gettext.textdomain (Build.GETTEXT_PACKAGE);
  return new GarbageApplet (canonical_name, uid, panel_id);
}

// vim: set ft=vala et ts=2 sts=2 sw=2 ai :
