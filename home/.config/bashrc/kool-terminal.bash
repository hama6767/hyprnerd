# Compact two-line prompt; Atuin retains its existing history hooks.
case $TERM in
    dumb) return ;;
esac
PS1='\[\e]0;\u@\h: \w\a\]\[\e[1;36m\]╭─ \u@\h \[\e[0;34m\]\w\[\e[0m\]\n\[\e[1;36m\]╰─\[\e[1;32m\]❯\[\e[0m\] '

# Show the dashboard only for a real Kitty shell, never for bash -c or pipes.
if [[ -t 1 && -z ${BASH_EXECUTION_STRING-} ]] && command -v fastfetch >/dev/null 2>&1; then
    fastfetch --config "$HOME/.config/fastfetch/kool.jsonc"
fi
