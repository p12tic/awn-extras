/*
 * A simple applet written in Vala that shows a stock icon.
 *
 * Copyright (C) 2007 Mark Lee <avant-wn@lazymalevolence.com>
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

using GLib;
using Gdk;
using Gtk;
using Awn;

public Applet awn_applet_factory_initp (string uid, int orient, int height) {
	AppletSimple applet;
	IconTheme theme;
	Pixbuf icon = null;
	applet = new AppletSimple (uid, orient, height);
	applet.set_size_request (height, -1);
	theme = IconTheme.get_default ();
	try {
		icon = theme.load_icon ("gtk-yes", (int)(applet.get_height () - 2),
		                        IconLookupFlags.USE_BUILTIN);
	} catch (Error e) {
		warning ("Could not load the icon. Something's probably wrong with Gtk+.");
	}
	applet.set_temp_icon (icon);
	applet.show_all ();
	return applet;
}

/* vim: set ft=cs noet ts=8 sts=8 sw=8 : */
