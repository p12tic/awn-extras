/*
 * Copyright (C) 2009 Michal Hruby <michal.mhr@gmail.com>
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
 */

using Gdk;
using Gtk;
using Awn;
using DesktopAgnostic.Config;

// only here so that config.h is before gi18n-lib.h
private const string not_used = Build.APPLETSDIR;

[DBus (name = "org.awnproject.Applet.Terminal")]
public interface TerminalDBus : GLib.Object {
  public abstract void toggle (uint32 time_) throws DBus.Error;
}

public class AwnTerminalApplet : AppletSimple, TerminalDBus
{
  private Client config;
  private Menu menu;
  private Awn.Dialog dialog;
  private Gtk.Notebook notebook;
  private Gtk.FileChooserButton chooser;
  private Gtk.Image preview_image;
  private Gtk.Window prefs_window;
  private Gtk.ListStore model = null;

  private int number_of_tabs;

  private float _bg_opacity;
  public float bg_opacity
  {
    get { return _bg_opacity; }
    set { this._bg_opacity = value; this.dialog.set_opacity (value); }
  }

  public bool hide_on_unfocus
  {
    get { return this.dialog.hide_on_unfocus; }
    set { this.dialog.hide_on_unfocus = value; }
  }

  private string _background_image = null;
  public string background_image
  {
    get { return this._background_image; }
    set
    {
      this._background_image = value;
      for (int i = 0; i < this.notebook.get_n_pages (); i++)
      {
        Vte.Terminal term = this.notebook.get_nth_page (i) as Vte.Terminal;
        term.set_background_image_file (value);
      }
    }
  }

  private string _keybinding = null;
  public string keybinding
  {
    get { return _keybinding; }
    set
    {
      debug ("keybinding: %s", value);
      if (this._keybinding != null && this._keybinding.size () > 0)
      {
        // unbind
        Awn.Keybinder.unbind (this._keybinding, this.global_keypress);
      }
      this._keybinding = value;
      if (this._keybinding != null && this._keybinding.size () > 0)
      {
        // bind
        Awn.Keybinder.bind (this._keybinding, this.global_keypress);
      }

      if (this.model != null)
      {
        Gtk.TreeIter iter;
        if (this.model.get_iter_first (out iter))
        {
          this.model.set (iter, 1,
            this._keybinding != null && this._keybinding.size () > 0 ?
              this._keybinding : _ ("Disabled"));
        }
      }
    }
  }

  private string _terminal_command = null;
  public string terminal_command
  {
    get { return this._terminal_command; }
    set { this._terminal_command = value; }
  }

  private TimeVal last_inactive_time;

  public AwnTerminalApplet (string canonical_name, string uid, int panel_id)
  {
    this.canonical_name = canonical_name;
    this.uid = uid;
    this.panel_id = panel_id;
    this.display_name = "Awn Terminal Applet";
  }

  construct
  {
    Awn.Keybinder.init ();
    this.last_inactive_time = TimeVal ();
  }

