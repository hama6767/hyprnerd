#!/usr/bin/env python3
"""Per-output Waybar selection indicator, updated by Hyprland IPC events."""
import html
import json
import os
import pathlib
import socket
import subprocess
import sys


def read_monitors():
    return json.loads(subprocess.check_output(['hyprctl', '-j', 'monitors'], text=True, timeout=3))


def monitor_label(index):
    label = ''
    while index:
        index, remainder = divmod(index - 1, 26)
        label = chr(ord('A') + remainder) + label
    return label


class Indicator:
    def __init__(self, output, reader=read_monitors):
        self.output = output
        self.reader = reader
        self.monitors = []
        self.active = ''

    def refresh(self):
        self.monitors = sorted(
            (m for m in self.reader() if not m.get('disabled') and m.get('mirrorOf') in (None, '', 'none', -1)),
            key=lambda m: (m['x'], m['y'], m['name']),
        )
        self.active = next((m['name'] for m in self.monitors if m.get('focused')), '')

    def event(self, line):
        event, separator, payload = line.strip().partition('>>')
        if not separator:
            return False
        if event in ('focusedmon', 'focusedmonv2'):
            self.active = payload.split(',', 1)[0]
            if not any(m['name'] == self.active for m in self.monitors):
                self.refresh()
            return True
        if event in ('monitoradded', 'monitoraddedv2', 'monitorremoved', 'monitorremovedv2', 'configreloaded'):
            self.refresh()
            return True
        return False

    def render(self):
        name = self.output or self.active
        index = next((i for i, m in enumerate(self.monitors, 1) if m['name'] == name), None)
        if index is None:
            return {'text': '', 'class': 'inactive', 'tooltip': ''}
        selected = name == self.active
        label = monitor_label(index)
        return {
            'text': label,
            'class': 'active' if selected else 'inactive',
            'tooltip': html.escape(
                f"モニター {label}: {name} — {'選択中' if selected else '未選択'}\n"
                'Super+矢印: ウィンドウ／モニター選択\n'
                'Super+Shift+矢印: タイル移動\nSuper+Enter: 選択先にターミナルを追加'
            ),
        }


def main():
    indicator = Indicator(os.environ.get('WAYBAR_OUTPUT_NAME', ''))
    runtime = pathlib.Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid())))
    signature = os.environ['HYPRLAND_INSTANCE_SIGNATURE']
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.connect(str(runtime / 'hypr' / signature / '.socket2.sock'))
        indicator.refresh()
        previous = None

        def publish():
            nonlocal previous
            value = json.dumps(indicator.render(), ensure_ascii=False)
            if value != previous:
                print(value, flush=True)
                previous = value

        publish()
        with connection.makefile(encoding='utf-8', errors='replace') as events:
            for line in events:
                if indicator.event(line):
                    publish()


if __name__ == '__main__':
    try:
        main()
    except BrokenPipeError:
        pass
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as error:
        print('Monitor indicator: ' + str(error), file=sys.stderr)
