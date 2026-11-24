#!/usr/bin/env python3
"""Install Hyprnerd's editor, CLI tools and Japanese input on Ubuntu or Arch."""
import argparse,configparser,datetime,gzip,hashlib,io,json,os,pathlib,platform,re,shlex,shutil,subprocess,tarfile,tempfile,urllib.request
R=pathlib.Path(__file__).resolve().parent
H=pathlib.Path.home()
PACKAGES={
 'ubuntu':['ca-certificates','curl','git','build-essential','unzip','ripgrep','fd-find','fzf','libcurl4t64','libssl3t64','fcitx5','fcitx5-mozc','fcitx5-frontend-gtk3','fcitx5-frontend-gtk4','fcitx5-frontend-qt5','fcitx5-frontend-qt6','fonts-noto-cjk'],
 'arch':['ca-certificates','curl','git','base-devel','unzip','ripgrep','fd','fzf','openssl','fcitx5','fcitx5-mozc','fcitx5-gtk','fcitx5-qt','noto-fonts-cjk'],
}
def run(args,**kwargs):return subprocess.run(args,check=True,**kwargs)
def os_family(path=pathlib.Path('/etc/os-release')):
    info=dict(line.split('=',1) for line in path.read_text().splitlines() if '=' in line)
    ident=info.get('ID','').strip('"')
    if ident not in PACKAGES:raise RuntimeError('Supported systems: Ubuntu 24.04/26.04 and Arch Linux')
    return ident
class Backup:
    def __init__(self):self.root=None;self.paths=[]
    def save(self,p):
        p=pathlib.Path(p);relative=str(p.relative_to(H))
        if relative in self.paths:return
        if self.root is None:
            self.root=H/'.local/state/hyprnerd/bootstrap-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f');self.root.mkdir(parents=True,mode=0o700)
            print('BACKUP:',self.root,flush=True)
        self.paths.append(relative)
        if p.exists() or p.is_symlink():
            dst=self.root/'files'/relative;dst.parent.mkdir(parents=True,exist_ok=True)
            if p.is_symlink():dst.symlink_to(p.readlink())
            elif p.is_dir():shutil.copytree(p,dst,symlinks=True)
            else:shutil.copy2(p,dst)
        (self.root/'manifest.json').write_text(json.dumps({'home':str(H),'paths':self.paths},indent=2)+'\n')
    def write(self,p,data):
        p=pathlib.Path(p)
        if p.is_file() and not p.is_symlink() and p.read_bytes()==data:return
        self.save(p);p.parent.mkdir(parents=True,exist_ok=True)
        if p.is_symlink():p.unlink()
        p.write_bytes(data)
    def link(self,p,target):
        if p.is_symlink() and p.resolve()==target.resolve():return
        self.save(p);p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() or p.is_symlink():p.unlink()
        p.symlink_to(target)
def package_commands(family):
    if family=='ubuntu':return [['apt-get','update'],['apt-get','install','-y','--no-install-recommends',*PACKAGES[family]]]
    # Never perform a partial Arch upgrade. Existing installations get a full -Syu.
    return [['pacman','-Syu','--needed','--noconfirm',*PACKAGES[family]]]
def install_packages(family):
    prefix=[] if os.geteuid()==0 else ['sudo']
    for cmd in package_commands(family):run(prefix+cmd)
def download(spec):
    cache=R/'.cache/foundation';cache.mkdir(parents=True,exist_ok=True)
    p=cache/(spec['sha256'][:16]+'-'+spec['name'])
    if not p.exists():
        temporary=p.with_suffix('.download')
        request=urllib.request.Request(spec['url'],headers={'User-Agent':'hyprnerd-bootstrap'})
        with urllib.request.urlopen(request,timeout=60) as response,temporary.open('wb') as out:shutil.copyfileobj(response,out)
        temporary.replace(p)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=spec['sha256']:raise RuntimeError('Checksum mismatch: '+str(p))
    return p