  public override void
  constructed ()
  {
    base.constructed ();

    // set icon & tooltip    
    this.set_tooltip_text ("Awn Terminal");
    this.set_icon_name ("terminal");

    // connect applet signals
    this.get_icon ().clicked.connect (this.clicked_cb);
    this.get_icon ().middle_clicked.connect (this.middle_clicked_cb);
    this.get_icon ().context_menu_popup.connect (this.on_context_menu_popup);

    // construct dialog
    this.dialog = new Awn.Dialog.for_widget (this);
    this.dialog.set_skip_taskbar_hint (false);
    this.number_of_tabs = 0;

    Gtk.VBox box = new Gtk.VBox (true, 0);
    this.dialog.add (box);

    this.notebook = new Gtk.Notebook ();
    this.notebook.set_tab_pos (Gtk.PositionType.TOP);
    this.notebook.set_scrollable (true);
    box.add (this.notebook);

    this.create_new_tab ();

    this.dialog.hide_on_unfocus = true;
    this.dialog.hide_on_esc = false;

    this.dialog.notify["is-active"].connect ((obj, pspec) =>
    {
      if ((obj as Awn.Dialog).is_active == false)
      {
        this.last_inactive_time.get_current_time ();
      }
    });

    // bind config keys
    this.config = Awn.Config.get_default_for_applet (this);
    try
    {
      this.config.bind (GROUP_DEFAULT, "opacity", 
                        this, "bg-opacity",
                        false, BindMethod.FALLBACK);
      this.config.bind (GROUP_DEFAULT, "hide_on_unfocus",
                        this, "hide-on-unfocus",
                        false, BindMethod.FALLBACK);
      this.config.bind (GROUP_DEFAULT, "global_hotkey",
                        this, "keybinding",
                        false, BindMethod.FALLBACK);
      this.config.bind (GROUP_DEFAULT, "bg_img", 
                        this, "background-image",
                        false, BindMethod.FALLBACK);
      this.config.bind (GROUP_DEFAULT, "main_terminal",
                        this, "terminal-command",
                        false, BindMethod.FALLBACK);
    }
    catch (DesktopAgnostic.Config.Error err)
    {
      critical ("Config Error: %s", err.message);
    }
  }

  private void
  global_keypress (string keystring)
  {
    this.toggle (Awn.Keybinder.get_current_event_time ());
  }

  public void
  toggle (uint32 time_)
  {
    WidgetFlags flags = this.dialog.get_flags () & WidgetFlags.VISIBLE;
    bool should_hide = flags != 0;
    if (should_hide)
    {
      // should it REALLY hide?
      if (this.dialog.is_active)
      {
        should_hide = true;
      }
      else
      {
        should_hide = false;
        TimeVal cur_time = TimeVal ();
        long sec_diff = cur_time.tv_sec - this.last_inactive_time.tv_sec;
        if (sec_diff <= 1)
        {
          long usec_diff = sec_diff * 1000000 + cur_time.tv_usec -
                           this.last_inactive_time.tv_usec;
          if (usec_diff <= 250000) // one fourth of second
          {
            should_hide = true;
          }
        }
      }
    }
    if (should_hide)
    {
      this.dialog.hide ();
    }
    else
    {
      this.dialog.show_all ();
      this.dialog.present_with_time (time_);
    }
  }

  private void
  create_new_tab ()
  {
    Vte.Terminal terminal = new Vte.Terminal ();
    terminal.set_emulation ("xterm");
    terminal.fork_command (null, null, null, "~/", false, false, false);
    if (this._background_image != null)
    {
      terminal.set_background_image_file (this._background_image);
    }

    this.number_of_tabs++;

    Gtk.Label label = new Gtk.Label ("Term #%d".printf (this.number_of_tabs));
    this.notebook.append_page (terminal, label);
    if (this.notebook.get_n_pages () > 1)
    {
      this.notebook.set_show_tabs (true);
      this.dialog.show_all ();
    }
    else
    {
      this.notebook.set_show_tabs (false);
    }

    Signal.connect_swapped (terminal, "child-exited", 
                            (GLib.Callback)this.exited_cb, this);
    Signal.connect_swapped (terminal, "key-press-event",
                            (GLib.Callback)this.key_press_cb, this);
  }

  private void
  clicked_cb ()
  {
    WidgetFlags flags = this.dialog.get_flags () & WidgetFlags.VISIBLE;
    if (flags != 0)
    {
      this.dialog.hide ();
    }
    else
    {
      this.dialog.show_all ();
    }
  }

  private void
  middle_clicked_cb ()
  {
    string terminal = this._terminal_command;
    try
    {
      if (terminal == null || terminal.size () == 0)
      {
        terminal = "gnome-terminal";
      }
      Gdk.spawn_command_line_on_screen (this.get_screen (), terminal);
    }
    catch
    {
      warning ("Unable to run '%s'!", terminal);
    }
  }

