#!/usr/bin/env python3
"""Waybar and Rofi front end to the in-compositor desktop controller."""
import argparse,json,os,pathlib,subprocess,sys
RUNTIME=pathlib.Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/'hyprnerd'
def state():
    try:return json.loads((RUNTIME/'desktop.json').read_text())
    except (OSError,ValueError):return {'mode':'tiling','current':1,'groups':[1],'monitors':1}
def action(code):subprocess.run(['hyprctl','eval','HYPRNERD_DESKTOP.'+code],check=True,stdout=subprocess.DEVNULL)
def menu(move=False):
    sys.dont_write_bytecode=True
    from WorkspaceOverview import menu as overview_menu
    overview_menu(move)
def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['mode','mode-status','status','next','previous','new','menu','move-menu']);a=p.parse_args()
    if a.command in ['mode-status','status']:
        s=state()
        if a.command=='mode-status':value={'text':'󰖲 Window' if s['mode']=='floating' else '󰙀 Tile','class':s['mode'],'tooltip':'Click: window / tile mode\nSuper+Alt+Space: switch mode\nSuper+Space: float current window'}
        else:value={'text':f"  {s['current']}",'tooltip':f"{len(s['groups'])} desktops · {s['monitors']} displays\nClick: choose desktop · Right click: move window\nScroll: previous / next · +: new desktop"}
        print(json.dumps(value,ensure_ascii=False));return
    if a.command=='menu':menu();return
    if a.command=='move-menu':menu(True);return
    action({'mode':'toggle_mode()','next':'step(1)','previous':'step(-1)','new':'new_workspace()'}[a.command])
if __name__=='__main__':main()
