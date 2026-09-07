"""UI helpers: warna/banner/log (Python)."""
from __future__ import annotations

import os
import sys


def _color_enabled() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


_ENABLED = _color_enabled()


def _c(code: str) -> str:
    return f"\033[{code}m" if _ENABLED else ""


BOLD = _c("1")
DIM = _c("2")
GREEN = _c("0;32m")
BLUE = _c("0;34m")
CYAN = _c("0;36m")
YELLOW = _c("0;33m")
RED = _c("0;31m")
RESET = _c("0m")


def banner() -> None:
    print(f"{CYAN}{BOLD}   ___                           _          {RESET}")
    print(f"{CYAN}{BOLD}  / _ | _______    _____ _ / /____ __   {RESET}")
    print(f"{CYAN}{BOLD} / __ |/ __/ _ \\/\\/ _ `/  '_/ // /   {RESET}")
    print(f"{CYAN}{BOLD}/_/ |_/_/  \\_/\\_/\\_,_/_/\\_\\\\_, /    {RESET}")
    print(f"{CYAN}{BOLD}                           /___/     {RESET}")
    print(f"{DIM} agents-arwaky Unified Tool Orchestrator (Python, per-tool){RESET}")
    print()


def info(msg: str) -> None:
    print(f"{CYAN}==>{RESET} {BOLD}{msg}{RESET}")


def sub(msg: str) -> None:
    print(f"  {BLUE}->{RESET} {msg}")


def ok(msg: str) -> None:
    print(f"  {GREEN}\u2713{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}\u26a0{RESET} {msg}")


def err(msg: str) -> None:
    print(f"  {RED}\u2717{RESET} {msg}", file=sys.stderr)
