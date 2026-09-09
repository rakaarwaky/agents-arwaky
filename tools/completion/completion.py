#!/usr/bin/env python3
"""Shell completion generator (Python) — pengganti completion.sh."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "lib"))
from paths import repo_root
ROOT = repo_root()
sys.path.insert(0, str(ROOT / "tools" / "lib"))

from xdg import data_home  # type: ignore[import-not-found]

COMMANDS = (
    "status doctor tool skill connect disconnect mcp anytype 9router service "
    "backup restore check submodules clean reset sync completion version help "
    # backward-compat verbs (deprecated but still dispatched by cli/arwaky.py)
    "list run install update uninstall"
)
HARNESSES = "--antigravity --hermes --opencode --qwencode --all --force --dry-run --mcp-only --skills-only --env-only"
SERVICE_ACTIONS = "status start stop restart logs"
SERVICE_TARGETS = "9router anytype all"
TOOL_SUBCOMMANDS = "list run install update uninstall"
FALLBACK_TOOLS = "context7 fetch ponytail anytype codegraph 9router workspace mnemosyne vision qwen-web lint blender skill"


def _tools_from_manifest() -> str:
    """Single source of truth: manifest.json (static fallback on any error)."""
    try:
        manifest_path = ROOT / "tools/config/manifest.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        ids = [t["id"] for t in data.get("tools", []) if t.get("id")]
        if ids:
            return " ".join(ids)
    except Exception:
        pass
    return FALLBACK_TOOLS


def generate_bash():
    tools = _tools_from_manifest()
    tool_subs = TOOL_SUBCOMMANDS
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
  local tools="{tools}"
  local tool_subs="{tool_subs}"
  if [ "$cword" -eq 1 ]; then
    COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
    return 0
  fi
  local first_cmd="${{words[1]}}"
  case "$first_cmd" in
    tool)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$tool_subs" -- "$cur") )
      elif [ "$cword" -eq 3 ]; then COMPREPLY=( $(compgen -W "$tools" -- "$cur") ); fi ;;
    run)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$tools" -- "$cur") ); fi ;;
    install)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$tools" -- "$cur") ); fi ;;
    connect|disconnect)
      COMPREPLY=( $(compgen -W "$harnesses" -- "$cur") ) ;;
    service)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "$service_actions" -- "$cur") )
      elif [ "$cword" -eq 3 ]; then COMPREPLY=( $(compgen -W "$service_targets" -- "$cur") ); fi ;;
    mcp)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "list generate show path" -- "$cur") ); fi ;;
    skill|skills)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "list install uninstall show check sync" -- "$cur") ); fi ;;
    backup|restore)
      if [ "$cword" -eq 2 ]; then COMPREPLY=( $(compgen -W "all anytype 9router mnemosyne list" -- "$cur") ); fi ;;
    clean)
      COMPREPLY=( $(compgen -W "--host --all" -- "$cur") ) ;;
    completion)
      COMPREPLY=( $(compgen -W "bash zsh --install" -- "$cur") ) ;;
    *) ;;
  esac
}}
complete -F _aa_completion aa agents-arwaky


'''


def generate_zsh():
    """Generate zsh completion using compdef/_describe."""
    cmds = " ".join(f"'{c}:{c} command'" for c in COMMANDS.split())
    return (
        "#compdef aa\n"
        "_aa() {\n"
        "  local -a commands\n"
        f"  commands=({cmds})\n"
        "  _describe 'command' commands\n"
        "}\n"
        "_aa \"$@\"\n"
    )



def install():
    target = data_home() / "bash-completion/completions"
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
    if target == "bash":
        print(generate_bash())
        return 0
    if target == "zsh":
        print(generate_zsh())
        return 0
    if target in ("help", "-h", "--help"):
        print("Usage: aa completion [bash|zsh|--install]")
        return 0
    print(generate_bash())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
