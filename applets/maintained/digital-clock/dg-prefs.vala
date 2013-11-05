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

using Gtk;
using DesktopAgnostic;

public const string APPLET_NAME = "digital-clock";

public class DigitalClockPrefs : GLib.Object
{
  private DesktopAgnostic.Config.Client client;

  private Awn.Applet applet;
  private ulong pos_changed_id;
  private Gtk.Dialog dialog;

  private weak Gtk.Widget hour_12_radio;
  private weak Gtk.Widget hour_24_radio;
  private weak Gtk.Widget show_date_check;
  private weak Gtk.Widget dbt_check;
  private weak Gtk.Widget calendar_entry;
  private weak Gtk.Widget time_admin_entry;

  public bool is_12_hour
  {
    get
    {
      return (this.hour_12_radio as Gtk.ToggleButton).active;
    }
    set
    {
      if (value) (this.hour_12_radio as Gtk.ToggleButton).active = true;
      else (this.hour_24_radio as Gtk.ToggleButton).active = true;
    }
  }
  public bool date_before_time
  {
    get
    {
      return !(this.dbt_check as Gtk.ToggleButton).active;
    }
    set
    {
      (this.dbt_check as Gtk.ToggleButton).active = !value;
    }
  }

  public DigitalClockPrefs(Awn.Applet applet)
  {
    this.applet = applet;

    string ui_path = GLib.Path.build_filename (Build.APPLETSDIR,
                                               APPLET_NAME,
                                               "dg-prefs.ui");

    Gtk.Builder builder = new Gtk.Builder();
    builder.add_from_file (ui_path);

    this.init_components (builder);

    this.pos_changed_id =
      this.applet.position_changed.connect (this.on_applet_position_changed);
    this.on_applet_position_changed (applet.get_pos_type ());

    // bind our config keys
    this.client = Awn.Config.get_default_for_applet (applet);
    this.client.bind (Config.GROUP_DEFAULT, "hour12",
                      this, "is_12_hour", false,
                      Config.BindMethod.FALLBACK);

    this.client.bind (Config.GROUP_DEFAULT, "show_date",
                      this.show_date_check, "active", false,
                      Config.BindMethod.FALLBACK);

    this.client.bind (Config.GROUP_DEFAULT, "dbt",
                      this, "date-before-time", false,
                      Config.BindMethod.FALLBACK);

    this.client.bind ("commands", "calendar",
                      this.calendar_entry, "text", false,
                      Config.BindMethod.FALLBACK);

    this.client.bind ("commands", "adjust_datetime",
                      this.time_admin_entry, "text", false,
                      Config.BindMethod.FALLBACK);
  }

  ~DigitalClockPrefs ()
  {
    SignalHandler.disconnect (this.applet, this.pos_changed_id);
    this.client.unbind_all_for_object (this);
  }

  private void on_applet_position_changed (Gtk.PositionType new_pos)
  {
    if (new_pos == Gtk.PositionType.TOP || new_pos == Gtk.PositionType.BOTTOM)
    {
      this.dbt_check.set_sensitive (true);
    }
    else
    {
      this.dbt_check.set_sensitive (false);
    }
  }

  private void init_components (Gtk.Builder builder)
  {
    Gtk.ToggleButton toggle;

    this.dialog = builder.get_object ("dialog1") as Gtk.Dialog;

    this.hour_12_radio = builder.get_object ("12_hour_radio") as Gtk.Widget;
    toggle = this.hour_12_radio as Gtk.ToggleButton;
    toggle.toggled.connect ((w) =>
    {
      if (w.get_active ()) this.is_12_hour = true;
    });

    this.hour_24_radio = builder.get_object ("24_hour_radio") as Gtk.Widget;
    toggle = this.hour_24_radio as Gtk.ToggleButton;
    toggle.toggled.connect ((w) =>
    {
      if (w.get_active ()) this.is_12_hour = false;
    });

    this.dbt_check = builder.get_object ("date_below_check") as Gtk.Widget;
    toggle = this.dbt_check as Gtk.ToggleButton;
    toggle.toggled.connect ((w) =>
    {
      this.date_before_time = !w.get_active ();
    });

    this.show_date_check = builder.get_object ("show_date_check") as Gtk.Widget;
    this.calendar_entry = builder.get_object ("calendar_entry") as Gtk.Widget;
    this.time_admin_entry = builder.get_object ("time_admin_entry") as Gtk.Widget;
  }

  public unowned Gtk.Dialog get_dialog ()
  {
    return this.dialog;
  }
}
