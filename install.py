#!/usr/bin/env python3
"""Backed-up, repeatable per-user installation; no root and no network."""
import argparse, datetime, hashlib, json, os, pathlib, shutil, subprocess, tempfile
R=pathlib.Path(__file__).resolve().parent
H=pathlib.Path.home()
ROOTS=['.config/nwg-dock-hyprland','.config/hypr','.config/waybar','.config/rofi','.config/wallust','.config/swaync','.config/wlogout','.config/quickshell','.config/Kvantum','.config/cava','.config/swappy','.config/kitty/kitty.conf','.config/fastfetch/kool.jsonc','.config/gtk-3.0/settings.ini','.config/gtk-4.0/settings.ini','.config/qt5ct/qt5ct.conf','.config/qt6ct/qt6ct.conf','.config/xsettingsd/xsettingsd.conf','.config/fontconfig/conf.d/05-kool-reference.conf','.config/bashrc/kool-terminal.bash','.icons/default/index.theme','.local/share/themes/Kali-Dark','.local/share/icons/Flat-Remix-Blue-Dark','.local/share/fonts/kool-reference','Pictures/wallpapers/wall_anime_4K.png']
GSET={'gtk-theme':'Kali-Dark','icon-theme':'Flat-Remix-Blue-Dark','font-name':'Adwaita Sans 11','cursor-theme':'Adwaita','cursor-size':24,'color-scheme':'prefer-dark'}
def exists(p):return p.exists() or p.is_symlink()
def rm(p):
    if p.is_symlink() or p.is_file():p.unlink()
    elif p.exists():shutil.rmtree(p)
def cp(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_symlink():dst.symlink_to(os.readlink(src))
    elif src.is_dir():shutil.copytree(src,dst,symlinks=True)
    else:shutil.copy2(src,dst)
def signature(p):
    if p.is_symlink():return ('link',os.readlink(p))
    if not p.exists():return None
    if p.is_file():return ('file',hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mode&0o111)
    return ('dir',[(f.name,signature(f)) for f in sorted(p.iterdir()) if not f.name.startswith(('.current_wallpaper_', '.wallpaper_current_')) and f.name not in ['.cache', '.last_used', '.last_wallpaper']])
def run(cmd,check=True):return subprocess.run(cmd,check=check,text=True,capture_output=True)
def capture_gsettings():
    return {k:run(['gsettings','get','org.gnome.desktop.interface',k]).stdout.strip() for k in GSET}
def reload_desktop():
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):print('No active Hyprland session: applied files; log in to activate.');return
    result=run(['hyprctl','reload','config-only']);print(result.stdout.strip())
    errors=run(['hyprctl','configerrors']).stdout.strip()
    if errors:raise RuntimeError('Hyprland config errors: '+errors)
    # Run in the compositor environment so all children receive the new Qt theme.
    cmd='"$HOME/.config/hypr/scripts/ApplyReferenceAppearance.sh"'
    print(run(['hyprctl','eval','hl.exec_cmd('+json.dumps(cmd)+')']).stdout.strip())
def read_backup(backup):
    m=json.loads((backup/'manifest.json').read_text())
    if m['home']!=str(H):raise ValueError('Backup belongs to a different HOME')
    allowed=set(ROOTS)|{'.bashrc','.local/bin/qs'}
    paths=m['paths']
    if not isinstance(paths,list) or len(set(paths))!=len(paths):raise ValueError('Invalid backup paths')
    for rel in paths:
        path=pathlib.PurePath(rel)
        if path.is_absolute() or '..' in path.parts or rel not in allowed:
            raise ValueError('Unsafe backup path: '+rel)
    if set(m['gsettings'])!=set(GSET):raise ValueError('Incomplete GTK backup')
    return m

