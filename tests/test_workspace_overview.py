import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch

path = pathlib.Path(__file__).resolve().parents[1] / 'home/.config/hypr/scripts/WorkspaceOverview.py'
spec = importlib.util.spec_from_file_location('workspace_overview', path)
module = importlib.util.module_from_spec(spec)
bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
finally:
    sys.dont_write_bytecode = bytecode_setting


def window(workspace, app='kitty', **kwargs):
    return {'workspace': {'name': workspace}, 'class': app, **kwargs}


class WorkspaceOverviewTests(unittest.TestCase):
    def test_aggregates_companion_outputs_without_duplicate_desktops(self):
        groups = module.collect([{'name': '1'}, {'name': 'hyprnerd-1-DP-2'}, {'name': '20'}], [
            window('1'), window('hyprnerd-1-DP-2'), window('hyprnerd-1-DP-3', 'firefox'),
            window('special:scratchpad'), window('1', mapped=False),
            window('hyprnerd-20-DP-2', 'slack'), window('0'),
        ], 2)
        self.assertEqual([g['id'] for g in groups], [1, 2, 20])
        self.assertEqual([(a['name'], a['count']) for a in groups[0]['apps']], [('firefox', 1), ('kitty', 2)])
        self.assertEqual(groups[1]['apps'], [])
        self.assertEqual(groups[2]['apps'][0]['name'], 'Slack')

    def test_overflow_keeps_current_visible_and_all_apps_in_tooltip(self):
        groups = module.collect([{'name': str(i)} for i in range(1, 41)], [window('39', '<&unknown>')], 39)
        rendered = module.render(groups, 39, 4)
        self.assertIn('> 39 </span>', rendered['text'])
        self.assertIn('…36', rendered['text'])
        self.assertIn('<b>40</b>', rendered['text'])
        self.assertIn('○  <b>1</b>', rendered['tooltip'])
        self.assertIn('&lt;&amp;unknown&gt;', rendered['tooltip'])
        self.assertNotIn('<&unknown>', rendered['tooltip'])

    def test_app_overflow_and_same_app_counts(self):
        groups = module.collect([], [window('1', app) for app in ['kitty'] * 12 + ['firefox', 'slack', 'thunar']], 1)
        rendered = module.render(groups, 1)
        self.assertIn('¹²', rendered['text'])
        self.assertIn('+1', rendered['text'])
        self.assertIn('Slack', rendered['tooltip'])
        self.assertIn('kitty ×12', rendered['tooltip'])

    def test_menu_uses_logical_id_and_sanitizes_app_text(self):
        groups = module.collect([], [window('hyprnerd-27-DP-2', 'x\nmalicious\x00')], 1)
        with patch.object(module, 'snapshot', return_value=(groups, 1, 7)), patch.object(module.subprocess, 'run') as run:
            run.return_value = types.SimpleNamespace(returncode=0, stdout='1\n')
            module.menu(move=True)
            self.assertEqual(run.call_args.args[0], ['hyprctl', 'eval', 'HYPRNERD_DESKTOP.move(27,true)'])
            self.assertNotIn('\x00', run.call_args_list[0].kwargs['input'])
            self.assertEqual(len(run.call_args_list[0].kwargs['input'].splitlines()), 2)

    def test_typing_and_window_focus_do_not_refresh_overview(self):
        for event in ['activewindow', 'activewindowv2', 'windowtitle', 'windowtitlev2', 'focusedmon', 'focusedmonv2']:
            self.assertNotIn(event, module.EVENTS)
        for event in ['openwindow', 'closewindow', 'movewindowv2', 'workspacev2', 'monitorremoved']:
            self.assertIn(event, module.EVENTS)


if __name__ == '__main__':
    unittest.main()
