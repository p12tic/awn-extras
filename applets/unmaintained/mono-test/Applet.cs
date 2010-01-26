/*
 * A simple applet written in C# that shows a stock icon.
 *
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
 */

using Gtk;
using Mono.GetOptions;
using Awn;

class AwnGetOptions : Options
{
	[Option("Panel ID", 'i', "panel-id")]
	public int panel_id = 1;

	[Option("UID", 'u', "uid")]
	public string uid = "";

	[Option("Window XID", 'w', "window")]
	public uint window_xid = 0;
}

public class MonoTest
{
	public static void Main(string [] args)
	{
		Application.Init ();

		AwnGetOptions options = new AwnGetOptions ();
		options.ProcessArgs (args);

		AppletSimple simple = new AppletSimple ("mono-test", options.uid, options.panel_id);
		simple.IconName = "gtk-yes";
		simple.TooltipText = "Test Mono applet";

		simple.Construct (options.window_xid);

		Application.Run ();
	}
}

