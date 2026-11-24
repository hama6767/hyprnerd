#!/usr/bin/env python3
"""Install pinned Ubuntu Kvantum plugins without root or changing APT sources."""
import argparse, hashlib, json, os, pathlib, platform, shutil, subprocess, tempfile, urllib.request
R=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--prefix',type=pathlib.Path,default=pathlib.Path.home()/'.local/lib');a=p.parse_args()
if platform.machine()!='x86_64':raise SystemExit('The bundled package lock supports Ubuntu amd64 only. Install native Kvantum on other systems.')
cache=R/'.cache';cache.mkdir(exist_ok=True)
for item in json.loads((R/'dependencies.lock.json').read_text())['qt_style_packages']:
    f=cache/item['url'].rsplit('/',1)[-1]
    if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=item['sha256']:
        data=urllib.request.urlopen(item['url'],timeout=60).read()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise SystemExit('Package checksum mismatch')
        f.write_bytes(data)
    with tempfile.TemporaryDirectory() as temp:
        subprocess.run(['dpkg-deb','-x',str(f),temp],check=True)
        src=pathlib.Path(temp)/item['member']
        result=subprocess.run(['ldd',str(src)],capture_output=True,text=True,env={k:v for k,v in os.environ.items() if k!='LD_PRELOAD'})
        if result.returncode or 'not found' in result.stdout:raise SystemExit(result.stdout+result.stderr)
        dest=a.prefix/f"kool-qt{item['qt']}/plugins"/item.get("target","styles/libkvantum.so")
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists() or dest.read_bytes()!=src.read_bytes():shutil.copy2(src,dest)
        print('Verified Qt',item['qt'],'plugin:',dest)
