[CCode (cprefix = "Awn", lower_case_cprefix = "awn_")]
namespace Awn {
	[CCode (cheader_filename = "awn-desktop-lookup.h")]
	public class DesktopLookup : GLib.Object {
		[CCode (cname = "awn_desktop_lookup_new", has_construct_function = false)]
		public DesktopLookup ();
		[CCode (cname = "awn_desktop_lookup_search_cache")]
		public unowned string search_cache (string class_name, string res_name, string cmd, string id);
		[CCode (cname = "awn_desktop_lookup_search_for_desktop")]
		public static unowned string search_for_desktop (ulong xid);
		[CCode (cname = "awn_desktop_lookup_special_case")]
		public static unowned string special_case (string cmd, string res_name, string class_name, string wm_icon_name, string wm_name, string window_role);
	}
	[CCode (cheader_filename = "awn-desktop-lookup-cached.h")]
	public class DesktopLookupCached : Awn.DesktopLookup {
		[CCode (cname = "awn_desktop_lookup_cached_new", has_construct_function = false)]
		public DesktopLookupCached ();
		[CCode (cname = "awn_desktop_lookup_search_by_wnck_window")]
		public unowned string search_by_wnck_window (Wnck.Window win);
	}
}