  private bool
  key_press_cb (Gdk.EventKey event, Vte.Terminal terminal)
  {
    Gdk.ModifierType mods = (Gdk.ModifierType) event.state;
    Gdk.ModifierType is_ctrl = mods & Gdk.ModifierType.CONTROL_MASK;
    Gdk.ModifierType is_shift = mods & Gdk.ModifierType.SHIFT_MASK;
    if (is_ctrl != 0 && is_shift != 0)
    {
      unowned string key = Gdk.keyval_name (Gdk.keyval_to_lower (event.keyval));
      if (key == "c")
      {
        terminal.copy_clipboard ();
      }
      else if (key == "v")
      {
        terminal.paste_clipboard ();
      }
      else if (key == "t")
      {
        this.create_new_tab ();
        this.notebook.set_current_page (this.notebook.get_n_pages () - 1);
      }

      return true;
    }
    else if (is_ctrl != 0)
    {
      unowned string key = Gdk.keyval_name (Gdk.keyval_to_lower (event.keyval));
      if (key == "Page_Up")
      {
        int page = this.notebook.get_current_page () - 1;
        page = page % this.notebook.get_n_pages ();
        this.notebook.set_current_page (page);
        return true;
      }
      else if (key == "Page_Down")
      {
        int page = this.notebook.get_current_page () + 1;
        page = page % this.notebook.get_n_pages ();
        this.notebook.set_current_page (page);
        return true;
      }
    }
    return false;
  }

  private void
  exited_cb (Vte.Terminal terminal)
  {
    int pages = this.notebook.get_n_pages ();
    if (pages > 1)
    {
      int page = this.notebook.get_current_page ();
      this.notebook.remove_page (page);

      if (pages == 2)
      {
        this.notebook.set_show_tabs (false);
      }
      this.dialog.show_all ();
    }
    else
    {
      // clear everything
      terminal.reset (true, true);
      // fork new terminal
      terminal.fork_command (null, null, null, "~/", false, false, false);

      this.dialog.hide ();
    }
  }

  private void
  on_context_menu_popup (EventButton evt)
  {
    if (this.menu == null)
    {
      ImageMenuItem prefs_item;
      Widget about_item;

      this.menu = this.create_default_menu () as Menu;
      
      prefs_item = new ImageMenuItem.from_stock (STOCK_PREFERENCES, null);
      prefs_item.activate.connect (this.on_prefs_activate);
      prefs_item.show ();
      this.menu.append (prefs_item);
      about_item = 
        this.create_about_item_simple ("Copyright © 2009 Michal Hruby" +
                                       "<michal.mhr@gmail.com>",
                                       AppletLicense.GPLV2, Build.VERSION);
      about_item.show ();
      this.menu.append (about_item as MenuItem);
    }
    this.menu.set_screen (null);
    this.menu.popup (null, null, null, evt.button, evt.time);
  }

