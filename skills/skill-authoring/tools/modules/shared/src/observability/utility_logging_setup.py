"""UI helpers: colors/banner/log (Python).

Skill-design owns its own utility tree, so it carries its own logging helpers rather than importing skill-traces'. No cross-skill import.
Moved as-is from tools/lib/ui.py (logging domain)."""
from __future__ import annotations

import logging
import os
import re
import sys

# Structured logging (P1-O1): level + timestamp + correlation ID on log output
_logger = logging.getLogger("sac")
if not _logger.handlers:
    _handler = logging.StreamHandler()
    _fmt = "%(asctime)s %(levelname)s [%(correlation_id)s] %(message)s"
    _handler.setFormatter(logging.Formatter(_fmt, datefmt="%H:%M:%S"))

    class _CorrelationFilter(logging.Filter):
        def filter(self, record):
            """Attach the correlation id to every log record from the SDC_CORRELATION_ID env var."""
            record.correlation_id = os.environ.get("SDC_CORRELATION_ID", "-")
            return True

    _handler.addFilter(_CorrelationFilter())
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


_color_override = None


def _color_enabled() -> bool:
    if _color_override is not None:
        return _color_override
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    return sys.stdout.isatty()


def _c(code: str) -> str:
    """Lazy color escape — evaluated at call time, not import time."""
    return f"\033[{code}m" if _color_enabled() else ""


# Lazy color accessors: evaluated at call time, not import time,
def BOLD() -> str:
    """Return the ANSI escape for bold weight (empty when colour is disabled)."""
    return _c("1")
def DIM() -> str:
    """Return the ANSI escape for faint/dim weight."""
    return _c("2")



def CYAN() -> str:
    """Return the ANSI escape for cyan foreground."""
    return _c("0;36")
def RED() -> str:
    """Return the ANSI escape for red foreground."""
    return _c("0;31")



def RESET() -> str:
    """Return the ANSI escape that resets all attributes."""
    return _c("0")


def _term_width() -> int:
    """Current terminal width in columns, with a safe fallback."""
    try:
        import shutil

        return shutil.get_terminal_size((80, 24)).columns
    except (OSError, ValueError):
        return 80


def banner() -> None:
    """Print the CLI banner (plain text on non-TTY or narrow terminal)."""
    display_name = os.environ.get("SDC_DISPLAY_NAME") or "skill-design"
    if not sys.stdout.isatty() or _term_width() < 50:
        # Non-TTY or narrow terminal: plain text, avoid broken ASCII art.
        print(f"{display_name} — skill-design CLI")
        print()
        return
    print(f"{CYAN()}{BOLD()}   ___                           _          {RESET()}")
    print(f"{CYAN()}{BOLD()}  / _ | _______    _____ _ / /____ __   {RESET()}")
    print(f"{CYAN()}{BOLD()} / __ |/ __/ _ \\/\\/ _ `/  '_/ // /   {RESET()}")
    print(f"{CYAN()}{BOLD()}/_/ |_/_/  \\_/\\_/\\_,_/_/\\_\\\\_, /    {RESET()}")
    print(f"{CYAN()}{BOLD()}                           /___/     {RESET()}")
    print(f"{DIM()} {display_name} CLI (Python, per-tool){RESET()}")
    print()


def info(msg: str) -> None:
    """Print a cyan '==>' styled heading to stdout."""
    print(f"{CYAN()}==>{RESET()} {BOLD()}{msg}{RESET()}")


def err(msg: str) -> None:
    """Print a red '[FAIL]' error message to stderr."""
    print(f"  {RED()}[FAIL]{RESET()} {msg}", file=sys.stderr)


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _harden_stdio() -> None:
    """Prevent UnicodeEncodeError crashes under C/POSIX (ASCII) locales."""
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(errors="replace")
        except (OSError, ValueError):
            pass


_harden_stdio()


