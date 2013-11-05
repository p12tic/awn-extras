namespace Awn {
  namespace Keybinder {
    namespace Egg {
      [CCode (cheader_filename = "eggaccelerators.h", cprefix = "EGG_VIRTUAL_", cname = "EggVirtualModifierType")]
      [Flags]
      public enum VirtualModifierType
      {
        SHIFT_MASK,
        LOCK_MASK,
        CONTROL_MASK,
        ALT_MASK,
        MOD2_MASK,
        MOD3_MASK,
        MOD4_MASK,
        MOD5_MASK,
        META_MASK,
        SUPER_MASK,
        HYPER_MASK,
        MODE_SWITCH_MASK,
        NUM_LOCK_MASK,
        SCROLL_LOCK_MASK,

        RELEASE_MASK
      }
      [CCode (cheader_filename = "eggaccelerators.h", cname = "egg_accelerator_parse_virtual")]
      public static bool accelerator_parse_virtual (string accelerator, out uint key, out VirtualModifierType mods);
      [CCode (cheader_filename = "eggaccelerators.h", cname = "egg_virtual_accelerator_name")]
      public static string virtual_accelerator_name (uint key, VirtualModifierType mods);
      [CCode (cheader_filename = "eggaccelerators.h", cname = "egg_keymap_virtualize_modifiers")]
      public static void keymap_virtualize_modifiers (Gdk.Keymap keymap, Gdk.ModifierType mods, out VirtualModifierType virtual_mods);
      [CCode (cheader_filename = "eggaccelerators.h", cname = "egg_keymap_resolve_virtual_modifiers")]
      public static void keymap_resolve_virtual_modifiers (Gdk.Keymap keymap, VirtualModifierType virtual_mods, out Gdk.ModifierType mods);
    }

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
