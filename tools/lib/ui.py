"""UI helpers: warna/banner/log (Python)."""
from __future__ import annotations

import logging as _logging
import os
import sys

# Structured logging (P1-O1): level + timestamp pada output log
_logger = _logging.getLogger("agents-arwaky")
if not _logger.handlers:
    _handler = _logging.StreamHandler()
    _handler.setFormatter(_logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
    _logger.addHandler(_handler)
    _logger.setLevel(_logging.INFO)


def log_debug(msg):
    _logger.debug(msg)


def log_info(msg):
    _logger.info(msg)


def log_warning(msg):
    _logger.warning(msg)


_color_override = None


def set_color_mode(enabled):
    """Override color detection. None = auto-detect."""
    global _color_override
    _color_override = enabled


def _color_enabled() -> bool:
    if _color_override is not None:
        return _color_override
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    return sys.stdout.isatty()


def _c(code: str) -> str:
    return f"\033[{code}m" if _color_enabled() else ""


BOLD = _c("1")
DIM = _c("2")
GREEN = _c("0;32")
BLUE = _c("0;34")
CYAN = _c("0;36")
YELLOW = _c("0;33")
RED = _c("0;31")
RESET = _c("0")


def _term_width() -> int:
    try:
        import shutil
        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


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
    print(f"  {GREEN}[OK]{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}[WARN]{RESET} {msg}")


def err(msg: str) -> None:
    print(f"  {RED}[FAIL]{RESET} {msg}", file=sys.stderr)
