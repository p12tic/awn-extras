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
 * Author : Michal Hruby <michal.mhr@gmail.com>
 */

using Gtk;
using Cairo;
using Awn;
using DesktopAgnostic;

// our local "libraries"
using EggTray;
using NotificationAreaPrefs;

static bool gpm_workaround_done = false;

public class NotificationArea : GLib.Object
{
  private const int BORDER = 2;

  private EggTray.Manager manager;
  private Awn.Applet applet;
  private List<weak EggTray.Child> tray_icons;

  private static NotificationAreaPrefs? prefs_window = null;

  private int max_rows;
  private int max_cols;
  private int redraw_timer;

  private Quark addition_quark;
  private Quark deletion_quark;

  private Gtk.EventBox eb;
  private Awn.Alignment align;
  private Gtk.Alignment inner_align;
  private Gtk.EventBox icon_painter;
  private Gtk.Table table;

  private DesktopAgnostic.Config.Client client;

  public int icons_per_cell
  {
    get
    {
      return this.max_rows;
    }
    set
    {
      this.max_rows = value;
      this.max_cols = value;
      this.update_icon_sizes ();
      this.table_refresh ();
    }
  }

  private int _icon_size;
  public int icon_size
  {
    get
    {
      return _icon_size;
    }
    set
    {
      _icon_size = value;
      this.update_icon_sizes ();
    }
  }

  private int _extra_offset;
  public int extra_offset
  {
    get
    {
      return _extra_offset;
    }
    set
    {
      _extra_offset = value;
      this.align.set_offset_modifier (_extra_offset - BORDER);
    }
  }

  private DesktopAgnostic.Color? _background_color;
  [Description(nick="Background color", blurb="Background color")]
  public DesktopAgnostic.Color? background_color
  {
    get
    {
      return _background_color;
    }
    set
    {
      _background_color = value;
      this.eb.queue_draw ();
      this.icon_painter.queue_draw ();
    }
  }

  private DesktopAgnostic.Color? _border_color;
  [Description(nick="Border color", blurb="Border color")]
  public DesktopAgnostic.Color? border_color
  {
    get
    {
      return _border_color;
    }
    set
    {
      _border_color = value;
      this.eb.queue_draw ();
    }
  }

