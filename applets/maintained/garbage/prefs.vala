/*
 * Preferences dialog for the Garbage applet.
 *
 * Copyright (C) 2009 Mark Lee <avant-wn@lazymalevolence.com>
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

using Gtk;

public class GarbagePrefs : Dialog
{
  private GarbageApplet _applet;

  public GarbagePrefs (GarbageApplet applet)
  {
    GLib.Object (type: Gtk.WindowType.TOPLEVEL);
    this.title = Gettext._ ("%s Preferences").printf (applet.display_name);
    this.icon_name = "gtk-preferences";
    this._applet = applet;

    this.create_ui ();
  }

  private void
  create_ui ()
  {
    CheckButton empty_button, count_button;

    this.vbox.spacing = 5;

    empty_button =
      new CheckButton.with_mnemonic (Gettext._ ("Confirm when emptying the trash"));
    empty_button.active = this._applet.confirm_empty;
    empty_button.toggled.connect (this.on_empty_toggled);
    this.vbox.add (empty_button);
    count_button =
      new CheckButton.with_mnemonic (Gettext._ ("Show the item count on the icon"));
    count_button.active = this._applet.show_count;
    count_button.toggled.connect (this.on_count_toggled);
    this.vbox.add (count_button);

    this.add_button (STOCK_CLOSE, ResponseType.CLOSE);
    this.response.connect (this.on_response);
  }

  private void
  on_empty_toggled (ToggleButton button)
  {
    this._applet.confirm_empty = button.active;
  }

  private void
  on_count_toggled (ToggleButton button)
  {
    this._applet.show_count = button.active;
  }

  private void
  on_response (int response_id)
  {
    this.hide ();
  }
}

// vim: set ft=vala et ts=2 sts=2 sw=2 ai :
