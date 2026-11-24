import importlib.util
import pathlib
import sys
import unittest

path = pathlib.Path(__file__).resolve().parents[1] / 'home/.config/hypr/scripts/MonitorIndicator.py'
spec = importlib.util.spec_from_file_location('monitor_indicator', path)
module = importlib.util.module_from_spec(spec)
# Runtime files are shipped with an exact asset manifest: tests must not add
# bytecode caches to the distributable home directory.
bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    spec.loader.exec_module(module)
finally:
    sys.dont_write_bytecode = bytecode_setting


class MonitorIndicatorTests(unittest.TestCase):
    def test_only_selected_output_is_highlighted_without_polling(self):
        monitors = [
            {'name': 'DP-2', 'x': 1920, 'y': 0, 'focused': False},
            {'name': 'eDP-1', 'x': 0, 'y': 0, 'focused': True},
        ]
        reads = []
        def reader():
            reads.append(True)
            return monitors
        left = module.Indicator('eDP-1', reader)
        right = module.Indicator('DP-2', reader)
        for indicator in (left, right):
            indicator.refresh()
        self.assertEqual(left.render()['class'], 'active')
        self.assertEqual(right.render()['class'], 'inactive')
        for indicator in (left, right):
            indicator.event('focusedmonv2>>DP-2,hyprnerd-1-DP-2\n')
        self.assertEqual(left.render()['class'], 'inactive')
        self.assertEqual(right.render()['class'], 'active')
        self.assertEqual(right.render()['text'], 'B')
        self.assertIn('DP-2', right.render()['tooltip'])
        self.assertEqual(len(reads), 2, 'Monitor focus must not spawn a query per keypress')

    def test_hotplug_reindexes_and_excludes_mirrors_and_disabled_outputs(self):
        monitors = [
            {'name': 'UP<&', 'x': 0, 'y': -720, 'focused': True},
            {'name': 'DOWN', 'x': 0, 'y': 0, 'focused': False},
            {'name': 'mirror', 'x': -500, 'y': 0, 'mirrorOf': 'DOWN'},
            {'name': 'off', 'x': -500, 'y': 0, 'disabled': True},
        ]
        top = module.Indicator('UP<&', lambda: monitors)
        bottom = module.Indicator('DOWN', lambda: monitors)
        top.refresh(); bottom.refresh()
        self.assertEqual(top.render()['text'], 'A')
        self.assertIn('UP&lt;&amp;', top.render()['tooltip'])
        self.assertEqual(bottom.render()['text'], 'B')
        monitors.pop(0); monitors[0]['focused'] = True
        top.event('monitorremoved>>UP<&'); bottom.event('monitorremoved>>UP<&')
        self.assertEqual(top.render()['text'], '')
        self.assertEqual(bottom.render()['text'], 'A')
        self.assertEqual(bottom.render()['class'], 'active')
        self.assertFalse(bottom.event('activewindow>>kitty,title'))

    def test_labels_are_not_limited_to_twenty_six_outputs(self):
        self.assertEqual(module.monitor_label(26), 'Z')
        self.assertEqual(module.monitor_label(27), 'AA')


if __name__ == '__main__':
    unittest.main()
