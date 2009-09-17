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
using Gdk;
using Cairo;
using Awn;
using Wnck;

using Build;

public class ShowDesktopApplet : AppletSimple
{
  private Menu menu;
  private unowned Wnck.Screen wnck_screen;
  private string _show_str;
  private string _hide_str;

  public ShowDesktopApplet (string canonical_name, string uid, int panel_id)
  {
    this.canonical_name = canonical_name;
    this.uid = uid;
    this.panel_id = panel_id;
    this.display_name = "Show Desktop";

    this.set_icon_name ("desktop");
    this._show_str = Gettext._ ("Show hidden windows");
    this._hide_str = Gettext._ ("Hide windows and show desktop");

    Awn.Tooltip tooltip = (this.get_icon () as Awn.Icon).get_tooltip ();
    tooltip.set ("toggle-on-click", false);

    this.clicked.connect (this.on_clicked);
    this.context_menu_popup.connect (this.on_context_menu_popup);
    
    this.wnck_screen = Wnck.Screen.get_default ();
    Signal.connect_swapped (this.wnck_screen, "showing-desktop-changed",
                            (GLib.Callback)this.on_showing_changed, this);

    this.on_showing_changed (this.wnck_screen);
  }

  private void on_clicked ()
  {
    bool showing = this.wnck_screen.get_showing_desktop ();
    this.wnck_screen.toggle_showing_desktop (! showing);
  }

  private void on_context_menu_popup (EventButton evt)
  {
    if (this.menu == null)
    {
      this.menu = this.create_default_menu () as Menu;
      Widget about_item;

      about_item = this.create_about_item_simple ("Copyright (C) 2009 Michal Hruby <michal.mhr@gmail.com>",
                                                  AppletLicense.GPLV2,
                                                  Build.VERSION);
      about_item.show ();
      this.menu.append (about_item as MenuItem);
    }

    this.menu.popup (null, null, null, evt.button, evt.time);
  }

  private void on_showing_changed (Wnck.Screen screen)
  {
    bool showing = screen.get_showing_desktop ();

    (this.get_icon () as Awn.Icon).set_is_active (showing);
    this.set_tooltip_text (showing ? this._show_str : this._hide_str);
  }
}

public Applet?
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  Intl.setlocale (LocaleCategory.ALL, "");
  Gettext.bindtextdomain (Build.GETTEXT_PACKAGE, Build.LOCALEDIR);
  Gettext.textdomain (Build.GETTEXT_PACKAGE);
  return new ShowDesktopApplet (canonical_name, uid, panel_id);
}

