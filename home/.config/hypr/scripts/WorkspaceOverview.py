#!/usr/bin/env python3
"""Event-driven overview of logical desktops, including every physical output."""
import argparse
import html
import json
import os
import pathlib
import re
import select
import socket
import subprocess
import sys
import time


APPS = [
    (r'kitty|konsole|foot|alacritty|ghostty|wezterm|terminal', '', 'Terminal'),
    (r'firefox|librewolf|floorp|waterfox', '', 'Firefox'),
    (r'chromium|chrome|brave|thorium|microsoft-edge', '', 'Browser'),
    (r'chatgpt|codex', '󰚩', 'ChatGPT'),
    (r'code|codium', '󰨞', 'Code'),
    (r'nvim|neovim', '', 'Neovim'),
    (r'thunar|nemo|dolphin|nautilus', '', 'Files'),
    (r'slack', '', 'Slack'),
    (r'discord|vesktop|webcord', '', 'Discord'),
    (r'telegram', '', 'Telegram'),
    (r'spotify', '', 'Spotify'),
    (r'mpv|vlc|celluloid', '', 'Video'),
    (r'thunderbird|betterbird', '', 'Mail'),
    (r'libreoffice', '', 'Office'),
    (r'steam', '', 'Steam'),
]
EVENTS = {
    'openwindow', 'closewindow', 'movewindow', 'movewindowv2',
    'workspace', 'workspacev2', 'createworkspace', 'createworkspacev2',
    'destroyworkspace', 'destroyworkspacev2', 'renameworkspace',
    'moveworkspace', 'moveworkspacev2', 'monitoradded', 'monitoraddedv2',
    'monitorremoved', 'monitorremovedv2', 'configreloaded', 'pin',
}


def group_number(workspace):
    if workspace.get('special') or workspace.get('type') == 'special':
        return None
    name = str(workspace.get('name', ''))
    match = re.fullmatch(r'(\d+)', name) or re.match(r'^hyprnerd-(\d+)-.+$', name)
    return int(match[1]) if match and int(match[1]) > 0 else None


def app_identity(window):
    name = window.get('class') or window.get('initialClass') or 'Application'
    for pattern, icon, fallback in APPS:
        if re.search(pattern, name, re.IGNORECASE):
            # Keep distinct browsers/terminals identifiable in the detailed list.
            label = name.rsplit('.', 1)[-1] if fallback in ('Terminal', 'Browser', 'Firefox') else fallback
            return name.casefold(), icon, label[:40]
    return name.casefold(), '', name.rsplit('.', 1)[-1][:40]


def collect(workspaces, windows, current):
    groups = {current: {}}
    for workspace in workspaces:
        number = group_number(workspace)
        if number:
            groups.setdefault(number, {})
    for window in windows:
        number = group_number(window.get('workspace', {}))
        # Inactive tab-group members still count; scratchpads and unmapped windows do not.
        if not number or window.get('mapped') is False:
            continue
        key, icon, name = app_identity(window)
        apps = groups.setdefault(number, {})
        app = apps.setdefault(key, {'icon': icon, 'name': name, 'count': 0})
        app['count'] += 1
    return [{'id': number, 'apps': sorted(apps.values(), key=lambda app: app['name'].casefold())}
            for number, apps in sorted(groups.items())]


def query(name):
    return json.loads(subprocess.check_output(['hyprctl', '-j', name], text=True, timeout=3))


def snapshot():
    monitors = query('monitors')
    active = next((m for m in monitors if m.get('focused')), {})
    current = group_number(active.get('activeWorkspace', {})) or 1
    groups = collect(query('workspaces'), query('clients'), current)
    output = os.environ.get('WAYBAR_OUTPUT_NAME')
    monitor = next((m for m in monitors if m['name'] == output), active)
    width = monitor.get('width', 1920) / (monitor.get('scale') or 1)
    if monitor.get('transform', 0) % 2:
        width = monitor.get('height', 1080) / (monitor.get('scale') or 1)
    return groups, current, max(3, min(7, int(width / 260)))


def app_summary(apps, icons=False, limit=None):
    shown = apps if limit is None else apps[:limit]
    values = []
    for app in shown:
        text = app['icon'] if icons else app['name']
        if app['count'] > 1:
            text += str(app['count']).translate(str.maketrans('0123456789', '⁰¹²³⁴⁵⁶⁷⁸⁹')) if icons else f" ×{app['count']}"
        values.append(text)
    if len(shown) < len(apps):
        values.append(f'+{len(apps) - len(shown)}')
    return ('  ' if icons else ' · ').join(values)


