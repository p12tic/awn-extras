namespace Awn {
  namespace Keybinder {
    [CCode (cheader_filename = "keybinder.h", cprefix = "Awn")]
    public delegate void BindkeyHandler (string keystring);
    [CCode (cheader_filename = "keybinder.h", lower_case_cprefix = "awn_keybinder_")]
	  public static void init ();
    public static bool bind (string keystring, BindkeyHandler handler);
    public static bool unbind (string keystring, BindkeyHandler handler);
    public static bool is_modifier (uint keycode);
    public static uint32 get_current_event_time ();
  }
}
