/*
 * Show/hide desktop applet written in Vala.
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

using Awn;

class ShowDesktop : AppletSimple
{
  private Gtk.Menu _menu;

  public ShowDesktop (string canonical_name, string uid, int panel_id)
  {
    unowned Wnck.Screen screen;

    this.canonical_name = canonical_name;
    this.uid = uid;
    this.panel_id = panel_id;

    Awn.Tooltip tooltip = (this.get_icon () as Awn.Icon).get_tooltip ();
    tooltip.set ("toggle-on-click", false);

    this.display_name = Gettext._ ("Show Desktop");
    this.clicked.connect (this.on_clicked);
    this.context_menu_popup.connect (this.on_context_menu_popup);

    screen = Wnck.Screen.get_default ();
    screen.showing_desktop_changed.connect (this.on_show_desktop_changed);
    this.on_show_desktop_changed (screen);
  }

  private void
  on_clicked ()
  {
    unowned Wnck.Screen screen;

    screen = Wnck.Screen.get_default ();
    screen.toggle_showing_desktop (!screen.get_showing_desktop ());
  }

  private void
  on_context_menu_popup (Gdk.EventButton event)
  {
    if (this._menu == null)
    {
      Gtk.Widget about_item;

      string[] authors = new string[] { "Mark Lee <avant-wn@lazymalevolence.com>" };

      this._menu = this.create_default_menu () as Gtk.Menu;
      about_item = this.create_about_item ("Copyright © 2009 Mark Lee",
                                           AppletLicense.GPLV2, Build.VERSION,
                                           "An applet to hide your windows and show your desktop", null, null, "user-desktop",
                                           null, authors, null, null);
      about_item.show ();
      this._menu.append (about_item as Gtk.MenuItem);
    }
    this._menu.set_screen (null);
    this._menu.popup (null, null, null, event.button, event.time);
  }

  private void
  on_show_desktop_changed (Wnck.Screen screen)
  {
    if (screen.get_showing_desktop ())
    {
      this.set_tooltip_text (Gettext._ ("Show hidden windows"));
      this.set_icon_name ("view-restore");
    }
    else
    {
      this.set_tooltip_text (Gettext._ ("Hide windows and show desktop"));
      this.set_icon_name ("user-desktop");
    }
  }
}

public Applet
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  Intl.setlocale (LocaleCategory.ALL, "");
  Gettext.bindtextdomain (Build.GETTEXT_PACKAGE, Build.LOCALEDIR);
  Gettext.textdomain (Build.GETTEXT_PACKAGE);
  return new ShowDesktop (canonical_name, uid, panel_id);
}

// vim:ft=vala:et:ts=2 sts=2 sw=2:ai:cindent
