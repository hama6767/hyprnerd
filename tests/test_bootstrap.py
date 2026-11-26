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
    def test_existing_zsh_setup_gets_atuin_without_losing_plugins(self):
        p=self.home/'.zshrc';p.write_text('source $ZSH/oh-my-zsh.sh\nfastfetch\neval "$(atuin init zsh)"\n')
        b.configure_shell(self.backup);first=p.read_text();b.configure_shell(self.backup)
        self.assertEqual(first,p.read_text());self.assertIn('source $ZSH/oh-my-zsh.sh',first)
        self.assertNotIn('fastfetch',first);self.assertIn('$HOME/.local/bin/atuin',first)
        self.assertIn('$+functions[_atuin_preexec]',first)
    def test_other_editor_config_is_backed_up(self):
        d=self.home/'.config/nvim';d.mkdir(parents=True);(d/'init.vim').write_text('set number\n')
        b.configure_nvim(self.backup)
        self.assertEqual((self.backup.root/'files/.config/nvim/init.vim').read_text(),'set number\n');self.assertTrue((d/'init.lua').exists())
    def test_input_preserves_keyboard_groups_and_gtk_theme(self):
        d=self.home/'.config/fcitx5';d.mkdir(parents=True);(d/'profile').write_text('[Groups/0]\nName=Estonian\nDefault Layout=ee-nodeadkeys\nDefaultIM=keyboard-ee-nodeadkeys\n[Groups/0/Items/0]\nName=keyboard-ee-nodeadkeys\nLayout=\n[GroupOrder]\n0=Estonian\n')
        gtk=self.home/'.config/gtk-3.0/settings.ini';gtk.parent.mkdir(parents=True);gtk.write_text('[Settings]\ngtk-theme-name=Custom\n')
        b.configure_input(self.backup);first=(d/'profile').read_text();b.configure_input(self.backup)
        self.assertEqual(first,(d/'profile').read_text());self.assertEqual(first.count('Name=mozc'),1);self.assertIn('Default Layout=ee-nodeadkeys',first);self.assertIn('Control+space',(d/'config').read_text());self.assertIn('gtk-theme-name=Custom',gtk.read_text())
    def test_quiet_shell_keeps_conditionals_valid(self):
        import subprocess
        text=b.quiet_shell("if true; then\nfastfetch\nfi\n")
        subprocess.run(["bash","-n"],input=text,text=True,check=True)
        self.assertNotIn("fastfetch",text)
    def test_legacy_snapshot_preserves_original_and_redirects_sources(self):
        spec=importlib.util.spec_from_file_location('legacy',b.R/'scripts/prepare-legacy-session.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
        d=self.home/'.config/hypr';d.mkdir(parents=True);original='source = $HOME/.config/hypr/UserConfigs/input.conf\n';(d/'hyprland.conf').write_text(original)
        (d/'UserConfigs').mkdir();(d/'UserConfigs/input.conf').write_text('input { kb_layout = ee }\n')
        with patch.object(legacy,'H',self.home):legacy.main(['--apply'])
        snapshots=list((self.home/'.local/state/hyprnerd/legacy-sessions').iterdir());self.assertEqual(len(snapshots),1)
        self.assertEqual((d/'hyprland.conf').read_text(),original);self.assertIn(str(snapshots[0]),(snapshots[0]/'hyprland.conf').read_text())
        self.assertIn(str(snapshots[0]),(self.home/'.local/state/hyprnerd/legacy-entry.conf').read_text())
    def test_arch_package_plan_is_full_upgrade(self):
        command=b.package_commands('arch')[0];self.assertIn('-Syu',command);self.assertIn('fcitx5-mozc',command)
    def test_spf_preserves_custom_options_and_sets_editor_and_cd(self):
        p=self.home/'.config/superfile/config.toml';p.parent.mkdir(parents=True)
        p.write_text('theme = "custom"\neditor = "nano"\ncd_on_quit = false\n')
        b.configure_spf(self.backup);first=p.read_text();b.configure_spf(self.backup)
        self.assertEqual(first,p.read_text());self.assertIn('theme = "custom"',first)
        self.assertIn('editor = "nvim"',first);self.assertIn('dir_editor = "nvim"',first);self.assertIn('cd_on_quit = true',first)
if __name__=='__main__':unittest.main()
