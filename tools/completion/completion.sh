#!/usr/bin/env bash
# tools/completion/completion.sh
# Shell Auto-Completion Generator for agents-arwaky (aa)
# Supports: Bash and Zsh

set -euo pipefail

generate_bash_completion() {
  cat << 'EOF'
# Bash / Zsh completion for agents-arwaky (aa)
_aa_completion() {
  local cur prev words cword
  _init_completion -n : 2>/dev/null || {
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    words=("${COMP_WORDS[@]}")
    cword=$COMP_CWORD
  }

  local commands="status doctor list run install shell mcp skill connect anytype 9router service sync backup restore setup check submodules clean destroy completion help"
  local harnesses="--antigravity --hermes --opencode --qwencode --all --force --dry-run --mcp-only --skills-only --env-only"
  local service_actions="status start stop restart logs"
  local service_targets="9router anytype all"
  local tools="context7 fetch lean-ctx ponytail anytype codegraph 9router workspace mnemosyne vision qwen-web lint blender skill"

  if [ "$cword" -eq 1 ]; then
    COMPREPLY=( $(compgen -W "$commands" -- "$cur") )
    return 0
  fi

  local first_cmd="${words[1]}"
  case "$first_cmd" in
    run)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "$tools" -- "$cur") )
      fi
      ;;
    install)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "$tools" -- "$cur") )
      elif [ "$cword" -eq 3 ]; then
        COMPREPLY=( $(compgen -W "" -- "$cur") )
      fi
      ;;
    connect)
      COMPREPLY=( $(compgen -W "$harnesses" -- "$cur") )
      ;;
    service)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "$service_actions" -- "$cur") )
      elif [ "$cword" -eq 3 ]; then
        COMPREPLY=( $(compgen -W "$service_targets" -- "$cur") )
      fi
      ;;
    mcp)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "list generate show path" -- "$cur") )
      fi
      ;;
    skill|skills)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "list info copy doctor" -- "$cur") )
      fi
      ;;
    anytype)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "status start stop restart logs auth-create auth-key space-join space-list service-install service-status" -- "$cur") )
      fi
      ;;
    9router)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "status start stop restart logs models password key provider open service-install service-status help" -- "$cur") )
      fi
      ;;
    backup|restore)
      if [ "$cword" -eq 2 ]; then
        COMPREPLY=( $(compgen -W "all anytype 9router mnemosyne" -- "$cur") )
      else
        COMPREPLY=( $(compgen -W "--gdrive" -- "$cur") )
      fi
      ;;
    sync)
      COMPREPLY=( $(compgen -W "--pull --build --no-connect --help" -- "$cur") )
      ;;
    clean)
      COMPREPLY=( $(compgen -W "--host --all" -- "$cur") )
      ;;
    completion)
      COMPREPLY=( $(compgen -W "bash zsh --install" -- "$cur") )
      ;;
    *)
      ;;
  esac
}

complete -F _aa_completion aa agents-arwaky
EOF
}

install_completion() {
  local target_dir="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
  mkdir -p "$target_dir"
  local target_file="$target_dir/aa"

  generate_bash_completion > "$target_file"
  ln -sf "aa" "$target_dir/agents-arwaky" 2>/dev/null || true

  echo "✓ Installed shell completions to: $target_file"

  # Check if bash-completion is sourced or suggest eval
  local rc_file="$HOME/.bashrc"
  [ -n "${ZSH_VERSION:-}" ] && rc_file="$HOME/.zshrc"

  local completion_cmd="source <(aa completion)"
  if ! grep -q "aa completion" "$rc_file" 2>/dev/null; then
    {
      echo ""
      echo "# agents-arwaky shell completion"
      echo "$completion_cmd"
    } >> "$rc_file"
    echo "✓ Added '$completion_cmd' to $rc_file"
  else
    echo "✓ Shell completion already configured in $rc_file"
  fi
  echo "Restart your shell or run: $completion_cmd"
}

main() {
  local target="${1:-bash}"

  case "$target" in
    --install)
      install_completion
      ;;
    bash|zsh)
      generate_bash_completion
      ;;
    help|-h|--help)
      echo "Usage: aa completion [bash|zsh|--install]"
      echo ""
      echo "Quick setup: eval \"\$(aa completion bash)\""
      echo "Persistent install: aa completion --install"
      ;;
    *)
      generate_bash_completion
      ;;
  esac
}

main "$@"