def render(groups, current, max_groups=7):
    selected = next((i for i, group in enumerate(groups) if group['id'] == current), 0)
    start = max(0, min(selected - max_groups // 2, len(groups) - max_groups))
    visible = groups[start:start + max_groups]
    segments = []
    if start:
        segments.append(f'<span foreground="#73878a">…{start}</span>')
    for group in visible:
        number, apps = group['id'], group['apps']
        content = html.escape(app_summary(apps, icons=True, limit=3)) or '·'
        if number == current:
            segments.append(f'<span background="#72c8c8" foreground="#191919" weight="bold"> {number} </span>'
                            f' <span foreground="#72c8c8">{content}</span>')
        else:
            color = '#d4dedf' if apps else '#73878a'
            segments.append(f'<span foreground="{color}"><b>{number}</b>  {content}</span>')
    remaining = len(groups) - start - len(visible)
    if remaining:
        segments.append(f'<span foreground="#73878a">{remaining}…</span>')
    tooltip = ['<b>ワークスペース · 全モニター</b>']
    for group in groups:
        marker = '●' if group['id'] == current else '○'
        summary = html.escape(app_summary(group['apps'])) or '空'
        tooltip.append(f"{marker}  <b>{group['id']}</b>   {summary}")
    tooltip.extend(['', '左クリック: アプリ名から選択 · 右クリック: ウィンドウを移動',
                    'スクロール: 前 / 次 · ＋: 追加'])
    return {'text': '  <span foreground="#3c5558">│</span>  '.join(segments),
            'tooltip': '\n'.join(tooltip), 'class': 'overview'}


def menu(move=False):
    groups, current, _ = snapshot()
    labels = [f"{'●' if group['id'] == current else '○'}  {group['id']}   "
              + (app_summary(group['apps']) or '空のワークスペース') for group in groups]
    if not move:
        labels.append('＋  新しいワークスペース')
    result = subprocess.run(
        ['rofi', '-dmenu', '-i', '-no-custom', '-format', 'i', '-selected-row',
         str(next((i for i, g in enumerate(groups) if g['id'] == current), 0)),
         '-p', '移動先' if move else 'ワークスペース',
         '-theme-str', 'window { width: 620px; } listview { lines: 8; columns: 1; }'],
        input='\n'.join(label.replace('\n', ' ').replace('\r', ' ').replace('\x00', '') for label in labels),
        text=True, capture_output=True)
    if result.returncode or not result.stdout.strip().isdigit():
        return
    index = int(result.stdout.strip())
    if index == len(groups) and not move:
        code = 'new_workspace()'
    elif 0 <= index < len(groups):
        number = groups[index]['id']
        code = f'move({number},true)' if move else f'switch({number})'
    else:
        return
    subprocess.run(['hyprctl', 'eval', 'HYPRNERD_DESKTOP.' + code], check=True, stdout=subprocess.DEVNULL)


def stream():
    runtime = pathlib.Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
    signature = os.environ['HYPRLAND_INSTANCE_SIGNATURE']
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(runtime / 'hypr' / signature / '.socket2.sock'))
        pending, previous, deadline = b'', None, time.monotonic()
        while True:
            timeout = None if deadline is None else max(0, deadline - time.monotonic())
            ready, _, _ = select.select([connection], [], [], timeout)
            if ready:
                data = connection.recv(65536)
                if not data:
                    return
                pending += data
                while b'\n' in pending:
                    line, pending = pending.split(b'\n', 1)
                    event = line.partition(b'>>')[0].decode('utf-8', errors='replace')
                    if event in EVENTS and deadline is None:
                        # Coalesce the per-output switch events; never query on keystrokes/title changes.
                        deadline = time.monotonic() + .08
            if deadline is not None and time.monotonic() >= deadline:
                value = json.dumps(render(*snapshot()), ensure_ascii=False)
                if value != previous:
                    print(value, flush=True)
                    previous = value
                deadline = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.once:
        print(json.dumps(render(*snapshot()), ensure_ascii=False))
    else:
        stream()


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        pass
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print('Workspace overview: ' + str(error), file=sys.stderr)
