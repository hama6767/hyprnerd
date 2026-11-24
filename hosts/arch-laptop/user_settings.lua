-- Intel laptop: retain the reference machine's Estonian keyboard and touchpad.
hl.config({ input = {
  kb_layout = "ee", kb_variant = "", kb_options = "",
  repeat_rate = 50, repeat_delay = 300, sensitivity = 0,
  numlock_by_default = true, left_handed = false, follow_mouse = 1,
  touchpad = { disable_while_typing = true, natural_scroll = false,
    clickfinger_behavior = false, middle_button_emulation = true,
    tap_to_click = true, drag_lock = false },
} })
