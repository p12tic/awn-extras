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
using Zeitgeist;

[DBus (name = "org.wncksync.Matcher")]
interface WnckSyncMatcher : GLib.Object
{
  public abstract string desktop_file_for_xid (uint32 xid) throws DBus.Error;
  public abstract bool window_match_is_ready (uint32 xid) throws DBus.Error;
  public abstract void register_desktop_file_for_pid (string filename, int32 pid) throws DBus.Error;
  public abstract uint32[] xids_for_desktop_file (string filename) throws DBus.Error;
}

struct DesktopFileInfo
{
  string name;
  string[] mimetypes;
}

class RelatedApplet : AppletSimple
{
  private unowned Wnck.Screen wnck_screen;

  private DesktopLookupCached lookup = new DesktopLookupCached ();
  private Zeitgeist.Log zg_log = new Zeitgeist.Log ();
  private Overlay throbber = new OverlayThrobber ();
  private Overlay star_overlay = new OverlayThemedIcon (Gtk.STOCK_ABOUT);
  private HashTable<string, DesktopFileInfo?> desktop_file_info;

  private Awn.Dialog dialog;
  private Gtk.VBox vbox;
  private string? current_desktop_file_path;

  public RelatedApplet (string canonical_name, string uid, int panel_id)
  {
    Object (canonical_name: canonical_name, uid: uid, panel_id: panel_id);

    desktop_file_info = new HashTable<string, DesktopFileInfo?> (
      str_hash, str_equal
    );

    // setup wnck stuff
    wnck_screen = Wnck.Screen.get_default ();
    Wnck.set_client_type (Wnck.ClientType.PAGER);

    wnck_screen.window_opened.connect (this.window_opened);
    wnck_screen.active_window_changed.connect (this.window_changed);

    // overlay setup
    this.add_overlay (throbber);
    this.add_overlay (star_overlay);

    this.set_icon_name ("zeitgeist-logo");
    this.clicked.connect (this.on_clicked);

    // dialog setup
    this.dialog = new Awn.Dialog.for_widget (this);
  }

  construct
  {
    star_overlay.active = false;
    star_overlay.gravity = Gdk.Gravity.SOUTH_EAST;
    (star_overlay as OverlayThemedIcon).scale = 0.3;

    throbber.gravity = Gdk.Gravity.SOUTH_WEST;
    (throbber as OverlayThrobber).scale = 0.3;
  }

  private void window_opened (Wnck.Window window)
  {
    string? desktop_file = lookup.search_by_wnck_window (window);
    if (desktop_file == null)
    {
      // try wncksync
      try
      {
        DBus.Connection con = DBus.Bus.get (DBus.BusType.SESSION);
        var matcher = (WnckSyncMatcher) con.get_object (
          "org.wncksync.Matcher",
          "/org/wncksync/Matcher",
          "org.wncksync.Matcher");
      
        string df = matcher.desktop_file_for_xid ((uint32) window.get_xid ());
        if (df != null && df != "")
        {
          debug ("wncksync found match: %s", df);
          desktop_file = df;
        }
      }
      catch (GLib.Error err)
      {
        // ignore that we don't have wncksync
      }
    }

    // get mimetypes this desktop file supports
    if (desktop_file != null)
    {
      unowned DesktopFileInfo? df_data;
      df_data = desktop_file_info.lookup (desktop_file);
      if (df_data == null)
      {
        var keyfile = new KeyFile ();
        string[] mimetypes = {};
        string app_name = "";
        try
        {
          keyfile.load_from_file (desktop_file, KeyFileFlags.NONE);
          app_name = keyfile.get_locale_string ("Desktop Entry", "Name", null);
          mimetypes = keyfile.get_string_list ("Desktop Entry", "MimeType");
        }
        catch (GLib.Error err)
        {
        }
        var w = DesktopFileInfo ();
        w.name = (owned) app_name;
        w.mimetypes = (owned) mimetypes;
        desktop_file_info.insert(desktop_file, w);
      }
    }
    window.set_data ("desktop-file-path", desktop_file);
  }

  private void window_changed (Wnck.Window? old_window)
  {
    Wnck.Window? active = wnck_screen.get_active_window ();
    if (active != null)
    {
      /*
      // don't update star after activating our dialog
      //var dialog_flags = dialog.get_flags () & Gtk.WidgetFlags.VISIBLE;
      if (dialog.get_visible ()) //(dialog_flags != 0)
      {
        return;
      }
      */

      string? desktop_file = active.get_data ("desktop-file-path");
      if (desktop_file != null)
      {
        update_star (desktop_file);
      }
      else
      {
        star_overlay.active = false;
      }
    }
  }

  private async void update_star (string desktop_file)
  {
    var ptr_array = new PtrArray ();
    unowned string actor = desktop_file.rchr (-1, '/').offset (1);

    var event = new Event ();
    var event2 = new Event ();
    event.set_actor ("application://" + actor);
    ptr_array.add (event);

    unowned DesktopFileInfo? df_data;
    df_data = desktop_file_info.lookup (desktop_file);
    if (df_data != null && df_data.mimetypes.length > 0)
    {
      foreach (unowned string mimetype in df_data.mimetypes)
      {
        var subject = new Subject ();
        subject.set_mimetype (mimetype);
        event2.add_subject (subject);
      }
      ptr_array.add (event2);
    }

    // anything for these?
    var events = yield zg_log.find_event_ids (new TimeRange.to_now (),
                                              (owned) ptr_array,
                                              StorageState.ANY, 1,
                                              ResultType.MOST_POPULAR_SUBJECTS,
                                              null);

    star_overlay.active = events.length > 0;
    this.set_tooltip_text (events.length > 0 ?
      "Show items related to %s".printf (df_data.name) : null
    );
  }