  public NotificationArea(Awn.Applet applet)
  {
    this.applet = applet;
    this.manager = new EggTray.Manager();
    this.tray_icons = new List<weak EggTray.Child>();

    this.max_rows = 2;
    this.max_cols = 2;
    this.redraw_timer = 0;

    this.addition_quark = Quark.from_string ("na-tray-icon-added");
    this.deletion_quark = Quark.from_string ("na-tray-icon-deleted");

    weak Gdk.Screen screen = applet.get_screen ();

    if (manager.manage_screen (screen) == false)
    {
      error ("Unable to manage the screen!");
    }

    // connect to tray-manager signals
    this.manager.tray_icon_added.connect (this.on_icon_added);
    this.manager.tray_icon_removed.connect (this.on_icon_removed);
    // connect to applet signals
    this.applet.position_changed.connect ((new_pos) =>
    {
      this.update_icon_sizes ();
      this.table_refresh ();
    });
    this.applet.size_changed.connect ((new_size) =>
    {
      this.update_icon_sizes ();
    });

    // this EventBox is needed to capture mouse clicks
    this.eb = new Gtk.EventBox ();
    Awn.Utils.ensure_transparent_bg (this.eb);

    this.align = new Awn.Alignment.for_applet (applet);
    this.align.set_offset_modifier (-BORDER);

    this.inner_align = new Gtk.Alignment (0f, 0f, 1f, 1f);
    this.inner_align.set_padding (BORDER, BORDER, BORDER, BORDER);

    this.icon_painter = new Gtk.EventBox ();
    Awn.Utils.ensure_transparent_bg (this.icon_painter);

    this.table = new Gtk.Table (1, 1, false);
    this.table.set_row_spacings (1);
    this.table.set_col_spacings (1);

    applet.add (this.eb);
    this.eb.add (this.align);
    this.align.add (this.inner_align);
    this.inner_align.add (this.icon_painter);

    if (screen.get_rgba_colormap () != null)
    {
      this.eb.set_colormap (screen.get_rgba_colormap ());
      this.icon_painter.set_colormap (screen.get_rgba_colormap ());
    }
    this.icon_painter.add (this.table);

    this.eb.expose_event.connect (this.on_applet_expose);
    this.eb.button_press_event.connect (this.button_press);

    Signal.connect_swapped (this.icon_painter, "expose-event",
                            (GLib.Callback)this.on_painter_expose, this);
    Signal.connect_swapped (this.icon_painter, "size-allocate",
                            (GLib.Callback)Gtk.Widget.queue_draw, this.eb);

    // bind our config keys
    this.client = Awn.Config.get_default_for_applet (applet);

    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "icons_per_cell", 
                      this, "icons-per-cell",
                      true, DesktopAgnostic.Config.BindMethod.FALLBACK);
    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "icon_size",
                      this, "icon-size",
                      true, DesktopAgnostic.Config.BindMethod.FALLBACK);
    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "extra_offset",
                      this, "extra-offset",
                      true, DesktopAgnostic.Config.BindMethod.FALLBACK);

    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "background_color", 
                      this, "background-color",
                      true, DesktopAgnostic.Config.BindMethod.FALLBACK);

    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "border_color", 
                      this, "border-color",
                      true, DesktopAgnostic.Config.BindMethod.FALLBACK);
  }

  private static void tray_icon_expose (Widget widget, Context cr)
  {
    weak EggTray.Child child = (EggTray.Child)widget;
    if (child.is_alpha_capable ())
    {
      cr.save ();

      Gdk.cairo_rectangle (cr, (Gdk.Rectangle)widget.allocation);
      cr.clip ();

      double x1, x2, y1, y2;
      cr.clip_extents (out x1, out y1, out x2, out y2);
      if (x2-x1 <= 0.0 || y2-y1 <= 0.0)
      {
        cr.restore();
        return;
      }

      Gdk.error_trap_push ();

      if (child.fake_transparency != 0)
      {
        Cairo.Surface? img_srfc = child.get_image_surface ();
        if (img_srfc != null)
        {
          cr.set_operator (Cairo.Operator.OVER);
          cr.set_source_surface (img_srfc,
                                 child.allocation.x,
                                 child.allocation.y);
          cr.paint ();
          cr.get_target ().flush ();
        }
      }
      else
      {
        Gdk.cairo_set_source_pixmap (cr, (Gdk.Pixmap*)widget.window,
                                     widget.allocation.x,
                                     widget.allocation.y);
        cr.paint ();
      }

      cr.restore ();

      Gdk.flush ();
      if (Gdk.error_trap_pop () != 0)
      {
        //message ("error!");
      }
    }
  }

  private bool on_painter_expose (Gdk.Event event, Gtk.Bin eb)
  {
    Cairo.Context? cr = Gdk.cairo_create (eb.window);
    Gdk.cairo_region (cr, event.expose.region);
    cr.clip ();

    cr.set_operator (Cairo.Operator.CLEAR);
    cr.paint ();

    cr.set_operator (Cairo.Operator.OVER);
    if (this._background_color != null)
    {
      Awn.CairoUtils.set_source_color (cr, this._background_color);
      cr.paint ();
    }
    else
    {
      DesktopAgnostic.Color da_color = 
        new DesktopAgnostic.Color (eb.style.bg[Gtk.StateType.ACTIVE], 65535);
      if (eb.is_composited ())
      {
        da_color.alpha = 65535 / 5;
      }
      Awn.CairoUtils.set_source_color (cr, da_color);
      cr.paint ();
    }

    weak Widget? child = eb.get_child ();
    if (child != null)
    {
      weak Gtk.Container container = (Gtk.Container)child;
      // container is actually this.table
      foreach (weak Widget w in container.get_children ())
      {
        this.tray_icon_expose (w, cr);
      }
    }

    cr = null;

    if (child != null)
    {
      eb.propagate_expose (child, event.expose);
    }

    return true;
  }

  private bool on_applet_expose (Gdk.EventExpose event)
  {
    Cairo.Context? cr = Gdk.cairo_create (this.eb.window);
    if (cr == null) return false;

    int x = this.inner_align.allocation.x;
    int y = this.inner_align.allocation.y;
    int w = this.inner_align.allocation.width;
    int h = this.inner_align.allocation.height;

    Gdk.cairo_region (cr, event.region);
    cr.clip ();

    cr.set_operator (Cairo.Operator.OVER);

    if (this._background_color != null)
    {
      Awn.CairoUtils.set_source_color (cr, this._background_color);
    }
    else
    {
      DesktopAgnostic.Color da_color = 
        new DesktopAgnostic.Color (eb.style.bg[Gtk.StateType.ACTIVE], 65535);
      if (this.applet.is_composited ())
      {
        da_color.alpha = 65535 / 5;
      }
      Awn.CairoUtils.set_source_color (cr, da_color);
    }
    cr.set_line_width (1.0);
    Awn.CairoUtils.rounded_rect (cr, x+0.5, y+0.5, w-1.0, h-1.0, 2.0*BORDER,
                                 Awn.CairoRoundCorners.ALL);
    if (this._border_color == null) cr.fill ();
    else cr.fill_preserve ();

    // don't paint the border by default
    if (this._border_color != null)
    {
      Awn.CairoUtils.set_source_color (cr, this._border_color);

      cr.set_operator (Cairo.Operator.DEST_OUT);
      cr.set_line_width (1.5);
      cr.stroke_preserve ();

      cr.set_operator (Cairo.Operator.OVER);
      cr.set_line_width (1.0);
      cr.stroke ();
    }

    return true;
  }

  private bool button_press (Gdk.EventButton event)
  {
    if (event.button == 3)
    {
      if (prefs_window == null)
      {
        prefs_window = new NotificationAreaPrefs (this.applet);
        unowned Gtk.Dialog dialog = prefs_window.get_dialog ();

        dialog.run ();
        dialog.destroy ();
        prefs_window = null;
      }
      else
      {
        var dialog = prefs_window.get_dialog ();
        dialog.present_with_time (event.time);
      }
      return true;
    }

    return false;
  }

  private void table_refresh ()
  {
    if (this.applet == null || this.table == null) return;
    
    int row = 0, col = 0;
    Gtk.PositionType position = this.applet.get_pos_type ();

    // stop displaying tray icons which were removed and update positions of
    // those which should still be displayed
    foreach (weak Widget icon in this.table.get_children ())
    {
      void* del = icon.get_qdata (this.deletion_quark);
      if (del != null)
      {
        this.table.remove (icon);
      }
      else
      {
        this.table.child_set (icon, 
                              "left-attach", col, "right-attach", col+1,
                              "top-attach", row, "bottom-attach", row+1);
        if (position == Gtk.PositionType.TOP ||
            position == Gtk.PositionType.BOTTOM)
        {
          row++;
          if (row == this.max_rows)
          {
            row = 0;
            col++;
          }
        }
        else
        {
          col++;
          if (col == this.max_cols)
          {
            col = 0;
            row++;
          }
        }
      }
    }

    // display tray icons which were added
    foreach (weak EggTray.Child icon in this.tray_icons)
    {
      void* added = icon.get_qdata (this.addition_quark);

      if (added == null) continue;

      icon.set_qdata (this.addition_quark, 0.to_pointer());
      this.table.attach_defaults (icon, col, col+1, row, row+1);

      if (position == Gtk.PositionType.TOP ||
          position == Gtk.PositionType.BOTTOM)
      {
        row++;
        if (row == this.max_rows)
        {
          row = 0;
          col++;
        }
      }
      else
      {
        col++;
        if (col == this.max_cols)
        {
          col = 0;
          row++;
        }
      }
    }

    uint elements = this.tray_icons.length ();
    uint num_rows, num_cols;
    uint rows = max_rows, cols = max_cols;

    if (position == Gtk.PositionType.TOP ||
        position == Gtk.PositionType.BOTTOM)
    {
      num_cols = this.table.n_columns;
      cols = elements % max_rows == 0 ? 
        num_cols / max_rows : num_cols / max_rows + 1;
    }
    else
    {
      num_rows = this.table.n_rows;
      rows = elements % max_cols == 0 ?
        num_rows / max_cols : num_rows / max_cols + 1;
    }
    this.table.resize (rows > 0 ? rows : 1, cols > 0 ? cols : 1);
    this.table.queue_draw ();
  }

  private int get_tray_icon_size ()
  {
    // we need to take care of the spacing in the table
    int size = (int)this.applet.get_size ();
    int icon_size = (size - (this.max_rows - 1)) / this.max_rows;
    icon_size = icon_size * this._icon_size / 100;

    // let's special case when we have two rows - use only even numbers for 
    // the icon sizes, so icons can have sharp edges
    if (this.max_rows == 2)
    {
      if (icon_size % 2 != 0)
      {
        icon_size--;
      }
      Gtk.PositionType position = this.applet.get_pos_type ();
      int extra_space = int.max (size - icon_size * this.max_rows, 1);
      if (position == Gtk.PositionType.TOP ||
          position == Gtk.PositionType.BOTTOM)
      {
        this.table.set_row_spacings (extra_space);
        this.table.set_col_spacings (1);
      }
      else
      {
        this.table.set_row_spacings (1);
        this.table.set_col_spacings (extra_space);
      }
    }
    else
    {
      this.table.set_row_spacings (1);
      this.table.set_col_spacings (1);
    }
    return icon_size < 1 ? 1 : icon_size;
  }

  private void update_icon_sizes ()
  {
    int icon_size = this.get_tray_icon_size ();
    foreach (weak EggTray.Child icon in this.tray_icons)
    {
      icon.set_size_request (icon_size, icon_size);
    }
  }

  private void on_icon_added (Widget widget)
  {
    unowned EggTray.Child icon = (EggTray.Child)widget;

    // workaround for https://bugzilla.gnome.org/show_bug.cgi?id=604579
    if (!gpm_workaround_done && icon.get_title () == "gnome-power-manager")
    {
      Timeout.add (2000, workaround_gpm_bug);
      gpm_workaround_done = true;
    }

    icon.set_qdata (this.addition_quark, 1.to_pointer());
    icon.set_qdata (this.deletion_quark, 0.to_pointer());

    this.tray_icons.append (icon);

    int icon_size = this.get_tray_icon_size ();
    icon.set_size_request (icon_size, icon_size);

    this.table_refresh ();
  }

  private void on_icon_removed (Widget widget)
  {
    unowned EggTray.Child icon = (EggTray.Child)widget;
    icon.set_qdata (this.deletion_quark, 1.to_pointer());

    this.tray_icons.remove (icon);

    this.table_refresh ();
  }

  private bool redraw_scheduler ()
  {
    this.eb.queue_draw ();
    switch (this.redraw_timer)
    {
      case 50:
        this.redraw_timer = 150;
        break;
      case 150:
        this.redraw_timer = 350;
        break;
      case 350:
        this.redraw_timer = 850;
        break;
      default:
        this.redraw_timer = 0;
        break;
    }
    if (this.redraw_timer != 0)
    {
      Timeout.add (this.redraw_timer, this.redraw_scheduler);
    }
    return false;
  }

  public bool on_visibility_change (Gdk.Event event, Widget applet)
  {
    if (event.visibility.state == Gdk.VisibilityState.UNOBSCURED)
    {
      if (applet.is_composited () && this.redraw_timer == 0)
      {
        // problem with redraw + fade-out auto-hide, composited windows really
        // don't like the hiding (same workaround is implemented in AwnPanel)
        this.redraw_timer = 50;
        Timeout.add (this.redraw_timer, this.redraw_scheduler);
      }
    }
    return false;
  }
}

