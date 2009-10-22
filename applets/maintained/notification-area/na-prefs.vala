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

public const string APPLET_NAME = "notification-area";

public class NotificationAreaPrefs : GLib.Object
{
  private DesktopAgnostic.Config.Client client;

  private Awn.Applet applet;
  private Gtk.Dialog dialog;

  private weak Gtk.SpinButton icons_per_cell_spin;
  private weak Gtk.Range icon_size_range;
  private weak Gtk.SpinButton extra_offset_spin;

  private weak Gtk.RadioButton auto_backround_radio;
  private weak Gtk.RadioButton custom_background_radio;
  private weak UI.ColorButton background_color_button;
  private weak Gtk.RadioButton auto_border_radio;
  private weak Gtk.RadioButton custom_border_radio;
  private weak UI.ColorButton border_color_button;

  public int icons_per_cell
  {
    get
    {
      return this.icons_per_cell_spin.get_value_as_int ();
    }
    set
    {
      if (this.icons_per_cell_spin.get_value_as_int () != value)
        this.icons_per_cell_spin.set_value (value);
    }
  }

  public int icon_size
  {
    get
    {
      return (int)this.icon_size_range.get_value ();
    }
    set
    {
      if ((int)this.icon_size_range.get_value () != value)
        this.icon_size_range.set_value (value);
    }
  }

  public int extra_offset
  {
    get
    {
      return this.extra_offset_spin.get_value_as_int ();
    }
    set
    {
      if (this.extra_offset_spin.get_value_as_int () != value)
        this.extra_offset_spin.set_value (value);
    }
  }

  private DesktopAgnostic.Color? _background_color;
  public DesktopAgnostic.Color? background_color
  {
    get
    {
      return _background_color;
    }
    set
    {
      if (value == null) this.auto_backround_radio.set_active (true);
      else if (this._background_color == null ||
               this._background_color.to_string () != value.to_string ())
      {
        this.custom_background_radio.set_active (true);
        this.background_color_button.da_color = value;
      }
      this._background_color = value;
    }
  }

  private DesktopAgnostic.Color? _border_color;
  public DesktopAgnostic.Color? border_color
  {
    get
    {
      return _border_color;
    }
    set
    {
      if (value == null) this.auto_border_radio.set_active (true);
      else if (this._border_color == null ||
               this._border_color.to_string () != value.to_string ())
      {
        this.custom_border_radio.set_active (true);
        this.border_color_button.da_color = value;
      }
      this._border_color = value;
    }
  }

  public NotificationAreaPrefs(Awn.Applet applet)
  {
    this.applet = applet;

    string ui_path = GLib.Path.build_filename (Build.APPLETSDIR,
                                               APPLET_NAME,
                                               "na-prefs.ui");

    Gtk.Builder builder = new Gtk.Builder();
    builder.add_from_file (ui_path);

    this.init_components (builder);

    // bind our config keys
    this.client = Awn.Config.get_default_for_applet (applet);

    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "icons_per_cell",
                      this, "icons-per-cell",
                      false, DesktopAgnostic.Config.BindMethod.FALLBACK);
    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "icon_size",
                      this, "icon-size",
                      false, DesktopAgnostic.Config.BindMethod.FALLBACK);
    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "extra_offset",
                      this, "extra-offset",
                      false, DesktopAgnostic.Config.BindMethod.FALLBACK);

    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "background_color",
                      this, "background-color",
                      false, DesktopAgnostic.Config.BindMethod.FALLBACK);

    this.client.bind (DesktopAgnostic.Config.GROUP_DEFAULT, "border_color",
                      this, "border-color",
                      false, DesktopAgnostic.Config.BindMethod.FALLBACK);
  }

  ~NotificationAreaPrefs ()
  {
    this.client.unbind_all_for_object (this);
  }

  private void init_components (Gtk.Builder builder)
  {
    this.dialog = (Gtk.Dialog)builder.get_object ("dialog1");

    this.icons_per_cell_spin = (Gtk.SpinButton)builder.get_object ("iconRowsSpinbutton");
    this.icons_per_cell_spin.value_changed.connect ((obj) => {
      this.icons_per_cell = obj.get_value_as_int ();
    });

    this.extra_offset_spin = (Gtk.SpinButton)builder.get_object ("offsetSpinbutton");
    this.extra_offset_spin.value_changed.connect ((obj) => {
      this.extra_offset = obj.get_value_as_int ();
    });

    this.icon_size_range = (Gtk.Range)builder.get_object ("sizeScale");
    this.icon_size_range.value_changed.connect ((obj) => {
      this.icon_size = (int)obj.get_value ();
    });

    this.auto_backround_radio = (Gtk.RadioButton)builder.get_object ("autoBackgroundRadio");
    this.auto_backround_radio.toggled.connect ((obj) => {
      if (obj.get_active ()) this.background_color = null;
    });

    this.custom_background_radio = (Gtk.RadioButton)builder.get_object ("customBackgroundRadio");
    this.custom_background_radio.toggled.connect ((obj) => {
      if (obj.get_active ())
      {
        this.background_color = this.background_color_button.da_color;
      }
    });

    this.background_color_button = (UI.ColorButton)builder.get_object ("backgroundColorbutton");
    this.background_color_button.color_set.connect ((obj) => {
      UI.ColorButton button = obj as UI.ColorButton;
      this.background_color = button.da_color;
    });

    this.auto_border_radio = (Gtk.RadioButton)builder.get_object ("autoBorderRadio");
    this.auto_border_radio.toggled.connect ((obj) => {
      if (obj.get_active ()) this.border_color = null;
    });

    this.custom_border_radio = (Gtk.RadioButton)builder.get_object ("customBorderRadio");
    this.custom_border_radio.toggled.connect ((obj) => {
      if (obj.get_active ())
      {
        this.border_color = this.border_color_button.da_color;
      }
    });

    this.border_color_button = (UI.ColorButton)builder.get_object ("borderColorbutton");
    this.border_color_button.color_set.connect ((obj) => {
      UI.ColorButton button = obj as UI.ColorButton;
      this.border_color = button.da_color;
    });
  }

  public unowned Gtk.Dialog get_dialog ()
  {
    return this.dialog;
  }
}
