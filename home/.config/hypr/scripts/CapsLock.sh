#!/bin/sh
# Read-only LEDs expose caps-lock without membership in the input group.
state=0
for f in /sys/class/leds/*::capslock/brightness; do
  [ -r "$f" ] || continue
  [ "$(cat "$f")" = 0 ] || state=1
done
if [ "$state" = 1 ]; then icon=''; else icon=''; fi
printf '{"text":"󰪛 %s","tooltip":"Caps Lock"}\n' "$icon"
