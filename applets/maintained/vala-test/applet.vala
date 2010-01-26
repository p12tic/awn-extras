/*
 * A simple applet written in Vala that shows a stock icon.
 *
 * Copyright (C) 2007, 2008, 2009 Mark Lee <avant-wn@lazymalevolence.com>
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

public Applet
awn_applet_factory_initp (string canonical_name, string uid, int panel_id)
{
  AppletSimple applet;

  applet = new AppletSimple (canonical_name, uid, panel_id);
  applet.set_icon_name ("gtk-yes");
  return applet;
}

// vim:et:ai:cindent:ts=2 sts=2 sw=2:
