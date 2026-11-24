#!/usr/bin/env bash
# Start one Fcitx5 instance; compositor layouts remain authoritative.
set -eu
command -v fcitx5 >/dev/null 2>&1 || exit 0
pgrep -u "$(id -u)" -x fcitx5 >/dev/null || fcitx5 -d
