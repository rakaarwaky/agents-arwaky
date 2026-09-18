"""Completion surface — CLI adapter for aa completion."""
from __future__ import annotations

from modules.shared.src.utility_completer import generate_bash, generate_zsh, install


def cmd_completion(args: list[str]) -> int:
    """aa completion [bash|zsh|--install]."""
    target = args[0] if args else "bash"
    if target == "--install":
        return install()
    if target == "zsh":
        print(generate_zsh())
        return 0
    if target in ("help", "-h", "--help"):
        print("Usage: aa completion [bash|zsh|--install]")
        return 0
    print(generate_bash())
    return 0
