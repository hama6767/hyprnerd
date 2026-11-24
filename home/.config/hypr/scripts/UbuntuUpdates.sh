#!/bin/sh
# Inspect the existing APT cache; this never refreshes repositories or installs.
LC_ALL=C apt list --upgradable 2>/dev/null | awk 'NR>1 {n++} END {print n+0}'