def install_tool(name,spec,backup):
    root=H/'.local/opt/hyprnerd-tools';root.mkdir(parents=True,exist_ok=True)
    target=root/(name+'-'+spec['version'])
    if not (target/'.verified-sha256').exists() or (target/'.verified-sha256').read_text()!=spec['sha256']:
        archive=download(spec)
        with tempfile.TemporaryDirectory(prefix='build-',dir=root) as tmp:
            payload=pathlib.Path(tmp)/'payload';payload.mkdir()
            if spec['format']=='gzip':(payload/spec['member']).write_bytes(gzip.decompress(archive.read_bytes()))
            else:
                with tarfile.open(archive) as tar:tar.extractall(payload,filter='data')
            binary=payload/spec['member']
            if not binary.is_file():raise RuntimeError('Missing binary in '+name+': '+str(binary))
            binary.chmod(0o755)
            (payload/'.verified-sha256').write_text(spec['sha256'])
            if target.exists():raise RuntimeError('Unexpected existing tool directory: '+str(target))
            payload.rename(target)
    backup.link(H/'.local/bin'/spec['binary'],target/spec['member'])
    print('Installed',name,spec['version'],flush=True)
def replace_block(text,tag,body):
    start,end='# BEGIN '+tag,'# END '+tag
    pattern=re.escape(start)+r'.*?'+re.escape(end)+r'\n?'
    text=re.sub(pattern,'',text,flags=re.S).rstrip()
    return text+'\n\n'+start+'\n'+body.rstrip()+'\n'+end+'\n'
def quiet_shell(text):
    # Only remove standalone startup commands; preserve aliases/functions and user code.
    return re.sub(r'(?m)^[ \t]*(?:fastfetch|neofetch)(?:[ \t]+[^\n;|&]*)?[ \t]*\n',': # Startup dashboard disabled by hyprnerd\n',text)
def configure_shell(backup):
    p=H/'.bashrc';text=p.read_text() if p.exists() else ''
    text=quiet_shell(text)
    # Use the installed binary even when an old Atuin installer prepends ~/.atuin/bin.
    text=re.sub(r'eval\s+"\$\(atuin init bash\)"','eval "$("$HOME/.local/bin/atuin" init bash)"',text)
    body='export PATH="$HOME/.local/bin:$PATH"\nif [[ $- == *i* && ${__atuin_initialized-} != true ]]; then\n    eval "$(atuin init bash)"\nfi'
    backup.write(p,replace_block(text,'HYPRNERD SHELL',body).encode())
    hook=H/'.config/bashrc/kool-terminal.bash'
    backup.write(hook,(R/'home/.config/bashrc/kool-terminal.bash').read_bytes())
    # No account registration or sync settings: existing Atuin history remains in place.
def configure_nvim(backup):
    dest=H/'.config/nvim';source=R/'foundation/nvim'
    lazy_config=dest/'lua/config/lazy.lua'
    is_lazy=lazy_config.exists() and 'LazyVim/LazyVim' in lazy_config.read_text()
    if dest.exists() and not is_lazy:
        backup.save(dest)
        if dest.is_symlink():dest.unlink()
        else:shutil.rmtree(dest)
    for p in source.rglob('*'):
        if p.is_file() and (not is_lazy or not (dest/p.relative_to(source)).exists()):backup.write(dest/p.relative_to(source),p.read_bytes())
    p=dest/'lua/config/options.lua';text=p.read_text() if p.exists() else ''
    start='-- BEGIN HYPRNERD OPTIONS';end='-- END HYPRNERD OPTIONS'
    text=re.sub(re.escape(start)+r'.*?'+re.escape(end)+r'\n?','',text,flags=re.S).rstrip()
    backup.write(p,(text+'\n\n'+start+'\nvim.opt.number = true\nvim.opt.relativenumber = true\n'+end+'\n').encode())
def read_ini(p):
    cfg=configparser.ConfigParser(interpolation=None,strict=False);cfg.optionxform=str
    if p.exists():cfg.read(p)
    return cfg
def ini_bytes(cfg):
    buf=io.StringIO();cfg.write(buf,space_around_delimiters=False);return buf.getvalue().encode()
