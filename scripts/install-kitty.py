#!/usr/bin/env python3
"""Install the pinned official Kitty build in user space, preserving old launchers."""
import datetime,hashlib,json,os,pathlib,platform,shutil,tarfile,tempfile,urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
def main():
    if platform.system()!='Linux' or platform.machine() not in ['x86_64','amd64']:
        raise SystemExit('This pinned binary is for Linux x86_64; install Kitty for your platform separately.')
    spec=json.loads((R/'dependencies.lock.json').read_text())['kitty_binary']
    cache=R/'.cache';cache.mkdir(exist_ok=True)
    archive=cache/pathlib.PurePosixPath(spec['url']).name
    if not archive.exists():
        temporary=archive.with_suffix('.download')
        urllib.request.urlretrieve(spec['url'],temporary);temporary.replace(archive)
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=spec['sha256']:
        raise SystemExit('Kitty archive checksum mismatch; remove the cached archive before retrying.')
    root=pathlib.Path.home()/'.local/opt/hyprnerd-kitty';root.mkdir(parents=True,exist_ok=True)
    target=root/spec['version']
    if not target.exists():
        with tempfile.TemporaryDirectory(prefix='install-',dir=root) as tmp:
            payload=pathlib.Path(tmp)/'app';payload.mkdir()
            with tarfile.open(archive) as tar:tar.extractall(payload,filter='data')
            if not (payload/'bin/kitty').is_file():raise RuntimeError('Kitty executable missing from archive')
            payload.rename(target)
    bindir=pathlib.Path.home()/'.local/bin';bindir.mkdir(parents=True,exist_ok=True)
    for name in ['kitty','kitten']:
        source=target/'bin'/name;link=bindir/name
        if link.is_symlink() and link.resolve()==source:continue
        if link.exists() or link.is_symlink():
            backup=link.with_name(name+'.before-hyprnerd-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
            link.rename(backup);print('BACKUP:',backup)
        link.symlink_to(source)
    print('Installed official Kitty',spec['version'],'at',target)
    print('Use ~/.local/bin/kitty; the system package and running windows are unchanged.')
if __name__=='__main__':main()
