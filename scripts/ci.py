#!/usr/bin/env python3
"""Offline repository checks; never imports or executes desktop configuration."""
import ast, hashlib, json, pathlib, re, shutil, subprocess, sys, tomllib
R=pathlib.Path(__file__).resolve().parents[1]
def load_jsonc(path):
    text=path.read_text()
    text=re.sub(r'("(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/)',lambda m:m[0] if m[0].startswith('"') else '',text)
    return json.loads(re.sub(r',\s*([}\]])',r'\1',text))
def main():
    manifest=json.loads((R/'assets-manifest.json').read_text())
    actual={str(p.relative_to(R)) for p in (R/'home').rglob('*') if p.is_file() or p.is_symlink()}
    assert actual==set(manifest),f'Asset manifest differs: {actual ^ set(manifest)}'
    for relative,expected in manifest.items():
        path=R/relative
        if isinstance(expected,dict):
            assert path.is_symlink() and str(path.readlink())==expected['link'],relative
            assert path.exists(),f'Broken link: {relative}'
            assert path.resolve().is_relative_to((R/'home').resolve()),f'External link: {relative}'
        else:
            assert not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==expected,relative
    tracked=subprocess.check_output(['git','-C',str(R),'ls-files','-z'],text=True).split('\0')
    secret=re.compile(r'-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----|(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})')
    for relative in filter(None,tracked):
        path=R/relative
        assert not any(p in {'.cache','__pycache__','.ssh','.aws'} for p in path.relative_to(R).parts),relative
        if path.is_symlink():continue
        assert path.stat().st_size<50*1024*1024,f'Oversized file: {relative}'
        try:text=path.read_text()
        except UnicodeDecodeError:continue
        assert not secret.search(text),f'Credential pattern in {relative}'
    python=[R/'install.py',* (R/'scripts').glob('*.py'),* (R/'tests').glob('*.py')]
    for path in python:ast.parse(path.read_text(),filename=str(path))
    shell=[p for p in (R/'home').rglob('*.sh') if not p.is_symlink()]
    for path in shell:subprocess.run(['bash','-n',str(path)],check=True)
    lua=list((R/'home/.config/hypr').rglob('*.lua'))+list((R/'hosts').rglob('*.lua'))
    compiler=shutil.which('luac5.4') or shutil.which('luac')
    if not compiler:raise RuntimeError('Install lua5.4 to check Lua syntax')
    for path in lua:subprocess.run([compiler,'-p',str(path)],check=True)
    for path in [R/'dependencies.lock.json',R/'docs/validation.json']:
        json.loads(path.read_text())
    for name in ['Modules','ModulesCustom','ModulesGroups','ModulesWorkspaces','UserModules','configs/[TOP & BOT] SummitSplit v2']:
        load_jsonc(R/'home/.config/hypr/waybar'/name)
    for path in (R/'home/.config/hypr/wallust').glob('*.toml'):tomllib.loads(path.read_text())
    print(f'PASS: {len(manifest)} assets, {len(python)} Python files, {len(shell)} shell scripts, {len(lua)} Lua files, JSON/TOML, public-content checks')
if __name__=='__main__':main()