def configure_input(backup):
    root=H/'.config/fcitx5';p=root/'config';cfg=read_ini(p)
    cfg['Hotkey/TriggerKeys']={'0':'Control+space'}
    if not cfg.has_section('Behavior'):cfg['Behavior']={}
    cfg['Behavior']['ActiveByDefault']='False';cfg['Behavior']['ShareInputState']='No'
    backup.write(p,ini_bytes(cfg))
    p=root/'profile';cfg=read_ini(p)
    groups=[s for s in cfg.sections() if re.fullmatch(r'Groups/\d+',s)]
    if not groups:cfg=read_ini(R/'foundation/fcitx5/profile');groups=['Groups/0']
    for group in groups:
        cfg[group]['DefaultIM']='mozc'
        items=[s for s in cfg.sections() if s.startswith(group+'/Items/')]
        if not any(cfg[s].get('Name')=='mozc' for s in items):
            index=max([int(s.rsplit('/',1)[1]) for s in items]+[-1])+1;cfg[group+'/Items/'+str(index)]={'Name':'mozc','Layout':''}
    backup.write(p,ini_bytes(cfg))
    for version in ['3.0','4.0']:
        p=H/('.config/gtk-'+version+'/settings.ini');cfg=read_ini(p)
        if not cfg.has_section('Settings'):cfg['Settings']={}
        cfg['Settings']['gtk-im-module']='fcitx';backup.write(p,ini_bytes(cfg))
    p=H/'.config/environment.d/60-hyprnerd-input.conf'
    backup.write(p,b'XMODIFIERS=@im=fcitx\nQT_IM_MODULE=fcitx\nQT_IM_MODULES=wayland;fcitx;ibus\nSDL_IM_MODULE=fcitx\n')
    p=H/'.config/autostart/org.fcitx.Fcitx5.desktop'
    backup.write(p,b'[Desktop Entry]\nType=Application\nName=Fcitx 5\nExec=fcitx5 -d\nTryExec=fcitx5\nX-GNOME-Autostart-enabled=true\n')
def sync_plugins():
    run([str(H/'.local/bin/nvim'),'--headless','+Lazy! restore','+qa'],timeout=600)
def activate_input():
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):return
    # New settings also apply to the legacy Arch session without loading Lua there.
    version=subprocess.check_output(["hyprctl","version"],text=True)
    if "0.52." in version:
        run(["hyprctl","keyword","bind","CTRL,SPACE,exec,fcitx5-remote -t"])
        run(["hyprctl","dispatch","exec","fcitx5 -rd"])
        return
    run(['hyprctl','eval','hl.env("XMODIFIERS","@im=fcitx"); hl.env("QT_IM_MODULE","fcitx"); hl.env("QT_IM_MODULES","wayland;fcitx;ibus"); hl.env("SDL_IM_MODULE","fcitx"); hl.exec_cmd("fcitx5 -rd")'])
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--check',action='store_true');p.add_argument('--skip-packages',action='store_true');p.add_argument('--skip-plugins',action='store_true');p.add_argument('--no-session',action='store_true');a=p.parse_args(argv)
    if not(a.apply or a.check):p.error('Choose --check or --apply')
    family=os_family();lock=json.loads((R/'dependencies.lock.json').read_text())
    if platform.machine() not in ['x86_64','amd64']:raise SystemExit('Pinned tool binaries currently require Linux x86_64')
    print('System:',family,'; tools:',', '.join(lock['foundation_tools']))
    for cmd in package_commands(family):print('Packages:',shlex.join(cmd))
    if not a.apply:print('Read-only check: no packages, files or downloads changed.');return
    if not a.skip_packages:install_packages(family)
    backup=Backup()
    # Snapshot existing history before a newer Atuin binary can migrate its schema.
    import sqlite3
    for database in (H/'.local/share/atuin').glob('*.db'):
        backup.save(database)
        copy=backup.root/'files'/database.relative_to(H)
        copy.unlink()
        with sqlite3.connect(str(database)) as source, sqlite3.connect(str(copy)) as dest:source.backup(dest)
    for name,spec in lock['foundation_tools'].items():install_tool(name,spec,backup)
    os.environ['PATH']=str(H/'.local/bin')+':'+os.environ.get('PATH','')
    if not shutil.which('fd') and shutil.which('fdfind'):backup.link(H/'.local/bin/fd',pathlib.Path(shutil.which('fdfind')))
    configure_shell(backup);configure_nvim(backup)
    if not a.no_session and os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        subprocess.run(["fcitx5-remote","-e"],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    configure_input(backup)
    if not a.skip_plugins:sync_plugins()
    if not a.no_session:activate_input()
    print('Foundation installed. Japanese input: Ctrl+Space. Neovim: relative line numbers.')
if __name__=='__main__':main()
