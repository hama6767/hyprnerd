#!/usr/bin/env python3
"""Read-only checks of the installed profile, including live compositor values."""
import hashlib,json,os,pathlib,shutil,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];H=pathlib.Path.home();report={};errors=[]
def call(*args):
 r=subprocess.run(args,capture_output=True,text=True)
 if r.returncode:raise RuntimeError(' '.join(args)+': '+r.stderr+r.stdout)
 return r.stdout.strip()
def check(name,fn):
 try:report[name]=fn();print('PASS',name)
 except Exception as e:report[name]={'error':str(e)};errors.append(name);print('FAIL',name,str(e))
def config():
 out=call('/usr/bin/Hyprland','--verify-config','-c',str(H/'.config/hypr/hyprland.lua'))
 assert 'config ok' in out,out
 return 'config ok'
def wallpaper():
 expected='6ea87df130eeb91675eafa7af3748afff62efed71d10347fae2d5b0b430d570b'
 actual=hashlib.sha256((H/'.config/hypr/wallpaper_effects/.wallpaper_current').read_bytes()).hexdigest()
 assert actual==expected,actual
 return actual
def palette():
 for rel in ['waybar/wallust/colors-waybar.css','rofi/wallust/colors-rofi.rasi','wallust/wallust-hyprland.conf']:
  assert (H/'.config/hypr'/rel).read_bytes()==(R/'home/.config/hypr/reference-palette'/rel).read_bytes(),rel
 return 'Exact reference palette in all three consumers'
def kitty():
 out=call('kitty','+runpy','from kitty.config import load_config; import json,os; bad=[]; o=load_config(os.path.expanduser("~/.config/kitty/kitty.conf"),accumulate_bad_lines=bad); print(json.dumps({"errors":str(bad),"font":str(o.font_family),"size":o.font_size,"opacity":o.background_opacity}))')
 obj=json.loads(out);assert obj['errors']=='[]' and obj['size']==12 and obj['opacity']==.9,obj
 return obj
def fonts():
 values={font:call('fc-match','-f','%{family}|%{style}',font) for font in ['Noto Sans Mono','Adwaita Sans','Fira Code:style=Medium','JetBrainsMono Nerd Font:style=Bold']}
 for requested,actual in values.items():assert requested.split(':')[0] in actual,values
 return values
def gtk():
 expected={'gtk-theme':'Kali-Dark','font-name':'Adwaita Sans 11','icon-theme':'Flat-Remix-Blue-Dark','cursor-theme':'Adwaita'}
 found={k:call('gsettings','get','org.gnome.desktop.interface',k).strip("'") for k in expected}
 assert found==expected,found
 return found
def live():
 assert not call('hyprctl','configerrors')
 expected={'general:border_size':('int',2),'decoration:rounding':('int',10),'decoration:blur:passes':('int',2),'decoration:active_opacity':('float',1.0),'decoration:inactive_opacity':('float',.9)}
 for k,(kind,value) in expected.items():
  obj=json.loads(call('hyprctl','-j','getoption',k));assert obj[kind]==value,(k,obj)
 layers=json.loads(call('hyprctl','-j','layers'));bars=[]
 for monitor,info in layers.items():
  for level,items in info['levels'].items():
   for item in items:
    if item['namespace'] in ['topbar','bottombar']:bars.append({'monitor':monitor,'name':item['namespace'],'height':item['h']})
 assert bars and all(x['name']=='topbar' and x['height']==30 for x in bars),bars
 opacity={}
 for c in json.loads(call('hyprctl','-j','clients')):
  if c['class'] not in ['firefox_firefox','kitty']:continue
  values={p:call('hyprctl','getprop','address:'+c['address'],p) for p in ['opacity','opacity_inactive','opacity_override']}
  assert values['opacity']==('0.9' if c['class']=='firefox_firefox' else '0.8') and values['opacity_inactive']=='0.7' and values['opacity_override']=='false',values
  opacity[c['class']]=values
 return {'configerrors':[],'bars':bars,'window_rules':opacity}
check('hyprland_config',config);check('wallpaper_sha256',wallpaper);check('reference_palette',palette);check('kitty',kitty);check('font_resolution',fonts);check('gtk',gtk)
check('rofi',lambda:call('rofi','-rasi-validate',str(H/'.config/hypr/rofi/config.rasi')) or 'valid')
if os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):check('live_hyprland',live)
else:report['live_hyprland']='Skipped: no active Hyprland session'
if '--json' in sys.argv:print(json.dumps(report,ensure_ascii=False,indent=2))
sys.exit(bool(errors))