// see https://bugzilla.gnome.org/show_bug.cgi?id=604579
public bool workaround_gpm_bug ()
{
  string command = "python -c \"" +
    "import gconf;" +
    "c = gconf.Client();" +
    "key = '/apps/gnome-power-manager/ui/icon_policy';" +
    "pol = c.get_string(key);" +
    "c.set_string(key, 'always');" +
    "c.set_string(key, pol);" +
    "\"";

  GLib.Process.spawn_command_line_async (command);

  return false;
}

public Applet?
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  if (EggTray.Manager.check_running (Gdk.Screen.get_default ()))
  {
    string msg = "There is already another notification area running" +
                 " on this screen!";
    MessageDialog d = new MessageDialog (null, DialogFlags.MODAL, 
                                         MessageType.ERROR, ButtonsType.CLOSE,
                                         "%s", msg);
    d.format_secondary_text ("Please remove the existing notification area" +
                             " and then restart the applet.");
    d.run ();

    error ("%s", msg);
    return null;
  }

  Applet applet = new Applet (canonical_name, uid, panel_id);

  NotificationArea na = new NotificationArea (applet);
  applet.set_data ("notification-area", na.@ref ());

  applet.add_events(Gdk.EventMask.VISIBILITY_NOTIFY_MASK);
  Signal.connect_swapped (applet, "visibility-notify-event",
                          (GLib.Callback)NotificationArea.on_visibility_change,
                          na);

  return applet;
}

