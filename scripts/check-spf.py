#!/usr/bin/env python3
"""Exercise a real superfile TUI in a private PTY and verify the parent shell cd."""
import errno,os,pathlib,pty,select,shutil,signal,subprocess,tempfile,time
home=pathlib.Path.home()
with tempfile.TemporaryDirectory(prefix='hyprnerd-spf-check-') as temporary:
    root=pathlib.Path(temporary);destination=root/"日本語 folder's";destination.mkdir()
    for shell in ['bash','zsh']:
        if not shutil.which(shell):continue
        marker=root/(shell+'.pwd')
        pid,fd=pty.fork()
        if pid==0:
            env=dict(os.environ,TERM='xterm-256color',PATH=str(home/'.local/bin')+':'+os.environ['PATH'],HYPRNERD_DEST=str(destination),HYPRNERD_MARKER=str(marker),HYPRNERD_HOOK=str(home/'.config/shell/hyprnerd-tools.sh'))
            os.execvpe(shell,[shell,'-c','. "$HYPRNERD_HOOK"; spf "$HYPRNERD_DEST"; printf "%s" "$PWD" > "$HYPRNERD_MARKER"'],env)
        deadline=time.monotonic()+15;next_quit=time.monotonic()+1.5;finished=False
        try:
            while time.monotonic()<deadline:
                ready,_,_=select.select([fd],[],[],.1)
                if ready:
                    try:
                        data=os.read(fd,65536)
                        if not data:break
                    except OSError as error:
                        if error.errno==errno.EIO:break
                        raise
                    if b'\x1b]11;' in data:os.write(fd,b'\x1b]11;rgb:1919/1919/1919\x1b\\')
                    if b'\x1b[6n' in data:os.write(fd,b'\x1b[1;1R')
                if time.monotonic()>=next_quit:
                    os.write(fd,b'q');next_quit=time.monotonic()+1
                done,status=os.waitpid(pid,os.WNOHANG)
                if done:finished=True;break
            if not finished:
                done,status=os.waitpid(pid,os.WNOHANG);finished=bool(done)
            assert marker.exists() and marker.read_text()==str(destination),shell+' did not cd on quit'
            print('PASS real superfile cd-on-quit in '+shell+' (spaces, quotes and Japanese path)')
        finally:
            if not finished:
                try:os.kill(pid,signal.SIGTERM)
                except ProcessLookupError:pass
                os.waitpid(pid,0)
            os.close(fd)
