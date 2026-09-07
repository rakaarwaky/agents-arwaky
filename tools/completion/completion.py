#!/usr/bin/env python3
"""Shell completion generator (Python) — pengganti completion.sh."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

COMMANDS = "status doctor list run install mcp skill connect disconnect unconnect unskill anytype 9router service sync backup restore check submodules clean uninstall reset completion help"
HARNESSES = "--antigravity --hermes --opencode --qwencode --all --force --dry-run --mcp-only --skills-only --env-only"
SERVICE_ACTIONS = "status start stop restart logs"
SERVICE_TARGETS = "9router anytype all"
TOOLS = "context7 fetch ponytail anytype codegraph 9router workspace mnemosyne vision qwen-web lint blender skill"


def generate_bash():
    return f'''# Bash / Zsh completion for agents-arwaky (aa)
_aa_completion() {{
  local cur prev words cword
  _init_completion -n : 2>/dev/null || {{
    cur="${{COMP_WORDS[COMP_CWORD]}}"
    prev="${{COMP_WORDS[COMP_CWORD-1]}}"
    words=("${{COMP_WORDS[@]}}")
    cword=$COMP_CWORD
  }}
  local commands="{COMMANDS}"
  local harnesses="{HARNESSES}"
  local service_actions="{SERVICE_ACTIONS}"
  local service_targets="{SERVICE_TARGETS}"
  local tools="{TOOLS}"
  if [ "$cword" -eq 1 ]; then
    COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
    return 0
  fi
  local first_cmd="${{words[1]}}"
  case "$first_cmd" in
    run)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$tools" -- "$cur") ); fi ;;
    install)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$tools" -- "$cur") ); fi ;;
    connect|disconnect|unconnect)
      COMPREPLY=( $(compgen -W "$harnesses" -- "$cur") ) ;;
    service)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$service_actions" -- "$cur") )
      elif [ "$cword" -eq 3 ]; then COMPREPLY=( $(compgen -W "$service_targets" -- "$cur") ); fi ;;
    mcp)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "list generate show path" -- "$cur") ); fi ;;
    skill|skills)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "list install uninstall show check sync" -- "$cur") ); fi ;;
    backup|restore)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "all anytype 9router mnemosyne" -- "$cur") ); fi ;;
    clean)
      COMPREPLY=( $(compgen -W "--host --all" -- "$cur") ) ;;
    completion)
      COMPREPLY=( $(compgen -W "bash zsh --install" -- "$cur") ) ;;
    *) ;;
  esac
}}
complete -F _aa_completion aa agents-arwaky
'''


def install():
    target = Path.home() / ".local/share/bash-completion/completions"
    target.mkdir(parents=True, exist_ok=True)
    f = target / "aa"
    f.write_text(generate_bash(), encoding="utf-8")
    (target / "agents-arwaky").unlink(missing_ok=True)
    (target / "agents-arwaky").symlink_to("aa")
    print(f"✓ Installed shell completions to: {f}")
    rc = Path.home() / ".bashrc"
    line = "source <(aa completion)"
    if rc.exists() and line not in rc.read_text(encoding="utf-8", errors="replace"):
        with rc.open("a", encoding="utf-8") as fh:
            fh.write(f"\n# agents-arwaky shell completion\n{line}\n")
        print(f"✓ Added '{line}' to {rc}")
    print("Restart your shell or run: " + line)
    return 0


def main(argv):
    target = argv[0] if argv else "bash"
    if target == "--install":
        return install()
    if target in ("bash", "zsh"):
        print(generate_bash())
        return 0
    if target in ("help", "-h", "--help"):
        print("Usage: aa completion [bash|zsh|--install]")
        return 0
    print(generate_bash())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