def restore(backup,reload=True):
    m=read_backup(backup)
    for rel in reversed(m['paths']):
        dst=H/rel;rm(dst)
        if exists(backup/'files'/rel):cp(backup/'files'/rel,dst)
    for k,v in m['gsettings'].items():run(['gsettings','set','org.gnome.desktop.interface',k,v])
    run(['fc-cache','-f'],False)
    # The restored configuration predates the profile helper, so reload directly.
    if reload and os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
        run(['hyprctl','reload','config-only'],False)
        subprocess.Popen([str(H/'.config/hypr/scripts/WallpaperDaemon.sh')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
        subprocess.Popen([str(H/'.config/hypr/scripts/WaybarStartup.sh'),'--restart'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
    print('Restored',backup)
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=['generic','ubuntu-desktop'],default='generic')
    p.add_argument('--apply',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--restore',type=pathlib.Path)
    p.add_argument('--no-reload',action='store_true')
    p.add_argument('--keep-legacy-session',action='store_true',help='Keep the entry prepared by scripts/prepare-legacy-session.py; requires --no-reload')
    a=p.parse_args(argv)
    if a.keep_legacy_session and not a.no_reload:p.error('--keep-legacy-session requires --no-reload')
    if a.restore:
        backup=a.restore.resolve()
        if a.check:
            m=read_backup(backup)
            print('Restore plan valid:',len(m['paths']),'paths; GTK settings recorded; no changes made.')
        else:restore(backup,reload=not a.no_reload)
        raise SystemExit()
    if not (a.apply or a.check):p.error('Choose --check or --apply (or --restore BACKUP)')
    required=['hyprctl','Hyprland','kitty','waybar','rofi','swaync','jq','gsettings','fc-cache','awww','awww-daemon','nwg-dock-hyprland']
    missing=[c for c in required if not shutil.which(c)]
    if missing:raise SystemExit('Missing prerequisites: '+', '.join(missing))
    v=run(['Hyprland','--version']).stdout
    if '0.57.' not in v:raise SystemExit('This port is tested for Hyprland 0.57.x; found '+v.splitlines()[0])
    if not (H/'.local/lib/kool-qt6/plugins/styles/libkvantum.so').exists() and not pathlib.Path('/usr/lib/x86_64-linux-gnu/qt6/plugins/styles/libkvantum.so').exists() and not pathlib.Path('/usr/lib/qt6/plugins/styles/libkvantum.so').exists():
        raise SystemExit('Install Kvantum first: python3 scripts/install-qt-plugins.py (Ubuntu 24.04 amd64)')
    with tempfile.TemporaryDirectory(prefix='kool-stage-') as temp:
        stage=pathlib.Path(temp)/'home';shutil.copytree(R/'home',stage,symlinks=True)
        roots=list(ROOTS)
        if a.keep_legacy_session:
            legacy=H/'.local/state/hyprnerd/legacy-entry.conf'
            if not legacy.is_file():raise RuntimeError('Run scripts/prepare-legacy-session.py --apply first')
            shutil.copy2(legacy,stage/'.config/hypr/hyprland.conf')
        hostfiles=['user_env.lua','user_settings.lua','monitors.lua','workspaces.lua']
        if a.profile=='ubuntu-desktop':
            for name in hostfiles:shutil.copy2(R/'hosts/ubuntu-desktop'/name,stage/'.config/hypr/UserConfigs'/name)
            if (H/'.local/share/ml4w-tools/quickshell/bin/qs').exists():
                target=stage/'.local/bin/qs';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'hosts/ubuntu-desktop/qs',target);roots.append('.local/bin/qs')
        else:
            # Retain host input and monitor overrides, then add the portable visual env.
            for name in hostfiles:
                src=H/'.config/hypr/UserConfigs'/name;dst=stage/'.config/hypr/UserConfigs'/name
                if src.exists():
                    if name=='user_env.lua':
                        host=src.read_text().split('-- BEGIN KOOL APPEARANCE')[0].rstrip()
                        dst.write_text(host+'\n\n-- BEGIN KOOL APPEARANCE\n'+dst.read_text())
                    else:shutil.copy2(src,dst)
        # Choose the first available CPU temperature sensor, never a copied laptop hwmon index.
        candidates=[]
        for hw in pathlib.Path('/sys/class/hwmon').glob('hwmon*'):
            if (hw/'name').exists() and (hw/'name').read_text().strip() in ['k10temp','coretemp','zenpower']:
                candidates+=list(hw.glob('temp*_input'))
        if candidates:
            path=stage/'.config/hypr/waybar/Modules';data=json.loads(path.read_text());data['temperature']['hwmon-path']=str(sorted(candidates)[0]);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        # Source hook only once; preserve ROS, Atuin and all unrelated shell settings.
        bashrc=H/'.bashrc';old=bashrc.read_text() if bashrc.exists() else ''
        if '.config/bashrc/kool-terminal.bash' not in old:
            (stage/'.bashrc').write_text(old+'\n# KooL terminal appearance\nif [[ $- == *i* && -n ${KITTY_WINDOW_ID-} && -f "$HOME/.config/bashrc/kool-terminal.bash" ]]; then\n    source "$HOME/.config/bashrc/kool-terminal.bash"\nfi\n');roots.append('.bashrc')
        changes=[rel for rel in roots if signature(stage/rel)!=signature(H/rel)]
        current=capture_gsettings();gchanges=[k for k,v in GSET.items() if current[k]!= (str(v) if isinstance(v,int) else repr(v))]
        print('Profile:',a.profile,'; changed paths:',len(changes),'; GTK settings:',', '.join(gchanges) or 'unchanged')
        for rel in changes:print(' ',rel)
        if not a.apply:raise SystemExit()
        if changes or gchanges:
            backup=H/'.local/state/kool-dotfiles/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
            backup.mkdir(parents=True)
            for rel in changes:
                if exists(H/rel):cp(H/rel,backup/'files'/rel)
            (backup/'manifest.json').write_text(json.dumps({'home':str(H),'profile':a.profile,'paths':changes,'gsettings':current},indent=2)+'\n')
            print('BACKUP:',backup,flush=True)
            try:
                for rel in changes:rm(H/rel);cp(stage/rel,H/rel)
                for k,v in GSET.items():run(['gsettings','set','org.gnome.desktop.interface',k,str(v)])
                run(['fc-cache','-f',str(H/'.local/share/fonts/kool-reference')])
                # Hyprland reads helper paths from HOME: validate after install, before live reload.
                result=run(['/usr/bin/Hyprland','--verify-config','-c',str(H/'.config/hypr/hyprland.lua')],False)
                if result.returncode:raise RuntimeError(result.stdout+result.stderr)
            except Exception:
                restore(backup,reload=not a.no_reload);raise
        if not a.no_reload:reload_desktop()
        print('Applied successfully.')


if __name__ == "__main__":
    main()
