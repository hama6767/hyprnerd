# Compact two-line prompt; Atuin retains its existing history hooks.
case $TERM in
    dumb) return ;;
esac
PS1='\[\e]0;\u@\h: \w\a\]\[\e[1;36m\]╭─ \u@\h \[\e[0;34m\]\w\[\e[0m\]\n\[\e[1;36m\]╰─\[\e[1;32m\]❯\[\e[0m\] '

# Keep shell startup quiet; fastfetch remains available as an explicit command.
