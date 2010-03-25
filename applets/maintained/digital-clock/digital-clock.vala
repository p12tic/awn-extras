/*
 * Digital-clock applet for Awn (based on applet by Ryan Rushton)
 *
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
using DesktopAgnostic.Config;

class DigitalClock : AppletSimple
{
  private const string EVOLUTION_COMMAND =
    "evolution calendar:///?startdate=%(year)02d%(month)02d%(day)02dT120000";
  private const string TIME_ADMIN_COMMAND = "gksudo time-admin";
  private const string[] authors = {
    "Michal Hruby <michal.mhr@gmail.com>"
  };

  private Gtk.Menu _menu;
  private Awn.Dialog dialog;
  private OverlayText time_overlay;
  private OverlayText am_pm_overlay;
  private OverlayText day_overlay;
  private OverlayText date_overlay;

  private DesktopAgnostic.Config.Client client;
  private string[] current_time = null;

  private DigitalClockPrefs? prefs = null;

  public bool is_12_hour { get; set; }
  public bool show_date { get; set; default = true; }
  public bool date_before_time { get; set; }
  public string calendar_command { get; set; default = EVOLUTION_COMMAND; }
  public string datetime_command { get; set; default = TIME_ADMIN_COMMAND; }

  public DigitalClock (string canonical_name, string uid, int panel_id)
  {
    Object(canonical_name: canonical_name, uid: uid, panel_id: panel_id);

    this.display_name = Gettext._ ("Digital Clock");
    this.clicked.connect (this.on_clicked);
    this.context_menu_popup.connect (this.on_context_menu_popup);

    this.client = Awn.Config.get_default_for_applet (this);
    this.client.bind (GROUP_DEFAULT, "hour12", this, "is_12_hour",
                      true, BindMethod.FALLBACK);
    this.client.bind (GROUP_DEFAULT, "show_date", this, "show_date",
                      true, BindMethod.FALLBACK);
    this.client.bind (GROUP_DEFAULT, "dbt", this, "date_before_time",
                      true, BindMethod.FALLBACK);
    this.client.bind ("commands", "calendar", this, "calendar_command",
                      true, BindMethod.FALLBACK);
    this.client.bind ("commands", "adjust_datetime", this, "datetime_command",
                      true, BindMethod.FALLBACK);

    this.time_overlay = new OverlayText ();
    this.time_overlay.apply_effects = true;
    this.add_overlay(this.time_overlay);

    this.am_pm_overlay = new OverlayText();
    this.am_pm_overlay.apply_effects = true;
    this.add_overlay(this.am_pm_overlay);

    this.day_overlay = new OverlayText();
    this.day_overlay.apply_effects = true;
    this.add_overlay(this.day_overlay);

    this.date_overlay = new OverlayText();
    this.date_overlay.apply_effects = true;
    this.add_overlay(this.date_overlay);

    // we'll just use overlays, but AwnIcon doesn't like not having icon set,
    // so we'll give it 1x1 transparent pixbuf
    Gdk.Pixbuf pixbuf = new Gdk.Pixbuf (Gdk.Colorspace.RGB, true, 8, 1, 1);
    pixbuf.fill (0);
    this.set_icon_pixbuf (pixbuf);

    this.position_changed.connect (this.refresh_overlays);
    this.size_changed.connect (this.refresh_overlays);
    this.notify.connect (this.force_refresh);

    this.refresh_overlays ();
    this.update_clock ();

    Timeout.add_seconds (1, () => { this.update_clock (); return true; });

    this.init_calendar ();
  }

  private void
  init_calendar ()
  {
    this.dialog = new Awn.Dialog.for_widget (this);
    this.dialog.hide_on_unfocus = true;

    Gtk.Calendar calendar = new Gtk.Calendar ();
    calendar.set_display_options (Gtk.CalendarDisplayOptions.SHOW_HEADING |
                                  Gtk.CalendarDisplayOptions.SHOW_DAY_NAMES |
                                  Gtk.CalendarDisplayOptions.SHOW_WEEK_NUMBERS);
    calendar.day_selected_double_click.connect (this.start_external_calendar);

    this.dialog.set_title (_ ("Calendar"));
    this.dialog.add (calendar);
  }

  private void
  start_external_calendar (Gtk.Calendar calendar)
  {
    uint year, month, day;
    calendar.get_date (out year, out month, out day);

    month++;
    // damn, this one is pretty complicated to do in Vala
    string python_cmd =
      "python -c \"" +
      "import subprocess;" +
      "data = {'year': %u, 'month': %u, 'day': %u};".printf (year, month, day) +
      "command = '%s';".printf (this.calendar_command) +
      "subprocess.Popen(command % data, shell=True);" +
      "\"";

    Process.spawn_command_line_async (python_cmd);
  }

  private void
  force_refresh ()
  {
    this.current_time = null;
    this.refresh_overlays ();
    this.update_clock ();
  }

  private void
  refresh_overlays ()
  {
    Gtk.PositionType position = this.get_pos_type ();
    int size = this.get_size ();

    this.am_pm_overlay.active = false;
    this.day_overlay.active = this.show_date;
    this.date_overlay.active = this.show_date;

    if (position == Gtk.PositionType.TOP || position == Gtk.PositionType.BOTTOM)
    {
      // horizontal orientation
      if (this.date_before_time || !this.show_date)
      {
        // date on left of time / no date
        int width = this.show_date ? size * 11 / 5 : size * 3 / 2;

        this.get_icon ().set_custom_paint (width, size);

        this.time_overlay.font_sizing = this.show_date ? 22 : 25;
        this.time_overlay.gravity = this.show_date || this.is_12_hour ?
            Gdk.Gravity.NORTH_EAST : Gdk.Gravity.CENTER;

        this.day_overlay.font_sizing = 14;
        this.day_overlay.gravity = Gdk.Gravity.WEST;
        this.day_overlay.y_adj = 0;

        this.date_overlay.font_sizing = 14;
        this.date_overlay.gravity = Gdk.Gravity.SOUTH_WEST;

        if (this.is_12_hour)
        {
          this.am_pm_overlay.active = true;
          this.am_pm_overlay.font_sizing = 14;
          this.am_pm_overlay.gravity = Gdk.Gravity.SOUTH_EAST;
        }
      }
      else
      {
        // date below time
        int width = this.is_12_hour ? size * 17 / 10 : size * 6 / 5;

        this.get_icon ().set_custom_paint (width, size);

        this.time_overlay.font_sizing = this.is_12_hour ? 17 : 18;
        this.time_overlay.gravity = Gdk.Gravity.NORTH;

        this.day_overlay.font_sizing = 14;
        this.day_overlay.gravity = Gdk.Gravity.CENTER;
        this.day_overlay.y_adj = 0.05;

        this.date_overlay.font_sizing = 14;
        this.date_overlay.gravity = Gdk.Gravity.SOUTH;
      }
    }
    else
    {
      // side orientation, no support for "Date before time"
      int height;
      if (this.show_date)
      {
        height = size;
      }
      else
      {
        height = size / 2;
      }

      this.get_icon ().set_custom_paint (size, height);

      this.time_overlay.font_sizing = this.is_12_hour ? 10 : 15;
      if (!this.show_date) this.time_overlay.font_sizing *= 2;
      this.time_overlay.gravity = this.show_date ?
          Gdk.Gravity.NORTH : Gdk.Gravity.CENTER;

      this.day_overlay.font_sizing = 12;
      this.day_overlay.gravity = Gdk.Gravity.CENTER;
      this.day_overlay.y_adj = 0.05;

      this.date_overlay.font_sizing = 12;
      this.date_overlay.gravity = Gdk.Gravity.SOUTH;
    }
  }

  private void
  update_clock ()
  {
    if (!this.time_string_changed ()) return;

    if (!this.is_12_hour || this.am_pm_overlay.active)
    {
      this.time_overlay.text = current_time[0];
      this.am_pm_overlay.text = current_time[1];
    }
    else
    {
      this.time_overlay.text = "%s %s".printf (current_time[0],
                                               current_time[1]);
    }

    this.day_overlay.text = current_time[2];
    this.date_overlay.text = current_time[3];
  }

  private bool time_string_changed ()
  {
    string[] cur_time = this.get_time_string ();

    if (this.current_time == null)
    {
      this.current_time = cur_time;
      return true;
    }

    for (int i=0; i<this.current_time.length; i++)
    {
      if (this.current_time[i] != cur_time[i])
      {
        this.current_time = cur_time;
        return true;
      }
    }

    return false;
  }

  private static string format_current_time (string format)
  {
    time_t cur_time_t = time_t ();
    Time cur_time = Time.local (cur_time_t);

    return cur_time.format (format);
  }

  private string[] get_time_string ()
  {
    string[] full_date = new string[4];

    time_t cur_time_t = time_t ();
    Time cur_time = Time.local (cur_time_t);

    if (this.is_12_hour)
    {
      full_date[0] = cur_time.format ("%I:%M");
      full_date[1] = cur_time.format ("%p");
    }
    else
    {
      full_date[0] = cur_time.format ("%H:%M");
      full_date[1] = "";
    }

    full_date[2] = cur_time.format ("%a");
    full_date[3] = cur_time.format ("%b %d");

    return full_date;
  }

  private void
  on_clicked ()
  {
    Gtk.WidgetFlags flags = this.dialog.get_flags () & Gtk.WidgetFlags.VISIBLE;
    if (flags != Gtk.WidgetFlags.VISIBLE)
    {
      this.dialog.show_all ();
    }
    else
    {
      this.dialog.hide ();
    }
  }

  private void
  on_context_menu_popup (Gdk.EventButton event)
  {
    if (this._menu == null)
    {
      Gtk.ImageMenuItem image_item;
      Gtk.MenuItem menu_item;
      Gtk.Widget about_item;

      this._menu = this.create_default_menu () as Gtk.Menu;

      // "Copy Time" menu item
      image_item = new Gtk.ImageMenuItem.with_label (_ ("Copy Time"));
      image_item.set_image (new Gtk.Image.from_stock (Gtk.STOCK_COPY,
                                                      Gtk.IconSize.MENU));
      image_item.activate.connect ((w) =>
      {
        unowned Gtk.Clipboard cb = Gtk.Clipboard.get (Gdk.SELECTION_CLIPBOARD);
        if (this.is_12_hour)
        {
          cb.set_text (format_current_time ("%I:%M %p"), -1);
        }
        else
        {
          cb.set_text (format_current_time ("%H:%M"), -1);
        }
      });
      image_item.show ();
      this._menu.append (image_item);

      // "Copy Date" menu item
      image_item = new Gtk.ImageMenuItem.with_label (_ ("Copy Date"));
      image_item.set_image (new Gtk.Image.from_stock (Gtk.STOCK_COPY,
                                                      Gtk.IconSize.MENU));
      image_item.activate.connect ((w) =>
      {
        unowned Gtk.Clipboard cb = Gtk.Clipboard.get (Gdk.SELECTION_CLIPBOARD);
        cb.set_text (format_current_time ("%A, %B %d %Y"), -1);
      });
      image_item.show ();
      this._menu.append (image_item);

      // "Adjust Date & Time" menu item
      image_item = new Gtk.ImageMenuItem.with_label (_ ("Adjust Date & Time"));
      image_item.set_image (new Gtk.Image.from_stock (Gtk.STOCK_EDIT,
                                                      Gtk.IconSize.MENU));
      image_item.activate.connect ((w) =>
      {
        if (this.datetime_command.length > 0)
        {
          Process.spawn_command_line_async (this.datetime_command);
        }
      });
      image_item.show ();
      this._menu.append (image_item);

      // Separator
      menu_item = new Gtk.SeparatorMenuItem ();
      menu_item.show ();
      this._menu.append (menu_item);

      image_item = new Gtk.ImageMenuItem.from_stock (Gtk.STOCK_PREFERENCES, null);
      image_item.activate.connect ((w) =>
      {
        if (this.prefs == null)
        {
          this.prefs = new DigitalClockPrefs (this);

          this.prefs.get_dialog ().run ();
          this.prefs.get_dialog ().destroy ();

          this.prefs = null;
        }
        else
        {
          var dialog = this.prefs.get_dialog ();
          dialog.present_with_time (Gtk.get_current_event_time ());
        }
      });
      image_item.show ();
      this._menu.append (image_item);

      // Separator
      Gtk.MenuItem separator = new Gtk.SeparatorMenuItem ();
      separator.show ();
      this._menu.append (separator);

      about_item = this.create_about_item ("Copyright © 2010 Michal Hruby",
                                           AppletLicense.GPLV2, Build.VERSION,
                                           Gettext._ ("Displays digital clock."),
                                           null, null, "awn-applet-digital-clock",
                                           null, authors, null, null);
      about_item.show ();
      this._menu.append (about_item as Gtk.MenuItem);
    }
    this._menu.set_screen (null);
    this._menu.popup (null, null, null, event.button, event.time);
  }
}

public Applet
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  // i18n support
  Gettext.bindtextdomain (Build.GETTEXT_PACKAGE, Build.LOCALEDIR);
  Gettext.textdomain (Build.GETTEXT_PACKAGE);

  return new DigitalClock (canonical_name, uid, panel_id);
}

// vim:ft=vala:et:ts=2 sts=2 sw=2:ai:cindent
