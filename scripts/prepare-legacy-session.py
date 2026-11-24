#!/usr/bin/env python3
"""Back up a pre-Lua Hyprland configuration and prepare a temporary compatibility entry."""
import argparse,datetime,json,os,pathlib,shutil,subprocess
H=pathlib.Path.home()
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');a=p.parse_args(argv)
    root=H/'.config/hypr';entry=root/'hyprland.conf'
    if not entry.is_file():raise SystemExit('No legacy hyprland.conf to preserve')
    if not a.apply:print('Will snapshot',root,'and keep its old session entry until next login.');return
    backup=H/'.local/state/hyprnerd/legacy-sessions'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(root,backup,symlinks=True)
    # Relative references remain inside the snapshot; redirect explicit old config paths.
    for path in backup.rglob('*'):
        if path.is_symlink():
            target=os.readlink(path)
            if str(root) in target:path.unlink();path.symlink_to(target.replace(str(root),str(backup)))
        elif path.is_file():
            try:text=path.read_text()
            except (UnicodeError,OSError):continue
            updated=text.replace(str(root),str(backup)).replace('$HOME/.config/hypr',str(backup)).replace('~/.config/hypr',str(backup))
            if updated!=text:path.write_text(updated)
    state=H/'.local/state/hyprnerd/legacy-entry.conf';state.write_text('# Previous session compatibility; new Hyprland reads hyprland.lua.\nsource = '+str(backup/'hyprland.conf')+'\n')
    print('LEGACY_BACKUP:',backup);print('COMPATIBILITY_ENTRY:',state)
if __name__=='__main__':main()