  private async bool get_recent_by_mimetype (string[] mimetypes)
  {
    var ptr_array = new PtrArray ();
    var event = new Event ();
    foreach (unowned string mimetype in mimetypes)
    {
      var subject = new Subject ();
      subject.set_mimetype (mimetype);
      event.add_subject (subject);
    }
    ptr_array.add (event);

    var events = yield zg_log.find_events (new TimeRange.to_now (),
                                           (owned) ptr_array,
                                           StorageState.ANY, 16,
                                           ResultType.MOST_RECENT_SUBJECTS,
                                           null);

    int results_pushed = 0;
    foreach (unowned Event e in events)
    {
      if (e.num_subjects () > 0)
      {
        // process results
        Subject s = e.get_subject (0);
        if (results_pushed < 3 && push_result (e, s)) results_pushed++;
      }
    }

    return events.size () > 0;
  }

  private async bool get_events_for_actor (string? actor)
  {
    var ptr_array = new PtrArray ();
    var event = new Event ();
    if (actor != null) event.set_actor ("application://" + actor);
    ptr_array.add (event);
    var events = yield zg_log.find_events (new TimeRange.to_now (),
                                           (owned) ptr_array,
                                           StorageState.ANY, 16,
                                           ResultType.MOST_POPULAR_SUBJECTS,
                                           null);

    int results_pushed = 0;
    foreach (unowned Event e in events)
    {
      if (e.num_subjects () > 0)
      {
        // process results
        Subject s = e.get_subject (0);
        if (results_pushed < 4 && push_result (e, s)) results_pushed++;
      }
    }

    return events.size () > 0;
  }

  private async void build_dialog (string? desktop_file)
  {
    if (this.vbox != null) this.vbox.destroy ();
    this.vbox = new Gtk.VBox (false, 3);
    this.dialog.add (this.vbox);

    bool found1 = false;
    bool found2 = false;

    current_desktop_file_path = desktop_file;
    throbber.active = true;

    if (desktop_file != null)
    {
      // get items by mimetype
      unowned DesktopFileInfo? df_data;
      df_data = desktop_file_info.lookup (desktop_file);
      if (df_data != null && df_data.mimetypes.length > 0)
      {
        found1 = yield get_recent_by_mimetype (df_data.mimetypes);
      }
    }
    else
    {
      found1 = yield get_recent_by_mimetype ({});
    }

    // separator
    if (found1) vbox.add (new Gtk.HSeparator ());

    // get items by app
    unowned string actor = null;
    if (desktop_file != null) actor = desktop_file.rchr (-1, '/').offset (1);
    found2 = yield get_events_for_actor (actor);

    if (desktop_file != null && !found1 && !found2)
    {
      build_dialog (null);
      return;
    }

    throbber.active = false;

    if (!found1 && !found2)
    {
      var l = new Gtk.Label ("There are no items to display...");
      vbox.add (l);
    }
    this.dialog.show_all ();
  }

  private void on_clicked ()
  {
    var dialog_flags = dialog.get_flags () & Gtk.WidgetFlags.VISIBLE;
    if (dialog_flags != 0)
    {
      dialog.hide ();
      return;
    }
    dialog.hide_on_unfocus = true;

    Wnck.Window? active = wnck_screen.get_active_window ();

    string? desktop_file = active.get_data ("desktop-file-path");
    build_dialog (desktop_file);
  }

  private bool push_result (Zeitgeist.Event event, Zeitgeist.Subject subject)
  {
    var f = File.new_for_uri (subject.get_uri ());
    if (f.is_native () && !f.query_exists (null)) return false;

    string? text = subject.get_text ();
    if (text == null) text = f.get_basename ();

    GLib.Icon icon;
    if (f.is_native ())
    {
      var fi = f.query_info (FILE_ATTRIBUTE_STANDARD_ICON, 0, null);
      icon = fi.get_icon ();
    }
    else
    {
      icon = g_content_type_get_icon (subject.get_mimetype ());
    }

    var button = new Gtk.Button ();
    var hbox = new Gtk.HBox (false, 6);
    var image = new Gtk.Image.from_gicon (icon, Gtk.IconSize.BUTTON);
    var label = new Gtk.Label (text);
    label.set_ellipsize (Pango.EllipsizeMode.MIDDLE);
    label.set_max_width_chars (35);
    label.xalign = 0.0f;
    hbox.pack_start (image, false, true, 0);
    hbox.pack_start (label, true, true, 0);
    button.set_relief (Gtk.ReliefStyle.NONE);
    button.set_focus_on_click (false);
    button.add (hbox);
    button.set_tooltip_text (f.is_native () ? f.get_path () : f.get_uri ());
    var desktop_file = this.current_desktop_file_path;
    button.clicked.connect (() => {
      var context = new AppLaunchContext ();
      if (desktop_file == null)
      {
        AppInfo.launch_default_for_uri (f.get_uri (), context);
      }
      else
      {
        var app_info = new DesktopAppInfo.from_filename (desktop_file);
        if (app_info.supports_uris ())
        {
          var l = new List<string> ();
          l.append (f.get_uri ());
          app_info.launch_uris (l, context);
        }
        else
        {
          var l = new List<File> ();
          l.append (f);
          app_info.launch (l, context);
        }
      }
      this.dialog.hide ();
    });

    this.vbox.add (button);

    return true;
  }
}

public Applet?
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  return new RelatedApplet (canonical_name, uid, panel_id);
}

