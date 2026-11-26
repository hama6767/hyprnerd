# Shared Bash/Zsh integration. Loaded only by the user's shell, not a child process.
export EDITOR=nvim
export VISUAL=nvim

spf() {
    local spf_last_dir spf_result
    spf_last_dir="$(command spf path-list --lastdir-file)" || return
    # Do not inherit the directory left by an interrupted earlier invocation.
    [ ! -f "$spf_last_dir" ] || rm -f -- "$spf_last_dir"
    if command spf "$@"; then spf_result=0; else spf_result=$?; fi
    if [ "$spf_result" -eq 0 ] && [ -f "$spf_last_dir" ]; then
        # superfile writes a shell-quoted cd command, including paths with quotes.
        . "$spf_last_dir"
        rm -f -- "$spf_last_dir"
    fi
    return "$spf_result"
}
