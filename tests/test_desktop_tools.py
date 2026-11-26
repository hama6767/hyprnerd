import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import types
import unittest

R=pathlib.Path(__file__).resolve().parents[1]
S=R/'home/.config/hypr/scripts'
spec=importlib.util.spec_from_file_location('wallpaper_privacy',S/'WallpaperPrivacy.py')
privacy=importlib.util.module_from_spec(spec)
previous=sys.dont_write_bytecode
try:
    sys.dont_write_bytecode=True
    spec.loader.exec_module(privacy)
finally:
    sys.dont_write_bytecode=previous

class WallpaperTests(unittest.TestCase):
    def test_restore_each_output_and_keep_state_when_restore_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);calls=[]
            query=': eDP-1: 1920x1080, scale: 1, currently displaying: image: /tmp/my image.png\n: DP-2: 1920x1200, scale: 1, currently displaying: color: 123abc\n'
            def run(args,**kwargs):
                calls.append(args)
                return types.SimpleNamespace(stdout=query)
            self.assertTrue(privacy.toggle(root,'awww',run))
            self.assertEqual(calls[-1],['awww','clear','000000'])
            self.assertFalse(privacy.toggle(root,'awww',run))
            self.assertIn(['awww','img','--outputs','eDP-1','--transition-type','none','/tmp/my image.png'],calls)
            self.assertIn(['awww','clear','--outputs','DP-2','123abc'],calls)
            privacy.toggle(root,'awww',run)
            def broken(args,**kwargs):
                if args[1]=='img':raise subprocess.CalledProcessError(1,args)
                return run(args,**kwargs)
            with self.assertRaises(subprocess.CalledProcessError):privacy.toggle(root,'awww',broken)
            self.assertTrue((root/'wallpaper-privacy.json').exists())
            self.assertTrue(all(c[0]=='awww' for c in calls))

class DisplayImportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=pathlib.Path(self.temp.name)
        self.norm=self.root/'norm.json';self.norm.write_text(json.dumps([{'port':'DP-1','identity':'Dell|Panel|one','description':'Dell','focused':True}]))
        self.conf=self.root/'monitors.conf'
    def parse(self,text):
        self.conf.write_text(text)
        return subprocess.run(['bash','-c','source "$1"; ds_from_nwg_conf "$2" "$3"','bash',str(S/'lib_display_store.sh'),str(self.conf),str(self.norm)],text=True,capture_output=True)
    def test_vrr_is_preserved_and_unsupported_extras_are_rejected(self):
        for vrr in [0,1,2,3]:
            result=self.parse(f'monitor=DP-1,1920x1080@60.0,-1920x360,1,vrr,{vrr}\n')
            self.assertEqual(result.returncode,0,result.stderr)
            monitor=json.loads(result.stdout)['monitors'][0]
            self.assertEqual((monitor['vrr'],monitor['x'],monitor['y']),(vrr,-1920,360))
        for extra in ['vrr,99','mirror,eDP-1','bitdepth,10']:
            result=self.parse('monitor=DP-1,1920x1080@60.0,0x0,1,'+extra+'\n')
            self.assertNotEqual(result.returncode,0)
    def test_import_backs_up_manual_rules_and_survives_restart(self):
        config=self.root/'config';user=config/'hypr/UserConfigs';user.mkdir(parents=True)
        manual=user/'monitors.lua';manual.write_text('-- user rules\nhl.monitor({output="DP-1",position="auto"})\n');old=manual.read_text()
        self.conf.write_text('monitor=DP-1,1920x1080@60.0,0x360,1,vrr,0\n')
        live=[{'name':'DP-1','make':'Dell','model':'Panel','serial':'one','width':1920,'height':1080,'refreshRate':60,'x':0,'y':360,'scale':1,'transform':0,'disabled':False,'focused':True,'availableModes':['1920x1080@60.00Hz']}]
        (self.root/'live.json').write_text(json.dumps(live))
        fake=self.root/'hyprctl';fake.write_text('#!/usr/bin/env python3\nimport sys,pathlib\np=pathlib.Path(__file__).parent\nif sys.argv[1]=="-j":print((p/"live.json").read_text())\nelse:\n with (p/"commands").open("a") as f:f.write(sys.argv[-1]+"\\n")\n print("ok")\n');fake.chmod(0o755)
        env=dict(os.environ,XDG_CONFIG_HOME=str(config),DP_RUNTIME_DIR=str(self.root/'run'),DP_HYPRCTL=str(fake),DP_PGREP='/bin/false',DP_NOTIFY='/bin/true',DP_WAYBAR_STARTUP='/bin/true',DP_SKIP_LOCK='1')
        result=subprocess.run(['bash',str(S/'DisplayProfile.sh'),'import-nwg',str(self.conf)],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('vrr = 0',manual.read_text());self.assertIn('0x360',manual.read_text())
        self.assertEqual(next(user.glob('monitors.lua.before-nwg-*')).read_text(),old)
        store=json.loads((user/'display-layouts.json').read_text());saved=next(iter(store['fingerprints'].values()))
        self.assertEqual(saved['default'],'nwg-displays');self.assertEqual(saved['layouts']['nwg-displays']['monitors'][0]['vrr'],0)
        self.assertIn('vrr = 0',(self.root/'commands').read_text())
        # Re-selecting identical settings must not trigger the compositor's
        # file watcher: both inode and nanosecond mtime remain unchanged.
        unchanged=(manual.stat().st_ino,manual.stat().st_mtime_ns)
        result=subprocess.run(['bash',str(S/'DisplayProfile.sh'),'--','nwg-displays'],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((manual.stat().st_ino,manual.stat().st_mtime_ns),unchanged)
        # The event watcher must use the non-persisting path even when the
        # store renders different config bytes. Otherwise each configreloaded
        # event writes monitors.lua and causes the next configreloaded event.
        saved['layouts']['nwg-displays']['monitors'][0]['vrr']=1
        (user/'display-layouts.json').write_text(json.dumps(store))
        events=self.root/'events';events.write_text('configreloaded>>\n')
        watcher_env=dict(env,MW_PROFILE_SCRIPT=str(S/'DisplayProfile.sh'),MW_RUNTIME_DIR=env['DP_RUNTIME_DIR'],MW_EVENT_FILE=str(events),MW_MAX_RECONNECTS='0',MW_NWG_PROC='',MW_NWG_CONF=str(self.conf))
        result=subprocess.run(['bash',str(S/'MonitorWatcher.sh')],env=watcher_env,text=True,capture_output=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('without rewriting monitor config',result.stderr)
        self.assertEqual((manual.stat().st_ino,manual.stat().st_mtime_ns),unchanged)
        self.assertIn('vrr = 0',manual.read_text())
        current=pathlib.Path(env['DP_RUNTIME_DIR'])/'kooldots-display-profiles/current'
        self.assertEqual(current.read_text().splitlines()[1],'nwg-displays')
        # No runtime state: a fresh session must resolve the saved arrangement.
        env['DP_RUNTIME_DIR']=str(self.root/'new-session')
        result=subprocess.run(['bash',str(S/'DisplayProfile.sh'),'auto'],env=env,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('nwg-displays',result.stderr)

if __name__=='__main__':unittest.main()
