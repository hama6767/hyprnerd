#!/usr/bin/env bash
# GPL-3.0-or-later. Keep one auto-hidden dock and rebuild hotspots on monitor changes.
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
exec python3 "${XDG_CONFIG_HOME:-$HOME/.config}/hypr/scripts/DockManager.py" "${1:-toggle}"
