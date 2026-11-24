"""Integration tests with fake desktop commands and real, isolated filesystem changes."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

SPEC=importlib.util.spec_from_file_location('installer',Path(__file__).resolve().parents[1]/'install.py')
installer=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name);self.home=self.base/'user';self.repo=self.base/'repo'
        self.home.mkdir();(self.repo/'home').mkdir(parents=True)
        self.settings={key:(str(value) if isinstance(value,int) else repr(value)) for key,value in installer.GSET.items()}
        self.settings['gtk-theme']="'PreviousTheme'";self.before=dict(self.settings)
        self.fail_verify=False
        for relative in installer.ROOTS:
            target=self.repo/'home'/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            if relative in ['.config/waybar','.config/rofi','.config/wallust']:
                target.symlink_to('hypr/'+relative.rsplit('/',1)[-1]);continue
            if relative in ['.config/nwg-dock-hyprland','.config/hypr','.config/swaync','.config/wlogout','.config/quickshell','.config/Kvantum','.config/cava','.config/swappy','.local/share/themes/Kali-Dark','.local/share/icons/Flat-Remix-Blue-Dark','.local/share/fonts/kool-reference']:
                target.mkdir();(target/'fixture').write_text('profile data\n')
            else:target.write_text('profile data\n')
        hypr=self.repo/'home/.config/hypr'
        for name in ['rofi','waybar','wallust','UserConfigs']:(hypr/name).mkdir(exist_ok=True)
        (hypr/'hyprland.lua').write_text('-- syntax handled by fake compositor\n')
        (hypr/'waybar/Modules').write_text('{"temperature": {}}\n')
        host=self.repo/'hosts/ubuntu-desktop';host.mkdir(parents=True)
        for name in ['user_env.lua','user_settings.lua','monitors.lua','workspaces.lua']:
            (hypr/'UserConfigs'/name).write_text('-- portable '+name+'\n')
            (host/name).write_text('-- desktop '+name+'\n')
        (host/'qs').write_text('#!/bin/sh\n')
        self.original=self.home/'.config/hypr';self.original.mkdir(parents=True)
        (self.original/'original.conf').write_text('original desktop\n')
        self.bashrc=self.home/'.bashrc';self.bashrc.write_text('# keep existing hooks\n')
        plugins=self.home/'.local/lib/kool-qt6/plugins/styles';plugins.mkdir(parents=True);(plugins/'libkvantum.so').touch()
        self.patches=[mock.patch.object(installer,'H',self.home),mock.patch.object(installer,'R',self.repo),mock.patch.object(installer,'run',side_effect=self.command),mock.patch.object(installer.shutil,'which',return_value='/usr/bin/fake'),mock.patch.dict(os.environ,{},clear=True)]
        for patch in self.patches:patch.start();self.addCleanup(patch.stop)

    def command(self,cmd,check=True):
        stdout=''
        if cmd[0]=='gsettings':
            if cmd[1]=='get':stdout=self.settings[cmd[3]]+'\n'
            else:
                value=cmd[4]
                self.settings[cmd[3]]=value if value.startswith("'") or value.isdigit() else repr(value)
        elif '--version' in cmd:stdout='Hyprland 0.57.2\n'
        elif '--verify-config' in cmd and self.fail_verify:
            return subprocess.CompletedProcess(cmd,1,'config failed','invalid fixture')
        return subprocess.CompletedProcess(cmd,0,stdout,'')

    def invoke(self,*args):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            try:installer.main(list(args))
            except SystemExit as exc:
                if exc.code not in (None,0):raise
        return stream.getvalue()

    def backups(self):return sorted((self.home/'.local/state/kool-dotfiles/backups').glob('*'))

    def test_check_is_read_only(self):
        before=installer.signature(self.home)
        self.invoke('--profile','generic','--check')
        self.assertEqual(before,installer.signature(self.home));self.assertEqual(self.settings,self.before)
        self.assertEqual(self.backups(),[])

    def test_apply_is_idempotent_and_preserves_shell_and_host(self):
        user=self.original/'UserConfigs';user.mkdir()
        (user/'user_env.lua').write_text('-- custom host\n')
        self.invoke('--profile','generic','--apply','--no-reload')
        self.assertIn('keep existing hooks',self.bashrc.read_text())
        self.assertIn('-- custom host',(user/'user_env.lua').read_text())
        self.assertEqual(self.settings['gtk-theme'],"'Kali-Dark'")
        self.assertTrue((self.home/'.config/waybar').is_symlink())
        count=len(self.backups());out=self.invoke('--profile','generic','--apply','--no-reload')
        self.assertIn('changed paths: 0',out);self.assertEqual(count,len(self.backups()))
        self.assertEqual(self.bashrc.read_text().count('# KooL terminal appearance'),1)
        self.assertEqual((user/'user_env.lua').read_text().count('-- BEGIN KOOL APPEARANCE'),1)

    def test_restore_round_trip_and_symlinks(self):
        alias=self.home/'.config/waybar';alias.symlink_to('old-theme')
        self.invoke('--profile','ubuntu-desktop','--apply','--no-reload')
        backup=self.backups()[0]
        self.assertIn('Restore plan valid',self.invoke('--restore',str(backup),'--check'))
        self.invoke('--restore',str(backup),'--no-reload')
        self.assertEqual((self.original/'original.conf').read_text(),'original desktop\n')
        self.assertEqual(alias.readlink(),Path('old-theme'))
        self.assertEqual(self.bashrc.read_text(),'# keep existing hooks\n')
        self.assertFalse((self.home/'Pictures/wallpapers/wall_anime_4K.png').exists())
        self.assertEqual(self.settings,self.before)

    def test_failed_config_rolls_back(self):
        self.fail_verify=True
        with self.assertRaises(RuntimeError):self.invoke('--apply','--no-reload')
        self.assertEqual((self.original/'original.conf').read_text(),'original desktop\n')
        self.assertEqual(self.bashrc.read_text(),'# keep existing hooks\n')
        self.assertEqual(self.settings,self.before)

    def test_restore_rejects_traversal_and_unmanaged_paths_before_deleting(self):
        backup=self.base/'malicious';backup.mkdir()
        for path in ['../outside','/tmp/outside','.ssh','unmanaged-file']:
            (backup/'manifest.json').write_text(json.dumps({'home':str(self.home),'paths':[path],'gsettings':self.before}))
            with self.assertRaises(ValueError):installer.restore(backup,reload=False)
        self.assertTrue((self.original/'original.conf').exists())

    def test_wrong_home_backup_rejected(self):
        backup=self.base/'wrong';backup.mkdir()
        (backup/'manifest.json').write_text(json.dumps({'home':'/another/user','paths':[],'gsettings':self.before}))
        with self.assertRaises(ValueError):installer.restore(backup,reload=False)

    def test_signature_tracks_executable_bits_and_link_targets(self):
        f=self.base/'executable';f.write_text('#!/bin/sh\n');f.chmod(0o644);before=installer.signature(f);f.chmod(0o755)
        self.assertNotEqual(before,installer.signature(f))
        link=self.base/'link';link.symlink_to('executable');before=installer.signature(link);link.unlink();link.symlink_to('missing')
        self.assertNotEqual(before,installer.signature(link))

if __name__=='__main__':unittest.main()
