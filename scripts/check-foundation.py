#!/usr/bin/env python3
"""Exercise installed tools and editor configuration without touching real accounts."""
import json,os,pathlib,subprocess,sys,tempfile
H=pathlib.Path.home()
def call(*args):return subprocess.check_output(args,text=True,stderr=subprocess.STDOUT).strip()
for executable,flag in [('nvim','--version'),('lazygit','--version'),('atuin','--version'),('lazydon','--help'),('tree-sitter','--version'),('rg','--version'),('fd','--version')]:
    out=call(str(H/'.local/bin'/executable),flag);assert out;print('PASS',executable,out.splitlines()[0])
with tempfile.TemporaryDirectory(prefix='hyprnerd-check-') as temporary:
    marker=pathlib.Path(temporary)/'editor.json'
    lua='vim.fn.writefile({vim.json.encode({number=vim.o.number,relative=vim.o.relativenumber,lazyvim=package.loaded["lazyvim"]~=nil})},'+json.dumps(str(marker))+')'
    subprocess.run([str(H/'.local/bin/nvim'),'--headless','+lua '+lua,'+qa'],check=True,timeout=120)
    values=json.loads(marker.read_text());assert all(values.values()),values;print('PASS LazyVim and relative line numbers')
    env=dict(os.environ,HOME=temporary,PATH=str(H/'.local/bin')+':'+os.environ['PATH'])
    script='eval "$(atuin init bash)"; [[ ${__atuin_initialized-} == true ]]'
    subprocess.run(['bash','--noprofile','--norc','-ic',script],env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=30)
    print('PASS Atuin Bash integration in an isolated home')
profile=(H/'.config/fcitx5/profile').read_text();config=(H/'.config/fcitx5/config').read_text()
assert 'mozc' in profile and 'Control+space' in config
assert pathlib.Path('/usr/share/fcitx5/inputmethod/mozc.conf').exists()
print('PASS Mozc package and Ctrl+Space configuration')