  private void
  on_prefs_activate ()
  {
    if (this.prefs_window != null)
    {
      this.prefs_window.show_all ();
      return;
    }

    this.prefs_window = new Gtk.Window (Gtk.WindowType.TOPLEVEL);
    this.prefs_window.set_title (_ ("Preferences"));
    this.prefs_window.set_default_icon_name ("terminal");
    this.prefs_window.set_border_width (6);

    this.prefs_window.delete_event.connect ((w, e) =>
    {
      w.hide ();
      return true;
    });

    // main box
    Gtk.Box box = new Gtk.VBox (false, 6);
    this.prefs_window.add (box);

    Gtk.Widget widget = new Gtk.Label ("");
    (widget as Gtk.Label).set_markup ("<b>%s</b>".printf (_ ("Behavior")));
    (widget as Gtk.Label).set_alignment (0.0f, 0.5f);
    box.pack_start (widget, false, false, 0);

    Gtk.Alignment align = new Gtk.Alignment (0.5f, 0.5f, 1.0f, 0.0f);
    align.set_padding (0, 0, 10, 0);
    box.pack_start (align, false, false, 0);

    Gtk.Box box2 = new Gtk.VBox (false, 6);
    align.add (box2);

    // focus out behavior checkbox
    widget = new Gtk.CheckButton.with_label (_ ("Hide when focus is lost"));
    (widget as CheckButton).set_active (this.hide_on_unfocus);
    (widget as CheckButton).toggled.connect ((w) =>
    {
      this.hide_on_unfocus = w.get_active ();
    });

    box2.pack_start (widget, false, false, 0);

    // keybinding treeview
    Gtk.CellRenderer ren;
    Gtk.TreeViewColumn col;

    Gtk.TreeView treeview = new Gtk.TreeView ();
    box2.pack_start (treeview, false, false, 0);
    this.model = new Gtk.ListStore (2, typeof (string), typeof (string));
    treeview.set_model (this.model);

    ren = new CellRendererText ();
    col = new TreeViewColumn.with_attributes (_ ("Action"), ren, "text", 0);
    treeview.append_column (col);

    ren = new CellRendererAccel ();
    (ren as CellRendererAccel).editable = true;
    (ren as CellRendererAccel).accel_mode = Gtk.CellRendererAccelMode.OTHER;
    (ren as CellRendererAccel).accel_edited.connect (
      (a, path, accel_key, accel_mods, keycode) =>
    {
      uint key;
      Awn.Keybinder.Egg.VirtualModifierType virt_mods;
      
      Awn.Keybinder.Egg.keymap_virtualize_modifiers (Gdk.Keymap.get_default (), accel_mods, out virt_mods);
      this.keybinding = Awn.Keybinder.Egg.virtual_accelerator_name (accel_key, virt_mods);
    });
    (ren as CellRendererAccel).accel_cleared.connect (
      (a, path) =>
    {
      this.keybinding = "";
    });
    col = new TreeViewColumn.with_attributes (_ ("Shortcut"), ren, "text",1);
    treeview.append_column (col);

    // add the actual item
    Gtk.TreeIter iter;
    this.model.append (out iter);
    this.model.set (iter, 0, _ ("Activate"));
    // this will set the keybinding in the model
    this.keybinding = this._keybinding;

    // background image section
    Gtk.Box section_box = new Gtk.VBox (false, 0);
    box.pack_start (section_box, false, false, 0);

    widget = new Gtk.Label ("");
    (widget as Gtk.Label).set_markup ("<b>%s</b>".printf (_ ("Background image")));
    (widget as Gtk.Label).set_alignment (0.0f, 0.5f);
    section_box.pack_start (widget, false, false, 0);

    align = new Gtk.Alignment (0.5f, 0.5f, 1.0f, 0.0f);
    align.set_padding (0, 0, 10, 0);
    section_box.pack_start (align, false, false, 0);

    box2 = new Gtk.HBox (false, 3);
    align.add (box2);

    this.preview_image = new Gtk.Image ();
    this.chooser = new Gtk.FileChooserButton (_ ("Select a file"),
                                        Gtk.FileChooserAction.OPEN);
    this.chooser.set_filename (this.background_image);
    this.chooser.set_preview_widget (this.preview_image);
    this.chooser.set_size_request (200, -1);

    this.chooser.file_set.connect ((w) => 
    {
      this.background_image = w.get_filename ();
    });

    this.chooser.update_preview.connect ((w) =>
    {
      string filename = w.get_preview_filename ();
      try
      {
        Gdk.Pixbuf? pixbuf = new Gdk.Pixbuf.from_file_at_size (filename, 128, 128);
        this.preview_image.set_from_pixbuf (pixbuf);
        w.set_preview_widget_active (true);
      }
      catch
      {
        w.set_preview_widget_active (false);
      }
    });

    box2.pack_start (this.chooser, true, true, 0);

    Gtk.Widget button = new Gtk.Button.from_stock (Gtk.STOCK_CLEAR);
    (button as Gtk.Button).clicked.connect ((b) =>
    {
      this.chooser.set_filename ("");
      this.background_image = "";
    });

    box2.pack_start (button, false, false, 0);

    // opacity section
    section_box = new Gtk.VBox (false, 0);
    box.pack_start (section_box, false, false, 0);

    widget = new Gtk.Label ("");
    (widget as Gtk.Label).set_markup ("<b>%s</b>".printf (_ ("Terminal opacity")));
    (widget as Gtk.Label).set_alignment (0.0f, 0.5f);
    section_box.pack_start (widget, false, false, 3);

    align = new Gtk.Alignment (0.5f, 0.5f, 1.0f, 0.0f);
    align.set_padding (0, 0, 10, 0);
    section_box.pack_start (align, false, false, 0);

    widget = new Gtk.HScale.with_range (0.1f, 1.0f, 0.1f);
    (widget as Gtk.Range).set_value (this._bg_opacity);
    (widget as Gtk.Scale).value_changed.connect ((w) =>
    {
      this.bg_opacity = (float)w.get_value ();
    });
    /* bug in Vala's Gtk bindings format-value declared as unowned string
    (widget as Gtk.Scale).format_value.connect ((w, v) =>
    {
      return "%d%%".printf ((int) GLib.Math.rint (v*100.0));
    });
    */
    align.add (widget);

    // external terminal command section
    section_box = new Gtk.VBox (false, 0);
    box.pack_start (section_box, false, false, 0);

    widget = new Gtk.Label ("");
    (widget as Gtk.Label).set_markup ("<b>%s</b>".printf (_ ("External Terminal")));
    (widget as Gtk.Label).set_alignment (0.0f, 0.5f);
    section_box.pack_start (widget, false, false, 3);

    align = new Gtk.Alignment (0.5f, 0.5f, 1.0f, 0.0f);
    align.set_padding (0, 0, 10, 0);
    section_box.pack_start (align, false, false, 0);

    widget = new Gtk.Entry ();
    (widget as Gtk.Entry).set_text (this.terminal_command);
    (widget as Gtk.Entry).focus_out_event.connect ((w, e) =>
    {
      this.terminal_command = (w as Gtk.Entry).get_text ();
    });
    align.add (widget);

    // close button
    box2 = new Gtk.HButtonBox ();
    (box2 as Gtk.ButtonBox).set_layout (Gtk.ButtonBoxStyle.END);
    box.pack_end (box2, false, false, 0);

    widget = new Gtk.Button.from_stock (Gtk.STOCK_CLOSE);
    box2.pack_start (widget, false, false, 0);
    (widget as Gtk.Button).clicked.connect ((w) =>
    {
      this.prefs_window.hide ();
    });
    
    this.prefs_window.show_all ();
  }
}

public Applet
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  Intl.setlocale (LocaleCategory.ALL, "");
  Gettext.bindtextdomain (Build.GETTEXT_PACKAGE, Build.LOCALEDIR);
  Gettext.textdomain (Build.GETTEXT_PACKAGE);

  var conn = DBus.Bus.get (DBus.BusType.SESSION);
  dynamic DBus.Object bus = conn.get_object ("org.freedesktop.DBus",
                                             "/org/freedesktop/DBus",
                                             "org.freedesktop.DBus");

  // try to register service in session bus
  uint result = bus.request_name ("org.awnproject.Applet.Terminal", (uint) 0);
  if (result != DBus.RequestNameReply.PRIMARY_OWNER)
  {
    warning ("Coudln't get ownership of org.awnproject.Applet.Terminal!");
  }

  AwnTerminalApplet applet = new AwnTerminalApplet (canonical_name, 
                                                    uid, panel_id);

  conn.register_object ("/org/awnproject/Applet/Terminal", applet);
                                                                
  return applet;
}

// vim: set ft=vala et ts=2 sts=2 sw=2 ai :
