import importlib.util,pathlib,tempfile,unittest
from unittest.mock import patch
SPEC=importlib.util.spec_from_file_location('bootstrap',pathlib.Path(__file__).resolve().parents[1]/'bootstrap.py')
b=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(b)
class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.home=pathlib.Path(self.tmp.name)
        self.patch=patch.object(b,'H',self.home);self.patch.start();self.addCleanup(self.patch.stop);self.backup=b.Backup()
    def test_shell_idempotence_preserves_ros_and_aliases(self):
        p=self.home/'.bashrc';p.write_text('source /opt/ros/jazzy/setup.bash\nfastfetch --config abc\nalias info="neofetch"\neval "$(atuin init bash)"\n')
        b.configure_shell(self.backup);first=p.read_text();b.configure_shell(self.backup)
        self.assertEqual(first,p.read_text());self.assertIn('source /opt/ros/jazzy/setup.bash',first);self.assertIn('alias info="neofetch"',first);self.assertNotIn('fastfetch --config',first)
        self.assertEqual(first.count('# BEGIN HYPRNERD SHELL'),1);self.assertIn('$HOME/.local/bin/atuin',first)
    def test_existing_lazyvim_customizations_survive(self):
        d=self.home/'.config/nvim';(d/'lua/config').mkdir(parents=True);(d/'lua/config/lazy.lua').write_text('-- LazyVim/LazyVim\n-- custom configuration\n');(d/'lua/config/options.lua').write_text('vim.opt.tabstop = 8\n')
        b.configure_nvim(self.backup);first=(d/'lua/config/options.lua').read_text();b.configure_nvim(self.backup)
        self.assertEqual(first,(d/'lua/config/options.lua').read_text());self.assertIn('tabstop = 8',first);self.assertIn('relativenumber = true',first);self.assertIn('custom configuration',(d/'lua/config/lazy.lua').read_text())
    def test_other_editor_config_is_backed_up(self):
        d=self.home/'.config/nvim';d.mkdir(parents=True);(d/'init.vim').write_text('set number\n')
        b.configure_nvim(self.backup)
        self.assertEqual((self.backup.root/'files/.config/nvim/init.vim').read_text(),'set number\n');self.assertTrue((d/'init.lua').exists())
    def test_input_preserves_keyboard_groups_and_gtk_theme(self):
        d=self.home/'.config/fcitx5';d.mkdir(parents=True);(d/'profile').write_text('[Groups/0]\nName=Estonian\nDefault Layout=ee-nodeadkeys\nDefaultIM=keyboard-ee-nodeadkeys\n[Groups/0/Items/0]\nName=keyboard-ee-nodeadkeys\nLayout=\n[GroupOrder]\n0=Estonian\n')
        gtk=self.home/'.config/gtk-3.0/settings.ini';gtk.parent.mkdir(parents=True);gtk.write_text('[Settings]\ngtk-theme-name=Custom\n')
        b.configure_input(self.backup);first=(d/'profile').read_text();b.configure_input(self.backup)
        self.assertEqual(first,(d/'profile').read_text());self.assertEqual(first.count('Name=mozc'),1);self.assertIn('Default Layout=ee-nodeadkeys',first);self.assertIn('Control+space',(d/'config').read_text());self.assertIn('gtk-theme-name=Custom',gtk.read_text())
    def test_arch_package_plan_is_full_upgrade(self):
        command=b.package_commands('arch')[0];self.assertIn('-Syu',command);self.assertIn('fcitx5-mozc',command)
if __name__=='__main__':unittest.main()
