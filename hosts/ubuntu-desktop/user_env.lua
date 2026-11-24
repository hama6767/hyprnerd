-- Host settings: NVIDIA RTX 5060 Ti, existing Estonian/US input layouts.
hl.env("LIBVA_DRIVER_NAME", "nvidia")
hl.env("__GLX_VENDOR_LIBRARY_NAME", "nvidia")
-- Keep the user-installed ML4W utilities on the session PATH.
hl.env("PATH", os.getenv("HOME") .. "/.local/bin:" .. os.getenv("PATH"))

-- NoMachine needs libnxegl inside Hyprland, not inside desktop applications.
-- Removing it from the environment leaves the compositor's loaded library intact.
do
    local preload = os.getenv("LD_PRELOAD") or ""
    if preload:find("/usr/NX/lib/libnxegl.so", 1, true) then
        local keep = {}
        for library in preload:gmatch("[^: ]+") do
            if library ~= "/usr/NX/lib/libnxegl.so" then
                table.insert(keep, library)
            end
        end
        hl.env("LD_PRELOAD", table.concat(keep, ":"))
    end
end


hl.env("WEATHER_UNITS", "metric")
hl.env("EDITOR", "nvim")
hl.env("VISUAL", "nvim")

local home = os.getenv("HOME") or ""
hl.env("QT_STYLE_OVERRIDE", "kvantum")
hl.env("QT_PLUGIN_PATH", home .. "/.local/lib/kool-qt6/plugins:" .. home .. "/.local/lib/kool-qt5/plugins")
hl.env("XCURSOR_THEME", "Adwaita")
hl.env("HYPRCURSOR_THEME", "Adwaita")
hl.env("XCURSOR_SIZE", "24")
hl.env("HYPRCURSOR_SIZE", "24")

hl.env("NVD_BACKEND", "direct")

-- qt6ct also advertises the qt5ct alias; this works for both Qt generations.
hl.env("QT_QPA_PLATFORMTHEME", "qt5ct")
