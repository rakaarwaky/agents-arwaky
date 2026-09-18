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


from modules.shared.src.contract_completion_aggregate import ICompletionAggregate


class CompletionVerb(ICompletionAggregate):
    """Agent-layer verb surface for the completion feature (AES405 aggregate implementor)."""

    def __init__(self) -> None:
        from modules.shared.src.utility_completer import generate_bash, generate_zsh, install

        self._generate_bash = generate_bash
        self._generate_zsh = generate_zsh
        self._install = install

    def generate(self, shell: str) -> str:
        if shell == "zsh":
            return self._generate_zsh()
        return self._generate_bash()

    def install(self) -> int:
        return self._install()
