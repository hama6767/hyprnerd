#!/usr/bin/env python3
"""One auto-hidden dock, with hotspots rebuilt when outputs are plugged/unplugged."""
import fcntl,json,os,pathlib,signal,subprocess,sys,time
STATE=pathlib.Path(os.environ.get('XDG_STATE_HOME',str(pathlib.Path.home()/'.local/state')))/'hyprnerd'
RUNTIME=pathlib.Path(os.environ.get('XDG_RUNTIME_DIR','/tmp'))/'hyprnerd'
SCRIPT=pathlib.Path(__file__).resolve()
def dock_command():
    return ['nwg-dock-hyprland','-d','-hd','0','-p','bottom','-l','overlay','-hl','overlay','-i','40','-mb','8','-w','0','-g','kitty-dropterm','-c',str(SCRIPT.parent/'RofiLauncher.sh')]
def output_names():
    result=subprocess.run(['hyprctl','-j','monitors'],capture_output=True,text=True,timeout=3,check=True)
    return tuple(sorted(m['name'] for m in json.loads(result.stdout) if not m.get('disabled',False) and m.get('mirrorOf') in (None, '', 'none')))
def daemon():
    lock=(RUNTIME/'dock.lock').open('w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return
    child=None;running=True;previous=None
    def stop(*args):
        nonlocal running;running=False
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    def stop_child():
        nonlocal child
        if child and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=3)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        child=None
    try:
        with (RUNTIME/'dock.log').open('a') as log:
            while running:
                try:names=output_names()
                except (subprocess.SubprocessError,ValueError):break
                marker=RUNTIME/'dock-restart'
                generation=marker.stat().st_mtime_ns if marker.exists() else 0
                enabled=not (STATE/'dock.disabled').exists()
                desired=(names,generation,enabled)
                if desired!=previous or (child and child.poll() is not None):
                    stop_child();previous=desired
                    if enabled and names:child=subprocess.Popen(dock_command(),stdout=log,stderr=log)
                time.sleep(1)
    finally:stop_child()
def main():
    STATE.mkdir(parents=True,exist_ok=True);RUNTIME.mkdir(parents=True,exist_ok=True)
    cmd=sys.argv[1].removeprefix('--') if len(sys.argv)>1 else 'toggle'
    disabled=STATE/'dock.disabled'
    if cmd=='daemon':daemon();return
    if cmd in ['stop','deactivate']:disabled.touch()
    elif cmd=='toggle':
        if disabled.exists():disabled.unlink()
        else:disabled.touch()
    elif cmd in ['enable','activate']:disabled.unlink(missing_ok=True)
    elif cmd in ['restart','start']:pass
    else:raise SystemExit('Use start, restart, toggle, stop or enable')
    if cmd=='restart':(RUNTIME/'dock-restart').touch()
    with (RUNTIME/'dock-manager.log').open('a') as log:
        subprocess.Popen([sys.executable,str(SCRIPT),'daemon'],stdout=log,stderr=log,start_new_session=True)
if __name__=='__main__':main()
