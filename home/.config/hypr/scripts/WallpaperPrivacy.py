#!/usr/bin/env python3
"""Temporarily clear wallpaper on every output without changing Wallust or theme files."""
import fcntl
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys


def parse_query(text):
    outputs = {}
    for line in text.splitlines():
        match = re.search(r'([^\s:]+): \d+x\d+,.*currently displaying: (image|color): (.*)$', line)
        if not match:
            continue
        output, kind, value = match.groups()
        if kind == 'color':
            if re.fullmatch(r'[0-9a-fA-F]{6,8}', value):
                value = value[:6]
            else:
                rgb = re.search(r'r:\s*(\d+).*g:\s*(\d+).*b:\s*(\d+)', value)
                if not rgb:
                    raise ValueError('Unknown wallpaper color: ' + value)
                value = ''.join(f'{int(n):02x}' for n in rgb.groups())
        outputs[output] = {'kind': kind, 'value': value}
    if not outputs:
        raise ValueError('No wallpaper outputs reported')
    return outputs


def toggle(root, binary, run=subprocess.run):
    root.mkdir(parents=True, exist_ok=True)
    state = root / 'wallpaper-privacy.json'
    with (root / 'wallpaper-privacy.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        live = parse_query(run([binary, 'query'], check=True, text=True, capture_output=True).stdout)
        if state.exists():
            saved = json.loads(state.read_text())
            fallback = next(iter(saved.values()))
            for output in live:
                item = saved.get(output, fallback)
                if item['kind'] == 'image':
                    run([binary, 'img', '--outputs', output, '--transition-type', 'none', item['value']], check=True)
                else:
                    run([binary, 'clear', '--outputs', output, item['value']], check=True)
            state.unlink()
            return False
        temporary = state.with_suffix('.tmp')
        temporary.write_text(json.dumps(live))
        temporary.replace(state)
        # Save before clearing, so a failed daemon command can still be undone.
        run([binary, 'clear', '000000'], check=True)
        return True


def main():
    binary = shutil.which('awww') or shutil.which('swww')
    if not binary:
        raise RuntimeError('awww / swww is not installed')
    runtime = pathlib.Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
    # A toggle is temporary to this compositor session, never a saved theme.
    session = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', 'session')
    toggle(runtime / 'hyprnerd' / session, binary)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        subprocess.run(['notify-send', '-u', 'normal', 'Wallpaper toggle', str(error)], check=False)
        print('Wallpaper toggle: ' + str(error), file=sys.stderr)
        sys.exit(1)
