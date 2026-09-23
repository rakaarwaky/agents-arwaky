"""Shell completion script generation for the aa CLI (bash + zsh)."""
from __future__ import annotations

COMMANDS = (
    "status doctor check submodules clean reset version help "
    "tool skill skills connect disconnect mcp completion "
    "anytype omniroute service backup restore "
    "install update uninstall list ls run"
)


def bash_completion() -> str:
    return f"""_aa_completions() {{
    local cur="${{COMP_WORDS[COMP_CWORD]}}"
    if [[ ${{COMP_CWORD}} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "{COMMANDS}" -- "$cur") )
    else
        case "${{COMP_WORDS[1]}}" in
            tool) COMPREPLY=( $(compgen -W "list ls run install update uninstall" -- "$cur") ) ;;
            skill|skills) COMPREPLY=( $(compgen -W "list ls install uninstall show check sync help" -- "$cur") ) ;;
            connect|disconnect) COMPREPLY=( $(compgen -W "--antigravity --hermes --opencode --qwencode --all" -- "$cur") ) ;;
            mcp) COMPREPLY=( $(compgen -W "list generate show" -- "$cur") ) ;;
            completion) COMPREPLY=( $(compgen -W "bash zsh" -- "$cur") ) ;;
            service) COMPREPLY=( $(compgen -W "start stop restart status" -- "$cur") ) ;;
            backup|restore) COMPREPLY=( $(compgen -W "--output" -- "$cur") ) ;;
        esac
    fi
}}
complete -F _aa_completions aa agents-arwaky"""


def zsh_completion() -> str:
    return f"""#compdef aa agents-arwaky
_aa() {{
    local -a commands
    commands=({COMMANDS})
    if (( CURRENT == 2 )); then
        _describe 'command' commands
    else
        case "${{words[2]}}" in
            tool) _values 'sub' list ls run install update uninstall ;;
            skill|skills) _values 'sub' list ls install uninstall show check sync help ;;
            connect|disconnect) _values 'flag' --antigravity --hermes --opencode --qwencode --all ;;
            mcp) _values 'sub' list generate show ;;
            completion) _values 'shell' bash zsh ;;
            service) _values 'sub' start stop restart status ;;
        esac
    fi
}}
compdef _aa aa"""


__all__ = ["COMMANDS", "bash_completion", "zsh_completion"]
