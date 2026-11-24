-- Generic appearance environment; host profile may replace this file.
local home = os.getenv("HOME") or ""
hl.env("QT_STYLE_OVERRIDE", "kvantum")
hl.env("QT_PLUGIN_PATH", home .. "/.local/lib/kool-qt6/plugins:" .. home .. "/.local/lib/kool-qt5/plugins")
hl.env("XCURSOR_THEME", "Adwaita")
hl.env("HYPRCURSOR_THEME", "Adwaita")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

-- qt6ct also advertises the qt5ct alias; this works for both Qt generations.
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
