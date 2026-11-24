#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
export QT_PLUGIN_PATH="$HOME/.local/lib/kool-qt6/plugins:$HOME/.local/lib/kool-qt5/plugins"
export QT_STYLE_OVERRIDE=kvantum
export QT_QPA_PLATFORMTHEME=qt5ct
export XCURSOR_THEME=Adwaita XCURSOR_SIZE=24
# Import exactly the appearance variables; retain the existing session environment.
dbus-update-activation-environment --systemd QT_PLUGIN_PATH QT_STYLE_OVERRIDE QT_QPA_PLATFORMTHEME XCURSOR_THEME XCURSOR_SIZE || true
hyprctl setcursor Adwaita 24 >/dev/null || true
pkill -x nwg-dock-hyprlan 2>/dev/null || true
# The running dock has a >15-character name, so inspect executable names explicitly.
for pid in $(pgrep -f '^nwg-dock-hyprland( |$)' || true); do kill "$pid" 2>/dev/null || true; done
"$HOME/.config/hypr/scripts/WallpaperDaemon.sh"
export WAYBAR_LOG="${XDG_RUNTIME_DIR:-/tmp}/kool-waybar.log"
"$HOME/.config/hypr/scripts/WaybarStartup.sh" --restart
swaync-client -R >/dev/null 2>&1 || true
swaync-client -rs >/dev/null 2>&1 || true
pkill -USR1 -x kitty 2>/dev/null || true
pkill -HUP -x xsettingsd 2>/dev/null || true
